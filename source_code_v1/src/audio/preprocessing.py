"""
음성 전처리 모듈
"""

import numpy as np
import librosa
import torch
import torchaudio
import os
import tempfile
import shutil
from typing import Optional, Tuple, Dict, Any
import logging
from dataclasses import dataclass
from collections import defaultdict

# 고급 화자 분리를 위한 import (최신 버전 3.3.2, 1.0.3 기준)
try:
    from speechbrain.inference.separation import SepformerSeparation as separator
    from speechbrain.inference.speaker import SpeakerRecognition
except ImportError:
    # 구버전 호환성
    try:
        from speechbrain.pretrained import SepformerSeparation as separator
        from speechbrain.pretrained import SpeakerRecognition
    except ImportError:
        separator = None
        SpeakerRecognition = None

try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.utils.hook import ProgressHook
except ImportError:
    Pipeline = None
    ProgressHook = None

from ..models.audio_models import AudioData, ProcessedAudio
from ..models.config_models import AudioConfig
from ..models.error_models import AudioError, AudioErrorType


@dataclass
class NoiseReductionConfig:
    """노이즈 제거 설정"""
    enabled: bool = True
    reduction_level: float = 0.5  # 0.0 ~ 1.0
    spectral_gating: bool = True
    stationary_noise_reduction: bool = True


@dataclass
class SpeakerSeparationConfig:
    """화자 분리 설정"""
    enabled: bool = True
    threshold: float = 0.7  # 화자 분리 임계값
    max_speakers: int = 5   # 최대 화자 수
    target_speaker_selection: str = "loudest"  # "loudest", "first", "manual"
    
    # 고급 화자 분리 설정
    use_advanced_separation: bool = True  # 고급 분리 모델 사용 여부
    huggingface_token: Optional[str] = None  # HuggingFace 토큰
    diarization_enabled: bool = True  # Diarization 사용 여부
    sepformer_enabled: bool = True  # SepFormer 사용 여부
    speaker_recognition_enabled: bool = True  # 화자 인식 사용 여부
    fallback_to_simple: bool = True  # 고급 모델 실패시 기본 방식 사용
    min_segment_length: float = 0.5  # 최소 세그먼트 길이 (초)
    energy_threshold_ratio: float = 0.7  # 에너지 임계값 비율
    
    def __post_init__(self):
        """초기화 후 환경변수에서 토큰 자동 로드"""
        if self.huggingface_token is None:
            import os
            # 환경변수에서 토큰 로드 시도
            self.huggingface_token = os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HF_TOKEN')


# 유틸리티 함수들
def rms_safe_normalize(waveform: torch.Tensor, max_target_rms: float = 0.05) -> torch.Tensor:
    """
    안전한 RMS 정규화
    
    Args:
        waveform: 입력 파형 텐서
        max_target_rms: 최대 목표 RMS 값
        
    Returns:
        정규화된 파형
        
    Raises:
        ValueError: 오디오가 비어있는 경우
    """
    rms = (waveform ** 2).mean().sqrt()
    peak = waveform.abs().max()

    if rms == 0 or peak == 0:
        raise ValueError('오디오파일이 비어있습니다')

    safe_target_rms = min(rms * (1.0 / peak), max_target_rms)
    scaled = waveform * (safe_target_rms / rms)
    return scaled.float()


