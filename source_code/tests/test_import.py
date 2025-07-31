#!/usr/bin/env python3
"""
import 테스트 파일 - 모든 모듈이 정상적으로 import되는지 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """모든 주요 모듈의 import 테스트"""
    print("🔍 모듈 import 테스트를 시작합니다...")
    
    try:
        print("1. 환경 설정 모듈 테스트...")
        from src.utils.env_loader import ensure_env_loaded
        from src.config import config_manager
        from src.logger import setup_logging, get_logger
        print("   ✅ 환경 설정 모듈 import 성공")
        
        print("2. 데이터 모델 테스트...")
        from src.models.audio_models import AudioData
        from src.models.config_models import AudioConfig
        from src.models.conversation_models import IntentType
        from src.models.response_models import ResponseType
        print("   ✅ 데이터 모델 import 성공")
        
        print("3. 주문 관리 모듈 테스트...")
        from src.order.menu import Menu
        from src.order.order import OrderManager
        print("   ✅ 주문 관리 모듈 import 성공")
        
        print("4. 대화 처리 모듈 테스트...")
        from src.conversation.intent import IntentRecognizer
        from src.conversation.dialogue import DialogueManager
        print("   ✅ 대화 처리 모듈 import 성공")
        
        print("5. 응답 시스템 테스트...")
        from src.response.text_response import TextResponseSystem
        print("   ✅ 응답 시스템 import 성공")
        
        print("6. 오류 처리 모듈 테스트...")
        from src.error.handler import ErrorHandler
        print("   ✅ 오류 처리 모듈 import 성공")
        
        print("7. 메인 파이프라인 테스트...")
        from src.main import VoiceKioskPipeline
        print("   ✅ 메인 파이프라인 import 성공")
        
        print("\n🎉 모든 모듈 import 테스트 완료!")
        return True
        
    except ImportError as e:
        print(f"   ❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
        return False

def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n🔧 기본 기능 테스트를 시작합니다...")
    
    try:
        # 환경 변수 로드 테스트
        from src.utils.env_loader import ensure_env_loaded
        ensure_env_loaded()
        print("   ✅ 환경 변수 로드 성공")
        
        # 메뉴 로드 테스트
        from src.order.menu import Menu
        menu = Menu.from_config_file("config/menu_config.json")
        print(f"   ✅ 메뉴 로드 성공 ({len(menu.config.menu_items)}개 메뉴)")
        
        # 주문 관리자 초기화 테스트
        from src.order.order import OrderManager
        order_manager = OrderManager(menu)
        print("   ✅ 주문 관리자 초기화 성공")
        
        # 설정 관리자 테스트
        from src.config import config_manager
        config_valid = config_manager.validate_config()
        print(f"   {'✅' if config_valid else '⚠️'} 설정 검증 {'성공' if config_valid else '실패'}")
        
        print("\n🎉 기본 기능 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"   ❌ 기본 기능 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 음성 키오스크 시스템 - Import 및 기본 기능 테스트")
    print("=" * 60)
    
    import_success = test_imports()
    
    if import_success:
        functionality_success = test_basic_functionality()
        
        if functionality_success:
            print("\n" + "=" * 60)
            print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
            print("💡 이제 다음 명령어로 시스템을 실행할 수 있습니다:")
            print("   python main.py          # 메인 시스템 실행")
            print("   python debug.py         # 디버그 모드 실행")
            print("   python run_debug.py     # 팀원용 간편 실행")
            print("=" * 60)
        else:
            print("\n❌ 기본 기능 테스트에서 문제가 발견되었습니다.")
            sys.exit(1)
    else:
        print("\n❌ 모듈 import에서 문제가 발견되었습니다.")
        sys.exit(1)