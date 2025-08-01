#!/usr/bin/env python3
"""
간단한 API 키 테스트 (OpenAI 클라이언트 없이)
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key

def main():
    print("🔑 간단한 API 키 테스트")
    print("=" * 40)
    
    # 환경 변수 로드
    ensure_env_loaded()
    
    # API 키 확인
    api_key = get_api_key()
    
    if not api_key:
        print("❌ API 키를 찾을 수 없습니다.")
        print("\n해결 방법:")
        print("1. .env 파일을 확인하세요")
        print("2. OPENAI_API_KEY=sk-your-key-here 형태로 설정하세요")
        return False
    
    if not validate_api_key(api_key):
        print("❌ API 키가 유효하지 않습니다.")
        print(f"현재 API 키: {api_key[:20]}...")
        return False
    
    print(f"✅ API 키가 정상적으로 설정되었습니다!")
    print(f"   API 키: {api_key[:20]}...")
    
    # 환경 변수 확인
    print(f"   모델: {os.getenv('OPENAI_MODEL', 'gpt-4o')}")
    print(f"   최대 토큰: {os.getenv('OPENAI_MAX_TOKENS', '1000')}")
    
    print("\n🎉 API 키 테스트 완료!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n💡 이제 다음 명령어로 시스템을 테스트할 수 있습니다:")
        print("   python src/debug_main.py --mode text --input \"빅맥 주문\" --verbose")
    sys.exit(0 if success else 1)