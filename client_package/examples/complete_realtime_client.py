#!/usr/bin/env python3
"""
완전한 실시간 마이크 입력 클라이언트
서버와 연결하여 VAD를 통한 실시간 음성 주문 처리
"""

import sys
import os
import time
from pathlib import Path

# 클라이언트 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import (
    VoiceClient, ConfigManager, RealTimeMicrophoneManager, 
    MicrophoneError, RecordingError
)
from utils.logger import setup_logging, get_logger


class CompleteRealTimeClient:
    """완전한 실시간 클라이언트"""
    
    def __init__(self, config_path="config.json"):
        self.config = None
        self.voice_client = None
        self.mic_manager = None
        self.logger = None
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "session_start_time": None
        }
        
        self._initialize(config_path)
    
    def _initialize(self, config_path):
        """클라이언트 초기화"""
        try:
            # 로깅 설정
            setup_logging(log_level="INFO")
            self.logger = get_logger(self.__class__.__name__)
            
            # 설정 로드
            self.config = ConfigManager.load_config(config_path)
            
            # 클라이언트 초기화
            self.voice_client = VoiceClient(self.config)
            
            # 실시간 마이크 관리자 초기화
            self.mic_manager = RealTimeMicrophoneManager(self.config, self.voice_client)
            
            self.logger.info("클라이언트 초기화 완료")
            
        except Exception as e:
            print(f"❌ 클라이언트 초기화 실패: {e}")
            raise
    
    def check_server_connection(self):
        """서버 연결 확인"""
        print("🏥 서버 연결 확인 중...")
        
        try:
            if self.voice_client.check_server_health():
                print("✅ 서버와의 연결이 정상입니다.")
                return True
            else:
                print("❌ 서버에 연결할 수 없습니다.")
                return False
        except Exception as e:
            print(f"❌ 서버 연결 오류: {e}")
            return False
    
    def test_microphone_system(self):
        """마이크 시스템 테스트"""
        print("\n🧪 마이크 시스템 테스트 중...")
        
        try:
            test_results = self.mic_manager.test_microphone()
            
            if test_results["overall_success"]:
                print("✅ 마이크 테스트 성공!")
                
                # 테스트 결과 상세 표시
                recording_test = test_results["recording_test"]
                print(f"   📊 평균 볼륨: {recording_test['average_volume']:.4f}")
                print(f"   📊 최대 볼륨: {recording_test['max_volume']:.4f}")
                print(f"   🎵 오디오 감지: {'✅' if recording_test['audio_detected'] else '❌'}")
                
                vad_test = test_results["vad_test"]
                if vad_test["success"]:
                    print(f"   🗣️ VAD 음성 감지: {'✅' if vad_test['speech_detected'] else '❌'}")
                    print("   🎯 VAD 모드 사용 가능")
                else:
                    print("   ⚠️ VAD 폴백 모드 (볼륨 기반 감지)")
                
                if test_results.get("recommendations"):
                    print("\n💡 권장사항:")
                    for rec in test_results["recommendations"]:
                        print(f"   - {rec}")
                
                return True
            else:
                print("❌ 마이크 테스트 실패:")
                
                if not test_results["hardware_test"]["success"]:
                    print(f"   🔧 하드웨어 오류: {test_results['hardware_test'].get('error', '알 수 없는 오류')}")
                
                if not test_results["recording_test"]["success"]:
                    print(f"   🎤 녹음 오류: {test_results['recording_test'].get('error', '알 수 없는 오류')}")
                
                print("\n💡 해결 방법:")
                print("   1. 마이크가 연결되어 있는지 확인하세요")
                print("   2. 마이크 권한이 허용되어 있는지 확인하세요")
                print("   3. 다른 프로그램에서 마이크를 사용하고 있지 않은지 확인하세요")
                print("   4. 마이크 볼륨을 확인하세요")
                
                return False
                
        except Exception as e:
            print(f"❌ 마이크 테스트 중 오류: {e}")
            return False
    
    def setup_callbacks(self):
        """콜백 함수 설정"""
        def on_audio_ready(audio_file_path):
            self.logger.info(f"음성 파일 준비됨: {audio_file_path}")
            print(f"🎵 음성 파일 생성: {Path(audio_file_path).name}")
        
        def on_response_received(response):
            self.session_stats["total_requests"] += 1
            
            if response.success:
                self.session_stats["successful_requests"] += 1
                
                print(f"\n✅ 서버 응답:")
                print(f"   📝 응답 텍스트: {response.message}")
                
                if response.order_data:
                    print(f"   🛒 주문 상태: {response.order_data}")
                
                if response.tts_audio_url:
                    print(f"   🔊 TTS 파일: {response.tts_audio_url}")
                    # TTS 파일 자동 다운로드 및 재생 (선택사항)
                    if self.config.ui.auto_play_tts:
                        self._play_tts_response(response.tts_audio_url)
                
                if response.ui_actions:
                    action_types = [action.action_type for action in response.ui_actions]
                    print(f"   🎬 UI 액션: {', '.join(action_types)}")
                
            else:
                self.session_stats["failed_requests"] += 1
                error_msg = response.error_info.error_message if response.error_info else '알 수 없는 오류'
                print(f"❌ 서버 오류: {error_msg}")
                
                if response.error_info and response.error_info.recovery_actions:
                    print("💡 복구 방법:")
                    for action in response.error_info.recovery_actions:
                        print(f"   - {action}")
            
            # 통계 출력
            success_rate = (self.session_stats["successful_requests"] / self.session_stats["total_requests"]) * 100
            print(f"📊 세션 통계: {self.session_stats['successful_requests']}/{self.session_stats['total_requests']} 성공 ({success_rate:.1f}%)")
        
        self.mic_manager.set_callbacks(
            on_audio_ready=on_audio_ready,
            on_response_received=on_response_received
        )
    
    def _play_tts_response(self, tts_url):
        """TTS 응답 재생 (선택사항)"""
        try:
            # TTS 파일 다운로드
            tts_file_path = self.voice_client.download_tts_file(tts_url)
            if tts_file_path:
                print(f"   🔊 TTS 재생: {tts_file_path}")
                # 여기서 실제 재생 로직을 구현할 수 있음
                # 예: pygame, playsound 등 사용
        except Exception as e:
            self.logger.warning(f"TTS 재생 실패: {e}")
    
    def show_session_info(self):
        """세션 정보 표시"""
        print(f"\n📊 세션 정보:")
        print(f"   🆔 세션 ID: {self.voice_client.get_session_id()}")
        print(f"   📡 서버 URL: {self.config.server.url}")
        print(f"   ⏰ 세션 시작: {self.session_stats['session_start_time']}")
        
        # 마이크 상태 표시
        mic_status = self.mic_manager.get_status()
        print(f"\n🎤 마이크 상태:")
        print(f"   🔧 하드웨어: {'✅' if mic_status['hardware_available'] else '❌'}")
        print(f"   🤖 VAD 모델: {'✅' if mic_status['vad_model_ready'] else '❌ (폴백 모드)'}")
        print(f"   📊 현재 볼륨: {mic_status['current_volume_level']:.4f}")
        
    def run_interactive_session(self):
        """대화형 세션 실행"""
        self.session_stats["session_start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n" + "="*70)
        print("🎙️ 실시간 음성 주문 시스템")
        print("="*70)
        print("💬 마이크에 대고 주문하세요 (예: '빅맥 세트 하나 주세요')")
        print("🔄 음성이 감지되면 자동으로 녹음하여 서버로 전송합니다")
        print("🚪 종료하려면 Ctrl+C를 누르세요")
        print("="*70)
        
        # 세션 정보 표시
        self.show_session_info()
        
        try:
            # 실시간 마이크 입력 시작
            self.mic_manager.start_listening()
            
        except KeyboardInterrupt:
            print("\n\n👋 세션이 사용자에 의해 종료되었습니다.")
            self._show_session_summary()
        except MicrophoneError as e:
            print(f"\n❌ 마이크 오류: {e}")
            print("💡 마이크 설정을 확인하고 다시 시도해주세요.")
        except RecordingError as e:
            print(f"\n❌ 녹음 오류: {e}")
            print("💡 마이크가 제대로 작동하는지 확인해주세요.")
        except Exception as e:
            print(f"\n❌ 예상치 못한 오류: {e}")
            self.logger.error(f"실행 중 오류: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def _show_session_summary(self):
        """세션 요약 표시"""
        duration = time.time() - time.mktime(time.strptime(self.session_stats["session_start_time"], "%Y-%m-%d %H:%M:%S"))
        
        print("\n" + "="*50)
        print("📊 세션 요약")
        print("="*50)
        print(f"⏰ 세션 시간: {duration:.0f}초")
        print(f"📞 총 요청 수: {self.session_stats['total_requests']}")
        print(f"✅ 성공 요청: {self.session_stats['successful_requests']}")
        print(f"❌ 실패 요청: {self.session_stats['failed_requests']}")
        
        if self.session_stats['total_requests'] > 0:
            success_rate = (self.session_stats['successful_requests'] / self.session_stats['total_requests']) * 100
            print(f"📈 성공률: {success_rate:.1f}%")
        
        print("="*50)
    
    def cleanup(self):
        """리소스 정리"""
        if self.voice_client:
            self.voice_client.close()
        self.logger.info("클라이언트 정리 완료")


def main():
    """메인 함수"""
    try:
        print("🎤 완전한 실시간 마이크 입력 클라이언트")
        print("=" * 50)
        
        # 클라이언트 초기화
        client = CompleteRealTimeClient()
        
        # 서버 연결 확인
        if not client.check_server_connection():
            print("\n💡 해결 방법:")
            print("   1. 서버가 실행 중인지 확인하세요")
            print("   2. config.json에서 서버 URL이 올바른지 확인하세요")
            print("   3. 네트워크 연결을 확인하세요")
            return 1
        
        # 마이크 시스템 테스트
        if not client.test_microphone_system():
            print("\n❌ 마이크 시스템 테스트 실패. 계속 진행하시겠습니까? (y/n): ", end="")
            try:
                if input().lower() not in ['y', 'yes', '예']:
                    return 1
            except (EOFError, KeyboardInterrupt):
                return 1
        
        # 콜백 설정
        client.setup_callbacks()
        
        # 대화형 세션 시작
        client.run_interactive_session()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 실행 중 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())