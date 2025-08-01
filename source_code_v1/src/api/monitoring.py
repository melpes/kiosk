"""
API 모니터링 시스템

통신 상태와 처리 성능을 추적하기 위한 로깅 및 모니터링 기능을 제공합니다.
Requirements: 6.1, 6.2, 6.3, 6.4
"""

import time
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import defaultdict, deque
import statistics

# 로그 디렉토리 생성
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 모니터링 로거 설정
monitoring_logger = logging.getLogger("voice_communication_monitoring")
monitoring_logger.setLevel(logging.INFO)

# 파일 핸들러 설정
file_handler = logging.FileHandler(LOG_DIR / "voice_communication.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 포맷터 설정
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
monitoring_logger.addHandler(file_handler)

# 콘솔 핸들러 추가 (선택적)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)
monitoring_logger.addHandler(console_handler)


@dataclass
class RequestMetrics:
    """요청 메트릭 데이터"""
    request_id: str
    client_ip: str
    start_time: float
    end_time: Optional[float] = None
    file_size: Optional[int] = None
    processing_time: Optional[float] = None
    status: str = "started"  # started, processing, completed, error
    error_message: Optional[str] = None
    response_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)
    
    def get_total_time(self) -> Optional[float]:
        """전체 처리 시간 계산"""
        if self.end_time:
            return self.end_time - self.start_time
        return None


@dataclass
class SystemMetrics:
    """시스템 메트릭 데이터"""
    timestamp: float
    active_requests: int
    total_requests: int
    error_count: int
    avg_processing_time: float
    avg_response_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


