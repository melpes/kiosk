"""
텍스트 응답 시스템 데모
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models import (
    ResponseType, MenuItem, OrderStatus, OrderSummary
)
from src.response import TextResponseSystem


def main():
    """텍스트 응답 시스템 데모 실행"""
    print("=" * 60)
    print("텍스트 응답 시스템 데모")
    print("=" * 60)
    
    # 텍스트 응답 시스템 초기화
    response_system = TextResponseSystem()
    
    print("\n1. 인사말 생성")
    print("-" * 30)
    greeting = response_system.generate_greeting()
    print(f"응답: {greeting.formatted_text}")
    print(f"타입: {greeting.response_type.value}")
    
    print("\n2. 주문 확인 응답 생성")
    print("-" * 30)
    order_confirmation = response_system.generate_order_confirmation(
        menu_name="빅맥 세트",
        quantity=1,
        total_amount=6500
    )
    print(f"응답: {order_confirmation.formatted_text}")
    print(f"타입: {order_confirmation.response_type.value}")
    
    print("\n3. 추가 주문 확인")
    print("-" * 30)
    additional_order = response_system.generate_order_confirmation(
        menu_name="감자튀김",
        quantity=2,
        total_amount=9500
    )
    print(f"응답: {additional_order.formatted_text}")
    
    print("\n4. 주문 요약 생성")
    print("-" * 30)
    menu_items = [
        MenuItem(
            name="빅맥 세트",
            category="세트",
            quantity=1,
            price=Decimal('6500')
        ),
        MenuItem(
            name="감자튀김",
            category="사이드",
            quantity=2,
            price=Decimal('1500')
        )
    ]
    
    order_summary = OrderSummary(
        order_id="demo_001",
        items=menu_items,
        total_amount=Decimal('9500'),
        item_count=2,
        total_quantity=3,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )
    
    summary_response = response_system.generate_order_summary(order_summary)
    print(f"응답: {summary_response.formatted_text}")
    print(f"타입: {summary_response.response_type.value}")
    
    print("\n5. 결제 요청 생성")
    print("-" * 30)
    payment_request = response_system.generate_payment_request(total_amount=9500)
    print(f"응답: {payment_request.formatted_text}")
    print(f"타입: {payment_request.response_type.value}")
    
    print("\n6. 주문 완료 응답")
    print("-" * 30)
    completion = response_system.generate_completion_response(total_amount=9500)
    print(f"응답: {completion.formatted_text}")
    print(f"타입: {completion.response_type.value}")
    
    print("\n7. 오류 처리 예시")
    print("-" * 30)
    
    # 메뉴 없음 오류
    menu_error = response_system.generate_error_response(
        menu_name="존재하지않는메뉴"
    )
    print(f"메뉴 없음 오류: {menu_error.formatted_text}")
    
    # 일반 오류
    general_error = response_system.generate_error_response()
    print(f"일반 오류: {general_error.formatted_text}")
    
    # 명확화 요청
    clarification = response_system.generate_clarification_request(
        "메뉴를 정확히 듣지 못했습니다"
    )
    print(f"명확화 요청: {clarification.formatted_text}")
    
    print("\n8. 주문 취소 예시")
    print("-" * 30)
    cancellation = response_system.generate_order_confirmation(
        menu_name="빅맥",
        quantity=1,
        total_amount=3000,
        cancelled=True
    )
    print(f"취소 확인: {cancellation.formatted_text}")
    
    print("\n9. 대량 주문 처리 예시")
    print("-" * 30)
    large_menu_items = []
    for i in range(5):
        large_menu_items.append(MenuItem(
            name=f"메뉴{i+1}",
            category="테스트",
            quantity=i+1,
            price=Decimal('2000')
        ))
    
    large_order_summary = OrderSummary(
        order_id="large_demo_001",
        items=large_menu_items,
        total_amount=Decimal('30000'),
        item_count=5,
        total_quantity=15,
        status=OrderStatus.PENDING,
        created_at=datetime.now()
    )
    
    large_summary_response = response_system.generate_order_summary(large_order_summary)
    print(f"대량 주문 요약: {large_summary_response.formatted_text}")
    
    print("\n10. 특수 문자 처리 예시")
    print("-" * 30)
    special_menu_response = response_system.generate_order_confirmation(
        menu_name="맥스파이시® 상하이버거",
        quantity=1,
        total_amount=7500
    )
    print(f"특수 문자 메뉴: {special_menu_response.formatted_text}")
    
    print("\n" + "=" * 60)
    print("데모 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()