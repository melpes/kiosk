#!/usr/bin/env python3
"""
MicrophoneInputManager 통합 테스트 데모
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.microphone_models import MicrophoneConfig
from src.microphone.microphone_manager import MicrophoneInputManager, MicrophoneError, RecordingError
from src.logger import get_logger

logger = get_logger(__name__)


def test_microphone_integration():
    """마이크 통합 테스트"""
    print("=== MicrophoneInputManager 통합 테스트 ===\n")
    
    # 설정 생성
    config = MicrophoneConfig(
        sample_rate=16000,
        frame_duration=0.5,
        max_silence_duration_start=5.0,
        max_silence_duration_end=3.0,
        min_record_duration=1.0,
        vad_threshold=0.2,
        output_filename="integration_test.wav"
    )
    
    try:
        # MicrophoneInputManager 초기화
        print("1. MicrophoneInputManager 초기화 중...")
        with MicrophoneInputManager(config) as mic_manager:
            
            # 진단 정보 출력
            print("\n2. 시스템 진단 정보:")
            diagnostic = mic_manager.get_diagnostic_info()
            print(f"   - 하드웨어 사용 가능: {diagnostic['hardware_status']['available']}")
            print(f"   - VAD 모델 준비됨: {diagnostic['vad_info']['model_loaded']}")
            print(f"   - 폴백 모드: {diagnostic['system_info']['fallback_mode']}")
            
            # 마이크 테스트
            print("\n3. 마이크 테스트 실행 중...")
            test_result = mic_manager.test_microphone()
            print(f"   - 전체 테스트 성공: {test_result['overall_success']}")
            print(f"   - 하드웨어 테스트: {test_result['hardware_test']['success']}")
            print(f"   - 녹음 테스트: {test_result['recording_test']['success']}")
            print(f"   - VAD 테스트: {test_result['vad_test']['success']}")
            
            if test_result.get('recommendations'):
                print("   권장사항:")
                for rec in test_result['recommendations']:
                    print(f"     - {rec}")
            
            if not test_result['overall_success']:
                print("   ⚠️ 마이크 테스트 실패. 기본 기능만 테스트합니다.")
                return
            
            # 설정 업데이트 테스트
            print("\n4. 설정 업데이트 테스트...")
            new_config = MicrophoneConfig(
                sample_rate=16000,
                vad_threshold=0.3,  # 임계값 변경
                max_silence_duration_end=2.0  # 무음 시간 단축
            )
            
            update_result = mic_manager.update_config(new_config)
            print(f"   - 설정 업데이트: {'성공' if update_result['success'] else '실패'}")
            if not update_result['success']:
                print(f"     오류: {update_result['message']}")
            
            # 상태 모니터링 테스트
            print("\n5. 상태 모니터링 테스트...")
            status = mic_manager.get_microphone_status()
            print(f"   - 현재 상태: {status['vad_status']}")
            print(f"   - 하드웨어 사용 가능: {status['hardware_available']}")
            print(f"   - 오류 개수: {status['error_count']}")
            
            # 실제 녹음 테스트 (사용자 선택)
            print("\n6. 실제 녹음 테스트를 진행하시겠습니까? (y/N): ", end="")
            user_input = input().strip().lower()
            
            if user_input == 'y':
                print("\n실제 녹음 테스트 시작...")
                try:
                    filename = mic_manager.start_listening()
                    print(f"\n✅ 녹음 완료! 파일: {filename}")
                    
                    # 파일 정보 출력
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        print(f"   파일 크기: {file_size} bytes")
                    
                except RecordingError as e:
                    print(f"\n❌ 녹음 오류: {e}")
                except MicrophoneError as e:
                    print(f"\n❌ 마이크 오류: {e}")
                except KeyboardInterrupt:
                    print("\n사용자에 의해 중단됨")
            else:
                print("실제 녹음 테스트를 건너뜁니다.")
            
            # 오류 기록 확인
            error_history = mic_manager.get_error_history()
            if error_history:
                print(f"\n7. 오류 기록 ({len(error_history)}개):")
                for i, error in enumerate(error_history[-3:], 1):  # 최근 3개만 표시
                    print(f"   {i}. [{error['error_type']}] {error['message']}")
            else:
                print("\n7. 오류 기록: 없음 ✅")
            
            print("\n=== 통합 테스트 완료 ===")
            
    except Exception as e:
        logger.error(f"통합 테스트 중 예상치 못한 오류: {e}")
        print(f"\n❌ 통합 테스트 실패: {e}")


def test_error_handling():
    """오류 처리 테스트"""
    print("\n=== 오류 처리 테스트 ===")
    
    # 잘못된 설정으로 테스트
    invalid_config = MicrophoneConfig(
        sample_rate=-1,  # 잘못된 값
        vad_threshold=2.0  # 범위 초과
    )
    
    try:
        mic_manager = MicrophoneInputManager(invalid_config)
        result = mic_manager.update_config(invalid_config)
        print(f"잘못된 설정 처리: {'성공' if not result['success'] else '실패'}")
        
    except Exception as e:
        print(f"예상된 오류 발생: {e}")


if __name__ == "__main__":
    try:
        test_microphone_integration()
        test_error_handling()
        
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류 발생: {e}")
        logger.error(f"메인 실행 중 오류: {e}")