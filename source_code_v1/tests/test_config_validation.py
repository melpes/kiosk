#!/usr/bin/env python3
"""
설정 시스템 검증 테스트 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import ConfigManager, TestConfiguration, MicrophoneConfig
from src.logger import setup_logging, get_logger

def test_config_validation():
    """설정 검증 테스트"""
    setup_logging()
    logger = get_logger("config_test")
    
    logger.info("=== 설정 시스템 검증 테스트 시작 ===")
    
    # ConfigManager 인스턴스 생성
    config_manager = ConfigManager()
    
    try:
        # 1. 테스트 설정 로드 및 검증
        logger.info("1. 테스트 설정 검증")
        test_config = config_manager.get_test_config()
        logger.info(f"테스트 설정: {test_config}")
        
        # 2. 마이크 설정 로드 및 검증
        logger.info("2. 마이크 설정 검증")
        mic_config = config_manager.get_microphone_config()
        logger.info(f"마이크 설정: {mic_config}")
        
        # 3. 전체 설정 검증
        logger.info("3. 전체 설정 검증")
        validation_results = config_manager.validate_config()
        logger.info(f"검증 결과: {validation_results}")
        
        # 4. 설정 요약 정보
        logger.info("4. 설정 요약 정보")
        config_summary = config_manager.get_config_summary()
        
        for category, settings in config_summary.items():
            logger.info(f"{category.upper()} 설정:")
            for key, value in settings.items():
                logger.info(f"  {key}: {value}")
        
        # 5. 환경 변수 기반 설정 테스트
        logger.info("5. 환경 변수 기반 설정 테스트")
        
        # 임시로 환경 변수 설정
        os.environ['TEST_MAX_TESTS_PER_CATEGORY'] = '100'
        os.environ['MIC_VAD_THRESHOLD'] = '0.3'
        
        # 설정 다시 로드
        config_manager.reload_all_configs()
        
        new_test_config = config_manager.get_test_config()
        new_mic_config = config_manager.get_microphone_config()
        
        logger.info(f"업데이트된 테스트 설정 - max_tests_per_category: {new_test_config.max_tests_per_category}")
        logger.info(f"업데이트된 마이크 설정 - vad_threshold: {new_mic_config.vad_threshold}")
        
        # 환경 변수 정리
        del os.environ['TEST_MAX_TESTS_PER_CATEGORY']
        del os.environ['MIC_VAD_THRESHOLD']
        
        logger.info("=== 설정 시스템 검증 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"설정 검증 테스트 중 오류 발생: {e}")
        return False

def test_individual_configs():
    """개별 설정 클래스 테스트"""
    setup_logging()
    logger = get_logger("individual_config_test")
    
    logger.info("=== 개별 설정 클래스 테스트 시작 ===")
    
    try:
        # TestConfiguration 테스트
        logger.info("1. TestConfiguration 테스트")
        test_config = TestConfiguration.from_env()
        logger.info(f"기본 테스트 설정: {test_config}")
        
        # 환경 변수 설정 후 테스트
        os.environ['TEST_INCLUDE_SLANG'] = 'false'
        os.environ['TEST_MAX_TESTS_PER_CATEGORY'] = '25'
        
        test_config_env = TestConfiguration.from_env()
        logger.info(f"환경 변수 기반 테스트 설정: {test_config_env}")
        
        # MicrophoneConfig 테스트
        logger.info("2. MicrophoneConfig 테스트")
        mic_config = MicrophoneConfig.from_env()
        logger.info(f"기본 마이크 설정: {mic_config}")
        
        # 환경 변수 설정 후 테스트
        os.environ['MIC_SAMPLE_RATE'] = '22050'
        os.environ['MIC_DEVICE_ID'] = '1'
        
        mic_config_env = MicrophoneConfig.from_env()
        logger.info(f"환경 변수 기반 마이크 설정: {mic_config_env}")
        
        # 환경 변수 정리
        for key in ['TEST_INCLUDE_SLANG', 'TEST_MAX_TESTS_PER_CATEGORY', 
                   'MIC_SAMPLE_RATE', 'MIC_DEVICE_ID']:
            if key in os.environ:
                del os.environ[key]
        
        logger.info("=== 개별 설정 클래스 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"개별 설정 테스트 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    success = True
    
    # 개별 설정 클래스 테스트
    if not test_individual_configs():
        success = False
    
    # 전체 설정 검증 테스트
    if not test_config_validation():
        success = False
    
    if success:
        print("\n✅ 모든 설정 테스트가 성공적으로 완료되었습니다!")
        sys.exit(0)
    else:
        print("\n❌ 일부 설정 테스트가 실패했습니다.")
        sys.exit(1)