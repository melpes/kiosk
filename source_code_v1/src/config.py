"""
설정 관리 모듈
API 키, 메뉴 설정, 시스템 설정을 관리합니다.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from loguru import logger
import threading
from datetime import datetime


@dataclass
class OpenAIConfig:
    """OpenAI API 설정"""
    api_key: str
    model: str = "gpt-4o"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: float = 60.0
    retry_count: int = 3
    retry_delay: float = 2.0
    
    @classmethod
    def from_env(cls) -> 'OpenAIConfig':
        """환경 변수에서 OpenAI 설정 로드"""
        return cls(
            api_key=os.getenv('OPENAI_API_KEY', ''),
            model=os.getenv('OPENAI_MODEL', 'gpt-4o'),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', 1000)),
            temperature=float(os.getenv('OPENAI_TEMPERATURE', 0.7)),
            timeout=float(os.getenv('API_TIMEOUT', 60.0)),
            retry_count=int(os.getenv('API_RETRY_COUNT', 3)),
            retry_delay=float(os.getenv('API_RETRY_DELAY', 2.0))
        )


@dataclass
class TTSConfig:
    """TTS 설정"""
    service: str = "openai"
    voice: str = "alloy"
    speed: float = 1.0
    engine: str = "default"
    pitch: float = 1.0
    volume: float = 1.0
    output_format: str = "wav"
    sample_rate: int = 22050
    
    @classmethod
    def from_env(cls) -> 'TTSConfig':
        """환경 변수에서 TTS 설정 로드"""
        return cls(
            service=os.getenv('TTS_SERVICE', 'openai'),
            voice=os.getenv('TTS_VOICE', 'alloy'),
            speed=float(os.getenv('TTS_SPEED', 1.0)),
            engine=os.getenv('TTS_ENGINE', 'default'),
            pitch=float(os.getenv('TTS_PITCH', 1.0)),
            volume=float(os.getenv('TTS_VOLUME', 1.0)),
            output_format=os.getenv('TTS_OUTPUT_FORMAT', 'wav'),
            sample_rate=int(os.getenv('TTS_SAMPLE_RATE', 22050))
        )


@dataclass
class AudioConfig:
    """음성 처리 설정"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    noise_reduction_level: float = 0.5
    speaker_separation_threshold: float = 0.7
    whisper_model: str = "base"
    whisper_language: str = "ko"
    whisper_device: Optional[str] = None
    max_recording_duration: int = 30
    silence_threshold: float = 0.01
    noise_reduction_enabled: bool = True
    speaker_separation_enabled: bool = True
    
    @classmethod
    def from_env(cls) -> 'AudioConfig':
        """환경 변수에서 음성 설정 로드"""
        whisper_device = os.getenv('WHISPER_DEVICE')
        if whisper_device and whisper_device.lower() == 'auto':
            whisper_device = None
            
        return cls(
            sample_rate=int(os.getenv('AUDIO_SAMPLE_RATE', 16000)),
            chunk_size=int(os.getenv('AUDIO_CHUNK_SIZE', 1024)),
            channels=int(os.getenv('AUDIO_CHANNELS', 1)),
            noise_reduction_level=float(os.getenv('NOISE_REDUCTION_LEVEL', 0.5)),
            speaker_separation_threshold=float(os.getenv('SPEAKER_SEPARATION_THRESHOLD', 0.7)),
            whisper_model=os.getenv('WHISPER_MODEL', 'base'),
            whisper_language=os.getenv('WHISPER_LANGUAGE', 'ko'),
            whisper_device=whisper_device,
            max_recording_duration=int(os.getenv('MAX_RECORDING_DURATION', 30)),
            silence_threshold=float(os.getenv('SILENCE_THRESHOLD', 0.01)),
            noise_reduction_enabled=os.getenv('NOISE_REDUCTION_ENABLED', 'true').lower() == 'true',
            speaker_separation_enabled=os.getenv('SPEAKER_SEPARATION_ENABLED', 'true').lower() == 'true'
        )


@dataclass
class MenuItemConfig:
    """메뉴 아이템 설정"""
    category: str
    price: float
    description: str
    available_options: list
    set_drink_options: list
    set_side_options: list


