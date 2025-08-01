#!/usr/bin/env python3
"""
HuggingFace 토큰 설정 도우미 스크립트

사용법:
    python setup_huggingface_token.py

또는 환경변수로 직접 설정:
    export HUGGINGFACE_TOKEN="your_token_here"
    # 또는
    export HF_TOKEN="your_token_here"
"""

import os
import sys

def setup_huggingface_token():
    """HuggingFace 토큰 설정 가이드"""
    print("="*80)
    print("🤗 HuggingFace 토큰 설정 가이드")
    print("="*80)
    
    # 현재 토큰 상태 확인
    current_token = os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HF_TOKEN')
    if current_token:
        print(f"✅ 현재 토큰이 설정되어 있습니다: {current_token[:8]}...")
        print("토큰을 변경하려면 계속 진행하세요.\n")
    else:
        print("❌ 토큰이 설정되지 않았습니다.\n")
    
    print("📋 HuggingFace 토큰 생성 및 설정 방법:")
    print("1. HuggingFace 계정 생성 (무료): https://huggingface.co/join")
    print("2. 토큰 생성 페이지: https://hf.co/settings/tokens")
    print("3. 'New token' 클릭 → 'Write' 권한 선택 → 토큰 생성")
    print("4. Gated 모델 접근 승인:")
    print("   - https://hf.co/pyannote/speaker-diarization-3.1")
    print("   - https://hf.co/pyannote/speaker-diarization")
    print("   - 각 페이지에서 'Accept repository conditions' 클릭")
    print()
    
    # 토큰 입력 받기
    token = input("생성된 HuggingFace 토큰을 입력하세요 (Enter로 건너뛰기): ").strip()
    
    if not token:
        print("\n⚠️  토큰을 입력하지 않았습니다.")
        print("토큰 없이도 기본 에너지 기반 화자 분리는 사용 가능합니다.")
        return None
    
    # 토큰 유효성 간단 체크
    if len(token) < 20 or not token.startswith('hf_'):
        print("\n⚠️  토큰 형식이 올바르지 않을 수 있습니다.")
        print("HuggingFace 토큰은 보통 'hf_'로 시작하고 길이가 20자 이상입니다.")
        
        confirm = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            return None
    
    # 환경변수 설정 방법 안내
    print(f"\n✅ 토큰: {token[:8]}...")
    print("\n📝 환경변수 설정 방법:")
    
    if os.name == 'nt':  # Windows
        print("Windows Command Prompt:")
        print(f"set HUGGINGFACE_TOKEN={token}")
        print("\nWindows PowerShell:")
        print(f"$env:HUGGINGFACE_TOKEN='{token}'")
    else:  # Linux/Mac
        print("Linux/Mac Terminal:")
        print(f"export HUGGINGFACE_TOKEN='{token}'")
        print("\n영구 설정 (~/.bashrc 또는 ~/.zshrc에 추가):")
        print(f"echo 'export HUGGINGFACE_TOKEN=\"{token}\"' >> ~/.bashrc")
    
    print("\n🔄 .env 파일 생성:")
    env_file = ".env"
    try:
        # .env 파일에 토큰 추가/업데이트
        env_content = ""
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 기존 HUGGINGFACE_TOKEN 라인 제거
            env_content = ''.join([
                line for line in lines 
                if not line.startswith('HUGGINGFACE_TOKEN=') and not line.startswith('HF_TOKEN=')
            ])
        
        # 새 토큰 추가
        env_content += f"HUGGINGFACE_TOKEN={token}\n"
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"✅ {env_file} 파일에 토큰이 저장되었습니다!")
        
    except Exception as e:
        print(f"⚠️  .env 파일 저장 실패: {e}")
    
    print("\n🧪 토큰 테스트:")
    print("python test_speaker_separation.py")
    
    return token

def test_token():
    """토큰 테스트"""
    print("\n🧪 HuggingFace 토큰 테스트 중...")
    
    try:
        from transformers import pipeline
        # 간단한 공개 모델로 토큰 테스트
        classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        result = classifier("This is a test.")
        print("✅ 토큰이 정상적으로 작동합니다!")
        return True
    except Exception as e:
        print(f"❌ 토큰 테스트 실패: {e}")
        print("토큰을 다시 확인해주세요.")
        return False

if __name__ == "__main__":
    try:
        token = setup_huggingface_token()
        
        if token:
            # 현재 세션에서 환경변수 설정
            os.environ['HUGGINGFACE_TOKEN'] = token
            
            # 토큰 테스트
            test_result = input("\n토큰을 테스트하시겠습니까? (y/N): ").strip().lower()
            if test_result == 'y':
                test_token()
        
        print("\n🎉 설정 완료!")
        print("이제 화자 분리 시스템을 사용할 수 있습니다.")
        
    except KeyboardInterrupt:
        print("\n\n❌ 설정이 취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        sys.exit(1)