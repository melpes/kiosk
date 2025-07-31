"""
음성 처리 모듈 테스트
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from src.models.audio_models import AudioData, ProcessedAudio
from src.models.config_models import AudioConfig
from src.models.error_models import AudioError, AudioErrorType
from src.audio.preprocessing import AudioProcessor


class TestAudioData:
    """AudioData 클래스 테스트"""
    
    def test_audio_data_creation_success(self):
        """AudioData 생성 성공 테스트"""
        data = np.random.randn(16000)  # 1초 분량
        audio = AudioData(
            data=data,
            sample_rate=16000,
            channels=1,
            duration=1.0
        )
        
        assert audio.data is not None
        assert len(audio.data) == 16000
        assert audio.sample_rate == 16000
        assert audio.channels == 1
        assert audio.duration == 1.0
    
    def test_audio_data_validation_empty_data(self):
        """빈 데이터로 AudioData 생성 실패 테스트"""
        with pytest.raises(ValueError, match="음성 데이터가 비어있습니다"):
            AudioData(
                data=np.array([]),
                sample_rate=16000,
                channels=1,
                duration=1.0
            )
    
    def test_audio_data_validation_invalid_sample_rate(self):
        """잘못된 샘플레이트로 AudioData 생성 실패 테스트"""
        with pytest.raises(ValueError, match="샘플링 레이트는 양수여야 합니다"):
            AudioData(
                data=np.random.randn(1000),
                sample_rate=0,
                channels=1,
                duration=1.0
            )
    
    def test_audio_data_validation_invalid_channels(self):
        """잘못된 채널 수로 AudioData 생성 실패 테스트"""
        with pytest.raises(ValueError, match="채널 수는 양수여야 합니다"):
            AudioData(
                data=np.random.randn(1000),
                sample_rate=16000,
                channels=0,
                duration=1.0
            )
    
    def test_audio_data_validation_invalid_duration(self):
        """잘못된 지속시간으로 AudioData 생성 실패 테스트"""
        with pytest.raises(ValueError, match="지속 시간은 양수여야 합니다"):
            AudioData(
                data=np.random.randn(1000),
                sample_rate=16000,
                channels=1,
                duration=0
            )


class TestProcessedAudio:
    """ProcessedAudio 클래스 테스트"""
    
    def test_processed_audio_creation_success(self):
        """ProcessedAudio 생성 성공 테스트"""
        features = np.random.randn(80, 3000)
        processed = ProcessedAudio(
            features=features,
            sample_rate=16000,
            original_duration=30.0
        )
        
        assert processed.features.shape == (80, 3000)
        assert processed.sample_rate == 16000
        assert processed.original_duration == 30.0
        assert processed.mel_filters == 80
        assert processed.time_steps == 3000
    
    def test_processed_audio_validation_none_features(self):
        """None 특징으로 ProcessedAudio 생성 실패 테스트"""
        with pytest.raises(ValueError, match="특징 데이터가 없습니다"):
            ProcessedAudio(features=None)
    
    def test_processed_audio_validation_wrong_shape(self):
        """잘못된 특징 크기로 ProcessedAudio 생성 실패 테스트"""
        with pytest.raises(ValueError, match="특징 크기가 올바르지 않습니다"):
            ProcessedAudio(features=np.random.randn(40, 1500))
    
    def test_processed_audio_validation_wrong_sample_rate(self):
        """잘못된 샘플레이트로 ProcessedAudio 생성 실패 테스트"""
        with pytest.raises(ValueError, match="처리된 음성의 샘플링 레이트는 16kHz여야 합니다"):
            ProcessedAudio(
                features=np.random.randn(80, 3000),
                sample_rate=22050
            )


class TestAudioProcessor:
    """AudioProcessor 클래스 테스트"""
    
    @pytest.fixture
    def audio_config(self):
        """테스트용 오디오 설정"""
        return AudioConfig(
            sample_rate=16000,
            chunk_size=1024,
            channels=1,
            noise_reduction_level=0.5,
            speaker_separation_threshold=0.7,
            max_recording_duration=30,
            silence_threshold=0.01,
            noise_reduction_enabled=True,
            speaker_separation_enabled=True
        )
    
    @pytest.fixture
    def audio_processor(self, audio_config):
        """테스트용 AudioProcessor"""
        return AudioProcessor(audio_config)
    
    @pytest.fixture
    def sample_audio_data(self):
        """테스트용 샘플 오디오 데이터"""
        # 5초 분량의 샘플 데이터
        data = np.random.randn(80000)  # 16000 * 5
        return AudioData(
            data=data,
            sample_rate=16000,
            channels=1,
            duration=5.0
        )
    
    def test_audio_processor_initialization(self, audio_config):
        """AudioProcessor 초기화 테스트"""
        processor = AudioProcessor(audio_config)
        
        assert processor.config == audio_config
        assert processor.noise_config.enabled is True
        assert processor.noise_config.reduction_level == 0.5
        assert processor.speaker_config.enabled is True
        assert processor.speaker_config.threshold == 0.7
    
    @patch('src.audio.preprocessing.librosa')
    def test_process_audio_success(self, mock_librosa, audio_processor, sample_audio_data):
        """음성 처리 성공 테스트"""
        # librosa.resample mock 설정 (이미 16kHz이므로 호출되지 않음)
        mock_librosa.resample.return_value = sample_audio_data.data
        
        # librosa.stft, istft mock 설정 (노이즈 제거용)
        mock_stft = np.random.randn(1025, 157) + 1j * np.random.randn(1025, 157)  # 예시 STFT 결과
        mock_librosa.stft.return_value = mock_stft
        mock_librosa.istft.return_value = sample_audio_data.data
        
        # librosa.feature.melspectrogram mock 설정
        mock_mel = np.random.randn(80, 3000)
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        
        # librosa.power_to_db mock 설정
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = audio_processor.process_audio(sample_audio_data)
        
        assert isinstance(result, ProcessedAudio)
        assert result.features.shape == (80, 3000)
        assert result.sample_rate == 16000
        assert result.original_duration == 5.0
    
    def test_process_audio_validation_too_long(self, audio_processor):
        """너무 긴 음성 처리 실패 테스트"""
        # 31초 분량의 긴 오디오
        long_data = np.random.randn(496000)  # 16000 * 31
        long_audio = AudioData(
            data=long_data,
            sample_rate=16000,
            channels=1,
            duration=31.0
        )
        
        with pytest.raises(AudioError) as exc_info:
            audio_processor.process_audio(long_audio)
        
        assert exc_info.value.error_type == AudioErrorType.PROCESSING_FAILED
        assert "30초를 초과합니다" in str(exc_info.value.message)
    
    def test_process_audio_validation_low_sample_rate(self, audio_processor):
        """낮은 샘플레이트 음성 처리 실패 테스트"""
        low_sr_data = np.random.randn(4000)  # 0.5초 @ 8kHz
        low_sr_audio = AudioData(
            data=low_sr_data,
            sample_rate=4000,  # 8kHz 미만
            channels=1,
            duration=1.0
        )
        
        with pytest.raises(AudioError) as exc_info:
            audio_processor.process_audio(low_sr_audio)
        
        assert exc_info.value.error_type == AudioErrorType.PROCESSING_FAILED
        assert "샘플링 레이트가 너무 낮습니다" in str(exc_info.value.message)
    
    @patch('src.audio.preprocessing.librosa')
    def test_process_audio_with_resampling(self, mock_librosa, audio_processor):
        """리샘플링이 필요한 음성 처리 테스트"""
        # 44.1kHz 오디오 데이터
        high_sr_data = np.random.randn(44100)  # 1초 @ 44.1kHz
        high_sr_audio = AudioData(
            data=high_sr_data,
            sample_rate=44100,
            channels=1,
            duration=1.0
        )
        
        # 리샘플링 결과 mock
        resampled_data = np.random.randn(16000)  # 1초 @ 16kHz
        mock_librosa.resample.return_value = resampled_data
        
        # 기타 librosa 함수들 mock
        mock_stft = np.random.randn(1025, 100) + 1j * np.random.randn(1025, 100)
        mock_librosa.stft.return_value = mock_stft
        mock_librosa.istft.return_value = resampled_data
        
        mock_mel = np.random.randn(80, 3000)
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = audio_processor.process_audio(high_sr_audio)
        
        # 리샘플링이 호출되었는지 확인
        mock_librosa.resample.assert_called_once_with(
            high_sr_data, orig_sr=44100, target_sr=16000
        )
        
        assert isinstance(result, ProcessedAudio)
        assert result.sample_rate == 16000
    
    def test_separate_speakers_basic(self, audio_processor):
        """기본 화자 분리 테스트"""
        # 5초 분량의 테스트 데이터
        audio_data = np.random.randn(80000)
        
        result = audio_processor._separate_speakers(audio_data, 16000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        # 화자 분리 후 길이가 원본보다 짧거나 같아야 함
        assert len(result) <= len(audio_data)
    
    def test_separate_speakers_empty_audio(self, audio_processor):
        """빈 오디오 화자 분리 테스트"""
        empty_data = np.array([])
        
        result = audio_processor._separate_speakers(empty_data, 16000)
        
        # 빈 데이터는 그대로 반환
        assert len(result) == 0
    
    @patch('src.audio.preprocessing.librosa')
    def test_reduce_noise_basic(self, mock_librosa, audio_processor):
        """기본 노이즈 제거 테스트"""
        audio_data = np.random.randn(16000)  # 1초 분량
        
        # STFT/ISTFT mock 설정
        mock_stft = np.random.randn(1025, 32) + 1j * np.random.randn(1025, 32)
        mock_librosa.stft.return_value = mock_stft
        mock_librosa.istft.return_value = audio_data
        
        result = audio_processor._reduce_noise(audio_data, 16000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        
        # STFT와 ISTFT가 호출되었는지 확인
        mock_librosa.stft.assert_called_once()
        mock_librosa.istft.assert_called_once()
    
    @patch('src.audio.preprocessing.librosa')
    def test_extract_mel_features_success(self, mock_librosa, audio_processor):
        """Mel 특징 추출 성공 테스트"""
        # 30초 분량의 16kHz 데이터
        audio_data = np.random.randn(480000)  # 16000 * 30
        
        # melspectrogram mock 설정
        mock_mel = np.random.randn(80, 3000)
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = audio_processor._extract_mel_features(audio_data)
        
        assert result.shape == (80, 3000)
        
        # melspectrogram이 올바른 파라미터로 호출되었는지 확인
        mock_librosa.feature.melspectrogram.assert_called_once_with(
            y=audio_data,
            sr=16000,
            n_fft=400,
            hop_length=160,
            n_mels=80,
            fmin=0,
            fmax=8000
        )
    
    @patch('src.audio.preprocessing.librosa')
    def test_extract_mel_features_short_audio(self, mock_librosa, audio_processor):
        """짧은 오디오의 Mel 특징 추출 테스트 (패딩)"""
        # 10초 분량의 16kHz 데이터
        short_audio = np.random.randn(160000)  # 16000 * 10
        
        mock_mel = np.random.randn(80, 1000)  # 짧은 특징
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = audio_processor._extract_mel_features(short_audio)
        
        # 패딩되어 3000 time steps가 되어야 함
        assert result.shape == (80, 3000)
    
    @patch('src.audio.preprocessing.librosa')
    def test_extract_mel_features_long_audio(self, mock_librosa, audio_processor):
        """긴 오디오의 Mel 특징 추출 테스트 (트림)"""
        # 60초 분량의 16kHz 데이터
        long_audio = np.random.randn(960000)  # 16000 * 60
        
        mock_mel = np.random.randn(80, 6000)  # 긴 특징
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = audio_processor._extract_mel_features(long_audio)
        
        # 트림되어 3000 time steps가 되어야 함
        assert result.shape == (80, 3000)
    
    def test_validate_audio_format_success(self, audio_processor):
        """음성 포맷 검증 성공 테스트"""
        valid_data = np.random.randn(16000)  # 1초 분량
        
        result = audio_processor.validate_audio_format(valid_data, 16000)
        
        assert result is True
    
    def test_validate_audio_format_empty_data(self, audio_processor):
        """빈 데이터 포맷 검증 실패 테스트"""
        empty_data = np.array([])
        
        result = audio_processor.validate_audio_format(empty_data, 16000)
        
        assert result is False
    
    def test_validate_audio_format_invalid_sample_rate(self, audio_processor):
        """잘못된 샘플레이트 포맷 검증 실패 테스트"""
        valid_data = np.random.randn(16000)
        
        result = audio_processor.validate_audio_format(valid_data, 0)
        
        assert result is False
    
    def test_validate_audio_format_too_long(self, audio_processor):
        """너무 긴 오디오 포맷 검증 실패 테스트"""
        long_data = np.random.randn(500000)  # 31초 @ 16kHz
        
        result = audio_processor.validate_audio_format(long_data, 16000)
        
        assert result is False
    
    def test_validate_audio_format_silent_audio(self, audio_processor):
        """무음 오디오 포맷 검증 실패 테스트"""
        silent_data = np.zeros(16000)  # 1초 분량의 무음
        
        result = audio_processor.validate_audio_format(silent_data, 16000)
        
        assert result is False
    
    @patch('src.audio.preprocessing.librosa')
    def test_get_audio_info_success(self, mock_librosa, audio_processor, sample_audio_data):
        """음성 정보 추출 성공 테스트"""
        # librosa 함수들 mock 설정
        mock_librosa.feature.zero_crossing_rate.return_value = np.array([[0.1]])
        mock_librosa.feature.spectral_centroid.return_value = np.array([[1000.0]])
        
        info = audio_processor.get_audio_info(sample_audio_data)
        
        assert info['duration'] == 5.0
        assert info['sample_rate'] == 16000
        assert info['channels'] == 1
        assert info['samples'] == 80000
        assert 'rms_energy' in info
        assert 'peak_amplitude' in info
        assert 'zero_crossing_rate' in info
        assert 'spectral_centroid' in info
        assert info['format_valid'] is True
    
    @patch('src.audio.preprocessing.librosa')
    def test_create_audio_data_success(self, mock_librosa, audio_processor):
        """파일에서 AudioData 생성 성공 테스트"""
        # librosa.load mock 설정
        mock_audio_data = np.random.randn(22050)  # 1초 @ 22050Hz
        mock_librosa.load.return_value = (mock_audio_data, 22050)
        
        result = audio_processor.create_audio_data("test.wav")
        
        assert isinstance(result, AudioData)
        assert result.sample_rate == 22050
        assert result.channels == 1
        assert result.duration == 1.0
        assert len(result.data) == 22050
        
        # librosa.load가 올바른 파라미터로 호출되었는지 확인
        mock_librosa.load.assert_called_once_with("test.wav", sr=None, mono=True)
    
    @patch('src.audio.preprocessing.librosa')
    def test_create_audio_data_file_error(self, mock_librosa, audio_processor):
        """파일 로드 실패 테스트"""
        # librosa.load가 예외를 발생시키도록 설정
        mock_librosa.load.side_effect = Exception("파일을 찾을 수 없습니다")
        
        with pytest.raises(AudioError) as exc_info:
            audio_processor.create_audio_data("nonexistent.wav")
        
        assert exc_info.value.error_type == AudioErrorType.FILE_LOAD_FAILED
        assert "음성 파일 로드 실패" in str(exc_info.value.message)
    
    @patch('src.audio.preprocessing.librosa')
    def test_process_audio_feature_extraction_error(self, mock_librosa, audio_processor, sample_audio_data):
        """특징 추출 실패 테스트"""
        # librosa 함수들이 정상 작동하도록 설정
        mock_librosa.resample.return_value = sample_audio_data.data
        mock_stft = np.random.randn(1025, 157) + 1j * np.random.randn(1025, 157)
        mock_librosa.stft.return_value = mock_stft
        mock_librosa.istft.return_value = sample_audio_data.data
        
        # melspectrogram에서 예외 발생
        mock_librosa.feature.melspectrogram.side_effect = Exception("특징 추출 실패")
        
        with pytest.raises(AudioError) as exc_info:
            audio_processor.process_audio(sample_audio_data)
        
        assert exc_info.value.error_type == AudioErrorType.FEATURE_EXTRACTION_FAILED
        assert "특징 추출 실패" in str(exc_info.value.message)


class TestAudioProcessorIntegration:
    """AudioProcessor 통합 테스트"""
    
    @pytest.fixture
    def full_config(self):
        """완전한 오디오 설정"""
        return AudioConfig(
            sample_rate=16000,
            chunk_size=1024,
            channels=1,
            noise_reduction_level=0.3,
            speaker_separation_threshold=0.8,
            max_recording_duration=30,
            silence_threshold=0.01,
            noise_reduction_enabled=True,
            speaker_separation_enabled=True
        )
    
    @pytest.fixture
    def disabled_config(self):
        """기능이 비활성화된 오디오 설정"""
        return AudioConfig(
            sample_rate=16000,
            chunk_size=1024,
            channels=1,
            noise_reduction_level=0.5,
            speaker_separation_threshold=0.7,
            max_recording_duration=30,
            silence_threshold=0.01,
            noise_reduction_enabled=False,
            speaker_separation_enabled=False
        )
    
    @patch('src.audio.preprocessing.librosa')
    def test_full_pipeline_with_all_features(self, mock_librosa, full_config):
        """모든 기능이 활성화된 전체 파이프라인 테스트"""
        processor = AudioProcessor(full_config)
        
        # 테스트 데이터
        audio_data = np.random.randn(80000)  # 5초 @ 16kHz
        audio_input = AudioData(
            data=audio_data,
            sample_rate=16000,
            channels=1,
            duration=5.0
        )
        
        # librosa mock 설정
        mock_stft = np.random.randn(1025, 157) + 1j * np.random.randn(1025, 157)
        mock_librosa.stft.return_value = mock_stft
        mock_librosa.istft.return_value = audio_data
        
        mock_mel = np.random.randn(80, 3000)
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = processor.process_audio(audio_input)
        
        assert isinstance(result, ProcessedAudio)
        assert result.features.shape == (80, 3000)
        assert result.sample_rate == 16000
        assert result.original_duration == 5.0
        
        # 노이즈 제거와 특징 추출이 호출되었는지 확인
        mock_librosa.stft.assert_called()
        mock_librosa.istft.assert_called()
        mock_librosa.feature.melspectrogram.assert_called()
    
    @patch('src.audio.preprocessing.librosa')
    def test_pipeline_with_disabled_features(self, mock_librosa, disabled_config):
        """기능이 비활성화된 파이프라인 테스트"""
        processor = AudioProcessor(disabled_config)
        
        # 테스트 데이터
        audio_data = np.random.randn(80000)  # 5초 @ 16kHz
        audio_input = AudioData(
            data=audio_data,
            sample_rate=16000,
            channels=1,
            duration=5.0
        )
        
        # librosa mock 설정 (노이즈 제거는 호출되지 않아야 함)
        mock_mel = np.random.randn(80, 3000)
        mock_librosa.feature.melspectrogram.return_value = mock_mel
        mock_librosa.power_to_db.return_value = mock_mel
        
        result = processor.process_audio(audio_input)
        
        assert isinstance(result, ProcessedAudio)
        assert result.features.shape == (80, 3000)
        
        # 노이즈 제거 관련 함수들이 호출되지 않았는지 확인
        mock_librosa.stft.assert_not_called()
        mock_librosa.istft.assert_not_called()
        
        # 특징 추출은 호출되어야 함
        mock_librosa.feature.melspectrogram.assert_called()