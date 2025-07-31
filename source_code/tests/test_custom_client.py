#!/usr/bin/env python3
"""
커스텀 OpenAI 클라이언트 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.env_loader import ensure_env_loaded, get_api_key
from src.utils.openai_client import create_openai_client

def test_custom_client():
    print("🔧 커스텀 OpenAI 클라이언트 테스트")
    print("=" * 50)
    
    # 환경 변수 로드
    ensure_env_loaded()
    api_key = get_api_key()
    
    if not api_key:
        print("❌ API 키를 찾을 수 없습니다.")
        return False
    
    print(f"✅ API 키: {api_key[:20]}...")
    
    try:
        # 커스텀 클라이언트 생성
        client = create_openai_client(api_key)
        print("✅ 커스텀 클라이언트 생성 성공")
        
        # 간단한 채팅 테스트
        print("\n📝 간단한 채팅 테스트:")
        messages = [
            {"role": "user", "content": "안녕하세요! 간단히 인사해주세요."}
        ]
        
        response = client.chat_completions_create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"   응답: {response.choices[0].message.content}")
        print(f"   모델: {response.model}")
        print(f"   토큰 사용량: {response.usage}")
        
        # Tool calling 테스트
        print("\n🛠️ Tool calling 테스트:")
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "날씨 정보를 가져옵니다",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "도시 이름"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        messages = [
            {"role": "user", "content": "서울의 날씨를 알려주세요"}
        ]
        
        try:
            response = client.chat_completions_create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=tools,
                max_tokens=100
            )
            
            print(f"   Tool calling 응답: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"   Tool calling 테스트 실패: {e}")
        
        print("\n🎉 커스텀 클라이언트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 커스텀 클라이언트 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_custom_client()
    sys.exit(0 if success else 1)