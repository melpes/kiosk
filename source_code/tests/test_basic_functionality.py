"""
기본 기능 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_test_case_generator():
    """TestCaseGenerator 기본 기능 테스트"""
    print("=== TestCaseGenerator 테스트 ===")
    
    try:
        from src.testing.test_case_generator import TestCaseGenerator
        from src.models.testing_models import TestCaseCategory
        from src.models.conversation_models import IntentType
        
        # 생성기 초기화
        generator = TestCaseGenerator()
        print("✅ TestCaseGenerator 초기화 성공")
        
        # 은어 매핑 확인
        slang_count = len(generator.slang_mappings)
        print(f"✅ 은어 매핑 {slang_count}개 로드됨")
        
        # 메뉴 아이템 확인
        menu_count = len(generator.menu_items)
        print(f"✅ 메뉴 아이템 {menu_count}개 로드됨")
        
        # 은어 테스트케이스 생성
        slang_cases = generator.generate_slang_cases()
        print(f"✅ 은어 테스트케이스 {len(slang_cases)}개 생성됨")
        
        # 반말 테스트케이스 생성
        informal_cases = generator.generate_informal_cases()
        print(f"✅ 반말 테스트케이스 {len(informal_cases)}개 생성됨")
        
        # 전체 테스트케이스 생성
        all_cases = generator.generate_mcdonald_test_cases()
        print(f"✅ 전체 테스트케이스 {len(all_cases)}개 생성됨")
        
        # 카테고리별 분류 확인
        categories = {}
        for case in all_cases:
            cat = case.category
            categories[cat] = categories.get(cat, 0) + 1
        
        print("카테고리별 분포:")
        for cat, count in categories.items():
            print(f"  {cat.value}: {count}개")
        
        # 샘플 테스트케이스 출력
        print("\n샘플 테스트케이스:")
        for i, case in enumerate(all_cases[:3]):
            print(f"  {i+1}. [{case.category.value}] {case.input_text}")
            print(f"     예상 의도: {case.expected_intent.value}")
            print(f"     신뢰도: {case.expected_confidence_min}")
        
        return True
        
    except Exception as e:
        print(f"❌ TestCaseGenerator 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_microphone_config():
    """MicrophoneConfig 기본 기능 테스트"""
    print("\n=== MicrophoneConfig 테스트 ===")
    
    try:
        from src.models.microphone_models import MicrophoneConfig, MicrophoneStatus
        
        # 기본 설정 생성
        config = MicrophoneConfig()
        print("✅ MicrophoneConfig 기본 설정 생성 성공")
        print(f"  샘플링 레이트: {config.sample_rate}")
        print(f"  VAD 임계값: {config.vad_threshold}")
        print(f"  최대 무음 시간: {config.max_silence_duration_end}")
        
        # 커스텀 설정 생성
        custom_config = MicrophoneConfig(
            sample_rate=22050,
            vad_threshold=0.3,
            max_silence_duration_end=2.0
        )
        print("✅ MicrophoneConfig 커스텀 설정 생성 성공")
        print(f"  커스텀 샘플링 레이트: {custom_config.sample_rate}")
        print(f"  커스텀 VAD 임계값: {custom_config.vad_threshold}")
        
        # 상태 객체 생성
        status = MicrophoneStatus(
            is_listening=False,
            is_recording=False,
            current_volume_level=0.0,
            recording_duration=0.0,
            vad_status="waiting",
            last_speech_detected=None
        )
        print("✅ MicrophoneStatus 생성 성공")
        print(f"  초기 상태: {status.vad_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ MicrophoneConfig 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vad_processor_init():
    """VADProcessor 초기화 테스트"""
    print("\n=== VADProcessor 초기화 테스트 ===")
    
    try:
        from src.microphone.vad_processor import VADProcessor
        from src.models.microphone_models import MicrophoneConfig
        
        config = MicrophoneConfig()
        
        # VAD 프로세서 초기화 (실제 모델 로딩은 시간이 걸릴 수 있음)
        print("VAD 프로세서 초기화 중... (시간이 걸릴 수 있습니다)")
        processor = VADProcessor(config)
        print("✅ VADProcessor 초기화 성공")
        
        # 모델 준비 상태 확인
        is_ready = processor.is_model_ready()
        print(f"VAD 모델 준비 상태: {'✅ 준비됨' if is_ready else '❌ 준비 안됨'}")
        
        if is_ready:
            model_info = processor.get_model_info()
            print(f"모델 정보: {model_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ VADProcessor 테스트 실패: {e}")
        print("참고: VAD 모델 로딩에는 인터넷 연결과 시간이 필요합니다.")
        return False


def test_audio_recorder():
    """AudioRecorder 기본 기능 테스트"""
    print("\n=== AudioRecorder 테스트 ===")
    
    try:
        from src.microphone.audio_recorder import AudioRecorder
        from src.models.microphone_models import MicrophoneConfig
        
        config = MicrophoneConfig()
        recorder = AudioRecorder(config)
        print("✅ AudioRecorder 초기화 성공")
        
        # 녹음 정보 확인
        info = recorder.get_recording_info()
        print(f"녹음 정보: {info}")
        
        return True
        
    except Exception as e:
        print(f"❌ AudioRecorder 테스트 실패: {e}")
        return False


def test_imports():
    """필수 모듈 import 테스트"""
    print("\n=== 모듈 Import 테스트 ===")
    
    modules_to_test = [
        "src.testing.test_case_generator",
        "src.testing.test_runner", 
        "src.testing.test_case_manager",
        "src.testing.result_analyzer",
        "src.models.testing_models",
        "src.models.microphone_models",
        "src.microphone.vad_processor",
        "src.microphone.audio_recorder",
        "src.microphone.microphone_manager",
        "src.microphone.realtime_processor"
    ]
    
    success_count = 0
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}: {e}")
    
    print(f"\n모듈 Import 결과: {success_count}/{len(modules_to_test)} 성공")
    return success_count == len(modules_to_test)


def main():
    """모든 테스트 실행"""
    print("기본 기능 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("모듈 Import", test_imports),
        ("TestCaseGenerator", test_test_case_generator),
        ("MicrophoneConfig", test_microphone_config),
        ("AudioRecorder", test_audio_recorder),
        ("VADProcessor", test_vad_processor_init),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print(f"\n{test_name} 테스트가 사용자에 의해 중단되었습니다.")
            break
        except Exception as e:
            print(f"\n{test_name} 테스트 중 예상치 못한 오류: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약:")
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
        if result:
            success_count += 1
    
    total_tests = len(results)
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n전체 결과: {success_count}/{total_tests} 성공 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 대부분의 기본 기능이 정상적으로 작동합니다!")
    elif success_rate >= 60:
        print("⚠️ 일부 기능에 문제가 있을 수 있습니다.")
    else:
        print("❌ 여러 기능에 문제가 있습니다. 설정을 확인해주세요.")


if __name__ == "__main__":
    main()