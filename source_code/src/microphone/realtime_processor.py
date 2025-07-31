"""
실시간 처리 및 상태 표시 모듈
"""
import time
import threading
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from src.logger import get_logger

logger = get_logger(__name__)


class RealTimeProcessor:
    """실시간 처리 및 상태 표시"""
    
    def __init__(self):
        self.is_running = False
        self.status_thread: Optional[threading.Thread] = None
        self.status_callback: Optional[Callable[[], Dict[str, Any]]] = None
        self.update_interval = 1.0  # 1초마다 업데이트
    
    def start_status_monitoring(self, status_callback: Callable[[], Dict[str, Any]]) -> None:
        """상태 모니터링 시작"""
        if self.is_running:
            logger.warning("상태 모니터링이 이미 실행 중입니다")
            return
        
        self.status_callback = status_callback
        self.is_running = True
        
        self.status_thread = threading.Thread(target=self._status_monitor_loop, daemon=True)
        self.status_thread.start()
        
        logger.info("실시간 상태 모니터링 시작")
    
    def stop_status_monitoring(self) -> None:
        """상태 모니터링 중단"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.status_thread and self.status_thread.is_alive():
            self.status_thread.join(timeout=2.0)
        
        logger.info("실시간 상태 모니터링 중단")
    
    def _status_monitor_loop(self) -> None:
        """상태 모니터링 루프"""
        while self.is_running:
            try:
                if self.status_callback:
                    status = self.status_callback()
                    self._display_detailed_status(status)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"상태 모니터링 중 오류: {e}")
                time.sleep(self.update_interval)
    
    def _display_detailed_status(self, status: Dict[str, Any]) -> None:
        """상세 상태 표시"""
        # 간단한 상태 표시 (실제 구현에서는 더 정교하게 할 수 있음)
        if status.get("is_listening"):
            vad_status = status.get("vad_status", "unknown")
            volume = status.get("current_volume_level", 0.0)
            duration = status.get("recording_duration", 0.0)
            
            status_line = f"[{datetime.now().strftime('%H:%M:%S')}] "
            status_line += f"상태: {vad_status} | "
            status_line += f"볼륨: {volume:.3f} | "
            status_line += f"시간: {duration:.1f}s"
            
            if status.get("fallback_mode"):
                status_line += " | 폴백모드"
            
            # 로그로만 기록 (콘솔 출력은 메인 스레드에서 처리)
            logger.debug(status_line)
    
    def set_update_interval(self, interval: float) -> None:
        """업데이트 간격 설정"""
        if interval > 0:
            self.update_interval = interval
            logger.info(f"상태 업데이트 간격을 {interval}초로 설정")
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop_status_monitoring()