#!/usr/bin/env python3
"""
간단한 디버그 도구 (API 키 없이도 작동)
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 프로젝트 루트를 Python 경로에 추가 (직접 실행 시)
if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# 환경 변수 로드
try:
    from .utils.env_loader import ensure_env_loaded
    from .config import config_manager
    from .order.menu import Menu
    from .order.order import OrderManager
    from .response.text_response import TextResponseSystem
except ImportError:
    # 직접 실행 시 절대 import 사용
    from src.utils.env_loader import ensure_env_loaded
    from src.config import config_manager
    from src.order.menu import Menu
    from src.order.order import OrderManager
    from src.response.text_response import TextResponseSystem

ensure_env_loaded()


def test_basic_system():
    """기본 시스템 테스트 (API 키 없이)"""
    print("🧪 기본 시스템 테스트")
    print("=" * 50)
    
    try:
        # 1. 설정 로드
        print("1. 설정 로드 중...")
        menu_config = config_manager.load_menu_config()
        print(f"   ✅ 메뉴 설정 로드 완료 ({len(menu_config.menu_items)}개 메뉴)")
        
        # 2. 메뉴 시스템 초기화
        print("2. 메뉴 시스템 초기화 중...")
        from dataclasses import asdict
        menu = Menu.from_dict({
            "restaurant_info": menu_config.restaurant_info,
            "categories": menu_config.categories,
            "menu_items": {name: asdict(item) for name, item in menu_config.menu_items.items()},
            "set_pricing": menu_config.set_pricing,
            "option_pricing": menu_config.option_pricing
        })
        print(f"   ✅ 메뉴 시스템 초기화 완료")
        
        # 3. 주문 관리자 초기화
        print("3. 주문 관리자 초기화 중...")
        order_manager = OrderManager(menu)
        print(f"   ✅ 주문 관리자 초기화 완료")
        
        # 4. 응답 시스템 초기화
        print("4. 응답 시스템 초기화 중...")
        response_system = TextResponseSystem()
        print(f"   ✅ 응답 시스템 초기화 완료")
        
        # 5. 기본 기능 테스트
        print("5. 기본 기능 테스트 중...")
        
        # 새 주문 생성
        order_manager.create_new_order()
        print("   📝 새 주문 생성됨")
        
        # 메뉴 추가 테스트
        result = order_manager.add_item("빅맥", 1)
        if result.success:
            print("   ✅ 빅맥 1개 주문 추가 성공")
            
            # 주문 상태 확인
            current_order = order_manager.get_current_order()
            if current_order:
                print(f"   📋 현재 주문: {len(current_order.items)}개 아이템, 총 {current_order.total_amount:,}원")
                
                # 주문 요약 생성
                order_summary = order_manager.get_order_summary()
                if order_summary:
                    summary_response = response_system.generate_order_summary(order_summary)
                    print(f"   🗣️ 응답: {summary_response.formatted_text}")
        else:
            print(f"   ❌ 주문 추가 실패: {result.message}")
        
        print("\n🎉 기본 시스템 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_menu_search():
    """메뉴 검색 테스트"""
    print("\n🔍 메뉴 검색 테스트")
    print("=" * 30)
    
    try:
        menu_config = config_manager.load_menu_config()
        from dataclasses import asdict
        menu = Menu.from_dict({
            "restaurant_info": menu_config.restaurant_info,
            "categories": menu_config.categories,
            "menu_items": {name: asdict(item) for name, item in menu_config.menu_items.items()},
            "set_pricing": menu_config.set_pricing,
            "option_pricing": menu_config.option_pricing
        })
        
        # 메뉴 목록 출력
        print("📋 사용 가능한 메뉴:")
        for category in menu_config.categories:
            items = [name for name, item in menu_config.menu_items.items() if item.category == category]
            if items:
                print(f"  {category}: {', '.join(items)}")
        
        # 검색 테스트
        search_terms = ["빅맥", "버거", "음료", "세트"]
        for term in search_terms:
            result = menu.search_items(term, limit=3)
            print(f"\n'{term}' 검색 결과 ({result.total_count}개):")
            for item in result.items:
                print(f"  - {item.name} ({item.category}) - {item.price:,}원")
        
        return True
        
    except Exception as e:
        print(f"❌ 메뉴 검색 테스트 중 오류: {e}")
        return False


def interactive_test():
    """대화형 테스트 (API 키 없이)"""
    print("\n💬 대화형 테스트 모드")
    print("=" * 30)
    print("💡 'quit'를 입력하면 종료됩니다.")
    print("💡 'menu'를 입력하면 메뉴를 확인할 수 있습니다.")
    print("💡 'order'를 입력하면 현재 주문을 확인할 수 있습니다.")
    
    try:
        # 시스템 초기화
        menu_config = config_manager.load_menu_config()
        from dataclasses import asdict
        menu = Menu.from_dict({
            "restaurant_info": menu_config.restaurant_info,
            "categories": menu_config.categories,
            "menu_items": {name: asdict(item) for name, item in menu_config.menu_items.items()},
            "set_pricing": menu_config.set_pricing,
            "option_pricing": menu_config.option_pricing
        })
        order_manager = OrderManager(menu)
        response_system = TextResponseSystem()
        
        # 새 주문 생성
        order_manager.create_new_order()
        
        # 인사말
        greeting = response_system.generate_greeting()
        print(f"\n🤖 {greeting.formatted_text}")
        
        while True:
            try:
                user_input = input("\n👤 입력: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("👋 테스트를 종료합니다.")
                    break
            except EOFError:
                print("\n👋 입력이 종료되어 테스트를 종료합니다.")
                break
            except KeyboardInterrupt:
                print("\n👋 테스트를 종료합니다.")
                break
            
            if user_input.lower() in ['menu', '메뉴']:
                print("📋 사용 가능한 메뉴:")
                for category in menu_config.categories:
                    items = [name for name, item in menu_config.menu_items.items() if item.category == category]
                    if items:
                        print(f"  {category}: {', '.join(items)}")
                continue
            
            if user_input.lower() in ['order', '주문']:
                current_order = order_manager.get_current_order()
                if current_order and current_order.items:
                    print("📋 현재 주문:")
                    for item in current_order.items:
                        print(f"  - {item.name} x{item.quantity} = {item.price * item.quantity:,}원")
                    print(f"💰 총 금액: {current_order.total_amount:,}원")
                else:
                    print("📋 현재 주문된 메뉴가 없습니다.")
                continue
            
            # 간단한 메뉴 인식 (키워드 기반)
            found_menu = None
            for menu_name in menu_config.menu_items.keys():
                if menu_name in user_input:
                    found_menu = menu_name
                    break
            
            if found_menu:
                # 수량 추출 (간단한 방법)
                quantity = 1
                for word in user_input.split():
                    if word.isdigit():
                        quantity = int(word)
                        break
                
                # 주문 추가
                result = order_manager.add_item(found_menu, quantity)
                if result.success:
                    confirmation = response_system.generate_order_confirmation(
                        menu_name=found_menu,
                        quantity=quantity,
                        total_amount=0  # 간단한 테스트용
                    )
                    print(f"🤖 {confirmation.formatted_text}")
                else:
                    error_response = response_system.generate_error_response(
                        error_message=result.message
                    )
                    print(f"🤖 {error_response.formatted_text}")
            else:
                print("🤖 죄송합니다. 메뉴를 찾을 수 없습니다. 'menu'를 입력하여 사용 가능한 메뉴를 확인해보세요.")
        
    except Exception as e:
        print(f"❌ 대화형 테스트 중 오류: {e}")


def main():
    """메인 실행 함수"""
    print("🎤 간단한 음성 키오스크 시스템 테스트")
    print("=" * 60)
    
    # 기본 시스템 테스트
    if not test_basic_system():
        print("❌ 기본 시스템 테스트 실패")
        return
    
    # 메뉴 검색 테스트
    if not test_menu_search():
        print("❌ 메뉴 검색 테스트 실패")
        return
    
    # 대화형 테스트 제안
    print("\n" + "=" * 60)
    try:
        choice = input("대화형 테스트를 실행하시겠습니까? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '예']:
            interactive_test()
    except EOFError:
        print("입력이 종료되었습니다.")
    except KeyboardInterrupt:
        print("\n사용자가 취소했습니다.")
    
    print("\n🎉 모든 테스트가 완료되었습니다!")


if __name__ == "__main__":
    main()