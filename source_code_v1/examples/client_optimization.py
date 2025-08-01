"""
클라이언트 최적화 예제
연결 풀링, 파일 압축, 캐싱 등의 클라이언트 측 최적화 기능 시연
"""

import os
import sys
import time
import asyncio
import aiohttp
import gzip
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent))

from src.logger import get_logger
from src.models.communication_models import ServerResponse


@dataclass
class ClientOptimizationConfig:
    """클라이언트 최적화 설정"""
    # 연결 풀 설정
    max_connections: int = 10
    connection_timeout: int = 30
    read_timeout: int = 60
    
    # 압축 설정
    enable_compression: bool = True
    compression_threshold: int = 1024  # 바이트
    
    # 재시도 설정
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    
    # 캐싱 설정
    enable_response_cache: bool = True
    cache_ttl: int = 300  # 초
    max_cache_size: int = 100


class ResponseCache:
    """응답 캐싱 시스템"""
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.logger = get_logger(__name__)
    
    def _generate_key(self, file_path: str, session_id: Optional[str] = None) -> str:
        """캐시 키 생성"""
        # 파일 내용 기반 해시 생성 (간단한 예제)
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            import hashlib
            file_hash = hashlib.md5(content).hexdigest()
            return f"{file_hash}_{session_id or 'no_session'}"
        except Exception:
            return f"{file_path}_{session_id or 'no_session'}"
    
    def get(self, file_path: str, session_id: Optional[str] = None) -> Optional[ServerResponse]:
        """캐시에서 응답 조회"""
        key = self._generate_key(file_path, session_id)
        
        with self.lock:
            entry = self.cache.get(key)
            if not entry:
                return None
            
            # TTL 체크
            if datetime.now() - entry['timestamp'] > timedelta(seconds=self.ttl):
                del self.cache[key]
                return None
            
            self.logger.debug(f"캐시 히트: {key}")
            return entry['response']
    
    def put(self, file_path: str, response: ServerResponse, session_id: Optional[str] = None):
        """응답을 캐시에 저장"""
        key = self._generate_key(file_path, session_id)
        
        with self.lock:
            # 캐시 크기 제한
            if len(self.cache) >= self.max_size:
                # 가장 오래된 항목 제거
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
                del self.cache[oldest_key]
            
            self.cache[key] = {
                'response': response,
                'timestamp': datetime.now()
            }
            
            self.logger.debug(f"캐시 저장: {key}")


