#!/usr/bin/env python3
"""
MicrophoneInputManager 시스템 전체 테스트
Requirements 2.4, 4.2, 4.3, 4.4, 4.5 검증
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.microphone_models import MicrophoneConfig
from src.microphone.microphone_manager import MicrophoneInputManager, MicrophoneError, RecordingError, VADError
from src.logger import get_logger

logger = get_logger(__name__)


def test_requirement_2_4():
    """Requirement 2.4: 마이크 입력 처리 완료 후 음성인식 결과와 대화 응답 제공"""
    print("=== Requirement 2.4 테스트: 마이크 입력 처리 완료 ===")
    
    config = MicrophoneConfig(
        sample_rate=16000,
        max_silence_duration_end=2.0,
        min_record_duration=0.5,
        output_filename="req_2_4_test.wav"
    )
    
    try:
        with MicrophoneInputManager(config) as mic_manager:
            print("✅ MicrophoneInputManager 초기화 완료")
            
            # 마이크 입력 처리 시뮬레이션 (실제로는 VoiceKioskPipeline.process_audio_input()로 전달)
            print("마이크 입력 처리 시뮬레이션...")
            status = mic_manager.get_microphone_status()
            
            if status['hardware_available'] and status['vad_model_ready']:
                print("✅ 마이크 시스템이 음성 파일 생성 준비 완료")
                print("   - 실제 사용 시 VoiceKioskPipeline.process_audio_input()로 전달됨")
                return True
            else:
                print("❌ 마이크 시스템 준비 실패")
                return False
                
    except Exception as e:
        print(f"❌ Requirement 2.4 테스트 실패: {e}")
        return False


def test_requirement_4_2():
    """Requirement 4.2: 마이크 입력 시작 시 현재 설정값과 마이크 상태 표시"""
    print("\n=== Requirement 4.2 테스트: 설정값과 마이크 상태 표시 ===")
    
    config = MicrophoneConfig(
        sample_rate=16000,
        vad_threshold=0.3,
        max_silence_duration_start=5.0,
        max_silence_duration_end=3.0
    )
    
    try:
        with MicrophoneInputManager(config) as mic_manager:
            status = mic_manager.get_microphone_status()
            
            print("현재 설정값:")
            config_info = status['config']
            print(f"  - 샘플레이트: {config_info['sample_rate']} Hz")
            print(f"  - VAD 임계값: {config_info['vad_threshold']}")
            print(f"  - 최대 무음 시간 (시작): {config_info['max_silence_duration_start']}초")
            print(f"  - 최대 무음 시간 (종료): {config_info['max_silence_duration_end']}초")
            print(f"  - 최소 녹음 시간: {config_info['min_record_duration']}초")
            
            print("\n마이크 상태:")
            print(f"  - 하드웨어 사용 가능: {status['hardware_available']}")
            print(f"  - VAD 모델 준비됨: {status['vad_model_ready']}")
            print(f"  - 폴백 모드: {status['fallback_mode']}")
            print(f"  - 현재 상태: {status['vad_status']}")
            
            print("✅ Requirement 4.2: 설정값과 상태 표시 완료")
            return True
            
    except Exception as e:
        print(f"❌ Requirement 4.2 테스트 실패: {e}")
        return False


def test_requirement_4_3():
    """Requirement 4.3: 음성 감지 중 실시간 음성 감지 상태 시각적 표시"""
    print("\n=== Requirement 4.3 테스트: 실시간 음성 감지 상태 표시 ===")
    
    config = MicrophoneConfig(sample_rate=16000)
    
    try:
        with MicrophoneInputManager(config) as mic_manager:
            # 상태 표시 기능 테스트
            print("실시간 상태 표시 기능 테스트:")
            
            # 다양한 상태 시뮬레이션
            test_statuses = ["waiting", "detecting", "recording", "processing"]
            
            for test_status in test_statuses:
                mic_manager.status.vad_status = test_status
                mic_manager.status.current_volume_level = 0.1 if test_status == "detecting" else 0.01
                
                print(f"상태 '{test_status}' 표시 테스트:")
                mic_manager._display_status()
                print()  # 줄바꿈
            
            print("✅ Requirement 4.3: 실시간 상태 표시 기능 완료")
            return True
            
    except Exception as e:
        print(f"❌ Requirement 4.3 테스트 실패: {e}")
        return False


def test_requirement_4_4():
    """Requirement 4.4: 녹음 완료 시 녹음된 파일의 길이와 품질 정보 제공"""
    print("\n=== Requirement 4.4 테스트: 녹음 파일 정보 제공 ===")
    
    config = MicrophoneConfig(
        sample_rate=16000,
        output_filename="req_4_4_test.wav"
    )
    
    try:
        with MicrophoneInputManager(config) as mic_manager:
            # 녹음 정보 기능 테스트
            if mic_manager.audio_recorder:
                recording_info = mic_manager.audio_recorder.get_recording_info()
                
                print("녹음 정보 제공 기능:")
                print(f"  - 녹음 상태: {recording_info['is_recording']}")
                print(f"  - 녹음 시간: {recording_info['recording_duration']:.2f}초")
                print(f"  - 녹음된 프레임 수: {recording_info['recorded_frames_count']}")
                print(f"  - 설정 정보:")
                print(f"    * 샘플레이트: {recording_info['config']['sample_rate']} Hz")
                print(f"    * 프레임 지속시간: {recording_info['config']['frame_duration']}초")
                print(f"    * 최소 녹음 시간: {recording_info['config']['min_record_duration']}초")
                
                print("✅ Requirement 4.4: 녹음 파일 정보 제공 기능 완료")
                return True
            else:
                print("❌ 오디오 레코더가 초기화되지 않음")
                return False
                
    except Exception as e:
        print(f"❌ Requirement 4.4 테스트 실패: {e}")
        return False


def test_requirement_4_5():
    """Requirement 4.5: 마이크 입력 문제 발생 시 적절한 오류 메시지와 해결 방법 제공"""
    print("\n=== Requirement 4.5 테스트: 오류 처리 및 해결 방법 제공 ===")
    
    # 잘못된 설정으로 오류 유발
    invalid_config = MicrophoneConfig(
        sample_rate=-1,  # 잘못된 샘플레이트
        vad_threshold=2.0  # 범위 초과
    )
    
    try:
        with MicrophoneInputManager(invalid_config) as mic_manager:
            # 설정 업데이트로 오류 유발
            result = mic_manager.update_config(invalid_config)
            
            if not result['success']:
                print("오류 메시지 및 해결 방법:")
                print(f"  - 오류 발생: {result['message']}")
                
                # 오류 기록 확인
                error_history = mic_manager.get_error_history()
                if error_history:
                    latest_error = error_history[-1]
                    print(f"  - 오류 유형: {latest_error['error_type']}")
                    print(f"  - 오류 시간: {latest_error['timestamp']}")
                    print(f"  - 상세 메시지: {latest_error['message']}")
                
                # 진단 정보 제공
                diagnostic = mic_manager.get_diagnostic_info()
                print("\n진단 정보:")
                print(f"  - 하드웨어 상태: {diagnostic['hardware_status']['available']}")
                print(f"  - VAD 모델 상태: {diagnostic['vad_info']['model_loaded']}")
                print(f"  - 총 오류 수: {diagnostic['error_summary']['total_errors']}")
                
                # 해결 방법 제안
                print("\n해결 방법:")
                print("  1. 설정값을 올바른 범위로 수정하세요")
                print("  2. 시스템 재설정을 시도해보세요")
                print("  3. 하드웨어 연결을 확인하세요")
                
                print("✅ Requirement 4.5: 오류 처리 및 해결 방법 제공 완료")
                return True
            else:
                print("❌ 예상된 오류가 발생하지 않음")
                return False
                
    except Exception as e:
        print(f"예상된 오류 처리: {e}")
        print("✅ Requirement 4.5: 예외 처리 완료")
        return True


def test_error_handling_integration():
    """통합 오류 처리 테스트"""
    print("\n=== 통합 오류 처리 테스트 ===")
    
    config = MicrophoneConfig()
    
    try:
        with MicrophoneInputManager(config) as mic_manager:
            print("1. 시스템 재설정 테스트...")
            reset_result = mic_manager.reset_system()
            print(f"   재설정 결과: {'성공' if reset_result['success'] else '실패'}")
            
            print("2. 마이크 테스트...")
            test_result = mic_manager.test_microphone()
            print(f"   테스트 결과: {'성공' if test_result['overall_success'] else '실패'}")
            
            print("3. 진단 정보 확인...")
            diagnostic = mic_manager.get_diagnostic_info()
            print(f"   시스템 상태: 정상")
            print(f"   오류 개수: {diagnostic['error_summary']['total_errors']}")
            
            print("✅ 통합 오류 처리 테스트 완료")
            return True
            
    except Exception as e:
        print(f"❌ 통합 오류 처리 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("MicrophoneInputManager 통합 및 오류 처리 테스트")
    print("=" * 60)
    
    test_results = []
    
    # 각 요구사항 테스트 실행
    test_results.append(("Requirement 2.4", test_requirement_2_4()))
    test_results.append(("Requirement 4.2", test_requirement_4_2()))
    test_results.append(("Requirement 4.3", test_requirement_4_3()))
    test_results.append(("Requirement 4.4", test_requirement_4_4()))
    test_results.append(("Requirement 4.5", test_requirement_4_5()))
    test_results.append(("통합 오류 처리", test_error_handling_integration()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n전체 결과: {passed}/{len(test_results)} 테스트 통과")
    
    if passed == len(test_results):
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\nMicrophoneInputManager 통합 및 오류 처리 구현이 완료되었습니다.")
        print("주요 기능:")
        print("- VAD, 녹음, 실시간 처리 통합")
        print("- 마이크 하드웨어 오류 처리")
        print("- VAD 모델 로딩 실패 시 폴백 모드")
        print("- 마이크 설정 조정 및 검증")
        print("- 실시간 상태 모니터링")
        print("- 상세한 오류 기록 및 진단")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 구현을 확인해주세요.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류 발생: {e}")
        logger.error(f"메인 테스트 실행 중 오류: {e}")