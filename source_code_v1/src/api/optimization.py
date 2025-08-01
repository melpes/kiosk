"""
서버 성능 최적화 기능 구현
음성 파일 압축, TTS 캐싱, 연결 풀링 등의 최적화 기능 제공
"""

import os
import gzip
import hashlib
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import wave
import io

from ..logger import get_logger


@dataclass
class CompressionConfig:
    """파일 압축 설정"""
    enabled: bool = True
    compression_level: int = 6  # gzip 압축 레벨 (1-9)
    min_file_size: int = 1024  # 최소 압축 대상 파일 크기 (바이트)
    audio_quality_reduction: bool = False  # 오디오 품질 감소 허용 여부
    target_bitrate: int = 16000  # 목표 비트레이트 (Hz)


@dataclass
class CacheConfig:
    """캐시 설정"""
    enabled: bool = True
    max_cache_size: int = 100  # 최대 캐시 항목 수
    ttl_seconds: int = 3600  # 캐시 TTL (초)
    cleanup_interval: int = 300  # 정리 주기 (초)
    memory_limit_mb: int = 500  # 메모리 사용 제한 (MB)


@dataclass
class ConnectionPoolConfig:
    """연결 풀 설정"""
    max_workers: int = 10  # 최대 워커 수
    queue_size: int = 100  # 큐 크기
    timeout_seconds: int = 30  # 타임아웃 (초)
    keepalive_enabled: bool = True  # Keep-alive 활성화


@dataclass
class CacheEntry:
    """캐시 항목"""
    key: str
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0


class AudioCompressor:
    """음성 파일 압축 클래스"""
    
    def __init__(self, config: CompressionConfig):
        self.config = config
        self.logger = get_logger(__name__)
    
    def compress_audio_file(self, file_path: str) -> Tuple[str, float]:
        """
        음성 파일 압축
        
        Args:
            file_path: 원본 파일 경로
            
        Returns:
            Tuple[압축된 파일 경로, 압축률]
        """
        if not self.config.enabled:
            return file_path, 1.0
        
        try:
            original_size = os.path.getsize(file_path)
            
            # 최소 크기 체크
            if original_size < self.config.min_file_size:
                return file_path, 1.0
            
            # 압축 파일 경로 생성
            compressed_path = f"{file_path}.gz"
            
            # gzip 압축
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=self.config.compression_level) as f_out:
                    f_out.write(f_in.read())
            
            compressed_size = os.path.getsize(compressed_path)
            compression_ratio = compressed_size / original_size
            
            self.logger.info(f"파일 압축 완료: {original_size} -> {compressed_size} bytes (압축률: {compression_ratio:.2f})")
            
            return compressed_path, compression_ratio
            
        except Exception as e:
            self.logger.error(f"파일 압축 실패: {e}")
            return file_path, 1.0
    
    def decompress_audio_file(self, compressed_path: str) -> str:
        """
        압축된 음성 파일 해제
        
        Args:
            compressed_path: 압축된 파일 경로
            
        Returns:
            해제된 파일 경로
        """
        if not compressed_path.endswith('.gz'):
            return compressed_path
        
        try:
            # 해제된 파일 경로 생성
            decompressed_path = compressed_path[:-3]  # .gz 제거
            
            # gzip 해제
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            self.logger.info(f"파일 압축 해제 완료: {compressed_path} -> {decompressed_path}")
            
            return decompressed_path
            
        except Exception as e:
            self.logger.error(f"파일 압축 해제 실패: {e}")
            return compressed_path
    
    def reduce_audio_quality(self, file_path: str) -> str:
        """
        오디오 품질 감소를 통한 파일 크기 최적화
        
        Args:
            file_path: 원본 파일 경로
            
        Returns:
            최적화된 파일 경로
        """
        if not self.config.audio_quality_reduction:
            return file_path
        
        try:
            # WAV 파일 읽기
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                params = wav_file.getparams()
            
            # 샘플레이트 변경이 필요한 경우
            if params.framerate > self.config.target_bitrate:
                # 새 파일 경로 생성
                optimized_path = file_path.replace('.wav', '_optimized.wav')
                
                # 새 파라미터 설정
                new_params = params._replace(framerate=self.config.target_bitrate)
                
                # 최적화된 파일 저장
                with wave.open(optimized_path, 'wb') as wav_file:
                    wav_file.setparams(new_params)
                    wav_file.writeframes(frames)
                
                original_size = os.path.getsize(file_path)
                optimized_size = os.path.getsize(optimized_path)
                
                self.logger.info(f"오디오 품질 최적화 완료: {original_size} -> {optimized_size} bytes")
                
                return optimized_path
            
            return file_path
            
        except Exception as e:
            self.logger.error(f"오디오 품질 최적화 실패: {e}")
            return file_path


