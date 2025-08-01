#!/usr/bin/env python3
"""
실시간 마이크 입력 클라이언트 예제
"""

import sys
import os
from pathlib import Path

# 클라이언트 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import VoiceClient, ConfigManager, RealTimeMicrophoneManager, MicrophoneError, RecordingError


def main():
    """실시간 마이크 입력 예제 실행"""
    try:
        print("🎤 실시간 마이크 입력 클라이언트 예제")
        print("=" * 50)
        
        # 설정 로드
        config = ConfigManager.load_config("config.json")
        
        # 클라이언트 초기화
        voice_client = VoiceClient(config)
        
        print(f"📡 서버: {config.server.url}")
        print(f"🆔 세션: {voice_client.get_session_id()}")
        print("-" * 50)
        
        # 서버 상태 확인
        print("🏥 서버 상태 확인 중...")
        if voice_client.check_server_health():
            print("✅ 서버가 정상적으로 작동 중입니다.")
        else:
            print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return 1
        
        # 실시간 마이크 관리자 초기화
        mic_manager = RealTimeMicrophoneManager(config, voice_client)
        
        # VAD 설정 최적화 (선택사항)
        # 더 민감한 감지를 원하면 임계값을 낮추세요 (기본값: 0.2)
        # 더 긴 선행 오디오를 원하면 preroll 시간을 늘리세요 (기본값: 1.0초)
        mic_manager.set_vad_settings(
            vad_threshold=0.15,  # 더 민감하게 설정 (음성 놓침 방지)
            preroll_duration=1.2  # 음성 시작 전 1.2초 포함 (자르기 방지)
        )
        
        # 콜백 함수 설정
        def on_audio_ready(audio_file_path):
            print(f"🎵 음성 파일 준비됨: {audio_file_path}")
        
        def on_response_received(response):
            if response.success:
                print(f"✅ 서버 응답:")
                print(f"   📝 텍스트: {response.message}")
                if response.tts_audio_url:
                    print(f"   🔊 TTS URL: {response.tts_audio_url}")
                if response.order_data:
                    print(f"   🛒 주문 상태: {response.order_data}")
            else:
                print(f"❌ 서버 오류: {response.error_info.error_message if response.error_info else '알 수 없는 오류'}")
        
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
        
        # VAD 설정 정보 출력
        status = mic_manager.get_status()
        print(f"\n⚙️ VAD 설정:")
        print(f"  - 감지 임계값: {status['vad_threshold']}")
        print(f"  - 선행 오디오: {status['preroll_duration']}초")
        print(f"  - 동작 모드: {'VAD 모드' if not status['fallback_mode'] else '폴백 모드 (볼륨 기반)'}")
        
        print("\n" + "="*70)
        print("🎙️ 실시간 마이크 입력 모드 시작")
        print("="*70)
        print("💬 마이크로 주문하세요 (예: '빅맥 세트 하나 주세요')")
        print("🚪 종료하려면 Ctrl+C를 누르세요")
        print("="*70)
        
        # 실시간 마이크 입력 시작
        mic_manager.start_listening()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
        return 0
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
        if 'voice_client' in locals():
            voice_client.close()


if __name__ == "__main__":
    sys.exit(main())