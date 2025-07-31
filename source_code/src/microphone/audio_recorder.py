"""
오디오 녹음 및 파일 생성 모듈
"""
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from collections import deque
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

from src.models.microphone_models import MicrophoneConfig
from src.logger import get_logger

logger = get_logger(__name__)


class AudioRecorder:
    """오디오 녹음 및 파일 생성"""
    
    def __init__(self, config: MicrophoneConfig):
        self.config = config
        self.recorded_frames: List[np.ndarray] = []
        self.silence_buffer_start = deque(
            maxlen=int(config.max_silence_duration_start / config.frame_duration)
        )
        self.silence_buffer_end = deque(
            maxlen=int(config.max_silence_duration_end / config.frame_duration)
        )
        self.stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.start_time: Optional[datetime] = None
    
    def start_recording(self) -> None:
        """녹음 시작"""
        try:
            logger.info("오디오 녹음 시작")
            self.recorded_frames = []
            self.silence_buffer_start.clear()
            self.silence_buffer_end.clear()
            self.is_recording = True
            self.start_time = datetime.now()
            
            # 오디오 스트림 초기화
            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=int(self.config.sample_rate * self.config.frame_duration)
            )
            self.stream.start()
            logger.info(f"오디오 스트림 시작 (샘플레이트: {self.config.sample_rate}Hz)")
            
        except Exception as e:
            logger.error(f"녹음 시작 중 오류 발생: {e}")
            self.is_recording = False
            raise
    
    def stop_recording(self) -> str:
        """녹음 종료 및 파일 저장"""
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            self.is_recording = False
            logger.info("오디오 녹음 종료")
            
            return self.save_recording()
            
        except Exception as e:
            logger.error(f"녹음 종료 중 오류 발생: {e}")
            raise
    
    def add_audio_frame(self, audio_frame: np.ndarray, is_speech: bool) -> None:
        """오디오 프레임 추가"""
        if is_speech:
            # 음성이 감지되면 이전 무음 버퍼를 녹음에 추가
            if len(self.silence_buffer_end) != 0:
                self.recorded_frames.extend(list(self.silence_buffer_end))
                self.silence_buffer_end.clear()
            self.recorded_frames.append(audio_frame)
        else:
            # 무음인 경우
            if self.recorded_frames:
                # 이미 녹음이 시작된 경우 종료 버퍼에 추가
                self.silence_buffer_end.append(audio_frame)
            else:
                # 아직 녹음이 시작되지 않은 경우 시작 버퍼에 추가
                self.silence_buffer_start.append(audio_frame)
    
    def should_stop_recording(self) -> tuple[bool, str]:
        """녹음을 중단해야 하는지 확인"""
        # 녹음이 시작된 후 무음이 지속되는 경우
        if self.recorded_frames:
            if len(self.silence_buffer_end) == self.silence_buffer_end.maxlen:
                return True, "무음이 지속되어 녹음을 종료합니다."
        else:
            # 녹음이 시작되지 않았는데 무음이 지속되는 경우
            if len(self.silence_buffer_start) == self.silence_buffer_start.maxlen:
                return True, "입력시간이 초과되었습니다."
        
        return False, ""
    
    def read_audio_frame(self) -> Optional[np.ndarray]:
        """오디오 프레임 읽기"""
        if not self.stream or not self.is_recording:
            return None
        
        try:
            audio_block, _ = self.stream.read(
                int(self.config.sample_rate * self.config.frame_duration)
            )
            return audio_block.squeeze()
        except Exception as e:
            logger.error(f"오디오 프레임 읽기 중 오류: {e}")
            return None
    
    def save_recording(self) -> str:
        """녹음 파일 저장"""
        if len(self.recorded_frames) < int(self.config.min_record_duration * self.config.sample_rate / (self.config.sample_rate * self.config.frame_duration)):
            raise ValueError("음성이 너무 짧습니다.")
        
        try:
            # 모든 오디오 프레임 결합
            all_audio = np.concatenate(self.recorded_frames)
            
            # 파일명에 타임스탬프 추가
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{self.config.output_filename}"
            
            # WAV 파일로 저장 (16비트 정수로 변환)
            write(filename, self.config.sample_rate, (all_audio * 32767).astype(np.int16))
            
            logger.info(f"오디오 파일 저장 완료: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"오디오 파일 저장 중 오류: {e}")
            raise
    
    def get_recording_info(self) -> Dict[str, Any]:
        """녹음 정보 반환"""
        duration = 0
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_recording": self.is_recording,
            "recorded_frames_count": len(self.recorded_frames),
            "recording_duration": duration,
            "silence_buffer_start_count": len(self.silence_buffer_start),
            "silence_buffer_end_count": len(self.silence_buffer_end),
            "config": {
                "sample_rate": self.config.sample_rate,
                "frame_duration": self.config.frame_duration,
                "min_record_duration": self.config.min_record_duration
            }
        }
    
    def cleanup(self) -> None:
        """리소스 정리"""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        self.recorded_frames = []
        self.silence_buffer_start.clear()
        self.silence_buffer_end.clear()
        self.is_recording = False