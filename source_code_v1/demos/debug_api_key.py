#!/usr/bin/env python3
"""
API 키 인식 문제 디버깅
"""

import sys
import os
from pathlib import Path

print("🔍 API 키 인식 문제 디버깅")
print("=" * 50)

# 1. 현재 작업 디렉토리 확인
print(f"1. 현재 작업 디렉토리: {os.getcwd()}")

# 2. .env 파일 존재 확인
env_file = Path(".env")
print(f"2. .env 파일 존재: {env_file.exists()}")
if env_file.exists():
    print(f"   .env 파일 경로: {env_file.absolute()}")
    print(f"   .env 파일 크기: {env_file.stat().st_size} bytes")

# 3. 환경 변수 직접 확인
print("3. 환경 변수 직접 확인:")
api_key_env = os.getenv('OPENAI_API_KEY')
print(f"   OPENAI_API_KEY (환경변수): {api_key_env}")

# 4. .env 파일 직접 읽기
print("4. .env 파일 직접 읽기:")
if env_file.exists():
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines[:10], 1):  # 처음 10줄만
            line = line.strip()
            if 'OPENAI_API_KEY' in line:
                print(f"   라인 {i}: {line[:50]}...")
                break
    except Exception as e:
        print(f"   .env 파일 읽기 오류: {e}")

# 5. 수동으로 환경 변수 로드
print("5. 수동으로 환경 변수 로드:")
if env_file.exists():
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'OPENAI_API_KEY':
                        os.environ[key] = value
                        print(f"   수동 로드 성공: {key} = {value[:20]}...")
                        break
    except Exception as e:
        print(f"   수동 로드 오류: {e}")

# 6. 로드 후 환경 변수 재확인
print("6. 로드 후 환경 변수 재확인:")
api_key_after = os.getenv('OPENAI_API_KEY')
print(f"   OPENAI_API_KEY (로드 후): {api_key_after[:20] if api_key_after else 'None'}...")

# 7. API 키 유효성 검증
print("7. API 키 유효성 검증:")
if api_key_after:
    is_valid = (
        api_key_after != 'your_openai_api_key_here' and
        api_key_after.startswith('sk-') and
        len(api_key_after) > 20
    )
    print(f"   유효성: {'✅ 유효' if is_valid else '❌ 무효'}")
    print(f"   길이: {len(api_key_after)}")
    print(f"   시작: {api_key_after[:10]}...")
else:
    print("   ❌ API 키를 찾을 수 없습니다")

# 8. 프로젝트 루트 경로 추가 후 테스트
print("8. 프로젝트 루트 경로 추가 후 테스트:")
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key
    
    print("   env_loader 모듈 import 성공")
    
    # 환경 변수 로드
    loaded = ensure_env_loaded()
    print(f"   ensure_env_loaded(): {loaded}")
    
    # API 키 가져오기
    api_key = get_api_key()
    print(f"   get_api_key(): {api_key[:20] if api_key else 'None'}...")
    
    # 유효성 검증
    is_valid = validate_api_key(api_key)
    print(f"   validate_api_key(): {is_valid}")
    
except Exception as e:
    print(f"   env_loader 테스트 오류: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("디버깅 완료!")