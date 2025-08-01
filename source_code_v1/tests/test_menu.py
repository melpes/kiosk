"""
메뉴 관리 시스템 테스트
"""

import pytest
import json
import tempfile
import os
from decimal import Decimal
from unittest.mock import patch, mock_open

from src.order.menu import Menu, MenuSearchResult
from src.models.config_models import MenuConfig, MenuItemConfig
from src.models.order_models import MenuItem
from src.models.error_models import ValidationError, ConfigurationError


class TestMenu:
    """Menu 클래스 테스트"""
    
    @pytest.fixture
    def sample_menu_config(self):
        """테스트용 메뉴 설정"""
        menu_items = {
            "빅맥": MenuItemConfig(
                name="빅맥",
                category="버거",
                price=Decimal("6500"),
                available_options=["단품", "세트", "라지세트"],
                description="빅맥 버거"
            ),
            "상하이버거": MenuItemConfig(
                name="상하이버거",
                category="버거",
                price=Decimal("5500"),
                available_options=["단품", "세트", "라지세트"],
                description="상하이 스파이시 치킨버거"
            ),
            "감자튀김": MenuItemConfig(
                name="감자튀김",
                category="사이드",
                price=Decimal("2500"),
                available_options=["미디움", "라지"],
                description="바삭한 감자튀김"
            ),
            "콜라": MenuItemConfig(
                name="콜라",
                category="음료",
                price=Decimal("2000"),
                available_options=["미디움", "라지"],
                description="코카콜라"
            )
        }
        
        return MenuConfig(
            restaurant_type="fast_food",
            menu_items=menu_items,
            categories=["버거", "사이드", "음료", "디저트"]
        )
    
    @pytest.fixture
    def menu(self, sample_menu_config):
        """테스트용 메뉴 인스턴스"""
        return Menu(sample_menu_config)
    
    def test_menu_initialization(self, sample_menu_config):
        """메뉴 초기화 테스트"""
        menu = Menu(sample_menu_config)
        
        assert menu.config == sample_menu_config
        assert len(menu._name_index) == 4
        assert len(menu._category_index) == 3  # 실제 사용된 카테고리만
        assert "빅맥" in menu._name_index
    
    def test_menu_initialization_invalid_config(self):
        """잘못된 설정으로 메뉴 초기화 테스트"""
        # 빈 메뉴 아이템
        with pytest.raises(ValueError, match="메뉴 아이템이 최소 하나는 있어야 합니다"):
            Menu(MenuConfig(
                restaurant_type="test",
                menu_items={},
                categories=["test"]
            ))
        
        # 빈 카테고리
        with pytest.raises(ValueError, match="카테고리가 최소 하나는 있어야 합니다"):
            Menu(MenuConfig(
                restaurant_type="test",
                menu_items={"test": MenuItemConfig("test", "cat", Decimal("1000"))},
                categories=[]
            ))
    
    def test_get_item(self, menu):
        """메뉴 아이템 조회 테스트"""
        # 존재하는 아이템
        item = menu.get_item("빅맥")
        assert item is not None
        assert item.name == "빅맥"
        assert item.price == Decimal("6500")
        
        # 대소문자 구분 없이 조회
        item = menu.get_item("빅맥")
        assert item is not None
        
        # 존재하지 않는 아이템
        item = menu.get_item("존재하지않는메뉴")
        assert item is None
    
    def test_get_items_by_category(self, menu):
        """카테고리별 메뉴 아이템 조회 테스트"""
        # 버거 카테고리
        burger_items = menu.get_items_by_category("버거")
        assert len(burger_items) == 2
        assert all(item.category == "버거" for item in burger_items)
        
        # 존재하지 않는 카테고리
        empty_items = menu.get_items_by_category("존재하지않는카테고리")
        assert len(empty_items) == 0
        
        # 판매 불가능한 아이템 포함 테스트
        menu.set_item_availability("빅맥", False)
        burger_items_available = menu.get_items_by_category("버거", available_only=True)
        burger_items_all = menu.get_items_by_category("버거", available_only=False)
        
        assert len(burger_items_available) == 1
        assert len(burger_items_all) == 2
    
    def test_search_items(self, menu):
        """메뉴 아이템 검색 테스트"""
        # 정확한 이름 검색
        result = menu.search_items("빅맥")
        assert result.total_count == 1
        assert result.items[0].name == "빅맥"
        assert result.search_query == "빅맥"
        
        # 부분 문자열 검색
        result = menu.search_items("버거")
        assert result.total_count == 2
        assert all("버거" in item.name or "버거" in item.description for item in result.items)
        
        # 카테고리 필터 적용
        result = menu.search_items("버거", category="버거")
        assert result.total_count == 2
        assert result.category_filter == "버거"
        
        # 제한 적용
        result = menu.search_items("", limit=2)
        assert len(result.items) <= 2
        
        # 존재하지 않는 검색어
        result = menu.search_items("존재하지않는메뉴")
        assert result.total_count == 0
        assert len(result.items) == 0
    
    def test_validate_item(self, menu):
        """메뉴 아이템 검증 테스트"""
        # 유효한 아이템
        assert menu.validate_item("빅맥") is True
        
        # 유효한 아이템과 옵션
        assert menu.validate_item("빅맥", {"option": "세트"}) is True
        
        # 존재하지 않는 아이템
        assert menu.validate_item("존재하지않는메뉴") is False
        
        # 유효하지 않은 옵션
        assert menu.validate_item("빅맥", {"option": "존재하지않는옵션"}) is False
        
        # 판매 불가능한 아이템
        menu.set_item_availability("빅맥", False)
        assert menu.validate_item("빅맥") is False
    
    def test_create_menu_item(self, menu):
        """주문용 메뉴 아이템 생성 테스트"""
        # 정상적인 아이템 생성
        item = menu.create_menu_item("빅맥", "세트", Decimal("8500"), 2)
        assert isinstance(item, MenuItem)
        assert item.name == "빅맥"
        assert item.category == "세트"
        assert item.price == Decimal("8500")
        assert item.quantity == 2
        
        # 옵션 포함 아이템 생성
        item = menu.create_menu_item("빅맥", "세트", Decimal("8500"), 1, {"option": "세트"})
        assert item.options == {"option": "세트"}
        
        # 존재하지 않는 아이템
        with pytest.raises(ValidationError, match="메뉴 아이템을 찾을 수 없습니다"):
            menu.create_menu_item("존재하지않는메뉴", "단품", Decimal("1000"))
        
        # 판매 불가능한 아이템
        menu.set_item_availability("빅맥", False)
        with pytest.raises(ValidationError, match="현재 판매하지 않는 메뉴입니다"):
            menu.create_menu_item("빅맥", "단품", Decimal("6500"))
    
    def test_get_categories(self, menu):
        """카테고리 목록 반환 테스트"""
        categories = menu.get_categories()
        expected_categories = ["버거", "사이드", "음료", "디저트"]
        
        assert categories == expected_categories
        assert isinstance(categories, list)
        
        # 원본 수정 방지 확인
        categories.append("새카테고리")
        assert len(menu.get_categories()) == 4
    
    def test_get_all_items(self, menu):
        """모든 메뉴 아이템 반환 테스트"""
        # 판매 가능한 아이템만
        items = menu.get_all_items(available_only=True)
        assert len(items) == 4
        assert all(item.is_available for item in items)
        
        # 판매 불가능한 아이템 포함
        menu.set_item_availability("빅맥", False)
        all_items = menu.get_all_items(available_only=False)
        available_items = menu.get_all_items(available_only=True)
        
        assert len(all_items) == 4
        assert len(available_items) == 3
        
        # 정렬 확인 (카테고리, 이름 순)
        assert items[0].category <= items[-1].category
    
    def test_is_item_available(self, menu):
        """메뉴 아이템 판매 가능 여부 확인 테스트"""
        # 판매 가능한 아이템
        assert menu.is_item_available("빅맥") is True
        
        # 존재하지 않는 아이템
        assert menu.is_item_available("존재하지않는메뉴") is False
        
        # 판매 불가능한 아이템
        menu.set_item_availability("빅맥", False)
        assert menu.is_item_available("빅맥") is False
    
    def test_set_item_availability(self, menu):
        """메뉴 아이템 판매 가능 여부 설정 테스트"""
        # 정상적인 설정
        menu.set_item_availability("빅맥", False)
        assert menu.is_item_available("빅맥") is False
        
        menu.set_item_availability("빅맥", True)
        assert menu.is_item_available("빅맥") is True
        
        # 존재하지 않는 아이템
        with pytest.raises(ValidationError, match="메뉴 아이템을 찾을 수 없습니다"):
            menu.set_item_availability("존재하지않는메뉴", False)
    
    def test_get_restaurant_type(self, menu):
        """식당 타입 반환 테스트"""
        assert menu.get_restaurant_type() == "fast_food"
    
    def test_get_menu_stats(self, menu):
        """메뉴 통계 정보 반환 테스트"""
        stats = menu.get_menu_stats()
        
        assert stats['total_items'] == 4
        assert stats['available_items'] == 4
        assert stats['unavailable_items'] == 0
        assert stats['total_categories'] == 4
        assert stats['restaurant_type'] == "fast_food"
        assert 'category_stats' in stats
        
        # 일부 아이템을 판매 불가능으로 설정
        menu.set_item_availability("빅맥", False)
        stats = menu.get_menu_stats()
        
        assert stats['available_items'] == 3
        assert stats['unavailable_items'] == 1
    
    def test_to_dict(self, menu):
        """딕셔너리 변환 테스트"""
        menu_dict = menu.to_dict()
        
        assert menu_dict['restaurant_type'] == "fast_food"
        assert len(menu_dict['categories']) == 4
        assert len(menu_dict['menu_items']) == 4
        assert menu_dict['currency'] == "KRW"
        assert 'tax_rate' in menu_dict
        assert 'service_charge' in menu_dict
    
    def test_from_config_file(self):
        """설정 파일에서 메뉴 로드 테스트"""
        config_data = {
            "restaurant_info": {
                "type": "fast_food"
            },
            "categories": ["버거", "음료"],
            "menu_items": {
                "빅맥": {
                    "category": "버거",
                    "price": 6500,
                    "description": "빅맥 버거",
                    "available_options": ["단품", "세트"]
                }
            }
        }
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False)
            temp_path = f.name
        
        try:
            menu = Menu.from_config_file(temp_path)
            assert menu.get_restaurant_type() == "fast_food"
            assert menu.get_item("빅맥") is not None
        finally:
            os.unlink(temp_path)
        
        # 존재하지 않는 파일
        with pytest.raises(ConfigurationError, match="설정 파일을 찾을 수 없습니다"):
            Menu.from_config_file("존재하지않는파일.json")
    
    def test_from_dict(self):
        """딕셔너리에서 메뉴 생성 테스트"""
        config_data = {
            "restaurant_info": {
                "type": "korean"
            },
            "categories": ["메인", "사이드"],
            "menu_items": {
                "김치찌개": {
                    "category": "메인",
                    "price": 8000,
                    "description": "김치찌개",
                    "available_options": ["일반", "곱빼기"]
                }
            },
            "currency": "KRW",
            "tax_rate": "0.1",
            "service_charge": "0.0"
        }
        
        menu = Menu.from_dict(config_data)
        
        assert menu.get_restaurant_type() == "korean"
        assert menu.get_item("김치찌개") is not None
        assert menu.get_item("김치찌개").price == Decimal("8000")


class TestMenuSearchResult:
    """MenuSearchResult 클래스 테스트"""
    
    def test_menu_search_result_creation(self):
        """MenuSearchResult 생성 테스트"""
        items = [
            MenuItemConfig("빅맥", "버거", Decimal("6500")),
            MenuItemConfig("상하이버거", "버거", Decimal("5500"))
        ]
        
        result = MenuSearchResult(
            items=items,
            total_count=2,
            search_query="버거",
            category_filter="버거"
        )
        
        assert len(result.items) == 2
        assert result.total_count == 2
        assert result.search_query == "버거"
        assert result.category_filter == "버거"


if __name__ == "__main__":
    pytest.main([__file__])