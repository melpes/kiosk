"""
클라이언트 로깅 시스템
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


class ClientLoggerManager:
    """클라이언트 로거 관리자"""
    
    def __init__(self):
        self.is_configured = False
        self.loggers = {}
    
    def setup_logger(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        max_size: int = 1024 * 1024,  # 1MB
        backup_count: int = 3,
        log_format: str = None
    ):
        """로거 설정"""
        if self.is_configured:
            return
        
        # 로그 레벨 설정
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # 포맷터 설정
        if log_format is None:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(
            log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 루트 로거 설정
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 기존 핸들러 제거
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 파일 핸들러 추가 (선택적)
        if log_file:
            # 로그 디렉토리 생성
            log_path = Path(log_file).parent
            if log_path != Path('.'):
                log_path.mkdir(parents=True, exist_ok=True)
            
            # 회전 파일 핸들러 사용
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        self.is_configured = True
        logging.info("클라이언트 로깅 시스템이 초기화되었습니다.")
    
    def get_logger(self, name: str = None):
        """로거 인스턴스 반환"""
        if not self.is_configured:
            self.setup_logger()
        
        if name is None:
            name = __name__
        
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        
        return self.loggers[name]
    
    def set_level(self, level: str):
        """로그 레벨 변경"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
    
    def add_file_handler(self, log_file: str, max_size: int = 1024 * 1024, backup_count: int = 3):
        """파일 핸들러 추가"""
        root_logger = logging.getLogger()
        
        # 로그 디렉토리 생성
        log_path = Path(log_file).parent
        if log_path != Path('.'):
            log_path.mkdir(parents=True, exist_ok=True)
        
        # 회전 파일 핸들러 생성
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
        logging.info(f"파일 핸들러 추가: {log_file}")


# 전역 로거 관리자 인스턴스
logger_manager = ClientLoggerManager()


def setup_logging(
    log_level: str = "INFO", 
    log_file: Optional[str] = "client.log",
    max_size: int = 1024 * 1024,
    backup_count: int = 3,
    log_format: str = None
):
    """로깅 설정 편의 함수"""
    logger_manager.setup_logger(
        log_level=log_level,
        log_file=log_file,
        max_size=max_size,
        backup_count=backup_count,
        log_format=log_format
    )


def get_logger(name: str = None):
    """로거 인스턴스 반환 편의 함수"""
    return logger_manager.get_logger(name)


def set_log_level(level: str):
    """로그 레벨 변경 편의 함수"""
    logger_manager.set_level(level)


def add_file_handler(log_file: str, max_size: int = 1024 * 1024, backup_count: int = 3):
    """파일 핸들러 추가 편의 함수"""
    logger_manager.add_file_handler(log_file, max_size, backup_count)