class TTSCache:
    """TTS 파일 캐싱 시스템"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.RLock()
        self.logger = get_logger(__name__)
        self.total_size_bytes = 0
        
        # 백그라운드 정리 작업 시작
        if self.config.enabled:
            self._start_cleanup_task()
    
    def _generate_cache_key(self, text: str, voice_config: Dict[str, Any]) -> str:
        """
        캐시 키 생성
        
        Args:
            text: TTS 텍스트
            voice_config: 음성 설정
            
        Returns:
            캐시 키
        """
        # 텍스트와 설정을 조합하여 해시 생성
        content = f"{text}_{str(sorted(voice_config.items()))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, text: str, voice_config: Dict[str, Any]) -> Optional[str]:
        """
        캐시에서 TTS 파일 경로 조회
        
        Args:
            text: TTS 텍스트
            voice_config: 음성 설정
            
        Returns:
            캐시된 파일 경로 (없으면 None)
        """
        if not self.config.enabled:
            return None
        
        cache_key = self._generate_cache_key(text, voice_config)
        
        with self.cache_lock:
            entry = self.cache.get(cache_key)
            if entry is None:
                return None
            
            # TTL 체크
            if datetime.now() - entry.created_at > timedelta(seconds=self.config.ttl_seconds):
                self._remove_entry(cache_key)
                return None
            
            # 파일 존재 체크
            if not os.path.exists(entry.data):
                self._remove_entry(cache_key)
                return None
            
            # 액세스 정보 업데이트
            entry.last_accessed = datetime.now()
            entry.access_count += 1
            
            self.logger.debug(f"캐시 히트: {cache_key}")
            return entry.data
    
    def put(self, text: str, voice_config: Dict[str, Any], file_path: str) -> bool:
        """
        TTS 파일을 캐시에 저장
        
        Args:
            text: TTS 텍스트
            voice_config: 음성 설정
            file_path: TTS 파일 경로
            
        Returns:
            저장 성공 여부
        """
        if not self.config.enabled:
            return False
        
        try:
            cache_key = self._generate_cache_key(text, voice_config)
            file_size = os.path.getsize(file_path)
            
            with self.cache_lock:
                # 메모리 제한 체크
                if self._check_memory_limit(file_size):
                    self._evict_entries()
                
                # 캐시 크기 제한 체크
                if len(self.cache) >= self.config.max_cache_size:
                    self._evict_lru_entry()
                
                # 캐시 항목 생성
                entry = CacheEntry(
                    key=cache_key,
                    data=file_path,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    size_bytes=file_size
                )
                
                self.cache[cache_key] = entry
                self.total_size_bytes += file_size
                
                self.logger.debug(f"캐시 저장: {cache_key} ({file_size} bytes)")
                return True
                
        except Exception as e:
            self.logger.error(f"캐시 저장 실패: {e}")
            return False
    
    def _check_memory_limit(self, additional_size: int) -> bool:
        """메모리 제한 체크"""
        memory_limit_bytes = self.config.memory_limit_mb * 1024 * 1024
        return (self.total_size_bytes + additional_size) > memory_limit_bytes
    
    def _evict_entries(self):
        """메모리 제한 초과 시 항목 제거"""
        # 가장 오래된 항목부터 제거
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        target_size = self.config.memory_limit_mb * 1024 * 1024 * 0.8  # 80%까지 줄이기
        
        for cache_key, entry in sorted_entries:
            if self.total_size_bytes <= target_size:
                break
            self._remove_entry(cache_key)
    
    def _evict_lru_entry(self):
        """LRU 항목 제거"""
        if not self.cache:
            return
        
        # 가장 오래 사용되지 않은 항목 찾기
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        self._remove_entry(lru_key)
    
    def _remove_entry(self, cache_key: str):
        """캐시 항목 제거"""
        entry = self.cache.pop(cache_key, None)
        if entry:
            self.total_size_bytes -= entry.size_bytes
            # 파일 삭제 (선택적)
            try:
                if os.path.exists(entry.data):
                    os.remove(entry.data)
            except Exception as e:
                self.logger.warning(f"캐시 파일 삭제 실패: {e}")
    
    def _start_cleanup_task(self):
        """백그라운드 정리 작업 시작"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(self.config.cleanup_interval)
                    self._cleanup_expired_entries()
                except Exception as e:
                    self.logger.error(f"캐시 정리 작업 오류: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.info("TTS 캐시 정리 작업 시작")
    
    def _cleanup_expired_entries(self):
        """만료된 캐시 항목 정리"""
        current_time = datetime.now()
        expired_keys = []
        
        with self.cache_lock:
            for cache_key, entry in self.cache.items():
                if current_time - entry.created_at > timedelta(seconds=self.config.ttl_seconds):
                    expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                self._remove_entry(cache_key)
        
        if expired_keys:
            self.logger.info(f"만료된 캐시 항목 {len(expired_keys)}개 정리 완료")
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        with self.cache_lock:
            total_access_count = sum(entry.access_count for entry in self.cache.values())
            
            return {
                "total_entries": len(self.cache),
                "total_size_mb": self.total_size_bytes / (1024 * 1024),
                "total_access_count": total_access_count,
                "memory_usage_percent": (self.total_size_bytes / (self.config.memory_limit_mb * 1024 * 1024)) * 100,
                "config": {
                    "max_cache_size": self.config.max_cache_size,
                    "ttl_seconds": self.config.ttl_seconds,
                    "memory_limit_mb": self.config.memory_limit_mb
                }
            }
    
    def clear(self):
        """캐시 전체 삭제"""
        with self.cache_lock:
            for entry in self.cache.values():
                try:
                    if os.path.exists(entry.data):
                        os.remove(entry.data)
                except Exception as e:
                    self.logger.warning(f"캐시 파일 삭제 실패: {e}")
            
            self.cache.clear()
            self.total_size_bytes = 0
            
        self.logger.info("TTS 캐시 전체 삭제 완료")


class ConnectionPool:
    """연결 풀 및 큐잉 시스템"""
    
    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.request_queue = asyncio.Queue(maxsize=config.queue_size)
        self.active_connections = 0
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.queue_lock = threading.Lock()
        self.logger = get_logger(__name__)
        
        self.logger.info(f"연결 풀 초기화 완료 (최대 워커: {config.max_workers}, 큐 크기: {config.queue_size})")
    
    async def submit_task(self, func, *args, **kwargs):
        """
        작업을 풀에 제출
        
        Args:
            func: 실행할 함수
            *args: 함수 인수
            **kwargs: 함수 키워드 인수
            
        Returns:
            작업 결과
        """
        with self.queue_lock:
            self.total_requests += 1
        
        try:
            # 큐가 가득 찬 경우 대기
            if self.request_queue.full():
                self.logger.warning("요청 큐가 가득 참, 대기 중...")
            
            # 작업 실행
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(self.executor, func, *args, **kwargs)
            
            # 타임아웃 적용
            result = await asyncio.wait_for(future, timeout=self.config.timeout_seconds)
            
            with self.queue_lock:
                self.completed_requests += 1
            
            return result
            
        except asyncio.TimeoutError:
            with self.queue_lock:
                self.failed_requests += 1
            self.logger.error(f"작업 타임아웃: {self.config.timeout_seconds}초")
            raise
            
        except Exception as e:
            with self.queue_lock:
                self.failed_requests += 1
            self.logger.error(f"작업 실행 실패: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 풀 통계 반환"""
        with self.queue_lock:
            return {
                "max_workers": self.config.max_workers,
                "active_connections": self.active_connections,
                "queue_size": self.request_queue.qsize(),
                "max_queue_size": self.config.queue_size,
                "total_requests": self.total_requests,
                "completed_requests": self.completed_requests,
                "failed_requests": self.failed_requests,
                "success_rate": (self.completed_requests / max(self.total_requests, 1)) * 100,
                "config": {
                    "max_workers": self.config.max_workers,
                    "queue_size": self.config.queue_size,
                    "timeout_seconds": self.config.timeout_seconds,
                    "keepalive_enabled": self.config.keepalive_enabled
                }
            }
    
    def shutdown(self):
        """연결 풀 종료"""
        self.executor.shutdown(wait=True)
        self.logger.info("연결 풀 종료 완료")


class OptimizationManager:
    """통합 최적화 관리자"""
    
    def __init__(self,
                 compression_config: Optional[CompressionConfig] = None,
                 cache_config: Optional[CacheConfig] = None,
                 connection_config: Optional[ConnectionPoolConfig] = None):
        """
        최적화 관리자 초기화
        
        Args:
            compression_config: 압축 설정
            cache_config: 캐시 설정
            connection_config: 연결 풀 설정
        """
        self.logger = get_logger(__name__)
        
        # 기본 설정 적용
        self.compression_config = compression_config or CompressionConfig()
        self.cache_config = cache_config or CacheConfig()
        self.connection_config = connection_config or ConnectionPoolConfig()
        
        # 컴포넌트 초기화
        self.compressor = AudioCompressor(self.compression_config)
        self.tts_cache = TTSCache(self.cache_config)
        self.connection_pool = ConnectionPool(self.connection_config)
        
        self.logger.info("최적화 관리자 초기화 완료")
    
    def optimize_audio_file(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        음성 파일 최적화
        
        Args:
            file_path: 원본 파일 경로
            
        Returns:
            Tuple[최적화된 파일 경로, 최적화 정보]
        """
        optimization_info = {
            "original_size": os.path.getsize(file_path),
            "compression_applied": False,
            "quality_reduction_applied": False,
            "final_size": 0,
            "optimization_ratio": 1.0
        }
        
        try:
            # 품질 감소 적용
            optimized_path = self.compressor.reduce_audio_quality(file_path)
            if optimized_path != file_path:
                optimization_info["quality_reduction_applied"] = True
            
            # 압축 적용
            compressed_path, compression_ratio = self.compressor.compress_audio_file(optimized_path)
            if compressed_path != optimized_path:
                optimization_info["compression_applied"] = True
            
            # 최종 정보 업데이트
            optimization_info["final_size"] = os.path.getsize(compressed_path)
            optimization_info["optimization_ratio"] = optimization_info["final_size"] / optimization_info["original_size"]
            
            self.logger.info(f"파일 최적화 완료: {optimization_info}")
            
            return compressed_path, optimization_info
            
        except Exception as e:
            self.logger.error(f"파일 최적화 실패: {e}")
            return file_path, optimization_info
    
    def get_cached_tts(self, text: str, voice_config: Dict[str, Any]) -> Optional[str]:
        """캐시된 TTS 파일 조회"""
        return self.tts_cache.get(text, voice_config)
    
    def cache_tts_file(self, text: str, voice_config: Dict[str, Any], file_path: str) -> bool:
        """TTS 파일 캐시 저장"""
        return self.tts_cache.put(text, voice_config, file_path)
    
    async def execute_with_pool(self, func, *args, **kwargs):
        """연결 풀을 사용한 작업 실행"""
        return await self.connection_pool.submit_task(func, *args, **kwargs)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """전체 최적화 통계 반환"""
        return {
            "compression": {
                "enabled": self.compression_config.enabled,
                "compression_level": self.compression_config.compression_level,
                "min_file_size": self.compression_config.min_file_size,
                "audio_quality_reduction": self.compression_config.audio_quality_reduction
            },
            "cache": self.tts_cache.get_stats(),
            "connection_pool": self.connection_pool.get_stats(),
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """캐시 전체 삭제"""
        self.tts_cache.clear()
    
    def shutdown(self):
        """최적화 관리자 종료"""
        self.connection_pool.shutdown()
        self.logger.info("최적화 관리자 종료 완료")


# 전역 최적화 관리자 인스턴스
_optimization_manager: Optional[OptimizationManager] = None


def get_optimization_manager() -> OptimizationManager:
    """전역 최적화 관리자 인스턴스 반환"""
    global _optimization_manager
    if _optimization_manager is None:
        _optimization_manager = OptimizationManager()
    return _optimization_manager


def initialize_optimization(
    compression_config: Optional[CompressionConfig] = None,
    cache_config: Optional[CacheConfig] = None,
    connection_config: Optional[ConnectionPoolConfig] = None
) -> OptimizationManager:
    """
    최적화 시스템 초기화
    
    Args:
        compression_config: 압축 설정
        cache_config: 캐시 설정
        connection_config: 연결 풀 설정
        
    Returns:
        OptimizationManager 인스턴스
    """
    global _optimization_manager
    _optimization_manager = OptimizationManager(
        compression_config=compression_config,
        cache_config=cache_config,
        connection_config=connection_config
    )
    return _optimization_manager