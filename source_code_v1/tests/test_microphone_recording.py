#!/usr/bin/env python3
"""
실제 마이크 녹음 테스트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.microphone_models import MicrophoneConfig
from src.microphone.microphone_manager import MicrophoneInputManager, MicrophoneError, RecordingError


def test_recording():
    """실제 녹음 테스트"""
    print("=== 실제 마이크 녹음 테스트 ===\n")
    
    config = MicrophoneConfig(
        sample_rate=16000,
        frame_duration=0.5,
        max_silence_duration_start=5.0,
        max_silence_duration_end=2.0,  # 짧게 설정
        min_record_duration=0.5,
        vad_threshold=0.2,
        output_filename="test_recording.wav"
    )
    
    try:
        with MicrophoneInputManager(config) as mic_manager:
            print("마이크 시스템이 준비되었습니다.")
            print("잠시 후 녹음이 시작됩니다. 아무 말이나 해보세요!")
            print("(Ctrl+C로 중단 가능)\n")
            
            filename = mic_manager.start_listening()
            
            print(f"\n✅ 녹음 완료!")
            print(f"파일: {filename}")
            
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"파일 크기: {file_size:,} bytes")
                
                # 파일 정보 더 자세히
                import wave
                try:
                    with wave.open(filename, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        duration = frames / sample_rate
                        print(f"샘플레이트: {sample_rate} Hz")
                        print(f"길이: {duration:.2f} 초")
                        print(f"프레임 수: {frames:,}")
                except Exception as e:
                    print(f"WAV 파일 정보 읽기 실패: {e}")
            
            # 상태 정보 출력
            status = mic_manager.get_microphone_status()
            print(f"\n최종 상태:")
            print(f"- VAD 상태: {status['vad_status']}")
            print(f"- 폴백 모드: {status['fallback_mode']}")
            print(f"- 오류 개수: {status['error_count']}")
            
    except RecordingError as e:
        print(f"\n❌ 녹음 오류: {e}")
    except MicrophoneError as e:
        print(f"\n❌ 마이크 오류: {e}")
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")


if __name__ == "__main__":
    test_recording()