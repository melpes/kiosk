#!/usr/bin/env python3
"""
환경변수 기반 설정 시스템 테스트 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_loading():
    """환경변수 로딩 테스트"""
    print("=== 환경변수 로딩 테스트 ===")
    
    # .env 파일 로드
    from src.utils.env_loader import ensure_env_loaded
    ensure_env_loaded()
    
    # 주요 환경변수들 확인
    env_vars_to_check = [
        'OPENAI_API_KEY',
        'OPENAI_MODEL',
        'TTS_SERVICE',
        'AUDIO_SAMPLE_RATE',
        'MIC_VAD_THRESHOLD',
        'TEST_MAX_TESTS_PER_CATEGORY',
        'LOG_LEVEL',
        'RESTAURANT_NAME'
    ]
    
    for var in env_vars_to_check:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {value}")
    
    return True

def test_config_classes():
    """설정 클래스들 테스트"""
    print("\n=== 설정 클래스 테스트 ===")
    
    try:
        from src.config import (
            OpenAIConfig, TTSConfig, AudioConfig, 
            MicrophoneConfig, TestConfiguration, 
            SystemConfig, MonitoringConfig
        )
        
        # OpenAI 설정 테스트
        print("1. OpenAI 설정 테스트")
        openai_config = OpenAIConfig.from_env()
        print(f"  모델: {openai_config.model}")
        print(f"  최대 토큰: {openai_config.max_tokens}")
        print(f"  온도: {openai_config.temperature}")
        print(f"  타임아웃: {openai_config.timeout}")
        
        # TTS 설정 테스트
        print("\n2. TTS 설정 테스트")
        tts_config = TTSConfig.from_env()
        print(f"  서비스: {tts_config.service}")
        print(f"  음성: {tts_config.voice}")
        print(f"  속도: {tts_config.speed}")
        print(f"  엔진: {tts_config.engine}")
        print(f"  샘플레이트: {tts_config.sample_rate}")
        
        # 오디오 설정 테스트
        print("\n3. 오디오 설정 테스트")
        audio_config = AudioConfig.from_env()
        print(f"  샘플레이트: {audio_config.sample_rate}")
        print(f"  청크 크기: {audio_config.chunk_size}")
        print(f"  채널: {audio_config.channels}")
        print(f"  노이즈 감소 레벨: {audio_config.noise_reduction_level}")
        print(f"  Whisper 모델: {audio_config.whisper_model}")
        
        # 마이크 설정 테스트
        print("\n4. 마이크 설정 테스트")
        mic_config = MicrophoneConfig.from_env()
        print(f"  샘플레이트: {mic_config.sample_rate}")
        print(f"  프레임 지속시간: {mic_config.frame_duration}")
        print(f"  VAD 임계값: {mic_config.vad_threshold}")
        print(f"  최대 무음 시작: {mic_config.max_silence_duration_start}")
        
        # 테스트 설정 테스트
        print("\n5. 테스트 설정 테스트")
        test_config = TestConfiguration.from_env()
        print(f"  은어 포함: {test_config.include_slang}")
        print(f"  반말 포함: {test_config.include_informal}")
        print(f"  최대 테스트 수: {test_config.max_tests_per_category}")
        print(f"  타임아웃: {test_config.timeout_seconds}")
        
        # 시스템 설정 테스트
        print("\n6. 시스템 설정 테스트")
        system_config = SystemConfig.from_env()
        print(f"  로그 레벨: {system_config.log_level}")
        print(f"  식당 이름: {system_config.restaurant_name}")
        print(f"  디버그 모드: {system_config.debug_mode}")
        print(f"  메모리 제한: {system_config.memory_limit_mb}MB")
        
        # 모니터링 설정 테스트
        print("\n7. 모니터링 설정 테스트")
        monitoring_config = MonitoringConfig.from_env()
        print(f"  성능 모니터링: {monitoring_config.enable_performance_monitoring}")
        print(f"  로그 간격: {monitoring_config.performance_log_interval}초")
        print(f"  메모리 추적: {monitoring_config.track_memory_usage}")
        print(f"  오류 임계값: {monitoring_config.error_threshold}")
        
        print("\n✅ 모든 설정 클래스 테스트 성공")
        return True
        
    except Exception as e:
        print(f"\n❌ 설정 클래스 테스트 실패: {e}")
        return False

def test_config_manager():
    """ConfigManager 테스트"""
    print("\n=== ConfigManager 테스트 ===")
    
    try:
        from src.config import ConfigManager
        
        # ConfigManager 인스턴스 생성
        config_manager = ConfigManager()
        
        # API 설정 로드
        print("1. API 설정 로드")
        api_config = config_manager.load_api_config()
        print(f"  API 키 설정됨: {bool(api_config.api_key and api_config.api_key != 'your_openai_api_key_here')}")
        
        # 메뉴 설정 로드
        print("\n2. 메뉴 설정 로드")
        try:
            menu_config = config_manager.load_menu_config()
            print(f"  메뉴 아이템 수: {len(menu_config.menu_items)}")
            print(f"  카테고리 수: {len(menu_config.categories)}")
            print(f"  통화: {menu_config.currency}")
            print(f"  세율: {menu_config.tax_rate}")
        except FileNotFoundError:
            print("  ⚠️ 메뉴 설정 파일을 찾을 수 없습니다")
        
        # 설정 검증
        print("\n3. 설정 검증")
        validation_results = config_manager.validate_config()
        for config_type, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            print(f"  {status} {config_type}: {'유효' if is_valid else '무효'}")
        
        # 설정 요약
        print("\n4. 설정 요약")
        config_summary = config_manager.get_config_summary()
        print(f"  API 모델: {config_summary.get('api', {}).get('model', 'N/A')}")
        print(f"  TTS 서비스: {config_summary.get('tts', {}).get('service', 'N/A')}")
        print(f"  오디오 샘플레이트: {config_summary.get('audio', {}).get('sample_rate', 'N/A')}")
        print(f"  시스템 언어: {config_summary.get('system', {}).get('language', 'N/A')}")
        
        print("\n✅ ConfigManager 테스트 성공")
        return True
        
    except Exception as e:
        print(f"\n❌ ConfigManager 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_env_override():
    """환경변수 오버라이드 테스트"""
    print("\n=== 환경변수 오버라이드 테스트 ===")
    
    try:
        from src.config import AudioConfig
        
        # 기본값 확인
        print("1. 기본값 확인")
        default_config = AudioConfig.from_env()
        print(f"  기본 샘플레이트: {default_config.sample_rate}")
        
        # 환경변수 변경
        print("\n2. 환경변수 변경 테스트")
        original_value = os.getenv('AUDIO_SAMPLE_RATE')
        os.environ['AUDIO_SAMPLE_RATE'] = '22050'
        
        modified_config = AudioConfig.from_env()
        print(f"  변경된 샘플레이트: {modified_config.sample_rate}")
        
        # 원래 값 복원
        if original_value:
            os.environ['AUDIO_SAMPLE_RATE'] = original_value
        else:
            del os.environ['AUDIO_SAMPLE_RATE']
        
        # 복원 확인
        restored_config = AudioConfig.from_env()
        print(f"  복원된 샘플레이트: {restored_config.sample_rate}")
        
        print("\n✅ 환경변수 오버라이드 테스트 성공")
        return True
        
    except Exception as e:
        print(f"\n❌ 환경변수 오버라이드 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🔧 환경변수 기반 설정 시스템 테스트 시작\n")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(("환경변수 로딩", test_env_loading()))
    test_results.append(("설정 클래스", test_config_classes()))
    test_results.append(("ConfigManager", test_config_manager()))
    test_results.append(("환경변수 오버라이드", test_env_override()))
    
    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 설정을 확인해주세요.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)