class OptimizedVoiceClient:
    """최적화된 음성 클라이언트"""
    
    def __init__(self, server_url: str, config: Optional[ClientOptimizationConfig] = None):
        self.server_url = server_url.rstrip('/')
        self.config = config or ClientOptimizationConfig()
        self.logger = get_logger(__name__)
        
        # 연결 풀 설정
        self.connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        # HTTP 세션 생성
        timeout = aiohttp.ClientTimeout(
            total=self.config.read_timeout,
            connect=self.config.connection_timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=timeout,
            headers={'User-Agent': 'OptimizedVoiceClient/1.0'}
        )
        
        # 응답 캐시
        self.response_cache = ResponseCache(
            max_size=self.config.max_cache_size,
            ttl=self.config.cache_ttl
        ) if self.config.enable_response_cache else None
        
        # 통계
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'compression_used': 0,
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'average_response_time': 0.0
        }
        self.stats_lock = threading.Lock()
        
        self.logger.info(f"최적화된 음성 클라이언트 초기화 완료: {server_url}")
    
    def compress_file(self, file_path: str) -> str:
        """파일 압축"""
        if not self.config.enable_compression:
            return file_path
        
        file_size = os.path.getsize(file_path)
        if file_size < self.config.compression_threshold:
            return file_path
        
        try:
            compressed_path = f"{file_path}.gz"
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            compressed_size = os.path.getsize(compressed_path)
            compression_ratio = compressed_size / file_size
            
            self.logger.info(f"파일 압축: {file_size} -> {compressed_size} bytes (압축률: {compression_ratio:.2f})")
            
            with self.stats_lock:
                self.stats['compression_used'] += 1
            
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"파일 압축 실패: {e}")
            return file_path
    
    async def send_audio_with_retry(self, audio_file_path: str, session_id: Optional[str] = None) -> ServerResponse:
        """재시도 로직이 포함된 음성 전송"""
        # 캐시 확인
        if self.response_cache:
            cached_response = self.response_cache.get(audio_file_path, session_id)
            if cached_response:
                with self.stats_lock:
                    self.stats['cache_hits'] += 1
                return cached_response
        
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._send_audio_request(audio_file_path, session_id)
                
                # 캐시에 저장
                if self.response_cache and response.success:
                    self.response_cache.put(audio_file_path, response, session_id)
                
                with self.stats_lock:
                    self.stats['successful_requests'] += 1
                
                return response
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"요청 실패 (시도 {attempt + 1}/{self.config.max_retries + 1}): {e}")
                
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (self.config.backoff_factor ** attempt)
                    await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        with self.stats_lock:
            self.stats['failed_requests'] += 1
        
        raise last_exception or Exception("모든 재시도 실패")   
 
    async def _send_audio_request(self, audio_file_path: str, session_id: Optional[str] = None) -> ServerResponse:
        """실제 음성 요청 전송"""
        start_time = time.time()
        
        with self.stats_lock:
            self.stats['total_requests'] += 1
        
        try:
            # 파일 압축
            compressed_file_path = self.compress_file(audio_file_path)
            
            # 파일 크기 통계
            file_size = os.path.getsize(compressed_file_path)
            with self.stats_lock:
                self.stats['total_bytes_sent'] += file_size
            
            # 멀티파트 폼 데이터 준비
            data = aiohttp.FormData()
            
            with open(compressed_file_path, 'rb') as f:
                data.add_field('audio_file', f, filename='audio.wav', content_type='audio/wav')
            
            if session_id:
                data.add_field('session_id', session_id)
            
            # 요청 전송
            async with self.session.post(f"{self.server_url}/api/voice/process", data=data) as response:
                response_data = await response.json()
                
                # 응답 크기 통계
                response_size = len(str(response_data))
                with self.stats_lock:
                    self.stats['total_bytes_received'] += response_size
                
                # 응답 시간 통계
                response_time = time.time() - start_time
                with self.stats_lock:
                    current_avg = self.stats['average_response_time']
                    total_requests = self.stats['total_requests']
                    self.stats['average_response_time'] = (current_avg * (total_requests - 1) + response_time) / total_requests
                
                if response.status == 200:
                    return ServerResponse(**response_data)
                else:
                    raise Exception(f"서버 오류: {response.status} - {response_data}")
            
        finally:
            # 압축 파일 정리
            if compressed_file_path != audio_file_path and os.path.exists(compressed_file_path):
                try:
                    os.remove(compressed_file_path)
                except Exception as e:
                    self.logger.warning(f"압축 파일 삭제 실패: {e}")
    
    async def batch_send_audio(self, audio_files: List[str], session_id: Optional[str] = None) -> List[ServerResponse]:
        """배치 음성 전송 (병렬 처리)"""
        self.logger.info(f"배치 음성 전송 시작: {len(audio_files)}개 파일")
        
        # 병렬 처리를 위한 태스크 생성
        tasks = []
        for audio_file in audio_files:
            task = asyncio.create_task(self.send_audio_with_retry(audio_file, session_id))
            tasks.append(task)
        
        # 모든 태스크 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 처리
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"파일 {audio_files[i]} 처리 실패: {result}")
                # 오류 응답 생성
                error_response = ServerResponse(
                    success=False,
                    message=f"처리 실패: {str(result)}",
                    tts_audio_url=None,
                    order_data=None,
                    ui_actions=[],
                    error_info=None,
                    processing_time=0.0
                )
                responses.append(error_response)
            else:
                responses.append(result)
        
        self.logger.info(f"배치 음성 전송 완료: {len(responses)}개 응답")
        return responses
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        with self.stats_lock:
            stats = self.stats.copy()
        
        # 추가 계산된 통계
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['successful_requests'] / stats['total_requests']) * 100
            stats['cache_hit_rate'] = (stats['cache_hits'] / stats['total_requests']) * 100 if self.response_cache else 0
            stats['compression_usage_rate'] = (stats['compression_used'] / stats['total_requests']) * 100
        else:
            stats['success_rate'] = 0
            stats['cache_hit_rate'] = 0
            stats['compression_usage_rate'] = 0
        
        # 네트워크 효율성
        if stats['total_bytes_sent'] > 0:
            stats['bytes_per_request'] = stats['total_bytes_sent'] / max(stats['total_requests'], 1)
        else:
            stats['bytes_per_request'] = 0
        
        return stats
    
    def reset_stats(self):
        """통계 초기화"""
        with self.stats_lock:
            self.stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cache_hits': 0,
                'compression_used': 0,
                'total_bytes_sent': 0,
                'total_bytes_received': 0,
                'average_response_time': 0.0
            }
        
        self.logger.info("성능 통계 초기화 완료")
    
    async def close(self):
        """클라이언트 종료"""
        await self.session.close()
        await self.connector.close()
        self.logger.info("최적화된 음성 클라이언트 종료")


