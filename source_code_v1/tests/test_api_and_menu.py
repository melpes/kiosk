#!/usr/bin/env python3
"""
API 키와 메뉴 인식 테스트 스크립트
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
            print("✅ .env 파일을 성공적으로 로드했습니다.")
        else:
            print("❌ .env 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 환경 변수 로드 중 오류: {e}")

def test_api_key():
    """API 키 테스트"""
    print("\n🔑 API 키 테스트")
    print("-" * 30)
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API 키 존재: {bool(api_key)}")
    
    if api_key:
        print(f"API 키 길이: {len(api_key)}")
        print(f"API 키 시작: {api_key[:10]}...")
        print(f"API 키가 기본값인가: {api_key == 'your_openai_api_key_here'}")
        
        if api_key.startswith('sk-'):
            print("✅ 유효한 OpenAI API 키 형식입니다.")
        else:
            print("⚠️ OpenAI API 키 형식이 아닙니다.")
    else:
        print("❌ API 키가 설정되지 않았습니다.")

def test_menu_config():
    """메뉴 설정 테스트"""
    print("\n📋 메뉴 설정 테스트")
    print("-" * 30)
    
    try:
        from src.config import config_manager
        menu_config = config_manager.load_menu_config()
        
        print(f"✅ 메뉴 설정 로드 성공")
        print(f"메뉴 아이템 수: {len(menu_config.menu_items)}")
        print(f"카테고리 수: {len(menu_config.categories)}")
        
        print("\n사용 가능한 메뉴:")
        for name, item in list(menu_config.menu_items.items())[:5]:
            print(f"  - {name}: {item.price:,}원 ({item.category})")
        
        if len(menu_config.menu_items) > 5:
            print(f"  ... 외 {len(menu_config.menu_items) - 5}개")
            
    except Exception as e:
        print(f"❌ 메뉴 설정 로드 실패: {e}")
        import traceback
        traceback.print_exc()

def test_menu_recognition():
    """메뉴 인식 테스트"""
    print("\n🔍 메뉴 인식 테스트")
    print("-" * 30)
    
    try:
        from src.config import config_manager
        menu_config = config_manager.load_menu_config()
        
        test_inputs = [
            "빅맥",
            "빅맥 주문",
            "빅맥 2개",
            "콜라",
            "감자튀김",
            "메뉴 뭐있어?",
            "치킨너겟 3개"
        ]
        
        for test_input in test_inputs:
            print(f"\n입력: '{test_input}'")
            
            # 메뉴 인식 로직 (simple_interactive.py와 동일)
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
                
                print(f"  ✅ 인식된 메뉴: {found_menu} x{quantity}")
            else:
                print(f"  ❌ 메뉴를 찾을 수 없음")
                
    except Exception as e:
        print(f"❌ 메뉴 인식 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🧪 API 키와 메뉴 인식 테스트")
    print("=" * 50)
    
    # 환경 변수 로드
    load_env_file()
    
    # 테스트 실행
    test_api_key()
    test_menu_config()
    test_menu_recognition()
    
    print("\n" + "=" * 50)
    print("테스트 완료!")

if __name__ == "__main__":
    main()