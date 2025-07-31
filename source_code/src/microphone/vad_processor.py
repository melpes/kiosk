"""
Voice Activity Detection 처리 모듈
"""
import torch
import urllib.error
from typing import Optional, Tuple, Dict, Any
from src.models.microphone_models import MicrophoneConfig
from src.logger import get_logger

logger = get_logger(__name__)


class VADProcessor:
    """Voice Activity Detection 처리"""
    
    def __init__(self, config: MicrophoneConfig):
        self.config = config
        self.model = None
        self.utils = None
        self._load_vad_model()
    
    def _load_vad_model(self) -> None:
        """Silero VAD 모델 로드"""
        logger.info("VAD 모델을 로드하는 중...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.model, self.utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False
                )
                logger.info("VAD 모델 로드 완료")
                return
            except urllib.error.HTTPError as e:
                logger.warning(f"VAD 모델 로드 시도 {attempt + 1}/{max_retries} 실패: {e}")
                if attempt == max_retries - 1:
                    logger.error("VAD 모델 로드 최종 실패")
                    raise
            except Exception as e:
                logger.error(f"VAD 모델 로드 중 예상치 못한 오류: {e}")
                raise
    
    def detect_speech(self, audio_tensor: torch.Tensor) -> bool:
        """음성 활동 감지"""
        if not self.is_model_ready():
            logger.warning("VAD 모델이 준비되지 않음")
            return False
        
        try:
            get_speech_timestamps, _, _, _, _ = self.utils
            speech_timestamps = get_speech_timestamps(
                audio_tensor,
                self.model,
                sampling_rate=self.config.sample_rate,
                threshold=self.config.vad_threshold
            )
            
            return len(speech_timestamps) > 0
            
        except Exception as e:
            logger.error(f"음성 감지 중 오류 발생: {e}")
            return False
    
    def is_model_ready(self) -> bool:
        """모델이 준비되었는지 확인"""
        return self.model is not None and self.utils is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_loaded": self.is_model_ready(),
            "vad_threshold": self.config.vad_threshold,
            "sample_rate": self.config.sample_rate
        }