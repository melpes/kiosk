"""
음성 처리 API 서버 CLI
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.server import run_server
from src.logger import setup_logging, get_logger


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="음성 처리 API 서버")
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="서버 호스트 주소 (기본값: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="서버 포트 번호 (기본값: 8000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="로그 레벨 (기본값: INFO)"
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging(level=args.log_level)
    logger = get_logger(__name__)
    
    logger.info(f"음성 처리 API 서버 시작")
    logger.info(f"호스트: {args.host}")
    logger.info(f"포트: {args.port}")
    logger.info(f"디버그 모드: {args.debug}")
    
    try:
        run_server(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        logger.info("서버가 사용자에 의해 중단되었습니다")
    except Exception as e:
        logger.error(f"서버 실행 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()