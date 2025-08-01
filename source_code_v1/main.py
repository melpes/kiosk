#!/usr/bin/env python3
"""
음성 기반 키오스크 AI 주문 시스템 - 프로젝트 루트 실행 파일
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# src.main 모듈에서 main 함수 import 및 실행
if __name__ == "__main__":
    from src.main import main
    main()