#!/usr/bin/env python3
"""
음성 키오스크 시스템 통합 테스트 실행 스크립트
전체 파이프라인 end-to-end 테스트, 기본 시나리오별 통합 테스트, 오류 상황 통합 테스트를 실행합니다.
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_test_file(test_file, description):
    """개별 테스트 파일 실행"""
    print(f"\n{'='*60}")
    print(f"테스트: {description}")
    print(f"파일: {test_file}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        # Python으로 테스트 파일 실행
        result = subprocess.run([
            sys.executable, test_file
        ], capture_output=True, text=True, timeout=300)  # 5분 타임아웃
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"실행 시간: {duration:.2f}초")
        
        if result.returncode == 0:
            print("테스트 성공")
            if result.stdout:
                print("\n출력:")
                print(result.stdout)
        else:
            print("테스트 실패")
            if result.stdout:
                print("\n표준 출력:")
                print(result.stdout)
            if result.stderr:
                print("\n오류 출력:")
                print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("테스트 타임아웃 (5분 초과)")
        return False
    except Exception as e:
        print(f"테스트 실행 중 오류: {e}")
        return False


def check_dependencies():
    """필요한 의존성 확인"""
    print("의존성 확인 중...")
    
    required_modules = [
        'pytest',
        'unittest',
        'pathlib',
        'json',
        'tempfile',
        'decimal',
        'datetime'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  OK {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"  NG {module} (누락)")
    
    if missing_modules:
        print(f"\n누락된 모듈: {', '.join(missing_modules)}")
        print("다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_modules)}")
        return False
    
    print("모든 의존성이 확인되었습니다.")
    return True


def check_project_structure():
    """프로젝트 구조 확인"""
    print("\n프로젝트 구조 확인 중...")
    
    required_paths = [
        "src/",
        "src/main.py",
        "src/models/",
        "src/audio/",
        "src/speech/",
        "src/conversation/",
        "src/order/",
        "src/response/",
        "src/error/",
        "src/cli/",
        "config/",
        "tests/"
    ]
    
    missing_paths = []
    
    for path in required_paths:
        if os.path.exists(path):
            print(f"  OK {path}")
        else:
            missing_paths.append(path)
            print(f"  NG {path} (누락)")
    
    if missing_paths:
        print(f"\n누락된 경로: {', '.join(missing_paths)}")
        return False
    
    print("프로젝트 구조가 확인되었습니다.")
    return True


def main():
    """메인 실행 함수"""
    print("음성 키오스크 시스템 통합 테스트 시작")
    print(f"실행 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 의존성 확인
    if not check_dependencies():
        print("의존성 확인 실패")
        return False
    
    # 프로젝트 구조 확인
    if not check_project_structure():
        print("프로젝트 구조 확인 실패")
        return False
    
    # 실행할 테스트 파일들
    test_files = [
        {
            "file": "test_integration_full.py",
            "description": "전체 파이프라인 End-to-End 통합 테스트"
        },
        {
            "file": "test_main_integration.py",
            "description": "메인 파이프라인 통합 테스트"
        },
        {
            "file": "test_config_integration.py",
            "description": "설정 관리 시스템 통합 테스트"
        },
        {
            "file": "test_menu_integration.py",
            "description": "메뉴 관리 시스템 통합 테스트"
        },
        {
            "file": "test_intent_integration.py",
            "description": "의도 파악 시스템 통합 테스트"
        },
        {
            "file": "test_dialogue_integration.py",
            "description": "대화 관리 시스템 통합 테스트"
        },
        {
            "file": "test_response_integration.py",
            "description": "응답 시스템 통합 테스트"
        },
        {
            "file": "test_cli_integration.py",
            "description": "CLI 인터페이스 통합 테스트"
        }
    ]
    
    # 테스트 결과 추적
    results = []
    total_start_time = time.time()
    
    # 각 테스트 파일 실행
    for test_info in test_files:
        test_file = test_info["file"]
        description = test_info["description"]
        
        # 파일 존재 확인
        if not os.path.exists(test_file):
            print(f"\n테스트 파일 없음: {test_file}")
            results.append({
                "file": test_file,
                "description": description,
                "success": False,
                "reason": "파일 없음"
            })
            continue
        
        # 테스트 실행
        success = run_test_file(test_file, description)
        results.append({
            "file": test_file,
            "description": description,
            "success": success,
            "reason": "성공" if success else "실패"
        })
    
    # 전체 결과 요약
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    print(f"\n{'='*60}")
    print("통합 테스트 결과 요약")
    print('='*60)
    print(f"총 실행 시간: {total_duration:.2f}초")
    print(f"총 테스트 파일: {len(results)}")
    
    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]
    
    print(f"성공: {len(successful_tests)}")
    print(f"실패: {len(failed_tests)}")
    
    if successful_tests:
        print("\n성공한 테스트:")
        for result in successful_tests:
            print(f"  - {result['description']}")
    
    if failed_tests:
        print("\n실패한 테스트:")
        for result in failed_tests:
            print(f"  - {result['description']} ({result['reason']})")
    
    success_rate = len(successful_tests) / len(results) * 100 if results else 0
    print(f"\n성공률: {success_rate:.1f}%")
    
    # 최종 결과
    overall_success = len(failed_tests) == 0
    
    if overall_success:
        print("\n모든 통합 테스트가 성공적으로 완료되었습니다!")
    else:
        print(f"\n{len(failed_tests)}개의 테스트가 실패했습니다.")
    
    return overall_success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)