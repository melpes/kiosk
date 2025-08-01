#!/usr/bin/env python3
"""
간편한 실시간 클라이언트 시작 스크립트
"""

import sys
import argparse
from pathlib import Path

# 클라이언트 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="실시간 VAD 음성 클라이언트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  %(prog)s                           # 기본 설정으로 실행
  %(prog)s --server-url http://192.168.1.100:8000  # 다른 서버 사용
  %(prog)s --config custom.json      # 사용자 정의 설정
        """
    )
    
    parser.add_argument(
        "--server-url",
        help="서버 URL (config.json 설정보다 우선)"
    )
    
    parser.add_argument(
        "--config",
        default="config.json",
        help="설정 파일 경로 (기본값: config.json)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    try:
        print("🚀 실시간 VAD 음성 클라이언트 시작")
        print("=" * 50)
        
        # 완전한 클라이언트 import
        from examples.complete_realtime_client import CompleteRealTimeClient
        
        # 클라이언트 초기화
        client = CompleteRealTimeClient(args.config)
        
        # 서버 URL 오버라이드
        if args.server_url:
            client.config.server.url = args.server_url
            print(f"🔧 서버 URL 변경: {args.server_url}")
        
        # 상세 로그 설정
        if args.verbose:
            from utils.logger import setup_logging
            setup_logging(log_level="DEBUG")
            print("🐛 디버그 모드 활성화")
        
        # 서버 연결 확인
        if not client.check_server_connection():
            print(f"\n❌ 서버에 연결할 수 없습니다: {client.config.server.url}")
            print("\n💡 해결 방법:")
            print("   1. 서버가 실행 중인지 확인하세요")
            print("   2. --server-url 옵션으로 올바른 서버 주소를 지정하세요")
            print("   3. 방화벽 설정을 확인하세요")
            return 1
        
        # 마이크 시스템 테스트
        if not client.test_microphone_system():
            print("\n⚠️ 마이크 테스트 실패했지만 계속 진행합니다...")
        
        # 콜백 설정
        client.setup_callbacks()
        
        # 실시간 세션 시작
        print(f"\n🎤 실시간 음성 주문 시작!")
        print(f"📡 연결된 서버: {client.config.server.url}")
        client.run_interactive_session()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 중단되었습니다.")
        return 0
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())