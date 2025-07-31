"""
마이크 시스템 사용 예제
"""

import os
import sys
import time
from typing import Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.microphone.microphone_manager import MicrophoneInputManager, MicrophoneError, RecordingError
from src.models.microphone_models import MicrophoneConfig
from src.main import VoiceKioskPipeline


def example_1_basic_microphone_setup():
    """예제 1: 기본 마이크 설정 및 초기화"""
    print("=== 예제 1: 기본 마이크 설정 및 초기화 ===")
    
    # 기본 설정으로 마이크 설정 생성
    config = MicrophoneConfig()
    
    print("기본 마이크 설정:")
    print(f"  샘플링 레이트: {config.sample_rate} Hz")
    print(f"  프레임 지속시간: {config.frame_duration} 초")
    print(f"  VAD 임계값: {config.vad_threshold}")
    print(f"  시작 최대 무음 시간: {config.max_silence_duration_start} 초")
    print(f"  종료 최대 무음 시간: {config.max_silence_duration_end} 초")
    print(f"  최소 녹음 시간: {config.min_record_duration} 초")
    print(f"  출력 파일명: {config.output_filename}")
    
    try:
        # 마이크 매니저 초기화
        print("\n마이크 매니저 초기화 중...")
        manager = MicrophoneInputManager(config)
        
        print("✅ 마이크 매니저 초기화 성공")
        
        # 초기 상태 확인
        status = manager.get_microphone_status()
        print(f"\n초기 상태:")
        print(f"  입력 대기 중: {status['is_listening']}")
        print(f"  녹음 중: {status['is_recording']}")
        print(f"  VAD 모델 준비: {status['vad_model_ready']}")
        print(f"  폴백 모드: {status['fallback_mode']}")
        print(f"  하드웨어 사용 가능: {status['hardware_available']}")
        
    except Exception as e:
        print(f"❌ 마이크 매니저 초기화 실패: {e}")


def example_2_custom_microphone_config():
    """예제 2: 커스텀 마이크 설정"""
    print("=== 예제 2: 커스텀 마이크 설정 ===")
    
    # 커스텀 설정 생성
    custom_config = MicrophoneConfig(
        sample_rate=22050,              # 더 높은 샘플링 레이트
        frame_duration=0.3,             # 더 짧은 프레임
        max_silence_duration_start=3.0, # 더 짧은 시작 대기 시간
        max_silence_duration_end=2.0,   # 더 짧은 종료 대기 시간
        min_record_duration=0.5,        # 더 짧은 최소 녹음 시간
        vad_threshold=0.3,              # 더 높은 VAD 임계값 (덜 민감)
        output_filename="custom_mic_input.wav"
    )
    
    print("커스텀 마이크 설정:")
    print(f"  샘플링 레이트: {custom_config.sample_rate} Hz")
    print(f"  프레임 지속시간: {custom_config.frame_duration} 초")
    print(f"  VAD 임계값: {custom_config.vad_threshold}")
    print(f"  시작 최대 무음 시간: {custom_config.max_silence_duration_start} 초")
    print(f"  종료 최대 무음 시간: {custom_config.max_silence_duration_end} 초")
    print(f"  최소 녹음 시간: {custom_config.min_record_duration} 초")
    print(f"  출력 파일명: {custom_config.output_filename}")
    
    try:
        manager = MicrophoneInputManager(custom_config)
        print("✅ 커스텀 설정으로 마이크 매니저 초기화 성공")
        
    except Exception as e:
        print(f"❌ 커스텀 설정 초기화 실패: {e}")