class CommunicationMonitor:
    """통신 모니터링 클래스"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.active_requests: Dict[str, RequestMetrics] = {}
        self.completed_requests: deque = deque(maxlen=max_history)
        self.error_requests: deque = deque(maxlen=max_history)
        self.system_metrics_history: deque = deque(maxlen=100)
        self.lock = threading.Lock()
        
        # 통계 카운터
        self.total_requests = 0
        self.total_errors = 0
        
    def start_request(self, request_id: str, client_ip: str, file_size: Optional[int] = None) -> None:
        """
        요청 시작 로깅
        Requirements: 6.1 - 파일 전송 시작 시간 기록
        """
        with self.lock:
            start_time = time.time()
            metrics = RequestMetrics(
                request_id=request_id,
                client_ip=client_ip,
                start_time=start_time,
                file_size=file_size,
                status="started"
            )
            
            self.active_requests[request_id] = metrics
            self.total_requests += 1
            
            # 로그 기록
            monitoring_logger.info(
                f"REQUEST_START - ID: {request_id}, Client: {client_ip}, "
                f"File Size: {file_size} bytes, Time: {datetime.fromtimestamp(start_time)}"
            )
    
    def update_processing_status(self, request_id: str) -> None:
        """처리 상태 업데이트"""
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id].status = "processing"
                
                monitoring_logger.info(
                    f"REQUEST_PROCESSING - ID: {request_id}"
                )
    
    def complete_request(self, request_id: str, processing_time: float, 
                        response_size: Optional[int] = None) -> None:
        """
        요청 완료 로깅
        Requirements: 6.2, 6.4 - 처리 시간 및 전체 처리 시간 기록
        """
        with self.lock:
            if request_id not in self.active_requests:
                monitoring_logger.warning(f"REQUEST_NOT_FOUND - ID: {request_id}")
                return
            
            metrics = self.active_requests[request_id]
            metrics.end_time = time.time()
            metrics.processing_time = processing_time
            metrics.response_size = response_size
            metrics.status = "completed"
            
            total_time = metrics.get_total_time()
            
            # 완료된 요청으로 이동
            self.completed_requests.append(metrics)
            del self.active_requests[request_id]
            
            # 로그 기록
            monitoring_logger.info(
                f"REQUEST_COMPLETE - ID: {request_id}, "
                f"Processing Time: {processing_time:.3f}s, "
                f"Total Time: {total_time:.3f}s, "
                f"Response Size: {response_size} bytes"
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
                metrics = RequestMetrics(
                    request_id=request_id,
                    client_ip="unknown",
                    start_time=error_time,
                    end_time=error_time,
                    error_message=error_message,
                    status="error"
                )
                self.error_requests.append(metrics)
            
            self.total_errors += 1
            
            # 로그 기록
            monitoring_logger.error(
                f"REQUEST_ERROR - ID: {request_id}, Type: {error_type}, "
                f"Message: {error_message}, Time: {datetime.fromtimestamp(error_time)}"
            )
    
    def get_current_metrics(self) -> SystemMetrics:
        """현재 시스템 메트릭 조회"""
        with self.lock:
            # 최근 완료된 요청들의 평균 처리 시간 계산
            recent_completed = list(self.completed_requests)[-50:]  # 최근 50개
            
            if recent_completed:
                processing_times = [r.processing_time for r in recent_completed if r.processing_time]
                response_times = [r.get_total_time() for r in recent_completed if r.get_total_time()]
                
                avg_processing_time = statistics.mean(processing_times) if processing_times else 0.0
                avg_response_time = statistics.mean(response_times) if response_times else 0.0
            else:
                avg_processing_time = 0.0
                avg_response_time = 0.0
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                active_requests=len(self.active_requests),
                total_requests=self.total_requests,
                error_count=self.total_errors,
                avg_processing_time=avg_processing_time,
                avg_response_time=avg_response_time
            )
            
            self.system_metrics_history.append(metrics)
            return metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        with self.lock:
            current_metrics = self.get_current_metrics()
            
            # 최근 요청들 분석
            recent_completed = list(self.completed_requests)[-100:]
            recent_errors = list(self.error_requests)[-50:]
            
            # 처리 시간 통계
            processing_times = [r.processing_time for r in recent_completed if r.processing_time]
            response_times = [r.get_total_time() for r in recent_completed if r.get_total_time()]
            
            processing_stats = {}
            response_stats = {}
            
            if processing_times:
                processing_stats = {
                    "min": min(processing_times),
                    "max": max(processing_times),
                    "avg": statistics.mean(processing_times),
                    "median": statistics.median(processing_times)
                }
            
            if response_times:
                response_stats = {
                    "min": min(response_times),
                    "max": max(response_times),
                    "avg": statistics.mean(response_times),
                    "median": statistics.median(response_times)
                }
            
            # 오류 분석
            error_types = defaultdict(int)
            for error_req in recent_errors:
                if error_req.error_message:
                    # 간단한 오류 타입 분류
                    if "timeout" in error_req.error_message.lower():
                        error_types["timeout"] += 1
                    elif "connection" in error_req.error_message.lower():
                        error_types["connection"] += 1
                    elif "file" in error_req.error_message.lower():
                        error_types["file"] += 1
                    else:
                        error_types["other"] += 1
            
            return {
                "timestamp": datetime.fromtimestamp(current_metrics.timestamp).isoformat(),
                "current_metrics": current_metrics.to_dict(),
                "processing_time_stats": processing_stats,
                "response_time_stats": response_stats,
                "error_analysis": dict(error_types),
                "recent_requests_count": len(recent_completed),
                "recent_errors_count": len(recent_errors)
            }
    
    def export_logs(self, output_file: str) -> None:
        """로그 데이터를 JSON 파일로 내보내기"""
        with self.lock:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "completed_requests": [req.to_dict() for req in self.completed_requests],
                "error_requests": [req.to_dict() for req in self.error_requests],
                "system_metrics": [metrics.to_dict() for metrics in self.system_metrics_history],
                "performance_report": self.get_performance_report()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            monitoring_logger.info(f"LOGS_EXPORTED - File: {output_file}")


# 전역 모니터 인스턴스
communication_monitor = CommunicationMonitor()


def get_monitor() -> CommunicationMonitor:
    """모니터 인스턴스 반환"""
    return communication_monitor


# 알림 시스템
class AlertManager:
    """알림 관리 클래스"""
    
    def __init__(self, error_threshold: int = 10, response_time_threshold: float = 5.0):
        self.error_threshold = error_threshold
        self.response_time_threshold = response_time_threshold
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5분 쿨다운
    
    def check_alerts(self, monitor: CommunicationMonitor) -> List[str]:
        """알림 조건 확인"""
        alerts = []
        current_time = time.time()
        
        # 오류 임계값 확인
        recent_errors = len([req for req in monitor.error_requests 
                           if current_time - req.start_time < 3600])  # 1시간 내
        
        if recent_errors >= self.error_threshold:
            alert_key = "high_error_rate"
            if (alert_key not in self.last_alert_time or 
                current_time - self.last_alert_time[alert_key] > self.alert_cooldown):
                
                alerts.append(f"높은 오류율 감지: 최근 1시간 내 {recent_errors}개 오류")
                self.last_alert_time[alert_key] = current_time
        
        # 응답 시간 임계값 확인
        metrics = monitor.get_current_metrics()
        if metrics.avg_response_time > self.response_time_threshold:
            alert_key = "slow_response"
            if (alert_key not in self.last_alert_time or 
                current_time - self.last_alert_time[alert_key] > self.alert_cooldown):
                
                alerts.append(f"느린 응답 시간 감지: 평균 {metrics.avg_response_time:.2f}초")
                self.last_alert_time[alert_key] = current_time
        
        # 알림 로깅
        for alert in alerts:
            monitoring_logger.warning(f"ALERT - {alert}")
        
        return alerts


# 전역 알림 관리자
alert_manager = AlertManager()


def get_alert_manager() -> AlertManager:
    """알림 관리자 인스턴스 반환"""
    return alert_manager