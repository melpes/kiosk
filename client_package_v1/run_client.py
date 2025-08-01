#!/usr/bin/env python3
"""
키오스크 클라이언트 실행 스크립트
"""

import sys
import argparse
from pathlib import Path

# 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from client import VoiceClient, ConfigManager, KioskUIManager, RealTimeMicrophoneManager, MicrophoneError, RecordingError
from utils.logger import setup_logging, get_logger
from examples.demo_client import KioskClientDemo


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="키오스크 클라이언트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  %(prog)s --demo                           # 데모 모드 실행
  %(prog)s --audio-file test.wav            # 특정 파일 전송
  %(prog)s --realtime-mic                   # 실시간 마이크 입력 모드
  %(prog)s --server-url http://192.168.1.100:8000  # 다른 서버 사용
  %(prog)s --config my_config.json          # 사용자 정의 설정
  %(prog)s --check-health                   # 서버 상태 확인
        """
    )
    
    # 기본 옵션
    parser.add_argument(
        "--config", 
        default="config.json",
        help="설정 파일 경로 (기본값: config.json)"
    )
    parser.add_argument(
        "--server-url",
        help="서버 URL (설정 파일보다 우선)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="로그 레벨 (설정 파일보다 우선)"
    )
    
    # 실행 모드
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--demo",
        action="store_true",
        help="데모 모드 실행"
    )
    mode_group.add_argument(
        "--audio-file",
        help="전송할 음성 파일 경로"
    )
    mode_group.add_argument(
        "--check-health",
        action="store_true",
        help="서버 상태 확인"
    )
    mode_group.add_argument(
        "--show-config",
        action="store_true",
        help="현재 설정 표시"
    )
    mode_group.add_argument(
        "--realtime-mic",
        action="store_true",
        help="실시간 마이크 입력 모드"
    )
    
    # 추가 옵션
    parser.add_argument(
        "--session-id",
        help="사용할 세션 ID"
    )
    parser.add_argument(
        "--no-auto-play",
        action="store_true",
        help="TTS 자동 재생 비활성화"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    try:
        # 설정 로드
        config = ConfigManager.load_config(args.config)
        
        # 명령줄 인수로 설정 오버라이드
        if args.server_url:
            config.server.url = args.server_url
        if args.log_level:
            config.logging.level = args.log_level
        if args.no_auto_play:
            config.ui.auto_play_tts = False
        if args.verbose:
            config.ui.show_detailed_logs = True
            config.logging.level = "DEBUG"
        
        # 로깅 설정
        setup_logging(
            log_level=config.logging.level,
            log_file=config.logging.file,
            max_size=config.logging.max_size,
            backup_count=config.logging.backup_count,
            log_format=config.logging.format
        )
        
        logger = get_logger(__name__)
        logger.info("키오스크 클라이언트 시작")
        
        # 설정 검증
        is_valid, errors = ConfigManager.validate_config(config)
        if not is_valid:
            print("❌ 설정 오류:")
            for error in errors:
                print(f"   - {error}")
            return 1
        
        # 실행 모드별 처리
        if args.show_config:
            return show_config(config)
        elif args.check_health:
            return check_server_health(config)
        elif args.audio_file:
            return send_audio_file(config, args.audio_file, args.session_id)
        elif args.realtime_mic:
            return run_realtime_microphone(config, args.session_id)
        else:
            # 기본값은 데모 모드
            return run_demo(config)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        return 1


def show_config(config):
    """설정 정보 표시"""
    print("⚙️  현재 설정:")
    print("=" * 50)
    
    print(f"📡 서버:")
    print(f"   URL: {config.server.url}")
    print(f"   타임아웃: {config.server.timeout}초")
    print(f"   최대 재시도: {config.server.max_retries}회")
    
    print(f"\n🎵 오디오:")
    print(f"   최대 파일 크기: {config.audio.max_file_size:,} bytes")
    print(f"   지원 형식: {', '.join(config.audio.supported_formats)}")
    print(f"   임시 디렉토리: {config.audio.temp_dir}")
    
    print(f"\n🖥️  UI:")
    print(f"   자동 TTS 재생: {config.ui.auto_play_tts}")
    print(f"   상세 로그: {config.ui.show_detailed_logs}")
    print(f"   언어: {config.ui.language}")
    
    print(f"\n📝 로깅:")
    print(f"   레벨: {config.logging.level}")
    print(f"   파일: {config.logging.file}")
    print(f"   최대 크기: {config.logging.max_size:,} bytes")
    
    print(f"\n🔗 세션:")
    print(f"   자동 ID 생성: {config.session.auto_generate_id}")
    print(f"   타임아웃: {config.session.session_timeout}초")
    
    return 0


def check_server_health(config):
    """서버 상태 확인"""
    print("🏥 서버 상태 확인 중...")
    
    client = VoiceClient(config)
    try:
        is_healthy = client.check_server_health()
        
        if is_healthy:
            print("✅ 서버가 정상적으로 작동 중입니다.")
            return 0
        else:
            print("❌ 서버에 문제가 있습니다.")
            return 1
    finally:
        client.close()


def send_audio_file(config, audio_file_path, session_id=None):
    """단일 음성 파일 전송"""
    print(f"🎤 음성 파일 전송: {audio_file_path}")
    
    # 파일 존재 확인
    if not Path(audio_file_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {audio_file_path}")
        return 1
    
    client = VoiceClient(config)
    ui_manager = KioskUIManager(client)
    
    try:
        # 세션 ID 설정
        if session_id:
            client.set_session_id(session_id)
        
        print(f"📡 서버: {config.server.url}")
        print(f"🆔 세션: {client.get_session_id()}")
        print("-" * 50)
        
        # 음성 파일 전송
        response = client.send_audio_file(audio_file_path)
        
        # 응답 처리
        ui_manager.handle_response(response)
        
        return 0 if response.success else 1
        
    finally:
        client.close()


def run_demo(config):
    """데모 모드 실행"""
    demo = KioskClientDemo(config)
    try:
        demo.run_demo()
        return 0
    finally:
        demo.close()


def run_realtime_microphone(config, session_id=None):
    """실시간 마이크 입력 모드 실행"""
    print("🎤 실시간 마이크 입력 모드를 시작합니다...")
    
    # 클라이언트 초기화
    voice_client = VoiceClient(config)
    ui_manager = KioskUIManager(voice_client)
    
    try:
        # 세션 ID 설정
        if session_id:
            voice_client.set_session_id(session_id)
        
        print(f"📡 서버: {config.server.url}")
        print(f"🆔 세션: {voice_client.get_session_id()}")
        print("-" * 50)
        
        # 실시간 마이크 관리자 초기화
        mic_manager = RealTimeMicrophoneManager(config, voice_client)
        
        # 콜백 함수 설정
        def on_audio_ready(audio_file_path):
            print(f"🎵 음성 파일 준비됨: {audio_file_path}")
        
        def on_response_received(response):
            # UI 매니저를 통해 응답 처리
            ui_manager.handle_response(response)
        
        mic_manager.set_callbacks(
            on_audio_ready=on_audio_ready,
            on_response_received=on_response_received
        )
        
        # 마이크 테스트
        print("\n🧪 마이크 테스트 실행 중...")
        test_results = mic_manager.test_microphone()
        
        if not test_results["overall_success"]:
            print("❌ 마이크 테스트 실패:")
            if not test_results["hardware_test"]["success"]:
                print(f"  - 하드웨어 오류: {test_results['hardware_test'].get('error', '알 수 없는 오류')}")
            if not test_results["recording_test"]["success"]:
                print(f"  - 녹음 오류: {test_results['recording_test'].get('error', '알 수 없는 오류')}")
            
            print("\n💡 해결 방법:")
            print("  1. 마이크가 연결되어 있는지 확인하세요")
            print("  2. 마이크 권한이 허용되어 있는지 확인하세요")
            print("  3. 다른 프로그램에서 마이크를 사용하고 있지 않은지 확인하세요")
            return 1
        
        print("✅ 마이크 테스트 성공!")
        print(f"  - 평균 볼륨: {test_results['recording_test']['average_volume']:.4f}")
        print(f"  - 최대 볼륨: {test_results['recording_test']['max_volume']:.4f}")
        print(f"  - 오디오 감지: {'✅' if test_results['recording_test']['audio_detected'] else '❌'}")
        
        if test_results["vad_test"]["success"]:
            print(f"  - VAD 음성 감지: {'✅' if test_results['vad_test']['speech_detected'] else '❌'}")
        else:
            print(f"  - VAD 상태: ⚠️ 폴백 모드 (볼륨 기반 감지)")
        
        if test_results.get("recommendations"):
            print("\n💡 권장사항:")
            for rec in test_results["recommendations"]:
                print(f"  - {rec}")
        
        print("\n" + "="*70)
        print("🎙️ 실시간 마이크 입력 모드 시작")
        print("="*70)
        print("💬 마이크로 주문하세요")
        print("🚪 종료하려면 Ctrl+C를 누르세요")
        print("="*70)
        
        # 실시간 마이크 입력 시작
        mic_manager.start_listening()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        return 1
    except MicrophoneError as e:
        print(f"\n❌ 마이크 오류: {e}")
        return 1
    except RecordingError as e:
        print(f"\n❌ 녹음 오류: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        voice_client.close()


if __name__ == "__main__":
    sys.exit(main())