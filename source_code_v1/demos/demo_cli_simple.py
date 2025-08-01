#!/usr/bin/env python3
"""
간단한 CLI 테스트 스크립트
API 키 없이도 기본 CLI 기능을 테스트합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.interface import CLIInterface
from src.logger import setup_logging, get_logger


def test_cli_basic_functions():
    """CLI 기본 기능 테스트"""
    print("🧪 CLI 기본 기능 테스트를 시작합니다...")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging(log_level="INFO", log_file="logs/demo_cli_simple.log")
    logger = get_logger("demo_cli_simple")
    
    try:
        # CLI 인터페이스 생성
        cli = CLIInterface()
        
        print("✅ CLI 인터페이스 객체가 생성되었습니다.")
        
        # 기본 명령어 테스트
        print("\n1️⃣ 도움말 테스트:")
        print("-" * 30)
        cli.show_help()
        
        print("\n2️⃣ 명령어 처리 테스트:")
        print("-" * 30)
        
        # 유효한 명령어 테스트
        test_commands = ['help', '도움말', 'status', '상태']
        for cmd in test_commands:
            result = cli.process_command(cmd)
            status = "✅ 성공" if result else "❌ 실패"
            print(f"  명령어 '{cmd}': {status}")
        
        # 무효한 명령어 테스트
        invalid_commands = ['invalid', '존재하지않음']
        for cmd in invalid_commands:
            result = cli.process_command(cmd)
            status = "✅ 올바르게 거부됨" if not result else "❌ 잘못 처리됨"
            print(f"  무효한 명령어 '{cmd}': {status}")
        
        print("\n3️⃣ CLI 초기화 테스트:")
        print("-" * 30)
        
        init_result = cli.initialize()
        if init_result:
            print("✅ CLI 초기화 성공")
            
            # 초기화 후 상태 확인
            print("\n4️⃣ 시스템 상태 확인:")
            print("-" * 30)
            cli.show_status()
            
            print("\n5️⃣ 설정 정보 확인:")
            print("-" * 30)
            cli.show_config()
            
        else:
            print("⚠️ CLI 초기화 실패 (정상적인 경우 - API 키 미설정)")
        
        print("\n✅ CLI 기본 기능 테스트가 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"CLI 테스트 중 오류: {e}")
        print(f"❌ 테스트 중 오류가 발생했습니다: {e}")
    
    finally:
        print("\n👋 테스트를 종료합니다.")


def test_cli_commands_only():
    """CLI 명령어만 테스트 (초기화 없이)"""
    print("🔧 CLI 명령어 단독 테스트를 시작합니다...")
    print("=" * 60)
    
    try:
        cli = CLIInterface()
        
        print("📖 도움말:")
        cli.show_help()
        
        print("\n⚙️ 설정 정보:")
        cli.show_config()
        
        print("\n✅ 명령어 단독 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 명령어 테스트 중 오류: {e}")


def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1 and sys.argv[1] == "--commands-only":
        test_cli_commands_only()
    else:
        test_cli_basic_functions()


if __name__ == "__main__":
    main()