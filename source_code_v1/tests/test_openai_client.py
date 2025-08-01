#!/usr/bin/env python3
"""
OpenAI 클라이언트 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.env_loader import get_api_key

def test_openai_client():
    print("🤖 OpenAI 클라이언트 테스트")
    print("=" * 40)
    
    api_key = get_api_key()
    if not api_key:
        print("❌ API 키를 찾을 수 없습니다.")
        return False
    
    print(f"✅ API 키: {api_key[:20]}...")
    
    # 방법 1: 기본 초기화
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        print("✅ 방법 1: 기본 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ 방법 1 실패: {e}")
    
    # 방법 2: 최소 설정으로 초기화
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            timeout=30.0
        )
        print("✅ 방법 2: 최소 설정 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ 방법 2 실패: {e}")
    
    # 방법 3: 환경 변수 사용
    try:
        import os
        os.environ['OPENAI_API_KEY'] = api_key
        from openai import OpenAI
        client = OpenAI()  # 환경 변수에서 자동으로 API 키 읽기
        print("✅ 방법 3: 환경 변수 사용 성공")
        return True
    except Exception as e:
        print(f"❌ 방법 3 실패: {e}")
    
    print("❌ 모든 방법이 실패했습니다.")
    return False

if __name__ == "__main__":
    success = test_openai_client()
    sys.exit(0 if success else 1)