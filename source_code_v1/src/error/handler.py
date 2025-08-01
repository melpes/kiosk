"""
오류 처리 시스템
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime

from ..models.error_models import (
    ErrorAction, ErrorResponse,
    AudioError, AudioErrorType,
    RecognitionError, RecognitionErrorType,
    IntentError, IntentErrorType,
    OrderError, OrderErrorType,
    ValidationError, ConfigurationError
)


class ErrorHandler:
    """
    통합 오류 처리기
    
    각 모듈별 오류를 처리하고 사용자 친화적인 메시지를 생성합니다.
    오류 복구 메커니즘과 재시도 로직을 제공합니다.
    """
    
    def __init__(self, max_retry_count: int = 3, logger: Optional[logging.Logger] = None):
        """
        ErrorHandler 초기화
        
        Args:
            max_retry_count: 최대 재시도 횟수
            logger: 로거 인스턴스
        """
        self.max_retry_count = max_retry_count
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.logger = logger or logging.getLogger(__name__)
        
        # 오류 메시지 템플릿
        self._init_error_templates()
    
    def _init_error_templates(self):
        """오류 메시지 템플릿 초기화"""
        self.audio_error_templates = {
            AudioErrorType.LOW_QUALITY: "음성이 명확하지 않습니다. 다시 말씀해 주세요.",
            AudioErrorType.NO_INPUT: "음성이 감지되지 않았습니다. 다시 말씀해 주세요.",
            AudioErrorType.TOO_LOUD: "음성이 너무 큽니다. 조금 더 작게 말씀해 주세요.",
            AudioErrorType.TOO_QUIET: "음성이 너무 작습니다. 조금 더 크게 말씀해 주세요.",
            AudioErrorType.MULTIPLE_SPEAKERS: "여러 명이 동시에 말씀하고 계십니다. 한 분씩 말씀해 주세요.",
            AudioErrorType.BACKGROUND_NOISE: "주변이 시끄럽습니다. 조금 더 크고 명확하게 말씀해 주세요.",
            AudioErrorType.PROCESSING_FAILED: "음성 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            AudioErrorType.INVALID_FORMAT: "지원하지 않는 음성 형식입니다.",
            AudioErrorType.FILE_LOAD_FAILED: "음성 파일을 불러올 수 없습니다.",
            AudioErrorType.FEATURE_EXTRACTION_FAILED: "음성 분석 중 오류가 발생했습니다."
        }
        
        self.recognition_error_templates = {
            RecognitionErrorType.LOW_CONFIDENCE: "정확히 듣지 못했습니다. 다시 주문해 주세요.",
            RecognitionErrorType.MODEL_ERROR: "음성 인식 모델에 오류가 발생했습니다.",
            RecognitionErrorType.MODEL_NOT_LOADED: "음성 인식 시스템을 준비 중입니다. 잠시만 기다려 주세요.",
            RecognitionErrorType.MODEL_LOAD_FAILED: "음성 인식 시스템을 시작할 수 없습니다.",
            RecognitionErrorType.RECOGNITION_FAILED: "음성을 인식할 수 없습니다. 다시 말씀해 주세요.",
            RecognitionErrorType.INVALID_INPUT: "올바르지 않은 음성 입력입니다.",
            RecognitionErrorType.TIMEOUT: "음성 처리 시간이 초과되었습니다. 다시 시도해 주세요.",
            RecognitionErrorType.LANGUAGE_MISMATCH: "지원하지 않는 언어입니다. 한국어로 말씀해 주세요.",
            RecognitionErrorType.TOKENIZATION_ERROR: "음성 처리 중 오류가 발생했습니다."
        }
        
        self.intent_error_templates = {
            IntentErrorType.AMBIGUOUS_INTENT: "요청하신 내용을 정확히 이해하지 못했습니다. 더 구체적으로 말씀해 주세요.",
            IntentErrorType.UNKNOWN_INTENT: "죄송합니다. 이해하지 못한 요청입니다. 다른 방식으로 말씀해 주세요.",
            IntentErrorType.LLM_API_ERROR: "시스템 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            IntentErrorType.TOOL_CALLING_ERROR: "요청 처리 중 오류가 발생했습니다.",
            IntentErrorType.CONTEXT_ERROR: "대화 맥락을 이해하지 못했습니다. 처음부터 다시 말씀해 주세요.",
            IntentErrorType.RECOGNITION_FAILED: "의도를 파악할 수 없습니다. 다시 말씀해 주세요."
        }
        
        self.order_error_templates = {
            OrderErrorType.ITEM_NOT_FOUND: "'{item_name}' 메뉴를 찾을 수 없습니다. 다른 메뉴를 선택해 주세요.",
            OrderErrorType.ITEM_UNAVAILABLE: "'{item_name}' 메뉴는 현재 판매하지 않습니다. 다른 메뉴를 선택해 주세요.",
            OrderErrorType.INVALID_QUANTITY: "수량이 올바르지 않습니다. 1개 이상으로 다시 말씀해 주세요.",
            OrderErrorType.INVALID_OPTION: "선택하신 옵션이 유효하지 않습니다. 다른 옵션을 선택해 주세요.",
            OrderErrorType.ITEM_NOT_IN_ORDER: "'{item_name}' 메뉴가 현재 주문에 없습니다. 주문 내역을 확인해 주세요.",
            OrderErrorType.NO_ACTIVE_ORDER: "진행 중인 주문이 없습니다. 먼저 메뉴를 주문해 주세요.",
            OrderErrorType.INVALID_ORDER_STATE: "현재 주문 상태에서는 해당 작업을 수행할 수 없습니다.",
            OrderErrorType.EMPTY_ORDER: "주문할 메뉴가 없습니다. 메뉴를 선택해 주세요.",
            OrderErrorType.INVALID_ITEM: "유효하지 않은 메뉴입니다.",
            OrderErrorType.ORDER_CONFLICT: "주문 처리 중 충돌이 발생했습니다.",
            OrderErrorType.PAYMENT_ERROR: "결제 처리 중 오류가 발생했습니다. 직원을 호출하겠습니다.",
            OrderErrorType.SYSTEM_ERROR: "시스템 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
        }
    
    def handle_audio_error(self, error: AudioError) -> ErrorResponse:
        """
        음성 처리 오류 처리
        
        Args:
            error: AudioError 인스턴스
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        error_key = f"audio_{error.error_type.value}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        # 오류 로깅
        self.logger.warning(f"Audio error: {error.error_type.value} - {error.message}")
        self._log_error_history("audio", error.error_type.value, error.message, retry_count)
        
        # 기본 메시지 가져오기
        message = self.audio_error_templates.get(
            error.error_type, 
            "음성 처리 중 오류가 발생했습니다."
        )
        
        # 오류 타입별 액션 결정
        if error.error_type in [AudioErrorType.LOW_QUALITY, AudioErrorType.NO_INPUT, 
                               AudioErrorType.TOO_LOUD, AudioErrorType.TOO_QUIET]:
            action = ErrorAction.REQUEST_RETRY
            can_recover = retry_count < self.max_retry_count
            
        elif error.error_type in [AudioErrorType.MULTIPLE_SPEAKERS, AudioErrorType.BACKGROUND_NOISE]:
            action = ErrorAction.REQUEST_CLARIFICATION
            can_recover = retry_count < self.max_retry_count
            
        elif error.error_type in [AudioErrorType.PROCESSING_FAILED, AudioErrorType.FEATURE_EXTRACTION_FAILED]:
            if retry_count < self.max_retry_count:
                action = ErrorAction.FALLBACK_MODE
                can_recover = True
            else:
                action = ErrorAction.ESCALATE_TO_HUMAN
                can_recover = False
                
        else:  # INVALID_FORMAT, FILE_LOAD_FAILED 등
            action = ErrorAction.ESCALATE_TO_HUMAN
            can_recover = False
        
        return ErrorResponse(
            message=message,
            action=action,
            retry_count=retry_count,
            can_recover=can_recover,
            metadata={"error_type": error.error_type.value, "details": error.details}
        )
    
    def handle_recognition_error(self, error: RecognitionError) -> ErrorResponse:
        """
        음성인식 오류 처리
        
        Args:
            error: RecognitionError 인스턴스
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        error_key = f"recognition_{error.error_type.value}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        # 오류 로깅
        self.logger.warning(f"Recognition error: {error.error_type.value} - {error.message}")
        self._log_error_history("recognition", error.error_type.value, error.message, retry_count)
        
        # 기본 메시지 가져오기
        message = self.recognition_error_templates.get(
            error.error_type,
            "음성 인식 중 오류가 발생했습니다."
        )
        
        # 오류 타입별 액션 결정
        if error.error_type in [RecognitionErrorType.LOW_CONFIDENCE, RecognitionErrorType.RECOGNITION_FAILED]:
            action = ErrorAction.REQUEST_CLARIFICATION
            can_recover = retry_count < self.max_retry_count
            
        elif error.error_type in [RecognitionErrorType.TIMEOUT, RecognitionErrorType.INVALID_INPUT]:
            action = ErrorAction.REQUEST_RETRY
            can_recover = retry_count < self.max_retry_count
            
        elif error.error_type == RecognitionErrorType.MODEL_NOT_LOADED:
            action = ErrorAction.FALLBACK_MODE
            can_recover = True
            message = "음성 인식 시스템을 준비 중입니다. 잠시만 기다려 주세요."
            
        else:  # MODEL_ERROR, MODEL_LOAD_FAILED 등
            action = ErrorAction.ESCALATE_TO_HUMAN
            can_recover = False
            message = "음성 인식 시스템에 문제가 발생했습니다. 직원을 호출하겠습니다."
        
        metadata = {
            "error_type": error.error_type.value,
            "confidence": error.confidence,
            "processing_time": error.processing_time,
            "details": error.details
        }
        
        return ErrorResponse(
            message=message,
            action=action,
            retry_count=retry_count,
            can_recover=can_recover,
            metadata=metadata
        )
    
    def handle_intent_error(self, error: IntentError) -> ErrorResponse:
        """
        의도 파악 오류 처리
        
        Args:
            error: IntentError 인스턴스
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        error_key = f"intent_{error.error_type.value}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        # 오류 로깅
        self.logger.warning(f"Intent error: {error.error_type.value} - {error.message}")
        self._log_error_history("intent", error.error_type.value, error.message, retry_count)
        
        # 기본 메시지 가져오기
        message = self.intent_error_templates.get(
            error.error_type,
            "요청을 처리할 수 없습니다."
        )
        
        # 제안 대안
        suggested_alternatives = []
        
        # 오류 타입별 액션 결정
        if error.error_type in [IntentErrorType.AMBIGUOUS_INTENT, IntentErrorType.UNKNOWN_INTENT]:
            action = ErrorAction.REQUEST_CLARIFICATION
            can_recover = retry_count < self.max_retry_count
            suggested_alternatives = ["주문하기", "변경하기", "취소하기", "결제하기", "주문 확인"]
            
        elif error.error_type == IntentErrorType.CONTEXT_ERROR:
            action = ErrorAction.REQUEST_CLARIFICATION
            can_recover = True
            message = "대화 맥락을 이해하지 못했습니다. 처음부터 다시 말씀해 주세요."
            
        elif error.error_type == IntentErrorType.LLM_API_ERROR:
            if retry_count < self.max_retry_count:
                action = ErrorAction.REQUEST_RETRY
                can_recover = True
            else:
                action = ErrorAction.ESCALATE_TO_HUMAN
                can_recover = False
                message = "시스템 처리 중 오류가 발생했습니다. 직원을 호출하겠습니다."
                
        else:  # TOOL_CALLING_ERROR, RECOGNITION_FAILED 등
            action = ErrorAction.REQUEST_CLARIFICATION
            can_recover = retry_count < self.max_retry_count
            message = "다시 말씀해 주세요."
        
        metadata = {
            "error_type": error.error_type.value,
            "raw_text": error.raw_text,
            "details": error.details
        }
        
        return ErrorResponse(
            message=message,
            action=action,
            retry_count=retry_count,
            can_recover=can_recover,
            suggested_alternatives=suggested_alternatives,
            metadata=metadata
        )
    
    def handle_order_error(self, error: OrderError) -> ErrorResponse:
        """
        주문 처리 오류 처리
        
        Args:
            error: OrderError 인스턴스
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        error_key = f"order_{error.error_type.value}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        # 오류 로깅
        self.logger.warning(f"Order error: {error.error_type.value} - {error.message}")
        self._log_error_history("order", error.error_type.value, error.message, retry_count)
        
        # 기본 메시지 가져오기
        message_template = self.order_error_templates.get(
            error.error_type,
            "주문 처리 중 오류가 발생했습니다."
        )
        
        # 메시지에 아이템명 삽입
        message = message_template.format(item_name=error.item_name) if error.item_name else message_template
        
        # 오류 타입별 액션 결정
        if error.error_type in [OrderErrorType.ITEM_NOT_FOUND, OrderErrorType.ITEM_UNAVAILABLE,
                               OrderErrorType.INVALID_QUANTITY, OrderErrorType.INVALID_OPTION,
                               OrderErrorType.ITEM_NOT_IN_ORDER, OrderErrorType.NO_ACTIVE_ORDER,
                               OrderErrorType.INVALID_ORDER_STATE, OrderErrorType.EMPTY_ORDER]:
            action = ErrorAction.REQUEST_CLARIFICATION
            can_recover = True
            
        elif error.error_type == OrderErrorType.PAYMENT_ERROR:
            action = ErrorAction.ESCALATE_TO_HUMAN
            can_recover = False
            
        elif error.error_type == OrderErrorType.SYSTEM_ERROR:
            if retry_count < self.max_retry_count:
                action = ErrorAction.REQUEST_RETRY
                can_recover = True
            else:
                action = ErrorAction.ESCALATE_TO_HUMAN
                can_recover = False
                message = "시스템 오류가 지속되고 있습니다. 직원을 호출하겠습니다."
                
        else:  # ORDER_CONFLICT, INVALID_ITEM 등
            action = ErrorAction.REQUEST_RETRY
            can_recover = retry_count < self.max_retry_count
        
        metadata = {
            "error_type": error.error_type.value,
            "item_name": error.item_name,
            "details": error.details
        }
        
        return ErrorResponse(
            message=message,
            action=action,
            retry_count=retry_count,
            can_recover=can_recover,
            metadata=metadata
        )
    
    def handle_validation_error(self, error: ValidationError) -> ErrorResponse:
        """
        데이터 검증 오류 처리
        
        Args:
            error: ValidationError 인스턴스
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        error_key = f"validation_{hash(error.message)}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        self.logger.warning(f"Validation error: {error.message}")
        self._log_error_history("validation", "validation_error", error.message, retry_count)
        
        return ErrorResponse(
            message=f"입력 데이터가 올바르지 않습니다: {error.message}",
            action=ErrorAction.REQUEST_CLARIFICATION,
            retry_count=retry_count,
            can_recover=True,
            metadata={"details": error.details}
        )
    
    def handle_configuration_error(self, error: ConfigurationError) -> ErrorResponse:
        """
        설정 오류 처리
        
        Args:
            error: ConfigurationError 인스턴스
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        error_key = f"config_{hash(error.message)}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        self.logger.error(f"Configuration error: {error.message}")
        self._log_error_history("configuration", "config_error", error.message, retry_count)
        
        return ErrorResponse(
            message="시스템 설정에 문제가 있습니다. 직원을 호출하겠습니다.",
            action=ErrorAction.ESCALATE_TO_HUMAN,
            retry_count=retry_count,
            can_recover=False,
            metadata={"config_path": error.config_path, "details": error.details}
        )
    
    def handle_general_error(self, error: Exception, context: str = "system") -> ErrorResponse:
        """
        일반적인 오류 처리
        
        Args:
            error: Exception 인스턴스
            context: 오류 발생 컨텍스트
            
        Returns:
            ErrorResponse: 처리된 오류 응답
        """
        # 특정 오류 타입별 처리
        if isinstance(error, AudioError):
            return self.handle_audio_error(error)
        elif isinstance(error, RecognitionError):
            return self.handle_recognition_error(error)
        elif isinstance(error, IntentError):
            return self.handle_intent_error(error)
        elif isinstance(error, OrderError):
            return self.handle_order_error(error)
        elif isinstance(error, ValidationError):
            return self.handle_validation_error(error)
        elif isinstance(error, ConfigurationError):
            return self.handle_configuration_error(error)
        
        # 일반적인 오류 처리
        error_key = f"{context}_{type(error).__name__}"
        retry_count = self._get_and_increment_error_count(error_key)
        
        self.logger.error(f"General error in {context}: {str(error)}")
        self._log_error_history(context, type(error).__name__, str(error), retry_count)
        
        if retry_count < self.max_retry_count:
            action = ErrorAction.REQUEST_RETRY
            can_recover = True
            message = "처리 중 오류가 발생했습니다. 다시 시도해 주세요."
        else:
            action = ErrorAction.ESCALATE_TO_HUMAN
            can_recover = False
            message = "시스템 오류가 지속되고 있습니다. 직원을 호출하겠습니다."
        
        return ErrorResponse(
            message=message,
            action=action,
            retry_count=retry_count,
            can_recover=can_recover,
            metadata={"error_type": type(error).__name__, "context": context}
        )
    
    def _get_and_increment_error_count(self, error_key: str) -> int:
        """오류 카운트 가져오기 및 증가"""
        current_count = self.error_counts.get(error_key, 0)
        self.error_counts[error_key] = current_count + 1
        return current_count
    
    def _log_error_history(self, category: str, error_type: str, message: str, retry_count: int):
        """오류 히스토리 로깅"""
        self.error_history.append({
            "timestamp": datetime.now(),
            "category": category,
            "error_type": error_type,
            "message": message,
            "retry_count": retry_count
        })
        
        # 히스토리 크기 제한 (최근 100개만 유지)
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def reset_error_count(self, error_key: str):
        """특정 오류의 카운트 리셋"""
        if error_key in self.error_counts:
            del self.error_counts[error_key]
            self.logger.info(f"Error count reset for: {error_key}")
    
    def reset_all_error_counts(self):
        """모든 오류 카운트 리셋"""
        self.error_counts.clear()
        self.logger.info("All error counts reset")
    
    def get_error_count(self, error_key: str) -> int:
        """특정 오류의 카운트 반환"""
        return self.error_counts.get(error_key, 0)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """오류 통계 반환"""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.error_history[-10:] if self.error_history else [],
            "max_retry_count": self.max_retry_count
        }
    
    def is_critical_error_threshold_reached(self, error_key: str, threshold: int = 5) -> bool:
        """임계 오류 횟수 도달 여부 확인"""
        return self.get_error_count(error_key) >= threshold


class ErrorRecoveryManager:
    """
    오류 복구 관리자
    
    오류 발생 시 시스템 복구를 위한 다양한 전략을 제공합니다.
    """
    
    def __init__(self, error_handler: ErrorHandler):
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
    
    def attempt_recovery(self, error_response: ErrorResponse, context: Dict[str, Any] = None) -> bool:
        """
        오류 복구 시도
        
        Args:
            error_response: 오류 응답
            context: 복구 컨텍스트
            
        Returns:
            bool: 복구 성공 여부
        """
        if not error_response.can_recover:
            self.logger.warning("Error is not recoverable")
            return False
        
        recovery_strategy = self._get_recovery_strategy(error_response.action)
        
        try:
            return recovery_strategy(error_response, context or {})
        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {str(e)}")
            return False
    
    def _get_recovery_strategy(self, action: ErrorAction):
        """복구 전략 선택"""
        strategies = {
            ErrorAction.REQUEST_RETRY: self._retry_recovery,
            ErrorAction.REQUEST_CLARIFICATION: self._clarification_recovery,
            ErrorAction.FALLBACK_MODE: self._fallback_recovery,
            ErrorAction.ESCALATE_TO_HUMAN: self._escalation_recovery,
            ErrorAction.SYSTEM_RESTART: self._restart_recovery,
            ErrorAction.IGNORE: self._ignore_recovery
        }
        
        return strategies.get(action, self._default_recovery)
    
    def _retry_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """재시도 복구"""
        self.logger.info("Attempting retry recovery")
        # 재시도 로직 구현
        return True
    
    def _clarification_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """명확화 복구"""
        self.logger.info("Attempting clarification recovery")
        # 명확화 요청 로직 구현
        return True
    
    def _fallback_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """대체 모드 복구"""
        self.logger.info("Attempting fallback recovery")
        # 대체 모드 전환 로직 구현
        return True
    
    def _escalation_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """에스컬레이션 복구"""
        self.logger.info("Escalating to human operator")
        # 직원 호출 로직 구현
        return False  # 사람 개입 필요
    
    def _restart_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """시스템 재시작 복구"""
        self.logger.info("Attempting system restart recovery")
        # 시스템 재시작 로직 구현
        return True
    
    def _ignore_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """무시 복구"""
        self.logger.info("Ignoring error")
        return True
    
    def _default_recovery(self, error_response: ErrorResponse, context: Dict[str, Any]) -> bool:
        """기본 복구"""
        self.logger.info("Attempting default recovery")
        return False