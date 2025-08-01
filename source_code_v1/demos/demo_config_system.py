#!/usr/bin/env python3
"""
확장된 설정 시스템 데모 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import ConfigManager
from src.logger import setup_logging, get_logger

def demo_config_system():
    """설정 시스템 데모"""
    setup_logging()
    logger = get_logger("config_demo")
    
    logger.info("=== 확장된 설정 시스템 데모 ===")
    
    # ConfigManager 인스턴스 생성
    config_manager = ConfigManager()
    
    # 1. 테스트 설정 데모
    logger.info("1. 테스트 설정")
    test_config = config_manager.get_test_config()
    logger.info(f"  - 은어 테스트 포함: {test_config.include_slang}")
    logger.info(f"  - 반말 테스트 포함: {test_config.include_informal}")
    logger.info(f"  - 복합 의도 테스트 포함: {test_config.include_complex}")
    logger.info(f"  - 카테고리별 최대 테스트 수: {test_config.max_tests_per_category}")
    logger.info(f"  - 출력 디렉토리: {test_config.output_directory}")
    logger.info(f"  - 타임아웃: {test_config.timeout_seconds}초")
    
    # 2. 마이크 설정 데모
    logger.info("2. 마이크 설정")
    mic_config = config_manager.get_microphone_config()
    logger.info(f"  - 샘플링 레이트: {mic_config.sample_rate}Hz")
    logger.info(f"  - 프레임 지속시간: {mic_config.frame_duration}초")
    logger.info(f"  - 최대 무음 시간 (시작): {mic_config.max_silence_duration_start}초")
    logger.info(f"  - 최대 무음 시간 (종료): {mic_config.max_silence_duration_end}초")
    logger.info(f"  - 최소 녹음 시간: {mic_config.min_record_duration}초")
    logger.info(f"  - VAD 임계값: {mic_config.vad_threshold}")
    logger.info(f"  - 출력 파일명: {mic_config.output_filename}")
    logger.info(f"  - 마이크 장치 ID: {mic_config.device_id}")
    logger.info(f"  - 채널 수: {mic_config.channels}")
    
    # 3. 환경 변수 기반 설정 변경 데모
    logger.info("3. 환경 변수 기반 설정 변경 데모")
    
    # 환경 변수 설정
    os.environ['TEST_MAX_TESTS_PER_CATEGORY'] = '75'
    os.environ['MIC_VAD_THRESHOLD'] = '0.25'
    os.environ['TEST_INCLUDE_SLANG'] = 'false'
    
    # 설정 다시 로드
    config_manager.reload_all_configs()
    
    # 변경된 설정 확인
    updated_test_config = config_manager.get_test_config()
    updated_mic_config = config_manager.get_microphone_config()
    
    logger.info(f"  - 업데이트된 최대 테스트 수: {updated_test_config.max_tests_per_category}")
    logger.info(f"  - 업데이트된 VAD 임계값: {updated_mic_config.vad_threshold}")
    logger.info(f"  - 업데이트된 은어 테스트 포함: {updated_test_config.include_slang}")
    
    # 4. 전체 설정 검증
    logger.info("4. 전체 설정 검증")
    validation_results = config_manager.validate_config()
    
    for config_type, is_valid in validation_results.items():
        status = "✅ 유효" if is_valid else "❌ 무효"
        logger.info(f"  - {config_type}: {status}")
    
    # 5. 설정 요약
    logger.info("5. 설정 요약")
    config_summary = config_manager.get_config_summary()
    
    logger.info(f"  - API 키 설정됨: {config_summary['api']['api_key_set']}")
    logger.info(f"  - 메뉴 아이템 수: {config_summary['menu']['menu_items_count']}")
    logger.info(f"  - 테스트 출력 디렉토리: {config_summary['test']['output_directory']}")
    logger.info(f"  - 마이크 샘플링 레이트: {config_summary['microphone']['sample_rate']}Hz")
    
    # 환경 변수 정리
    for key in ['TEST_MAX_TESTS_PER_CATEGORY', 'MIC_VAD_THRESHOLD', 'TEST_INCLUDE_SLANG']:
        if key in os.environ:
            del os.environ[key]
    
    logger.info("=== 설정 시스템 데모 완료 ===")

if __name__ == "__main__":
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()
    
    demo_config_system()