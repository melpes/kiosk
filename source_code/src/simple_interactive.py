#!/usr/bin/env python3
"""
간단한 대화형 모드 (API 키 없이도 작동)
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 수동 로드
def load_env_file(env_path=".env"):
    """환경 변수 파일을 수동으로 로드"""
    try:
        if Path(env_path).exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    except Exception as e:
        print(f"환경 변수 로드 중 오류: {e}")

load_env_file()

# 프로젝트 루트를 Python 경로에 추가 (직접 실행 시)
if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

try:
    from .config import config_manager
    from .order.menu import Menu
    from .order.order import OrderManager
    from .response.text_response import TextResponseSystem
except ImportError:
    # 직접 실행 시 절대 import 사용
    from src.config import config_manager
    from src.order.menu import Menu
    from src.order.order import OrderManager
    from src.response.text_response import TextResponseSystem
from dataclasses import asdict


def run_simple_interactive():
    """간단한 대화형 모드 실행"""
    print("🎤 음성 키오스크 시스템 (간단한 대화형 모드)")
    print("=" * 60)
    print("💡 'quit' 또는 'exit'를 입력하면 종료됩니다.")
    print("💡 'clear'를 입력하면 주문을 초기화합니다.")
    print("💡 'status'를 입력하면 현재 주문 상태를 확인합니다.")
    print("💡 'menu' 또는 '메뉴'를 입력하면 사용 가능한 메뉴를 확인합니다.")
    print("💡 메뉴명을 입력하여 주문하세요. 예: '빅맥', '콜라 2개'")
    print()
    
    try:
        # 시스템 초기화
        menu_config = config_manager.load_menu_config()
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
        print(f"🤖 {greeting.formatted_text}")
        
        while True:
            try:
                user_input = input("\n👤 사용자: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("👋 시스템을 종료합니다.")
                    break
                
                if user_input.lower() in ['clear', '초기화']:
                    order_manager.create_new_order()
                    print("🗑️ 주문이 초기화되었습니다.")
                    continue
                
                if user_input.lower() in ['status', '상태']:
                    current_order = order_manager.get_current_order()
                    if current_order and current_order.items:
                        print("📋 현재 주문:")
                        for item in current_order.items:
                            print(f"  - {item.name} x{item.quantity} = {item.price * item.quantity:,}원")
                        print(f"💰 총 금액: {current_order.total_amount:,}원")
                    else:
                        print("📋 현재 주문된 메뉴가 없습니다.")
                    continue
                
                if user_input.lower() in ['menu', '메뉴']:
                    print("📋 사용 가능한 메뉴:")
                    
                    for category in menu_config.categories:
                        items_in_category = []
                        for item_name, item_config in menu_config.menu_items.items():
                            if item_config.category == category:
                                items_in_category.append(f"{item_name} ({item_config.price:,}원)")
                        
                        if items_in_category:
                            print(f"  {category}: {', '.join(items_in_category)}")
                    
                    print("💡 메뉴명을 입력하여 주문하세요. 예: '빅맥 주문', '콜라 2개'")
                    continue
                
                # 간단한 메뉴 인식 (키워드 기반) - 개선된 버전
                found_menu = None
                user_input_lower = user_input.lower()
                
                # 메뉴 이름으로 직접 검색
                for menu_name in menu_config.menu_items.keys():
                    if menu_name.lower() in user_input_lower:
                        found_menu = menu_name
                        break
                
                # 메뉴 이름의 일부로 검색 (더 유연한 매칭)
                if not found_menu:
                    for menu_name in menu_config.menu_items.keys():
                        menu_words = menu_name.lower().split()
                        for word in menu_words:
                            if word in user_input_lower:
                                found_menu = menu_name
                                break
                        if found_menu:
                            break
                
                if found_menu:
                    # 수량 추출 (개선된 방법)
                    quantity = 1
                    import re
                    
                    # 숫자 + "개" 패턴 찾기
                    quantity_match = re.search(r'(\d+)\s*개', user_input)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                    else:
                        # 단순 숫자 찾기
                        numbers = re.findall(r'\d+', user_input)
                        if numbers:
                            quantity = int(numbers[0])
                    
                    # 주문 추가
                    result = order_manager.add_item(found_menu, quantity)
                    if result.success:
                        confirmation = response_system.generate_order_confirmation(
                            menu_name=found_menu,
                            quantity=quantity,
                            total_amount=0  # 간단한 테스트용
                        )
                        print(f"🤖 {confirmation.formatted_text}")
                        
                        # 현재 주문 상태 간단히 표시
                        current_order = order_manager.get_current_order()
                        if current_order:
                            print(f"📋 현재 총 {len(current_order.items)}개 아이템, {current_order.total_amount:,}원")
                    else:
                        error_response = response_system.generate_error_response(
                            error_message=result.message
                        )
                        print(f"🤖 {error_response.formatted_text}")
                else:
                    # 메뉴를 찾지 못한 경우, 더 친절한 응답
                    available_menus = list(menu_config.menu_items.keys())[:5]  # 처음 5개만 표시
                    menu_list = ", ".join(available_menus)
                    print(f"🤖 죄송합니다. '{user_input}'에서 메뉴를 찾을 수 없습니다.")
                    print(f"💡 사용 가능한 메뉴 예시: {menu_list}")
                    print("💡 'menu'를 입력하면 전체 메뉴를 확인할 수 있습니다.")
            
            except KeyboardInterrupt:
                print("\n👋 시스템을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 처리 중 오류가 발생했습니다: {e}")
        
    except Exception as e:
        print(f"❌ 시스템 초기화 중 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_simple_interactive()