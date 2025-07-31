"""
주문 관리 시스템 테스트
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from src.models.order_models import (
    MenuItem, Order, OrderStatus, OrderResult, OrderSummary
)
from src.models.config_models import MenuConfig, MenuItemConfig
from src.models.error_models import OrderErrorType, ValidationError
from src.order.menu import Menu
from src.order.order import OrderManager


class TestOrderManager:
    """OrderManager 클래스 테스트"""
    
    @pytest.fixture
    def sample_menu_config(self):
        """테스트용 메뉴 설정"""
        menu_items = {
            "빅맥": MenuItemConfig(
                name="빅맥",
                category="단품",
                price=Decimal("6500"),
                available_options=["콜라", "사이다", "오렌지주스"],
                description="빅맥 버거",
                is_available=True
            ),
            "빅맥세트": MenuItemConfig(
                name="빅맥세트",
                category="세트",
                price=Decimal("8500"),
                available_options=["콜라", "사이다", "오렌지주스"],
                description="빅맥 세트 메뉴",
                is_available=True
            ),
            "치킨너겟": MenuItemConfig(
                name="치킨너겟",
                category="사이드",
                price=Decimal("3500"),
                available_options=[],
                description="치킨 너겟",
                is_available=True
            ),
            "품절메뉴": MenuItemConfig(
                name="품절메뉴",
                category="단품",
                price=Decimal("5000"),
                available_options=[],
                description="품절된 메뉴",
                is_available=False
            )
        }
        
        return MenuConfig(
            restaurant_type="패스트푸드",
            menu_items=menu_items,
            categories=["단품", "세트", "사이드"],
            currency="KRW",
            tax_rate=Decimal("0.1"),
            service_charge=Decimal("0.0")
        )
    
    @pytest.fixture
    def menu(self, sample_menu_config):
        """테스트용 메뉴 객체"""
        return Menu(sample_menu_config)
    
    @pytest.fixture
    def order_manager(self, menu):
        """테스트용 주문 관리자"""
        return OrderManager(menu)
    
    def test_create_new_order(self, order_manager):
        """새 주문 생성 테스트"""
        order = order_manager.create_new_order()
        
        assert order is not None
        assert order.order_id is not None
        assert order.status == OrderStatus.PENDING
        assert len(order.items) == 0
        assert order.total_amount == Decimal('0')
        assert order_manager.current_order == order
    
    def test_create_new_order_cancels_existing(self, order_manager):
        """기존 주문이 있을 때 새 주문 생성 테스트"""
        # 첫 번째 주문 생성
        first_order = order_manager.create_new_order()
        first_order_id = first_order.order_id
        
        # 두 번째 주문 생성
        second_order = order_manager.create_new_order()
        
        assert second_order.order_id != first_order_id
        assert order_manager.current_order == second_order
        assert len(order_manager.order_history) == 1
        assert order_manager.order_history[0].status == OrderStatus.CANCELLED
    
    def test_add_item_success(self, order_manager):
        """아이템 추가 성공 테스트"""
        result = order_manager.add_item("빅맥", 2)
        
        assert result.success is True
        assert "빅맥 2개가 주문에 추가되었습니다" in result.message
        assert len(order_manager.current_order.items) == 1
        assert order_manager.current_order.items[0].name == "빅맥"
        assert order_manager.current_order.items[0].quantity == 2
        assert order_manager.current_order.total_amount == Decimal("13000")  # 6500 * 2
    
    def test_add_item_with_options(self, order_manager):
        """옵션과 함께 아이템 추가 테스트"""
        result = order_manager.add_item("빅맥세트", 1, {"음료": "콜라"})
        
        assert result.success is True
        assert len(order_manager.current_order.items) == 1
        assert order_manager.current_order.items[0].options == {"음료": "콜라"}
    
    def test_add_item_duplicate_increases_quantity(self, order_manager):
        """동일 아이템 추가 시 수량 증가 테스트"""
        order_manager.add_item("빅맥", 1)
        result = order_manager.add_item("빅맥", 2)
        
        assert result.success is True
        assert len(order_manager.current_order.items) == 1
        assert order_manager.current_order.items[0].quantity == 3
    
    def test_add_item_not_found(self, order_manager):
        """존재하지 않는 아이템 추가 테스트"""
        result = order_manager.add_item("존재하지않는메뉴", 1)
        
        assert result.success is False
        assert result.error_code == OrderErrorType.ITEM_NOT_FOUND.value
        assert "메뉴를 찾을 수 없습니다" in result.message
    
    def test_add_item_unavailable(self, order_manager):
        """품절 아이템 추가 테스트"""
        result = order_manager.add_item("품절메뉴", 1)
        
        assert result.success is False
        assert result.error_code == OrderErrorType.ITEM_UNAVAILABLE.value
        assert "현재 판매하지 않는 메뉴입니다" in result.message
    
    def test_add_item_invalid_quantity(self, order_manager):
        """잘못된 수량으로 아이템 추가 테스트"""
        result = order_manager.add_item("빅맥", 0)
        
        assert result.success is False
        assert result.error_code == OrderErrorType.INVALID_QUANTITY.value
        assert "수량은 1개 이상이어야 합니다" in result.message
    
    def test_add_item_invalid_option(self, order_manager):
        """잘못된 옵션으로 아이템 추가 테스트"""
        result = order_manager.add_item("빅맥", 1, {"음료": "맥주"})
        
        assert result.success is False
        assert result.error_code == OrderErrorType.INVALID_OPTION.value
        assert "유효하지 않은 옵션입니다" in result.message
    
    def test_remove_item_success(self, order_manager):
        """아이템 제거 성공 테스트"""
        order_manager.add_item("빅맥", 3)
        result = order_manager.remove_item("빅맥", 1)
        
        assert result.success is True
        assert "빅맥 1개가 주문에서 제거되었습니다" in result.message
        assert order_manager.current_order.items[0].quantity == 2
    
    def test_remove_item_complete(self, order_manager):
        """아이템 전체 제거 테스트"""
        order_manager.add_item("빅맥", 2)
        result = order_manager.remove_item("빅맥")
        
        assert result.success is True
        assert len(order_manager.current_order.items) == 0
    
    def test_remove_item_not_in_order(self, order_manager):
        """주문에 없는 아이템 제거 테스트"""
        order_manager.create_new_order()
        result = order_manager.remove_item("빅맥")
        
        assert result.success is False
        assert result.error_code == OrderErrorType.ITEM_NOT_IN_ORDER.value
        assert "주문에서 해당 메뉴를 찾을 수 없습니다" in result.message
    
    def test_remove_item_no_active_order(self, order_manager):
        """활성 주문 없이 아이템 제거 테스트"""
        result = order_manager.remove_item("빅맥")
        
        assert result.success is False
        assert result.error_code == OrderErrorType.NO_ACTIVE_ORDER.value
        assert "진행 중인 주문이 없습니다" in result.message
    
    def test_modify_item_success(self, order_manager):
        """아이템 수정 성공 테스트"""
        order_manager.add_item("빅맥", 2)
        result = order_manager.modify_item("빅맥", 5)
        
        assert result.success is True
        assert "빅맥이(가) 수정되었습니다" in result.message
        assert order_manager.current_order.items[0].quantity == 5
    
    def test_modify_item_with_options(self, order_manager):
        """옵션과 함께 아이템 수정 테스트"""
        order_manager.add_item("빅맥세트", 1, {"음료": "콜라"})
        result = order_manager.modify_item("빅맥세트", 2, {"음료": "콜라"}, {"음료": "사이다"})
        
        assert result.success is True
        assert order_manager.current_order.items[0].quantity == 2
        assert order_manager.current_order.items[0].options == {"음료": "사이다"}
    
    def test_modify_item_invalid_quantity(self, order_manager):
        """잘못된 수량으로 아이템 수정 테스트"""
        order_manager.add_item("빅맥", 2)
        result = order_manager.modify_item("빅맥", 0)
        
        assert result.success is False
        assert result.error_code == OrderErrorType.INVALID_QUANTITY.value
        assert "수량은 1개 이상이어야 합니다" in result.message
    
    def test_clear_order_success(self, order_manager):
        """주문 전체 취소 성공 테스트"""
        order_manager.add_item("빅맥", 2)
        order_manager.add_item("치킨너겟", 1)
        
        result = order_manager.clear_order()
        
        assert result.success is True
        assert "주문이 취소되었습니다" in result.message
        assert order_manager.current_order is None
        assert len(order_manager.order_history) == 1
        assert order_manager.order_history[0].status == OrderStatus.CANCELLED
    
    def test_confirm_order_success(self, order_manager):
        """주문 확정 성공 테스트"""
        order_manager.add_item("빅맥", 2)
        
        result = order_manager.confirm_order()
        
        assert result.success is True
        assert "주문이 확정되었습니다" in result.message
        assert order_manager.current_order is None
        assert len(order_manager.order_history) == 1
        assert order_manager.order_history[0].status == OrderStatus.CONFIRMED
    
    def test_confirm_order_empty(self, order_manager):
        """빈 주문 확정 테스트"""
        order_manager.create_new_order()
        
        result = order_manager.confirm_order()
        
        assert result.success is False
        assert result.error_code == OrderErrorType.EMPTY_ORDER.value
        assert "주문할 메뉴가 없습니다" in result.message
    
    def test_confirm_order_no_active_order(self, order_manager):
        """활성 주문 없이 확정 테스트"""
        result = order_manager.confirm_order()
        
        assert result.success is False
        assert result.error_code == OrderErrorType.NO_ACTIVE_ORDER.value
        assert "진행 중인 주문이 없습니다" in result.message
    
    def test_get_order_summary(self, order_manager):
        """주문 요약 조회 테스트"""
        order_manager.add_item("빅맥", 2)
        order_manager.add_item("치킨너겟", 1)
        
        summary = order_manager.get_order_summary()
        
        assert summary is not None
        assert summary.item_count == 2
        assert summary.total_quantity == 3
        assert summary.total_amount == order_manager.current_order.total_amount
    
    def test_get_order_summary_no_order(self, order_manager):
        """주문 없을 때 요약 조회 테스트"""
        summary = order_manager.get_order_summary()
        assert summary is None
    
    def test_validate_order_success(self, order_manager):
        """주문 검증 성공 테스트"""
        order_manager.add_item("빅맥", 2)
        
        result = order_manager.validate_order()
        
        assert result.success is True
        assert "주문이 유효합니다" in result.message
    
    def test_validate_order_empty(self, order_manager):
        """빈 주문 검증 테스트"""
        order_manager.create_new_order()
        
        result = order_manager.validate_order()
        
        assert result.success is False
        assert result.error_code == OrderErrorType.EMPTY_ORDER.value
        assert "주문할 메뉴가 없습니다" in result.message
    
    def test_validate_order_no_active_order(self, order_manager):
        """활성 주문 없이 검증 테스트"""
        result = order_manager.validate_order()
        
        assert result.success is False
        assert result.error_code == OrderErrorType.NO_ACTIVE_ORDER.value
        assert "진행 중인 주문이 없습니다" in result.message
    
    def test_get_order_history(self, order_manager):
        """주문 히스토리 조회 테스트"""
        # 첫 번째 주문
        order_manager.add_item("빅맥", 1)
        order_manager.confirm_order()
        
        # 두 번째 주문
        order_manager.add_item("치킨너겟", 2)
        order_manager.clear_order()
        
        history = order_manager.get_order_history()
        
        assert len(history) == 2
        assert history[0].status == OrderStatus.CONFIRMED
        assert history[1].status == OrderStatus.CANCELLED
    
    def test_get_order_stats(self, order_manager):
        """주문 통계 조회 테스트"""
        # 현재 주문 생성
        order_manager.add_item("빅맥", 2)
        
        # 히스토리에 주문 추가
        order_manager.confirm_order()
        order_manager.add_item("치킨너겟", 1)
        order_manager.clear_order()
        
        stats = order_manager.get_order_stats()
        
        assert stats['current_order']['exists'] is False
        assert stats['history']['total_orders'] == 2
        assert stats['history']['confirmed_orders'] == 1
        assert stats['history']['cancelled_orders'] == 1
    
    def test_order_total_calculation(self, order_manager):
        """주문 총액 계산 테스트"""
        order_manager.add_item("빅맥", 2)  # 6500 * 2 = 13000
        order_manager.add_item("치킨너겟", 1)  # 3500 * 1 = 3500
        
        # 총액: 16500 (6500 * 2 + 3500 * 1)
        expected_total = Decimal("16500")
        
        assert order_manager.current_order.total_amount == expected_total
    
    @patch('src.order.order.datetime')
    def test_order_timestamps(self, mock_datetime, order_manager):
        """주문 타임스탬프 테스트"""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        order_manager.add_item("빅맥", 1)
        
        assert order_manager.current_order.created_at == fixed_time
        assert order_manager.current_order.updated_at == fixed_time
    
    def test_error_handling_system_error(self, order_manager, monkeypatch):
        """시스템 오류 처리 테스트"""
        # menu.get_item이 예외를 발생시키도록 설정
        def mock_get_item(name):
            raise Exception("시스템 오류")
        
        monkeypatch.setattr(order_manager.menu, 'get_item', mock_get_item)
        
        result = order_manager.add_item("빅맥", 1)
        
        assert result.success is False
        assert result.error_code == OrderErrorType.SYSTEM_ERROR.value
        assert "주문 추가 중 오류가 발생했습니다" in result.message


class TestOrderIntegration:
    """주문 시스템 통합 테스트"""
    
    @pytest.fixture
    def setup_order_system(self):
        """주문 시스템 설정"""
        menu_items = {
            "빅맥세트": MenuItemConfig(
                name="빅맥세트",
                category="세트",
                price=Decimal("8500"),
                available_options=["콜라", "사이다"],
                description="빅맥 세트",
                is_available=True
            ),
            "감자튀김": MenuItemConfig(
                name="감자튀김",
                category="사이드",
                price=Decimal("2500"),
                available_options=["소금", "케첩"],
                description="감자튀김",
                is_available=True
            )
        }
        
        config = MenuConfig(
            restaurant_type="패스트푸드",
            menu_items=menu_items,
            categories=["세트", "사이드"],
            currency="KRW",
            tax_rate=Decimal("0.1"),
            service_charge=Decimal("0.05")
        )
        
        menu = Menu(config)
        return OrderManager(menu)
    
    def test_complete_order_flow(self, setup_order_system):
        """완전한 주문 플로우 테스트"""
        order_manager = setup_order_system
        
        # 1. 주문 시작
        order_manager.create_new_order()
        assert order_manager.current_order is not None
        
        # 2. 아이템 추가
        result1 = order_manager.add_item("빅맥세트", 2, {"음료": "콜라"})
        assert result1.success is True
        
        result2 = order_manager.add_item("감자튀김", 1, {"토핑": "케첩"})
        assert result2.success is True
        
        # 3. 주문 수정
        result3 = order_manager.modify_item("빅맥세트", 1, {"음료": "콜라"}, {"음료": "사이다"})
        assert result3.success is True
        
        # 4. 주문 검증
        validation = order_manager.validate_order()
        assert validation.success is True
        
        # 5. 주문 요약 확인
        summary = order_manager.get_order_summary()
        assert summary.item_count == 2
        assert summary.total_quantity == 2
        
        # 6. 주문 확정
        result4 = order_manager.confirm_order()
        assert result4.success is True
        assert order_manager.current_order is None
        assert len(order_manager.order_history) == 1
        
        # 7. 히스토리 확인
        history = order_manager.get_order_history()
        assert len(history) == 1
        assert history[0].status == OrderStatus.CONFIRMED
    
    def test_order_modification_scenarios(self, setup_order_system):
        """주문 수정 시나리오 테스트"""
        order_manager = setup_order_system
        
        # 초기 주문
        order_manager.add_item("빅맥세트", 2)
        order_manager.add_item("감자튀김", 3)
        
        initial_total = order_manager.current_order.total_amount
        
        # 수량 증가
        order_manager.modify_item("빅맥세트", 3)
        assert order_manager.current_order.total_amount > initial_total
        
        # 아이템 일부 제거
        order_manager.remove_item("감자튀김", 1)
        assert len(order_manager.current_order.items) == 2
        assert order_manager.current_order.items[1].quantity == 2
        
        # 아이템 전체 제거
        order_manager.remove_item("감자튀김")
        assert len(order_manager.current_order.items) == 1
        
        # 최종 검증
        validation = order_manager.validate_order()
        assert validation.success is True