@dataclass
class TestConfiguration:
    """테스트 설정"""
    include_slang: bool = True
    include_informal: bool = True
    include_complex: bool = True
    include_edge_cases: bool = True
    max_tests_per_category: int = 50
    output_directory: str = "test_results"
    generate_markdown: bool = True
    generate_text: bool = True
    timeout_seconds: int = 30
    
    @classmethod
    def from_env(cls) -> 'TestConfiguration':
        """환경 변수에서 테스트 설정 로드"""
        return cls(
            include_slang=os.getenv('TEST_INCLUDE_SLANG', 'true').lower() == 'true',
            include_informal=os.getenv('TEST_INCLUDE_INFORMAL', 'true').lower() == 'true',
            include_complex=os.getenv('TEST_INCLUDE_COMPLEX', 'true').lower() == 'true',
            include_edge_cases=os.getenv('TEST_INCLUDE_EDGE_CASES', 'true').lower() == 'true',
            max_tests_per_category=int(os.getenv('TEST_MAX_TESTS_PER_CATEGORY', 50)),
            output_directory=os.getenv('TEST_OUTPUT_DIRECTORY', 'test_results'),
            generate_markdown=os.getenv('TEST_GENERATE_MARKDOWN', 'true').lower() == 'true',
            generate_text=os.getenv('TEST_GENERATE_TEXT', 'true').lower() == 'true',
            timeout_seconds=int(os.getenv('TEST_TIMEOUT_SECONDS', 30))
        )


@dataclass
class MicrophoneConfig:
    """마이크 입력 설정"""
    sample_rate: int = 16000
    frame_duration: float = 0.5
    max_silence_duration_start: float = 5.0
    max_silence_duration_end: float = 3.0
    min_record_duration: float = 1.0
    vad_threshold: float = 0.2
    output_filename: str = "mic_input.wav"
    device_id: Optional[int] = None
    channels: int = 1
    
    @classmethod
    def from_env(cls) -> 'MicrophoneConfig':
        """환경 변수에서 마이크 설정 로드"""
        device_id_str = os.getenv('MIC_DEVICE_ID')
        device_id = None
        if device_id_str and device_id_str.strip():
            try:
                device_id = int(device_id_str)
            except ValueError:
                logger.warning(f"잘못된 MIC_DEVICE_ID 값: {device_id_str}")
                
        return cls(
            sample_rate=int(os.getenv('MIC_SAMPLE_RATE', 16000)),
            frame_duration=float(os.getenv('MIC_FRAME_DURATION', 0.5)),
            max_silence_duration_start=float(os.getenv('MIC_MAX_SILENCE_START', 5.0)),
            max_silence_duration_end=float(os.getenv('MIC_MAX_SILENCE_END', 3.0)),
            min_record_duration=float(os.getenv('MIC_MIN_RECORD_DURATION', 1.0)),
            vad_threshold=float(os.getenv('MIC_VAD_THRESHOLD', 0.2)),
            output_filename=os.getenv('MIC_OUTPUT_FILENAME', 'mic_input.wav'),
            device_id=device_id,
            channels=int(os.getenv('MIC_CHANNELS', 1))
        )


@dataclass
class MonitoringConfig:
    """모니터링 설정"""
    enable_performance_monitoring: bool = True
    performance_log_interval: int = 60
    track_memory_usage: bool = True
    track_cpu_usage: bool = True
    error_reporting: bool = True
    error_threshold: int = 10
    
    @classmethod
    def from_env(cls) -> 'MonitoringConfig':
        """환경 변수에서 모니터링 설정 로드"""
        return cls(
            enable_performance_monitoring=os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
            performance_log_interval=int(os.getenv('PERFORMANCE_LOG_INTERVAL', 60)),
            track_memory_usage=os.getenv('TRACK_MEMORY_USAGE', 'true').lower() == 'true',
            track_cpu_usage=os.getenv('TRACK_CPU_USAGE', 'true').lower() == 'true',
            error_reporting=os.getenv('ERROR_REPORTING', 'true').lower() == 'true',
            error_threshold=int(os.getenv('ERROR_THRESHOLD', 10))
        )


