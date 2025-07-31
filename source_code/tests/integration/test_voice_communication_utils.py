"""
음성 통신 통합 테스트 유틸리티
테스트에서 공통으로 사용되는 헬퍼 함수들
"""

import tempfile
import wave
import struct
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import requests
from unittest.mock import Mock

# 프로젝트 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.communication_models import ServerResponse, ErrorInfo, ErrorCode
from src.logger import get_logger

logger = get_logger(__name__)


class AudioFileGenerator:
    """테스트용 오디오 파일 생성기"""
    
    @staticmethod
    def create_wav_file(duration: float = 1.0, sample_rate: int = 16000, 
                       frequency: int = 440, amplitude: float = 0.3) -> str:
        """
        테스트용 WAV 파일 생성
        
        Args:
            duration: 파일 길이 (초)
            sample_rate: 샘플링 레이트
            frequency: 주파수 (Hz)
            amplitude: 진폭 (0.0 ~ 1.0)
            
        Returns:
            생성된 파일 경로
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # 모노
            wav_file.setsampwidth(2)  # 16비트
            wav_file.setframerate(sample_rate)
            
            # 사인파 생성
            frames = []
            for i in range(int(sample_rate * duration)):
                # 간단한 사각파 생성 (테스트용)
                value = int(32767 * amplitude * 
                           (1 if i % (sample_rate // frequency) < (sample_rate // frequency // 2) else -1))
                frames.append(struct.pack('<h', value))
            
            wav_file.writeframes(b''.join(frames))
        
        logger.debug(f"테스트용 WAV 파일 생성: {temp_file.name} ({duration}초, {sample_rate}Hz)")
        return temp_file.name
    
    @staticmethod
    def create_silent_wav_file(duration: float = 1.0, sample_rate: int = 16000) -> str:
        """
        무음 WAV 파일 생성
        
        Args:
            duration: 파일 길이 (초)
            sample_rate: 샘플링 레이트
            
        Returns:
            생성된 파일 경로
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            # 무음 데이터 생성
            silence_frames = b'\x00\x00' * int(sample_rate * duration)
            wav_file.writeframes(silence_frames)
        
        logger.debug(f"무음 WAV 파일 생성: {temp_file.name} ({duration}초)")
        return temp_file.name
    
    @staticmethod
    def create_invalid_wav_file(file_type: str = "empty") -> str:
        """
        잘못된 WAV 파일 생성
        
        Args:
            file_type: 파일 타입 ("empty", "text", "large", "corrupted")
            
        Returns:
            생성된 파일 경로
        """
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        if file_type == "empty":
            # 빈 파일
            pass
        elif file_type == "text":
            # 텍스트 파일
            temp_file.write(b"This is not a WAV file")
        elif file_type == "large":
            # 큰 파일 (15MB)
            temp_file.write(b'0' * (15 * 1024 * 1024))
        elif file_type == "corrupted":
            # 손상된 WAV 헤더
            temp_file.write(b"RIFF\x00\x00\x00\x00WAVE")
            temp_file.write(b"fmt \x00\x00\x00\x00")  # 잘못된 fmt 청크
        
        temp_file.close()
        logger.debug(f"잘못된 WAV 파일 생성: {temp_file.name} (타입: {file_type})")
        return temp_file.name


class MockServerResponse:
    """모의 서버 응답 생성기"""
    
    @staticmethod
    def create_success_response(processing_time: float = 1.0, 
                              session_id: str = None) -> Dict[str, Any]:
        """성공 응답 생성"""
        return {
            "success": True,
            "message": "음성 처리가 완료되었습니다",
            "processing_time": processing_time,
            "session_id": session_id,
            "tts_audio_url": "/api/voice/tts/test_file_id",
            "order_data": {
                "order_id": "test_order_123",
                "items": [
                    {
                        "name": "테스트 메뉴",
                        "quantity": 1,
                        "price": 5000,
                        "category": "테스트"
                    }
                ],
                "total_amount": 5000.0,
                "status": "pending",
                "requires_confirmation": False,
                "item_count": 1
            },
            "ui_actions": [
                {
                    "action_type": "update_order",
                    "data": {"message": "주문이 업데이트되었습니다"},
                    "priority": 1,
                    "requires_user_input": False,
                    "timeout_seconds": None
                }
            ],
            "timestamp": "2024-01-01T12:00:00"
        }
    
    @staticmethod
    def create_error_response(error_code: str = "server_error", 
                            error_message: str = "서버 오류가 발생했습니다") -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            "success": False,
            "message": error_message,
            "processing_time": 0.0,
            "error_info": {
                "error_code": error_code,
                "error_message": error_message,
                "recovery_actions": [
                    "잠시 후 다시 시도해주세요",
                    "문제가 지속되면 관리자에게 문의해주세요"
                ],
                "timestamp": "2024-01-01T12:00:00"
            },
            "ui_actions": [
                {
                    "action_type": "show_error",
                    "data": {
                        "error_message": error_message,
                        "recovery_actions": ["다시 시도해주세요"]
                    },
                    "priority": 0,
                    "requires_user_input": False,
                    "timeout_seconds": None
                }
            ],
            "timestamp": "2024-01-01T12:00:00"
        }


