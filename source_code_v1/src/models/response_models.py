"""
응답 관련 데이터 모델
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class ResponseType(Enum):
    """응답 타입"""
    GREETING = "greeting"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_SUMMARY = "order_summary"
    PAYMENT_REQUEST = "payment_request"
    ERROR = "error"
    CLARIFICATION = "clarification"
    COMPLETION = "completion"


class ResponseFormat(Enum):
    """응답 포맷"""
    TEXT = "text"
    STRUCTURED = "structured"
    TEMPLATE = "template"


@dataclass
class ResponseTemplate:
    """응답 템플릿"""
    template_id: str
    template_text: str
    variables: Dict[str, str]
    response_type: ResponseType
    
    def format(self, **kwargs) -> str:
        """템플릿을 포맷팅하여 실제 응답 텍스트 생성"""
        try:
            return self.template_text.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"템플릿 변수 누락: {e}")


@dataclass
class TextResponse:
    """텍스트 응답"""
    text: str
    response_type: ResponseType
    format_type: ResponseFormat
    template_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class FormattedResponse:
    """포맷팅된 응답"""
    original_text: str
    formatted_text: str
    response_type: ResponseType
    formatting_applied: bool
    formatting_rules: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()