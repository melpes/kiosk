"""
오류 처리 시스템 테스트
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime

from src.error.handler import ErrorHandler, ErrorRecoveryManager
from src.models.error_models import (
    ErrorAction, ErrorResponse,
    AudioError, AudioErrorType,
    RecognitionError, RecognitionErrorType,
    IntentError, IntentErrorType,
    OrderError, OrderErrorType,
    ValidationError, ConfigurationError
)


class TestErrorHandler:
    """ErrorHandler 클래스 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.error_handler = ErrorHandler(max_retry_count=3)
    
    def test_init(self):
        """초기화 테스트"""
        handler = ErrorHandler(max_retry_count=5)
        assert handler.max_retry_count == 5
        assert handler.error_counts == {}
        assert handler.error_history == []
        assert handler.logger is not None
    
    def test_handle_audio_error_low_quality(self):
        """음성 품질 낮음 오류 처리 테스트"""
        error = AudioError(
            error_type=AudioErrorType.LOW_QUALITY,
            message="Low quality audio"
        )
        
        response = self.error_handler.handle_audio_error(error)
        
        assert response.message == "음성이 명확하지 않습니다. 다시 말씀해 주세요."
        assert response.action == ErrorAction.REQUEST_RETRY
        assert response.retry_count == 0
        assert response.can_recover is True
        assert response.metadata["error_type"] == "low_quality"
    
    def test_handle_audio_error_no_input(self):
        """음성 입력 없음 오류 처리 테스트"""
        error = AudioError(
            error_type=AudioErrorType.NO_INPUT,
            message="No audio input"
        )
        
        response = self.error_handler.handle_audio_error(error)
        
        assert response.message == "음성이 감지되지 않았습니다. 다시 말씀해 주세요."
        assert response.action == ErrorAction.REQUEST_RETRY
        assert response.can_recover is True
    
    def test_handle_audio_error_multiple_speakers(self):
        """다중 화자 오류 처리 테스트"""
        error = AudioError(
            error_type=AudioErrorType.MULTIPLE_SPEAKERS,
            message="Multiple speakers detected"
        )
        
        response = self.error_handler.handle_audio_error(error)
        
        assert response.message == "여러 명이 동시에 말씀하고 계십니다. 한 분씩 말씀해 주세요."
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert response.can_recover is True
    
    def test_handle_audio_error_processing_failed(self):
        """음성 처리 실패 오류 처리 테스트"""
        error = AudioError(
            error_type=AudioErrorType.PROCESSING_FAILED,
            message="Processing failed"
        )
        
        response = self.error_handler.handle_audio_error(error)
        
        assert response.action == ErrorAction.FALLBACK_MODE
        assert response.can_recover is True
    
    def test_handle_audio_error_max_retries(self):
        """최대 재시도 횟수 초과 테스트"""
        error = AudioError(
            error_type=AudioErrorType.PROCESSING_FAILED,
            message="Processing failed"
        )
        
        # 최대 재시도 횟수만큼 오류 발생시키기
        for _ in range(self.error_handler.max_retry_count):
            self.error_handler.handle_audio_error(error)
        
        response = self.error_handler.handle_audio_error(error)
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert response.can_recover is False
    
    def test_handle_recognition_error_low_confidence(self):
        """낮은 신뢰도 음성인식 오류 처리 테스트"""
        error = RecognitionError(
            error_type=RecognitionErrorType.LOW_CONFIDENCE,
            message="Low confidence",
            confidence=0.3
        )
        
        response = self.error_handler.handle_recognition_error(error)
        
        assert response.message == "정확히 듣지 못했습니다. 다시 주문해 주세요."
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert response.metadata["confidence"] == 0.3
    
    def test_handle_recognition_error_model_not_loaded(self):
        """모델 미로드 오류 처리 테스트"""
        error = RecognitionError(
            error_type=RecognitionErrorType.MODEL_NOT_LOADED,
            message="Model not loaded"
        )
        
        response = self.error_handler.handle_recognition_error(error)
        
        assert response.action == ErrorAction.FALLBACK_MODE
        assert response.can_recover is True
        assert "준비 중" in response.message
    
    def test_handle_recognition_error_model_error(self):
        """모델 오류 처리 테스트"""
        error = RecognitionError(
            error_type=RecognitionErrorType.MODEL_ERROR,
            message="Model error"
        )
        
        response = self.error_handler.handle_recognition_error(error)
        
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert response.can_recover is False
        assert "직원을 호출" in response.message
    
    def test_handle_intent_error_ambiguous(self):
        """모호한 의도 오류 처리 테스트"""
        error = IntentError(
            error_type=IntentErrorType.AMBIGUOUS_INTENT,
            message="Ambiguous intent",
            raw_text="뭔가 주문하고 싶어요"
        )
        
        response = self.error_handler.handle_intent_error(error)
        
        assert response.message == "요청하신 내용을 정확히 이해하지 못했습니다. 더 구체적으로 말씀해 주세요."
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert response.metadata["raw_text"] == "뭔가 주문하고 싶어요"
    
    def test_handle_intent_error_unknown(self):
        """알 수 없는 의도 오류 처리 테스트"""
        error = IntentError(
            error_type=IntentErrorType.UNKNOWN_INTENT,
            message="Unknown intent"
        )
        
        response = self.error_handler.handle_intent_error(error)
        
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert len(response.suggested_alternatives) > 0
        assert "주문하기" in response.suggested_alternatives
    
    def test_handle_intent_error_llm_api_error(self):
        """LLM API 오류 처리 테스트"""
        error = IntentError(
            error_type=IntentErrorType.LLM_API_ERROR,
            message="API error"
        )
        
        response = self.error_handler.handle_intent_error(error)
        
        assert response.action == ErrorAction.REQUEST_RETRY
        assert response.can_recover is True
    
    def test_handle_intent_error_llm_api_error_max_retries(self):
        """LLM API 오류 최대 재시도 테스트"""
        error = IntentError(
            error_type=IntentErrorType.LLM_API_ERROR,
            message="API error"
        )
        
        # 최대 재시도 횟수만큼 오류 발생시키기
        for _ in range(self.error_handler.max_retry_count):
            self.error_handler.handle_intent_error(error)
        
        response = self.error_handler.handle_intent_error(error)
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert response.can_recover is False
    
    def test_handle_order_error_item_not_found(self):
        """메뉴 아이템 없음 오류 처리 테스트"""
        error = OrderError(
            error_type=OrderErrorType.ITEM_NOT_FOUND,
            message="Item not found",
            item_name="비빔밥"
        )
        
        response = self.error_handler.handle_order_error(error)
        
        assert "'비빔밥' 메뉴를 찾을 수 없습니다" in response.message
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert response.metadata["item_name"] == "비빔밥"
    
    def test_handle_order_error_payment_error(self):
        """결제 오류 처리 테스트"""
        error = OrderError(
            error_type=OrderErrorType.PAYMENT_ERROR,
            message="Payment failed"
        )
        
        response = self.error_handler.handle_order_error(error)
        
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert response.can_recover is False
        assert "결제 처리 중 오류" in response.message
    
    def test_handle_order_error_system_error(self):
        """시스템 오류 처리 테스트"""
        error = OrderError(
            error_type=OrderErrorType.SYSTEM_ERROR,
            message="System error"
        )
        
        response = self.error_handler.handle_order_error(error)
        
        assert response.action == ErrorAction.REQUEST_RETRY
        assert response.can_recover is True
    
    def test_handle_order_error_system_error_max_retries(self):
        """시스템 오류 최대 재시도 테스트"""
        error = OrderError(
            error_type=OrderErrorType.SYSTEM_ERROR,
            message="System error"
        )
        
        # 최대 재시도 횟수만큼 오류 발생시키기
        for _ in range(self.error_handler.max_retry_count):
            self.error_handler.handle_order_error(error)
        
        response = self.error_handler.handle_order_error(error)
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert "지속되고 있습니다" in response.message
    
    def test_handle_validation_error(self):
        """데이터 검증 오류 처리 테스트"""
        error = ValidationError(
            message="Invalid data format",
            details={"field": "quantity", "value": -1}
        )
        
        response = self.error_handler.handle_validation_error(error)
        
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert response.can_recover is True
        assert "입력 데이터가 올바르지 않습니다" in response.message
        assert response.metadata["details"]["field"] == "quantity"
    
    def test_handle_configuration_error(self):
        """설정 오류 처리 테스트"""
        error = ConfigurationError(
            message="Missing API key",
            config_path="/config/api_keys.json"
        )
        
        response = self.error_handler.handle_configuration_error(error)
        
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert response.can_recover is False
        assert "시스템 설정에 문제" in response.message
        assert response.metadata["config_path"] == "/config/api_keys.json"
    
    def test_handle_general_error_specific_types(self):
        """일반 오류 처리 - 특정 타입 테스트"""
        audio_error = AudioError(
            error_type=AudioErrorType.LOW_QUALITY,
            message="Low quality"
        )
        
        response = self.error_handler.handle_general_error(audio_error, "test_context")
        
        # 특정 타입은 해당 핸들러로 처리되어야 함
        assert response.action == ErrorAction.REQUEST_RETRY
        assert "음성이 명확하지 않습니다" in response.message
    
    def test_handle_general_error_unknown_type(self):
        """일반 오류 처리 - 알 수 없는 타입 테스트"""
        error = ValueError("Unknown error")
        
        response = self.error_handler.handle_general_error(error, "test_context")
        
        assert response.action == ErrorAction.REQUEST_RETRY
        assert response.can_recover is True
        assert "처리 중 오류가 발생했습니다" in response.message
        assert response.metadata["context"] == "test_context"
    
    def test_handle_general_error_max_retries(self):
        """일반 오류 처리 - 최대 재시도 테스트"""
        error = ValueError("Unknown error")
        
        # 최대 재시도 횟수만큼 오류 발생시키기
        for _ in range(self.error_handler.max_retry_count):
            self.error_handler.handle_general_error(error, "test_context")
        
        response = self.error_handler.handle_general_error(error, "test_context")
        assert response.action == ErrorAction.ESCALATE_TO_HUMAN
        assert response.can_recover is False
        assert "지속되고 있습니다" in response.message
    
    def test_error_count_management(self):
        """오류 카운트 관리 테스트"""
        error_key = "test_error"
        
        # 초기 카운트는 0
        assert self.error_handler.get_error_count(error_key) == 0
        
        # 카운트 증가 테스트
        count = self.error_handler._get_and_increment_error_count(error_key)
        assert count == 0
        assert self.error_handler.get_error_count(error_key) == 1
        
        # 다시 증가
        count = self.error_handler._get_and_increment_error_count(error_key)
        assert count == 1
        assert self.error_handler.get_error_count(error_key) == 2
        
        # 리셋 테스트
        self.error_handler.reset_error_count(error_key)
        assert self.error_handler.get_error_count(error_key) == 0
    
    def test_reset_all_error_counts(self):
        """모든 오류 카운트 리셋 테스트"""
        # 여러 오류 카운트 생성
        self.error_handler._get_and_increment_error_count("error1")
        self.error_handler._get_and_increment_error_count("error2")
        self.error_handler._get_and_increment_error_count("error3")
        
        assert len(self.error_handler.error_counts) == 3
        
        # 모든 카운트 리셋
        self.error_handler.reset_all_error_counts()
        assert len(self.error_handler.error_counts) == 0
    
    def test_error_history_logging(self):
        """오류 히스토리 로깅 테스트"""
        # 초기 히스토리는 비어있음
        assert len(self.error_handler.error_history) == 0
        
        # 오류 처리 시 히스토리에 기록됨
        error = AudioError(
            error_type=AudioErrorType.LOW_QUALITY,
            message="Low quality"
        )
        
        self.error_handler.handle_audio_error(error)
        
        assert len(self.error_handler.error_history) == 1
        history_entry = self.error_handler.error_history[0]
        assert history_entry["category"] == "audio"
        assert history_entry["error_type"] == "low_quality"
        assert history_entry["retry_count"] == 0
        assert isinstance(history_entry["timestamp"], datetime)
    
    def test_error_history_size_limit(self):
        """오류 히스토리 크기 제한 테스트"""
        # 100개 이상의 오류 생성
        for i in range(105):
            self.error_handler._log_error_history(
                "test", "test_error", f"Error {i}", 0
            )
        
        # 최근 100개만 유지되어야 함
        assert len(self.error_handler.error_history) == 100
        
        # 가장 오래된 것들이 제거되고 최근 것들만 남아있어야 함
        assert self.error_handler.error_history[0]["message"] == "Error 5"
        assert self.error_handler.error_history[-1]["message"] == "Error 104"
    
    def test_get_error_statistics(self):
        """오류 통계 반환 테스트"""
        # 몇 개의 오류 생성
        error = AudioError(
            error_type=AudioErrorType.LOW_QUALITY,
            message="Low quality"
        )
        
        self.error_handler.handle_audio_error(error)
        self.error_handler.handle_audio_error(error)
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 2
        assert "audio_low_quality" in stats["error_counts"]
        assert stats["error_counts"]["audio_low_quality"] == 2
        assert len(stats["recent_errors"]) == 2
        assert stats["max_retry_count"] == 3
    
    def test_is_critical_error_threshold_reached(self):
        """임계 오류 횟수 도달 확인 테스트"""
        error_key = "test_error"
        
        # 임계값 미달
        assert not self.error_handler.is_critical_error_threshold_reached(error_key, 5)
        
        # 임계값까지 오류 발생
        for _ in range(5):
            self.error_handler._get_and_increment_error_count(error_key)
        
        # 임계값 도달
        assert self.error_handler.is_critical_error_threshold_reached(error_key, 5)
    
    @patch('src.error.handler.logging.getLogger')
    def test_logger_usage(self, mock_get_logger):
        """로거 사용 테스트"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ErrorHandler(logger=mock_logger)
        
        error = AudioError(
            error_type=AudioErrorType.LOW_QUALITY,
            message="Low quality"
        )
        
        handler.handle_audio_error(error)
        
        # 로거가 호출되었는지 확인
        mock_logger.warning.assert_called_once()


class TestErrorRecoveryManager:
    """ErrorRecoveryManager 클래스 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.error_handler = ErrorHandler()
        self.recovery_manager = ErrorRecoveryManager(self.error_handler)
    
    def test_init(self):
        """초기화 테스트"""
        assert self.recovery_manager.error_handler == self.error_handler
        assert self.recovery_manager.logger is not None
    
    def test_attempt_recovery_not_recoverable(self):
        """복구 불가능한 오류 테스트"""
        error_response = ErrorResponse(
            message="Critical error",
            action=ErrorAction.ESCALATE_TO_HUMAN,
            can_recover=False
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is False
    
    def test_attempt_recovery_retry(self):
        """재시도 복구 테스트"""
        error_response = ErrorResponse(
            message="Retry error",
            action=ErrorAction.REQUEST_RETRY,
            can_recover=True
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is True
    
    def test_attempt_recovery_clarification(self):
        """명확화 복구 테스트"""
        error_response = ErrorResponse(
            message="Clarification needed",
            action=ErrorAction.REQUEST_CLARIFICATION,
            can_recover=True
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is True
    
    def test_attempt_recovery_fallback(self):
        """대체 모드 복구 테스트"""
        error_response = ErrorResponse(
            message="Fallback needed",
            action=ErrorAction.FALLBACK_MODE,
            can_recover=True
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is True
    
    def test_attempt_recovery_escalation(self):
        """에스컬레이션 복구 테스트"""
        error_response = ErrorResponse(
            message="Escalate to human",
            action=ErrorAction.ESCALATE_TO_HUMAN,
            can_recover=True
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is False  # 사람 개입 필요
    
    def test_attempt_recovery_restart(self):
        """시스템 재시작 복구 테스트"""
        error_response = ErrorResponse(
            message="System restart needed",
            action=ErrorAction.SYSTEM_RESTART,
            can_recover=True
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is True
    
    def test_attempt_recovery_ignore(self):
        """무시 복구 테스트"""
        error_response = ErrorResponse(
            message="Ignore error",
            action=ErrorAction.IGNORE,
            can_recover=True
        )
        
        result = self.recovery_manager.attempt_recovery(error_response)
        assert result is True
    
    def test_attempt_recovery_with_context(self):
        """컨텍스트와 함께 복구 테스트"""
        error_response = ErrorResponse(
            message="Error with context",
            action=ErrorAction.REQUEST_RETRY,
            can_recover=True
        )
        
        context = {"user_id": "test_user", "session_id": "test_session"}
        result = self.recovery_manager.attempt_recovery(error_response, context)
        assert result is True
    
    def test_attempt_recovery_exception_handling(self):
        """복구 중 예외 처리 테스트"""
        error_response = ErrorResponse(
            message="Error",
            action=ErrorAction.REQUEST_RETRY,
            can_recover=True
        )
        
        # 복구 전략에서 예외 발생하도록 모킹
        with patch.object(self.recovery_manager, '_retry_recovery', side_effect=Exception("Recovery failed")):
            result = self.recovery_manager.attempt_recovery(error_response)
            assert result is False
    
    @patch('src.error.handler.logging.getLogger')
    def test_recovery_logging(self, mock_get_logger):
        """복구 로깅 테스트"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        recovery_manager = ErrorRecoveryManager(self.error_handler)
        recovery_manager.logger = mock_logger
        
        error_response = ErrorResponse(
            message="Test error",
            action=ErrorAction.REQUEST_RETRY,
            can_recover=True
        )
        
        recovery_manager.attempt_recovery(error_response)
        
        # 로거가 호출되었는지 확인
        mock_logger.info.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])