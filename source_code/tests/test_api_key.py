#!/usr/bin/env python3
"""
API 키 인식 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key

def main():
    print("🔑 API 키 인식 테스트")
    print("=" * 40)
    
    # 1. 환경 변수 로드
    print("1. 환경 변수 로드 중...")
    loaded = ensure_env_loaded()
    print(f"   {'✅' if loaded else '❌'} 환경 변수 로드: {'성공' if loaded else '실패'}")
    
    # 2. API 키 가져오기
    print("2. API 키 확인 중...")
    api_key = get_api_key()
    if api_key:
        print(f"   ✅ API 키 발견: {api_key[:20]}...")
    else:
        print("   ❌ API 키를 찾을 수 없습니다")
    
    # 3. API 키 유효성 검증
    print("3. API 키 유효성 검증 중...")
    is_valid = validate_api_key(api_key)
    print(f"   {'✅' if is_valid else '❌'} API 키 유효성: {'유효' if is_valid else '무효'}")
    
    # 4. OpenAI 클라이언트 테스트
    if is_valid:
        print("4. OpenAI 클라이언트 테스트 중...")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            print("   ✅ OpenAI 클라이언트 생성 성공")
            
            # 간단한 API 호출 테스트 (실제로는 호출하지 않음)
            print("   💡 API 키가 정상적으로 설정되었습니다!")
            
        except Exception as e:
            print(f"   ❌ OpenAI 클라이언트 생성 실패: {e}")
    else:
        print("4. ❌ API 키가 유효하지 않아 클라이언트 테스트를 건너뜁니다")
    
    print("\n" + "=" * 40)
    
    if is_valid:
        print("🎉 API 키가 정상적으로 인식되었습니다!")
        return True
    else:
        print("❌ API 키 설정에 문제가 있습니다.")
        print("\n해결 방법:")
        print("1. .env 파일에 올바른 API 키가 설정되어 있는지 확인")
        print("2. API 키가 'sk-'로 시작하는지 확인")
        print("3. API 키에 따옴표나 공백이 없는지 확인")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)