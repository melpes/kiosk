"""
마이크 입력 시스템 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
import torch

from ..models.microphone_models import (
    MicrophoneConfig, MicrophoneStatus, AudioFrame, 
    RecordingInfo, VADResult, AudioBuffer
)


class IVADProcessor(ABC):
    """Voice Activity Detection 처리기 인터페이스"""
    
    @abstractmethod
    def detect_speech(self, audio_tensor: torch.Tensor) -> VADResult:
        """음성 활동 감지"""
        pass
    
    @abstractmethod
    def is_model_ready(self) -> bool:
        """모델 준비 상태 확인"""
        pass
    
    @abstractmethod
    def load_model(self) -> bool:
        """VAD 모델 로드"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        pass


class IAudioRecorder(ABC):
    """오디오 녹음기 인터페이스"""
    
    @abstractmethod
    def start_recording(self) -> bool:
        """녹음 시작"""
        pass
    
    @abstractmethod
    def stop_recording(self) -> Optional[str]:
        """녹음 종료 및 파일 경로 반환"""
        pass
    
    @abstractmethod
    def add_audio_frame(self, audio_frame: np.ndarray, is_speech: bool):
        """오디오 프레임 추가"""
        pass
    
    @abstractmethod
    def save_recording(self) -> Optional[str]:
        """녹음 저장"""
        pass
    
    @abstractmethod
    def get_recording_info(self) -> Optional[RecordingInfo]:
        """녹음 정보 반환"""
        pass
    
    @abstractmethod
    def clear_recording(self):
        """녹음 데이터 초기화"""
        pass


class IRealTimeProcessor(ABC):
    """실시간 처리기 인터페이스"""
    
    @abstractmethod
    def update_status(self, status: MicrophoneStatus):
        """상태 업데이트"""
        pass
    
    @abstractmethod
    def display_volume_level(self, level: float):
        """볼륨 레벨 표시"""
        pass
    
    @abstractmethod
    def display_vad_status(self, is_speech: bool, confidence: float):
        """VAD 상태 표시"""
        pass
    
    @abstractmethod
    def display_recording_progress(self, duration: float):
        """녹음 진행 상황 표시"""
        pass


class IMicrophoneInputManager(ABC):
    """마이크 입력 관리자 인터페이스"""
    
    @abstractmethod
    def start_listening(self) -> Optional[str]:
        """마이크 리스닝 시작"""
        pass
    
    @abstractmethod
    def stop_listening(self):
        """마이크 리스닝 종료"""
        pass
    
    @abstractmethod
    def get_microphone_status(self) -> MicrophoneStatus:
        """마이크 상태 반환"""
        pass
    
    @abstractmethod
    def update_config(self, new_config: MicrophoneConfig):
        """설정 업데이트"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """마이크 사용 가능 여부 확인"""
        pass
    
    @abstractmethod
    def test_microphone(self) -> Dict[str, Any]:
        """마이크 테스트"""
        pass