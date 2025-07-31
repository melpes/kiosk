"""
클라이언트-서버 통신용 데이터 모델 (클라이언트 전용)
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class UIActionType(Enum):
    """UI 액션 타입"""
    SHOW_MENU = "show_menu"
    SHOW_PAYMENT = "show_payment"
    SHOW_OPTIONS = "show_options"
    UPDATE_ORDER = "update_order"
    SHOW_CONFIRMATION = "show_confirmation"
    SHOW_ERROR = "show_error"


class ErrorCode(Enum):
    """오류 코드"""
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    AUDIO_PROCESSING_ERROR = "audio_processing_error"
    SPEECH_RECOGNITION_ERROR = "speech_recognition_error"
    INTENT_RECOGNITION_ERROR = "intent_recognition_error"
    ORDER_PROCESSING_ERROR = "order_processing_error"
    PAYMENT_ERROR = "payment_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MenuItemData:
    """메뉴 아이템 데이터"""
    item_id: str
    name: str
    price: float
    quantity: int = 1
    options: List[str] = field(default_factory=list)
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MenuItemData':
        """딕셔너리에서 생성"""
        return cls(**data)


@dataclass
class MenuOption:
    """메뉴 선택 옵션"""
    option_id: str
    display_text: str
    category: str
    price: Optional[float] = None
    description: Optional[str] = None
    available: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MenuOption':
        """딕셔너리에서 생성"""
        return cls(**data)


@dataclass
class PaymentData:
    """결제 정보"""
    total_amount: float
    payment_methods: List[str]
    order_summary: List[Dict[str, Any]]
    tax_amount: float = 0.0
    service_charge: float = 0.0
    discount_amount: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaymentData':
        """딕셔너리에서 생성"""
        return cls(**data)


@dataclass
class ErrorInfo:
    """오류 정보"""
    error_code: str
    error_message: str
    recovery_actions: List[str]
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorInfo':
        """딕셔너리에서 생성"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def from_exception(cls, error_code: ErrorCode, exception: Exception, 
                      recovery_actions: List[str] = None) -> 'ErrorInfo':
        """예외에서 생성"""
        if recovery_actions is None:
            recovery_actions = ["다시 시도해주세요"]
        
        return cls(
            error_code=error_code.value,
            error_message=str(exception),
            recovery_actions=recovery_actions,
            details={"exception_type": type(exception).__name__}
        )


@dataclass
class UIAction:
    """UI 액션 정보"""
    action_type: str
    data: Dict[str, Any]
    priority: int = 0
    requires_user_input: bool = False
    timeout_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIAction':
        """딕셔너리에서 생성"""
        return cls(**data)
    
    @classmethod
    def show_menu(cls, menu_options: List[MenuOption], category: str = None) -> 'UIAction':
        """메뉴 표시 액션 생성"""
        return cls(
            action_type=UIActionType.SHOW_MENU.value,
            data={
                "menu_options": [option.to_dict() for option in menu_options],
                "category": category
            },
            requires_user_input=True
        )
    
    @classmethod
    def show_payment(cls, payment_data: PaymentData) -> 'UIAction':
        """결제 화면 표시 액션 생성"""
        return cls(
            action_type=UIActionType.SHOW_PAYMENT.value,
            data=payment_data.to_dict(),
            requires_user_input=True,
            timeout_seconds=300  # 5분 타임아웃
        )
    
    @classmethod
    def update_order(cls, order_data: 'OrderData') -> 'UIAction':
        """주문 상태 업데이트 액션 생성"""
        return cls(
            action_type=UIActionType.UPDATE_ORDER.value,
            data=order_data.to_dict(),
            priority=1
        )
    
    @classmethod
    def show_confirmation(cls, message: str, options: List[str] = None) -> 'UIAction':
        """확인 화면 표시 액션 생성"""
        if options is None:
            options = ["예", "아니오"]
        
        return cls(
            action_type=UIActionType.SHOW_CONFIRMATION.value,
            data={
                "message": message,
                "options": options
            },
            requires_user_input=True,
            timeout_seconds=30
        )


@dataclass
class OrderData:
    """주문 상태 데이터"""
    order_id: Optional[str]
    items: List[Dict[str, Any]]
    total_amount: float
    status: str
    requires_confirmation: bool
    item_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderData':
        """딕셔너리에서 생성"""
        return cls(**data)


@dataclass
class ServerResponse:
    """서버 응답 데이터"""
    success: bool
    message: str
    tts_audio_url: Optional[str] = None
    order_data: Optional[OrderData] = None
    ui_actions: List[UIAction] = field(default_factory=list)
    error_info: Optional[ErrorInfo] = None
    processing_time: float = 0.0
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = {
            'success': self.success,
            'message': self.message,
            'tts_audio_url': self.tts_audio_url,
            'order_data': self.order_data.to_dict() if self.order_data else None,
            'ui_actions': [action.to_dict() for action in self.ui_actions],
            'error_info': self.error_info.to_dict() if self.error_info else None,
            'processing_time': self.processing_time,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat()
        }
        return data
    
    def to_json(self) -> str:
        """JSON 문자열로 직렬화"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerResponse':
        """딕셔너리에서 생성"""
        # UI 액션들 복원
        ui_actions = []
        if data.get('ui_actions'):
            ui_actions = [UIAction.from_dict(action_data) for action_data in data['ui_actions']]
        
        # 주문 데이터 복원
        order_data = None
        if data.get('order_data'):
            order_data = OrderData.from_dict(data['order_data'])
        
        # 오류 정보 복원
        error_info = None
        if data.get('error_info'):
            error_info = ErrorInfo.from_dict(data['error_info'])
        
        # 타임스탬프 복원
        timestamp = datetime.now()
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            success=data['success'],
            message=data['message'],
            tts_audio_url=data.get('tts_audio_url'),
            order_data=order_data,
            ui_actions=ui_actions,
            error_info=error_info,
            processing_time=data.get('processing_time', 0.0),
            session_id=data.get('session_id'),
            timestamp=timestamp
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ServerResponse':
        """JSON 문자열에서 역직렬화"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create_error_response(cls, error_info: ErrorInfo, 
                            session_id: str = None) -> 'ServerResponse':
        """오류 응답 생성"""
        ui_actions = [UIAction(
            action_type=UIActionType.SHOW_ERROR.value,
            data={
                "error_message": error_info.error_message,
                "recovery_actions": error_info.recovery_actions
            }
        )]
        
        return cls(
            success=False,
            message=error_info.error_message,
            error_info=error_info,
            ui_actions=ui_actions,
            session_id=session_id
        )
    
    @classmethod
    def create_success_response(cls, message: str, 
                              order_data: OrderData = None,
                              tts_audio_url: str = None,
                              ui_actions: List[UIAction] = None,
                              processing_time: float = 0.0,
                              session_id: str = None) -> 'ServerResponse':
        """성공 응답 생성"""
        if ui_actions is None:
            ui_actions = []
        
        return cls(
            success=True,
            message=message,
            tts_audio_url=tts_audio_url,
            order_data=order_data,
            ui_actions=ui_actions,
            processing_time=processing_time,
            session_id=session_id
        )