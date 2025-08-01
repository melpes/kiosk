"""
TTS 관리자 클래스
다양한 TTS 제공자를 관리하고 교체 가능하게 하는 매니저
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Type, List
from datetime import datetime, timedelta

from .tts_providers.base_tts import BaseTTSProvider, TTSError, TTSInitializationError, TTSConversionError
from .tts_providers.openai_tts import OpenAITTSProvider
from ..logger import get_logger


class TTSManager:
    """TTS 관리자 클래스"""
    
    # 사용 가능한 TTS 제공자 등록
    AVAILABLE_PROVIDERS: Dict[str, Type[BaseTTSProvider]] = {
        'openai': OpenAITTSProvider,
    }
    
    def __init__(self, 
                 provider_name: str = 'openai',
                 provider_config: Optional[Dict[str, Any]] = None,
                 output_directory: Optional[str] = None):
        """
        TTS 관리자 초기화
        
        Args:
            provider_name: 사용할 TTS 제공자 이름
            provider_config: 제공자별 설정
            output_directory: TTS 파일 출력 디렉토리
        """
        self.logger = get_logger(__name__)
        self.provider_name = provider_name
        self.provider_config = provider_config or {}
        
        # 출력 디렉토리 설정
        if output_directory:
            self.output_directory = Path(output_directory)
        else:
            self.output_directory = Path(tempfile.gettempdir()) / "voice_kiosk_tts"
        
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # TTS 제공자 인스턴스
        self.provider: Optional[BaseTTSProvider] = None
        
        # 파일 캐시 관리
        self.file_cache: Dict[str, Dict[str, Any]] = {}
        
        # 초기화
        self._initialize_provider()
    
    def _initialize_provider(self):
        """TTS 제공자 초기화"""
        try:
            if self.provider_name not in self.AVAILABLE_PROVIDERS:
                available = ', '.join(self.AVAILABLE_PROVIDERS.keys())
                raise TTSInitializationError(
                    f"지원하지 않는 TTS 제공자: {self.provider_name}. "
                    f"사용 가능한 제공자: {available}"
                )
            
            # 제공자 인스턴스 생성
            provider_class = self.AVAILABLE_PROVIDERS[self.provider_name]
            self.provider = provider_class(self.provider_config)
            
            # 제공자 초기화
            if not self.provider.initialize():
                raise TTSInitializationError(f"TTS 제공자 초기화 실패: {self.provider_name}")
            
            self.logger.info(f"TTS 관리자 초기화 완료 (제공자: {self.provider_name})")
            
        except Exception as e:
            self.logger.error(f"TTS 관리자 초기화 실패: {e}")
            raise
    
    def switch_provider(self, 
                       provider_name: str, 
                       provider_config: Optional[Dict[str, Any]] = None):
        """
        TTS 제공자 교체
        
        Args:
            provider_name: 새로운 제공자 이름
            provider_config: 새로운 제공자 설정
        """
        try:
            self.logger.info(f"TTS 제공자 교체: {self.provider_name} -> {provider_name}")
            
            # 기존 제공자 정리
            if self.provider:
                self.provider.cleanup()
            
            # 새로운 제공자 설정
            self.provider_name = provider_name
            self.provider_config = provider_config or {}
            
            # 새로운 제공자 초기화
            self._initialize_provider()
            
            self.logger.info(f"TTS 제공자 교체 완료: {provider_name}")
            
        except Exception as e:
            self.logger.error(f"TTS 제공자 교체 실패: {e}")
            raise
    
    def text_to_speech(self, 
                      text: str, 
                      file_id: Optional[str] = None,
                      **kwargs) -> str:
        """
        텍스트를 음성으로 변환하고 파일 ID 반환
        
        Args:
            text: 변환할 텍스트
            file_id: 파일 ID (None인 경우 자동 생성)
            **kwargs: 제공자별 추가 옵션
            
        Returns:
            생성된 파일 ID
        """
        if not self.provider:
            raise TTSInitializationError("TTS 제공자가 초기화되지 않았습니다")
        
        try:
            # 파일 ID 생성
            if not file_id:
                file_id = str(uuid.uuid4())
            
            # 출력 파일 경로 생성
            file_extension = kwargs.get('format', 'wav')
            output_filename = f"tts_{file_id}.{file_extension}"
            output_path = self.output_directory / output_filename
            
            self.logger.info(f"TTS 변환 시작: {len(text)}자 -> {output_path}")
            
            # TTS 변환 수행
            success = self.provider.text_to_speech(text, str(output_path), **kwargs)
            
            if not success:
                raise TTSConversionError("TTS 변환 실패")
            
            # 파일 캐시에 저장
            expires_at = datetime.now() + timedelta(hours=1)  # 1시간 후 만료
            self.file_cache[file_id] = {
                'path': str(output_path),
                'text': text,
                'provider': self.provider_name,
                'created_at': datetime.now(),
                'expires_at': expires_at,
                'kwargs': kwargs
            }
            
            self.logger.info(f"TTS 변환 완료: {file_id}")
            return file_id
            
        except Exception as e:
            self.logger.error(f"TTS 변환 실패: {e}")
            raise TTSConversionError(f"TTS 변환 실패: {str(e)}")
    
    def get_file_path(self, file_id: str) -> Optional[str]:
        """
        파일 ID로 파일 경로 반환
        
        Args:
            file_id: 파일 ID
            
        Returns:
            파일 경로 (존재하지 않으면 None)
        """
        if file_id not in self.file_cache:
            self.logger.warning(f"TTS 파일 ID를 찾을 수 없음: {file_id}")
            return None
        
        file_info = self.file_cache[file_id]
        file_path = file_info['path']
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            self.logger.warning(f"TTS 파일이 존재하지 않음: {file_path}")
            del self.file_cache[file_id]
            return None
        
        # 만료 시간 확인
        if datetime.now() > file_info['expires_at']:
            self.logger.info(f"TTS 파일 만료: {file_path}")
            self._remove_file(file_id)
            return None
        
        return file_path
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        파일 ID로 파일 정보 반환
        
        Args:
            file_id: 파일 ID
            
        Returns:
            파일 정보 딕셔너리 (존재하지 않으면 None)
        """
        if file_id not in self.file_cache:
            return None
        
        file_info = self.file_cache[file_id].copy()
        
        # 만료 시간 확인
        if datetime.now() > file_info['expires_at']:
            self._remove_file(file_id)
            return None
        
        return file_info
    
    def _remove_file(self, file_id: str):
        """파일 삭제"""
        if file_id not in self.file_cache:
            return
        
        file_info = self.file_cache[file_id]
        file_path = file_info['path']
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            del self.file_cache[file_id]
            self.logger.info(f"TTS 파일 삭제: {file_path}")
        except Exception as e:
            self.logger.error(f"TTS 파일 삭제 실패: {e}")
    
    def cleanup_expired_files(self):
        """만료된 파일 정리"""
        try:
            current_time = datetime.now()
            expired_files = []
            
            for file_id, file_info in self.file_cache.items():
                if current_time > file_info['expires_at']:
                    expired_files.append(file_id)
            
            for file_id in expired_files:
                self._remove_file(file_id)
            
            if expired_files:
                self.logger.info(f"만료된 TTS 파일 {len(expired_files)}개 정리 완료")
                
        except Exception as e:
            self.logger.error(f"TTS 파일 정리 실패: {e}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        현재 TTS 제공자 정보 반환
        
        Returns:
            제공자 정보 딕셔너리
        """
        if not self.provider:
            return {'provider': None, 'initialized': False}
        
        info = {
            'provider': self.provider_name,
            'provider_class': self.provider.provider_name,
            'initialized': self.provider.is_initialized,
            'supported_voices': self.provider.get_supported_voices(),
            'supported_formats': self.provider.get_supported_formats(),
        }
        
        # OpenAI 제공자인 경우 추가 정보
        if isinstance(self.provider, OpenAITTSProvider):
            info.update({
                'supported_models': self.provider.get_supported_models(),
                'current_model': self.provider.model,
                'current_voice': self.provider.voice,
                'current_speed': self.provider.speed,
            })
        
        return info
    
    def get_available_providers(self) -> List[str]:
        """
        사용 가능한 TTS 제공자 목록 반환
        
        Returns:
            제공자 이름 목록
        """
        return list(self.AVAILABLE_PROVIDERS.keys())
    
    def estimate_cost(self, text: str) -> Optional[float]:
        """
        TTS 변환 비용 추정
        
        Args:
            text: 변환할 텍스트
            
        Returns:
            추정 비용 (제공자가 지원하지 않으면 None)
        """
        if not self.provider:
            return None
        
        # OpenAI 제공자인 경우 비용 추정
        if isinstance(self.provider, OpenAITTSProvider):
            return self.provider.estimate_cost(text)
        
        return None
    
    def cleanup(self):
        """리소스 정리"""
        try:
            # 모든 캐시된 파일 삭제
            for file_id in list(self.file_cache.keys()):
                self._remove_file(file_id)
            
            # 제공자 정리
            if self.provider:
                self.provider.cleanup()
                self.provider = None
            
            self.logger.info("TTS 관리자 정리 완료")
            
        except Exception as e:
            self.logger.error(f"TTS 관리자 정리 실패: {e}")
    
    def __del__(self):
        """소멸자"""
        self.cleanup()