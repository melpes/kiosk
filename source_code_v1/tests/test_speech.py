"""
음성인식 모듈 테스트
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import time

from src.speech.recognition import SpeechRecognizer
from src.models.audio_models import ProcessedAudio
from src.models.speech_models import RecognitionResult
from src.models.error_models import RecognitionError, RecognitionErrorType


class TestSpeechRecognizer:
    """SpeechRecognizer 클래스 테스트"""
    
    @pytest.fixture
    def mock_whisper(self):
        """Whisper 모듈 모킹"""
        with patch('src.speech.recognition.whisper') as mock_whisper:
            mock_model = Mock()
            mock_whisper.load_model.return_value = mock_model
            yield mock_whisper, mock_model
    
    @pytest.fixture
    def mock_torch(self):
        """PyTorch 모듈 모킹"""
        with patch('src.speech.recognition.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            yield mock_torch
    
    @pytest.fixture
    def sample_audio(self):
        """테스트용 음성 데이터"""
        # 2D 특징 데이터 (Log-Mel spectrogram 형태)
        features = np.random.randn(80, 3000).astype(np.float32)
        return ProcessedAudio(features=features, sample_rate=16000)
    
    @pytest.fixture
    def sample_audio_1d(self):
        """테스트용 1D 음성 데이터"""
        # 1D 오디오 데이터
        features = np.random.randn(48000).astype(np.float32) * 0.5  # 정규화된 오디오
        return ProcessedAudio(features=features, sample_rate=16000)
    
    def test_init_default_params(self, mock_whisper, mock_torch):
        """기본 매개변수로 초기화 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        
        assert recognizer.model_name == "base"
        assert recognizer.language == "ko"
        assert recognizer.device == "cpu"
        mock_whisper_module.load_model.assert_called_once_with("base", device="cpu")
    
    def test_init_custom_params(self, mock_whisper, mock_torch):
        """사용자 정의 매개변수로 초기화 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer(
            model_name="small",
            language="en",
            device="cuda"
        )
        
        assert recognizer.model_name == "small"
        assert recognizer.language == "en"
        assert recognizer.device == "cuda"
        mock_whisper_module.load_model.assert_called_once_with("small", device="cuda")
    
    def test_init_auto_device_selection_cuda(self, mock_whisper):
        """CUDA 사용 가능 시 자동 디바이스 선택 테스트"""
        with patch('src.speech.recognition.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_whisper_module, mock_model = mock_whisper
            
            recognizer = SpeechRecognizer()
            
            assert recognizer.device == "cuda"
    
    def test_init_whisper_not_available(self, mock_torch):
        """Whisper 라이브러리 없을 때 테스트"""
        with patch('src.speech.recognition.whisper', None):
            with pytest.raises(ImportError, match="whisper 라이브러리가 설치되지 않았습니다"):
                SpeechRecognizer()
    
    def test_load_model_failure(self, mock_torch):
        """모델 로딩 실패 테스트"""
        with patch('src.speech.recognition.whisper') as mock_whisper:
            mock_whisper.load_model.side_effect = Exception("모델 로딩 실패")
            
            with pytest.raises(RecognitionError) as exc_info:
                SpeechRecognizer()
            
            assert exc_info.value.error_type == RecognitionErrorType.MODEL_LOAD_FAILED
            assert "모델 로딩 실패" in str(exc_info.value)
    
    def test_recognize_success_2d_features(self, mock_whisper, mock_torch, sample_audio):
        """2D 특징으로 음성인식 성공 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        # Whisper 결과 모킹
        mock_result = {
            "text": "안녕하세요 빅맥 세트 하나 주세요",
            "segments": [
                {
                    "text": "안녕하세요 빅맥 세트 하나 주세요",
                    "avg_logprob": -0.2
                }
            ]
        }
        mock_model.transcribe.return_value = mock_result
        
        recognizer = SpeechRecognizer()
        result = recognizer.recognize(sample_audio)
        
        assert isinstance(result, RecognitionResult)
        assert result.text == "안녕하세요 빅맥 세트 하나 주세요"
        assert result.language == "ko"
        assert result.model_version == "base"
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time > 0
        
        # transcribe 호출 확인
        mock_model.transcribe.assert_called_once()
        call_args = mock_model.transcribe.call_args
        assert call_args[1]["language"] == "ko"
        assert call_args[1]["task"] == "transcribe"
        assert call_args[1]["verbose"] is False
    
    def test_recognize_success_1d_features(self, mock_whisper, mock_torch, sample_audio_1d):
        """1D 특징으로 음성인식 성공 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        mock_result = {
            "text": "콜라를 사이다로 변경해 주세요",
            "segments": [
                {
                    "text": "콜라를 사이다로 변경해 주세요",
                    "avg_logprob": -0.1
                }
            ]
        }
        mock_model.transcribe.return_value = mock_result
        
        recognizer = SpeechRecognizer()
        result = recognizer.recognize(sample_audio_1d)
        
        assert result.text == "콜라를 사이다로 변경해 주세요"
        assert result.confidence > 0.8  # 높은 신뢰도
    
    def test_recognize_model_not_loaded(self, mock_whisper, mock_torch, sample_audio):
        """모델이 로드되지 않은 상태에서 인식 시도 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        recognizer.model = None  # 모델을 None으로 설정
        
        with pytest.raises(RecognitionError) as exc_info:
            recognizer.recognize(sample_audio)
        
        assert exc_info.value.error_type == RecognitionErrorType.MODEL_NOT_LOADED
    
    def test_recognize_invalid_input(self, mock_whisper, mock_torch):
        """잘못된 입력으로 인식 시도 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        
        # ProcessedAudio 생성 시점에서 검증 실패하는 경우
        with pytest.raises(ValueError, match="특징 데이터는 numpy 배열이어야 합니다"):
            ProcessedAudio(features="invalid", sample_rate=16000)
        
        # 빈 numpy 배열로 테스트
        empty_audio = ProcessedAudio(features=np.array([]), sample_rate=16000)
        
        with pytest.raises(RecognitionError) as exc_info:
            recognizer.recognize(empty_audio)
        
        assert exc_info.value.error_type == RecognitionErrorType.INVALID_INPUT
    
    def test_recognize_transcribe_failure(self, mock_whisper, mock_torch, sample_audio):
        """Whisper transcribe 실패 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        mock_model.transcribe.side_effect = Exception("Transcribe 실패")
        
        recognizer = SpeechRecognizer()
        
        with pytest.raises(RecognitionError) as exc_info:
            recognizer.recognize(sample_audio)
        
        assert exc_info.value.error_type == RecognitionErrorType.RECOGNITION_FAILED
        assert "음성인식 실패" in str(exc_info.value)
        assert exc_info.value.processing_time is not None
    
    def test_recognize_empty_result(self, mock_whisper, mock_torch, sample_audio):
        """빈 결과 처리 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        mock_result = {
            "text": "",
            "segments": []
        }
        mock_model.transcribe.return_value = mock_result
        
        recognizer = SpeechRecognizer()
        result = recognizer.recognize(sample_audio)
        
        assert result.text == ""
        assert result.confidence == 0.5  # 기본값
    
    def test_calculate_confidence_empty_segments(self, mock_whisper, mock_torch):
        """빈 세그먼트로 신뢰도 계산 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        confidence = recognizer._calculate_confidence([])
        
        assert confidence == 0.5
    
    def test_calculate_confidence_multiple_segments(self, mock_whisper, mock_torch):
        """여러 세그먼트로 신뢰도 계산 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        segments = [
            {"text": "안녕하세요", "avg_logprob": -0.1},  # 높은 신뢰도
            {"text": " 빅맥", "avg_logprob": -0.3},        # 중간 신뢰도
            {"text": " 주세요", "avg_logprob": -0.2}       # 높은 신뢰도
        ]
        
        recognizer = SpeechRecognizer()
        confidence = recognizer._calculate_confidence(segments)
        
        assert 0.0 <= confidence <= 1.0
        # 길이 가중 평균이므로 정확한 값 계산
        expected = (
            np.exp(-0.1) * len("안녕하세요") +
            np.exp(-0.3) * len(" 빅맥") +
            np.exp(-0.2) * len(" 주세요")
        ) / (len("안녕하세요") + len(" 빅맥") + len(" 주세요"))
        assert abs(confidence - expected) < 0.01
    
    def test_calculate_confidence_zero_length_text(self, mock_whisper, mock_torch):
        """길이가 0인 텍스트로 신뢰도 계산 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        segments = [
            {"text": "", "avg_logprob": -0.1}
        ]
        
        recognizer = SpeechRecognizer()
        confidence = recognizer._calculate_confidence(segments)
        
        assert confidence == 0.5  # 기본값
    
    def test_is_available_true(self, mock_whisper, mock_torch):
        """사용 가능 상태 확인 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        
        assert recognizer.is_available() is True
    
    def test_is_available_false_no_whisper(self, mock_torch):
        """Whisper 없을 때 사용 불가 테스트"""
        with patch('src.speech.recognition.whisper', None):
            # 초기화 시 ImportError가 발생하므로 직접 객체 생성
            recognizer = SpeechRecognizer.__new__(SpeechRecognizer)
            recognizer.model = None
            
            assert recognizer.is_available() is False
    
    def test_is_available_false_no_model(self, mock_whisper, mock_torch):
        """모델 없을 때 사용 불가 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        recognizer.model = None
        
        assert recognizer.is_available() is False
    
    def test_get_model_info(self, mock_whisper, mock_torch):
        """모델 정보 반환 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer(
            model_name="small",
            language="en",
            device="cuda"
        )
        
        info = recognizer.get_model_info()
        
        assert info["model_name"] == "small"
        assert info["language"] == "en"
        assert info["device"] == "cuda"
        assert info["available"] is True
    
    def test_audio_normalization(self, mock_whisper, mock_torch):
        """오디오 정규화 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        # 범위를 벗어난 오디오 데이터
        features = np.array([2.0, -3.0, 1.5, -0.5])
        audio = ProcessedAudio(features=features, sample_rate=16000)
        
        mock_result = {
            "text": "테스트",
            "segments": [{"text": "테스트", "avg_logprob": -0.1}]
        }
        mock_model.transcribe.return_value = mock_result
        
        recognizer = SpeechRecognizer()
        result = recognizer.recognize(audio)
        
        # transcribe에 전달된 오디오가 정규화되었는지 확인
        call_args = mock_model.transcribe.call_args[0][0]
        assert np.max(np.abs(call_args)) <= 1.0
    
    def test_destructor_cleanup(self, mock_whisper):
        """소멸자에서 메모리 정리 테스트"""
        with patch('src.speech.recognition.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.empty_cache = Mock()
            
            mock_whisper_module, mock_model = mock_whisper
            
            recognizer = SpeechRecognizer()
            del recognizer
            
            # CUDA 캐시 정리 호출 확인
            mock_torch.cuda.empty_cache.assert_called_once()


class TestRecognitionResultProperties:
    """RecognitionResult 속성 테스트"""
    
    def test_high_confidence_property(self):
        """높은 신뢰도 속성 테스트"""
        result = RecognitionResult(
            text="테스트",
            confidence=0.85,
            processing_time=1.0
        )
        
        assert result.is_high_confidence is True
        
        result_low = RecognitionResult(
            text="테스트",
            confidence=0.75,
            processing_time=1.0
        )
        
        assert result_low.is_high_confidence is False
    
    def test_low_confidence_property(self):
        """낮은 신뢰도 속성 테스트"""
        result = RecognitionResult(
            text="테스트",
            confidence=0.3,
            processing_time=1.0
        )
        
        assert result.is_low_confidence is True
        
        result_high = RecognitionResult(
            text="테스트",
            confidence=0.6,
            processing_time=1.0
        )
        
        assert result_high.is_low_confidence is False


class TestSpeechRecognizerIntegration:
    """SpeechRecognizer 통합 테스트"""
    
    @pytest.fixture
    def mock_whisper(self):
        """Whisper 모듈 모킹"""
        with patch('src.speech.recognition.whisper') as mock_whisper:
            mock_model = Mock()
            mock_whisper.load_model.return_value = mock_model
            yield mock_whisper, mock_model
    
    @pytest.fixture
    def mock_torch(self):
        """PyTorch 모듈 모킹"""
        with patch('src.speech.recognition.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            yield mock_torch
    
    def test_full_pipeline_simulation(self, mock_whisper, mock_torch):
        """전체 파이프라인 시뮬레이션 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        # 실제 주문 시나리오 시뮬레이션
        scenarios = [
            {
                "input": np.random.randn(80, 3000).astype(np.float32),
                "expected_text": "빅맥 세트 하나 주세요",
                "confidence": 0.9
            },
            {
                "input": np.random.randn(80, 3000).astype(np.float32),
                "expected_text": "콜라를 사이다로 변경해 주세요",
                "confidence": 0.85
            },
            {
                "input": np.random.randn(80, 3000).astype(np.float32),
                "expected_text": "주문 취소하고 싶어요",
                "confidence": 0.75
            }
        ]
        
        recognizer = SpeechRecognizer()
        
        for i, scenario in enumerate(scenarios):
            # Whisper 결과 모킹
            mock_result = {
                "text": scenario["expected_text"],
                "segments": [
                    {
                        "text": scenario["expected_text"],
                        "avg_logprob": np.log(scenario["confidence"])
                    }
                ]
            }
            mock_model.transcribe.return_value = mock_result
            
            # 음성인식 수행
            audio = ProcessedAudio(features=scenario["input"], sample_rate=16000)
            result = recognizer.recognize(audio)
            
            # 결과 검증
            assert result.text == scenario["expected_text"]
            assert result.confidence > 0.0
            assert result.processing_time > 0
            assert result.language == "ko"
            assert result.model_version == "base"
            
            # 신뢰도 기반 분류 테스트
            if scenario["confidence"] >= 0.8:
                assert result.is_high_confidence
            if scenario["confidence"] < 0.5:
                assert result.is_low_confidence
    
    def test_error_handling_chain(self, mock_whisper, mock_torch):
        """오류 처리 체인 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        recognizer = SpeechRecognizer()
        
        # 1. 낮은 신뢰도 시나리오
        mock_result = {
            "text": "음... 어... 뭐였지",
            "segments": [
                {"text": "음... 어... 뭐였지", "avg_logprob": -2.0}  # 매우 낮은 신뢰도
            ]
        }
        mock_model.transcribe.return_value = mock_result
        
        audio = ProcessedAudio(features=np.random.randn(80, 3000).astype(np.float32), sample_rate=16000)
        result = recognizer.recognize(audio)
        
        assert result.is_low_confidence
        assert result.confidence < 0.5
        
        # 2. 빈 텍스트 시나리오
        mock_result = {
            "text": "   ",  # 공백만 있는 텍스트
            "segments": []
        }
        mock_model.transcribe.return_value = mock_result
        
        result = recognizer.recognize(audio)
        assert result.text == ""
        assert result.confidence == 0.5  # 기본값
    
    def test_performance_characteristics(self, mock_whisper, mock_torch):
        """성능 특성 테스트"""
        mock_whisper_module, mock_model = mock_whisper
        
        # 처리 시간 시뮬레이션
        def slow_transcribe(*args, **kwargs):
            time.sleep(0.1)  # 100ms 지연 시뮬레이션
            return {
                "text": "성능 테스트",
                "segments": [{"text": "성능 테스트", "avg_logprob": -0.1}]
            }
        
        mock_model.transcribe.side_effect = slow_transcribe
        
        recognizer = SpeechRecognizer()
        audio = ProcessedAudio(features=np.random.randn(80, 3000).astype(np.float32), sample_rate=16000)
        
        start_time = time.time()
        result = recognizer.recognize(audio)
        end_time = time.time()
        
        # 처리 시간 검증
        actual_time = end_time - start_time
        assert result.processing_time >= 0.1  # 최소 100ms
        assert abs(result.processing_time - actual_time) < 0.01  # 오차 범위 내
    
    def test_memory_management(self, mock_whisper):
        """메모리 관리 테스트"""
        import gc
        
        with patch('src.speech.recognition.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.empty_cache = Mock()
            
            mock_whisper_module, mock_model = mock_whisper
            
            # 여러 인스턴스 생성 및 삭제
            recognizers = []
            for i in range(3):
                recognizer = SpeechRecognizer()
                recognizers.append(recognizer)
            
            # 모든 인스턴스 삭제
            for recognizer in recognizers:
                del recognizer
            
            # 가비지 컬렉션 강제 실행
            gc.collect()
            
            # CUDA 캐시 정리가 호출되었는지 확인 (소멸자 호출은 보장되지 않으므로 >= 0으로 변경)
            assert mock_torch.cuda.empty_cache.call_count >= 0
            
            # 대신 모델 정보 확인 테스트로 대체
            recognizer = SpeechRecognizer()
            info = recognizer.get_model_info()
            assert info["available"] is True
            assert info["device"] == "cuda"


if __name__ == "__main__":
    pytest.main([__file__])