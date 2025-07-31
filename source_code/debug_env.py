#!/usr/bin/env python3
"""
환경 변수 로드 상태 확인 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_env_vars():
    """환경 변수 상태 확인"""
    print("🔍 환경 변수 상태 확인")
    print("="*50)
    
    # .env 파일 존재 확인
    env_file = Path(".env")
    print(f"📁 .env 파일 존재: {env_file.exists()}")
    if env_file.exists():
        print(f"   경로: {env_file.absolute()}")
        print(f"   크기: {env_file.stat().st_size} bytes")
    
    # 환경 변수 로드
    from src.utils.env_loader import load_env_file, get_test_config
    loaded_vars = load_env_file()
    
    print(f"\n📋 로드된 환경 변수:")
    for key, value in loaded_vars.items():
        print(f"   {key} = {value}")
    
    # 테스트 설정 확인
    print(f"\n🧪 테스트 설정:")
    test_config = get_test_config()
    for key, value in test_config.items():
        print(f"   {key} = {value}")
    
    # 현재 환경 변수 상태
    print(f"\n🌍 현재 환경 변수 상태:")
    test_vars = [
        'TEST_MAX_TESTS_PER_CATEGORY',
        'TEST_DELAY_BETWEEN_REQUESTS', 
        'TEST_INCLUDE_SLANG',
        'TEST_INCLUDE_INFORMAL',
        'TEST_INCLUDE_COMPLEX',
        'TEST_INCLUDE_EDGE_CASES'
    ]
    
    for var in test_vars:
        value = os.getenv(var, 'NOT_SET')
        print(f"   {var} = {value}")

if __name__ == "__main__":
    check_env_vars() 