def example_3_microphone_test():
    """예제 3: 마이크 테스트"""
    print("=== 예제 3: 마이크 테스트 ===")
    
    config = MicrophoneConfig()
    
    try:
        manager = MicrophoneInputManager(config)
        
        print("마이크 테스트 실행 중...")
        print("(테스트 중에 마이크에 소리를 내주세요)")
        
        # 마이크 테스트 실행
        test_result = manager.test_microphone()
        
        print(f"\n마이크 테스트 결과:")
        print(f"  전체 성공: {'✅' if test_result['overall_success'] else '❌'}")
        
        # 하드웨어 테스트 결과
        hw_test = test_result['hardware_test']
        print(f"  하드웨어 테스트: {'✅' if hw_test['success'] else '❌'}")
        if hw_test['success']:
            details = hw_test['details']
            print(f"    입력 장치 수: {details['input_devices_count']}")
            print(f"    기본 장치: {details['default_device']}")
            print(f"    기본 샘플레이트: {details['default_samplerate']} Hz")
        
        # 녹음 테스트 결과
        rec_test = test_result['recording_test']
        print(f"  녹음 테스트: {'✅' if rec_test['success'] else '❌'}")
        if rec_test['success']:
            print(f"    평균 볼륨: {rec_test['average_volume']:.6f}")
            print(f"    최대 볼륨: {rec_test['max_volume']:.6f}")
            print(f"    오디오 감지: {'✅' if rec_test['audio_detected'] else '❌'}")
        
        # VAD 테스트 결과
        vad_test = test_result['vad_test']
        print(f"  VAD 테스트: {'✅' if vad_test['success'] else '❌'}")
        if vad_test['success']:
            print(f"    음성 감지: {'✅' if vad_test['speech_detected'] else '❌'}")
        elif 'error' in vad_test:
            print(f"    VAD 오류: {vad_test['error']}")
        
        # 권장사항
        if 'recommendations' in test_result and test_result['recommendations']:
            print(f"\n권장사항:")
            for rec in test_result['recommendations']:
                print(f"  • {rec}")
        
    except Exception as e:
        print(f"❌ 마이크 테스트 실패: {e}")


def example_4_basic_voice_input():
    """예제 4: 기본 음성 입력"""
    print("=== 예제 4: 기본 음성 입력 ===")
    
    config = MicrophoneConfig()
    
    try:
        manager = MicrophoneInputManager(config)
        
        print("음성 입력 준비 완료!")
        print("아무 키나 누르면 음성 입력을 시작합니다...")
        input()
        
        print("\n음성 입력 시작...")
        print("말씀해주세요. 말을 멈추면 자동으로 녹음이 종료됩니다.")
        
        # 음성 입력 시작
        audio_file = manager.start_listening()
        
        print(f"\n✅ 음성 입력 완료!")
        print(f"녹음 파일: {audio_file}")
        
        # 파일 정보 확인
        if os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            print(f"파일 크기: {file_size} bytes")
        
    except MicrophoneError as e:
        print(f"❌ 마이크 오류: {e}")
    except RecordingError as e:
        print(f"❌ 녹음 오류: {e}")
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


def example_5_voice_input_with_pipeline():
    """예제 5: 파이프라인과 연동된 음성 입력"""
    print("=== 예제 5: 파이프라인과 연동된 음성 입력 ===")
    
    config = MicrophoneConfig()
    
    try:
        # 마이크 매니저와 파이프라인 초기화
        print("시스템 초기화 중...")
        manager = MicrophoneInputManager(config)
        pipeline = VoiceKioskPipeline()
        
        print("✅ 시스템 초기화 완료!")
        print("아무 키나 누르면 음성 주문을 시작합니다...")
        input()
        
        print("\n🎤 음성 주문을 말씀해주세요...")
        
        # 음성 입력
        audio_file = manager.start_listening()
        
        print(f"\n🔄 음성 처리 중...")
        
        # 파이프라인으로 음성 처리
        response = pipeline.process_audio_input(audio_file)
        
        print(f"\n🤖 시스템 응답:")
        print(f"   {response}")
        
        # 임시 파일 정리
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"\n🗑️ 임시 파일 정리 완료")
        
    except MicrophoneError as e:
        print(f"❌ 마이크 오류: {e}")
    except Exception as e:
        print(f"❌ 처리 오류: {e}")
        print("참고: 실제 음성 처리를 위해서는 OpenAI API 키가 필요합니다.")