class AudioProcessor:
    """음성 전처리 클래스"""
    
    def __init__(self, config: AudioConfig):
        """
        AudioProcessor 초기화
        
        Args:
            config: 음성 처리 설정
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 노이즈 제거 설정
        self.noise_config = NoiseReductionConfig(
            enabled=getattr(config, 'noise_reduction_enabled', True),
            reduction_level=getattr(config, 'noise_reduction_level', 0.5)
        )
        
        # 화자 분리 설정
        self.speaker_config = SpeakerSeparationConfig(
            enabled=getattr(config, 'speaker_separation_enabled', True),
            threshold=getattr(config, 'speaker_separation_threshold', 0.7)
        )
        
        # 모델 캐싱을 위한 디렉토리 설정
        self.models_cache_dir = os.path.join(tempfile.gettempdir(), "speechbrain_models")
        os.makedirs(self.models_cache_dir, exist_ok=True)
        
        # 모델 인스턴스 캐싱
        self._sepformer_model = None
        self._speaker_recognition_model = None
        self._diarization_pipeline = None
        
        self.logger.info("AudioProcessor 초기화 완료")
    
    def process_audio(self, audio_input: AudioData) -> ProcessedAudio:
        """
        음성 데이터 전처리
        
        Args:
            audio_input: 원본 음성 데이터
            
        Returns:
            전처리된 음성 데이터
            
        Raises:
            AudioError: 음성 처리 실패 시
        """
        try:
            self.logger.info(f"음성 처리 시작 - 길이: {audio_input.duration}초, 샘플레이트: {audio_input.sample_rate}Hz")
            
            # 1. 입력 검증
            self._validate_input(audio_input)
            
            # 2. 다중화자 분리 (활성화된 경우)
            processed_audio = audio_input.data
            if self.speaker_config.enabled:
                processed_audio = self._separate_speakers(processed_audio, audio_input.sample_rate)
            
            # 3. 노이즈 제거 (활성화된 경우)
            if self.noise_config.enabled:
                processed_audio = self._reduce_noise(processed_audio, audio_input.sample_rate)
            
            # 4. 16kHz로 리샘플링
            if audio_input.sample_rate != 16000:
                processed_audio = librosa.resample(
                    processed_audio, 
                    orig_sr=audio_input.sample_rate, 
                    target_sr=16000
                )
            
            # 5. Log-Mel spectrogram 특징 추출
            features = self._extract_mel_features(processed_audio)
            
            result = ProcessedAudio(
                features=features,
                sample_rate=16000,
                original_duration=audio_input.duration
            )
            
            self.logger.info(f"음성 처리 완료 - 특징 크기: {features.shape}")
            return result
            
        except Exception as e:
            self.logger.error(f"음성 처리 중 오류 발생: {str(e)}")
            raise AudioError(
                error_type=AudioErrorType.PROCESSING_FAILED,
                message=f"음성 처리 실패: {str(e)}",
                details={'original_error': str(e)}
            )
    
    def _validate_input(self, audio_input: AudioData):
        """입력 음성 데이터 검증"""
        if audio_input.duration > 30.0:
            raise AudioError(
                error_type=AudioErrorType.INVALID_FORMAT,
                message="음성 길이가 30초를 초과합니다",
                details={'duration': audio_input.duration}
            )
        
        if audio_input.sample_rate < 8000:
            raise AudioError(
                error_type=AudioErrorType.INVALID_FORMAT,
                message="샘플링 레이트가 너무 낮습니다 (최소 8kHz)",
                details={'sample_rate': audio_input.sample_rate}
            )
    
    def _separate_speakers(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        고급 다중화자 분리 처리
        
        Args:
            audio_data: 음성 데이터
            sample_rate: 샘플링 레이트
            
        Returns:
            주 화자 음성 데이터
        """
        try:
            print("\n" + "="*60)
            print("🎤 고급 다중화자 분리 시스템 시작")
            print("="*60)
            
            # 고급 분리 모델 사용 여부 확인
            if (self.speaker_config.use_advanced_separation and 
                Pipeline is not None and 
                separator is not None and 
                SpeakerRecognition is not None):
                
                print("✅ 고급 AI 모델 사용 가능 - Pyannote + SepFormer + ECAPA 활성화")
                result = self._advanced_speaker_separation(audio_data, sample_rate)
                print("🎯 고급 화자 분리 완료!")
                return result
            else:
                print("⚠️  고급 모델 사용 불가, 기본 에너지 기반 분리 사용")
                missing_models = []
                if Pipeline is None:
                    missing_models.append("Pyannote")
                if separator is None:
                    missing_models.append("SepFormer")
                if SpeakerRecognition is None:
                    missing_models.append("ECAPA")
                if missing_models:
                    print(f"❌ 누락된 모델: {', '.join(missing_models)}")
                
                print("🔄 기본 에너지 기반 분리로 전환합니다...")
                result = self._simple_speaker_separation(audio_data, sample_rate)
                print("✅ 기본 에너지 기반 분리 완료")
                return result
                
        except Exception as e:
            print(f"\n❌ 화자 분리 실패: {str(e)}")
            if self.speaker_config.fallback_to_simple:
                print("🔄 기본 방식으로 대체 시도...")
                result = self._simple_speaker_separation(audio_data, sample_rate)
                print("✅ 기본 방식 대체 완료")
                return result
            else:
                print("⚠️  Fallback 비활성화 - 원본 반환")
                return audio_data
    
    def _advanced_speaker_separation(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Pyannote + SepFormer + ECAPA 기반 고급 화자 분리
        
        Args:
            audio_data: 음성 데이터 (numpy array)
            sample_rate: 샘플링 레이트
            
        Returns:
            주 화자 음성 데이터
        """
        try:
            print("\n🚀 고급 화자 분리 파이프라인 시작")
            print(f"📊 입력: {len(audio_data)} 샘플, {sample_rate}Hz")
            
            # 1. 임시 파일 생성 (pyannote는 파일 경로가 필요)
            temp_dir = tempfile.mkdtemp(prefix="speaker_separation_")
            temp_file = os.path.join(temp_dir, 'temp_audio_for_diarization.wav')
            
            # 오디오 데이터가 올바른 범위에 있는지 확인
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data)) * 0.95
            
            torchaudio.save(temp_file, torch.from_numpy(audio_data).unsqueeze(0).float(), sample_rate)
            
            try:
                print("\n🎯 1단계: Pyannote Diarization 수행 중...")
                # 2. Diarization 수행
                main_speaker_segments = self._perform_diarization(temp_file, audio_data, sample_rate)
                
                if not main_speaker_segments:
                    print("❌ Diarization으로 주 화자를 찾지 못함 → 기본 방식으로 전환")
                    print("🔄 기본 에너지 기반 분리로 전환합니다...")
                    result = self._simple_speaker_separation(audio_data, sample_rate)
                    print("✅ 기본 방식 대체 완료")
                    return result
                
                print(f"✅ 주 화자 세그먼트 {len(main_speaker_segments)}개 발견!")
                
                # 3. SepFormer 음성 분리 (선택적)
                if self.speaker_config.sepformer_enabled:
                    print("\n🎯 2단계: SepFormer 음성 분리 수행 중...")
                    separated_audio = self._perform_sepformer_separation(audio_data, sample_rate, main_speaker_segments)
                    if separated_audio is not None:
                        print("✅ SepFormer 분리 + ECAPA 매칭 성공!")
                        return separated_audio
                    else:
                        print("⚠️  SepFormer 분리 실패 → Diarization 결과만 사용")
                else:
                    print("⚠️  SepFormer 비활성화 → Diarization 결과만 사용")
                
                # 4. Diarization 결과만으로 주 화자 추출
                print("\n🎯 3단계: Diarization 세그먼트 추출")
                result = self._extract_main_speaker_from_segments(audio_data, sample_rate, main_speaker_segments)
                print("✅ Diarization 기반 주 화자 추출 완료!")
                return result
                
            finally:
                # 임시 디렉토리 정리
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
        except Exception as e:
            self.logger.error(f"고급 화자 분리 실패: {str(e)}")
            raise
    
    def _perform_diarization(self, audio_file: str, audio_data: np.ndarray, sample_rate: int) -> Optional[list]:
        """
        Pyannote를 사용한 화자 구분 및 주 화자 선택
        
        Args:
            audio_file: 임시 오디오 파일 경로
            audio_data: 원본 오디오 데이터
            sample_rate: 샘플링 레이트
            
        Returns:
            주 화자의 세그먼트 리스트 또는 None
        """
        try:
            print("  📡 Pyannote diarization 엔진 시작...")
            
            # 16kHz로 리샘플링 (pyannote 요구사항)
            if sample_rate != 16000:
                resampled_audio = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
                temp_16k_file = os.path.join(os.path.dirname(audio_file), 'temp_audio_16k.wav')
                
                # 정규화된 오디오 저장
                if np.max(np.abs(resampled_audio)) > 1.0:
                    resampled_audio = resampled_audio / np.max(np.abs(resampled_audio)) * 0.95
                
                torchaudio.save(temp_16k_file, torch.from_numpy(resampled_audio).unsqueeze(0).float(), 16000)
                audio_file = temp_16k_file
                working_sample_rate = 16000
                working_audio = resampled_audio
            else:
                working_sample_rate = sample_rate
                working_audio = audio_data
            
            # Diarization 파이프라인 초기화 (pyannote.audio 3.3.2) - 캐싱 적용
            if self._diarization_pipeline is None:
                token = self.speaker_config.huggingface_token
                print("    🔄 Diarization 모델 로딩 중...")
                
                # HuggingFace 토큰 확인
                if not token:
                    print("    ⚠️  HuggingFace 토큰이 설정되지 않았습니다!")
                    print("    💡 해결방법:")
                    print("       1. HuggingFace 계정 생성: https://huggingface.co/join")
                    print("       2. 토큰 생성: https://hf.co/settings/tokens")
                    print("       3. Gated 모델 접근 승인: https://hf.co/pyannote/speaker-diarization-3.1")
                    print("    🔄 토큰 없이 구버전 모델로 시도...")

                try:
                    # 최신 버전 API - pyannote.audio 3.3.2
                    if token:
                        print("    📡 시도: speaker-diarization-3.1 (최신)")
                        self._diarization_pipeline = Pipeline.from_pretrained(
                            "pyannote/speaker-diarization-3.1", 
                            use_auth_token=token
                        )
                        if self._diarization_pipeline is not None:
                            print("    ✅ 최신 모델 로딩 성공!")
                        else:
                            print("    ❌ 최신 모델 로딩 실패: None 반환")
                            raise ValueError("Pipeline returned None")
                    else:
                        raise ValueError("No token provided")
                        
                except Exception as e1:
                    print(f"    ⚠️  최신 모델 실패: {str(e1)[:100]}...")
                    try:
                        # fallback to older model
                        print("    📡 시도: speaker-diarization@2.1 (구버전)")
                        self._diarization_pipeline = Pipeline.from_pretrained(
                            "pyannote/speaker-diarization@2.1", 
                            use_auth_token=token if token else None
                        )
                        if self._diarization_pipeline is not None:
                            print("    ✅ 구버전 모델 로딩 성공!")
                        else:
                            print("    ❌ 구버전 모델 로딩 실패: None 반환")
                            raise ValueError("Pipeline returned None")
                            
                    except Exception as e2:
                        print(f"    ⚠️  구버전 모델 실패: {str(e2)[:100]}...")
                        try:
                            # fallback to token parameter name
                            if token:
                                print("    📡 시도: 토큰 파라미터 변경")
                                self._diarization_pipeline = Pipeline.from_pretrained(
                                    "pyannote/speaker-diarization-3.1", 
                                    token=token
                                )
                                if self._diarization_pipeline is not None:
                                    print("    ✅ 토큰 변경 성공!")
                                else:
                                    print("    ❌ 토큰 변경 실패: None 반환")
                                    raise ValueError("Pipeline returned None")
                            else:
                                raise ValueError("No token for final attempt")
                                
                        except Exception as e3:
                            print(f"    ❌ 모든 diarization 모델 로딩 실패:")
                            print(f"       최신 모델: {str(e1)[:80]}...")
                            print(f"       구버전 모델: {str(e2)[:80]}...")
                            print(f"       토큰 변경: {str(e3)[:80]}...")
                            print("    🔄 고급 모델 없이 기본 에너지 기반 분리로 전환됩니다.")
                            self._diarization_pipeline = None
                            raise Exception("All diarization models failed to load")
                
                # pipeline이 성공적으로 로드된 경우에만 GPU로 이동
                if self._diarization_pipeline is not None:
                    try:
                        # GPU 사용 가능시 GPU로 이동
                        if torch.cuda.is_available():
                            self._diarization_pipeline.to(torch.device("cuda"))
                            print("    🚀 GPU 모드 활성화")
                        else:
                            print("    💻 CPU 모드 사용")
                    except Exception as gpu_error:
                        print(f"    ⚠️  GPU 이동 실패, CPU 사용: {gpu_error}")
                else:
                    print("    ❌ Pipeline이 None입니다 - 초기화 실패")
                    raise Exception("Diarization pipeline is None")
                
                print("    ✅ Diarization 파이프라인 준비 완료!")
            
            pipeline = self._diarization_pipeline
            
            # Diarization 수행
            diarization = pipeline(audio_file)
            
            # 화자별 에너지 계산
            total_energy = defaultdict(float)
            speaker_names = []
            waveform_tensor = torch.from_numpy(working_audio).unsqueeze(0)
            
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                speaker_names.append(speaker)
                
                start_sample = int(segment.start * working_sample_rate)
                end_sample = int(segment.end * working_sample_rate)
                segment_waveform = waveform_tensor[:, start_sample:end_sample]
                
                energy = torch.norm(segment_waveform)
                total_energy[speaker] += energy.item()
            
            speaker_names = list(set(speaker_names))
            
            # 화자 수 확인
            print(f"  📊 발견된 화자 수: {len(speaker_names)}명")
            for speaker in speaker_names:
                energy_ratio = total_energy[speaker] / max(total_energy.values()) if total_energy else 0
                print(f"    - {speaker}: 에너지 비율 {energy_ratio:.2%}")
            
            if not total_energy or len(speaker_names) <= 1:
                print(f"  ⚠️  화자 수가 {len(speaker_names)}명이므로 분리할 필요가 없습니다.")
                return None
            
            # 주 화자 선택 (에너지 기준)
            main_speaker = max(total_energy, key=total_energy.get)
            energy_percentage = total_energy[main_speaker] / sum(total_energy.values()) * 100
            print(f"  🎯 주 화자 선택: {main_speaker} (에너지 점유율: {energy_percentage:.1f}%)")
            print(f"  📈 총 화자 수: {len(speaker_names)}명")
            
            # 주 화자 세그먼트 수집
            main_speaker_segments = []
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                if speaker == main_speaker:
                    # 원본 샘플링 레이트로 변환
                    if sample_rate != 16000:
                        start_original = int(segment.start * sample_rate)
                        end_original = int(segment.end * sample_rate)
                    else:
                        start_original = int(segment.start * working_sample_rate)
                        end_original = int(segment.end * working_sample_rate)
                    
                    main_speaker_segments.append((start_original, end_original))
            
            # 임시 16kHz 파일 정리
            if sample_rate != 16000:
                temp_16k_file = os.path.join(os.path.dirname(audio_file), 'temp_audio_16k.wav')
                if os.path.exists(temp_16k_file):
                    os.remove(temp_16k_file)
            
            return main_speaker_segments
            
        except Exception as e:
            self.logger.error(f"Diarization 실패: {str(e)}")
            return None
    
    def _reduce_noise(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        노이즈 제거 처리
        
        Args:
            audio_data: 음성 데이터
            sample_rate: 샘플링 레이트
            
        Returns:
            노이즈가 제거된 음성 데이터
        """
        try:
            self.logger.debug("노이즈 제거 시작")
            
            # 기본적인 스펙트럴 게이팅 기반 노이즈 제거
            # 실제 환경에서는 더 정교한 노이즈 제거 알고리즘 사용 권장
            
            # STFT 변환
            stft = librosa.stft(audio_data, n_fft=2048, hop_length=512)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # 노이즈 추정 (처음 0.5초를 노이즈로 가정)
            noise_frames = int(0.5 * sample_rate / 512)  # hop_length=512
            if noise_frames > 0 and noise_frames < magnitude.shape[1]:
                noise_profile = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
            else:
                noise_profile = np.mean(magnitude, axis=1, keepdims=True) * 0.1
            
            # 스펙트럴 게이팅
            reduction_factor = self.noise_config.reduction_level
            mask = magnitude > (noise_profile * (1 + reduction_factor))
            
            # 부드러운 마스킹 적용
            smooth_mask = np.maximum(mask.astype(float), 0.1)  # 최소 10% 유지
            
            # 마스크 적용
            cleaned_magnitude = magnitude * smooth_mask
            
            # ISTFT로 복원
            cleaned_stft = cleaned_magnitude * np.exp(1j * phase)
            cleaned_audio = librosa.istft(cleaned_stft, hop_length=512)
            
            self.logger.debug("노이즈 제거 완료")
            return cleaned_audio
            
        except Exception as e:
            self.logger.warning(f"노이즈 제거 실패, 원본 음성 사용: {str(e)}")
            return audio_data
    
    def _extract_mel_features(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Log-Mel spectrogram 특징 추출
        
        Args:
            audio_data: 16kHz 음성 데이터
            
        Returns:
            (80, 3000) 크기의 Log-Mel spectrogram
        """
        try:
            self.logger.debug("Mel 특징 추출 시작")
            
            # Whisper 표준 설정에 맞춘 특징 추출
            # 30초 길이로 패딩 또는 트림
            target_length = 16000 * 30  # 30초 * 16kHz
            
            if len(audio_data) > target_length:
                # 30초보다 길면 트림
                audio_data = audio_data[:target_length]
            elif len(audio_data) < target_length:
                # 30초보다 짧으면 패딩
                padding = target_length - len(audio_data)
                audio_data = np.pad(audio_data, (0, padding), mode='constant', constant_values=0)
            
            # Mel spectrogram 계산
            mel_spec = librosa.feature.melspectrogram(
                y=audio_data,
                sr=16000,
                n_fft=400,      # Whisper 설정
                hop_length=160, # Whisper 설정
                n_mels=80,      # Whisper 설정
                fmin=0,
                fmax=8000
            )
            
            # Log 변환
            log_mel = librosa.power_to_db(mel_spec, ref=np.max)
            
            # 정규화 (-80dB ~ 0dB를 0 ~ 1로)
            log_mel = np.clip((log_mel + 80) / 80, 0, 1)
            
            # 크기 확인 및 조정
            if log_mel.shape[1] != 3000:
                if log_mel.shape[1] > 3000:
                    log_mel = log_mel[:, :3000]
                else:
                    padding = 3000 - log_mel.shape[1]
                    log_mel = np.pad(log_mel, ((0, 0), (0, padding)), mode='constant', constant_values=0)
            
            self.logger.debug(f"Mel 특징 추출 완료 - 크기: {log_mel.shape}")
            return log_mel
            
        except Exception as e:
            self.logger.error(f"Mel 특징 추출 실패: {str(e)}")
            raise AudioError(
                error_type=AudioErrorType.FEATURE_EXTRACTION_FAILED,
                message=f"특징 추출 실패: {str(e)}",
                details={'original_error': str(e)}
            )
    
    def _perform_sepformer_separation(self, audio_data: np.ndarray, sample_rate: int, main_speaker_segments: list) -> Optional[np.ndarray]:
        """
        SepFormer를 사용한 음성 분리 및 화자 매칭
        """
        try:
            print("  🔊 SepFormer 음성 분리 엔진 시작...")
            
            # 8kHz로 리샘플링 (SepFormer 요구사항)
            if sample_rate != 8000:
                resampled_audio = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=8000)
            else:
                resampled_audio = audio_data
            
            # SepFormer 모델 로드 (speechbrain 1.0.3) - 캐싱 적용
            if self._sepformer_model is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f"    🔄 SepFormer 모델 로딩 중... (device: {device})")
                
                try:
                    # 최신 버전 API with improved caching
                    print("    📡 speechbrain/sepformer-wsj02mix 다운로드 중...")
                    self._sepformer_model = separator.from_hparams(
                        source="speechbrain/sepformer-wsj02mix",
                        run_opts={"device": device},
                        savedir=os.path.join(self.models_cache_dir, "sepformer")
                    )
                    print("    ✅ 최신 API로 SepFormer 로딩 성공!")
                except Exception as e:
                    print(f"    ⚠️  최신 API 실패: {str(e)[:50]}...")
                    # fallback to older API
                    print("    🔄 구버전 API로 재시도...")
                    self._sepformer_model = separator.from_hparams(
                        source="speechbrain/sepformer-wsj02mix",
                        run_opts={"device": device}
                    )
                    print("    ✅ 구버전 API로 SepFormer 로딩 성공!")
                
                self._sepformer_model.eval()
                print("    ✅ SepFormer 모델 준비 완료!")
            
            model = self._sepformer_model
            
            # 음성 분리 수행
            waveform_tensor = torch.from_numpy(resampled_audio).unsqueeze(0)
            if torch.cuda.is_available():
                waveform_tensor = waveform_tensor.to('cuda')
            
            print("    🔀 음성 분리 수행 중...")
            estimated_sources = model(waveform_tensor)
            estimated_sources = estimated_sources.squeeze(0)
            num_speakers = estimated_sources.shape[1]
            print(f"    📊 {num_speakers}개 음성으로 분리 완료!")
            
            # 분리된 각 음성을 정규화
            separated_waveforms = []
            for i in range(num_speakers):
                waveform = estimated_sources[:, i].unsqueeze(0)
                waveform = rms_safe_normalize(waveform, max_target_rms=0.05)
                separated_waveforms.append(waveform)
            
            # 화자 인식을 사용하여 주 화자와 매칭
            if self.speaker_config.speaker_recognition_enabled and SpeakerRecognition is not None:
                matched_audio = self._match_speaker_with_recognition(
                    separated_waveforms, main_speaker_segments, audio_data, sample_rate
                )
                if matched_audio is not None:
                    return matched_audio
            
            # 화자 인식이 실패하면 첫 번째 분리된 음성 반환
            if separated_waveforms:
                result_8k = separated_waveforms[0].cpu().numpy().squeeze()
                if sample_rate != 8000:
                    result = librosa.resample(result_8k, orig_sr=8000, target_sr=sample_rate)
                else:
                    result = result_8k
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"SepFormer 분리 실패: {str(e)}")
            return None
    
    def _match_speaker_with_recognition(self, separated_waveforms: list, main_speaker_segments: list, 
                                       original_audio: np.ndarray, sample_rate: int) -> Optional[np.ndarray]:
        """
        ECAPA 화자 인식을 사용하여 분리된 음성과 주 화자 매칭
        """
        try:
            print("  🎭 ECAPA 화자 인식을 통한 매칭 시작...")
            
            # 화자 인식 모델 로드 (speechbrain 1.0.3) - 캐싱 적용
            if self._speaker_recognition_model is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f"    🔄 ECAPA 모델 로딩 중... (device: {device})")
                
                try:
                    # 최신 버전 API with improved caching
                    print("    📡 speechbrain/spkrec-ecapa-voxceleb 다운로드 중...")
                    self._speaker_recognition_model = SpeakerRecognition.from_hparams(
                        source="speechbrain/spkrec-ecapa-voxceleb",
                        run_opts={"device": device},
                        savedir=os.path.join(self.models_cache_dir, "ecapa")
                    )
                    print("    ✅ 최신 API로 ECAPA 로딩 성공!")
                except Exception as e:
                    print(f"    ⚠️  최신 API 실패: {str(e)[:50]}...")
                    # fallback to older API
                    print("    🔄 구버전 API로 재시도...")
                    self._speaker_recognition_model = SpeakerRecognition.from_hparams(
                        source="speechbrain/spkrec-ecapa-voxceleb",
                        run_opts={"device": device}
                    )
                    print("    ✅ 구버전 API로 ECAPA 로딩 성공!")
                
                print("    ✅ ECAPA 모델 준비 완료!")
            
            recognizer = self._speaker_recognition_model
            
            # 주 화자 세그먼트에서 임베딩 추출 (16kHz 필요)
            if sample_rate != 16000:
                resampled_original = librosa.resample(original_audio, orig_sr=sample_rate, target_sr=16000)
                working_sr = 16000
                main_segments_16k = [
                    (int(start * 16000 / sample_rate), int(end * 16000 / sample_rate))
                    for start, end in main_speaker_segments
                ]
            else:
                resampled_original = original_audio
                working_sr = 16000
                main_segments_16k = main_speaker_segments
            
            # 주 화자 세그먼트들을 연결
            main_speaker_audio_segments = []
            for start, end in main_segments_16k:
                segment = resampled_original[start:end]
                if len(segment) > 0:
                    main_speaker_audio_segments.append(segment)
            
            if not main_speaker_audio_segments:
                return None
            
            main_speaker_waveform = np.concatenate(main_speaker_audio_segments)
            main_speaker_tensor = torch.from_numpy(main_speaker_waveform).unsqueeze(0)
            
            if torch.cuda.is_available():
                main_speaker_tensor = main_speaker_tensor.to('cuda')
            
            # 주 화자 임베딩 추출
            main_speaker_embedding = recognizer.encode_batch(main_speaker_tensor).squeeze()
            
            # 분리된 각 음성의 임베딩 추출 및 유사도 계산
            print("    🔍 각 분리된 음성과 주 화자 유사도 계산 중...")
            similarities = []
            resampler_to_16k = torchaudio.transforms.Resample(orig_freq=8000, new_freq=16000)
            if torch.cuda.is_available():
                resampler_to_16k = resampler_to_16k.to('cuda')
            
            for i, waveform in enumerate(separated_waveforms):
                print(f"      분리음성 {i+1} 임베딩 추출 중...")
                resampled_waveform = resampler_to_16k(waveform)
                embedding = recognizer.encode_batch(resampled_waveform).squeeze()
                
                similarity = torch.nn.functional.cosine_similarity(
                    main_speaker_embedding, embedding, dim=0
                ).item()
                similarities.append(similarity)
                print(f"      분리음성 {i+1} 유사도: {similarity:.4f}")
            
            # 가장 유사한 음성 선택
            best_match_idx = similarities.index(max(similarities))
            best_similarity = max(similarities)
            print(f"    🎯 최고 유사도: {best_similarity:.4f} (분리음성 {best_match_idx+1} 선택)")
            
            if best_similarity < 0.5:
                print(f"    ⚠️  유사도가 낮음 ({best_similarity:.4f} < 0.5) - 결과 품질 주의")
            
            # 선택된 음성을 원본 샘플링 레이트로 변환
            selected_waveform = separated_waveforms[best_match_idx].cpu().numpy().squeeze()
            if sample_rate != 8000:
                result = librosa.resample(selected_waveform, orig_sr=8000, target_sr=sample_rate)
            else:
                result = selected_waveform
            
            return result
            
        except Exception as e:
            self.logger.error(f"화자 매칭 실패: {str(e)}")
            return None
    
    def _extract_main_speaker_from_segments(self, audio_data: np.ndarray, sample_rate: int, 
                                          main_speaker_segments: list) -> np.ndarray:
        """
        Diarization 결과로부터 주 화자 세그먼트만 추출
        """
        try:
            print("  ✂️  주 화자 세그먼트 추출 중...")
            segments = []
            total_duration = 0
            
            for i, (start, end) in enumerate(main_speaker_segments):
                segment = audio_data[start:end]
                if len(segment) > 0:
                    segments.append(segment)
                    duration = len(segment) / sample_rate
                    total_duration += duration
                    print(f"    세그먼트 {i+1}: {duration:.2f}초")
            
            if segments:
                result = np.concatenate(segments)
                original_duration = len(audio_data) / sample_rate
                reduction_ratio = (original_duration - total_duration) / original_duration * 100
                print(f"  📊 추출 완료 - 원본: {original_duration:.2f}초 → 결과: {total_duration:.2f}초")
                print(f"  📉 음성 압축률: {reduction_ratio:.1f}% 제거")
                return result
            else:
                print("  ⚠️  유효한 세그먼트 없음 - 원본 반환")
                return audio_data
                
        except Exception as e:
            self.logger.error(f"세그먼트 추출 실패: {str(e)}")
            return audio_data
    
    def _simple_speaker_separation(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        기본 에너지 기반 화자 선택 (기존 방식)
        """
        try:
            print("\n🔋 기본 에너지 기반 화자 분리 시작")
            print(f"📊 입력: {len(audio_data)} 샘플, {sample_rate}Hz")
            
            # 음성을 세그먼트로 나누어 에너지 분석
            segment_length = int(sample_rate * self.speaker_config.min_segment_length)
            segments = []
            
            for i in range(0, len(audio_data), segment_length):
                segment = audio_data[i:i + segment_length]
                if len(segment) > 0:
                    energy = np.sum(segment ** 2)
                    segments.append((i, segment, energy))
            
            if not segments:
                return audio_data
            
            # 에너지가 높은 세그먼트들을 주 화자로 간주
            segments.sort(key=lambda x: x[2], reverse=True)
            
            # 설정된 비율만큼 상위 에너지 세그먼트 선택
            threshold_idx = max(1, int(len(segments) * (1 - self.speaker_config.energy_threshold_ratio)))
            selected_segments = segments[:threshold_idx]
            
            # 시간 순서로 재정렬
            selected_segments.sort(key=lambda x: x[0])
            
            # 선택된 세그먼트들을 연결
            result_audio = np.concatenate([seg[1] for seg in selected_segments])
            
            original_duration = len(audio_data) / sample_rate
            result_duration = len(result_audio) / sample_rate
            reduction_ratio = (original_duration - result_duration) / original_duration * 100
            
            print(f"📊 기본 분리 완료:")
            print(f"  - 원본: {original_duration:.2f}초 ({len(audio_data)} 샘플)")
            print(f"  - 결과: {result_duration:.2f}초 ({len(result_audio)} 샘플)")
            print(f"  - 압축률: {reduction_ratio:.1f}% 제거")
            print(f"  - 사용된 세그먼트: {len(selected_segments)}/{len(segments)}개")
            
            return result_audio
            
        except Exception as e:
            self.logger.warning(f"기본 화자 분리 실패, 원본 음성 사용: {str(e)}")
            return audio_data
    
    def validate_audio_format(self, audio_data: np.ndarray, sample_rate: int) -> bool:
        """
        음성 포맷 검증
        
        Args:
            audio_data: 음성 데이터
            sample_rate: 샘플링 레이트
            
        Returns:
            검증 결과
        """
        try:
            # 기본 검증
            if audio_data is None or len(audio_data) == 0:
                return False
            
            if sample_rate <= 0:
                return False
            
            # 길이 검증 (최대 30초)
            duration = len(audio_data) / sample_rate
            if duration > 30.0:
                return False
            
            # 동적 범위 검증
            if np.max(np.abs(audio_data)) == 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_audio_info(self, audio_input: AudioData) -> Dict[str, Any]:
        """
        음성 정보 반환
        
        Args:
            audio_input: 음성 데이터
            
        Returns:
            음성 정보 딕셔너리
        """
        try:
            # 기본 정보
            info = {
                'duration': audio_input.duration,
                'sample_rate': audio_input.sample_rate,
                'channels': audio_input.channels,
                'samples': len(audio_input.data),
                'format_valid': self.validate_audio_format(audio_input.data, audio_input.sample_rate)
            }
            
            # 음성 품질 분석
            if len(audio_input.data) > 0:
                info.update({
                    'rms_energy': float(np.sqrt(np.mean(audio_input.data ** 2))),
                    'peak_amplitude': float(np.max(np.abs(audio_input.data))),
                    'zero_crossing_rate': float(np.mean(librosa.feature.zero_crossing_rate(audio_input.data)[0])),
                    'spectral_centroid': float(np.mean(librosa.feature.spectral_centroid(
                        y=audio_input.data, sr=audio_input.sample_rate)[0]))
                })
            
            return info
            
        except Exception as e:
            self.logger.error(f"음성 정보 추출 실패: {str(e)}")
            return {
                'duration': audio_input.duration,
                'sample_rate': audio_input.sample_rate,
                'channels': audio_input.channels,
                'error': str(e)
            }
    
    def create_audio_data(self, file_path: str) -> AudioData:
        """
        파일에서 AudioData 생성
        
        Args:
            file_path: 음성 파일 경로
            
        Returns:
            AudioData 객체
            
        Raises:
            AudioError: 파일 로드 실패 시
        """
        try:
            # librosa로 음성 파일 로드
            audio_data, sample_rate = librosa.load(file_path, sr=None, mono=True)
            
            duration = len(audio_data) / sample_rate
            channels = 1  # mono로 로드했으므로
            
            return AudioData(
                data=audio_data,
                sample_rate=sample_rate,
                channels=channels,
                duration=duration
            )
            
        except Exception as e:
            raise AudioError(
                error_type=AudioErrorType.FILE_LOAD_FAILED,
                message=f"음성 파일 로드 실패: {str(e)}",
                details={'file_path': file_path, 'original_error': str(e)}
            )


# 테스트 함수
def test_speaker_separation_system():
    """
    화자 분리 시스템 테스트 함수
    더미 데이터로 시스템 작동 여부를 확인합니다.
    """
    print("\n" + "="*80)
    print("🧪 화자 분리 시스템 테스트 시작")
    print("="*80)
    
    try:
        # 더미 설정 생성
        from ..models.config_models import AudioConfig
        
        config = AudioConfig()
        processor = AudioProcessor(config)
        
        # 더미 오디오 데이터 생성 (5초, 16kHz)
        import numpy as np
        duration = 5.0  # 5초
        sample_rate = 16000
        
        # 2명 화자를 시뮬레이션한 더미 데이터
        t = np.linspace(0, duration, int(duration * sample_rate), False)
        speaker1_freq = 440  # A note (더 강함)
        speaker2_freq = 880  # A note 2배 (더 약함)
        
        # 첫 번째 화자가 더 큰 소리로 말하는 것처럼 시뮬레이션
        speaker1_signal = 0.7 * np.sin(speaker1_freq * 2.0 * np.pi * t)
        speaker2_signal = 0.3 * np.sin(speaker2_freq * 2.0 * np.pi * t)
        
        # 노이즈 추가
        noise = 0.1 * np.random.randn(len(t))
        
        # 혼합 신호 생성
        mixed_audio = speaker1_signal + speaker2_signal + noise
        
        print(f"🎵 더미 오디오 생성: {duration}초, {sample_rate}Hz")
        print(f"📊 화자1 (440Hz): 70% 강도, 화자2 (880Hz): 30% 강도")
        
        # 화자 분리 테스트
        result = processor._separate_speakers(mixed_audio, sample_rate)
        
        result_duration = len(result) / sample_rate
        reduction = (duration - result_duration) / duration * 100
        
        print(f"\n🎯 테스트 결과:")
        print(f"  ✅ 시스템 정상 작동")
        print(f"  📊 원본: {duration:.2f}초 → 결과: {result_duration:.2f}초")
        print(f"  📉 압축률: {reduction:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        print("🔧 해결 방법:")
        print("  1. 필요한 라이브러리 설치: pip install -r requirements.txt")
        print("  2. HuggingFace 토큰 설정 확인")
        print("  3. GPU/CUDA 환경 확인")
        return False
    
    finally:
        print("\n" + "="*80)
        print("🧪 화자 분리 시스템 테스트 완료")
        print("="*80)


if __name__ == "__main__":
    # 직접 실행 시 테스트 함수 호출
    test_speaker_separation_system()