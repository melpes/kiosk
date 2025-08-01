"""
실시간 마이크 입력 관리 모듈 (클라이언트용)
"""
import torch
import numpy as np
import sounddevice as sd
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path

from .config_manager import ClientConfig
from .vad_processor import VADProcessor
from .models.communication_models import ServerResponse
from .voice_client import VoiceClient
from utils.logger import get_logger

logger = get_logger(__name__)


class MicrophoneError(Exception):
    """마이크 관련 오류"""
    pass


class RecordingError(Exception):
    """녹음 관련 오류"""
    pass


class ErrorType(Enum):
    """오류 유형"""
    HARDWARE_ERROR = "hardware_error"
    VAD_MODEL_ERROR = "vad_model_error"
    RECORDING_ERROR = "recording_error"
    CONFIG_ERROR = "config_error"
    UNKNOWN_ERROR = "unknown_error"


class RealTimeMicrophoneManager:
    """실시간 마이크 입력 및 자동 서버 전송 관리"""
    
    def __init__(self, config: ClientConfig, voice_client: VoiceClient):
        self.config = config
        self.voice_client = voice_client
        self.vad_processor = VADProcessor()
        
        # 마이크 설정
        self.sample_rate = 16000
        self.frame_duration = 0.5
        self.max_silence_duration_start = 5.0
        self.max_silence_duration_end = 3.0
        self.min_record_duration = 0.3  # 짧은 답변 처리를 위해 0.3초로 줄임
        self.vad_threshold = 0.2
        self.preroll_duration = 1.0  # 음성 시작 전 포함할 오디오 길이 (초)
        
        # 상태 관리
        self.is_listening = False
        self.is_recording = False
        self.current_volume_level = 0.0
        self.recording_duration = 0.0
        self.vad_status = "waiting"
        self.last_speech_detected = None
        self.error_history: List[Dict[str, Any]] = []
        self.fallback_mode = False
        
        # 무한반복 방지용 카운터
        self.consecutive_short_recordings = 0
        self.max_consecutive_failures = 5
        self.last_timeout_message_time = None
        self.timeout_message_interval = 15.0  # 타임아웃 메시지 간격 (초) - 더 길게 설정
        self.timeout_silence_period = 5.0  # 타임아웃 후 무음 처리 시간 (초) - 더 길게 설정
        self.consecutive_timeouts = 0  # 연속 타임아웃 카운터
        
        # 녹음 관련
        self.stream: Optional[sd.InputStream] = None
        self.recorded_frames: List[np.ndarray] = []
        self.silence_buffer_start = []
        self.silence_buffer_end = []
        self.start_time: Optional[datetime] = None
        
        # 콜백 함수
        self.on_audio_ready: Optional[Callable[[str], None]] = None
        self.on_response_received: Optional[Callable[[ServerResponse], None]] = None
        
        # 초기화
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """컴포넌트 초기화"""
        try:
            # VAD 프로세서 초기화 확인
            if not self.vad_processor.is_model_ready():
                logger.warning("VAD 모델 로딩 실패, 폴백 모드로 전환")
                self.fallback_mode = True
                self._log_error(ErrorType.VAD_MODEL_ERROR, "VAD 모델 로딩 실패")
            
            logger.info("실시간 마이크 컴포넌트 초기화 완료")
            
        except Exception as e:
            logger.error(f"컴포넌트 초기화 실패: {e}")
            self._log_error(ErrorType.UNKNOWN_ERROR, f"컴포넌트 초기화 실패: {e}")
            raise MicrophoneError(f"마이크 시스템 초기화 실패: {e}")
    
    def _log_error(self, error_type: ErrorType, message: str) -> None:
        """오류 로그 기록"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "message": message
        }
        self.error_history.append(error_entry)
        
        # 최대 100개의 오류만 보관
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def _check_hardware_availability(self) -> Dict[str, Any]:
        """하드웨어 가용성 확인"""
        try:
            # 사용 가능한 오디오 장치 확인
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if not input_devices:
                raise MicrophoneError("사용 가능한 마이크 장치가 없습니다")
            
            # 기본 입력 장치 확인
            default_device = sd.query_devices(kind='input')
            
            return {
                "available": True,
                "input_devices_count": len(input_devices),
                "default_device": default_device['name'],
                "default_samplerate": default_device.get('default_samplerate', 44100)
            }
            
        except Exception as e:
            logger.error(f"하드웨어 확인 실패: {e}")
            self._log_error(ErrorType.HARDWARE_ERROR, f"하드웨어 확인 실패: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def _detect_speech_fallback(self, audio_frame: np.ndarray) -> bool:
        """폴백 모드: 볼륨 기반 음성 감지"""
        volume_level = float(np.abs(audio_frame).mean())
        return volume_level > (self.vad_threshold * 10)
    
    def start_listening(self) -> None:
        """실시간 마이크 입력 시작"""
        logger.info("실시간 마이크 입력 모드 시작")
        
        # 하드웨어 가용성 확인
        hardware_status = self._check_hardware_availability()
        if not hardware_status["available"]:
            error_msg = f"마이크 하드웨어 사용 불가: {hardware_status.get('error', '알 수 없는 오류')}"
            self._log_error(ErrorType.HARDWARE_ERROR, error_msg)
            raise MicrophoneError(error_msg)
        
        # VAD 모델 상태 확인
        if not self.fallback_mode and not self.vad_processor.is_model_ready():
            logger.warning("VAD 모델이 준비되지 않음, 폴백 모드로 전환")
            self.fallback_mode = True
            self._log_error(ErrorType.VAD_MODEL_ERROR, "VAD 모델 준비되지 않음")
        
        try:
            self.is_listening = True
            self.vad_status = "waiting"
            
            if self.fallback_mode:
                print("🎤 실시간 주문 대기 중... (볼륨 감지 모드)")
            else:
                print("🎤 실시간 주문 대기 중... (VAD 모드)")
            
            # 메인 루프
            while self.is_listening:
                try:
                    self._wait_for_speech_and_record()
                    
                except KeyboardInterrupt:
                    print("\n사용자에 의해 중단되었습니다.")
                    break
                except Exception as e:
                    logger.error(f"오디오 처리 중 오류: {e}")
                    self._log_error(ErrorType.RECORDING_ERROR, f"오디오 처리 오류: {e}")
                    print(f"❌ 처리 중 오류: {e}")
                    time.sleep(1)  # 잠시 대기 후 재시도
                    
        except Exception as e:
            logger.error(f"실시간 마이크 입력 중 예상치 못한 오류: {e}")
            self._log_error(ErrorType.UNKNOWN_ERROR, f"예상치 못한 오류: {e}")
            raise MicrophoneError(f"실시간 마이크 입력 실패: {e}")
        finally:
            self._cleanup()
    
    def _wait_for_speech_and_record(self) -> None:
        """음성 감지 대기 및 녹음"""
        # 초기화
        self._reset_recording_state()
        
        # 오디오 스트림 시작
        self._start_audio_stream()
        
        try:
            frame_count = 0
            speech_detected = False
            
            while self.is_listening:
                # 오디오 프레임 읽기
                audio_frame = self._read_audio_frame()
                if audio_frame is None:
                    continue
                
                # 볼륨 레벨 계산
                self.current_volume_level = float(np.abs(audio_frame).mean())
                
                # 음성 감지
                if self.fallback_mode:
                    is_speech = self._detect_speech_fallback(audio_frame)
                else:
                    audio_tensor = torch.from_numpy(audio_frame)
                    is_speech = self.vad_processor.detect_speech(audio_tensor)
                
                # 음성 감지 상태 업데이트
                if is_speech:
                    if not speech_detected:
                        print("\n🗣️ 음성 감지됨! 녹음 시작...")
                        speech_detected = True
                        self.vad_status = "recording"
                        self.is_recording = True
                        self.start_time = datetime.now()
                        # 음성이 감지되면 연속 타임아웃 카운터 리셋
                        self.consecutive_timeouts = 0
                        
                        # 음성 시작 전 일부 무음도 포함 (pre-roll)
                        # 설정된 시간만큼의 선행 무음을 포함
                        max_preroll_frames = int(self.preroll_duration / self.frame_duration)
                        preroll_frames = self.silence_buffer_start[-max_preroll_frames:] if len(self.silence_buffer_start) > 0 else []
                        if preroll_frames:
                            self.recorded_frames.extend(preroll_frames)
                            print(f"   📀 음성 시작 전 {len(preroll_frames) * self.frame_duration:.1f}초 선행 오디오 포함")
                    
                    self.last_speech_detected = datetime.now()
                    # 무음 버퍼가 있다면 녹음에 추가
                    if self.silence_buffer_end:
                        self.recorded_frames.extend(self.silence_buffer_end)
                        self.silence_buffer_end = []
                    self.recorded_frames.append(audio_frame)
                else:
                    if speech_detected:
                        # 음성 후 무음
                        self.silence_buffer_end.append(audio_frame)
                    else:
                        # 음성 전 무음
                        self.silence_buffer_start.append(audio_frame)
                
                # 상태 표시 업데이트
                frame_count += 1
                if frame_count % 10 == 0:  # 주기적으로 상태 표시
                    self._display_status()
                
                # 녹음 종료 조건 확인
                should_stop, stop_reason = self._should_stop_recording(speech_detected)
                if should_stop:
                    if speech_detected and self.recorded_frames:
                        if stop_reason:  # 메시지가 있을 때만 출력
                            print(f"\n{stop_reason}")
                        process_result = self._process_recorded_audio()
                        if process_result:
                            break  # 성공적으로 처리됨
                    else:
                        if stop_reason:  # 메시지가 있을 때만 출력
                            print(f"\n{stop_reason}")
                        break
                        
        finally:
            self._stop_audio_stream()
    
    def _reset_recording_state(self) -> None:
        """녹음 상태 초기화"""
        self.recorded_frames = []
        self.silence_buffer_start = []
        self.silence_buffer_end = []
        self.is_recording = False
        self.vad_status = "waiting"
        self.start_time = None
        # 연속 실패 카운터는 여기서 리셋하지 않음 (연속성 유지를 위해)
    
    def _start_audio_stream(self) -> None:
        """오디오 스트림 시작"""
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            blocksize=int(self.sample_rate * self.frame_duration)
        )
        self.stream.start()
    
    def _stop_audio_stream(self) -> None:
        """오디오 스트림 중지"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def _read_audio_frame(self) -> Optional[np.ndarray]:
        """오디오 프레임 읽기"""
        if not self.stream:
            return None
        
        try:
            audio_block, _ = self.stream.read(
                int(self.sample_rate * self.frame_duration)
            )
            return audio_block.squeeze()
        except Exception as e:
            logger.error(f"오디오 프레임 읽기 중 오류: {e}")
            return None
    
    def _should_stop_recording(self, speech_detected: bool) -> tuple[bool, str]:
        """녹음을 중단해야 하는지 확인"""
        max_silence_frames_start = int(self.max_silence_duration_start / self.frame_duration)
        max_silence_frames_end = int(self.max_silence_duration_end / self.frame_duration)
        
        if speech_detected:
            # 녹음 중인데 무음이 지속되는 경우
            if len(self.silence_buffer_end) >= max_silence_frames_end:
                return True, "🔇 무음이 지속되어 녹음을 종료합니다."
        else:
            # 아직 음성이 감지되지 않았는데 대기 시간 초과
            if len(self.silence_buffer_start) >= max_silence_frames_start:
                current_time = time.time()
                
                # 최근에 타임아웃 메시지를 출력했다면 완전히 무시하고 버퍼만 클리어
                if (self.last_timeout_message_time is not None and 
                    current_time - self.last_timeout_message_time < self.timeout_silence_period):
                    # 버퍼를 대폭 클리어하여 재발생 방지
                    self.silence_buffer_start = []
                    return False, ""
                
                # 연속 타임아웃이 너무 많으면 메시지 출력 빈도를 더 줄임
                self.consecutive_timeouts += 1
                
                # 타임아웃 메시지 빈도 조절 (연속 타임아웃이 많을수록 더 긴 간격)
                effective_interval = self.timeout_message_interval + (self.consecutive_timeouts * 5)
                
                if (self.last_timeout_message_time is None or 
                    current_time - self.last_timeout_message_time >= effective_interval):
                    self.last_timeout_message_time = current_time
                    # 타임아웃 발생 시 버퍼를 완전히 클리어
                    self.silence_buffer_start = []
                    return True, "⏰ 입력 대기 시간이 초과되었습니다. 다시 말씀해주세요."
                else:
                    # 메시지 없이 조용히 대기 상태로 돌아가면서 버퍼 완전 클리어
                    self.silence_buffer_start = []
                    return False, ""
        
        return False, ""
    
    def _process_recorded_audio(self) -> bool:
        """녹음된 오디오 처리 및 서버 전송"""
        try:
            print("🔄 음성을 처리하고 서버로 전송 중...")
            
            # 최소 녹음 길이 확인
            min_frames = int(self.min_record_duration * self.sample_rate / (self.sample_rate * self.frame_duration))
            if len(self.recorded_frames) < min_frames:
                self.consecutive_short_recordings += 1
                
                # 연속 실패 횟수가 많으면 잠시 대기
                if self.consecutive_short_recordings >= self.max_consecutive_failures:
                    print(f"⚠️ 녹음이 계속 짧습니다. {self.max_consecutive_failures}회 연속 실패 후 잠시 대기합니다...")
                    time.sleep(2)  # 2초 대기
                    self.consecutive_short_recordings = 0  # 카운터 리셋
                    return False
                else:
                    print("⚠️ 녹음이 너무 짧습니다. 다시 시도해주세요.")
                    return False
            
            # 성공적으로 처리되면 카운터 리셋
            self.consecutive_short_recordings = 0
            
            # 오디오 파일 생성
            audio_file_path = self._save_audio_file()
            
            # 콜백 호출
            if self.on_audio_ready:
                self.on_audio_ready(audio_file_path)
            
            # 서버로 전송
            print("📡 서버로 음성 전송 중...")
            response = self.voice_client.send_audio_file(audio_file_path)
            
            # 설정에 따라 임시 파일 삭제
            if self.config.audio.delete_after_upload:
                try:
                    Path(audio_file_path).unlink()
                    print(f"🗑️ 업로드 후 음성 파일 삭제: {Path(audio_file_path).name}")
                except Exception as e:
                    print(f"⚠️ 파일 삭제 실패: {e}")
            else:
                print(f"💾 음성 파일 보관됨: {audio_file_path}")
            
            # 응답 처리
            if response.success:
                print(f"✅ 서버 응답: {response.message}")
                if self.on_response_received:
                    self.on_response_received(response)
            else:
                print(f"❌ 서버 오류: {response.error_info.error_message if response.error_info else '알 수 없는 오류'}")
            
            return True
            
        except Exception as e:
            logger.error(f"오디오 처리 중 오류: {e}")
            print(f"❌ 오디오 처리 실패: {e}")
            return False
    
    def _save_audio_file(self) -> str:
        """녹음 파일 저장"""
        try:
            # 모든 오디오 프레임 결합
            all_audio = np.concatenate(self.recorded_frames)
            
            # 임시 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_dir = Path(self.config.audio.temp_dir)
            temp_dir.mkdir(exist_ok=True)
            
            filename = temp_dir / f"realtime_mic_{timestamp}.wav"
            
            # WAV 파일로 저장
            from scipy.io.wavfile import write
            write(str(filename), self.sample_rate, (all_audio * 32767).astype(np.int16))
            
            logger.info(f"음성 파일 저장 완료: {filename}")
            return str(filename)
            
        except Exception as e:
            logger.error(f"음성 파일 저장 중 오류: {e}")
            raise
    
    def _display_status(self) -> None:
        """실시간 상태 표시"""
        status_symbols = {
            "waiting": "⏳",
            "detecting": "🗣️",
            "recording": "🎙️",
            "processing": "⚙️"
        }
        
        symbol = status_symbols.get(self.vad_status, "❓")
        volume_bar = "█" * min(int(self.current_volume_level * 50), 10)
        
        print(f"\r{symbol} 상태: {self.vad_status} | 볼륨: {volume_bar:<10} | "
              f"{'폴백 모드' if self.fallback_mode else 'VAD 모드'}", end="", flush=True)
    
    def stop_listening(self) -> None:
        """실시간 마이크 입력 중단"""
        logger.info("실시간 마이크 입력 중단")
        self.is_listening = False
        self._cleanup()
    
    def set_callbacks(self, 
                     on_audio_ready: Optional[Callable[[str], None]] = None,
                     on_response_received: Optional[Callable[[ServerResponse], None]] = None) -> None:
        """콜백 함수 설정"""
        self.on_audio_ready = on_audio_ready
        self.on_response_received = on_response_received
    
    def set_vad_settings(self, vad_threshold: Optional[float] = None, 
                        preroll_duration: Optional[float] = None) -> None:
        """VAD 설정 조정"""
        if vad_threshold is not None:
            self.vad_threshold = max(0.1, min(1.0, vad_threshold))  # 0.1~1.0 범위로 제한
            logger.info(f"VAD 임계값 변경: {self.vad_threshold}")
        
        if preroll_duration is not None:
            self.preroll_duration = max(0.0, min(3.0, preroll_duration))  # 0~3초 범위로 제한
            logger.info(f"Pre-roll 시간 변경: {self.preroll_duration}초")
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 반환"""
        recording_duration = 0
        if self.start_time:
            recording_duration = (datetime.now() - self.start_time).total_seconds()
        
        hardware_status = self._check_hardware_availability()
        
        return {
            "is_listening": self.is_listening,
            "is_recording": self.is_recording,
            "current_volume_level": self.current_volume_level,
            "recording_duration": recording_duration,
            "vad_status": self.vad_status,
            "last_speech_detected": self.last_speech_detected.isoformat() if self.last_speech_detected else None,
            "vad_model_ready": self.vad_processor.is_model_ready(),
            "fallback_mode": self.fallback_mode,
            "hardware_available": hardware_status["available"],
            "error_count": len(self.error_history),
            "last_error": self.error_history[-1] if self.error_history else None,
            "vad_threshold": self.vad_threshold,
            "preroll_duration": self.preroll_duration
        }
    
    def test_microphone(self) -> Dict[str, Any]:
        """마이크 테스트"""
        logger.info("마이크 테스트 시작")
        
        test_results = {
            "hardware_test": {"success": False},
            "vad_test": {"success": False},
            "recording_test": {"success": False},
            "overall_success": False
        }
        
        try:
            # 1. 하드웨어 테스트
            hardware_status = self._check_hardware_availability()
            test_results["hardware_test"] = {
                "success": hardware_status["available"],
                "details": hardware_status
            }
            
            if not hardware_status["available"]:
                test_results["hardware_test"]["error"] = hardware_status.get("error", "하드웨어 사용 불가")
                return test_results
            
            # 2. 짧은 시간 동안 오디오 입력 테스트
            test_duration = 2.0  # 2초
            print(f"마이크 테스트 중... {test_duration}초간 소리를 내주세요.")
            
            test_audio = sd.rec(
                int(test_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            
            # 볼륨 레벨 계산
            volume_level = float(np.abs(test_audio).mean())
            max_volume = float(np.abs(test_audio).max())
            
            test_results["recording_test"] = {
                "success": True,
                "average_volume": volume_level,
                "max_volume": max_volume,
                "sample_rate": self.sample_rate,
                "test_duration": test_duration,
                "audio_detected": volume_level > 0.001
            }
            
            # 3. VAD 테스트
            if self.vad_processor.is_model_ready():
                try:
                    audio_tensor = torch.from_numpy(test_audio.squeeze())
                    speech_detected = self.vad_processor.detect_speech(audio_tensor)
                    
                    test_results["vad_test"] = {
                        "success": True,
                        "speech_detected": speech_detected,
                        "model_ready": True
                    }
                except Exception as e:
                    test_results["vad_test"] = {
                        "success": False,
                        "error": str(e),
                        "model_ready": False
                    }
            else:
                test_results["vad_test"] = {
                    "success": False,
                    "error": "VAD 모델이 준비되지 않음",
                    "model_ready": False
                }
            
            # 전체 성공 여부 결정
            test_results["overall_success"] = (
                test_results["hardware_test"]["success"] and
                test_results["recording_test"]["success"]
            )
            
            # 권장사항 추가
            recommendations = []
            if volume_level < 0.001:
                recommendations.append("마이크 볼륨을 높이거나 더 가까이에서 말해보세요")
            if not test_results["vad_test"]["success"]:
                recommendations.append("VAD 모델 문제로 폴백 모드가 사용됩니다")
            
            test_results["recommendations"] = recommendations
            
            logger.info(f"마이크 테스트 완료: {'성공' if test_results['overall_success'] else '실패'}")
            return test_results
            
        except Exception as e:
            logger.error(f"마이크 테스트 실패: {e}")
            self._log_error(ErrorType.HARDWARE_ERROR, f"마이크 테스트 실패: {e}")
            test_results["error"] = str(e)
            return test_results
    
    def _cleanup(self) -> None:
        """리소스 정리"""
        print()  # 상태 표시 줄바꿈
        self.is_listening = False
        self.is_recording = False
        self.vad_status = "waiting"
        self._stop_audio_stream()
        self._reset_recording_state()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self._cleanup()