"""
키오스크 클라이언트 패키지
"""

__version__ = "1.0.0"
__author__ = "Voice Kiosk Team"

from .voice_client import VoiceClient
from .config_manager import ConfigManager
from .ui_manager import KioskUIManager
from .microphone_manager import RealTimeMicrophoneManager, MicrophoneError, RecordingError
from .vad_processor import VADProcessor

__all__ = [
    "VoiceClient",
    "ConfigManager", 
    "KioskUIManager",
    "RealTimeMicrophoneManager",
    "MicrophoneError",
    "RecordingError",
    "VADProcessor"
]