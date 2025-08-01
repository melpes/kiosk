"""
클라이언트 설정 관리자
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from utils.logger import get_logger


@dataclass
class ServerConfig:
    """서버 설정"""
    url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60


@dataclass
class AudioConfig:
    """오디오 설정"""
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_formats: list = field(default_factory=lambda: [".wav"])
    temp_dir: str = "temp_audio"
    auto_cleanup: bool = True
    cleanup_interval: int = 3600  # 1시간
    delete_after_upload: bool = False  # 업로드 후 파일 삭제 여부 (기본값: 보관)


@dataclass
class UIConfig:
    """UI 설정"""
    auto_play_tts: bool = True
    show_detailed_logs: bool = False
    language: str = "ko"
    theme: str = "default"
    font_size: int = 12


@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    file: str = "client.log"
    max_size: int = 1024 * 1024  # 1MB
    backup_count: int = 3
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class SessionConfig:
    """세션 설정"""
    auto_generate_id: bool = True
    session_timeout: int = 1800  # 30분
    keep_alive_interval: int = 300  # 5분


@dataclass
class PerformanceConfig:
    """성능 설정"""
    connection_pool_size: int = 10
    request_timeout: int = 30
    download_timeout: int = 60
    upload_chunk_size: int = 8192


@dataclass
class ClientConfig:
    """전체 클라이언트 설정"""
    server: ServerConfig = field(default_factory=ServerConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "server": {
                "url": self.server.url,
                "timeout": self.server.timeout,
                "max_retries": self.server.max_retries,
                "retry_delay": self.server.retry_delay,
                "health_check_interval": self.server.health_check_interval
            },
            "audio": {
                "max_file_size": self.audio.max_file_size,
                "supported_formats": self.audio.supported_formats,
                "temp_dir": self.audio.temp_dir,
                "auto_cleanup": self.audio.auto_cleanup,
                "cleanup_interval": self.audio.cleanup_interval,
                "delete_after_upload": self.audio.delete_after_upload
            },
            "ui": {
                "auto_play_tts": self.ui.auto_play_tts,
                "show_detailed_logs": self.ui.show_detailed_logs,
                "language": self.ui.language,
                "theme": self.ui.theme,
                "font_size": self.ui.font_size
            },
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "max_size": self.logging.max_size,
                "backup_count": self.logging.backup_count,
                "format": self.logging.format
            },
            "session": {
                "auto_generate_id": self.session.auto_generate_id,
                "session_timeout": self.session.session_timeout,
                "keep_alive_interval": self.session.keep_alive_interval
            },
            "performance": {
                "connection_pool_size": self.performance.connection_pool_size,
                "request_timeout": self.performance.request_timeout,
                "download_timeout": self.performance.download_timeout,
                "upload_chunk_size": self.performance.upload_chunk_size
            }
        }


class ConfigManager:
    """설정 관리자"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.ConfigManager")
    
    @staticmethod
    def load_config(config_path: str) -> ClientConfig:
        """
        설정 파일에서 설정 로드
        
        Args:
            config_path: 설정 파일 경로
            
        Returns:
            ClientConfig: 로드된 설정
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger = get_logger(f"{__name__}.ConfigManager")
            logger.warning(f"설정 파일을 찾을 수 없습니다: {config_path}")
            logger.info("기본 설정을 사용합니다.")
            return ClientConfig()
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 설정 객체 생성
            config = ClientConfig()
            
            # 서버 설정
            if 'server' in config_data:
                server_data = config_data['server']
                config.server = ServerConfig(
                    url=server_data.get('url', config.server.url),
                    timeout=server_data.get('timeout', config.server.timeout),
                    max_retries=server_data.get('max_retries', config.server.max_retries),
                    retry_delay=server_data.get('retry_delay', config.server.retry_delay),
                    health_check_interval=server_data.get('health_check_interval', config.server.health_check_interval)
                )
            
            # 오디오 설정
            if 'audio' in config_data:
                audio_data = config_data['audio']
                config.audio = AudioConfig(
                    max_file_size=audio_data.get('max_file_size', config.audio.max_file_size),
                    supported_formats=audio_data.get('supported_formats', config.audio.supported_formats),
                    temp_dir=audio_data.get('temp_dir', config.audio.temp_dir),
                    auto_cleanup=audio_data.get('auto_cleanup', config.audio.auto_cleanup),
                    cleanup_interval=audio_data.get('cleanup_interval', config.audio.cleanup_interval),
                    delete_after_upload=audio_data.get('delete_after_upload', config.audio.delete_after_upload)
                )
            
            # UI 설정
            if 'ui' in config_data:
                ui_data = config_data['ui']
                config.ui = UIConfig(
                    auto_play_tts=ui_data.get('auto_play_tts', config.ui.auto_play_tts),
                    show_detailed_logs=ui_data.get('show_detailed_logs', config.ui.show_detailed_logs),
                    language=ui_data.get('language', config.ui.language),
                    theme=ui_data.get('theme', config.ui.theme),
                    font_size=ui_data.get('font_size', config.ui.font_size)
                )
            
            # 로깅 설정
            if 'logging' in config_data:
                logging_data = config_data['logging']
                config.logging = LoggingConfig(
                    level=logging_data.get('level', config.logging.level),
                    file=logging_data.get('file', config.logging.file),
                    max_size=logging_data.get('max_size', config.logging.max_size),
                    backup_count=logging_data.get('backup_count', config.logging.backup_count),
                    format=logging_data.get('format', config.logging.format)
                )
            
            # 세션 설정
            if 'session' in config_data:
                session_data = config_data['session']
                config.session = SessionConfig(
                    auto_generate_id=session_data.get('auto_generate_id', config.session.auto_generate_id),
                    session_timeout=session_data.get('session_timeout', config.session.session_timeout),
                    keep_alive_interval=session_data.get('keep_alive_interval', config.session.keep_alive_interval)
                )
            
            # 성능 설정
            if 'performance' in config_data:
                performance_data = config_data['performance']
                config.performance = PerformanceConfig(
                    connection_pool_size=performance_data.get('connection_pool_size', config.performance.connection_pool_size),
                    request_timeout=performance_data.get('request_timeout', config.performance.request_timeout),
                    download_timeout=performance_data.get('download_timeout', config.performance.download_timeout),
                    upload_chunk_size=performance_data.get('upload_chunk_size', config.performance.upload_chunk_size)
                )
            
            logger = get_logger(f"{__name__}.ConfigManager")
            logger.info(f"설정 파일 로드 완료: {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            logger = get_logger(f"{__name__}.ConfigManager")
            logger.error(f"설정 파일 JSON 형식 오류: {e}")
            logger.info("기본 설정을 사용합니다.")
            return ClientConfig()
        except Exception as e:
            logger = get_logger(f"{__name__}.ConfigManager")
            logger.error(f"설정 파일 로드 실패: {e}")
            logger.info("기본 설정을 사용합니다.")
            return ClientConfig()
    
    @staticmethod
    def save_config(config: ClientConfig, config_path: str) -> bool:
        """
        설정을 파일에 저장
        
        Args:
            config: 저장할 설정
            config_path: 설정 파일 경로
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger = get_logger(f"{__name__}.ConfigManager")
            logger.info(f"설정 파일 저장 완료: {config_path}")
            return True
            
        except Exception as e:
            logger = get_logger(f"{__name__}.ConfigManager")
            logger.error(f"설정 파일 저장 실패: {e}")
            return False
    
    @staticmethod
    def validate_config(config: ClientConfig) -> tuple[bool, list[str]]:
        """
        설정 유효성 검증
        
        Args:
            config: 검증할 설정
            
        Returns:
            tuple[bool, list[str]]: (유효성, 오류 메시지 목록)
        """
        errors = []
        
        # 서버 URL 검증
        if not config.server.url:
            errors.append("서버 URL이 설정되지 않았습니다.")
        elif not config.server.url.startswith(('http://', 'https://')):
            errors.append("서버 URL은 http:// 또는 https://로 시작해야 합니다.")
        
        # 타임아웃 값 검증
        if config.server.timeout <= 0:
            errors.append("서버 타임아웃은 0보다 커야 합니다.")
        
        # 재시도 횟수 검증
        if config.server.max_retries < 0:
            errors.append("최대 재시도 횟수는 0 이상이어야 합니다.")
        
        # 파일 크기 검증
        if config.audio.max_file_size <= 0:
            errors.append("최대 파일 크기는 0보다 커야 합니다.")
        
        # 지원 형식 검증
        if not config.audio.supported_formats:
            errors.append("지원하는 오디오 형식이 설정되지 않았습니다.")
        
        # 로그 레벨 검증
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if config.logging.level not in valid_log_levels:
            errors.append(f"로그 레벨은 {valid_log_levels} 중 하나여야 합니다.")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_default_config_path() -> str:
        """기본 설정 파일 경로 반환"""
        return str(Path(__file__).parent.parent / "config.json")
    
    @staticmethod
    def create_sample_config(config_path: str) -> bool:
        """
        샘플 설정 파일 생성
        
        Args:
            config_path: 생성할 설정 파일 경로
            
        Returns:
            bool: 생성 성공 여부
        """
        sample_config = ClientConfig()
        return ConfigManager.save_config(sample_config, config_path)