"""
음성 통신 통합 테스트 실행기
개별 테스트나 전체 테스트 스위트를 실행할 수 있는 스크립트
"""

import pytest
import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logger import get_logger

logger = get_logger(__name__)


def run_integration_tests(test_pattern: str = None, verbose: bool = True, 
                         capture: str = "no", markers: str = None):
    """
    통합 테스트 실행
    
    Args:
        test_pattern: 실행할 테스트 패턴 (예: "test_basic_*")
        verbose: 상세 출력 여부
        capture: 출력 캡처 설정 ("no", "sys", "fd")
        markers: pytest 마커 필터
    """
    logger.info("음성 통신 통합 테스트 시작")
    
    # pytest 인수 구성
    args = [
        str(Path(__file__).parent / "test_voice_communication.py"),
        "--tb=short",  # 짧은 traceback
        "--durations=10",  # 가장 느린 10개 테스트 표시
    ]
    
    if verbose:
        args.append("-v")
    
    if capture:
        args.extend(["-s", f"--capture={capture}"])
    
    if markers:
        args.extend(["-m", markers])
    
    if test_pattern:
        args.extend(["-k", test_pattern])
    
    # 환경 변수 설정
    os.environ["PYTEST_CURRENT_TEST"] = "voice_communication_integration"
    
    # 테스트 실행
    exit_code = pytest.main(args)
    
    if exit_code == 0:
        logger.info("모든 통합 테스트가 성공적으로 완료되었습니다")
    else:
        logger.error(f"일부 테스트가 실패했습니다 (종료 코드: {exit_code})")
    
    return exit_code


def run_specific_test_class(class_name: str):
    """특정 테스트 클래스 실행"""
    logger.info(f"테스트 클래스 실행: {class_name}")
    
    args = [
        str(Path(__file__).parent / "test_voice_communication.py"),
        f"::{class_name}",
        "-v",
        "--tb=short"
    ]
    
    return pytest.main(args)


def run_performance_tests():
    """성능 테스트만 실행"""
    logger.info("성능 테스트 실행")
    
    args = [
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "performance or concurrent or stress",
        "-v",
        "--tb=short",
        "--durations=0"
    ]
    
    return pytest.main(args)


def run_error_recovery_tests():
    """오류 복구 테스트만 실행"""
    logger.info("오류 복구 테스트 실행")
    
    args = [
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "error or recovery or invalid",
        "-v",
        "--tb=short"
    ]
    
    return pytest.main(args)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="음성 통신 통합 테스트 실행기")
    
    parser.add_argument(
        "--pattern", "-k",
        help="실행할 테스트 패턴 (예: 'test_basic_*')"
    )
    
    parser.add_argument(
        "--class", "-c",
        dest="test_class",
        help="실행할 테스트 클래스 이름"
    )
    
    parser.add_argument(
        "--performance", "-p",
        action="store_true",
        help="성능 테스트만 실행"
    )
    
    parser.add_argument(
        "--error-recovery", "-e",
        action="store_true",
        help="오류 복구 테스트만 실행"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="상세 출력"
    )
    
    parser.add_argument(
        "--capture",
        choices=["no", "sys", "fd"],
        default="no",
        help="출력 캡처 설정"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="pytest 마커 필터"
    )
    
    args = parser.parse_args()
    
    try:
        if args.test_class:
            exit_code = run_specific_test_class(args.test_class)
        elif args.performance:
            exit_code = run_performance_tests()
        elif args.error_recovery:
            exit_code = run_error_recovery_tests()
        else:
            exit_code = run_integration_tests(
                test_pattern=args.pattern,
                verbose=args.verbose,
                capture=args.capture,
                markers=args.markers
            )
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("테스트 실행이 사용자에 의해 중단되었습니다")
        sys.exit(1)
    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()