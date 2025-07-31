"""
오류 처리 및 복구 시스템 통합 테스트
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

# 프로젝트 루트 경로 추가
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.error_handler import APIErrorHandler, handle_api_error
from src.models.communication_models import ServerResponse, ErrorInfo, ErrorCode
from client_package.client.voice_client import VoiceClient
from client_package.client.config_manager import ClientConfig
from client_package.client.error_recovery import ErrorRecoveryManager, RecoveryStrategy, RecoveryResult


class TestAPIErrorHandler:
    """API 오류 처리기 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.error_handler = APIErrorHandler()
    
    def test_handle_network_error(self):
        """네트워크 오류 처리 테스트"""
        exception = ConnectionError("Connection failed")
        response = self.error_handler.handle_exception(exception)
        
        assert not response.success
        assert response.error_info is not None
        assert response.error_info.error_code == ErrorCode.NETWORK_ERROR.value
        assert "네트워크 연결" in response.error_info.error_message
        assert len(response.error_info.recovery_actions) > 0
    
    def test_handle_timeout_error(self):
        """타임아웃 오류 처리 테스트"""
        exception = TimeoutError("Request timeout")
        response = self.error_handler.handle_exception(exception)
        
        assert not response.success
        assert response.error_info.error_code == ErrorCode.TIMEOUT_ERROR.value
        assert "시간이 초과" in response.error_info.error_message
    
    def test_handle_validation_error(self):
        """검증 오류 처리 테스트"""
        exception = ValueError("Invalid input")
        response = self.error_handler.handle_exception(exception)
        
        assert not response.success
        assert response.error_info.error_code == ErrorCode.VALIDATION_ERROR.value
        assert len(response.ui_actions) > 0
    
    def test_error_statistics(self):
        """오류 통계 테스트"""
        # 여러 오류 발생
        exceptions = [
            ConnectionError("Network error 1"),
            TimeoutError("Timeout error 1"),
            ConnectionError("Network error 2"),
            ValueError("Validation error 1")
        ]
        
        for exc in exceptions:
            self.error_handler.handle_exception(exc)
        
        stats = self.error_handler.get_error_stats()
        
        assert stats['total_errors'] == 4
        assert ErrorCode.NETWORK_ERROR.value in stats['error_stats']
        assert stats['error_stats'][ErrorCode.NETWORK_ERROR.value]['count'] == 2
    
    def test_user_friendly_messages(self):
        """사용자 친화적 메시지 테스트"""
        test_cases = [
            (ConnectionError("Connection failed"), "네트워크 연결"),
            (TimeoutError("Timeout"), "시간이 초과"),
            (ValueError("Invalid"), "정보에 문제")
        ]
        
        for exception, expected_keyword in test_cases:
            response = self.error_handler.handle_exception(exception)
            assert expected_keyword in response.error_info.error_message


