#!/usr/bin/env python3
"""
팀원용 간편 실행 스크립트
복잡한 옵션 없이 쉽게 시스템을 테스트할 수 있습니다.
"""

import sys
import subprocess
from pathlib import Path


def print_menu():
    """메뉴 출력"""
    print("🎤 음성 키오스크 시스템 - 팀원용 테스트 도구")
    print("=" * 50)
    print("1. 대화형 모드 (디버그)")
    print("2. 텍스트 입력 테스트")
    print("3. 음성 파일 테스트")
    print("4. 시스템 상태 확인")
    print("5. 데모 실행")
    print("0. 종료")
    print("=" * 50)


def run_interactive_debug():
    """대화형 디버그 모드 실행"""
    print("🚀 대화형 디버그 모드를 시작합니다...")
    
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
                            import os
                            os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"환경 변수 로드 중 오류: {e}")
    
    load_env_file()
    
    # API 키 확인
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == "your_openai_api_key_here" or api_key.strip() == "":
        print("⚠️ OpenAI API 키가 설정되지 않았습니다.")
        print("💡 간단한 대화형 모드로 실행합니다 (기본 기능만 사용 가능)")
        subprocess.run([sys.executable, "src/simple_interactive.py"])
    else:
        print("✅ API 키가 설정되어 있습니다. 전체 기능을 사용합니다.")
        # debug_main.py가 있는지 확인
        if Path("src/debug_main.py").exists():
            subprocess.run([
                sys.executable, "src/debug_main.py",
                "--mode", "interactive",
                "--debug"
            ])
        else:
            print("⚠️ debug_main.py를 찾을 수 없습니다. 간단한 대화형 모드로 실행합니다.")
            subprocess.run([sys.executable, "src/simple_interactive.py"])


def run_text_test():
    """텍스트 입력 테스트"""
    print("\n💬 텍스트 입력 테스트")
    print("예시: '빅맥 세트 2개 주문해주세요', '감자튀김 추가', '결제할게요'")
    
    try:
        text = input("테스트할 텍스트를 입력하세요: ").strip()
        if not text:
            print("❌ 텍스트를 입력해주세요.")
            return
        
        print(f"\n🔍 '{text}' 처리 중...")
        subprocess.run([
            sys.executable, "src/debug_main.py",
            "--mode", "text",
            "--input", text,
            "--show-llm-processing",
            "--show-order-management",
            "--verbose"
        ])
    except EOFError:
        print("\n❌ 입력이 중단되었습니다.")
        return
    except KeyboardInterrupt:
        print("\n❌ 사용자가 취소했습니다.")
        return


def run_audio_test():
    """음성 파일 테스트"""
    print("\n🎤 음성 파일 테스트")
    print("지원 형식: .wav, .mp3, .m4a")
    
    try:
        audio_path = input("음성 파일 경로를 입력하세요: ").strip()
        if not audio_path:
            print("❌ 파일 경로를 입력해주세요.")
            return
        
        if not Path(audio_path).exists():
            print(f"❌ 파일을 찾을 수 없습니다: {audio_path}")
            return
    except EOFError:
        print("\n❌ 입력이 중단되었습니다.")
        return
    except KeyboardInterrupt:
        print("\n❌ 사용자가 취소했습니다.")
        return
    
    print(f"\n🔍 '{audio_path}' 처리 중...")
    subprocess.run([
        sys.executable, "src/debug_main.py",
        "--mode", "audio",
        "--input", audio_path,
        "--show-transcription",
        "--show-llm-processing",
        "--show-order-management",
        "--verbose"
    ])


def check_system_status():
    """시스템 상태 확인"""
    print("\n🔧 시스템 상태를 확인합니다...")
    subprocess.run([sys.executable, "demos/demo_config_management.py"])


def run_demo():
    """데모 실행"""
    print("\n🎬 데모를 실행합니다...")
    subprocess.run([sys.executable, "demos/run_all_demos.py"])


def main():
    """메인 실행 함수"""
    while True:
        try:
            print_menu()
            choice = input("선택하세요 (0-5): ").strip()
            
            if choice == "0":
                print("👋 프로그램을 종료합니다.")
                break
            elif choice == "1":
                run_interactive_debug()
            elif choice == "2":
                run_text_test()
            elif choice == "3":
                run_audio_test()
            elif choice == "4":
                check_system_status()
            elif choice == "5":
                run_demo()
            else:
                print("❌ 잘못된 선택입니다. 0-5 사이의 숫자를 입력해주세요.")
            
            try:
                input("\n계속하려면 Enter를 누르세요...")
            except EOFError:
                print("\n👋 프로그램을 종료합니다.")
                break
            except KeyboardInterrupt:
                print("\n👋 프로그램을 종료합니다.")
                break
            
            print("\n" * 2)
            
        except EOFError:
            print("\n👋 입력이 종료되어 프로그램을 종료합니다.")
            break
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")
            print("프로그램을 계속 실행합니다...")


if __name__ == "__main__":
    main()