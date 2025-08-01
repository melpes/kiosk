#!/usr/bin/env python3
"""
환경 변수 로딩 테스트
"""

import os
from pathlib import Path

def load_env_file(env_path=".env"):
    """환경 변수 파일을 수동으로 로드"""
    env_file = Path(env_path)
    if not env_file.exists():
        print(f"❌ .env 파일을 찾을 수 없습니다: {env_path}")
        return False
    
    print(f"📁 .env 파일 경로: {env_file.absolute()}")
    
    loaded_vars = {}
    with open(env_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                try:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    os.environ[key] = value
                    loaded_vars[key] = value
                    print(f"✅ {key} = {value[:20]}{'...' if len(value) > 20 else ''}")
                except Exception as e:
                    print(f"❌ 라인 {line_num} 파싱 오류: {e}")
    
    print(f"\n📊 총 {len(loaded_vars)}개 환경 변수 로드됨")
    return True

def test_api_key():
    """API 키 테스트"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        return False
    
    if api_key == "your_openai_api_key_here":
        print("❌ API 키가 기본값으로 설정되어 있습니다.")
        return False
    
    if not api_key.startswith('sk-'):
        print("❌ API 키 형식이 올바르지 않습니다. (sk-로 시작해야 함)")
        return False
    
    print(f"✅ API 키가 올바르게 설정되었습니다: {api_key[:20]}...")
    return True

def main():
    print("🔧 환경 변수 로딩 테스트")
    print("=" * 50)
    
    # 1. .env 파일 로드
    if load_env_file():
        print("\n🧪 API 키 검증")
        print("-" * 30)
        test_api_key()
        
        print("\n📋 주요 환경 변수 확인")
        print("-" * 30)
        important_vars = [
            'OPENAI_API_KEY', 'OPENAI_MODEL', 'LOG_LEVEL', 
            'RESTAURANT_NAME', 'LANGUAGE'
        ]
        
        for var in important_vars:
            value = os.getenv(var, 'NOT_SET')
            if var == 'OPENAI_API_KEY' and value != 'NOT_SET':
                display_value = f"{value[:10]}..."
            else:
                display_value = value
            print(f"  {var}: {display_value}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()