class TestErrorRecoveryManager:
    """오류 복구 관리자 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        # 모의 설정 생성
        self.mock_config = Mock()
        self.mock_config.server.max_retries = 3
        self.mock_config.server.retry_delay = 1
        
        self.recovery_manager = ErrorRecoveryManager(self.mock_config)
    
    def test_determine_recovery_strategies(self):
        """복구 전략 결정 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.NETWORK_ERROR.value,
            error_message="Network error",
            recovery_actions=["Retry"]
        )
        
        strategies = self.recovery_manager._determine_recovery_strategies(error_info)
        
        assert RecoveryStrategy.DELAYED_RETRY in strategies
        assert len(strategies) > 0
    
    def test_immediate_retry_success(self):
        """즉시 재시도 성공 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.TIMEOUT_ERROR.value,
            error_message="Timeout",
            recovery_actions=["Retry"]
        )
        
        # 성공하는 재시도 콜백
        def success_callback():
            mock_response = Mock()
            mock_response.success = True
            return mock_response
        
        result = self.recovery_manager._immediate_retry(
            error_info, {}, success_callback
        )
        
        assert result['result'] == RecoveryResult.SUCCESS
        assert 'response' in result
    
    def test_immediate_retry_failure(self):
        """즉시 재시도 실패 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.TIMEOUT_ERROR.value,
            error_message="Timeout",
            recovery_actions=["Retry"]
        )
        
        # 실패하는 재시도 콜백
        def failure_callback():
            mock_response = Mock()
            mock_response.success = False
            return mock_response
        
        result = self.recovery_manager._immediate_retry(
            error_info, {}, failure_callback
        )
        
        assert result['result'] == RecoveryResult.FAILED
    
    def test_user_intervention_request(self):
        """사용자 개입 요청 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.SPEECH_RECOGNITION_ERROR.value,
            error_message="Speech recognition failed",
            recovery_actions=["Speak clearly"]
        )
        
        result = self.recovery_manager._request_user_intervention(error_info)
        
        assert result['result'] == RecoveryResult.REQUIRES_USER_ACTION
        assert 'user_guidance' in result
        assert 'ui_actions' in result
    
    def test_fallback_mode_activation(self):
        """폴백 모드 활성화 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.SPEECH_RECOGNITION_ERROR.value,
            error_message="Speech recognition failed",
            recovery_actions=["Use text input"]
        )
        
        result = self.recovery_manager._activate_fallback_mode(error_info)
        
        assert result['result'] == RecoveryResult.PARTIAL_SUCCESS
        assert 'fallback_actions' in result
        assert result['mode'] == 'fallback'
    
    def test_error_escalation(self):
        """오류 에스컬레이션 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.SERVER_ERROR.value,
            error_message="Critical server error",
            recovery_actions=["Contact admin"]
        )
        
        result = self.recovery_manager._escalate_error(error_info)
        
        assert result['result'] == RecoveryResult.ESCALATED
        assert 'escalation_info' in result
        assert 'support_contact' in result
    
    def test_error_frequency_tracking(self):
        """오류 빈도 추적 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.NETWORK_ERROR.value,
            error_message="Network error",
            recovery_actions=["Retry"]
        )
        
        # 여러 번 같은 오류 기록
        for _ in range(6):
            self.recovery_manager._record_error(error_info)
        
        # 빈번한 오류로 감지되는지 확인
        is_frequent = self.recovery_manager._is_frequent_error(
            ErrorCode.NETWORK_ERROR.value, threshold=5
        )
        
        assert is_frequent
    
    def test_recovery_statistics(self):
        """복구 통계 테스트"""
        # 초기 통계 확인
        stats = self.recovery_manager.get_recovery_stats()
        assert stats['total_attempts'] == 0
        assert stats['success_rate'] == 0.0
        
        # 복구 시도 시뮬레이션
        self.recovery_manager.recovery_stats['total_attempts'] = 10
        self.recovery_manager.recovery_stats['successful_recoveries'] = 7
        
        stats = self.recovery_manager.get_recovery_stats()
        assert stats['success_rate'] == 70.0


