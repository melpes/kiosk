#!/usr/bin/env python3
"""
메뉴 표시 테스트 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
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

def test_menu_display():
    """메뉴 표시 테스트"""
    try:
        from src.config import config_manager
        
        print("🧪 메뉴 설정 로드 테스트")
        print("-" * 40)
        
        menu_config = config_manager.load_menu_config()
        print(f"✅ 메뉴 설정 로드 성공!")
        print(f"총 메뉴 아이템: {len(menu_config.menu_items)}개")
        print(f"카테고리: {len(menu_config.categories)}개")
        
        print("\n📋 전체 메뉴:")
        for category in menu_config.categories:
            items_in_category = []
            for item_name, item_config in menu_config.menu_items.items():
                if item_config.category == category:
                    items_in_category.append(f"{item_name} ({item_config.price:,}원)")
            
            if items_in_category:
                print(f"  {category}: {', '.join(items_in_category)}")
        
        print("\n🔍 메뉴 인식 테스트:")
        test_cases = [
            "메뉴 뭐있어?",
            "빅맥",
            "빅맥 주문해줘",
            "콜라 2개",
            "감자튀김 3개 주문",
            "치킨너겟",
            "아이스크림"
        ]
        
        for test_input in test_cases:
            print(f"\n입력: '{test_input}'")
            
            # 메뉴 인식 로직
            found_menu = None
            user_input_lower = test_input.lower()
            
            # 메뉴 이름으로 직접 검색
            for menu_name in menu_config.menu_items.keys():
                if menu_name.lower() in user_input_lower:
                    found_menu = menu_name
                    break
            
            # 메뉴 이름의 일부로 검색
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
                # 수량 추출
                import re
                quantity = 1
                quantity_match = re.search(r'(\d+)\s*개', test_input)
                if quantity_match:
                    quantity = int(quantity_match.group(1))
                else:
                    numbers = re.findall(r'\d+', test_input)
                    if numbers:
                        quantity = int(numbers[0])
                
                item_config = menu_config.menu_items[found_menu]
                total_price = item_config.price * quantity
                print(f"  ✅ 인식: {found_menu} x{quantity} = {total_price:,}원")
            else:
                print(f"  ❌ 메뉴를 찾을 수 없음")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_menu_display()