"""
설정 관리 시스템 테스트
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from datetime import datetime

from src.config import (
    ConfigManager, 
    OpenAIConfig, 
    MenuConfig, 
    AudioConfig, 
    SystemConfig, 
    TTSConfig,
    MenuItemConfig
)


class TestConfigManager:
    """ConfigManager 테스트"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """임시 설정 디렉토리 생성"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            yield config_dir
    
    @pytest.fixture
    def sample_api_config(self):
        """샘플 API 설정"""
        return {
            "openai": {
                "api_key": "test_api_key",
                "model": "gpt-4o",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "tts": {
                "service": "openai",
                "voice": "alloy",
                "speed": 1.0
            }
        }
    
    @pytest.fixture
    def sample_menu_config(self):
        """샘플 메뉴 설정"""
        return {
            "restaurant_info": {
                "name": "테스트 식당",
                "type": "fast_food",
                "language": "ko"
            },
            "categories": ["버거", "음료"],
            "menu_items": {
                "빅맥": {
                    "category": "버거",
                    "price": 6500,
                    "description": "빅맥 버거",
                    "available_options": ["단품", "세트"],
                    "set_drink_options": ["콜라"],
                    "set_side_options": ["감자튀김"]
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
            "set_pricing": {"세트": 2000},
            "option_pricing": {"라지": 500}
        }
    
    def test_load_api_config_from_file(self, temp_config_dir, sample_api_config):
        """파일에서 API 설정 로드 테스트"""
        # API 설정 파일 생성
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        api_config = config_manager.load_api_config()
        
        assert api_config.api_key == "test_api_key"
        assert api_config.model == "gpt-4o"
        assert api_config.max_tokens == 1000
        assert api_config.temperature == 0.7
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'env_api_key',
        'OPENAI_MODEL': 'gpt-3.5-turbo',
        'OPENAI_MAX_TOKENS': '500',
        'OPENAI_TEMPERATURE': '0.5'
    })
    def test_load_api_config_from_env(self, temp_config_dir, sample_api_config):
        """환경 변수에서 API 설정 로드 테스트 (환경 변수 우선)"""
        # API 설정 파일 생성
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        api_config = config_manager.load_api_config()
        
        # 환경 변수 값이 우선되어야 함
        assert api_config.api_key == "env_api_key"
        assert api_config.model == "gpt-3.5-turbo"
        assert api_config.max_tokens == 500
        assert api_config.temperature == 0.5
    
    def test_load_menu_config(self, temp_config_dir, sample_menu_config):
        """메뉴 설정 로드 테스트"""
        # 메뉴 설정 파일 생성
        menu_file = temp_config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        menu_config = config_manager.load_menu_config()
        
        assert menu_config.restaurant_info["name"] == "테스트 식당"
        assert len(menu_config.categories) == 2
        assert len(menu_config.menu_items) == 2
        assert "빅맥" in menu_config.menu_items
        assert menu_config.menu_items["빅맥"].price == 6500
    
    def test_menu_config_dynamic_loading(self, temp_config_dir, sample_menu_config):
        """메뉴 설정 동적 로딩 테스트"""
        menu_file = temp_config_dir / "menu_config.json"
        
        # 초기 메뉴 설정 파일 생성
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 첫 번째 로드
        menu_config1 = config_manager.load_menu_config()
        assert len(menu_config1.menu_items) == 2
        
        # 메뉴 설정 수정
        sample_menu_config["menu_items"]["새로운메뉴"] = {
            "category": "버거",
            "price": 7000,
            "description": "새로운 버거",
            "available_options": ["단품"],
            "set_drink_options": [],
            "set_side_options": []
        }
        
        # 파일 수정 시간을 변경하기 위해 잠시 대기
        import time
        time.sleep(0.1)
        
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        # 두 번째 로드 (동적 로딩)
        menu_config2 = config_manager.load_menu_config()
        assert len(menu_config2.menu_items) == 3
        assert "새로운메뉴" in menu_config2.menu_items
    
    @patch.dict(os.environ, {
        'AUDIO_SAMPLE_RATE': '22050',
        'AUDIO_CHUNK_SIZE': '2048',
        'NOISE_REDUCTION_LEVEL': '0.8',
        'SPEAKER_SEPARATION_THRESHOLD': '0.9'
    })
    def test_get_audio_config_from_env(self, temp_config_dir):
        """환경 변수에서 음성 설정 로드 테스트"""
        config_manager = ConfigManager(str(temp_config_dir))
        audio_config = config_manager.get_audio_config()
        
        assert audio_config.sample_rate == 22050
        assert audio_config.chunk_size == 2048
        assert audio_config.noise_reduction_level == 0.8
        assert audio_config.speaker_separation_threshold == 0.9
    
    @patch.dict(os.environ, {
        'LOG_LEVEL': 'DEBUG',
        'RESTAURANT_NAME': '환경변수 식당',
        'RESTAURANT_TYPE': 'casual_dining',
        'LANGUAGE': 'en'
    })
    def test_get_system_config_from_env(self, temp_config_dir):
        """환경 변수에서 시스템 설정 로드 테스트"""
        config_manager = ConfigManager(str(temp_config_dir))
        system_config = config_manager.get_system_config()
        
        assert system_config.log_level == 'DEBUG'
        assert system_config.restaurant_name == '환경변수 식당'
        assert system_config.restaurant_type == 'casual_dining'
        assert system_config.language == 'en'
    
    def test_get_tts_config(self, temp_config_dir, sample_api_config):
        """TTS 설정 로드 테스트"""
        # API 설정 파일 생성
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        tts_config = config_manager.get_tts_config()
        
        assert tts_config.service == "openai"
        assert tts_config.voice == "alloy"
        assert tts_config.speed == 1.0
    
    def test_validate_config(self, temp_config_dir, sample_api_config, sample_menu_config):
        """설정 유효성 검증 테스트"""
        # 설정 파일들 생성
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        menu_file = temp_config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        validation_results = config_manager.validate_config()
        
        assert validation_results['api_config'] is True
        assert validation_results['menu_config'] is True
        assert validation_results['audio_config'] is True
        assert validation_results['system_config'] is True
        assert validation_results['tts_config'] is True
    
    def test_validate_config_invalid_api_key(self, temp_config_dir, sample_api_config, sample_menu_config):
        """유효하지 않은 API 키 검증 테스트"""
        # 유효하지 않은 API 키 설정
        sample_api_config["openai"]["api_key"] = "your_openai_api_key_here"
        
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        menu_file = temp_config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        validation_results = config_manager.validate_config()
        
        assert validation_results['api_config'] is False
        assert validation_results['menu_config'] is True
    
    def test_validate_config_invalid_menu(self, temp_config_dir, sample_api_config):
        """유효하지 않은 메뉴 설정 검증 테스트"""
        # 유효하지 않은 메뉴 설정 (카테고리에 없는 메뉴 아이템)
        invalid_menu_config = {
            "restaurant_info": {"name": "테스트 식당"},
            "categories": ["버거"],
            "menu_items": {
                "콜라": {
                    "category": "음료",  # categories에 없는 카테고리
                    "price": 2000,
                    "description": "코카콜라",
                    "available_options": ["미디움"],
                    "set_drink_options": [],
                    "set_side_options": []
                }
            },
            "set_pricing": {},
            "option_pricing": {}
        }
        
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        menu_file = temp_config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        validation_results = config_manager.validate_config()
        
        assert validation_results['menu_config'] is False
    
    def test_reload_all_configs(self, temp_config_dir, sample_api_config, sample_menu_config):
        """모든 설정 다시 로드 테스트"""
        # 설정 파일들 생성
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        menu_file = temp_config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        
        # 초기 로드
        api_config1 = config_manager.load_api_config()
        menu_config1 = config_manager.load_menu_config()
        
        # 설정 변경
        sample_api_config["openai"]["model"] = "gpt-3.5-turbo"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        # 다시 로드
        config_manager.reload_all_configs()
        api_config2 = config_manager.load_api_config()
        
        assert api_config2.model == "gpt-3.5-turbo"
    
    def test_get_config_summary(self, temp_config_dir, sample_api_config, sample_menu_config):
        """설정 요약 정보 테스트"""
        # 설정 파일들 생성
        api_file = temp_config_dir / "api_keys.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(sample_api_config, f)
        
        menu_file = temp_config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(sample_menu_config, f)
        
        config_manager = ConfigManager(str(temp_config_dir))
        summary = config_manager.get_config_summary()
        
        assert 'api' in summary
        assert 'menu' in summary
        assert 'audio' in summary
        assert 'system' in summary
        assert 'tts' in summary
        
        assert summary['api']['model'] == 'gpt-4o'
        assert summary['api']['api_key_set'] is True
        assert summary['menu']['menu_items_count'] == 2
        assert summary['menu']['categories_count'] == 2


class TestDataClasses:
    """데이터 클래스 테스트"""
    
    def test_audio_config_from_env(self):
        """AudioConfig 환경 변수 로드 테스트"""
        with patch.dict(os.environ, {
            'AUDIO_SAMPLE_RATE': '22050',
            'AUDIO_CHUNK_SIZE': '2048'
        }):
            config = AudioConfig.from_env()
            assert config.sample_rate == 22050
            assert config.chunk_size == 2048
    
    def test_system_config_from_env(self):
        """SystemConfig 환경 변수 로드 테스트"""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'RESTAURANT_NAME': '테스트 식당'
        }):
            config = SystemConfig.from_env()
            assert config.log_level == 'DEBUG'
            assert config.restaurant_name == '테스트 식당'
    
    def test_menu_config_validate_valid(self):
        """유효한 메뉴 설정 검증 테스트"""
        menu_items = {
            "빅맥": MenuItemConfig(
                category="버거",
                price=6500,
                description="빅맥 버거",
                available_options=["단품"],
                set_drink_options=[],
                set_side_options=[]
            )
        }
        
        config = MenuConfig(
            restaurant_info={"name": "테스트 식당"},
            categories=["버거"],
            menu_items=menu_items,
            set_pricing={},
            option_pricing={}
        )
        
        assert config.validate() is True
    
    def test_menu_config_validate_invalid_category(self):
        """유효하지 않은 카테고리 메뉴 설정 검증 테스트"""
        menu_items = {
            "콜라": MenuItemConfig(
                category="음료",  # categories에 없는 카테고리
                price=2000,
                description="코카콜라",
                available_options=["미디움"],
                set_drink_options=[],
                set_side_options=[]
            )
        }
        
        config = MenuConfig(
            restaurant_info={"name": "테스트 식당"},
            categories=["버거"],  # "음료" 카테고리가 없음
            menu_items=menu_items,
            set_pricing={},
            option_pricing={}
        )
        
        assert config.validate() is False
    
    def test_menu_config_validate_empty_items(self):
        """빈 메뉴 아이템 검증 테스트"""
        config = MenuConfig(
            restaurant_info={"name": "테스트 식당"},
            categories=["버거"],
            menu_items={},  # 빈 메뉴 아이템
            set_pricing={},
            option_pricing={}
        )
        
        assert config.validate() is False
    
    def test_menu_config_validate_empty_categories(self):
        """빈 카테고리 검증 테스트"""
        menu_items = {
            "빅맥": MenuItemConfig(
                category="버거",
                price=6500,
                description="빅맥 버거",
                available_options=["단품"],
                set_drink_options=[],
                set_side_options=[]
            )
        }
        
        config = MenuConfig(
            restaurant_info={"name": "테스트 식당"},
            categories=[],  # 빈 카테고리
            menu_items=menu_items,
            set_pricing={},
            option_pricing={}
        )
        
        assert config.validate() is False