#!/usr/bin/env python3
"""
팀원용 초간단 테스트 스크립트
"""

import subprocess
import sys

def main():
    print("🎤 음성 키오스크 시스템 - 초간단 테스트")
    print("=" * 50)
    print("1. 기본 테스트 (API 키 불필요)")
    print("2. 전체 테스트 (API 키 필요)")
    print("3. 시스템 상태 확인")
    print("0. 종료")
    print("=" * 50)
    
    try:
        choice = input("선택하세요 (0-3): ").strip()
        
        if choice == "1":
            print("🚀 기본 테스트를 시작합니다...")
            subprocess.run([sys.executable, "src/simple_debug.py"])
        elif choice == "2":
            print("🚀 전체 테스트를 시작합니다...")
            subprocess.run([sys.executable, "run_debug.py"])
        elif choice == "3":
            print("🔧 시스템 상태를 확인합니다...")
            subprocess.run([sys.executable, "demos/demo_config_management.py"])
        elif choice == "0":
            print("👋 종료합니다.")
        else:
            print("❌ 잘못된 선택입니다.")
    except EOFError:
        print("\n👋 입력이 종료되어 프로그램을 종료합니다.")
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")

if __name__ == "__main__":
    main()