def example_6_config_update():
    """예제 6: 런타임 설정 업데이트"""
    print("=== 예제 6: 런타임 설정 업데이트 ===")
    
    # 초기 설정
    initial_config = MicrophoneConfig(vad_threshold=0.2)
    
    try:
        manager = MicrophoneInputManager(initial_config)
        
        print("초기 설정:")
        status = manager.get_microphone_status()
        print(f"  VAD 임계값: {status['config']['vad_threshold']}")
        
        # 설정 업데이트
        print("\n설정 업데이트 중...")
        new_config = MicrophoneConfig(
            vad_threshold=0.3,  # 더 높은 임계값
            max_silence_duration_end=2.0  # 더 짧은 대기 시간
        )
        
        result = manager.update_config(new_config)
        
        if result["success"]:
            print("✅ 설정 업데이트 성공")
            
            # 업데이트된 설정 확인
            status = manager.get_microphone_status()
            print(f"\n업데이트된 설정:")
            print(f"  VAD 임계값: {status['config']['vad_threshold']}")
            print(f"  종료 대기 시간: {status['config']['max_silence_duration_end']}")
            
        else:
            print(f"❌ 설정 업데이트 실패: {result['message']}")
        
        # 잘못된 설정으로 업데이트 시도
        print(f"\n잘못된 설정으로 업데이트 시도...")
        invalid_config = MicrophoneConfig(
            vad_threshold=2.0,  # 잘못된 값 (0-1 범위 초과)
            sample_rate=-1000   # 잘못된 값
        )
        
        result = manager.update_config(invalid_config)
        
        if not result["success"]:
            print(f"✅ 잘못된 설정 거부됨: {result['message']}")
        
    except Exception as e:
        print(f"❌ 설정 업데이트 예제 실패: {e}")


def example_7_error_handling():
    """예제 7: 오류 처리 및 진단"""
    print("=== 예제 7: 오류 처리 및 진단 ===")
    
    config = MicrophoneConfig()
    
    try:
        manager = MicrophoneInputManager(config)
        
        # 진단 정보 확인
        print("시스템 진단 정보:")
        diagnostic = manager.get_diagnostic_info()
        
        print(f"  폴백 모드: {diagnostic['system_info']['fallback_mode']}")
        print(f"  VAD 프로세서 초기화: {diagnostic['system_info']['components_initialized']['vad_processor']}")
        print(f"  오디오 레코더 초기화: {diagnostic['system_info']['components_initialized']['audio_recorder']}")
        
        # 하드웨어 상태
        hw_status = diagnostic['hardware_status']
        print(f"  하드웨어 사용 가능: {hw_status['available']}")
        
        # 오류 기록 확인
        error_summary = diagnostic['error_summary']
        print(f"  총 오류 수: {error_summary['total_errors']}")
        
        if error_summary['total_errors'] > 0:
            print(f"  오류 유형: {', '.join(error_summary['error_types'])}")
            
            # 최근 오류 출력
            if error_summary['recent_errors']:
                print(f"  최근 오류:")
                for error in error_summary['recent_errors'][-3:]:  # 최근 3개만
                    print(f"    [{error['timestamp']}] {error['error_type']}: {error['message']}")
        
        # 오류 기록 초기화
        print(f"\n오류 기록 초기화...")
        manager.clear_error_history()
        
        # 시스템 재설정
        print(f"시스템 재설정...")
        reset_result = manager.reset_system()
        
        if reset_result["success"]:
            print("✅ 시스템 재설정 성공")
        else:
            print(f"❌ 시스템 재설정 실패: {reset_result['message']}")
        
    except Exception as e:
        print(f"❌ 진단 예제 실패: {e}")


def example_8_context_manager():
    """예제 8: 컨텍스트 매니저 사용"""
    print("=== 예제 8: 컨텍스트 매니저 사용 ===")
    
    config = MicrophoneConfig()
    
    print("컨텍스트 매니저를 사용한 안전한 마이크 사용:")
    
    try:
        # 컨텍스트 매니저로 안전한 사용
        with MicrophoneInputManager(config) as manager:
            print("✅ 마이크 매니저 생성됨")
            
            # 상태 확인
            status = manager.get_microphone_status()
            print(f"  하드웨어 사용 가능: {status['hardware_available']}")
            print(f"  VAD 모델 준비: {status['vad_model_ready']}")
            
            # 간단한 작업 수행
            print("  마이크 테스트 실행...")
            test_result = manager.test_microphone()
            print(f"  테스트 결과: {'성공' if test_result['overall_success'] else '실패'}")
            
        print("✅ 컨텍스트 매니저 종료 - 자동으로 정리됨")
        
    except Exception as e:
        print(f"❌ 컨텍스트 매니저 예제 실패: {e}")


