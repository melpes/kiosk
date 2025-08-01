"""
대화 처리 관련 데이터 모델
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime


class IntentType(Enum):
    """의도 타입"""
    ORDER = "order"          # 주문
    MODIFY = "modify"        # 변경
    CANCEL = "cancel"        # 취소
    PAYMENT = "payment"      # 결제
    INQUIRY = "inquiry"      # 문의
    UNKNOWN = "unknown"      # 알 수 없음


@dataclass
class Modification:
    """주문 변경 정보"""
    item_name: str           # 변경할 아이템명
    action: str              # 변경 액션 (add, remove, change_quantity, change_option)
    new_quantity: Optional[int] = None      # 새로운 수량
    new_options: Optional[Dict[str, str]] = None  # 새로운 옵션


@dataclass
class Intent:
    """사용자 의도"""
    type: IntentType                        # 의도 타입
    confidence: float                       # 신뢰도
    menu_items: Optional[List[Any]] = None     # 주문할 메뉴 아이템들
    modifications: Optional[List[Modification]] = None  # 변경 사항들
    cancel_items: Optional[List[str]] = None           # 취소할 아이템명들
    payment_method: Optional[str] = None               # 결제 방법
    inquiry_text: Optional[str] = None                 # 문의 내용
    raw_text: Optional[str] = None                     # 원본 텍스트
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """데이터 검증"""
        if not isinstance(self.type, IntentType):
            raise ValueError("의도 타입은 IntentType이어야 합니다")
        
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("신뢰도는 0.0과 1.0 사이의 값이어야 합니다")
        
        # 의도 타입별 필수 필드 검증
        if self.type == IntentType.ORDER and not self.menu_items:
            raise ValueError("주문 의도에는 메뉴 아이템이 필요합니다")
        
        if self.type == IntentType.MODIFY and not self.modifications:
            raise ValueError("변경 의도에는 변경 사항이 필요합니다")
        
        # CANCEL intent는 cancel_items가 비어있어도 허용 (전체 주문 취소 의미)
        # if self.type == IntentType.CANCEL and not self.cancel_items:
        #     raise ValueError("취소 의도에는 취소할 아이템이 필요합니다")
    
    @property
    def is_high_confidence(self) -> bool:
        """높은 신뢰도 여부"""
        return self.confidence >= 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'type': self.type.value,
            'confidence': self.confidence,
            'menu_items': [item.to_dict() for item in self.menu_items] if self.menu_items else None,
            'modifications': [
                {
                    'item_name': mod.item_name,
                    'action': mod.action,
                    'new_quantity': mod.new_quantity,
                    'new_options': mod.new_options
                } for mod in self.modifications
            ] if self.modifications else None,
            'cancel_items': self.cancel_items,
            'payment_method': self.payment_method,
            'inquiry_text': self.inquiry_text,
            'raw_text': self.raw_text,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ConversationContext:
    """대화 컨텍스트"""
    session_id: str                         # 세션 ID
    conversation_history: List[Dict[str, str]] = field(default_factory=list)  # 대화 기록
    current_order: Optional[Any] = None  # 현재 주문
    user_preferences: Dict[str, Any] = field(default_factory=dict)  # 사용자 선호도
    last_intent: Optional[Intent] = None     # 마지막 의도
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, order_id: Optional[str] = None):
        """메시지 추가"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'order_id': order_id
        })
    
    def get_recent_messages(self, count: int = 5) -> List[Dict[str, str]]:
        """최근 메시지 가져오기"""
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def get_messages_by_order_id(self, order_id: str, count: int = 10) -> List[Dict[str, str]]:
        """특정 주문 ID의 메시지만 가져오기"""
        if not order_id:
            return []
        
        order_messages = [
            msg for msg in self.conversation_history 
            if msg.get('order_id') == order_id
        ]
        return order_messages[-count:] if order_messages else []


@dataclass
class DialogueResponse:
    """대화 응답"""
    text: str                               # 응답 텍스트
    order_state: Optional[Any] = None  # 주문 상태
    requires_confirmation: bool = False      # 확인 필요 여부
    suggested_actions: List[str] = field(default_factory=list)  # 제안 액션들
    metadata: Dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터
    
    def __post_init__(self):
        """데이터 검증"""
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("응답 텍스트는 비어있을 수 없습니다")