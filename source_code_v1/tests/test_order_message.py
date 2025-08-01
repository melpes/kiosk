#!/usr/bin/env python3
"""
OrderManager의 주문 추가 메시지 개선 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.order.menu import Menu
from src.order.order import OrderManager

def test_order_message_improvement():
    """주문 메시지 개선 테스트"""
    print("=== OrderManager 주문 추가 메시지 개선 테스트 ===\n")
    
    # Menu와 OrderManager 초기화
    config_path = "config/menu_config.json"
    menu = Menu.from_config_file(config_path)
    order_manager = OrderManager(menu)
    
    # 새 주문 생성
    order_manager.create_new_order()
    
    # 테스트 케이스 1: 옵션이 없는 경우 (단품으로 표시되어야 함)
    print("1. 옵션이 없는 경우 테스트:")
    result = order_manager.add_item("빅맥", 1)
    print(f"   결과: {result.message}")
    print(f"   예상: 빅맥 단품 1개가 주문에 추가되었습니다.")
    print()
    
    # 테스트 케이스 2: 세트 옵션이 있는 경우
    print("2. 세트 옵션이 있는 경우 테스트:")
    result = order_manager.add_item("빅맥", 1, {"type": "세트"})
    print(f"   결과: {result.message}")
    print(f"   예상: 빅맥 세트 1개가 주문에 추가되었습니다.")
    print()
    
    # 테스트 케이스 3: 라지세트 옵션이 있는 경우
    print("3. 라지세트 옵션이 있는 경우 테스트:")
    result = order_manager.add_item("빅맥", 1, {"type": "라지세트"})
    print(f"   결과: {result.message}")
    print(f"   예상: 빅맥 라지세트 1개가 주문에 추가되었습니다.")
    print()
    
    # 테스트 케이스 4: 여러 개 주문
    print("4. 여러 개 주문 테스트:")
    result = order_manager.add_item("치킨버거", 2, {"type": "세트"})
    print(f"   결과: {result.message}")
    print(f"   예상: 치킨버거 세트 2개가 주문에 추가되었습니다.")
    print()
    
    # 현재 주문 요약 확인
    print("5. 주문 요약 확인:")
    order_summary = order_manager.get_order_summary()
    if order_summary:
        print("   현재 주문 항목들:")
        for item in order_summary.items:
            option_text = ""
            if item.options and "type" in item.options:
                option_text = f" {item.options['type']}"
            else:
                option_text = " 단품"
            print(f"   - {item.name}{option_text} {item.quantity}개")
    print()

if __name__ == "__main__":
    test_order_message_improvement()