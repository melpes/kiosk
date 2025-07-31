"""
클라이언트 모니터링 예제

클라이언트 측에서 통신 상태와 성능을 모니터링하는 예제입니다.
Requirements: 6.1, 6.2, 6.3, 6.4
"""

import time
import logging
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import deque
import statistics

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 클라이언트 모니터링 로거 설정
client_logger = logging.getLogger("voice_client_monitoring")
client_logger.setLevel(logging.INFO)

# 파일 핸들러 설정
file_handler = logging.FileHandler(LOG_DIR / "voice_client.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 포맷터 설정
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
client_logger.addHandler(file_handler)

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
client_logger.addHandler(console_handler)


@dataclass
class ClientRequestMetrics:
    """클라이언트 요청 메트릭"""
    request_id: str
    start_time: float
    file_upload_start: Optional[float] = None
    file_upload_end: Optional[float] = None
    response_received: Optional[float] = None
    end_time: Optional[float] = None
    file_size: Optional[int] = None
    response_size: Optional[int] = None
    status: str = "started"  # started, uploading, waiting, completed, error
    error_message: Optional[str] = None
    server_processing_time: Optional[float] = None
    
    def get_upload_time(self) -> Optional[float]:
        """파일 업로드 시간 계산"""
        if self.file_upload_start and self.file_upload_end:
            return self.file_upload_end - self.file_upload_start
        return None
    
    def get_waiting_time(self) -> Optional[float]:
        """서버 응답 대기 시간 계산"""
        if self.file_upload_end and self.response_received:
            return self.response_received - self.file_upload_end
        return None
    
    def get_total_time(self) -> Optional[float]:
        """전체 처리 시간 계산"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['upload_time'] = self.get_upload_time()
        data['waiting_time'] = self.get_waiting_time()
        data['total_time'] = self.get_total_time()
        return data


class ClientMonitor:
    """클라이언트 모니터링 클래스"""
    
    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self.active_requests: Dict[str, ClientRequestMetrics] = {}
        self.completed_requests: deque = deque(maxlen=max_history)
        self.error_requests: deque = deque(maxlen=max_history)
        self.lock = threading.Lock()
        
        # 통계 카운터
        self.total_requests = 0
        self.total_errors = 0
        self.connection_errors = 0
        self.timeout_errors = 0
    
    def start_request(self, request_id: str, file_size: Optional[int] = None) -> None:
        """
        요청 시작 모니터링
        Requirements: 6.1 - 파일 전송 시작 시간 기록
        """
        with self.lock:
            start_time = time.time()
            metrics = ClientRequestMetrics(
                request_id=request_id,
                start_time=start_time,
                file_size=file_size,
                status="started"
            )
            
            self.active_requests[request_id] = metrics
            self.total_requests += 1
            
            # 로그 기록
            client_logger.info(
                f"CLIENT_REQUEST_START - ID: {request_id}, "
                f"File Size: {file_size} bytes, Time: {datetime.fromtimestamp(start_time)}"
            )
    
    def start_file_upload(self, request_id: str) -> None:
        """파일 업로드 시작"""
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id].file_upload_start = time.time()
                self.active_requests[request_id].status = "uploading"
                
                client_logger.info(f"CLIENT_UPLOAD_START - ID: {request_id}")
    
    def complete_file_upload(self, request_id: str) -> None:
        """파일 업로드 완료"""
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id].file_upload_end = time.time()
                self.active_requests[request_id].status = "waiting"
                
                upload_time = self.active_requests[request_id].get_upload_time()
                client_logger.info(
                    f"CLIENT_UPLOAD_COMPLETE - ID: {request_id}, "
                    f"Upload Time: {upload_time:.3f}s"
                )
    
    def receive_response(self, request_id: str, response_size: Optional[int] = None,
                        server_processing_time: Optional[float] = None) -> None:
        """서버 응답 수신"""
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id].response_received = time.time()
                self.active_requests[request_id].response_size = response_size
                self.active_requests[request_id].server_processing_time = server_processing_time
                
                waiting_time = self.active_requests[request_id].get_waiting_time()
                client_logger.info(
                    f"CLIENT_RESPONSE_RECEIVED - ID: {request_id}, "
                    f"Waiting Time: {waiting_time:.3f}s, "
                    f"Server Processing: {server_processing_time:.3f}s, "
                    f"Response Size: {response_size} bytes"
                )
    
    def complete_request(self, request_id: str) -> None:
        """
        요청 완료
        Requirements: 6.2, 6.4 - 처리 시간 및 전체 처리 시간 기록
        """
        with self.lock:
            if request_id not in self.active_requests:
                client_logger.warning(f"CLIENT_REQUEST_NOT_FOUND - ID: {request_id}")
                return
            
            metrics = self.active_requests[request_id]
            metrics.end_time = time.time()
            metrics.status = "completed"
            
            total_time = metrics.get_total_time()
            upload_time = metrics.get_upload_time()
            waiting_time = metrics.get_waiting_time()
            
            # 완료된 요청으로 이동
            self.completed_requests.append(metrics)
            del self.active_requests[request_id]
            
            # 로그 기록
            client_logger.info(
                f"CLIENT_REQUEST_COMPLETE - ID: {request_id}, "
                f"Total Time: {total_time:.3f}s, "
                f"Upload: {upload_time:.3f}s, "
                f"Waiting: {waiting_time:.3f}s"
            )
    
    def log_error(self, request_id: str, error_message: str, error_type: str = "UNKNOWN") -> None:
        """
        오류 로깅
        Requirements: 6.3 - 오류 내용과 시간 기록
        """
        with self.lock:
            error_time = time.time()
            
            # 활성 요청에서 오류 정보 업데이트
            if request_id in self.active_requests:
                metrics = self.active_requests[request_id]
                metrics.end_time = error_time
                metrics.error_message = error_message
                metrics.status = "error"
                
                # 오류 요청으로 이동
                self.error_requests.append(metrics)
                del self.active_requests[request_id]
            else:
                # 새로운 오류 메트릭 생성
                metrics = ClientRequestMetrics(
                    request_id=request_id,
                    start_time=error_time,
                    end_time=error_time,
                    error_message=error_message,
                    status="error"
                )
                self.error_requests.append(metrics)
            
            self.total_errors += 1
            
            # 오류 타입별 카운터 업데이트
            if "connection" in error_type.lower() or "connection" in error_message.lower():
                self.connection_errors += 1
            elif "timeout" in error_type.lower() or "timeout" in error_message.lower():
                self.timeout_errors += 1
            
            # 로그 기록
            client_logger.error(
                f"CLIENT_ERROR - ID: {request_id}, Type: {error_type}, "
                f"Message: {error_message}, Time: {datetime.fromtimestamp(error_time)}"
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        with self.lock:
            recent_completed = list(self.completed_requests)[-50:]  # 최근 50개
            
            if not recent_completed:
                return {
                    "total_requests": self.total_requests,
                    "total_errors": self.total_errors,
                    "connection_errors": self.connection_errors,
                    "timeout_errors": self.timeout_errors,
                    "active_requests": len(self.active_requests),
                    "message": "충분한 데이터가 없습니다"
                }
            
            # 시간 통계 계산
            total_times = [r.get_total_time() for r in recent_completed if r.get_total_time()]
            upload_times = [r.get_upload_time() for r in recent_completed if r.get_upload_time()]
            waiting_times = [r.get_waiting_time() for r in recent_completed if r.get_waiting_time()]
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "connection_errors": self.connection_errors,
                "timeout_errors": self.timeout_errors,
                "active_requests": len(self.active_requests),
                "recent_requests_analyzed": len(recent_completed)
            }
            
            if total_times:
                stats["total_time_stats"] = {
                    "min": min(total_times),
                    "max": max(total_times),
                    "avg": statistics.mean(total_times),
                    "median": statistics.median(total_times)
                }
            
            if upload_times:
                stats["upload_time_stats"] = {
                    "min": min(upload_times),
                    "max": max(upload_times),
                    "avg": statistics.mean(upload_times),
                    "median": statistics.median(upload_times)
                }
            
            if waiting_times:
                stats["waiting_time_stats"] = {
                    "min": min(waiting_times),
                    "max": max(waiting_times),
                    "avg": statistics.mean(waiting_times),
                    "median": statistics.median(waiting_times)
                }
            
            return stats
    
    def export_client_logs(self, output_file: str) -> None:
        """클라이언트 로그 데이터 내보내기"""
        with self.lock:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "completed_requests": [req.to_dict() for req in self.completed_requests],
                "error_requests": [req.to_dict() for req in self.error_requests],
                "performance_stats": self.get_performance_stats()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            client_logger.info(f"CLIENT_LOGS_EXPORTED - File: {output_file}")


# 전역 클라이언트 모니터 인스턴스
client_monitor = ClientMonitor()


def get_client_monitor() -> ClientMonitor:
    """클라이언트 모니터 인스턴스 반환"""
    return client_monitor


# 모니터링 데코레이터
def monitor_request(func):
    """요청 모니터링 데코레이터"""
    def wrapper(*args, **kwargs):
        import uuid
        request_id = str(uuid.uuid4())
        monitor = get_client_monitor()
        
        try:
            # 파일 크기 추출 시도
            file_size = None
            if 'audio_file_path' in kwargs:
                try:
                    file_size = Path(kwargs['audio_file_path']).stat().st_size
                except:
                    pass
            
            monitor.start_request(request_id, file_size)
            result = func(*args, **kwargs)
            monitor.complete_request(request_id)
            return result
            
        except Exception as e:
            monitor.log_error(request_id, str(e), type(e).__name__)
            raise
    
    return wrapper


# 사용 예제
def example_usage():
    """모니터링 사용 예제"""
    monitor = get_client_monitor()
    
    # 요청 시뮬레이션
    request_id = "test_request_001"
    
    try:
        # 요청 시작
        monitor.start_request(request_id, file_size=1024000)  # 1MB 파일
        
        # 파일 업로드 시뮬레이션
        monitor.start_file_upload(request_id)
        time.sleep(0.5)  # 업로드 시간 시뮬레이션
        monitor.complete_file_upload(request_id)
        
        # 서버 응답 대기 시뮬레이션
        time.sleep(2.0)  # 서버 처리 시간 시뮬레이션
        
        # 응답 수신
        monitor.receive_response(request_id, response_size=2048, server_processing_time=1.8)
        
        # 요청 완료
        monitor.complete_request(request_id)
        
    except Exception as e:
        monitor.log_error(request_id, str(e))
    
    # 성능 통계 출력
    stats = monitor.get_performance_stats()
    print("=== 클라이언트 성능 통계 ===")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 로그 내보내기
    monitor.export_client_logs("client_monitoring_export.json")


if __name__ == "__main__":
    print("클라이언트 모니터링 예제 실행")
    example_usage()