#!/usr/bin/env python3
"""
OpenAI API 실제 호출 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.env_loader import ensure_env_loaded, get_api_key

def test_openai_api():
    print("🤖 OpenAI API 실제 호출 테스트")
    print("=" * 50)
    
    # 환경 변수 로드
    ensure_env_loaded()
    api_key = get_api_key()
    
    if not api_key:
        print("❌ API 키를 찾을 수 없습니다.")
        return False
    
    print(f"✅ API 키: {api_key[:20]}...")
    
    # 방법 1: requests 라이브러리로 직접 호출
    print("\n1. requests 라이브러리로 직접 API 호출:")
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'user', 'content': '안녕하세요'}
            ],
            'max_tokens': 50
        }
        
        print("   API 호출 중...")
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"   ✅ API 호출 성공!")
            print(f"   응답: {message}")
            return True
        else:
            print(f"   ❌ API 호출 실패: {response.status_code}")
            print(f"   오류: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ requests 호출 오류: {e}")
    
    # 방법 2: OpenAI 라이브러리 (환경 변수 설정)
    print("\n2. OpenAI 라이브러리 (환경 변수 설정):")
    try:
        os.environ['OPENAI_API_KEY'] = api_key
        
        # 기존 openai 모듈이 import되어 있다면 reload
        if 'openai' in sys.modules:
            import importlib
            importlib.reload(sys.modules['openai'])
        
        from openai import OpenAI
        
        # 최소한의 설정으로 클라이언트 생성
        client = OpenAI()
        
        print("   ✅ OpenAI 클라이언트 생성 성공!")
        
        # 간단한 API 호출
        print("   API 호출 중...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "안녕하세요"}
            ],
            max_tokens=50
        )
        
        message = response.choices[0].message.content
        print(f"   ✅ API 호출 성공!")
        print(f"   응답: {message}")
        return True
        
    except Exception as e:
        print(f"   ❌ OpenAI 라이브러리 오류: {e}")
    
    # 방법 3: 구버전 방식
    print("\n3. 구버전 openai 라이브러리 방식:")
    try:
        import openai
        openai.api_key = api_key
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "안녕하세요"}
            ],
            max_tokens=50
        )
        
        message = response.choices[0].message.content
        print(f"   ✅ 구버전 방식 성공!")
        print(f"   응답: {message}")
        return True
        
    except Exception as e:
        print(f"   ❌ 구버전 방식 오류: {e}")
    
    return False

if __name__ == "__main__":
    success = test_openai_api()
    if success:
        print("\n🎉 OpenAI API 테스트 성공!")
    else:
        print("\n❌ 모든 방법이 실패했습니다.")
        print("\n가능한 원인:")
        print("1. API 키가 만료되었거나 유효하지 않음")
        print("2. 네트워크 연결 문제")
        print("3. OpenAI 서비스 장애")
        print("4. 라이브러리 버전 호환성 문제")
    
    sys.exit(0 if success else 1)