class TestMetrics:
    """테스트 메트릭 수집기"""
    
    def __init__(self):
        self.metrics = {
            "requests": [],
            "errors": [],
            "performance": {
                "response_times": [],
                "processing_times": [],
                "file_sizes": []
            }
        }
    
    def record_request(self, request_id: str, response_time: float, 
                      processing_time: float = 0.0, file_size: int = 0,
                      success: bool = True, error_message: str = None):
        """요청 메트릭 기록"""
        request_data = {
            "request_id": request_id,
            "timestamp": time.time(),
            "response_time": response_time,
            "processing_time": processing_time,
            "file_size": file_size,
            "success": success,
            "error_message": error_message
        }
        
        self.metrics["requests"].append(request_data)
        
        if success:
            self.metrics["performance"]["response_times"].append(response_time)
            self.metrics["performance"]["processing_times"].append(processing_time)
            self.metrics["performance"]["file_sizes"].append(file_size)
        else:
            self.metrics["errors"].append(request_data)
    
    def get_summary(self) -> Dict[str, Any]:
        """메트릭 요약 반환"""
        total_requests = len(self.metrics["requests"])
        successful_requests = len([r for r in self.metrics["requests"] if r["success"]])
        error_count = len(self.metrics["errors"])
        
        response_times = self.metrics["performance"]["response_times"]
        processing_times = self.metrics["performance"]["processing_times"]
        
        summary = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_count": error_count,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0
        }
        
        if response_times:
            summary["response_time_stats"] = {
                "min": min(response_times),
                "max": max(response_times),
                "avg": sum(response_times) / len(response_times),
                "count": len(response_times)
            }
        
        if processing_times:
            summary["processing_time_stats"] = {
                "min": min(processing_times),
                "max": max(processing_times),
                "avg": sum(processing_times) / len(processing_times),
                "count": len(processing_times)
            }
        
        return summary
    
    def export_to_file(self, file_path: str):
        """메트릭을 파일로 내보내기"""
        export_data = {
            "export_timestamp": time.time(),
            "metrics": self.metrics,
            "summary": self.get_summary()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"테스트 메트릭 내보내기 완료: {file_path}")


class TestEnvironmentManager:
    """테스트 환경 관리자"""
    
    def __init__(self):
        self.temp_files = []
        self.test_metrics = TestMetrics()
    
    def create_test_audio_file(self, duration: float = 1.0, 
                             file_type: str = "normal") -> str:
        """테스트용 오디오 파일 생성 및 관리"""
        if file_type == "normal":
            file_path = AudioFileGenerator.create_wav_file(duration)
        elif file_type == "silent":
            file_path = AudioFileGenerator.create_silent_wav_file(duration)
        else:
            file_path = AudioFileGenerator.create_invalid_wav_file(file_type)
        
        self.temp_files.append(file_path)
        return file_path
    
    def cleanup(self):
        """임시 파일 정리"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"임시 파일 삭제: {file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {file_path}, 오류: {e}")
        
        self.temp_files.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


def assert_response_structure(response_data: Dict[str, Any], 
                            expect_success: bool = True):
    """서버 응답 구조 검증"""
    required_fields = ['success', 'message', 'processing_time']
    
    for field in required_fields:
        assert field in response_data, f"필수 필드 누락: {field}"
    
    assert response_data['success'] == expect_success, \
        f"예상 성공 상태와 다름: {response_data['success']} != {expect_success}"
    
    if expect_success:
        # 성공 응답 검증
        if 'order_data' in response_data and response_data['order_data']:
            order_data = response_data['order_data']
            assert 'order_id' in order_data
            assert 'items' in order_data
            assert 'total_amount' in order_data
            assert 'status' in order_data
        
        if 'ui_actions' in response_data:
            for action in response_data['ui_actions']:
                assert 'action_type' in action
                assert 'data' in action
    else:
        # 오류 응답 검증
        assert 'error_info' in response_data, "오류 응답에 error_info 필드 누락"
        error_info = response_data['error_info']
        assert 'error_code' in error_info
        assert 'error_message' in error_info
        assert 'recovery_actions' in error_info


def assert_performance_requirements(response_time: float, 
                                  max_response_time: float = 3.0):
    """성능 요구사항 검증"""
    assert response_time <= max_response_time, \
        f"응답 시간 초과: {response_time:.2f}초 > {max_response_time}초"


def create_mock_client_session(responses: List[Dict[str, Any]]) -> Mock:
    """모의 클라이언트 세션 생성"""
    mock_session = Mock()
    
    # 응답 순서대로 반환하도록 설정
    response_iter = iter(responses)
    
    def mock_post(*args, **kwargs):
        try:
            response_data = next(response_iter)
            mock_response = Mock()
            mock_response.status_code = response_data.get('status_code', 200)
            mock_response.json.return_value = response_data.get('json', {})
            mock_response.content = response_data.get('content', b'')
            return mock_response
        except StopIteration:
            # 응답이 더 없으면 기본 성공 응답
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = MockServerResponse.create_success_response()
            return mock_response
    
    mock_session.post.side_effect = mock_post
    return mock_session


def wait_for_server_ready(server_url: str, timeout: int = 30) -> bool:
    """서버가 준비될 때까지 대기"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{server_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    logger.info(f"서버 준비 완료: {server_url}")
                    return True
        except Exception as e:
            logger.debug(f"서버 상태 확인 중: {e}")
        
        time.sleep(1)
    
    logger.error(f"서버 준비 타임아웃: {server_url}")
    return False


# 테스트 데이터 상수
TEST_AUDIO_DURATIONS = [0.5, 1.0, 2.0, 3.0]  # 다양한 길이의 테스트 파일
TEST_SAMPLE_RATES = [16000, 22050, 44100]  # 다양한 샘플링 레이트
TEST_FILE_SIZES = [1024, 10240, 102400, 1024000]  # 다양한 파일 크기 (bytes)

# 성능 테스트 기준값
PERFORMANCE_THRESHOLDS = {
    "max_response_time": 3.0,  # 최대 응답 시간 (초)
    "min_success_rate": 95.0,  # 최소 성공률 (%)
    "max_concurrent_requests": 50,  # 최대 동시 요청 수
    "max_error_rate": 5.0  # 최대 오류율 (%)
}