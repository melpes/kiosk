#!/usr/bin/env python3
"""
음성 키오스크 서버 시작 스크립트
메인 프로젝트에서 이 스크립트를 실행하여 서버를 시작합니다.
"""

import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_environment():
    """환경 설정 확인"""
    print("🔧 환경 설정 확인 중...")
    
    # OpenAI API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print("💡 해결 방법:")
        print("   1. .env 파일에서 OPENAI_API_KEY를 설정하세요")
        print("   2. 또는 환경변수로 설정하세요: export OPENAI_API_KEY='your_key'")
        return False
    
    print(f"✅ OpenAI API 키: {api_key[:10]}...")
    
    # 기타 환경 변수 표시
    tts_provider = os.getenv('TTS_PROVIDER', 'openai')
    tts_model = os.getenv('TTS_MODEL', 'tts-1')
    tts_voice = os.getenv('TTS_VOICE', 'alloy')
    
    print(f"🎤 TTS 설정:")
    print(f"   - 제공자: {tts_provider}")
    print(f"   - 모델: {tts_model}")
    print(f"   - 음성: {tts_voice}")
    
    return True

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="음성 키오스크 서버 시작",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  %(prog)s                           # 기본 설정으로 서버 시작
  %(prog)s --host 0.0.0.0 --port 8000  # 특정 호스트/포트로 시작
  %(prog)s --debug                   # 디버그 모드로 시작
        """
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0", 
        help="서버 호스트 주소 (기본값: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="서버 포트 번호 (기본값: 8000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="디버그 모드 활성화"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="로그 레벨 (기본값: INFO)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎤 음성 키오스크 API 서버")
    print("=" * 70)
    
    # 환경 변수 로드
    try:
        from src.utils.env_loader import ensure_env_loaded
        ensure_env_loaded()
        print("✅ 환경 변수 로드 완료")
    except Exception as e:
        print(f"⚠️ 환경 변수 로드 실패: {e}")
    
    # 환경 변수에서 LOG_LEVEL 확인 및 적용
    env_log_level = os.getenv('LOG_LEVEL')
    if env_log_level and env_log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        # 명령행에서 log-level이 명시적으로 제공되지 않은 경우에만 환경 변수 사용
        if '--log-level' not in sys.argv:
            args.log_level = env_log_level.upper()
            print(f"✅ 환경 변수에서 로그 레벨 적용: {args.log_level}")
    
    # 환경 설정 확인
    if not check_environment():
        print("\n❌ 환경 설정을 완료한 후 다시 시도해주세요.")
        return 1
    
    # 로깅 설정
    try:
        from src.logger import setup_logging
        setup_logging(log_level=args.log_level)
        print("✅ 로깅 시스템 초기화 완료")
    except Exception as e:
        print(f"❌ 로깅 초기화 실패: {e}")
        return 1
    
    print(f"\n🚀 서버 설정:")
    print(f"   - 호스트: {args.host}")
    print(f"   - 포트: {args.port}")
    print(f"   - 디버그: {args.debug}")
    print(f"   - 로그레벨: {args.log_level}")
    
    print(f"\n📡 서버 URL: http://{args.host}:{args.port}")
    print(f"📊 헬스체크: http://{args.host}:{args.port}/health")
    print(f"📁 API 문서: http://{args.host}:{args.port}/docs")
    
    print("\n" + "=" * 70)
    print("🎯 클라이언트 사용 방법:")
    print("   1. client_package 디렉토리를 다른 컴퓨터로 복사")
    print("   2. client_package/config.json에서 server.url을 이 서버 주소로 설정")
    print(f"      \"url\": \"http://{args.host}:{args.port}\"")
    print("   3. 클라이언트에서 실행:")
    print("      python run_client.py --realtime-mic")
    print("=" * 70)
    
    try:
        print("\n🔄 서버 시작 중...")
        
        # 서버 실행
        from src.api.server import run_server
        run_server(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 서버가 사용자에 의해 중단되었습니다.")
        return 0
    except Exception as e:
        print(f"\n❌ 서버 실행 중 오류 발생: {e}")
        import traceback
        if args.debug:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())