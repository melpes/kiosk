#!/usr/bin/env python3
"""
최적화 기능 테스트 스크립트
"""

import os
import sys
import time
import tempfile
import wave
import struct
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.api.optimization import (
    OptimizationManager, CompressionConfig, CacheConfig, ConnectionPoolConfig,
    AudioCompressor, TTSCache
)
from src.logger import get_logger


def create_test_audio_file(file_path: str, duration: float = 2.0, sample_rate: int = 16000):
    """테스트용 WAV 파일 생성"""
    num_samples = int(sample_rate * duration)
    
    with wave.open(file_path, 'w') as wav_file:
        wav_file.setnchannels(1)  # 모노
        wav_file.setsampwidth(2)  # 16비트
        wav_file.setframerate(sample_rate)
        
        # 간단한 사인파 생성
        for i in range(num_samples):
            # 440Hz 사인파 (A4 음)
            sample = int(16000 * 0.5 * (i % 100) / 100)  # 간단한 톤
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"테스트 오디오 파일 생성: {file_path} ({os.path.getsize(file_path)} bytes)")


def test_audio_compression():
    """오디오 압축 기능 테스트"""
    print("\n=== 오디오 압축 테스트 ===")
    
    # 압축 설정
    config = CompressionConfig(
        enabled=True,
        compression_level=6,
        min_file_size=1024,
        audio_quality_reduction=True,
        target_bitrate=8000
    )
    
    compressor = AudioCompressor(config)
    
    # 테스트 파일 생성
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        test_file_path = temp_file.name
    
    try:
        create_test_audio_file(test_file_path, duration=5.0)
        original_size = os.path.getsize(test_file_path)
        
        print(f"원본 파일 크기: {original_size} bytes")
        
        # 품질 감소 테스트
        optimized_path = compressor.reduce_audio_quality(test_file_path)
        if optimized_path != test_file_path:
            optimized_size = os.path.getsize(optimized_path)
            print(f"품질 최적화 후 크기: {optimized_size} bytes (감소율: {(1 - optimized_size/original_size)*100:.1f}%)")
        
        # 압축 테스트
        compressed_path, compression_ratio = compressor.compress_audio_file(optimized_path)
        if compressed_path != optimized_path:
            compressed_size = os.path.getsize(compressed_path)
            print(f"압축 후 크기: {compressed_size} bytes (압축률: {compression_ratio:.2f})")
            
            # 압축 해제 테스트
            decompressed_path = compressor.decompress_audio_file(compressed_path)
            if os.path.exists(decompressed_path):
                decompressed_size = os.path.getsize(decompressed_path)
                print(f"압축 해제 후 크기: {decompressed_size} bytes")
                
                # 정리
                os.remove(compressed_path)
                if decompressed_path != optimized_path:
                    os.remove(decompressed_path)
        
        # 정리
        if optimized_path != test_file_path:
            os.remove(optimized_path)
        
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
    
    print("오디오 압축 테스트 완료")


def test_tts_cache():
    """TTS 캐시 기능 테스트"""
    print("\n=== TTS 캐시 테스트 ===")
    
    # 캐시 설정
    config = CacheConfig(
        enabled=True,
        max_cache_size=5,
        ttl_seconds=10,
        cleanup_interval=5,
        memory_limit_mb=10
    )
    
    cache = TTSCache(config)
    
    # 테스트 데이터
    test_texts = [
        "안녕하세요, 주문을 도와드리겠습니다.",
        "메뉴를 선택해 주세요.",
        "주문이 완료되었습니다.",
        "결제를 진행하시겠습니까?",
        "감사합니다."
    ]
    
    voice_config = {
        'provider': 'openai',
        'model': 'tts-1',
        'voice': 'alloy',
        'speed': 1.0
    }
    
    # 테스트 파일들 생성 및 캐시 저장
    temp_files = []
    
    try:
        for i, text in enumerate(test_texts):
            # 임시 TTS 파일 생성
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_files.append(temp_file_path)
            
            create_test_audio_file(temp_file_path, duration=len(text) * 0.1)
            
            # 캐시에 저장
            success = cache.put(text, voice_config, temp_file_path)
            print(f"캐시 저장 {'성공' if success else '실패'}: {text[:20]}...")
        
        # 캐시 조회 테스트
        print(f"\n캐시 통계: {cache.get_stats()}")
        
        # 캐시에서 조회
        for text in test_texts[:3]:
            cached_path = cache.get(text, voice_config)
            if cached_path:
                print(f"캐시 히트: {text[:20]}... -> {cached_path}")
            else:
                print(f"캐시 미스: {text[:20]}...")
        
        # TTL 테스트 (잠시 대기)
        print("\nTTL 테스트를 위해 잠시 대기...")
        time.sleep(12)  # TTL(10초)보다 길게 대기
        
        # 만료된 캐시 조회
        expired_path = cache.get(test_texts[0], voice_config)
        if expired_path:
            print("TTL 테스트 실패: 만료된 캐시가 반환됨")
        else:
            print("TTL 테스트 성공: 만료된 캐시가 정리됨")
        
        print(f"최종 캐시 통계: {cache.get_stats()}")
        
    finally:
        # 정리
        cache.clear()
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    print("TTS 캐시 테스트 완료")


def test_optimization_manager():
    """통합 최적화 관리자 테스트"""
    print("\n=== 통합 최적화 관리자 테스트 ===")
    
    # 설정
    compression_config = CompressionConfig(enabled=True, compression_level=6)
    cache_config = CacheConfig(enabled=True, max_cache_size=10, ttl_seconds=30)
    connection_config = ConnectionPoolConfig(max_workers=5, queue_size=20)
    
    manager = OptimizationManager(
        compression_config=compression_config,
        cache_config=cache_config,
        connection_config=connection_config
    )
    
    # 테스트 파일 생성
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        test_file_path = temp_file.name
    
    try:
        create_test_audio_file(test_file_path, duration=3.0)
        
        # 파일 최적화 테스트
        optimized_path, optimization_info = manager.optimize_audio_file(test_file_path)
        print(f"파일 최적화 결과: {optimization_info}")
        
        # TTS 캐시 테스트
        test_text = "최적화 관리자 테스트입니다."
        voice_config = {'provider': 'test', 'voice': 'test'}
        
        # 캐시에 저장
        cache_success = manager.cache_tts_file(test_text, voice_config, test_file_path)
        print(f"TTS 캐시 저장: {'성공' if cache_success else '실패'}")
        
        # 캐시에서 조회
        cached_path = manager.get_cached_tts(test_text, voice_config)
        print(f"TTS 캐시 조회: {'성공' if cached_path else '실패'}")
        
        # 통계 조회
        stats = manager.get_optimization_stats()
        print(f"최적화 통계:")
        print(f"  - 압축 설정: {stats['compression']}")
        print(f"  - 캐시 통계: {stats['cache']}")
        print(f"  - 연결 풀 통계: {stats['connection_pool']}")
        
        # 정리
        if optimized_path != test_file_path and os.path.exists(optimized_path):
            os.remove(optimized_path)
        
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
        manager.shutdown()
    
    print("통합 최적화 관리자 테스트 완료")


def main():
    """메인 테스트 함수"""
    logger = get_logger(__name__)
    
    print("=== 최적화 기능 테스트 시작 ===")
    
    try:
        # 개별 기능 테스트
        test_audio_compression()
        test_tts_cache()
        test_optimization_manager()
        
        print("\n=== 모든 테스트 완료 ===")
        
    except Exception as e:
        logger.error(f"테스트 중 오류 발생: {e}")
        print(f"테스트 실패: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())