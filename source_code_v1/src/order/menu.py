"""
메뉴 관리 시스템
"""

import json
import os
from typing import Dict, List, Optional, Any, Set
from decimal import Decimal
from dataclasses import dataclass
import re

from ..models.config_models import MenuConfig, MenuItemConfig
from ..models.order_models import MenuItem
from ..models.error_models import ValidationError, ConfigurationError


@dataclass
class MenuSearchResult:
    """메뉴 검색 결과"""
    items: List[MenuItemConfig]  # 검색된 메뉴 아이템들
    total_count: int             # 전체 검색 결과 수
    search_query: str            # 검색 쿼리
    category_filter: Optional[str] = None  # 카테고리 필터


class Menu:
    """메뉴 관리 클래스"""
    
    def __init__(self, config: MenuConfig):
        """
        메뉴 초기화
        
        Args:
            config: 메뉴 설정
        """
        self.config = config
        self._validate_config()
        self._build_search_index()
    
    @classmethod
    def from_config_file(cls, config_path: str) -> 'Menu':
        """
        설정 파일에서 메뉴 로드
        
        Args:
            config_path: 설정 파일 경로
            
        Returns:
            Menu 인스턴스
            
        Raises:
            ConfigurationError: 설정 파일 로드 실패 시
        """
        try:
            if not os.path.exists(config_path):
                raise ConfigurationError(f"설정 파일을 찾을 수 없습니다: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return cls.from_dict(config_data)
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"설정 파일 JSON 파싱 오류: {e}")
        except Exception as e:
            raise ConfigurationError(f"설정 파일 로드 오류: {e}")
    
    @classmethod
    def from_dict(cls, config_data: Dict[str, Any]) -> 'Menu':
        """
        딕셔너리에서 메뉴 생성
        
        Args:
            config_data: 설정 데이터
            
        Returns:
            Menu 인스턴스
        """
        # 메뉴 아이템 변환
        menu_items = {}
        for name, item_data in config_data.get('menu_items', {}).items():
            menu_items[name] = MenuItemConfig(
                name=name,
                category=item_data['category'],
                price=Decimal(str(item_data['price'])),
                available_options=item_data.get('available_options', []),
                description=item_data.get('description', ''),
                is_available=item_data.get('is_available', True)
            )
        
        # 메뉴 설정 생성
        config = MenuConfig(
            restaurant_type=config_data.get('restaurant_info', {}).get('type', 'general'),
            menu_items=menu_items,
            categories=config_data.get('categories', []),
            currency=config_data.get('currency', 'KRW'),
            tax_rate=Decimal(str(config_data.get('tax_rate', '0.1'))),
            service_charge=Decimal(str(config_data.get('service_charge', '0.0')))
        )
        
        return cls(config)
    
    def _validate_config(self):
        """설정 검증"""
        if not self.config.menu_items:
            raise ValidationError("메뉴 아이템이 없습니다")
        
        if not self.config.categories:
            raise ValidationError("카테고리가 없습니다")
        
        # 모든 메뉴 아이템의 카테고리가 정의된 카테고리에 포함되는지 확인
        for name, item in self.config.menu_items.items():
            if item.category not in self.config.categories:
                raise ValidationError(f"메뉴 아이템 '{name}'의 카테고리 '{item.category}'가 정의되지 않았습니다")
    
    def _build_search_index(self):
        """검색 인덱스 구축"""
        self._name_index = {}  # 이름 -> 메뉴 아이템
        self._category_index = {}  # 카테고리 -> 메뉴 아이템 리스트
        self._keyword_index = {}  # 키워드 -> 메뉴 아이템 리스트
        
        for name, item in self.config.menu_items.items():
            # 이름 인덱스
            self._name_index[name.lower()] = item
            
            # 카테고리 인덱스
            if item.category not in self._category_index:
                self._category_index[item.category] = []
            self._category_index[item.category].append(item)
            
            # 키워드 인덱스 (이름과 설명에서 키워드 추출)
            keywords = self._extract_keywords(name + " " + item.description)
            for keyword in keywords:
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = []
                self._keyword_index[keyword].append(item)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """텍스트에서 키워드 추출"""
        # 한글, 영문, 숫자만 추출하고 공백으로 분리
        keywords = set()
        
        # 전체 텍스트를 소문자로 변환
        text = text.lower()
        
        # 단어 단위로 분리
        words = re.findall(r'[가-힣a-z0-9]+', text)
        
        for word in words:
            if len(word) >= 2:  # 2글자 이상만 키워드로 사용
                keywords.add(word)
                
                # 부분 문자열도 키워드로 추가 (한글의 경우)
                if len(word) > 2:
                    for i in range(len(word) - 1):
                        substring = word[i:i+2]
                        keywords.add(substring)
        
        return keywords
    
    def get_item(self, name: str) -> Optional[MenuItemConfig]:
        """
        메뉴 아이템 조회
        
        Args:
            name: 메뉴 이름
            
        Returns:
            메뉴 아이템 또는 None
        """
        return self._name_index.get(name.lower())
    
    def get_items_by_category(self, category: str, available_only: bool = True) -> List[MenuItemConfig]:
        """
        카테고리별 메뉴 아이템 조회
        
        Args:
            category: 카테고리명
            available_only: 판매 가능한 아이템만 반환할지 여부
            
        Returns:
            메뉴 아이템 리스트
        """
        items = self._category_index.get(category, [])
        
        if available_only:
            items = [item for item in items if item.is_available]
        
        return items
    
    def search_items(self, query: str, category: Optional[str] = None, 
                    available_only: bool = True, limit: int = 10) -> MenuSearchResult:
        """
        메뉴 아이템 검색
        
        Args:
            query: 검색 쿼리
            category: 카테고리 필터 (선택사항)
            available_only: 판매 가능한 아이템만 검색할지 여부
            limit: 최대 결과 수
            
        Returns:
            검색 결과
        """
        query = query.lower().strip()
        found_items = set()
        
        # 정확한 이름 매칭 우선
        exact_match = self._name_index.get(query)
        if exact_match and (not available_only or exact_match.is_available):
            if not category or exact_match.category == category:
                found_items.add(exact_match)
        
        # 키워드 검색
        keywords = self._extract_keywords(query)
        for keyword in keywords:
            if keyword in self._keyword_index:
                for item in self._keyword_index[keyword]:
                    if not available_only or item.is_available:
                        if not category or item.category == category:
                            found_items.add(item)
        
        # 부분 문자열 검색 (이름에서)
        for name, item in self._name_index.items():
            if query in name and (not available_only or item.is_available):
                if not category or item.category == category:
                    found_items.add(item)
        
        # 결과를 리스트로 변환하고 정렬
        result_items = list(found_items)
        result_items.sort(key=lambda x: (x.category, x.name))
        
        # 제한 적용
        limited_items = result_items[:limit]
        
        return MenuSearchResult(
            items=limited_items,
            total_count=len(result_items),
            search_query=query,
            category_filter=category
        )
    
    def validate_item(self, item_name: str, options: Optional[Dict[str, str]] = None) -> bool:
        """
        메뉴 아이템 및 옵션 검증
        
        Args:
            item_name: 메뉴 이름
            options: 옵션 딕셔너리
            
        Returns:
            검증 결과
        """
        menu_item = self.get_item(item_name)
        
        if not menu_item:
            return False
        
        if not menu_item.is_available:
            return False
        
        # 옵션 검증
        if options:
            for option_key, option_value in options.items():
                if option_value not in menu_item.available_options:
                    return False
        
        return True
    
    def create_menu_item(self, name: str, category: str, price: Decimal, 
                        quantity: int = 1, options: Optional[Dict[str, str]] = None) -> MenuItem:
        """
        주문용 메뉴 아이템 생성
        
        Args:
            name: 메뉴 이름
            category: 카테고리 (단품, 세트, 라지세트 등)
            price: 가격
            quantity: 수량
            options: 옵션
            
        Returns:
            주문용 메뉴 아이템
            
        Raises:
            ValidationError: 검증 실패 시
        """
        menu_config = self.get_item(name)
        if not menu_config:
            raise ValidationError(f"메뉴 아이템을 찾을 수 없습니다: {name}")
        
        if not menu_config.is_available:
            raise ValidationError(f"현재 판매하지 않는 메뉴입니다: {name}")
        
        # 옵션 검증
        if options:
            for option_key, option_value in options.items():
                if option_value not in menu_config.available_options:
                    raise ValidationError(f"유효하지 않은 옵션입니다: {option_key}={option_value}")
        
        return MenuItem(
            name=name,
            category=category,
            quantity=quantity,
            price=price,
            options=options or {}
        )
    
    def get_categories(self) -> List[str]:
        """
        카테고리 목록 반환
        
        Returns:
            카테고리 리스트
        """
        return self.config.categories.copy()
    
    def get_all_items(self, available_only: bool = True) -> List[MenuItemConfig]:
        """
        모든 메뉴 아이템 반환
        
        Args:
            available_only: 판매 가능한 아이템만 반환할지 여부
            
        Returns:
            메뉴 아이템 리스트
        """
        items = list(self.config.menu_items.values())
        
        if available_only:
            items = [item for item in items if item.is_available]
        
        return sorted(items, key=lambda x: (x.category, x.name))
    
    def get_restaurant_type(self) -> str:
        """
        식당 타입 반환
        
        Returns:
            식당 타입
        """
        return self.config.restaurant_type
    
    def is_item_available(self, name: str) -> bool:
        """
        메뉴 아이템 판매 가능 여부 확인
        
        Args:
            name: 메뉴 이름
            
        Returns:
            판매 가능 여부
        """
        item = self.get_item(name)
        return item is not None and item.is_available
    
    def set_item_availability(self, name: str, available: bool):
        """
        메뉴 아이템 판매 가능 여부 설정
        
        Args:
            name: 메뉴 이름
            available: 판매 가능 여부
            
        Raises:
            ValidationError: 메뉴 아이템을 찾을 수 없는 경우
        """
        item = self.get_item(name)
        if not item:
            raise ValidationError(f"메뉴 아이템을 찾을 수 없습니다: {name}")
        
        item.is_available = available
        
        # 검색 인덱스 재구축
        self._build_search_index()
    
    def get_menu_stats(self) -> Dict[str, Any]:
        """
        메뉴 통계 정보 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        total_items = len(self.config.menu_items)
        available_items = len([item for item in self.config.menu_items.values() if item.is_available])
        
        category_stats = {}
        for category in self.config.categories:
            items = self.get_items_by_category(category, available_only=False)
            available = len([item for item in items if item.is_available])
            category_stats[category] = {
                'total': len(items),
                'available': available,
                'unavailable': len(items) - available
            }
        
        return {
            'total_items': total_items,
            'available_items': available_items,
            'unavailable_items': total_items - available_items,
            'total_categories': len(self.config.categories),
            'restaurant_type': self.config.restaurant_type,
            'category_stats': category_stats
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환
        
        Returns:
            메뉴 정보 딕셔너리
        """
        return {
            'restaurant_type': self.config.restaurant_type,
            'categories': self.config.categories,
            'menu_items': {name: item.to_dict() for name, item in self.config.menu_items.items()},
            'currency': self.config.currency,
            'tax_rate': float(self.config.tax_rate),
            'service_charge': float(self.config.service_charge)
        }