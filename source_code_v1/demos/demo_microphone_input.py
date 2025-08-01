"""
VAD 기반 마이크 입력 데모
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.microphone_models import MicrophoneConfig
from src.microphone.microphone_manager import MicrophoneInputManager


def main():
    """마이크 입력 데모"""
    print("=== VAD 기반 마이크 입력 데모 ===")
    print("이 데모는 실제 마이크를 사용하여 음성을 녹음합니다.")
    print("말씀을 시작하면 자동으로 녹음이 시작되고, 무음이 지속되면 자동으로 종료됩니다.")
    
    # 설정
    config = MicrophoneConfig(
        max_silence_duration_start=5.0,  # 5초 대기
        max_silence_duration_end=3.0,    # 3초 무음 후 종료
        min_record_duration=1.0,         # 최소 1초 녹음
        vad_threshold=0.2,               # VAD 민감도
        output_filename="demo_recording.wav"
    )
    
    print(f"\n설정:")
    print(f"- 최대 대기 시간: {config.max_silence_duration_start}초")
    print(f"- 무음 종료 시간: {config.max_silence_duration_end}초")
    print(f"- 최소 녹음 시간: {config.min_record_duration}초")
    print(f"- VAD 임계값: {config.vad_threshold}")
    
    while True:
        print("\n옵션을 선택하세요:")
        print("1. 마이크 테스트")
        print("2. 음성 녹음 시작")
        print("3. 설정 변경")
        print("4. 종료")
        
        choice = input("선택 (1-4): ").strip()
        
        if choice == "1":
            test_microphone(config)
        elif choice == "2":
            record_audio(config)
        elif choice == "3":
            config = change_settings(config)
        elif choice == "4":
            print("데모를 종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")


def test_microphone(config: MicrophoneConfig):
    """마이크 테스트"""
    print("\n=== 마이크 테스트 ===")
    
    try:
        manager = MicrophoneInputManager(config)
        result = manager.test_microphone()
        
        if result["test_successful"]:
            print("✅ 마이크 테스트 성공!")
            print(f"평균 볼륨: {result['average_volume']:.6f}")
            print(f"최대 볼륨: {result['max_volume']:.6f}")
            print(f"샘플레이트: {result['sample_rate']}Hz")
        else:
            print("❌ 마이크 테스트 실패!")
            print(f"오류: {result['error']}")
            
    except Exception as e:
        print(f"❌ 마이크 테스트 중 오류: {e}")


def record_audio(config: MicrophoneConfig):
    """음성 녹음"""
    print("\n=== 음성 녹음 ===")
    
    try:
        manager = MicrophoneInputManager(config)
        
        print("준비 완료! 말씀해주세요...")
        filename = manager.start_listening()
        
        print(f"✅ 녹음 완료: {filename}")
        
        # 파일 정보 표시
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"파일 크기: {file_size} bytes")
        
    except ValueError as e:
        print(f"⚠️ 녹음 오류: {e}")
    except Exception as e:
        print(f"❌ 녹음 중 오류: {e}")


def change_settings(config: MicrophoneConfig) -> MicrophoneConfig:
    """설정 변경"""
    print("\n=== 설정 변경 ===")
    
    try:
        print("현재 설정:")
        print(f"1. 최대 대기 시간: {config.max_silence_duration_start}초")
        print(f"2. 무음 종료 시간: {config.max_silence_duration_end}초")
        print(f"3. 최소 녹음 시간: {config.min_record_duration}초")
        print(f"4. VAD 임계값: {config.vad_threshold}")
        
        choice = input("변경할 설정 번호 (1-4, 엔터로 건너뛰기): ").strip()
        
        if choice == "1":
            value = float(input(f"새로운 최대 대기 시간 (현재: {config.max_silence_duration_start}): "))
            config.max_silence_duration_start = value
        elif choice == "2":
            value = float(input(f"새로운 무음 종료 시간 (현재: {config.max_silence_duration_end}): "))
            config.max_silence_duration_end = value
        elif choice == "3":
            value = float(input(f"새로운 최소 녹음 시간 (현재: {config.min_record_duration}): "))
            config.min_record_duration = value
        elif choice == "4":
            value = float(input(f"새로운 VAD 임계값 (현재: {config.vad_threshold}): "))
            config.vad_threshold = value
        
        print("✅ 설정이 변경되었습니다.")
        
    except ValueError:
        print("❌ 잘못된 값입니다.")
    except Exception as e:
        print(f"❌ 설정 변경 중 오류: {e}")
    
    return config


if __name__ == "__main__":
    main()