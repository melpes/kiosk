"""
pytest 설정 파일
테스트 전반에 사용되는 fixture와 설정을 정의합니다.
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import ConfigManager
from src.logger import setup_logging


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """테스트 환경 설정"""
    # 테스트용 로깅 설정 (로그 레벨을 WARNING으로 설정하여 테스트 출력 최소화)
    setup_logging(log_level="WARNING", log_file=None)


@pytest.fixture
def config_manager():
    """설정 관리자 fixture"""
    return ConfigManager()


@pytest.fixture
def sample_menu_config():
    """테스트용 메뉴 설정"""
    return {
        "restaurant_info": {
            "name": "테스트 식당",
            "type": "fast_food",
            "language": "ko"
        },
        "categories": ["버거", "음료"],
        "menu_items": {
            "테스트버거": {
                "category": "버거",
                "price": 5000,
                "description": "테스트용 버거",
                "available_options": ["단품", "세트"],
                "set_drink_options": ["콜라"],
                "set_side_options": ["감자튀김"]
            }
        },
        "set_pricing": {"세트": 2000},
        "option_pricing": {}
    }


@pytest.fixture
def sample_api_config():
    """테스트용 API 설정"""
    return {
        "openai": {
            "api_key": "test_api_key",
            "model": "gpt-4o",
            "max_tokens": 1000,
            "temperature": 0.7
        }
    }