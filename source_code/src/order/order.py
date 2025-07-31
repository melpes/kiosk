"""
주문 관리 시스템
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..models.order_models import MenuItem, Order, OrderStatus, OrderResult, OrderSummary
from ..models.error_models import OrderErrorType
from .menu import Menu


class OrderManager:
    """주문 관리자 클래스"""
    
    def __init__(self, menu: Menu):
        self.menu = menu
        self.current_order: Optional[Order] = None
        self.order_history: List[Order] = []
    
    def create_new_order(self) -> Order:
        if self.current_order and self.current_order.status == OrderStatus.PENDING:
            self.current_order.status = OrderStatus.CANCELLED
            self.order_history.append(self.current_order)
        
        self.current_order = Order(
            order_id=str(uuid.uuid4()),
            items=[],
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return self.current_order
    
    def get_current_order(self) -> Optional[Order]:
        return self.current_order
    
    def add_item(self, item_name: str, quantity: int = 1, 
                 options: Optional[Dict[str, str]] = None) -> OrderResult:
        try:
            if not self.current_order:
                self.create_new_order()
            
            if self.current_order.status != OrderStatus.PENDING:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 아닙니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_ORDER_STATE.value
                )
            
            menu_item_config = self.menu.get_item(item_name)
            if not menu_item_config:
                return OrderResult(
                    success=False,
                    message=f"메뉴를 찾을 수 없습니다: {item_name}",
                    order=self.current_order,
                    error_code=OrderErrorType.ITEM_NOT_FOUND.value
                )
            
            if not menu_item_config.is_available:
                return OrderResult(
                    success=False,
                    message=f"현재 판매하지 않는 메뉴입니다: {item_name}",
                    order=self.current_order,
                    error_code=OrderErrorType.ITEM_UNAVAILABLE.value
                )
            
            if quantity <= 0:
                return OrderResult(
                    success=False,
                    message="수량은 1개 이상이어야 합니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_QUANTITY.value
                )
            
            if options:
                print(f"🔍 [DEBUG] 옵션 검증 시작 - 메뉴: {item_name}")
                print(f"🔍 [DEBUG] 전달된 옵션: {options}")
                print(f"🔍 [DEBUG] 허용된 옵션: {menu_item_config.available_options}")
                
                for option_key, option_value in options.items():
                    print(f"🔍 [DEBUG] 검증 중 - {option_key}={option_value}")
                    print(f"🔍 [DEBUG] option_value 타입: {type(option_value)}")
                    print(f"🔍 [DEBUG] option_value repr: {repr(option_value)}")
                    print(f"🔍 [DEBUG] available_options 타입: {type(menu_item_config.available_options)}")
                    print(f"🔍 [DEBUG] available_options: {menu_item_config.available_options}")
                    
                    # 개별 비교 확인
                    for available_option in menu_item_config.available_options:
                        print(f"🔍 [DEBUG] '{option_value}' == '{available_option}': {option_value == available_option}")
                    
                    if option_value not in menu_item_config.available_options:
                        print(f"🔍 [DEBUG] 옵션 검증 실패!")
                        return OrderResult(
                            success=False,
                            message=f"유효하지 않은 옵션입니다: {option_key}={option_value}",
                            order=self.current_order,
                            error_code=OrderErrorType.INVALID_OPTION.value
                        )
                    else:
                        print(f"🔍 [DEBUG] 옵션 검증 성공!")
            
            existing_item = None
            for item in self.current_order.items:
                if item.name == item_name and item.options == (options or {}):
                    existing_item = item
                    break
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.updated_at = datetime.now()
            else:
                # 기본 가격 계산
                base_price = menu_item_config.price
                final_price = base_price
                
                # 세트 추가 요금 적용
                if options and "type" in options:
                    option_type = options["type"]
                    # config_manager를 통해 set_pricing 정보 가져오기
                    try:
                        from ..config import config_manager
                        menu_config = config_manager.load_menu_config()
                        set_pricing = menu_config.set_pricing
                        
                        if option_type == "세트":
                            final_price += set_pricing.get("세트", 0)
                        elif option_type == "라지세트":
                            final_price += set_pricing.get("라지세트", 0)
                    except Exception:
                        # 설정 로드 실패 시 기본값 사용
                        pass
                
                new_item = MenuItem(
                    name=item_name,
                    category=menu_item_config.category,
                    quantity=quantity,
                    price=final_price,
                    options=options or {},
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.current_order.items.append(new_item)
            
            self.current_order.updated_at = datetime.now()
            
            # 더 구체적인 메시지 생성 - 세부 옵션 정보 포함
            option_text = ""
            if options and "type" in options:
                option_text = f" {options['type']}"
            else:
                # 옵션이 없는 경우 기본값으로 "단품" 표시
                option_text = " 단품"
            
            return OrderResult(
                success=True,
                message=f"{item_name}{option_text} {quantity}개가 주문에 추가되었습니다.",
                order=self.current_order
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 추가 중 오류가 발생했습니다: {str(e)}",
                order=self.current_order,
                error_code=OrderErrorType.SYSTEM_ERROR.value
            )
    
    def remove_item(self, item_name: str, quantity: Optional[int] = None,
                   options: Optional[Dict[str, str]] = None) -> OrderResult:
        try:
            if not self.current_order:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 없습니다.",
                    order=None,
                    error_code=OrderErrorType.NO_ACTIVE_ORDER.value
                )
            
            if self.current_order.status != OrderStatus.PENDING:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 아닙니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_ORDER_STATE.value
                )
            
            target_item = None
            # 정확한 이름 매칭부터 시도
            for item in self.current_order.items:
                if item.name == item_name:
                    if options is None or item.options == options:
                        target_item = item
                        break
            
            # 정확한 매칭 실패 시 유연한 매칭 시도
            if not target_item:
                normalized_search_name = item_name.replace(" ", "").replace("　", "").lower()
                for item in self.current_order.items:
                    normalized_item_name = item.name.replace(" ", "").replace("　", "").lower()
                    if normalized_item_name == normalized_search_name:
                        if options is None or item.options == options:
                            target_item = item
                            break
            
            if not target_item:
                return OrderResult(
                    success=False,
                    message=f"주문에서 해당 메뉴를 찾을 수 없습니다: {item_name}",
                    order=self.current_order,
                    error_code=OrderErrorType.ITEM_NOT_IN_ORDER.value
                )
            
            if quantity is None or quantity >= target_item.quantity:
                self.current_order.items.remove(target_item)
                removed_quantity = target_item.quantity
            else:
                if quantity <= 0:
                    return OrderResult(
                        success=False,
                        message="제거할 수량은 1개 이상이어야 합니다.",
                        order=self.current_order,
                        error_code=OrderErrorType.INVALID_QUANTITY.value
                    )
                
                target_item.quantity -= quantity
                target_item.updated_at = datetime.now()
                removed_quantity = quantity
            
            self.current_order.updated_at = datetime.now()
            
            return OrderResult(
                success=True,
                message=f"{item_name} {removed_quantity}개가 주문에서 제거되었습니다.",
                order=self.current_order
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 제거 중 오류가 발생했습니다: {str(e)}",
                order=self.current_order,
                error_code=OrderErrorType.SYSTEM_ERROR.value
            )
    
    def modify_item(self, item_name: str, new_quantity: int,
                   old_options: Optional[Dict[str, str]] = None,
                   new_options: Optional[Dict[str, str]] = None) -> OrderResult:
        try:
            if not self.current_order:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 없습니다.",
                    order=None,
                    error_code=OrderErrorType.NO_ACTIVE_ORDER.value
                )
            
            if self.current_order.status != OrderStatus.PENDING:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 아닙니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_ORDER_STATE.value
                )
            
            if new_quantity <= 0:
                return OrderResult(
                    success=False,
                    message="수량은 1개 이상이어야 합니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_QUANTITY.value
                )
            
            if new_options:
                # 먼저 정확한 이름으로 검색
                menu_item_config = self.menu.get_item(item_name)
                
                # 정확한 매칭 실패 시 유연한 검색으로 fallback
                if not menu_item_config:
                    print(f"🔍 [DEBUG] 정확한 매칭 실패 - 유연한 검색 시도: {item_name}")
                    search_result = self.menu.search_items(item_name, limit=1)
                    if search_result.items:
                        menu_item_config = search_result.items[0]
                        print(f"🔍 [DEBUG] 유연한 검색 성공: {menu_item_config.name}")
                
                if not menu_item_config:
                    return OrderResult(
                        success=False,
                        message=f"메뉴를 찾을 수 없습니다: {item_name}",
                        order=self.current_order,
                        error_code=OrderErrorType.ITEM_NOT_FOUND.value
                    )
                
                print(f"🔍 [DEBUG] 옵션 변경 검증 시작 - 메뉴: {item_name}")
                print(f"🔍 [DEBUG] 새로운 옵션: {new_options}")
                print(f"🔍 [DEBUG] 허용된 옵션: {menu_item_config.available_options}")
                
                for option_key, option_value in new_options.items():
                    print(f"🔍 [DEBUG] 변경 옵션 검증 중 - {option_key}={option_value}")
                    if option_value not in menu_item_config.available_options:
                        print(f"🔍 [DEBUG] 변경 옵션 검증 실패!")
                        return OrderResult(
                            success=False,
                            message=f"유효하지 않은 옵션입니다: {option_key}={option_value}",
                            order=self.current_order,
                            error_code=OrderErrorType.INVALID_OPTION.value
                        )
                    else:
                        print(f"🔍 [DEBUG] 변경 옵션 검증 성공!")
            
            target_item = None
            print(f"🔍 [DEBUG] 현재 주문에서 아이템 찾기 시작")
            print(f"🔍 [DEBUG] 찾는 아이템: {item_name}")
            print(f"🔍 [DEBUG] old_options: {old_options}")
            
            # 정확한 이름 매칭부터 시도
            for i, item in enumerate(self.current_order.items):
                print(f"🔍 [DEBUG] 아이템 {i}: {item.name}, 옵션: {item.options}")
                if item.name == item_name:
                    print(f"🔍 [DEBUG] 정확한 이름 일치 발견!")
                    if old_options is None or item.options == old_options:
                        print(f"🔍 [DEBUG] 옵션도 일치 (또는 old_options가 None)")
                        target_item = item
                        break
                    else:
                        print(f"🔍 [DEBUG] 옵션 불일치: {item.options} != {old_options}")
            
            # 정확한 매칭 실패 시 공백 제거한 유연한 매칭 시도
            if not target_item:
                print(f"🔍 [DEBUG] 정확한 매칭 실패 - 유연한 매칭 시도")
                normalized_search_name = item_name.replace(" ", "").replace("　", "").lower()
                for i, item in enumerate(self.current_order.items):
                    normalized_item_name = item.name.replace(" ", "").replace("　", "").lower()
                    print(f"🔍 [DEBUG] 유연한 매칭 비교: '{normalized_search_name}' vs '{normalized_item_name}'")
                    if normalized_item_name == normalized_search_name:
                        print(f"🔍 [DEBUG] 유연한 이름 매칭 성공!")
                        if old_options is None or item.options == old_options:
                            print(f"🔍 [DEBUG] 옵션도 일치 (또는 old_options가 None)")
                            target_item = item
                            break
                        else:
                            print(f"🔍 [DEBUG] 옵션 불일치: {item.options} != {old_options}")
            
            print(f"🔍 [DEBUG] 찾은 target_item: {target_item}")
            
            if not target_item:
                return OrderResult(
                    success=False,
                    message=f"주문에서 해당 메뉴를 찾을 수 없습니다: {item_name}",
                    order=self.current_order,
                    error_code=OrderErrorType.ITEM_NOT_IN_ORDER.value
                )
            
            print(f"🔍 [DEBUG] 수정 전 아이템: {target_item}")
            
            target_item.quantity = new_quantity
            if new_options is not None:
                print(f"🔍 [DEBUG] 옵션 변경: {target_item.options} -> {new_options}")
                target_item.options = new_options
                
                # 옵션 변경에 따른 가격 재계산
                if "type" in new_options:
                    option_type = new_options["type"]
                    # 실제 주문에 있는 아이템명을 사용 (유연한 매칭을 위해)
                    actual_item_name = target_item.name
                    menu_item_config = self.menu.get_item(actual_item_name)
                    
                    # 정확한 매칭 실패 시 유연한 검색 시도
                    if not menu_item_config:
                        search_result = self.menu.search_items(actual_item_name, limit=1)
                        if search_result.items:
                            menu_item_config = search_result.items[0]
                    
                    base_price = menu_item_config.price
                    
                    try:
                        from ..config import config_manager
                        menu_config = config_manager.load_menu_config()
                        set_pricing = menu_config.set_pricing
                        
                        if option_type == "세트":
                            target_item.price = base_price + set_pricing.get("세트", 0)
                        elif option_type == "라지세트":
                            target_item.price = base_price + set_pricing.get("라지세트", 0)
                        else:  # 단품
                            target_item.price = base_price
                        
                        print(f"🔍 [DEBUG] 가격 변경: {target_item.price}")
                        print(f"🔍 [DEBUG] 총 가격 변경: {target_item.total_price}")
                    except Exception as e:
                        print(f"🔍 [DEBUG] 가격 계산 오류: {e}")
                        
            target_item.updated_at = datetime.now()
            self.current_order.updated_at = datetime.now()
            
            print(f"🔍 [DEBUG] 수정 후 아이템: {target_item}")
            print(f"🔍 [DEBUG] 전체 주문 총액: {self.current_order.total_amount}")
            print(f"🔍 [DEBUG] 현재 주문 상태: {self.current_order}")
            
            return OrderResult(
                success=True,
                message=f"{item_name}이(가) 수정되었습니다.",
                order=self.current_order
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 수정 중 오류가 발생했습니다: {str(e)}",
                order=self.current_order,
                error_code=OrderErrorType.SYSTEM_ERROR.value
            )
    
    def clear_order(self) -> OrderResult:
        try:
            if not self.current_order:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 없습니다.",
                    order=None,
                    error_code=OrderErrorType.NO_ACTIVE_ORDER.value
                )
            
            if self.current_order.status != OrderStatus.PENDING:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 아닙니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_ORDER_STATE.value
                )
            
            self.current_order.status = OrderStatus.CANCELLED
            self.current_order.updated_at = datetime.now()
            
            self.order_history.append(self.current_order)
            self.current_order = None
            
            return OrderResult(
                success=True,
                message="주문이 취소되었습니다.",
                order=None
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 취소 중 오류가 발생했습니다: {str(e)}",
                order=self.current_order,
                error_code=OrderErrorType.SYSTEM_ERROR.value
            )
    
    def confirm_order(self) -> OrderResult:
        try:
            if not self.current_order:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 없습니다.",
                    order=None,
                    error_code=OrderErrorType.NO_ACTIVE_ORDER.value
                )
            
            if self.current_order.status != OrderStatus.PENDING:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 아닙니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.INVALID_ORDER_STATE.value
                )
            
            if not self.current_order.items:
                return OrderResult(
                    success=False,
                    message="주문할 메뉴가 없습니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.EMPTY_ORDER.value
                )
            
            self.current_order.status = OrderStatus.CONFIRMED
            self.current_order.updated_at = datetime.now()
            
            confirmed_order = self.current_order
            self.order_history.append(confirmed_order)
            self.current_order = None
            
            return OrderResult(
                success=True,
                message="주문이 확정되었습니다.",
                order=confirmed_order
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 확정 중 오류가 발생했습니다: {str(e)}",
                order=self.current_order,
                error_code=OrderErrorType.SYSTEM_ERROR.value
            )
    
    def get_order_summary(self) -> Optional[OrderSummary]:
        if not self.current_order:
            return None
        return self.current_order.get_summary()
    
    def get_order_history(self) -> List[Order]:
        return self.order_history.copy()
    
    def validate_order(self) -> OrderResult:
        try:
            if not self.current_order:
                return OrderResult(
                    success=False,
                    message="진행 중인 주문이 없습니다.",
                    order=None,
                    error_code=OrderErrorType.NO_ACTIVE_ORDER.value
                )
            
            if not self.current_order.items:
                return OrderResult(
                    success=False,
                    message="주문할 메뉴가 없습니다.",
                    order=self.current_order,
                    error_code=OrderErrorType.EMPTY_ORDER.value
                )
            
            for item in self.current_order.items:
                if not self.menu.validate_item(item.name, item.options):
                    return OrderResult(
                        success=False,
                        message=f"유효하지 않은 메뉴 또는 옵션입니다: {item.name}",
                        order=self.current_order,
                        error_code=OrderErrorType.INVALID_ITEM.value
                    )
                
                if item.quantity <= 0:
                    return OrderResult(
                        success=False,
                        message=f"유효하지 않은 수량입니다: {item.name} ({item.quantity}개)",
                        order=self.current_order,
                        error_code=OrderErrorType.INVALID_QUANTITY.value
                    )
            
            return OrderResult(
                success=True,
                message="주문이 유효합니다.",
                order=self.current_order
            )
            
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 검증 중 오류가 발생했습니다: {str(e)}",
                order=self.current_order,
                error_code=OrderErrorType.SYSTEM_ERROR.value
            )
    
    def get_order_stats(self) -> Dict[str, Any]:
        stats = {
            'current_order': {
                'exists': self.current_order is not None,
                'item_count': len(self.current_order.items) if self.current_order else 0,
                'total_amount': float(self.current_order.total_amount) if self.current_order else 0,
                'status': self.current_order.status.value if self.current_order else None
            },
            'history': {
                'total_orders': len(self.order_history),
                'confirmed_orders': len([o for o in self.order_history if o.status == OrderStatus.CONFIRMED]),
                'cancelled_orders': len([o for o in self.order_history if o.status == OrderStatus.CANCELLED])
            }
        }
        
        return stats