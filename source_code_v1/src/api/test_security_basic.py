#!/usr/bin/env python3
"""
기본 보안 기능 테스트 스크립트
"""

import os
import tempfile
import time
from pathlib import Path

from security import (
    SecurityConfig, RateLimitConfig, RateLimiter, FileValidator,
    FileUploadValidator, validate_file_upload, get_security_stats
)


def test_rate_limiter():
    """Rate limiter 기본 테스트"""
    print("=== Rate Limiter 테스트 ===")
    
    config = RateLimitConfig(max_requests=3, time_window=5, block_duration=2)
    limiter = RateLimiter(config)
    
    client_ip = "192.168.1.100"
    
    # 3번의 요청은 허용되어야 함
    for i in range(3):
        result = limiter.check_rate_limit(client_ip)
        remaining = limiter.get_remaining_requests(client_ip)
        print(f"요청 {i+1}: 허용={result}, 남은 요청={remaining}")
        assert result == True
    
    # 4번째 요청은 차단되어야 함
    result = limiter.check_rate_limit(client_ip)
    print(f"요청 4: 허용={result} (차단되어야 함)")
    assert result == False
    assert limiter.is_blocked(client_ip) == True
    
    print("✓ Rate limiter 테스트 통과")


def test_file_validator():
    """파일 검증기 테스트"""
    print("\n=== File Validator 테스트 ===")
    
    config = SecurityConfig(
        max_file_size=1024,  # 1KB
        allowed_extensions=['.wav'],
        allowed_file_types=['audio/wav']
    )
    validator = FileValidator(config)
    
    # 파일 크기 테스트
    assert validator.validate_file_size(512) == True
    assert validator.validate_file_size(1025) == False
    print("✓ 파일 크기 검증 통과")
    
    # 파일 확장자 테스트
    assert validator.validate_file_extension('test.wav') == True
    assert validator.validate_file_extension('test.txt') == False
    print("✓ 파일 확장자 검증 통과")
    
    # 파일명 보안 테스트
    assert validator.validate_filename_security('test.wav') == True
    assert validator.validate_filename_security('../test.wav') == False
    assert validator.validate_filename_security('test/file.wav') == False
    print("✓ 파일명 보안 검증 통과")
    
    # WAV 파일 헤더 테스트
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # 올바른 WAV 헤더 작성
        wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        f.write(wav_header)
        temp_wav_path = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b'This is not a WAV file')
        temp_txt_path = f.name
    
    try:
        assert validator.validate_file_content(temp_wav_path) == True
        assert validator.validate_file_content(temp_txt_path) == False
        print("✓ 파일 내용 검증 통과")
    finally:
        os.remove(temp_wav_path)
        os.remove(temp_txt_path)


def test_file_upload_validator():
    """파일 업로드 검증기 테스트"""
    print("\n=== File Upload Validator 테스트 ===")
    
    config = SecurityConfig(
        max_file_size=1024,
        allowed_extensions=['.wav']
    )
    validator = FileUploadValidator(config)
    
    # 정상 파일
    errors = validator.validate_uploaded_file('test.wav', 512)
    assert len(errors) == 0
    print("✓ 정상 파일 검증 통과")
    
    # 문제가 있는 파일
    errors = validator.validate_uploaded_file('../test.txt', 2048)
    assert 'filename' in errors
    assert 'extension' in errors
    assert 'size' in errors
    print("✓ 문제 파일 검증 통과")


def test_security_stats():
    """보안 통계 테스트"""
    print("\n=== Security Stats 테스트 ===")
    
    stats = get_security_stats()
    
    required_keys = ['rate_limit_config', 'blocked_ips', 'active_clients', 'file_validation_config']
    for key in required_keys:
        assert key in stats
    
    print("✓ 보안 통계 조회 통과")
    print(f"  - Rate limit 설정: {stats['rate_limit_config']}")
    print(f"  - 차단된 IP 수: {stats['blocked_ips']}")
    print(f"  - 활성 클라이언트 수: {stats['active_clients']}")


def main():
    """메인 테스트 실행"""
    print("보안 기능 기본 테스트 시작\n")
    
    try:
        test_rate_limiter()
        test_file_validator()
        test_file_upload_validator()
        test_security_stats()
        
        print("\n🎉 모든 보안 기능 테스트 통과!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        raise


if __name__ == "__main__":
    main()