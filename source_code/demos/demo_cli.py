#!/usr/bin/env python3
"""
CLI 인터페이스 데모 스크립트
기본 CLI 기능을 시연합니다.
"""

import sys
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.interface import CLIInterface
from src.logger import setup_logging, get_logger


def run_cli_demo():
    """CLI 데모 실행"""
    print("🎬 CLI 인터페이스 데모를 시작합니다...")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging(log_level="INFO", log_file="logs/demo_cli.log")
    logger = get_logger("demo_cli")
    
    try:
        # CLI 인터페이스 초기화
        cli = CLIInterface()
        
        if not cli.initialize():
            print("❌ CLI 시스템 초기화에 실패했습니다.")
            return
        
        print("✅ CLI 시스템이 성공적으로 초기화되었습니다.")
        
        # 1. 시스템 상태 확인
        print("\n1️⃣ 시스템 상태 확인:")
        print("-" * 30)
        cli.show_status()
        
        time.sleep(2)
        
        # 2. 메뉴 표시
        print("\n2️⃣ 메뉴 표시:")
        print("-" * 30)
        cli.show_menu()
        
        time.sleep(2)
        
        # 3. 데모 시나리오 실행
        print("\n3️⃣ 데모 시나리오 실행:")
        print("-" * 30)
        cli.run_demo()
        
        time.sleep(2)
        
        # 4. 주문 확인
        print("\n4️⃣ 주문 확인:")
        print("-" * 30)
        cli.show_order()
        
        time.sleep(2)
        
        # 5. 시스템 테스트
        print("\n5️⃣ 시스템 테스트:")
        print("-" * 30)
        cli.run_test()
        
        print("\n✅ CLI 데모가 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"CLI 데모 실행 중 오류: {e}")
        print(f"❌ 데모 실행 중 오류가 발생했습니다: {e}")
    
    finally:
        if 'cli' in locals():
            cli.quit_system()


def run_interactive_demo():
    """대화형 데모 실행"""
    print("💬 대화형 CLI 데모를 시작합니다...")
    print("=" * 60)
    print("💡 다음 명령어들을 시도해보세요:")
    print("  • help - 도움말")
    print("  • status - 시스템 상태")
    print("  • menu - 메뉴 보기")
    print("  • demo - 자동 데모")
    print("  • test - 시스템 테스트")
    print("  • '빅맥 세트 하나 주세요' - 주문 테스트")
    print("  • quit - 종료")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging(log_level="INFO", log_file="logs/demo_cli_interactive.log")
    
    try:
        # CLI 인터페이스 초기화 및 실행
        cli = CLIInterface()
        
        if not cli.initialize():
            print("❌ CLI 시스템 초기화에 실패했습니다.")
            return
        
        # 대화형 모드 실행
        cli.run_interactive_mode()
        
    except Exception as e:
        print(f"❌ 대화형 데모 실행 중 오류가 발생했습니다: {e}")


def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_demo()
    else:
        run_cli_demo()


if __name__ == "__main__":
    main()