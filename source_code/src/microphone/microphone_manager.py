"""
실시간 마이크 입력 관리 모듈
"""
import torch
import numpy as np
import sounddevice as sd
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from src.models.microphone_models import MicrophoneConfig, MicrophoneStatus
from src.microphone.vad_processor import VADProcessor
from src.microphone.audio_recorder import AudioRecorder
from src.microphone.realtime_processor import RealTimeProcessor
from src.logger import get_logger

logger = get_logger(__name__)


class MicrophoneError(Exception):
    """마이크 관련 오류"""
    pass


class VADError(Exception):
    """VAD 관련 오류"""
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


class MicrophoneInputManager:
    """실시간 마이크 입력 관리"""
    
    def __init__(self, config: MicrophoneConfig):
        self.config = config
        self.vad_processor = None
        self.audio_recorder = None
        self.realtime_processor = RealTimeProcessor()
        self.status = MicrophoneStatus(
            is_listening=False,
            is_recording=False,
            current_volume_level=0.0,
            recording_duration=0.0,
            vad_status="waiting",
            last_speech_detected=None
        )
        self.error_history: List[Dict[str, Any]] = []
        self.fallback_mode = False  # VAD 실패 시 볼륨 기반 감지 사용
        
        # 초기화
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """컴포넌트 초기화"""
        try:
            # VAD 프로세서 초기화
            self.vad_processor = VADProcessor(self.config)
            if not self.vad_processor.is_model_ready():
                logger.warning("VAD 모델 로딩 실패, 폴백 모드로 전환")
                self.fallback_mode = True
                self._log_error(ErrorType.VAD_MODEL_ERROR, "VAD 모델 로딩 실패")
            
            # 오디오 레코더 초기화
            self.audio_recorder = AudioRecorder(self.config)
            
            logger.info("마이크 컴포넌트 초기화 완료")
            
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
            
            # 샘플레이트 지원 확인 (default_samplerate는 float이므로 직접 비교)
            default_samplerate = default_device.get('default_samplerate', 44100)
            sample_rate_supported = abs(self.config.sample_rate - default_samplerate) < 1000  # 1kHz 오차 허용
            
            return {
                "available": True,
                "input_devices_count": len(input_devices),
                "default_device": default_device['name'],
                "default_samplerate": default_samplerate,
                "sample_rate_supported": sample_rate_supported
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
        # 간단한 볼륨 임계값 기반 감지 (VAD 임계값의 10배 사용)
        return volume_level > (self.config.vad_threshold * 10)
    
    def start_listening(self) -> str:
        """마이크 입력 시작 및 녹음된 파일 경로 반환"""
        logger.info("마이크 입력 모드 시작")
        
        # 하드웨어 가용성 확인
        hardware_status = self._check_hardware_availability()
        if not hardware_status["available"]:
            error_msg = f"마이크 하드웨어 사용 불가: {hardware_status.get('error', '알 수 없는 오류')}"
            self._log_error(ErrorType.HARDWARE_ERROR, error_msg)
            raise MicrophoneError(error_msg)
        
        # VAD 모델 상태 확인
        if not self.fallback_mode and (not self.vad_processor or not self.vad_processor.is_model_ready()):
            logger.warning("VAD 모델이 준비되지 않음, 폴백 모드로 전환")
            self.fallback_mode = True
            self._log_error(ErrorType.VAD_MODEL_ERROR, "VAD 모델 준비되지 않음")
        
        try:
            self.status.is_listening = True
            self.status.vad_status = "waiting"
            
            # 녹음 시작
            if not self.audio_recorder:
                raise RecordingError("오디오 레코더가 초기화되지 않았습니다")
            
            self.audio_recorder.start_recording()
            self.status.is_recording = True
            
            if self.fallback_mode:
                print("주문을 말씀해주세요. (간단한 볼륨 감지 모드)")
            else:
                print("주문을 말씀해주세요. 말씀을 시작하시면 자동으로 녹음됩니다.")
            
            # 실시간 상태 표시
            self._display_status()
            
            # 메인 루프
            frame_count = 0
            while self.status.is_listening:
                try:
                    # 오디오 프레임 읽기
                    audio_frame = self.audio_recorder.read_audio_frame()
                    if audio_frame is None:
                        logger.warning("오디오 프레임 읽기 실패")
                        break
                    
                    # 볼륨 레벨 계산
                    self.status.current_volume_level = float(np.abs(audio_frame).mean())
                    
                    # 음성 감지 (VAD 또는 폴백 모드)
                    if self.fallback_mode:
                        is_speech = self._detect_speech_fallback(audio_frame)
                    else:
                        audio_tensor = torch.from_numpy(audio_frame)
                        is_speech = self.vad_processor.detect_speech(audio_tensor)
                    
                    if is_speech:
                        self.status.vad_status = "detecting"
                        self.status.last_speech_detected = datetime.now()
                        logger.debug("🗣️ 음성 감지됨")
                    else:
                        if self.status.vad_status == "detecting":
                            self.status.vad_status = "recording"
                        logger.debug("🔇 무음")
                    
                    # 오디오 프레임 추가
                    self.audio_recorder.add_audio_frame(audio_frame, is_speech)
                    
                    # 주기적으로 상태 표시 업데이트
                    frame_count += 1
                    if frame_count % 10 == 0:  # 5초마다 (0.5초 * 10)
                        self._display_status()
                    
                    # 녹음 종료 조건 확인
                    should_stop, stop_reason = self.audio_recorder.should_stop_recording()
                    if should_stop:
                        print(f"\n{stop_reason}")
                        break
                        
                except KeyboardInterrupt:
                    print("\n사용자에 의해 중단되었습니다.")
                    break
                except Exception as e:
                    logger.error(f"오디오 처리 중 오류: {e}")
                    self._log_error(ErrorType.RECORDING_ERROR, f"오디오 처리 오류: {e}")
                    # 일시적 오류는 계속 진행
                    continue
            
            # 녹음 종료 및 파일 저장
            self.status.vad_status = "processing"
            print("녹음을 처리하는 중...")
            
            filename = self.audio_recorder.stop_recording()
            
            logger.info(f"마이크 입력 완료: {filename}")
            return filename
            
        except ValueError as e:
            logger.warning(f"녹음 길이 부족: {e}")
            self._log_error(ErrorType.RECORDING_ERROR, f"녹음 길이 부족: {e}")
            raise RecordingError(f"녹음이 너무 짧습니다: {e}")
        except (MicrophoneError, RecordingError, VADError):
            # 이미 처리된 커스텀 예외는 다시 발생
            raise
        except Exception as e:
            logger.error(f"마이크 입력 중 예상치 못한 오류 발생: {e}")
            self._log_error(ErrorType.UNKNOWN_ERROR, f"예상치 못한 오류: {e}")
            raise MicrophoneError(f"마이크 입력 실패: {e}")
        finally:
            self._cleanup()
    
    def _display_status(self) -> None:
        """실시간 상태 표시"""
        status_symbols = {
            "waiting": "⏳",
            "detecting": "🗣️",
            "recording": "🎙️",
            "processing": "⚙️"
        }
        
        symbol = status_symbols.get(self.status.vad_status, "❓")
        volume_bar = "█" * min(int(self.status.current_volume_level * 50), 10)
        
        print(f"\r{symbol} 상태: {self.status.vad_status} | 볼륨: {volume_bar:<10} | "
              f"{'폴백 모드' if self.fallback_mode else 'VAD 모드'}", end="", flush=True)
    
    def stop_listening(self) -> None:
        """마이크 입력 중단"""
        logger.info("마이크 입력 중단")
        self.status.is_listening = False
        self._cleanup()
    
    def get_microphone_status(self) -> Dict[str, Any]:
        """마이크 상태 반환"""
        recording_info = {}
        if self.audio_recorder:
            recording_info = self.audio_recorder.get_recording_info()
        
        hardware_status = self._check_hardware_availability()
        
        return {
            "is_listening": self.status.is_listening,
            "is_recording": self.status.is_recording,
            "current_volume_level": self.status.current_volume_level,
            "recording_duration": recording_info.get("recording_duration", 0.0),
            "vad_status": self.status.vad_status,
            "last_speech_detected": self.status.last_speech_detected.isoformat() if self.status.last_speech_detected else None,
            "vad_model_ready": self.vad_processor.is_model_ready() if self.vad_processor else False,
            "fallback_mode": self.fallback_mode,
            "hardware_available": hardware_status["available"],
            "recording_info": recording_info,
            "error_count": len(self.error_history),
            "last_error": self.error_history[-1] if self.error_history else None,
            "config": {
                "sample_rate": self.config.sample_rate,
                "vad_threshold": self.config.vad_threshold,
                "max_silence_duration_start": self.config.max_silence_duration_start,
                "max_silence_duration_end": self.config.max_silence_duration_end,
                "min_record_duration": self.config.min_record_duration
            }
        }
    
    def update_config(self, new_config: MicrophoneConfig) -> Dict[str, Any]:
        """설정 업데이트"""
        logger.info("마이크 설정 업데이트")
        
        try:
            # 설정 유효성 검증
            validation_result = self._validate_config(new_config)
            if not validation_result["valid"]:
                error_msg = f"잘못된 설정: {validation_result['errors']}"
                self._log_error(ErrorType.CONFIG_ERROR, error_msg)
                raise ValueError(error_msg)
            
            old_config = self.config
            self.config = new_config
            
            # 현재 녹음 중이면 중단
            if self.status.is_listening:
                logger.warning("설정 업데이트를 위해 현재 녹음을 중단합니다")
                self.stop_listening()
            
            # 새로운 설정으로 프로세서들 재초기화
            try:
                self._initialize_components()
                logger.info("설정 업데이트 및 컴포넌트 재초기화 완료")
                return {"success": True, "message": "설정이 성공적으로 업데이트되었습니다"}
                
            except Exception as e:
                # 초기화 실패 시 이전 설정으로 복원
                logger.error(f"컴포넌트 재초기화 실패, 이전 설정으로 복원: {e}")
                self.config = old_config
                self._initialize_components()
                error_msg = f"설정 업데이트 실패, 이전 설정으로 복원됨: {e}"
                self._log_error(ErrorType.CONFIG_ERROR, error_msg)
                return {"success": False, "message": error_msg}
                
        except Exception as e:
            error_msg = f"설정 업데이트 중 오류: {e}"
            logger.error(error_msg)
            self._log_error(ErrorType.CONFIG_ERROR, error_msg)
            return {"success": False, "message": error_msg}
    
    def _validate_config(self, config: MicrophoneConfig) -> Dict[str, Any]:
        """설정 유효성 검증"""
        errors = []
        
        if config.sample_rate <= 0 or config.sample_rate > 48000:
            errors.append("샘플레이트는 1-48000 범위여야 합니다")
        
        if config.frame_duration <= 0 or config.frame_duration > 5.0:
            errors.append("프레임 지속시간은 0-5초 범위여야 합니다")
        
        if config.max_silence_duration_start <= 0:
            errors.append("시작 최대 무음 시간은 양수여야 합니다")
        
        if config.max_silence_duration_end <= 0:
            errors.append("종료 최대 무음 시간은 양수여야 합니다")
        
        if config.min_record_duration <= 0:
            errors.append("최소 녹음 시간은 양수여야 합니다")
        
        if config.vad_threshold < 0 or config.vad_threshold > 1:
            errors.append("VAD 임계값은 0-1 범위여야 합니다")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
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
                int(test_duration * self.config.sample_rate),
                samplerate=self.config.sample_rate,
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
                "sample_rate": self.config.sample_rate,
                "test_duration": test_duration,
                "audio_detected": volume_level > 0.001  # 최소 볼륨 임계값
            }
            
            # 3. VAD 테스트
            if self.vad_processor and self.vad_processor.is_model_ready():
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
    
    def get_error_history(self) -> List[Dict[str, Any]]:
        """오류 기록 반환"""
        return self.error_history.copy()
    
    def clear_error_history(self) -> None:
        """오류 기록 초기화"""
        logger.info("오류 기록 초기화")
        self.error_history.clear()
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """진단 정보 반환"""
        return {
            "system_info": {
                "fallback_mode": self.fallback_mode,
                "components_initialized": {
                    "vad_processor": self.vad_processor is not None,
                    "audio_recorder": self.audio_recorder is not None
                }
            },
            "hardware_status": self._check_hardware_availability(),
            "vad_info": self.vad_processor.get_model_info() if self.vad_processor else {"model_loaded": False},
            "current_status": self.get_microphone_status(),
            "error_summary": {
                "total_errors": len(self.error_history),
                "error_types": list(set(e["error_type"] for e in self.error_history)),
                "recent_errors": self.error_history[-5:] if self.error_history else []
            }
        }
    
    def reset_system(self) -> Dict[str, Any]:
        """시스템 재설정"""
        logger.info("마이크 시스템 재설정")
        
        try:
            # 현재 작업 중단
            if self.status.is_listening:
                self.stop_listening()
            
            # 오류 기록 초기화
            self.clear_error_history()
            
            # 폴백 모드 해제
            self.fallback_mode = False
            
            # 컴포넌트 재초기화
            self._initialize_components()
            
            logger.info("시스템 재설정 완료")
            return {"success": True, "message": "시스템이 성공적으로 재설정되었습니다"}
            
        except Exception as e:
            error_msg = f"시스템 재설정 실패: {e}"
            logger.error(error_msg)
            self._log_error(ErrorType.UNKNOWN_ERROR, error_msg)
            return {"success": False, "message": error_msg}
    
    def _cleanup(self) -> None:
        """리소스 정리"""
        print()  # 상태 표시 줄바꿈
        self.status.is_listening = False
        self.status.is_recording = False
        self.status.vad_status = "waiting"
        if self.audio_recorder:
            self.audio_recorder.cleanup()
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self._cleanup()