class TestVoiceClientErrorHandling:
    """VoiceClient 오류 처리 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        # 모의 설정 생성
        self.mock_config = Mock()
        self.mock_config.server.url = "http://localhost:8000"
        self.mock_config.server.timeout = 30
        self.mock_config.server.max_retries = 3
        self.mock_config.server.retry_delay = 1
        self.mock_config.audio.supported_formats = ['.wav']
        self.mock_config.audio.max_file_size = 10 * 1024 * 1024
        self.mock_config.session.auto_generate_id = True
        self.mock_config.performance.connection_pool_size = 10
        self.mock_config.performance.download_timeout = 30
        
        # VoiceClient 생성 (실제 네트워크 요청 없이)
        with patch('client_package.client.voice_client.requests.Session'):
            self.voice_client = VoiceClient(self.mock_config)
    
    def test_file_validation_error_handling(self):
        """파일 검증 오류 처리 테스트"""
        # 존재하지 않는 파일
        response = self.voice_client.send_audio_file("/nonexistent/file.wav")
        
        assert not response.success
        assert response.error_info is not None
        assert response.error_info.error_code == ErrorCode.VALIDATION_ERROR.value
    
    def test_network_error_recovery(self):
        """네트워크 오류 복구 테스트"""
        # 임시 오디오 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'dummy audio data')
            temp_file_path = temp_file.name
        
        try:
            # 네트워크 오류 시뮬레이션
            with patch.object(self.voice_client.session, 'post') as mock_post:
                mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
                
                response = self.voice_client.send_audio_file(temp_file_path)
                
                assert not response.success
                assert response.error_info.error_code == ErrorCode.NETWORK_ERROR.value
                
                # 복구 정보 확인
                if response.error_info.details and 'recovery_result' in response.error_info.details:
                    recovery_result = response.error_info.details['recovery_result']
                    assert 'result' in recovery_result
        
        finally:
            # 임시 파일 정리
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_server_health_check(self):
        """서버 상태 확인 테스트"""
        with patch.object(self.voice_client.session, 'get') as mock_get:
            # 정상 응답
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'status': 'healthy'}
            mock_get.return_value = mock_response
            
            is_healthy = self.voice_client.check_server_health()
            assert is_healthy
            
            # 오류 응답
            mock_response.status_code = 500
            is_healthy = self.voice_client.check_server_health()
            assert not is_healthy
    
    def test_error_recovery_stats(self):
        """오류 복구 통계 테스트"""
        stats = self.voice_client.get_error_recovery_stats()
        
        assert 'total_attempts' in stats
        assert 'successful_recoveries' in stats
        assert 'success_rate' in stats
        
        # 통계 초기화 테스트
        self.voice_client.reset_error_recovery_stats()
        stats_after_reset = self.voice_client.get_error_recovery_stats()
        assert stats_after_reset['total_attempts'] == 0


class TestIntegrationScenarios:
    """통합 시나리오 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.api_error_handler = APIErrorHandler()
        
        # 모의 설정
        self.mock_config = Mock()
        self.mock_config.server.max_retries = 2
        self.mock_config.server.retry_delay = 0.1  # 테스트용 짧은 지연
        
        self.recovery_manager = ErrorRecoveryManager(self.mock_config)
    
    def test_end_to_end_error_recovery(self):
        """종단간 오류 복구 테스트"""
        # 1. 서버에서 오류 발생
        server_exception = ConnectionError("Database connection failed")
        server_response = self.api_error_handler.handle_exception(server_exception)
        
        assert not server_response.success
        assert server_response.error_info is not None
        
        # 2. 클라이언트에서 복구 시도
        recovery_result = self.recovery_manager.handle_error(
            server_response,
            context={'endpoint': '/api/voice/process'},
            retry_callback=lambda: Mock(success=True)  # 성공하는 재시도
        )
        
        # 복구 성공 확인
        assert recovery_result['result'] == RecoveryResult.SUCCESS
    
    def test_multiple_error_pattern_detection(self):
        """다중 오류 패턴 감지 테스트"""
        # 같은 오류를 여러 번 발생시켜 패턴 감지
        for _ in range(6):
            exception = ConnectionError("Repeated network error")
            response = self.api_error_handler.handle_exception(exception)
            
            self.recovery_manager.handle_error(
                response,
                context={'pattern_test': True}
            )
        
        # 오류 통계 확인
        api_stats = self.api_error_handler.get_error_stats()
        recovery_stats = self.recovery_manager.get_recovery_stats()
        
        assert api_stats['total_errors'] == 6
        assert recovery_stats['total_attempts'] == 6
        
        # 빈번한 오류로 감지되는지 확인
        is_frequent = self.recovery_manager._is_frequent_error(
            ErrorCode.NETWORK_ERROR.value, threshold=5
        )
        assert is_frequent
    
    def test_recovery_strategy_escalation(self):
        """복구 전략 에스컬레이션 테스트"""
        error_info = ErrorInfo(
            error_code=ErrorCode.SERVER_ERROR.value,
            error_message="Critical system error",
            recovery_actions=["Contact administrator"]
        )
        
        # 빈번한 오류로 만들기
        for _ in range(6):
            self.recovery_manager._record_error(error_info)
        
        # 복구 시도 - 에스컬레이션되어야 함
        recovery_result = self.recovery_manager.handle_error(
            ServerResponse.create_error_response(error_info),
            context={'critical_error': True}
        )
        
        assert recovery_result['result'] == RecoveryResult.ESCALATED
        assert 'escalation_info' in recovery_result


if __name__ == "__main__":
    # 개별 테스트 실행
    pytest.main([__file__, "-v"])