@dataclass
class SystemConfig:
    """시스템 설정"""
    log_level: str = "INFO"
    restaurant_name: str = "테스트 식당"
    restaurant_type: str = "fast_food"
    language: str = "ko"
    debug_mode: bool = False
    memory_limit_mb: int = 1024
    io_buffer_size: int = 8192
    secure_temp_directory: bool = True
    file_permissions: int = 0o600
    cleanup_on_exit: bool = True
    validate_input_paths: bool = True
    
    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """환경 변수에서 시스템 설정 로드"""
        return cls(
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            restaurant_name=os.getenv('RESTAURANT_NAME', '테스트 식당'),
            restaurant_type=os.getenv('RESTAURANT_TYPE', 'fast_food'),
            language=os.getenv('LANGUAGE', 'ko'),
            debug_mode=os.getenv('DEBUG_MODE', 'false').lower() == 'true',
            memory_limit_mb=int(os.getenv('MEMORY_LIMIT_MB', 1024)),
            io_buffer_size=int(os.getenv('IO_BUFFER_SIZE', 8192)),
            secure_temp_directory=os.getenv('SECURE_TEMP_DIRECTORY', 'true').lower() == 'true',
            file_permissions=int(os.getenv('FILE_PERMISSIONS', '0o600'), 8),
            cleanup_on_exit=os.getenv('CLEANUP_ON_EXIT', 'true').lower() == 'true',
            validate_input_paths=os.getenv('VALIDATE_INPUT_PATHS', 'true').lower() == 'true'
        )


