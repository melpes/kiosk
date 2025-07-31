#!/usr/bin/env python3
"""
모든 통합 테스트를 실행하는 스크립트
"""

import sys
import subprocess
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_test(test_name, description):
    """개별 테스트 실행"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        test_path = Path(__file__).parent / test_name
        result = subprocess.run([sys.executable, str(test_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} 성공")
            if result.stdout:
                print("출력:")
                print(result.stdout)
        else:
            print(f"❌ {description} 실패")
            if result.stderr:
                print("오류:")
                print(result.stderr)
            if result.stdout:
                print("출력:")
                print(result.stdout)
                
        return result.returncode == 0
        
    except FileNotFoundError:
        print(f"❌ {test_name} 파일을 찾을 수 없습니다")
        return False


def main():
    """메인 실행 함수"""
    print("🎯 음성 키오스크 시스템 통합 테스트 모음")
    print("=" * 60)
    
    tests = [
        ("test_config_integration.py", "설정 관리 시스템 통합 테스트"),
        ("test_menu_integration.py", "메뉴 관리 시스템 통합 테스트"),
        ("test_response_integration.py", "응답 시스템 통합 테스트"),
        ("test_intent_integration.py", "의도 파악 시스템 통합 테스트"),
        ("test_dialogue_integration.py", "대화 관리 시스템 통합 테스트"),
        ("test_main_integration.py", "메인 파이프라인 통합 테스트"),
        ("test_cli_integration.py", "CLI 인터페이스 통합 테스트"),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_file, test_desc in tests:
        if run_test(test_file, test_desc):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 테스트 결과: {success_count}/{total_count} 성공")
    
    if success_count == total_count:
        print("🎉 모든 통합 테스트가 성공했습니다!")
    else:
        print(f"⚠️ {total_count - success_count}개의 테스트가 실패했습니다.")
    
    print("💡 개별 테스트를 실행하려면 각 파일을 직접 실행하세요.")
    print("💡 전체 시스템 테스트는 'test_integration_full.py'를 실행하세요.")
    print(f"{'='*60}")
    
    return success_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)