"""
주문 관리 관련 데이터 모델
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from decimal import Decimal


class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "pending"          # 대기 중
    CONFIRMED = "confirmed"      # 확인됨
    PREPARING = "preparing"      # 준비 중
    READY = "ready"             # 준비 완료
    COMPLETED = "completed"      # 완료
    CANCELLED = "cancelled"      # 취소됨


@dataclass
class MenuItem:
    """메뉴 아이템"""
    name: str                    # 메뉴명
    category: str                # 카테고리 (단품, 세트, 라지세트)
    quantity: int                # 수량
    price: Decimal               # 가격
    options: Dict[str, str] = field(default_factory=dict)  # 옵션 (음료 변경 등)
    item_id: Optional[str] = None  # 아이템 ID
    created_at: datetime = field(default_factory=datetime.now)  # 생성 시간
    updated_at: datetime = field(default_factory=datetime.now)  # 수정 시간
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.name or not self.name.strip():
            raise ValueError("메뉴명은 비어있을 수 없습니다")
        
        if not self.category or not self.category.strip():
            raise ValueError("카테고리는 비어있을 수 없습니다")
        
        if self.quantity <= 0:
            raise ValueError("수량은 양수여야 합니다")
        
        if self.price < 0:
            raise ValueError("가격은 음수일 수 없습니다")
        
        # 가격을 Decimal로 변환
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
    
    @property
    def total_price(self) -> Decimal:
        """총 가격 (수량 * 단가)"""
        return self.price * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'price': float(self.price),
            'options': self.options,
            'item_id': self.item_id,
            'total_price': float(self.total_price)
        }
    
    def __str__(self) -> str:
        options_str = f" ({', '.join(f'{k}: {v}' for k, v in self.options.items())})" if self.options else ""
        return f"{self.name}{options_str} x{self.quantity} - {self.total_price}원"


@dataclass
class Order:
    """주문"""
    items: List[MenuItem] = field(default_factory=list)  # 주문 아이템들
    status: OrderStatus = OrderStatus.PENDING            # 주문 상태
    created_at: datetime = field(default_factory=datetime.now)  # 생성 시간
    updated_at: datetime = field(default_factory=datetime.now)  # 수정 시간
    order_id: Optional[str] = None                       # 주문 ID
    customer_info: Dict[str, str] = field(default_factory=dict)  # 고객 정보
    subtotal: Decimal = field(default_factory=lambda: Decimal('0'))  # 소계
    tax_amount: Decimal = field(default_factory=lambda: Decimal('0'))  # 세금
    service_charge: Decimal = field(default_factory=lambda: Decimal('0'))  # 서비스 요금
    
    def add_item(self, item: MenuItem):
        """아이템 추가"""
        if not isinstance(item, MenuItem):
            raise ValueError("MenuItem 객체여야 합니다")
        
        # 동일한 아이템이 있는지 확인 (이름과 옵션이 같은 경우)
        existing_item = self._find_existing_item(item)
        if existing_item:
            existing_item.quantity += item.quantity
        else:
            self.items.append(item)
        
        self.updated_at = datetime.now()
    
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """아이템 제거"""
        for item in self.items:
            if item.name == item_name:
                if item.quantity <= quantity:
                    self.items.remove(item)
                else:
                    item.quantity -= quantity
                self.updated_at = datetime.now()
                return True
        return False
    
    def clear(self):
        """주문 초기화"""
        self.items.clear()
        self.status = OrderStatus.PENDING
        self.updated_at = datetime.now()
    
    def _find_existing_item(self, new_item: MenuItem) -> Optional[MenuItem]:
        """동일한 아이템 찾기"""
        for item in self.items:
            if item.name == new_item.name and item.options == new_item.options:
                return item
        return None
    
    @property
    def total_amount(self) -> Decimal:
        """총 주문 금액"""
        return sum(item.total_price for item in self.items)
    
    @property
    def item_count(self) -> int:
        """총 아이템 수"""
        return sum(item.quantity for item in self.items)
    
    @property
    def is_empty(self) -> bool:
        """주문이 비어있는지 확인"""
        return len(self.items) == 0
    
    def get_summary(self) -> 'OrderSummary':
        """주문 요약 반환"""
        return OrderSummary(
            order_id=self.order_id,
            items=self.items.copy(),
            total_amount=self.total_amount,
            item_count=len(self.items),  # 아이템 종류 수
            total_quantity=self.item_count,  # 총 수량
            status=self.status,
            created_at=self.created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'order_id': self.order_id,
            'items': [item.to_dict() for item in self.items],
            'total_amount': float(self.total_amount),
            'item_count': self.item_count,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'customer_info': self.customer_info
        }


@dataclass
class OrderResult:
    """주문 처리 결과"""
    success: bool                # 성공 여부
    order: Optional[Order] = None  # 주문 객체
    message: str = ""            # 결과 메시지
    error_code: Optional[str] = None  # 오류 코드
    added_item: Optional[MenuItem] = None  # 추가된 아이템 정보
    
    def __post_init__(self):
        """데이터 검증"""
        # 성공한 경우에만 주문 객체가 필요 (실패한 경우는 None일 수 있음)
        pass


@dataclass
class OrderSummary:
    """주문 요약"""
    order_id: Optional[str]      # 주문 ID
    items: List[MenuItem]        # 주문 아이템들
    total_amount: Decimal        # 총 금액
    item_count: int              # 총 아이템 종류 수
    total_quantity: int          # 총 수량
    status: OrderStatus          # 주문 상태
    created_at: datetime         # 생성 시간
    
    def __str__(self) -> str:
        items_str = "\n".join(f"- {item}" for item in self.items)
        return f"""주문 요약:
{items_str}
총 {self.item_count}개 아이템, 총 금액: {self.total_amount}원
상태: {self.status.value}"""