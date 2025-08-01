#!/usr/bin/env python3
"""
음성 통신 통합 테스트 실행 스크립트
Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logger import get_logger

logger = get_logger(__name__)


def check_dependencies():
    """필요한 의존성 확인"""
    required_packages = [
        'pytest',
        'requests',
        'fastapi',
        'uvicorn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"필요한 패키지가 설치되지 않았습니다: {', '.join(missing_packages)}")
        logger.info("다음 명령어로 설치하세요:")
        logger.info(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def setup_test_environment():
    """테스트 환경 설정"""
    logger.info("테스트 환경 설정 중...")
    
    # 환경 변수 설정
    os.environ["PYTHONPATH"] = str(project_root)
    os.environ["TESTING"] = "true"
    
    # 테스트용 설정
    os.environ["TTS_PROVIDER"] = "mock"  # 테스트용 모의 TTS
    os.environ["MAX_FILE_SIZE_MB"] = "10"
    os.environ["RATE_LIMIT_REQUESTS"] = "1000"  # 테스트용 높은 제한
    
    # 로그 디렉토리 생성
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.info("테스트 환경 설정 완료")


def run_basic_tests():
    """기본 통신 테스트 실행"""
    logger.info("=== 기본 통신 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "test_basic_voice_communication_flow or test_session_continuity",
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_file_format_tests():
    """파일 형식 테스트 실행"""
    logger.info("=== 파일 형식 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "test_various_audio_file_formats or test_invalid_file_format_handling",
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_error_recovery_tests():
    """오류 복구 테스트 실행"""
    logger.info("=== 오류 복구 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "test_error_recovery_scenarios or test_client_retry_mechanism",
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_performance_tests():
    """성능 테스트 실행"""
    logger.info("=== 성능 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "test_performance_requirements or test_concurrent_request_handling",
        "-v", "--tb=short", "--durations=10"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_integration_tests():
    """통합 테스트 실행"""
    logger.info("=== 통합 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "test_end_to_end_workflow or test_server_monitoring_integration",
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_stress_tests():
    """스트레스 테스트 실행"""
    logger.info("=== 스트레스 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-k", "TestVoiceCommunicationStress",
        "-v", "--tb=short", "--durations=0"
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def run_all_tests():
    """모든 테스트 실행"""
    logger.info("=== 전체 통합 테스트 실행 ===")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "-v", "--tb=short", "--durations=10",
        "--maxfail=5"  # 5개 실패 시 중단
    ]
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def generate_test_report():
    """테스트 보고서 생성"""
    logger.info("=== 테스트 보고서 생성 ===")
    
    report_dir = project_root / "test_results" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"voice_communication_test_report_{timestamp}.html"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_voice_communication.py"),
        "--html", str(report_file),
        "--self-contained-html",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        if result.returncode == 0:
            logger.info(f"테스트 보고서 생성 완료: {report_file}")
        return result.returncode == 0
    except Exception as e:
        logger.warning(f"테스트 보고서 생성 실패 (pytest-html 미설치?): {e}")
        return False


def main():
    """메인 함수"""
    logger.info("음성 통신 통합 테스트 시작")
    
    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # 테스트 환경 설정
    setup_test_environment()
    
    # 테스트 실행 옵션
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "basic":
            success = run_basic_tests()
        elif test_type == "format":
            success = run_file_format_tests()
        elif test_type == "error":
            success = run_error_recovery_tests()
        elif test_type == "performance":
            success = run_performance_tests()
        elif test_type == "integration":
            success = run_integration_tests()
        elif test_type == "stress":
            success = run_stress_tests()
        elif test_type == "report":
            success = generate_test_report()
        elif test_type == "all":
            success = run_all_tests()
        else:
            logger.error(f"알 수 없는 테스트 타입: {test_type}")
            logger.info("사용 가능한 옵션: basic, format, error, performance, integration, stress, report, all")
            sys.exit(1)
    else:
        # 기본적으로 모든 테스트 실행
        success = run_all_tests()
    
    if success:
        logger.info("모든 테스트가 성공적으로 완료되었습니다! ✅")
        
        # 성공 시 간단한 보고서 생성 시도
        try:
            generate_test_report()
        except:
            pass
        
        sys.exit(0)
    else:
        logger.error("일부 테스트가 실패했습니다! ❌")
        sys.exit(1)


if __name__ == "__main__":
    main()