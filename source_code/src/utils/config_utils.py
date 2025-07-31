"""
설정 관리 유틸리티 함수들
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


def create_default_config_files(config_dir: str = "config"):
    """기본 설정 파일들을 생성합니다."""
    config_path = Path(config_dir)
    config_path.mkdir(exist_ok=True)
    
    # 기본 메뉴 설정 파일
    menu_config_file = config_path / "menu_config.json"
    if not menu_config_file.exists():
        default_menu_config = {
            "restaurant_info": {
                "name": "테스트 식당",
                "type": "fast_food",
                "language": "ko"
            },
            "categories": [
                "버거",
                "치킨",
                "사이드",
                "음료",
                "디저트"
            ],
            "menu_items": {
                "빅맥": {
                    "category": "버거",
                    "price": 6500,
                    "description": "빅맥 버거",
                    "available_options": ["단품", "세트", "라지세트"],
                    "set_drink_options": ["콜라", "사이다", "오렌지주스"],
                    "set_side_options": ["감자튀김", "치킨너겟"]
                },
                "콜라": {
                    "category": "음료",
                    "price": 2000,
                    "description": "코카콜라",
                    "available_options": ["미디움", "라지"],
                    "set_drink_options": [],
                    "set_side_options": []
                }
            },
            "set_pricing": {
                "세트": 2000,
                "라지세트": 3000
            },
            "option_pricing": {
                "라지": 500
            }
        }
        
        with open(menu_config_file, 'w', encoding='utf-8') as f:
            json.dump(default_menu_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"기본 메뉴 설정 파일을 생성했습니다: {menu_config_file}")


def create_env_file(env_file_path: str = ".env"):
    """기본 환경 변수 파일을 생성합니다."""
    env_path = Path(env_file_path)
    
    if not env_path.exists():
        default_env_content = """# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# TTS 설정
TTS_SERVICE=openai
TTS_VOICE=alloy
TTS_SPEED=1.0
TTS_ENGINE=default
TTS_PITCH=1.0
TTS_VOLUME=1.0
TTS_OUTPUT_FORMAT=wav
TTS_SAMPLE_RATE=22050

# Whisper 음성인식 설정
WHISPER_MODEL=base
WHISPER_LANGUAGE=ko
WHISPER_DEVICE=auto

# 음성 처리 설정
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024
AUDIO_CHANNELS=1
NOISE_REDUCTION_LEVEL=0.5
SPEAKER_SEPARATION_THRESHOLD=0.7
MAX_RECORDING_DURATION=30
SILENCE_THRESHOLD=0.01
NOISE_REDUCTION_ENABLED=true
SPEAKER_SEPARATION_ENABLED=true

# 마이크 입력 설정
MIC_SAMPLE_RATE=16000
MIC_FRAME_DURATION=0.5
MIC_MAX_SILENCE_START=5.0
MIC_MAX_SILENCE_END=3.0
MIC_MIN_RECORD_DURATION=1.0
MIC_VAD_THRESHOLD=0.2
MIC_OUTPUT_FILENAME=mic_input.wav
MIC_DEVICE_ID=
MIC_CHANNELS=1

# 테스트 시스템 설정
TEST_INCLUDE_SLANG=true
TEST_INCLUDE_INFORMAL=true
TEST_INCLUDE_COMPLEX=true
TEST_INCLUDE_EDGE_CASES=true
TEST_MAX_TESTS_PER_CATEGORY=50
TEST_OUTPUT_DIRECTORY=test_results
TEST_GENERATE_MARKDOWN=true
TEST_GENERATE_TEXT=true
TEST_TIMEOUT_SECONDS=30

# 시스템 설정
LOG_LEVEL=INFO
RESTAURANT_NAME=테스트 식당
RESTAURANT_TYPE=fast_food
LANGUAGE=ko
DEBUG_MODE=false

# 메뉴 설정
MENU_CURRENCY=KRW
MENU_TAX_RATE=0.1
MENU_SERVICE_CHARGE=0.0

# 성능 및 제한 설정
API_TIMEOUT=60.0
API_RETRY_COUNT=3
API_RETRY_DELAY=2.0
MEMORY_LIMIT_MB=1024
IO_BUFFER_SIZE=8192

