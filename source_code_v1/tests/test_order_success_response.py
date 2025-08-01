#!/usr/bin/env python3
"""
주문 성공 응답 생성 로직 개선 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock
from src.conversation.dialogue import DialogueManager
from src.models.order_models import OrderResult, Order, MenuItem, OrderStatus
from src.order.order import OrderManager
from src.order.menu import Menu
from datetime import datetime

def test_order_success_response():
    """주문 성공 응답 생성 테스트"""
    
    # Mock 객체들 생성
    mock_menu = Mock(spec=Menu)
    mock_order_manager = Mock(spec=OrderManager)
    mock_openai_client = Mock()
    
    # DialogueManager 인스턴스 생성
    dialogue_manager = DialogueManager.__new__(DialogueManager)
    dialogue_manager.order_manager = mock_order_manager
    dialogue_manager.client = mock_openai_client
    dialogue_manager.active_contexts = {}
    
    # 테스트 케이스 1: 단일 항목 (세트 옵션)
    print("=== 테스트 1: 단일 항목 (세트 옵션) ===")
    order1 = Order(order_id="test1", status=OrderStatus.PENDING)
    item1 = MenuItem(
        name="빅맥", 
        category="버거", 
        quantity=1, 
        price=7500,
        options={"type": "세트"}
    )
    order1.items = [item1]
    
    result1 = OrderResult(
        success=True,
        message="빅맥 세트 1개가 주문에 추가되었습니다.",
        order=order1
    )
    
    response1 = dialogue_manager._generate_order_success_response([result1])
    print(f"응답: {response1}")
    
    # 테스트 케이스 2: 단일 항목 (단품 옵션)
    print("\n=== 테스트 2: 단일 항목 (단품 옵션) ===")
    order2 = Order(order_id="test2", status=OrderStatus.PENDING)
    item2 = MenuItem(
        name="빅맥", 
        category="버거", 
        quantity=2, 
        price=5900,
        options={"type": "단품"}
    )
    order2.items = [item2]
    
    result2 = OrderResult(
        success=True,
        message="빅맥 단품 2개가 주문에 추가되었습니다.",
        order=order2
    )
    
    response2 = dialogue_manager._generate_order_success_response([result2])
    print(f"응답: {response2}")
    
    # 테스트 케이스 3: 옵션이 없는 경우 (기본값으로 단품 표시)
    print("\n=== 테스트 3: 옵션이 없는 경우 (기본값으로 단품 표시) ===")
    order3 = Order(order_id="test3", status=OrderStatus.PENDING)
    item3 = MenuItem(
        name="감자튀김", 
        category="사이드", 
        quantity=1, 
        price=2400
        # options 없음
    )
    order3.items = [item3]
    
    result3 = OrderResult(
        success=True,
        message="감자튀김 1개가 주문에 추가되었습니다.",
        order=order3
    )
    
    response3 = dialogue_manager._generate_order_success_response([result3])
    print(f"응답: {response3}")
    
    # 테스트 케이스 4: 여러 항목 (각 항목의 옵션을 명확하게 구분)
    print("\n=== 테스트 4: 여러 항목 (각 항목의 옵션을 명확하게 구분) ===")
    order4a = Order(order_id="test4a", status=OrderStatus.PENDING)
    item4a = MenuItem(
        name="빅맥", 
        category="버거", 
        quantity=1, 
        price=7500,
        options={"type": "세트"}
    )
    order4a.items = [item4a]
    
    order4b = Order(order_id="test4b", status=OrderStatus.PENDING)
    item4b = MenuItem(
        name="치킨버거", 
        category="버거", 
        quantity=2, 
        price=5900,
        options={"type": "단품"}
    )
    order4b.items = [item4b]
    
    result4a = OrderResult(success=True, message="", order=order4a)
    result4b = OrderResult(success=True, message="", order=order4b)
    
    response4 = dialogue_manager._generate_order_success_response([result4a, result4b])
    print(f"응답: {response4}")
    
    # 테스트 케이스 5: 동일 메뉴의 다른 옵션을 별도 항목으로 표시
    print("\n=== 테스트 5: 동일 메뉴의 다른 옵션을 별도 항목으로 표시 ===")
    order5a = Order(order_id="test5a", status=OrderStatus.PENDING)
    item5a = MenuItem(
        name="빅맥", 
        category="버거", 
        quantity=1, 
        price=7500,
        options={"type": "세트"}
    )
    order5a.items = [item5a]
    
    order5b = Order(order_id="test5b", status=OrderStatus.PENDING)
    item5b = MenuItem(
        name="빅맥", 
        category="버거", 
        quantity=1, 
        price=5900,
        options={"type": "단품"}
    )
    order5b.items = [item5b]
    
    result5a = OrderResult(success=True, message="", order=order5a)
    result5b = OrderResult(success=True, message="", order=order5b)
    
    response5 = dialogue_manager._generate_order_success_response([result5a, result5b])
    print(f"응답: {response5}")

if __name__ == "__main__":
    test_order_success_response()