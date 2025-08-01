#!/usr/bin/env python3
"""
OrderManager의 주문 추가 메시지 개선 테스트 (확장)
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.order.menu import Menu
from src.order.order import OrderManager

def test_order_message_comprehensive():
    """주문 메시지 개선 종합 테스트"""
    print("=== OrderManager 주문 메시지 개선 종합 테스트 ===\n")
    
    # 초기화
    config_path = "config/menu_config.json"
    menu = Menu.from_config_file(config_path)
    order_manager = OrderManager(menu)
    
    # 새 주문 생성
    order_manager.create_new_order()
    
    # 테스트 케이스 1: 다양한 옵션 테스트
    print("1. 다양한 옵션 테스트:")
    
    # 단품 (옵션 없음)
    result1 = order_manager.add_item("빅맥", 1)
    print(f"   단품: {result1.message}")
    
    # 세트
    result2 = order_manager.add_item("상하이버거", 1, {"type": "세트"})
    print(f"   세트: {result2.message}")
    
    # 라지세트
    result3 = order_manager.add_item("불고기버거", 1, {"type": "라지세트"})
    print(f"   라지세트: {result3.message}")
    print()
    
    # 테스트 케이스 2: 수량 테스트
    print("2. 수량 테스트:")
    result4 = order_manager.add_item("빅맥", 3, {"type": "세트"})
    print(f"   여러 개: {result4.message}")
    print()
    
    # 테스트 케이스 3: 주문 요약 확인
    print("3. 현재 주문 요약:")
    order_summary = order_manager.get_order_summary()
    if order_summary:
        for item in order_summary.items:
            option_text = ""
            if item.options and "type" in item.options:
                option_text = f" {item.options['type']}"
            else:
                option_text = " 단품"
            print(f"   - {item.name}{option_text} {item.quantity}개 - {item.price * item.quantity:,}원")
        print(f"   총 금액: {order_summary.total_amount:,}원")
    print()
    
    # 테스트 케이스 4: 동일 메뉴 다른 옵션 구분 테스트
    print("4. 동일 메뉴 다른 옵션 구분 테스트:")
    order_manager.create_new_order()  # 새 주문 시작
    
    result5 = order_manager.add_item("빅맥", 1)  # 단품
    print(f"   빅맥 단품 추가: {result5.message}")
    
    result6 = order_manager.add_item("빅맥", 1, {"type": "세트"})  # 세트
    print(f"   빅맥 세트 추가: {result6.message}")
    
    print("   최종 주문 요약:")
    final_summary = order_manager.get_order_summary()
    if final_summary:
        for item in final_summary.items:
            option_text = ""
            if item.options and "type" in item.options:
                option_text = f" {item.options['type']}"
            else:
                option_text = " 단품"
            print(f"   - {item.name}{option_text} {item.quantity}개")
    print()

if __name__ == "__main__":
    test_dialogue_response_improvement()