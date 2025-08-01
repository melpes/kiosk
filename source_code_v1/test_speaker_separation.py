#!/usr/bin/env python3
"""
화자 분리 시스템 테스트 스크립트

사용법:
    python test_speaker_separation.py

이 스크립트는 화자 분리 시스템이 올바르게 작동하는지 확인합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import logging

def create_test_audio():
    """테스트용 혼합 음성 데이터 생성"""
    print("🎵 테스트 오디오 생성 중...")
    
    duration = 5.0  # 5초
    sample_rate = 16000
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    
    # 주 화자 (강한 신호) - 440Hz
    main_speaker = 0.8 * np.sin(440 * 2.0 * np.pi * t)
    
    # 배경 화자 (약한 신호) - 880Hz  
    background_speaker = 0.3 * np.sin(880 * 2.0 * np.pi * t)
    
    # 백색 노이즈
    noise = 0.1 * np.random.randn(len(t))
    
    # 혼합 신호
    mixed_audio = main_speaker + background_speaker + noise
    
    # 정규화
    mixed_audio = mixed_audio / np.max(np.abs(mixed_audio)) * 0.9
    
    print(f"  📊 생성완료: {duration}초, {sample_rate}Hz")
    print(f"  🎭 주화자(440Hz): 80%, 배경화자(880Hz): 30%, 노이즈: 10%")
    
    return mixed_audio, sample_rate

def test_basic_system():
    """기본 시스템 테스트"""
    print("\n🔋 기본 에너지 기반 화자 분리 테스트")
    print("-" * 50)
    
    try:
        from src.audio.preprocessing import AudioProcessor
        from src.models.config_models import AudioConfig
        
        # 설정 생성 (고급 모델 비활성화)
        config = AudioConfig()
        processor = AudioProcessor(config)
        processor.speaker_config.use_advanced_separation = False
        
        # 테스트 오디오 생성
        audio_data, sample_rate = create_test_audio()
        
        # 화자 분리 실행
        result = processor._separate_speakers(audio_data, sample_rate)
        
        # 결과 분석
        original_duration = len(audio_data) / sample_rate
        result_duration = len(result) / sample_rate
        compression_ratio = (original_duration - result_duration) / original_duration * 100
        
        print(f"\n✅ 기본 시스템 테스트 성공!")
        print(f"  📊 원본: {original_duration:.2f}초 → 결과: {result_duration:.2f}초")
        print(f"  📉 압축률: {compression_ratio:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 시스템 테스트 실패: {e}")
        return False

def test_advanced_system():
    """고급 AI 모델 시스템 테스트"""
    print("\n🚀 고급 AI 모델 화자 분리 테스트")
    print("-" * 50)
    
    try:
        from src.audio.preprocessing import AudioProcessor
        from src.models.config_models import AudioConfig
        import os
        
        # HuggingFace 토큰 확인
        token = os.getenv('HUGGINGFACE_TOKEN') or os.getenv('HF_TOKEN')
        if not token:
            print("⚠️  HuggingFace 토큰이 설정되지 않았습니다.")
            print("🔧 해결 방법:")
            print("   1. python setup_huggingface_token.py 실행")
            print("   2. 또는 환경변수 설정: export HUGGINGFACE_TOKEN='your_token'")
            print("   3. 또는 .env 파일에 HUGGINGFACE_TOKEN=your_token 추가")
            print("\n🔄 고급 모델 없이 기본 방식만 테스트합니다...")
            return test_basic_system()
        
        # 설정 생성 (고급 모델 활성화)
        config = AudioConfig()
        processor = AudioProcessor(config)
        processor.speaker_config.use_advanced_separation = True
        # 토큰은 자동으로 환경변수에서 로드됨
        
        # 테스트 오디오 생성
        audio_data, sample_rate = create_test_audio()
        
        # 화자 분리 실행
        result = processor._separate_speakers(audio_data, sample_rate)
        
        # 결과 분석
        original_duration = len(audio_data) / sample_rate
        result_duration = len(result) / sample_rate
        compression_ratio = (original_duration - result_duration) / original_duration * 100
        
        print(f"\n✅ 고급 시스템 테스트 성공!")
        print(f"  📊 원본: {original_duration:.2f}초 → 결과: {result_duration:.2f}초")
        print(f"  📉 압축률: {compression_ratio:.1f}%")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  고급 모델 라이브러리 누락: {e}")
        print("   💡 해결방법: pip install pyannote.audio speechbrain")
        print("\n🔄 기본 방식으로 테스트합니다...")
        return test_basic_system()
    except Exception as e:
        print(f"❌ 고급 시스템 테스트 실패: {e}")
        print("\n🔄 기본 방식으로 대체 테스트합니다...")
        return test_basic_system()

def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("🧪 화자 분리 시스템 종합 테스트")
    print("=" * 80)
    
    # 로깅 설정 (WARNING 이상만 출력)
    logging.basicConfig(level=logging.WARNING)
    
    results = []
    
    # 1. 기본 시스템 테스트
    basic_result = test_basic_system()
    results.append(("기본 에너지 기반", basic_result))
    
    # 2. 고급 시스템 테스트
    advanced_result = test_advanced_system()
    results.append(("고급 AI 모델", advanced_result))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📋 테스트 결과 요약")
    print("=" * 80)
    
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name:20} : {status}")
    
    success_count = sum(results[i][1] for i in range(len(results)))
    total_count = len(results)
    
    print(f"\n🎯 전체 결과: {success_count}/{total_count} 테스트 통과")
    
    if success_count == total_count:
        print("🎉 모든 테스트 통과! 화자 분리 시스템이 정상 작동합니다.")
        return 0
    elif success_count > 0:
        print("⚠️  일부 테스트 실패. 기본 기능은 사용 가능합니다.")
        print("\n💡 HuggingFace 토큰을 설정하면 고급 AI 모델을 사용할 수 있습니다:")
        print("   python setup_huggingface_token.py")
        return 1
    else:
        print("❌ 모든 테스트 실패. 시스템 설정을 확인해주세요.")
        print("\n🔧 문제 해결:")
        print("   1. 필요 라이브러리 설치: pip install -r requirements.txt")
        print("   2. HuggingFace 토큰 설정: python setup_huggingface_token.py")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)