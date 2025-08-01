"""
TTS 제공자 기본 인터페이스
다양한 TTS API를 교체 가능하게 하는 추상 클래스
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path


class BaseTTSProvider(ABC):
    """TTS 제공자 기본 인터페이스"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        TTS 제공자 초기화
        
        Args:
            config: 제공자별 설정 딕셔너리
        """
        self.config = config or {}
        self.is_initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        TTS 제공자 초기화
        
        Returns:
            초기화 성공 여부
        """
        pass
    
    @abstractmethod
    def text_to_speech(self, text: str, output_path: str, **kwargs) -> bool:
        """
        텍스트를 음성으로 변환하여 파일로 저장
        
        Args:
            text: 변환할 텍스트
            output_path: 출력 파일 경로
            **kwargs: 제공자별 추가 옵션
            
        Returns:
            변환 성공 여부
        """
        pass
    
    @abstractmethod
    def get_supported_voices(self) -> list:
        """
        지원하는 음성 목록 반환
        
        Returns:
            음성 목록
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """
        지원하는 오디오 형식 목록 반환
        
        Returns:
            오디오 형식 목록
        """
        pass
    
    def validate_text(self, text: str) -> bool:
        """
        텍스트 유효성 검증
        
        Args:
            text: 검증할 텍스트
            
        Returns:
            유효성 여부
        """
        if not text or not text.strip():
            return False
        
        # 기본 길이 제한 (제공자별로 오버라이드 가능)
        max_length = self.config.get('max_text_length', 4000)
        if len(text) > max_length:
            return False
        
        return True
    
    def cleanup(self):
        """리소스 정리"""
        pass
    
    @property
    def provider_name(self) -> str:
        """제공자 이름 반환"""
        return self.__class__.__name__


class TTSError(Exception):
    """TTS 관련 오류"""
    pass


class TTSInitializationError(TTSError):
    """TTS 초기화 오류"""
    pass


class TTSConversionError(TTSError):
    """TTS 변환 오류"""
    pass


class TTSConfigurationError(TTSError):
    """TTS 설정 오류"""
    pass