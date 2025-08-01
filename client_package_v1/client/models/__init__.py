"""
클라이언트 데이터 모델 패키지
"""

from .communication_models import (
    ServerResponse,
    OrderData,
    UIAction,
    MenuOption,
    PaymentData,
    ErrorInfo,
    UIActionType,
    ErrorCode
)

__all__ = [
    "ServerResponse",
    "OrderData", 
    "UIAction",
    "MenuOption",
    "PaymentData",
    "ErrorInfo",
    "UIActionType",
    "ErrorCode"
]