@dataclass
class MenuConfig:
    """메뉴 설정"""
    restaurant_info: Dict[str, Any]
    categories: List[str]
    menu_items: Dict[str, MenuItemConfig]
    set_pricing: Dict[str, float]
    option_pricing: Dict[str, float]
    currency: str = "KRW"
    tax_rate: float = 0.1
    service_charge: float = 0.0
    last_modified: Optional[datetime] = None
    
    @classmethod
    def from_env_and_file(cls, config_file_path: str) -> 'MenuConfig':
        """환경 변수와 파일에서 메뉴 설정 로드"""
        # 파일에서 기본 메뉴 정보 로드
        config_path = Path(config_file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"메뉴 설정 파일을 찾을 수 없습니다: {config_file_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 메뉴 아이템을 MenuItemConfig 객체로 변환
        menu_items = {}
        for item_name, item_data in config_data.get('menu_items', {}).items():
            try:
                menu_items[item_name] = MenuItemConfig(**item_data)
            except TypeError as e:
                logger.error(f"메뉴 아이템 '{item_name}' 설정 오류: {e}")
                continue
        
        # 환경 변수에서 추가 설정 로드
        return cls(
            restaurant_info=config_data.get('restaurant_info', {}),
            categories=config_data.get('categories', []),
            menu_items=menu_items,
            set_pricing=config_data.get('set_pricing', {}),
            option_pricing=config_data.get('option_pricing', {}),
            currency=os.getenv('MENU_CURRENCY', 'KRW'),
            tax_rate=float(os.getenv('MENU_TAX_RATE', 0.1)),
            service_charge=float(os.getenv('MENU_SERVICE_CHARGE', 0.0)),
            last_modified=datetime.fromtimestamp(config_path.stat().st_mtime)
        )
    
    def validate(self) -> bool:
        """메뉴 설정 유효성 검증"""
        if not self.menu_items:
            logger.error("메뉴 아이템이 비어있습니다.")
            return False
        
        if not self.categories:
            logger.error("메뉴 카테고리가 비어있습니다.")
            return False
        
        # 메뉴 아이템의 카테고리가 유효한지 확인
        for item_name, item_config in self.menu_items.items():
            if item_config.category not in self.categories:
                logger.error(f"메뉴 아이템 '{item_name}'의 카테고리 '{item_config.category}'가 유효하지 않습니다.")
                return False
        
        return True


class ConfigManager:
    """설정 관리자 클래스"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._api_config = None
        self._menu_config = None
        self._audio_config = None
        self._system_config = None
        self._tts_config = None
        self._test_config = None
        self._microphone_config = None
        self._monitoring_config = None
        self._menu_file_mtime = None
        self._lock = threading.Lock()  # 스레드 안전성을 위한 락
        
    def load_api_config(self, force_reload: bool = False) -> OpenAIConfig:
        """API 설정 로드 (환경 변수만 사용)"""
        with self._lock:
            if self._api_config is None or force_reload:
                self._api_config = OpenAIConfig.from_env()
                
                # API 키 검증
                if not self._api_config.api_key or self._api_config.api_key == "your_openai_api_key_here":
                    logger.warning("OpenAI API 키가 설정되지 않았습니다. .env 파일에서 OPENAI_API_KEY를 설정하세요.")
                
                logger.info("API 설정을 성공적으로 로드했습니다.")
        
        return self._api_config
    
    def load_menu_config(self, force_reload: bool = False) -> MenuConfig:
        """메뉴 설정 동적 로딩"""
        with self._lock:
            config_path = self.config_dir / "menu_config.json"
            
            if not config_path.exists():
                logger.error(f"메뉴 설정 파일을 찾을 수 없습니다: {config_path}")
                raise FileNotFoundError(f"메뉴 설정 파일을 찾을 수 없습니다: {config_path}")
            
            # 파일 수정 시간 확인하여 동적 로딩
            current_mtime = config_path.stat().st_mtime
            
            if (self._menu_config is None or 
                force_reload or 
                self._menu_file_mtime is None or 
                current_mtime > self._menu_file_mtime):
                
                try:
                    self._menu_config = MenuConfig.from_env_and_file(str(config_path))
                    self._menu_file_mtime = current_mtime
                    
                    # 메뉴 설정 유효성 검증
                    if not self._menu_config.validate():
                        logger.error("메뉴 설정 유효성 검증 실패")
                        raise ValueError("메뉴 설정이 유효하지 않습니다.")
                    
                    logger.info(f"메뉴 설정을 성공적으로 로드했습니다. 총 {len(self._menu_config.menu_items)}개 메뉴 아이템")
                    
                except Exception as e:
                    logger.error(f"메뉴 설정 로드 중 오류 발생: {e}")
                    raise
            else:
                logger.debug("메뉴 설정 파일이 변경되지 않아 캐시된 설정을 사용합니다.")
        
        return self._menu_config
    
    def get_audio_config(self) -> AudioConfig:
        """음성 처리 설정 반환"""
        if self._audio_config is None:
            self._audio_config = AudioConfig.from_env()
        return self._audio_config
    
    def get_system_config(self) -> SystemConfig:
        """시스템 설정 반환"""
        if self._system_config is None:
            self._system_config = SystemConfig.from_env()
        return self._system_config
    
    def get_tts_config(self) -> TTSConfig:
        """TTS 설정 반환 (환경 변수만 사용)"""
        if self._tts_config is None:
            self._tts_config = TTSConfig.from_env()
        
        return self._tts_config
    
    def get_test_config(self) -> TestConfiguration:
        """테스트 설정 반환"""
        if self._test_config is None:
            self._test_config = TestConfiguration.from_env()
        return self._test_config
    
    def get_microphone_config(self) -> MicrophoneConfig:
        """마이크 설정 반환"""
        if self._microphone_config is None:
            self._microphone_config = MicrophoneConfig.from_env()
        return self._microphone_config
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """모니터링 설정 반환"""
        if self._monitoring_config is None:
            self._monitoring_config = MonitoringConfig.from_env()
        return self._monitoring_config
    
    def validate_config(self) -> Dict[str, bool]:
        """설정 유효성 검증"""
        validation_results = {
            'api_config': False,
            'menu_config': False,
            'audio_config': False,
            'system_config': False,
            'tts_config': False,
            'test_config': False,
            'microphone_config': False,
            'monitoring_config': False
        }
        
        try:
            # API 설정 검증
            api_config = self.load_api_config()
            if api_config.api_key and api_config.api_key != "your_openai_api_key_here":
                validation_results['api_config'] = True
                logger.info("API 설정이 유효합니다.")
            else:
                logger.error("유효한 OpenAI API 키가 설정되지 않았습니다.")
            
        except Exception as e:
            logger.error(f"API 설정 검증 중 오류: {e}")
        
        try:
            # 메뉴 설정 검증
            menu_config = self.load_menu_config()
            validation_results['menu_config'] = menu_config.validate()
            
        except Exception as e:
            logger.error(f"메뉴 설정 검증 중 오류: {e}")
        
        try:
            # 음성 설정 검증
            audio_config = self.get_audio_config()
            if (audio_config.sample_rate > 0 and 
                audio_config.chunk_size > 0 and 
                0 <= audio_config.noise_reduction_level <= 1 and
                0 <= audio_config.speaker_separation_threshold <= 1):
                validation_results['audio_config'] = True
                logger.info("음성 설정이 유효합니다.")
            else:
                logger.error("음성 설정 값이 유효하지 않습니다.")
                
        except Exception as e:
            logger.error(f"음성 설정 검증 중 오류: {e}")
        
        try:
            # 시스템 설정 검증
            system_config = self.get_system_config()
            if (system_config.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR'] and
                system_config.restaurant_name and
                system_config.restaurant_type and
                system_config.language):
                validation_results['system_config'] = True
                logger.info("시스템 설정이 유효합니다.")
            else:
                logger.error("시스템 설정 값이 유효하지 않습니다.")
                
        except Exception as e:
            logger.error(f"시스템 설정 검증 중 오류: {e}")
        
        try:
            # TTS 설정 검증
            tts_config = self.get_tts_config()
            if (tts_config.service and 
                tts_config.voice and 
                tts_config.speed > 0):
                validation_results['tts_config'] = True
                logger.info("TTS 설정이 유효합니다.")
            else:
                logger.error("TTS 설정 값이 유효하지 않습니다.")
                
        except Exception as e:
            logger.error(f"TTS 설정 검증 중 오류: {e}")
        
        try:
            # 테스트 설정 검증
            test_config = self.get_test_config()
            if (test_config.max_tests_per_category > 0 and
                test_config.timeout_seconds > 0 and
                test_config.output_directory):
                validation_results['test_config'] = True
                logger.info("테스트 설정이 유효합니다.")
            else:
                logger.error("테스트 설정 값이 유효하지 않습니다.")
                
        except Exception as e:
            logger.error(f"테스트 설정 검증 중 오류: {e}")
        
        try:
            # 마이크 설정 검증
            mic_config = self.get_microphone_config()
            if (mic_config.sample_rate > 0 and
                mic_config.frame_duration > 0 and
                mic_config.max_silence_duration_start > 0 and
                mic_config.max_silence_duration_end > 0 and
                mic_config.min_record_duration > 0 and
                0 <= mic_config.vad_threshold <= 1 and
                mic_config.channels > 0):
                validation_results['microphone_config'] = True
                logger.info("마이크 설정이 유효합니다.")
            else:
                logger.error("마이크 설정 값이 유효하지 않습니다.")
                
        except Exception as e:
            logger.error(f"마이크 설정 검증 중 오류: {e}")
        
        try:
            # 모니터링 설정 검증
            monitoring_config = self.get_monitoring_config()
            if (monitoring_config.performance_log_interval > 0 and
                monitoring_config.error_threshold > 0):
                validation_results['monitoring_config'] = True
                logger.info("모니터링 설정이 유효합니다.")
            else:
                logger.error("모니터링 설정 값이 유효하지 않습니다.")
                
        except Exception as e:
            logger.error(f"모니터링 설정 검증 중 오류: {e}")
        
        all_valid = all(validation_results.values())
        if all_valid:
            logger.info("모든 설정이 유효합니다.")
        else:
            logger.warning(f"일부 설정이 유효하지 않습니다: {validation_results}")
        
        return validation_results
    
    def reload_all_configs(self):
        """모든 설정을 다시 로드"""
        logger.info("모든 설정을 다시 로드합니다.")
        self._api_config = None
        self._menu_config = None
        self._audio_config = None
        self._system_config = None
        self._tts_config = None
        self._test_config = None
        self._microphone_config = None
        self._monitoring_config = None
        self._menu_file_mtime = None
    
    def get_config_summary(self) -> Dict[str, Any]:
        """설정 요약 정보 반환"""
        try:
            api_config = self.load_api_config()
            menu_config = self.load_menu_config()
            audio_config = self.get_audio_config()
            system_config = self.get_system_config()
            tts_config = self.get_tts_config()
            test_config = self.get_test_config()
            mic_config = self.get_microphone_config()
            monitoring_config = self.get_monitoring_config()
            
            return {
                'api': {
                    'model': api_config.model,
                    'max_tokens': api_config.max_tokens,
                    'temperature': api_config.temperature,
                    'timeout': api_config.timeout,
                    'retry_count': api_config.retry_count,
                    'api_key_set': bool(api_config.api_key and api_config.api_key != "your_openai_api_key_here")
                },
                'menu': {
                    'restaurant_name': menu_config.restaurant_info.get('name', 'Unknown'),
                    'restaurant_type': menu_config.restaurant_info.get('type', 'Unknown'),
                    'menu_items_count': len(menu_config.menu_items),
                    'categories_count': len(menu_config.categories),
                    'currency': menu_config.currency,
                    'tax_rate': menu_config.tax_rate,
                    'last_modified': menu_config.last_modified.isoformat() if menu_config.last_modified else None
                },
                'audio': {
                    'sample_rate': audio_config.sample_rate,
                    'chunk_size': audio_config.chunk_size,
                    'channels': audio_config.channels,
                    'noise_reduction_level': audio_config.noise_reduction_level,
                    'speaker_separation_threshold': audio_config.speaker_separation_threshold,
                    'whisper_model': audio_config.whisper_model,
                    'max_recording_duration': audio_config.max_recording_duration
                },
                'system': {
                    'log_level': system_config.log_level,
                    'restaurant_name': system_config.restaurant_name,
                    'restaurant_type': system_config.restaurant_type,
                    'language': system_config.language,
                    'debug_mode': system_config.debug_mode,
                    'memory_limit_mb': system_config.memory_limit_mb
                },
                'tts': {
                    'service': tts_config.service,
                    'voice': tts_config.voice,
                    'speed': tts_config.speed,
                    'engine': tts_config.engine,
                    'pitch': tts_config.pitch,
                    'volume': tts_config.volume,
                    'sample_rate': tts_config.sample_rate
                },
                'test': {
                    'include_slang': test_config.include_slang,
                    'include_informal': test_config.include_informal,
                    'include_complex': test_config.include_complex,
                    'include_edge_cases': test_config.include_edge_cases,
                    'max_tests_per_category': test_config.max_tests_per_category,
                    'output_directory': test_config.output_directory,
                    'timeout_seconds': test_config.timeout_seconds
                },
                'microphone': {
                    'sample_rate': mic_config.sample_rate,
                    'frame_duration': mic_config.frame_duration,
                    'max_silence_duration_start': mic_config.max_silence_duration_start,
                    'max_silence_duration_end': mic_config.max_silence_duration_end,
                    'min_record_duration': mic_config.min_record_duration,
                    'vad_threshold': mic_config.vad_threshold,
                    'device_id': mic_config.device_id,
                    'channels': mic_config.channels
                },
                'monitoring': {
                    'enable_performance_monitoring': monitoring_config.enable_performance_monitoring,
                    'performance_log_interval': monitoring_config.performance_log_interval,
                    'track_memory_usage': monitoring_config.track_memory_usage,
                    'track_cpu_usage': monitoring_config.track_cpu_usage,
                    'error_reporting': monitoring_config.error_reporting,
                    'error_threshold': monitoring_config.error_threshold
                }
            }
        except Exception as e:
            logger.error(f"설정 요약 생성 중 오류: {e}")
            return {}


# 전역 설정 관리자 인스턴스
config_manager = ConfigManager()


def load_config() -> Dict[str, Any]:
    """
    환경 변수에서 설정을 로드하여 딕셔너리로 반환
    
    Returns:
        설정 딕셔너리
    """
    try:
        # ConfigManager를 사용하여 모든 설정 로드
        manager = ConfigManager()
        return manager.get_config_summary()
        
    except Exception as e:
        logger.error(f"설정 로드 중 오류 발생: {e}")
        return {}