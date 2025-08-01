"""
오류 처리 관련 데이터 모델
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class ErrorAction(Enum):
    """오류 처리 액션"""
    REQUEST_RETRY = "request_retry"              # 재시도 요청
    REQUEST_CLARIFICATION = "request_clarification"  # 명확화 요청
    FALLBACK_MODE = "fallback_mode"              # 대체 모드
    ESCALATE_TO_HUMAN = "escalate_to_human"      # 직원 호출
    SYSTEM_RESTART = "system_restart"           # 시스템 재시작
    IGNORE = "ignore"                            # 무시


class AudioErrorType(Enum):
    """음성 오류 타입"""
    LOW_QUALITY = "low_quality"                  # 낮은 음질
    NO_INPUT = "no_input"                        # 입력 없음
    TOO_LOUD = "too_loud"                        # 너무 큰 소리
    TOO_QUIET = "too_quiet"                      # 너무 작은 소리
    MULTIPLE_SPEAKERS = "multiple_speakers"       # 다중 화자
    BACKGROUND_NOISE = "background_noise"         # 배경 소음
    PROCESSING_FAILED = "processing_failed"       # 처리 실패
    INVALID_FORMAT = "invalid_format"            # 잘못된 포맷
    FILE_LOAD_FAILED = "file_load_failed"        # 파일 로드 실패
    FEATURE_EXTRACTION_FAILED = "feature_extraction_failed"  # 특징 추출 실패


class RecognitionErrorType(Enum):
    """음성인식 오류 타입"""
    LOW_CONFIDENCE = "low_confidence"            # 낮은 신뢰도
    MODEL_ERROR = "model_error"                  # 모델 오류
    MODEL_NOT_LOADED = "model_not_loaded"        # 모델 미로드
    MODEL_LOAD_FAILED = "model_load_failed"      # 모델 로드 실패
    RECOGNITION_FAILED = "recognition_failed"    # 인식 실패
    INVALID_INPUT = "invalid_input"              # 잘못된 입력
    TIMEOUT = "timeout"                          # 시간 초과
    LANGUAGE_MISMATCH = "language_mismatch"      # 언어 불일치
    TOKENIZATION_ERROR = "tokenization_error"    # 토큰화 오류


class IntentErrorType(Enum):
    """의도 파악 오류 타입"""
    AMBIGUOUS_INTENT = "ambiguous_intent"        # 모호한 의도
    UNKNOWN_INTENT = "unknown_intent"            # 알 수 없는 의도
    LLM_API_ERROR = "llm_api_error"             # LLM API 오류
    TOOL_CALLING_ERROR = "tool_calling_error"    # Tool calling 오류
    CONTEXT_ERROR = "context_error"              # 컨텍스트 오류
    RECOGNITION_FAILED = "recognition_failed"    # 의도 파악 실패


class OrderErrorType(Enum):
    """주문 오류 타입"""
    ITEM_NOT_FOUND = "item_not_found"           # 메뉴 아이템 없음
    ITEM_UNAVAILABLE = "item_unavailable"       # 메뉴 아이템 판매 불가
    INVALID_QUANTITY = "invalid_quantity"        # 잘못된 수량
    INVALID_OPTION = "invalid_option"           # 잘못된 옵션
    ITEM_NOT_IN_ORDER = "item_not_in_order"     # 주문에 없는 아이템
    NO_ACTIVE_ORDER = "no_active_order"         # 활성 주문 없음
    INVALID_ORDER_STATE = "invalid_order_state" # 잘못된 주문 상태
    EMPTY_ORDER = "empty_order"                 # 빈 주문
    INVALID_ITEM = "invalid_item"               # 유효하지 않은 아이템
    ORDER_CONFLICT = "order_conflict"           # 주문 충돌
    PAYMENT_ERROR = "payment_error"             # 결제 오류
    SYSTEM_ERROR = "system_error"               # 시스템 오류


class ValidationError(Exception):
    """데이터 검증 오류"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()


class ConfigurationError(Exception):
    """설정 오류"""
    def __init__(self, message: str, config_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.config_path = config_path
        self.details = details or {}
        self.timestamp = datetime.now()


@dataclass
class AudioError(Exception):
    """음성 처리 오류"""
    error_type: AudioErrorType   # 오류 타입
    message: str                 # 오류 메시지
    details: Optional[Dict[str, Any]] = None  # 추가 세부 정보
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        super().__init__(self.message)


@dataclass
class RecognitionError(Exception):
    """음성인식 오류"""
    error_type: RecognitionErrorType   # 오류 타입
    message: str                 # 오류 메시지
    confidence: Optional[float] = None  # 신뢰도 (해당하는 경우)
    processing_time: Optional[float] = None  # 처리 시간 (해당하는 경우)
    details: Optional[Dict[str, Any]] = None  # 추가 세부 정보
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        super().__init__(self.message)


@dataclass
class IntentError(Exception):
    """의도 파악 오류"""
    error_type: IntentErrorType  # 오류 타입
    message: str                 # 오류 메시지
    raw_text: Optional[str] = None  # 원본 텍스트
    details: Optional[Dict[str, Any]] = None  # 추가 세부 정보
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        super().__init__(self.message)


@dataclass
class OrderError(Exception):
    """주문 처리 오류"""
    error_type: OrderErrorType   # 오류 타입
    message: str                 # 오류 메시지
    item_name: Optional[str] = None  # 관련 메뉴 아이템명
    details: Optional[Dict[str, Any]] = None  # 추가 세부 정보
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        super().__init__(self.message)


@dataclass
class ErrorResponse:
    """오류 응답"""
    message: str                 # 사용자에게 표시할 메시지
    action: ErrorAction          # 권장 액션
    retry_count: int = 0         # 재시도 횟수
    can_recover: bool = True     # 복구 가능 여부
    suggested_alternatives: list = None  # 제안 대안들
    metadata: Optional[Dict[str, Any]] = None  # 추가 메타데이터
    
    def __post_init__(self):
        if self.suggested_alternatives is None:
            self.suggested_alternatives = []
        
        if not self.message or not self.message.strip():
            raise ValueError("오류 메시지는 비어있을 수 없습니다")
        
        if not isinstance(self.action, ErrorAction):
            raise ValueError("액션은 ErrorAction 타입이어야 합니다")