# 보안 설정
SECURE_TEMP_DIRECTORY=true
FILE_PERMISSIONS=0o600
CLEANUP_ON_EXIT=true
VALIDATE_INPUT_PATHS=true

# 모니터링 설정
ENABLE_PERFORMANCE_MONITORING=true
PERFORMANCE_LOG_INTERVAL=60
TRACK_MEMORY_USAGE=true
TRACK_CPU_USAGE=true
ERROR_REPORTING=true
ERROR_THRESHOLD=10
"""
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(default_env_content)
        
        logger.info(f"기본 환경 변수 파일을 생성했습니다: {env_path}")


def load_env_file(env_file_path: str = ".env"):
    """환경 변수 파일을 로드합니다."""
    env_path = Path(env_file_path)
    
    if not env_path.exists():
        logger.warning(f"환경 변수 파일을 찾을 수 없습니다: {env_path}")
        return
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        logger.info(f"환경 변수 파일을 로드했습니다: {env_path}")
        
    except Exception as e:
        logger.error(f"환경 변수 파일 로드 중 오류: {e}")


def validate_api_key(api_key: str) -> bool:
    """API 키 유효성을 간단히 검증합니다."""
    if not api_key:
        return False
    
    if api_key == "your_openai_api_key_here":
        return False
    
    # OpenAI API 키 형식 검증 (sk-로 시작하고 적절한 길이)
    if api_key.startswith('sk-') and len(api_key) > 20:
        return True
    
    return False


def backup_config_file(file_path: str) -> Optional[str]:
    """설정 파일을 백업합니다."""
    try:
        source_path = Path(file_path)
        if not source_path.exists():
            logger.warning(f"백업할 파일이 존재하지 않습니다: {file_path}")
            return None
        
        backup_path = source_path.with_suffix(f"{source_path.suffix}.backup")
        
        import shutil
        shutil.copy2(source_path, backup_path)
        
        logger.info(f"설정 파일을 백업했습니다: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"설정 파일 백업 중 오류: {e}")
        return None


def restore_config_file(backup_path: str, target_path: str) -> bool:
    """백업된 설정 파일을 복원합니다."""
    try:
        backup_file = Path(backup_path)
        target_file = Path(target_path)
        
        if not backup_file.exists():
            logger.error(f"백업 파일이 존재하지 않습니다: {backup_path}")
            return False
        
        import shutil
        shutil.copy2(backup_file, target_file)
        
        logger.info(f"설정 파일을 복원했습니다: {target_path}")
        return True
        
    except Exception as e:
        logger.error(f"설정 파일 복원 중 오류: {e}")
        return False


def merge_config_dicts(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """두 설정 딕셔너리를 병합합니다."""
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_config_dicts(merged[key], value)
        else:
            merged[key] = value
    
    return merged


def get_config_file_info(file_path: str) -> Dict[str, Any]:
    """설정 파일의 정보를 반환합니다."""
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {
                'exists': False,
                'path': str(path),
                'size': 0,
                'modified': None,
                'readable': False,
                'writable': False
            }
        
        stat = path.stat()
        
        return {
            'exists': True,
            'path': str(path),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'readable': os.access(path, os.R_OK),
            'writable': os.access(path, os.W_OK)
        }
        
    except Exception as e:
        logger.error(f"설정 파일 정보 조회 중 오류: {e}")
        return {
            'exists': False,
            'path': file_path,
            'error': str(e)
        }


def validate_json_file(file_path: str) -> Dict[str, Any]:
    """JSON 파일의 유효성을 검증합니다."""
    try:
        path = Path(file_path)
        
        if not path.exists():
            return {
                'valid': False,
                'error': 'File does not exist',
                'path': str(path)
            }
        
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        
        return {
            'valid': True,
            'path': str(path)
        }
        
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': f'JSON parsing error: {e}',
            'path': file_path
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'File access error: {e}',
            'path': file_path
        }


def setup_initial_config():
    """초기 설정을 수행합니다."""
    logger.info("초기 설정을 시작합니다.")
    
    # 설정 디렉토리 생성
    create_default_config_files()
    
    # 환경 변수 파일 생성
    create_env_file()
    
    # 환경 변수 로드
    load_env_file()
    
    logger.info("초기 설정이 완료되었습니다.")


if __name__ == "__main__":
    # 스크립트로 실행될 때 초기 설정 수행
    setup_initial_config()