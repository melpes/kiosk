"""
오디오 처리 유틸리티
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Tuple
import tempfile
import shutil

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

from .logger import get_logger


class AudioUtils:
    """오디오 처리 유틸리티 클래스"""
    
    def __init__(self):
        self.logger = get_logger(f"{__name__}.AudioUtils")
        self.temp_dir = Path(tempfile.gettempdir()) / "voice_client_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # pygame 초기화 (사용 가능한 경우)
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.pygame_initialized = True
                self.logger.info("pygame 오디오 시스템 초기화 완료")
            except Exception as e:
                self.pygame_initialized = False
                self.logger.warning(f"pygame 초기화 실패: {e}")
        else:
            self.pygame_initialized = False
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        오디오 파일 유효성 검증
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            Tuple[bool, str]: (유효성, 오류 메시지)
        """
        try:
            file_path = Path(file_path)
            
            # 파일 존재 확인
            if not file_path.exists():
                return False, f"파일을 찾을 수 없습니다: {file_path}"
            
            # 파일 크기 확인
            file_size = file_path.stat().st_size
            if file_size == 0:
                return False, "파일이 비어있습니다"
            
            # 파일 확장자 확인
            supported_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
            if file_path.suffix.lower() not in supported_extensions:
                return False, f"지원하지 않는 파일 형식입니다: {file_path.suffix}"
            
            # soundfile로 파일 정보 확인 (가능한 경우)
            if SOUNDFILE_AVAILABLE:
                try:
                    info = sf.info(str(file_path))
                    self.logger.debug(f"오디오 파일 정보: {info.frames} frames, {info.samplerate} Hz, {info.channels} channels")
                    
                    # 기본적인 유효성 검사
                    if info.frames == 0:
                        return False, "오디오 데이터가 없습니다"
                    if info.samplerate <= 0:
                        return False, "잘못된 샘플링 레이트입니다"
                    if info.channels <= 0:
                        return False, "잘못된 채널 수입니다"
                        
                except Exception as e:
                    return False, f"오디오 파일 분석 실패: {e}"
            
            return True, "유효한 오디오 파일입니다"
            
        except Exception as e:
            return False, f"파일 검증 중 오류 발생: {e}"
    
    def get_audio_info(self, file_path: str) -> Optional[dict]:
        """
        오디오 파일 정보 반환
        
        Args:
            file_path: 오디오 파일 경로
            
        Returns:
            dict: 오디오 파일 정보 (실패시 None)
        """
        if not SOUNDFILE_AVAILABLE:
            self.logger.warning("soundfile 라이브러리가 없어 오디오 정보를 가져올 수 없습니다")
            return None
        
        try:
            info = sf.info(str(file_path))
            return {
                'frames': info.frames,
                'samplerate': info.samplerate,
                'channels': info.channels,
                'duration': info.frames / info.samplerate,
                'format': info.format,
                'subtype': info.subtype
            }
        except Exception as e:
            self.logger.error(f"오디오 정보 가져오기 실패: {e}")
            return None
    
    def play_audio_file(self, file_path: str, method: str = "auto") -> bool:
        """
        오디오 파일 재생
        
        Args:
            file_path: 재생할 파일 경로
            method: 재생 방법 ("auto", "pygame", "playsound", "system")
            
        Returns:
            bool: 재생 성공 여부
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"재생할 파일을 찾을 수 없습니다: {file_path}")
            return False
        
        self.logger.info(f"오디오 파일 재생 시작: {file_path} (방법: {method})")
        
        # 자동 선택
        if method == "auto":
            if self.pygame_initialized:
                method = "pygame"
            elif PLAYSOUND_AVAILABLE:
                method = "playsound"
            else:
                method = "system"
        
        try:
            if method == "pygame" and self.pygame_initialized:
                return self._play_with_pygame(str(file_path))
            elif method == "playsound" and PLAYSOUND_AVAILABLE:
                return self._play_with_playsound(str(file_path))
            elif method == "system":
                return self._play_with_system(str(file_path))
            else:
                self.logger.error(f"지원하지 않는 재생 방법: {method}")
                return False
                
        except Exception as e:
            self.logger.error(f"오디오 재생 실패: {e}")
            return False
    
    def _play_with_pygame(self, file_path: str) -> bool:
        """pygame으로 오디오 재생"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 재생 완료까지 대기
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            self.logger.info("pygame으로 오디오 재생 완료")
            return True
        except Exception as e:
            self.logger.error(f"pygame 재생 실패: {e}")
            return False
    
    def _play_with_playsound(self, file_path: str) -> bool:
        """playsound로 오디오 재생"""
        try:
            playsound(file_path)
            self.logger.info("playsound로 오디오 재생 완료")
            return True
        except Exception as e:
            self.logger.error(f"playsound 재생 실패: {e}")
            return False
    
    def _play_with_system(self, file_path: str) -> bool:
        """시스템 명령어로 오디오 재생"""
        try:
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                os.system(f'start "" "{file_path}"')
            elif system == "darwin":  # macOS
                os.system(f'afplay "{file_path}"')
            elif system == "linux":
                # 여러 플레이어 시도
                players = ["aplay", "paplay", "play", "mpg123", "ffplay"]
                for player in players:
                    if shutil.which(player):
                        os.system(f'{player} "{file_path}" > /dev/null 2>&1')
                        break
                else:
                    self.logger.error("사용 가능한 오디오 플레이어를 찾을 수 없습니다")
                    return False
            else:
                self.logger.error(f"지원하지 않는 운영체제: {system}")
                return False
            
            self.logger.info("시스템 명령어로 오디오 재생 완료")
            return True
        except Exception as e:
            self.logger.error(f"시스템 재생 실패: {e}")
            return False
    
    def save_audio_data(self, audio_data: bytes, file_path: str, 
                       sample_rate: int = 16000, channels: int = 1) -> bool:
        """
        오디오 데이터를 파일로 저장
        
        Args:
            audio_data: 오디오 바이너리 데이터
            file_path: 저장할 파일 경로
            sample_rate: 샘플링 레이트
            channels: 채널 수
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(audio_data)
            
            self.logger.info(f"오디오 데이터 저장 완료: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"오디오 데이터 저장 실패: {e}")
            return False
    
    def create_temp_file(self, suffix: str = ".wav") -> str:
        """
        임시 오디오 파일 경로 생성
        
        Args:
            suffix: 파일 확장자
            
        Returns:
            str: 임시 파일 경로
        """
        timestamp = int(time.time())
        temp_file = self.temp_dir / f"temp_audio_{timestamp}{suffix}"
        return str(temp_file)
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        오래된 임시 파일 정리
        
        Args:
            max_age_hours: 최대 보관 시간 (시간)
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_count = 0
            for temp_file in self.temp_dir.glob("temp_audio_*"):
                if temp_file.is_file():
                    file_age = current_time - temp_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        temp_file.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(f"임시 파일 {cleaned_count}개 정리 완료")
        except Exception as e:
            self.logger.error(f"임시 파일 정리 실패: {e}")
    
    def get_available_players(self) -> List[str]:
        """사용 가능한 오디오 플레이어 목록 반환"""
        players = []
        
        if self.pygame_initialized:
            players.append("pygame")
        if PLAYSOUND_AVAILABLE:
            players.append("playsound")
        
        # 시스템 플레이어 확인
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            players.append("system (Windows Media Player)")
        elif system == "darwin":
            if shutil.which("afplay"):
                players.append("system (afplay)")
        elif system == "linux":
            linux_players = ["aplay", "paplay", "play", "mpg123", "ffplay"]
            for player in linux_players:
                if shutil.which(player):
                    players.append(f"system ({player})")
                    break
        
        return players
    
    def __del__(self):
        """소멸자 - pygame 정리"""
        if hasattr(self, 'pygame_initialized') and self.pygame_initialized:
            try:
                pygame.mixer.quit()
            except:
                pass