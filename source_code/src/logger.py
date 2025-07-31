"""
로깅 시스템 설정 모듈
시스템 전반의 로깅을 관리합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class LoggerManager:
    """로거 관리자 클래스"""
    
    def __init__(self):
        self.is_configured = False
        self.loggers = {}
    
    def setup_logger(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ):
        """로거 설정"""
        if self.is_configured:
            return
        
        # 로그 레벨 설정
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s',
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
            log_path = Path("logs")
            log_path.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(
                log_path / log_file,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        self.is_configured = True
        logging.info("로깅 시스템이 초기화되었습니다.")
    
    def get_logger(self, name: str = None):
        """로거 인스턴스 반환"""
        if not self.is_configured:
            self.setup_logger()
        
        if name is None:
            name = __name__
        
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        
        return self.loggers[name]


# 전역 로거 관리자 인스턴스
logger_manager = LoggerManager()

# 편의를 위한 함수들
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = "voice_kiosk.log"):
    """로깅 설정 편의 함수"""
    logger_manager.setup_logger(log_level=log_level, log_file=log_file)

def get_logger(name: str = None):
    """로거 인스턴스 반환 편의 함수"""
    return logger_manager.get_logger(name)