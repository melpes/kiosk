"""
MicrophoneInputManager 클래스에 대한 기본 테스트
"""

import pytest
import numpy as np
import torch
from unittest.mock import Mock, patch, MagicMock
from src.microphone.microphone_manager import MicrophoneInputManager, MicrophoneError, VADError, RecordingError
from src.models.microphone_models import MicrophoneConfig, MicrophoneStatus


class TestMicrophoneInputManager:
    """MicrophoneInputManager 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.config = MicrophoneConfig(
            sample_rate=16000,
            frame_duration=0.5,
            max_silence_duration_start=5.0,
            max_silence_duration_end=3.0,
            min_record_duration=1.0,
            vad_threshold=0.2,
            output_filename="test_mic_input.wav"
        )
    
    @patch('src.microphone.microphone_manager.VADProcessor')
    @patch('src.microphone.microphone_manager.AudioRecorder')
    def test_initialization_success(self, mock_audio_recorder, mock_vad_processor):
        """정상 초기화 테스트"""
        # VAD 프로세서 모킹
        mock_vad = Mock()
        mock_vad.is_model_ready.return_value = True
        mock_vad_processor.return_value = mock_vad
        
        # 오디오 레코더 모킹
        mock_recorder = Mock()
        mock_audio_recorder.return_value = mock_recorder
        
        manager = MicrophoneInputManager(self.config)
        
        # 초기화 검증
        assert manager.config == self.config
        assert manager.vad_processor is not None
        assert manager.audio_recorder is not None
        assert not manager.fallback_mode
        assert isinstance(manager.status, MicrophoneStatus)
        assert not manager.status.is_listening
        assert not manager.status.is_recording
    
    @patch('src.microphone.microphone_manager.VADProcessor')
    @patch('src.microphone.microphone_manager.AudioRecorder')
    def test_initialization_vad_failure(self, mock_audio_recorder, mock_vad_processor):
        """VAD 초기화 실패 시 폴백 모드 테스트"""
        # VAD 프로세서 실패 모킹
        mock_vad = Mock()
        mock_vad.is_model_ready.return_value = False
        mock_vad_processor.return_value = mock_vad
        
        # 오디오 레코더 모킹
        mock_recorder = Mock()
        mock_audio_recorder.return_value = mock_recorder
        
        manager = MicrophoneInputManager(self.config)
        
        # 폴백 모드 확인
        assert manager.fallback_mode
        assert len(manager.error_history) > 0
        assert manager.error_history[-1]["error_type"] == "vad_model_error"
    
    @patch('src.microphone.microphone_manager.VADProcessor')
    @patch('src.microphone.microphone_manager.AudioRecorder')
    def test_initialization_complete_failure(self, mock_audio_recorder, mock_vad_processor):
        """완전한 초기화 실패 테스트"""
        # VAD 프로세서 예외 발생
        mock_vad_processor.side_effect = Exception("VAD 초기화 실패")
        
        with pytest.raises(MicrophoneError):
            MicrophoneInputManager(self.config)
    
    @patch('src.microphone.microphone_manager.sd.query_devices')
    def test_check_hardware_availability_success(self, mock_query_devices):
        """하드웨어 가용성 확인 성공 테스트"""
        # 가상의 오디오 장치 설정
        mock_devices = [
            {'name': 'Microphone', 'max_input_channels': 1, 'default_samplerate': 44100.0},
            {'name': 'Speaker', 'max_input_channels': 0, 'default_samplerate': 44100.0}
        ]
        mock_query_devices.return_value = mock_devices
        
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            hardware_status = manager._check_hardware_availability()
            
            assert hardware_status["available"]
            assert hardware_status["input_devices_count"] == 1
            assert "Microphone" in hardware_status["default_device"]
    
    @patch('src.microphone.microphone_manager.sd.query_devices')
    def test_check_hardware_availability_no_input_devices(self, mock_query_devices):
        """입력 장치 없음 테스트"""
        # 입력 장치가 없는 상황
        mock_devices = [
            {'name': 'Speaker', 'max_input_channels': 0, 'default_samplerate': 44100.0}
        ]
        mock_query_devices.return_value = mock_devices
        
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            hardware_status = manager._check_hardware_availability()
            
            assert not hardware_status["available"]
            assert "error" in hardware_status
    
    def test_detect_speech_fallback(self):
        """폴백 모드 음성 감지 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            manager.fallback_mode = True
            
            # 높은 볼륨 (음성 있음)
            high_volume_audio = np.random.normal(0, 0.5, 1000).astype(np.float32)
            assert manager._detect_speech_fallback(high_volume_audio)
            
            # 낮은 볼륨 (음성 없음)
            low_volume_audio = np.random.normal(0, 0.01, 1000).astype(np.float32)
            assert not manager._detect_speech_fallback(low_volume_audio)
    
    def test_get_microphone_status(self):
        """마이크 상태 반환 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor') as mock_vad_processor, \
             patch('src.microphone.microphone_manager.AudioRecorder') as mock_audio_recorder, \
             patch('src.microphone.microphone_manager.sd.query_devices') as mock_query_devices:
            
            # 모킹 설정
            mock_vad = Mock()
            mock_vad.is_model_ready.return_value = True
            mock_vad_processor.return_value = mock_vad
            
            mock_recorder = Mock()
            mock_recorder.get_recording_info.return_value = {"recording_duration": 2.5}
            mock_audio_recorder.return_value = mock_recorder
            
            mock_query_devices.return_value = [
                {'name': 'Microphone', 'max_input_channels': 1, 'default_samplerate': 44100.0}
            ]
            
            manager = MicrophoneInputManager(self.config)
            status = manager.get_microphone_status()
            
            # 상태 검증
            assert "is_listening" in status
            assert "is_recording" in status
            assert "current_volume_level" in status
            assert "recording_duration" in status
            assert "vad_status" in status
            assert "vad_model_ready" in status
            assert "fallback_mode" in status
            assert "hardware_available" in status
            assert "recording_info" in status
            assert "error_count" in status
            assert "config" in status
            
            # 설정 정보 확인
            assert status["config"]["sample_rate"] == self.config.sample_rate
            assert status["config"]["vad_threshold"] == self.config.vad_threshold
    
    def test_validate_config_valid(self):
        """유효한 설정 검증 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            valid_config = MicrophoneConfig(
                sample_rate=16000,
                frame_duration=0.5,
                max_silence_duration_start=5.0,
                max_silence_duration_end=3.0,
                min_record_duration=1.0,
                vad_threshold=0.3
            )
            
            result = manager._validate_config(valid_config)
            assert result["valid"]
            assert len(result["errors"]) == 0
    
    def test_validate_config_invalid(self):
        """잘못된 설정 검증 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            invalid_config = MicrophoneConfig(
                sample_rate=-1000,  # 잘못된 샘플레이트
                frame_duration=-0.5,  # 잘못된 프레임 지속시간
                max_silence_duration_start=-1.0,  # 잘못된 무음 시간
                max_silence_duration_end=0,  # 잘못된 무음 시간
                min_record_duration=-1.0,  # 잘못된 최소 녹음 시간
                vad_threshold=1.5  # 잘못된 VAD 임계값
            )
            
            result = manager._validate_config(invalid_config)
            assert not result["valid"]
            assert len(result["errors"]) > 0
    
    def test_update_config_success(self):
        """설정 업데이트 성공 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            new_config = MicrophoneConfig(
                sample_rate=22050,
                frame_duration=0.3,
                vad_threshold=0.3
            )
            
            result = manager.update_config(new_config)
            
            assert result["success"]
            assert manager.config.sample_rate == 22050
            assert manager.config.frame_duration == 0.3
            assert manager.config.vad_threshold == 0.3
    
    def test_update_config_invalid(self):
        """잘못된 설정 업데이트 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            original_config = manager.config
            
            invalid_config = MicrophoneConfig(
                sample_rate=-1000,  # 잘못된 값
                vad_threshold=2.0   # 잘못된 값
            )
            
            result = manager.update_config(invalid_config)
            
            assert not result["success"]
            assert manager.config == original_config  # 원래 설정 유지
    
    @patch('src.microphone.microphone_manager.sd.rec')
    @patch('src.microphone.microphone_manager.sd.wait')
    def test_test_microphone_success(self, mock_wait, mock_rec):
        """마이크 테스트 성공 테스트"""
        # 가상의 오디오 데이터 생성
        test_audio = np.random.normal(0, 0.1, (32000, 1)).astype(np.float32)
        mock_rec.return_value = test_audio
        
        with patch('src.microphone.microphone_manager.VADProcessor') as mock_vad_processor, \
             patch('src.microphone.microphone_manager.AudioRecorder'), \
             patch('src.microphone.microphone_manager.sd.query_devices') as mock_query_devices:
            
            # 모킹 설정
            mock_vad = Mock()
            mock_vad.is_model_ready.return_value = True
            mock_vad.detect_speech.return_value = True
            mock_vad_processor.return_value = mock_vad
            
            mock_query_devices.return_value = [
                {'name': 'Microphone', 'max_input_channels': 1, 'default_samplerate': 44100.0}
            ]
            
            manager = MicrophoneInputManager(self.config)
            result = manager.test_microphone()
            
            assert result["overall_success"]
            assert result["hardware_test"]["success"]
            assert result["recording_test"]["success"]
            assert result["vad_test"]["success"]
            assert "average_volume" in result["recording_test"]
            assert "max_volume" in result["recording_test"]
    
    def test_error_logging(self):
        """오류 로깅 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            # 오류 로그 추가
            from src.microphone.microphone_manager import ErrorType
            manager._log_error(ErrorType.HARDWARE_ERROR, "테스트 오류")
            
            assert len(manager.error_history) > 0
            assert manager.error_history[-1]["error_type"] == "hardware_error"
            assert manager.error_history[-1]["message"] == "테스트 오류"
            assert "timestamp" in manager.error_history[-1]
    
    def test_clear_error_history(self):
        """오류 기록 초기화 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            # 오류 추가
            from src.microphone.microphone_manager import ErrorType
            manager._log_error(ErrorType.HARDWARE_ERROR, "테스트 오류")
            assert len(manager.error_history) > 0
            
            # 초기화
            manager.clear_error_history()
            assert len(manager.error_history) == 0
    
    def test_get_diagnostic_info(self):
        """진단 정보 반환 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor') as mock_vad_processor, \
             patch('src.microphone.microphone_manager.AudioRecorder'), \
             patch('src.microphone.microphone_manager.sd.query_devices') as mock_query_devices:
            
            # 모킹 설정
            mock_vad = Mock()
            mock_vad.is_model_ready.return_value = True
            mock_vad.get_model_info.return_value = {"model_loaded": True, "model_name": "silero_vad"}
            mock_vad_processor.return_value = mock_vad
            
            mock_query_devices.return_value = [
                {'name': 'Microphone', 'max_input_channels': 1, 'default_samplerate': 44100.0}
            ]
            
            manager = MicrophoneInputManager(self.config)
            diagnostic = manager.get_diagnostic_info()
            
            # 진단 정보 검증
            assert "system_info" in diagnostic
            assert "hardware_status" in diagnostic
            assert "vad_info" in diagnostic
            assert "current_status" in diagnostic
            assert "error_summary" in diagnostic
            
            # 시스템 정보 확인
            assert "fallback_mode" in diagnostic["system_info"]
            assert "components_initialized" in diagnostic["system_info"]
    
    def test_reset_system(self):
        """시스템 재설정 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            # 오류 추가 및 폴백 모드 설정
            from src.microphone.microphone_manager import ErrorType
            manager._log_error(ErrorType.HARDWARE_ERROR, "테스트 오류")
            manager.fallback_mode = True
            
            # 재설정
            result = manager.reset_system()
            
            assert result["success"]
            assert len(manager.error_history) == 0
            # 폴백 모드는 VAD 모델 상태에 따라 결정되므로 여기서는 확인하지 않음
    
    def test_context_manager(self):
        """컨텍스트 매니저 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            
            with MicrophoneInputManager(self.config) as manager:
                assert manager is not None
                assert isinstance(manager, MicrophoneInputManager)
            
            # 컨텍스트 종료 후 정리 확인
            assert not manager.status.is_listening
            assert not manager.status.is_recording
    
    def test_stop_listening(self):
        """마이크 입력 중단 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder') as mock_audio_recorder:
            
            mock_recorder = Mock()
            mock_audio_recorder.return_value = mock_recorder
            
            manager = MicrophoneInputManager(self.config)
            manager.status.is_listening = True
            manager.status.is_recording = True
            
            manager.stop_listening()
            
            assert not manager.status.is_listening
            assert not manager.status.is_recording
            assert manager.status.vad_status == "waiting"
            mock_recorder.cleanup.assert_called_once()
    
    @patch('builtins.print')  # print 출력 모킹
    def test_display_status(self, mock_print):
        """상태 표시 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            manager.status.vad_status = "detecting"
            manager.status.current_volume_level = 0.5
            
            manager._display_status()
            
            # print가 호출되었는지 확인
            mock_print.assert_called()
            call_args = mock_print.call_args[0][0]
            assert "detecting" in call_args
            assert "🗣️" in call_args
    
    def test_error_history_limit(self):
        """오류 기록 개수 제한 테스트"""
        with patch('src.microphone.microphone_manager.VADProcessor'), \
             patch('src.microphone.microphone_manager.AudioRecorder'):
            manager = MicrophoneInputManager(self.config)
            
            # 101개의 오류 추가 (제한은 100개)
            from src.microphone.microphone_manager import ErrorType
            for i in range(101):
                manager._log_error(ErrorType.HARDWARE_ERROR, f"테스트 오류 {i}")
            
            # 최대 100개만 보관되는지 확인
            assert len(manager.error_history) == 100
            
            # 가장 최근 오류가 마지막에 있는지 확인
            assert manager.error_history[-1]["message"] == "테스트 오류 100"