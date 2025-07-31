"""
Whisper 기반 음성인식 모듈
"""

import time
import logging
from typing import Optional, Dict, Any
import numpy as np

try:
    import whisper
    import torch
except ImportError as e:
    logging.warning(f"Whisper 관련 라이브러리를 가져올 수 없습니다: {e}")
    whisper = None
    torch = None

from ..models.audio_models import ProcessedAudio
from ..models.speech_models import RecognitionResult
from ..models.error_models import RecognitionError, RecognitionErrorType
from ..logger import get_logger


class HuggingFaceWhisperWrapper:
    """허깅페이스 Whisper 모델을 OpenAI Whisper API와 호환되도록 래핑하는 클래스"""
    
    def __init__(self, model, processor, device):
        self.model = model
        self.processor = processor
        self.device = device
        self.logger = get_logger(__name__)
    
    def transcribe(self, audio, language=None, task="transcribe", verbose=False):
        """OpenAI Whisper의 transcribe 메서드와 호환되는 인터페이스"""
        try:
            import torch
            
            # 오디오 전처리
            if isinstance(audio, np.ndarray):
                # 샘플링 레이트 16kHz로 가정
                inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
            else:
                inputs = self.processor(audio, return_tensors="pt")
            
            # 디바이스로 이동
            if self.device == "cuda" and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # 생성 설정
            generation_kwargs = {
                "max_length": 448,
                "num_beams": 1,
                "do_sample": False
            }
            
            # 언어 설정 (한국어 강제)
            if language == "ko":
                # 한국어 토큰 ID 직접 설정
                decoder_input_ids = torch.tensor([[50258, 50259, 50359, 50363]])  # <|startoftranscript|><|ko|><|transcribe|><|notimestamps|>
                if self.device == "cuda" and torch.cuda.is_available():
                    decoder_input_ids = decoder_input_ids.to("cuda")
                generation_kwargs["decoder_input_ids"] = decoder_input_ids
            
            # 생성
            with torch.no_grad():
                predicted_ids = self.model.generate(
                    inputs["input_features"],
                    **generation_kwargs
                )
            
            # 텍스트 디코딩
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)
            text = transcription[0] if transcription else ""
            
            # OpenAI Whisper 형식으로 결과 반환
            return {
                "text": text,
                "segments": [
                    {
                        "text": text,
                        "avg_logprob": -0.5,  # 임시 값
                        "start": 0.0,
                        "end": len(text) * 0.1  # 임시 값
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"허깅페이스 모델 추론 실패: {e}")
            return {"text": "", "segments": []}


class SpeechRecognizer:
    """
    Whisper 기반 음성인식 클래스
    
    기본 Whisper 모델을 사용하여 음성을 텍스트로 변환하고
    신뢰도를 계산하는 기능을 제공합니다.
    """
    
    def __init__(self, model_name: str = "base", language: str = "ko", device: Optional[str] = None):
        """
        SpeechRecognizer 초기화
        
        Args:
            model_name: Whisper 모델 이름 (tiny, base, small, medium, large)
            language: 인식할 언어 코드 (기본값: "ko")
            device: 사용할 디바이스 ("cpu", "cuda", None=자동선택)
        """
        self.logger = get_logger(__name__)
        self.model_name = model_name
        self.language = language
        
        # 디바이스 설정
        if device is None:
            self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Whisper 모델 로드 (기본, 로컬, 허깅페이스 모델 지원)"""
        if whisper is None:
            raise ImportError("whisper 라이브러리가 설치되지 않았습니다. 'pip install openai-whisper' 명령으로 설치하세요.")
        
        try:
            self.logger.info(f"Whisper 모델 로딩 중: {self.model_name} (device: {self.device})")
            
            # 모델 타입 판별 및 로드
            if self._is_huggingface_model(self.model_name):
                # 허깅페이스 모델 로드 (로컬/원격 모두 포함)
                self.logger.info(f"허깅페이스 모델 로드: {self.model_name}")
                self.model = self._load_huggingface_model(self.model_name)
                
            elif self._is_local_path(self.model_name):
                # 로컬 OpenAI Whisper 모델 파일 로드
                self.logger.info(f"로컬 OpenAI Whisper 모델 파일 로드: {self.model_name}")
                self.model = whisper.load_model(self.model_name, device=self.device)
                
            else:
                # 기본 OpenAI Whisper 모델 로드
                self.logger.info(f"기본 Whisper 모델 로드: {self.model_name}")
                self.model = whisper.load_model(self.model_name, device=self.device)
            
            self.logger.info("Whisper 모델 로딩 완료")
            
        except Exception as e:
            self.logger.error(f"Whisper 모델 로딩 실패: {e}")
            raise RecognitionError(
                RecognitionErrorType.MODEL_LOAD_FAILED,
                f"모델 로딩 실패: {e}"
            )
    
    def _is_local_path(self, model_name: str) -> bool:
        """로컬 파일 경로인지 확인"""
        return (model_name.startswith("./") or 
                model_name.startswith("/") or 
                model_name.startswith("\\") or
                (len(model_name) > 1 and model_name[1] == ":"))  # Windows 절대 경로
    
    def _is_local_huggingface_model(self, model_name: str) -> bool:
        """로컬 허깅페이스 모델인지 확인"""
        if not self._is_local_path(model_name):
            return False
        
        from pathlib import Path
        model_path = Path(model_name)
        
        # config.json과 model.safetensors (또는 pytorch_model.bin) 파일이 있으면 HF 모델
        has_config = (model_path / "config.json").exists()
        has_model = (model_path / "model.safetensors").exists() or (model_path / "pytorch_model.bin").exists()
        
        return has_config and has_model
    
    def _is_huggingface_model(self, model_name: str) -> bool:
        """허깅페이스 모델 형식인지 확인"""
        # 로컬 허깅페이스 모델 확인
        if self._is_local_huggingface_model(model_name):
            return True
        
        # 원격 허깅페이스 모델은 보통 "organization/model-name" 형식
        return "/" in model_name and not self._is_local_path(model_name)
    
    def _load_huggingface_model(self, model_name: str):
        """허깅페이스에서 Whisper 모델 로드"""
        try:
            # transformers 라이브러리 사용하여 허깅페이스 모델 로드
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
            import torch
            
            self.logger.info(f"허깅페이스에서 모델 다운로드 중: {model_name}")
            
            # 모델과 프로세서 로드
            model = WhisperForConditionalGeneration.from_pretrained(model_name)
            processor = WhisperProcessor.from_pretrained(model_name)
            
            # 디바이스로 이동
            if self.device == "cuda" and torch.cuda.is_available():
                model = model.to("cuda")
            
            # Whisper 호환 래퍼 생성
            return HuggingFaceWhisperWrapper(model, processor, self.device)
            
        except ImportError:
            self.logger.error("transformers 라이브러리가 필요합니다. 'pip install transformers' 명령으로 설치하세요.")
            raise RecognitionError(
                RecognitionErrorType.MODEL_LOAD_FAILED,
                "transformers 라이브러리가 설치되지 않았습니다"
            )
        except Exception as e:
            self.logger.error(f"허깅페이스 모델 로드 실패: {e}")
            # 허깅페이스 로드 실패 시 기본 whisper로 시도
            self.logger.info("기본 whisper 모델로 재시도합니다...")
            return whisper.load_model(model_name.split("/")[-1], device=self.device)
    
    def recognize_from_file(self, file_path: str) -> RecognitionResult:
        """
        음성 파일에서 직접 텍스트로 변환
        
        Args:
            file_path: 음성 파일 경로
            
        Returns:
            RecognitionResult: 인식 결과
            
        Raises:
            RecognitionError: 음성인식 실패 시
        """
        if self.model is None:
            raise RecognitionError(
                RecognitionErrorType.MODEL_NOT_LOADED,
                "모델이 로드되지 않았습니다"
            )
        
        start_time = time.time()
        
        try:
            # 파일 경로 검증 및 디버그
            from pathlib import Path
            file_path_obj = Path(file_path)
            self.logger.debug(f"파일 경로 확인: {file_path}")
            self.logger.debug(f"절대 경로: {file_path_obj.absolute()}")
            self.logger.debug(f"파일 존재 여부: {file_path_obj.exists()}")
            
            if not file_path_obj.exists():
                raise RecognitionError(
                    RecognitionErrorType.INVALID_INPUT,
                    f"음성 파일을 찾을 수 없습니다: {file_path}"
                )
            
            # 한글 파일명 처리를 위해 librosa로 먼저 로드
            try:
                import librosa
                audio_data, sr = librosa.load(str(file_path_obj.absolute()), sr=16000)
                self.logger.debug(f"librosa로 오디오 로드 성공: shape={audio_data.shape}, sr={sr}")
                
                # Whisper 모델로 음성인식 수행 (오디오 데이터 직접 전달)
                result = self.model.transcribe(
                    audio_data,
                    language=self.language,
                    task="transcribe",
                    verbose=False
                )
            except ImportError:
                # librosa가 없는 경우 기존 방식 사용
                result = self.model.transcribe(
                    str(file_path_obj.absolute()),
                    language=self.language,
                    task="transcribe",
                    verbose=False
                )
            
            # 결과 추출
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            
            # 신뢰도 계산 (세그먼트별 평균 확률)
            confidence = self._calculate_confidence(segments)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"음성인식 완료: '{text}' (신뢰도: {confidence:.2f}, 처리시간: {processing_time:.2f}s)")
            
            return RecognitionResult(
                text=text,
                confidence=confidence,
                processing_time=processing_time,
                language=self.language,
                model_version=self.model_name
            )
            
        except RecognitionError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"음성인식 중 오류 발생: {e}")
            raise RecognitionError(
                RecognitionErrorType.RECOGNITION_FAILED,
                f"음성인식 실패: {e}",
                processing_time=processing_time
            )

    def recognize(self, audio: ProcessedAudio) -> RecognitionResult:
        """
        음성을 텍스트로 변환
        
        Args:
            audio: 전처리된 음성 데이터
            
        Returns:
            RecognitionResult: 인식 결과
            
        Raises:
            RecognitionError: 음성인식 실패 시
        """
        if self.model is None:
            raise RecognitionError(
                RecognitionErrorType.MODEL_NOT_LOADED,
                "모델이 로드되지 않았습니다"
            )
        
        start_time = time.time()
        
        try:
            # 음성 데이터 검증
            if not isinstance(audio.features, np.ndarray):
                raise RecognitionError(
                    RecognitionErrorType.INVALID_INPUT,
                    "음성 특징이 numpy 배열이 아닙니다"
                )
            
            if audio.features.size == 0:
                raise RecognitionError(
                    RecognitionErrorType.INVALID_INPUT,
                    "음성 특징 데이터가 비어있습니다"
                )
            
            # Whisper는 1차원 오디오 데이터를 기대하므로 변환
            if len(audio.features.shape) == 2:
                # Log-Mel spectrogram을 다시 오디오로 변환하는 대신
                # 원본 오디오 데이터를 사용해야 함
                # 여기서는 임시로 평균을 취해서 1차원으로 변환
                audio_data = np.mean(audio.features, axis=0)
            else:
                audio_data = audio.features
            
            # 오디오 데이터 정규화 (Whisper는 -1~1 범위를 기대)
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            audio_data = audio_data.astype(np.float32)
            
            # Whisper 모델로 음성인식 수행
            result = self.model.transcribe(
                audio_data,
                language=self.language,
                task="transcribe",
                verbose=False
            )
            
            # 결과 추출
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            
            # 신뢰도 계산 (세그먼트별 평균 확률)
            confidence = self._calculate_confidence(segments)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"음성인식 완료: '{text}' (신뢰도: {confidence:.2f}, 처리시간: {processing_time:.2f}s)")
            
            return RecognitionResult(
                text=text,
                confidence=confidence,
                processing_time=processing_time,
                language=self.language,
                model_version=self.model_name
            )
            
        except RecognitionError:
            raise
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"음성인식 중 오류 발생: {e}")
            raise RecognitionError(
                RecognitionErrorType.RECOGNITION_FAILED,
                f"음성인식 실패: {e}",
                processing_time=processing_time
            )
    
    def _calculate_confidence(self, segments: list) -> float:
        """
        세그먼트 정보를 바탕으로 신뢰도 계산
        
        Args:
            segments: Whisper 결과의 세그먼트 리스트
            
        Returns:
            float: 평균 신뢰도 (0.0 ~ 1.0)
        """
        if not segments:
            return 0.5  # 기본값
        
        # 각 세그먼트의 평균 로그 확률을 신뢰도로 변환
        total_confidence = 0.0
        total_length = 0
        
        for segment in segments:
            # avg_logprob을 확률로 변환 (exp 함수 사용)
            avg_logprob = segment.get("avg_logprob", -1.0)
            segment_confidence = min(1.0, max(0.0, np.exp(avg_logprob)))
            
            # 세그먼트 길이로 가중평균
            segment_length = len(segment.get("text", ""))
            total_confidence += segment_confidence * segment_length
            total_length += segment_length
        
        if total_length == 0:
            return 0.5
        
        return total_confidence / total_length
    
    def is_available(self) -> bool:
        """
        음성인식 모듈 사용 가능 여부 확인
        
        Returns:
            bool: 사용 가능 여부
        """
        return whisper is not None and self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        모델 정보 반환
        
        Returns:
            Dict: 모델 정보
        """
        model_type = "unknown"
        if self._is_local_path(self.model_name):
            model_type = "local_file"
        elif self._is_huggingface_model(self.model_name):
            model_type = "huggingface"
        elif self.model_name in ["tiny", "base", "small", "medium", "large"]:
            model_type = "openai_whisper"
        
        return {
            "model_name": self.model_name,
            "model_type": model_type,
            "language": self.language,
            "device": self.device,
            "available": self.is_available(),
            "is_local": self._is_local_path(self.model_name),
            "is_huggingface": self._is_huggingface_model(self.model_name)
        }
    
    def __del__(self):
        """소멸자 - 모델 메모리 해제"""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()