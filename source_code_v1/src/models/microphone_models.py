"""
마이크 입력 관련 데이터 모델
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


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


@dataclass
class MicrophoneStatus:
    """마이크 상태 정보"""
    is_listening: bool
    is_recording: bool
    current_volume_level: float
    recording_duration: float
    vad_status: str  # "waiting", "detecting", "recording", "processing"
    last_speech_detected: Optional[datetime]