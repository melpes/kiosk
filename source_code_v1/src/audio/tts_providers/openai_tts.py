"""
OpenAI TTS API 제공자 구현
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path

from openai import OpenAI

from .base_tts import BaseTTSProvider, TTSInitializationError, TTSConversionError, TTSConfigurationError
from ...logger import get_logger


class OpenAITTSProvider(BaseTTSProvider):
    """OpenAI TTS API 제공자"""
    
    # OpenAI TTS에서 지원하는 음성 목록
    SUPPORTED_VOICES = [
        "alloy",    # 중성적이고 균형잡힌 음성
        "echo",     # 남성적인 음성
        "fable",    # 영국식 남성 음성
        "onyx",     # 깊고 남성적인 음성
        "nova",     # 젊고 활기찬 여성 음성
        "shimmer"   # 부드럽고 여성적인 음성
    ]
    
    # 지원하는 오디오 형식
    SUPPORTED_FORMATS = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
    
    # 지원하는 모델
    SUPPORTED_MODELS = ["tts-1", "tts-1-hd"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        OpenAI TTS 제공자 초기화
        
        Args:
            config: 설정 딕셔너리
                - api_key: OpenAI API 키
                - model: 사용할 모델 (기본: tts-1)
                - voice: 사용할 음성 (기본: alloy)
                - speed: 음성 속도 (0.25-4.0, 기본: 1.0)
                - response_format: 응답 형식 (기본: wav)
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.client: Optional[OpenAI] = None
        
        # 기본 설정
        self.api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.model = self.config.get('model', 'tts-1')
        self.voice = self.config.get('voice', 'alloy')
        self.speed = self.config.get('speed', 1.0)
        self.response_format = self.config.get('response_format', 'wav')
        
        # 설정 검증
        self._validate_config()
    
    def _validate_config(self):
        """설정 유효성 검증"""
        if not self.api_key:
            raise TTSConfigurationError("OpenAI API 키가 설정되지 않았습니다")
        
        if self.model not in self.SUPPORTED_MODELS:
            raise TTSConfigurationError(f"지원하지 않는 모델: {self.model}")
        
        if self.voice not in self.SUPPORTED_VOICES:
            raise TTSConfigurationError(f"지원하지 않는 음성: {self.voice}")
        
        if not (0.25 <= self.speed <= 4.0):
            raise TTSConfigurationError(f"음성 속도는 0.25-4.0 범위여야 합니다: {self.speed}")
        
        if self.response_format not in self.SUPPORTED_FORMATS:
            raise TTSConfigurationError(f"지원하지 않는 형식: {self.response_format}")
    
    def initialize(self) -> bool:
        """
        OpenAI 클라이언트 초기화
        
        Returns:
            초기화 성공 여부
        """
        try:
            self.client = OpenAI(api_key=self.api_key)
            
            # API 연결 테스트 (모델 목록 조회)
            models = self.client.models.list()
            self.is_initialized = True
            
            self.logger.info(f"OpenAI TTS 제공자 초기화 완료 (모델: {self.model}, 음성: {self.voice})")
            return True
            
        except Exception as e:
            self.logger.error(f"OpenAI TTS 제공자 초기화 실패: {e}")
            raise TTSInitializationError(f"OpenAI TTS 초기화 실패: {str(e)}")
    
    def text_to_speech(self, text: str, output_path: str, **kwargs) -> bool:
        """
        텍스트를 음성으로 변환하여 파일로 저장
        
        Args:
            text: 변환할 텍스트
            output_path: 출력 파일 경로
            **kwargs: 추가 옵션
                - voice: 음성 (기본값 사용)
                - speed: 속도 (기본값 사용)
                - model: 모델 (기본값 사용)
                
        Returns:
            변환 성공 여부
        """
        if not self.is_initialized:
            raise TTSInitializationError("TTS 제공자가 초기화되지 않았습니다")
        
        if not self.validate_text(text):
            raise TTSConversionError("유효하지 않은 텍스트입니다")
        
        try:
            # 옵션 설정 (kwargs로 오버라이드 가능)
            voice = kwargs.get('voice', self.voice)
            speed = kwargs.get('speed', self.speed)
            model = kwargs.get('model', self.model)
            
            # 옵션 검증
            if voice not in self.SUPPORTED_VOICES:
                raise TTSConversionError(f"지원하지 않는 음성: {voice}")
            
            if not (0.25 <= speed <= 4.0):
                raise TTSConversionError(f"음성 속도는 0.25-4.0 범위여야 합니다: {speed}")
            
            self.logger.info(f"TTS 변환 시작: {len(text)}자, 음성={voice}, 속도={speed}")
            
            # OpenAI TTS API 호출
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed,
                response_format=self.response_format
            )
            
            # 출력 디렉토리 생성
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 파일로 저장
            with open(output_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            self.logger.info(f"TTS 변환 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"TTS 변환 실패: {e}")
            raise TTSConversionError(f"TTS 변환 실패: {str(e)}")
    
    def get_supported_voices(self) -> List[str]:
        """
        지원하는 음성 목록 반환
        
        Returns:
            음성 목록
        """
        return self.SUPPORTED_VOICES.copy()
    
    def get_supported_formats(self) -> List[str]:
        """
        지원하는 오디오 형식 목록 반환
        
        Returns:
            오디오 형식 목록
        """
        return self.SUPPORTED_FORMATS.copy()
    
    def get_supported_models(self) -> List[str]:
        """
        지원하는 모델 목록 반환
        
        Returns:
            모델 목록
        """
        return self.SUPPORTED_MODELS.copy()
    
    def validate_text(self, text: str) -> bool:
        """
        텍스트 유효성 검증 (OpenAI 특화)
        
        Args:
            text: 검증할 텍스트
            
        Returns:
            유효성 여부
        """
        if not super().validate_text(text):
            return False
        
        # OpenAI TTS 특화 검증
        # 최대 4096자 제한
        if len(text) > 4096:
            return False
        
        return True
    
    def estimate_cost(self, text: str, model: Optional[str] = None) -> float:
        """
        TTS 변환 비용 추정 (USD)
        
        Args:
            text: 변환할 텍스트
            model: 사용할 모델 (None인 경우 기본 모델 사용)
            
        Returns:
            추정 비용 (USD)
        """
        if not model:
            model = self.model
        
        # OpenAI TTS 가격 (2024년 기준)
        # tts-1: $15.00 / 1M characters
        # tts-1-hd: $30.00 / 1M characters
        price_per_million = 15.00 if model == 'tts-1' else 30.00
        
        char_count = len(text)
        cost = (char_count / 1_000_000) * price_per_million
        
        return cost
    
    def cleanup(self):
        """리소스 정리"""
        if self.client:
            self.client = None
        self.is_initialized = False
        self.logger.info("OpenAI TTS 제공자 정리 완료")
    
    @property
    def provider_name(self) -> str:
        """제공자 이름 반환"""
        return "OpenAI TTS"