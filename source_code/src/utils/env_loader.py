"""
환경 변수 로더 유틸리티
"""

import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """
    환경 변수 파일을 로드하여 os.environ에 설정
    
    Args:
        env_path: .env 파일 경로
        
    Returns:
        로드된 환경 변수 딕셔너리
    """
    loaded_vars = {}
    env_file = Path(env_path)
    
    if not env_file.exists():
        # 프로젝트 루트에서 .env 파일 찾기
        current_dir = Path(__file__).parent
        while current_dir.parent != current_dir:  # 루트 디렉토리까지
            env_candidate = current_dir / ".env"
            if env_candidate.exists():
                env_file = env_candidate
                break
            current_dir = current_dir.parent
    
    if not env_file.exists():
        return loaded_vars
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 따옴표 제거
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    os.environ[key] = value
                    loaded_vars[key] = value
    except Exception as e:
        print(f"환경 변수 파일 로드 중 오류: {e}")
    
    return loaded_vars


def ensure_env_loaded() -> bool:
    """
    환경 변수가 로드되었는지 확인하고, 필요시 로드
    
    Returns:
        로드 성공 여부
    """
    # .env 파일 로드 시도
    loaded_vars = load_env_file()
    
    # 로드 성공 확인 (API 키 기준)
    api_key = os.getenv('OPENAI_API_KEY')
    return bool(api_key and api_key != 'your_openai_api_key_here')


def get_api_key() -> Optional[str]:
    """
    OpenAI API 키 반환
    
    Returns:
        API 키 또는 None
    """
    ensure_env_loaded()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your_openai_api_key_here':
        return None
    
    return api_key


def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    API 키 유효성 검증
    
    Args:
        api_key: 검증할 API 키 (None인 경우 환경 변수에서 가져옴)
        
    Returns:
        유효성 여부
    """
    if api_key is None:
        api_key = get_api_key()
    
    if not api_key:
        return False
    
    if api_key == 'your_openai_api_key_here':
        return False
    
    if not api_key.startswith('sk-'):
        return False
    
    return True


def get_test_config() -> Dict[str, any]:
    """
    테스트 관련 설정을 환경 변수에서 가져옴
    
    Returns:
        테스트 설정 딕셔너리
    """
    # 환경 변수 다시 로드
    load_env_file()
    
    return {
        'max_tests_per_category': int(os.getenv('TEST_MAX_TESTS_PER_CATEGORY', '20')),
        'delay_between_requests': float(os.getenv('TEST_DELAY_BETWEEN_REQUESTS', '2.0')),
        'include_slang': os.getenv('TEST_INCLUDE_SLANG', 'true').lower() == 'true',
        'include_informal': os.getenv('TEST_INCLUDE_INFORMAL', 'true').lower() == 'true',
        'include_complex': os.getenv('TEST_INCLUDE_COMPLEX', 'true').lower() == 'true',
        'include_edge_cases': os.getenv('TEST_INCLUDE_EDGE_CASES', 'true').lower() == 'true',
    }


# 모듈 import 시 자동으로 환경 변수 로드
ensure_env_loaded()