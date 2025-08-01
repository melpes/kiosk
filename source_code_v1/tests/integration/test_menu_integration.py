#!/usr/bin/env python3
"""
메뉴 관리 시스템 통합 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.order.menu import Menu
from decimal import Decimal

def main():
    """메뉴 시스템 통합 테스트"""
    print("=== 메뉴 관리 시스템 통합 테스트 ===\n")
    
    # 설정 파일에서 메뉴 로드
    try:
        menu = Menu.from_config_file("config/menu_config.json")
        print("메뉴 설정 파일 로드 성공")
    except Exception as e:
        print(f"메뉴 설정 파일 로드 실패: {e}")
        return
    
    # 기본 정보 출력
    print(f"식당 타입: {menu.get_restaurant_type()}")
    print(f"카테고리: {', '.join(menu.get_categories())}")
    
    # 메뉴 통계
    stats = menu.get_menu_stats()
    print(f"총 메뉴 아이템: {stats['total_items']}개")
    print(f"판매 가능 아이템: {stats['available_items']}개")
    
    print("\n=== 메뉴 검색 테스트 ===")
    
    # 메뉴 검색 테스트
    search_queries = ["빅맥", "버거", "치킨", "음료", "감자"]
    
    for query in search_queries:
        result = menu.search_items(query, limit=3)
        print(f"\n'{query}' 검색 결과 ({result.total_count}개):")
        for item in result.items:
            print(f"  - {item.name} ({item.category}) - {item.price}원")
    
    print("\n=== 카테고리별 메뉴 조회 ===")
    
    # 카테고리별 메뉴 조회
    for category in menu.get_categories():
        items = menu.get_items_by_category(category)
        print(f"\n{category} ({len(items)}개):")
        for item in items:
            print(f"  - {item.name}: {item.price}원")
            if item.available_options:
                print(f"    옵션: {', '.join(item.available_options)}")
    
    print("\n=== 메뉴 아이템 검증 테스트 ===")
    
    # 메뉴 아이템 검증
    test_items = [
        ("빅맥", None),
        ("빅맥", {"option": "세트"}),
        ("존재하지않는메뉴", None),
        ("빅맥", {"option": "존재하지않는옵션"})
    ]
    
    for item_name, options in test_items:
        is_valid = menu.validate_item(item_name, options)
        options_str = f" (옵션: {options})" if options else ""
        status = "OK" if is_valid else "NG"
        print(f"{status} {item_name}{options_str}: {'유효' if is_valid else '무효'}")
    
    print("\n=== 주문용 메뉴 아이템 생성 테스트 ===")
    
    # 주문용 메뉴 아이템 생성
    try:
        item = menu.create_menu_item("빅맥", "세트", Decimal("8500"), 2)
        print(f"메뉴 아이템 생성 성공: {item}")
    except Exception as e:
        print(f"메뉴 아이템 생성 실패: {e}")
    
    print("\n=== 메뉴 가용성 관리 테스트 ===")
    
    # 메뉴 가용성 관리
    test_item = "빅맥"
    print(f"'{test_item}' 초기 상태: {'판매중' if menu.is_item_available(test_item) else '판매중지'}")
    
    menu.set_item_availability(test_item, False)
    print(f"'{test_item}' 판매 중지 후: {'판매중' if menu.is_item_available(test_item) else '판매중지'}")
    
    menu.set_item_availability(test_item, True)
    print(f"'{test_item}' 판매 재개 후: {'판매중' if menu.is_item_available(test_item) else '판매중지'}")
    
    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    main()