def example_9_multiple_voice_inputs():
    """예제 9: 연속 음성 입력"""
    print("=== 예제 9: 연속 음성 입력 ===")
    
    config = MicrophoneConfig()
    
    try:
        with MicrophoneInputManager(config) as manager:
            print("연속 음성 입력 모드")
            print("각 입력 후 Enter를 누르면 다음 입력을 받습니다.")
            print("'quit'을 입력하면 종료합니다.")
            
            session_count = 0
            
            while True:
                user_input = input(f"\n[세션 {session_count + 1}] 음성 입력을 시작하려면 Enter를 누르세요 (quit으로 종료): ")
                
                if user_input.lower() == 'quit':
                    break
                
                try:
                    print(f"🎤 음성 입력 {session_count + 1} 시작...")
                    
                    start_time = time.time()
                    audio_file = manager.start_listening()
                    duration = time.time() - start_time
                    
                    print(f"✅ 음성 입력 완료 (소요시간: {duration:.1f}초)")
                    print(f"   파일: {audio_file}")
                    
                    # 파일 정보
                    if os.path.exists(audio_file):
                        file_size = os.path.getsize(audio_file)
                        print(f"   크기: {file_size} bytes")
                        
                        # 임시 파일 정리
                        os.remove(audio_file)
                    
                    session_count += 1
                    
                except (MicrophoneError, RecordingError) as e:
                    print(f"❌ 음성 입력 오류: {e}")
                    continue
                except KeyboardInterrupt:
                    print("\n음성 입력이 중단되었습니다.")
                    break
            
            print(f"\n총 {session_count}개의 음성 입력을 처리했습니다.")
        
    except Exception as e:
        print(f"❌ 연속 음성 입력 예제 실패: {e}")


def example_10_performance_monitoring():
    """예제 10: 성능 모니터링"""
    print("=== 예제 10: 성능 모니터링 ===")
    
    config = MicrophoneConfig()
    
    try:
        manager = MicrophoneInputManager(config)
        
        print("성능 모니터링 시작...")
        
        # 초기 상태 기록
        initial_status = manager.get_microphone_status()
        print(f"초기 상태:")
        print(f"  오류 수: {initial_status['error_count']}")
        
        # 여러 번의 상태 확인으로 성능 측정
        status_check_times = []
        
        for i in range(5):
            start_time = time.time()
            status = manager.get_microphone_status()
            check_time = time.time() - start_time
            status_check_times.append(check_time)
            
            print(f"  상태 확인 {i+1}: {check_time*1000:.2f}ms")
            time.sleep(0.1)  # 짧은 대기
        
        avg_check_time = sum(status_check_times) / len(status_check_times)
        print(f"\n평균 상태 확인 시간: {avg_check_time*1000:.2f}ms")
        
        # 진단 정보 성능 측정
        print(f"\n진단 정보 성능 측정...")
        start_time = time.time()
        diagnostic = manager.get_diagnostic_info()
        diagnostic_time = time.time() - start_time
        
        print(f"진단 정보 생성 시간: {diagnostic_time*1000:.2f}ms")
        
        # 메모리 사용량 추정 (간접적)
        import sys
        current_objects = len(gc.get_objects()) if 'gc' in sys.modules else "N/A"
        print(f"현재 객체 수: {current_objects}")
        
    except Exception as e:
        print(f"❌ 성능 모니터링 예제 실패: {e}")


def main():
    """모든 예제 실행"""
    print("마이크 시스템 사용 예제 실행")
    print("=" * 50)
    
    examples = [
        example_1_basic_microphone_setup,
        example_2_custom_microphone_config,
        example_3_microphone_test,
        example_4_basic_voice_input,
        example_5_voice_input_with_pipeline,
        example_6_config_update,
        example_7_error_handling,
        example_8_context_manager,
        example_9_multiple_voice_inputs,
        example_10_performance_monitoring
    ]
    
    print("실행할 예제를 선택하세요:")
    for i, example_func in enumerate(examples):
        print(f"  {i+1}. {example_func.__doc__.split(':')[1].strip()}")
    print(f"  0. 모든 예제 실행")
    
    try:
        choice = input("\n선택 (0-10): ").strip()
        
        if choice == "0":
            # 모든 예제 실행 (음성 입력 예제 제외)
            safe_examples = examples[:3] + examples[5:8] + examples[9:]  # 음성 입력 예제 제외
            for example_func in safe_examples:
                try:
                    example_func()
                    print()
                except Exception as e:
                    print(f"예제 실행 중 오류: {e}")
                    print()
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            examples[int(choice) - 1]()
        else:
            print("잘못된 선택입니다.")
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"예제 실행 중 오류: {e}")
    
    print("\n예제 실행 완료!")


if __name__ == "__main__":
    import gc  # 성능 모니터링용
    main()