class ConnectionPoolExample:
    """연결 풀링 예제"""
    
    def __init__(self, server_url: str, pool_size: int = 10):
        self.server_url = server_url
        self.pool_size = pool_size
        self.executor = ThreadPoolExecutor(max_workers=pool_size)
        self.logger = get_logger(__name__)
    
    async def demonstrate_connection_pooling(self, audio_files: List[str]):
        """연결 풀링 시연"""
        self.logger.info(f"연결 풀링 시연 시작: {len(audio_files)}개 파일, 풀 크기: {self.pool_size}")
        
        # 최적화된 클라이언트 생성
        config = ClientOptimizationConfig(
            max_connections=self.pool_size,
            enable_compression=True,
            enable_response_cache=True
        )
        
        client = OptimizedVoiceClient(self.server_url, config)
        
        try:
            start_time = time.time()
            
            # 배치 처리
            responses = await client.batch_send_audio(audio_files)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 결과 분석
            successful_responses = sum(1 for r in responses if r.success)
            
            self.logger.info(f"연결 풀링 시연 완료:")
            self.logger.info(f"  - 총 처리 시간: {total_time:.2f}초")
            self.logger.info(f"  - 성공한 요청: {successful_responses}/{len(responses)}")
            self.logger.info(f"  - 평균 처리 시간: {total_time/len(audio_files):.2f}초/파일")
            
            # 성능 통계 출력
            stats = client.get_performance_stats()
            self.logger.info(f"성능 통계: {stats}")
            
            return responses
            
        finally:
            await client.close()
    
    def shutdown(self):
        """연결 풀 종료"""
        self.executor.shutdown(wait=True)
        self.logger.info("연결 풀 종료 완료")


async def demonstrate_client_optimization():
    """클라이언트 최적화 기능 시연"""
    logger = get_logger(__name__)
    
    # 서버 URL 설정
    server_url = os.getenv('VOICE_SERVER_URL', 'http://localhost:8000')
    
    # 테스트용 음성 파일 경로 (실제 파일이 있다고 가정)
    test_audio_files = [
        "data/bigorder.wav",  # 실제 파일 경로로 변경 필요
    ]
    
    # 존재하는 파일만 필터링
    existing_files = [f for f in test_audio_files if os.path.exists(f)]
    
    if not existing_files:
        logger.warning("테스트용 음성 파일이 없습니다. 시연을 건너뜁니다.")
        return
    
    logger.info("=== 클라이언트 최적화 기능 시연 시작 ===")
    
    # 1. 기본 최적화 클라이언트 테스트
    logger.info("\n1. 기본 최적화 클라이언트 테스트")
    
    config = ClientOptimizationConfig(
        enable_compression=True,
        enable_response_cache=True,
        max_retries=2
    )
    
    client = OptimizedVoiceClient(server_url, config)
    
    try:
        # 단일 파일 전송
        response = await client.send_audio_with_retry(existing_files[0])
        logger.info(f"응답: {response.message}")
        
        # 같은 파일 다시 전송 (캐시 테스트)
        response2 = await client.send_audio_with_retry(existing_files[0])
        logger.info(f"캐시된 응답: {response2.message}")
        
        # 성능 통계 출력
        stats = client.get_performance_stats()
        logger.info(f"성능 통계: {stats}")
        
    finally:
        await client.close()
    
    # 2. 연결 풀링 시연
    logger.info("\n2. 연결 풀링 시연")
    
    pool_example = ConnectionPoolExample(server_url, pool_size=5)
    
    try:
        # 여러 파일을 동시에 처리 (같은 파일을 여러 번 사용)
        test_files = existing_files * 3  # 파일을 3번 반복
        await pool_example.demonstrate_connection_pooling(test_files)
        
    finally:
        pool_example.shutdown()
    
    logger.info("=== 클라이언트 최적화 기능 시연 완료 ===")


def main():
    """메인 함수"""
    logger = get_logger(__name__)
    
    try:
        # 비동기 시연 실행
        asyncio.run(demonstrate_client_optimization())
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"시연 중 오류 발생: {e}")


if __name__ == "__main__":
    main()