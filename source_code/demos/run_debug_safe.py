#!/usr/bin/env python3
"""
팀원용 간편 실행 스크립트 (안전한 입력 처리)
복잡한 옵션 없이 쉽게 시스템을 테스트할 수 있습니다.
"""

import sys
import subprocess
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.input_utils import get_menu_choice, safe_input, confirm_action, pause_for_continue


def print_menu():
    """메뉴 출력"""
    print("🎤 음성 키오스크 시스템 - 팀원용 테스트 도구")
    print("=" * 50)


def run_interactive_debug():
    """대화형 디버그 모드 실행"""
    print("🚀 대화형 디버그 모드를 시작합니다...")
    try:
        subprocess.run([
            sys.executable, "src/debug_main.py",
            "--mode", "interactive",
            "--debug"
        ])
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")


def run_text_test():
    """텍스트 입력 테스트"""
    print("\n💬 텍스트 입력 테스트")
    print("예시: '빅맥 세트 2개 주문해주세요', '감자튀김 추가', '결제할게요'")
    
    text = safe_input("테스트할 텍스트를 입력하세요: ")
    if not text:
        print("❌ 텍스트 입력이 취소되었습니다.")
        return
    
    print(f"\n🔍 '{text}' 처리 중...")
    try:
        subprocess.run([
            sys.executable, "src/debug_main.py",
            "--mode", "text",
            "--input", text,
            "--show-llm-processing",
            "--show-order-management",
            "--verbose"
        ])
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")


def run_audio_test():
    """음성 파일 테스트"""
    print("\n🎤 음성 파일 테스트")
    print("지원 형식: .wav, .mp3, .m4a")
    
    audio_path = safe_input("음성 파일 경로를 입력하세요: ")
    if not audio_path:
        print("❌ 파일 경로 입력이 취소되었습니다.")
        return
    
    if not Path(audio_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {audio_path}")
        return
    
    print(f"\n🔍 '{audio_path}' 처리 중...")
    try:
        subprocess.run([
            sys.executable, "src/debug_main.py",
            "--mode", "audio",
            "--input", audio_path,
            "--show-transcription",
            "--show-llm-processing",
            "--show-order-management",
            "--verbose"
        ])
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")


def check_system_status():
    """시스템 상태 확인"""
    print("\n🔧 시스템 상태를 확인합니다...")
    try:
        subprocess.run([sys.executable, "demos/demo_config_management.py"])
    except KeyboardInterrupt:
        print("\n상태 확인이 중단되었습니다.")


def run_demo():
    """데모 실행"""
    print("\n🎬 데모를 실행합니다...")
    try:
        subprocess.run([sys.executable, "demos/run_all_demos.py"])
    except KeyboardInterrupt:
        print("\n데모가 중단되었습니다.")


def run_simple_test():
    """간단한 시스템 테스트"""
    print("\n🧪 간단한 시스템 테스트를 실행합니다...")
    try:
        subprocess.run([sys.executable, "src/simple_debug.py"])
    except KeyboardInterrupt:
        print("\n테스트가 중단되었습니다.")


def main():
    """메인 실행 함수"""
    menu_items = {
        "0": "종료",
        "1": "간단한 시스템 테스트 (추천, API 키 불필요)",
        "2": "대화형 디버그 모드 (API 키 필요)",
        "3": "텍스트 입력 테스트 (API 키 필요)",
        "4": "음성 파일 테스트 (API 키 필요)",
        "5": "시스템 상태 확인",
        "6": "데모 실행"
    }
    
    while True:
        print_menu()
        choice = get_menu_choice(menu_items, "선택하세요")
        
        if choice is None:  # EOF 또는 KeyboardInterrupt
            print("👋 프로그램을 종료합니다.")
            break
        
        if choice == "0":
            print("👋 프로그램을 종료합니다.")
            break
        elif choice == "1":
            run_simple_test()
        elif choice == "2":
            run_interactive_debug()
        elif choice == "3":
            run_text_test()
        elif choice == "4":
            run_audio_test()
        elif choice == "5":
            check_system_status()
        elif choice == "6":
            run_demo()
        
        # 계속 진행 확인
        if not pause_for_continue():
            print("👋 프로그램을 종료합니다.")
            break
        
        print("\n" * 2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("프로그램을 종료합니다.")