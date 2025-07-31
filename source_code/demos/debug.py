#!/usr/bin/env python3
"""
디버그 모드 실행 파일 - 프로젝트 루트에서 실행
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    from src.debug_main import main
    main()