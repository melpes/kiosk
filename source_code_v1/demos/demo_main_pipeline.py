#!/usr/bin/env python3
"""
메인 파이프라인 데모 스크립트
API 키 없이도 기본 기능을 테스트할 수 있도록 구성
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.logger import setup_logging, get_logger
from src.order.menu import Menu
from src.order.order import OrderManager
from src.response.text_response import TextResponseSystem
from src.models.response_models import ResponseType


def demo_basic_pipeline():
    """기본 파이프라인 데모 (API 키 없이 실행 가능)"""
    # 로깅 설정
    setup_logging(log_level="INFO", log_file="demo_pipeline.log")
    logger = get_logger("demo")
    
    print("🎤 음성 키오스크 파이프라인 데모")
    print("="*50)
    
    try:
        # 1. 메뉴 시스템 초기화
        logger.info("메뉴 시스템 초기화...")
        menu_config_path = "config/menu_config.json"
        menu = Menu.from_config_file(menu_config_path)
        order_manager = OrderManager(menu)
        
        # 2. 응답 시스템 초기화
        logger.info("응답 시스템 초기화...")
        response_system = TextResponseSystem()
        
        print("✅ 시스템 초기화 완료")
        print()
        
        # 3. 기본 시나리오 테스트
        print("📋 시나리오 테스트 시작")
        print("-" * 30)
        
        # 인사말
        greeting = response_system.generate_greeting()
        print(f"🤖 {greeting.formatted_text}")
        print()
        
        # 새 주문 생성
        order_manager.create_new_order()
        print("📝 새 주문 생성됨")
        
        # 메뉴 추가 테스트
        test_orders = [
            ("빅맥", 1, {}),
            ("감자튀김", 2, {}),
            ("콜라", 1, {})  # 옵션 제거 (메뉴 설정에 size 옵션이 없음)
        ]
        
        for menu_name, quantity, options in test_orders:
            print(f"\n👤 사용자: {menu_name} {quantity}개 주문")
            
            result = order_manager.add_item(menu_name, quantity, options)
            
            if result.success:
                # 주문 확인 응답 생성
                confirmation = response_system.generate_order_confirmation(
                    menu_name=menu_name,
                    quantity=quantity,
                    total_amount=0  # 데모용
                )
                print(f"🤖 {confirmation.formatted_text}")
            else:
                # 오류 응답 생성
                error_response = response_system.generate_error_response(
                    error_message=result.message,
                    menu_name=menu_name
                )
                print(f"🤖 {error_response.formatted_text}")
        
        # 주문 요약
        print(f"\n👤 사용자: 주문 내역 확인")
        order_summary = order_manager.get_order_summary()
        if order_summary:
            summary_response = response_system.generate_order_summary(order_summary)
            print(f"🤖 {summary_response.formatted_text}")
        
        # 결제 요청
        print(f"\n👤 사용자: 결제하겠습니다")
        if order_summary:
            payment_response = response_system.generate_payment_request(
                total_amount=int(order_summary.total_amount)
            )
            print(f"🤖 {payment_response.formatted_text}")
        
        # 주문 확정
        confirm_result = order_manager.confirm_order()
        if confirm_result.success:
            completion_response = response_system.generate_completion_response(
                total_amount=int(order_summary.total_amount) if order_summary else 0
            )
            print(f"🤖 {completion_response.formatted_text}")
        
        print("\n" + "="*50)
        print("✅ 데모 완료!")
        
        # 시스템 통계
        stats = order_manager.get_order_stats()
        print(f"\n📊 주문 통계:")
        print(f"   - 확정된 주문: {stats['history']['confirmed_orders']}개")
        print(f"   - 취소된 주문: {stats['history']['cancelled_orders']}개")
        
    except Exception as e:
        logger.error(f"데모 실행 중 오류: {e}")
        print(f"❌ 오류 발생: {e}")


def demo_error_handling():
    """오류 처리 데모"""
    print("\n🚨 오류 처리 데모")
    print("-" * 30)
    
    try:
        menu = Menu.from_config_file("config/menu_config.json")
        order_manager = OrderManager(menu)
        response_system = TextResponseSystem()
        
        order_manager.create_new_order()
        
        # 존재하지 않는 메뉴 주문
        print("👤 사용자: 존재하지 않는 메뉴 주문")
        result = order_manager.add_item("존재하지않는메뉴", 1)
        
        if not result.success:
            error_response = response_system.generate_error_response(
                error_message=result.message,
                menu_name="존재하지않는메뉴"
            )
            print(f"🤖 {error_response.formatted_text}")
        
        # 잘못된 수량
        print("\n👤 사용자: 잘못된 수량으로 주문")
        result = order_manager.add_item("빅맥", -1)
        
        if not result.success:
            error_response = response_system.generate_error_response(
                error_message=result.message
            )
            print(f"🤖 {error_response.formatted_text}")
        
        # 빈 주문으로 결제 시도
        print("\n👤 사용자: 빈 주문으로 결제 시도")
        result = order_manager.confirm_order()
        
        if not result.success:
            error_response = response_system.generate_error_response(
                error_message=result.message
            )
            print(f"🤖 {error_response.formatted_text}")
        
        print("\n✅ 오류 처리 데모 완료!")
        
    except Exception as e:
        print(f"❌ 데모 실행 중 오류: {e}")


def main():
    """메인 함수"""
    print("🎯 메인 파이프라인 통합 데모")
    print("=" * 60)
    
    # 기본 파이프라인 데모
    demo_basic_pipeline()
    
    # 오류 처리 데모
    demo_error_handling()
    
    print("\n🎉 모든 데모가 완료되었습니다!")
    print("💡 실제 시스템을 사용하려면 OpenAI API 키를 설정하고 python src/main.py를 실행하세요.")


if __name__ == "__main__":
    main()