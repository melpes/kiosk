"""
보안 기능 테스트
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient

from src.api.security import (
    SecurityConfig, RateLimitConfig, RateLimiter, FileValidator,
    SecurityMiddleware, FileUploadValidator, validate_file_upload,
    get_security_stats, clear_rate_limit_data
)


class TestRateLimiter:
    """Rate limiter 테스트"""
    
    def test_rate_limiter_init(self):
        """Rate limiter 초기화 테스트"""
        config = RateLimitConfig(max_requests=10, time_window=60, block_duration=300)
        limiter = RateLimiter(config)
        
        assert limiter.config.max_requests == 10
        assert limiter.config.time_window == 60
        assert limiter.config.block_duration == 300
        assert len(limiter.requests) == 0
        assert len(limiter.blocked_ips) == 0
    
    def test_get_client_ip_direct(self):
        """직접 연결 클라이언트 IP 추출 테스트"""
        config = RateLimitConfig()
        limiter = RateLimiter(config)
        
        # Mock request 생성
        request = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        
        ip = limiter.get_client_ip(request)
        assert ip == "192.168.1.100"
    
    def test_get_client_ip_forwarded(self):
        """프록시를 통한 클라이언트 IP 추출 테스트"""
        config = RateLimitConfig()
        limiter = RateLimiter(config)
        
        # Mock request 생성
        request = Mock()
        request.client.host = "10.0.0.1"  # 프록시 IP
        request.headers = {
            'X-Forwarded-For': '203.0.113.1, 10.0.0.1',
            'X-Real-IP': '203.0.113.1'
        }
        
        # 신뢰할 수 있는 프록시가 있는 경우
        ip = limiter.get_client_ip(request, trusted_proxies=['10.0.0.1'])
        assert ip == "203.0.113.1"
        
        # 신뢰할 수 있는 프록시가 없는 경우
        ip = limiter.get_client_ip(request, trusted_proxies=[])
        assert ip == "10.0.0.1"
    
    def test_rate_limit_normal(self):
        """정상적인 rate limit 테스트"""
        config = RateLimitConfig(max_requests=5, time_window=60)
        limiter = RateLimiter(config)
        
        client_ip = "192.168.1.100"
        
        # 5번의 요청은 허용되어야 함
        for i in range(5):
            assert limiter.check_rate_limit(client_ip) == True
            remaining = limiter.get_remaining_requests(client_ip)
            assert remaining == 5 - (i + 1)
        
        # 6번째 요청은 차단되어야 함
        assert limiter.check_rate_limit(client_ip) == False
        assert limiter.is_blocked(client_ip) == True
    
    def test_rate_limit_time_window(self):
        """시간 창 기반 rate limit 테스트"""
        config = RateLimitConfig(max_requests=2, time_window=1, block_duration=1)  # 1초 창, 1초 차단
        limiter = RateLimiter(config)
        
        client_ip = "192.168.1.100"
        
        # 2번의 요청
        assert limiter.check_rate_limit(client_ip) == True
        assert limiter.check_rate_limit(client_ip) == True
        
        # 3번째 요청은 차단
        assert limiter.check_rate_limit(client_ip) == False
        assert limiter.is_blocked(client_ip) == True
        
        # 1초 대기 후 차단 해제되고 다시 요청 가능
        time.sleep(1.1)
        assert limiter.is_blocked(client_ip) == False
        assert limiter.check_rate_limit(client_ip) == True


class TestFileValidator:
    """파일 검증기 테스트"""
    
    def test_file_validator_init(self):
        """파일 검증기 초기화 테스트"""
        config = SecurityConfig()
        validator = FileValidator(config)
        
        assert validator.config == config
    
    def test_validate_file_size(self):
        """파일 크기 검증 테스트"""
        config = SecurityConfig(max_file_size=1024)  # 1KB
        validator = FileValidator(config)
        
        # 정상 크기
        assert validator.validate_file_size(512) == True
        assert validator.validate_file_size(1024) == True
        
        # 초과 크기
        assert validator.validate_file_size(1025) == False
        assert validator.validate_file_size(2048) == False
        
        # None (크기 불명)
        assert validator.validate_file_size(None) == True
    
    def test_validate_file_extension(self):
        """파일 확장자 검증 테스트"""
        config = SecurityConfig(allowed_extensions=['.wav', '.mp3'])
        validator = FileValidator(config)
        
        # 허용된 확장자
        assert validator.validate_file_extension('test.wav') == True
        assert validator.validate_file_extension('test.WAV') == True
        assert validator.validate_file_extension('test.mp3') == True
        
        # 허용되지 않은 확장자
        assert validator.validate_file_extension('test.txt') == False
        assert validator.validate_file_extension('test.exe') == False
        
        # 잘못된 파일명
        assert validator.validate_file_extension('') == False
        assert validator.validate_file_extension(None) == False
    
    def test_validate_filename_security(self):
        """파일명 보안 검증 테스트"""
        config = SecurityConfig()
        validator = FileValidator(config)
        
        # 안전한 파일명
        assert validator.validate_filename_security('test.wav') == True
        assert validator.validate_filename_security('audio_file_123.wav') == True
        
        # 위험한 파일명
        assert validator.validate_filename_security('../test.wav') == False
        assert validator.validate_filename_security('test/file.wav') == False
        assert validator.validate_filename_security('test\\file.wav') == False
        assert validator.validate_filename_security('test:file.wav') == False
        
        # 빈 파일명
        assert validator.validate_filename_security('') == False
        assert validator.validate_filename_security(None) == False
        
        # 너무 긴 파일명
        long_name = 'a' * 256 + '.wav'
        assert validator.validate_filename_security(long_name) == False
    
    def test_validate_file_content(self):
        """파일 내용 검증 테스트"""
        config = SecurityConfig(allowed_file_types=['audio/wav'])
        validator = FileValidator(config)
        
        # 임시 WAV 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # WAV 헤더 작성
            wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            f.write(wav_header)
            temp_wav_path = f.name
        
        # 임시 텍스트 파일 생성
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'This is not a WAV file')
            temp_txt_path = f.name
        
        try:
            # WAV 파일은 통과해야 함
            assert validator.validate_file_content(temp_wav_path) == True
            
            # 텍스트 파일은 실패해야 함
            assert validator.validate_file_content(temp_txt_path) == False
            
            # 존재하지 않는 파일은 실패해야 함
            assert validator.validate_file_content('/nonexistent/file.wav') == False
            
        finally:
            # 정리
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            if os.path.exists(temp_txt_path):
                os.remove(temp_txt_path)


class TestFileUploadValidator:
    """파일 업로드 검증기 테스트"""
    
    def test_validate_upload_request(self):
        """업로드 요청 검증 테스트"""
        config = SecurityConfig(max_file_size=1024)
        validator = FileUploadValidator(config)
        
        # 정상 요청
        request = Mock()
        request.headers = {
            'content-type': 'multipart/form-data; boundary=something',
            'content-length': '512'
        }
        
        errors = validator.validate_upload_request(request)
        assert len(errors) == 0
        
        # 잘못된 Content-Type
        request.headers['content-type'] = 'application/json'
        errors = validator.validate_upload_request(request)
        assert 'content_type' in errors
        
        # 파일 크기 초과
        request.headers['content-type'] = 'multipart/form-data'
        request.headers['content-length'] = '2048'
        errors = validator.validate_upload_request(request)
        assert 'file_size' in errors
    
    def test_validate_uploaded_file(self):
        """업로드된 파일 검증 테스트"""
        config = SecurityConfig(
            max_file_size=1024,
            allowed_extensions=['.wav'],
            allowed_file_types=['audio/wav']
        )
        validator = FileUploadValidator(config)
        
        # 정상 파일
        errors = validator.validate_uploaded_file('test.wav', 512)
        assert len(errors) == 0
        
        # 여러 오류가 있는 파일
        errors = validator.validate_uploaded_file('../test.txt', 2048)
        assert 'filename' in errors
        assert 'extension' in errors
        assert 'size' in errors


class TestValidateFileUpload:
    """validate_file_upload 함수 테스트"""
    
    def test_validate_file_upload_success(self):
        """파일 업로드 검증 성공 테스트"""
        # 정상 파일은 예외가 발생하지 않아야 함
        try:
            validate_file_upload('test.wav', 1024)
        except HTTPException:
            pytest.fail("정상 파일에서 예외가 발생했습니다")
    
    def test_validate_file_upload_failure(self):
        """파일 업로드 검증 실패 테스트"""
        # 잘못된 파일은 HTTPException이 발생해야 함
        with pytest.raises(HTTPException) as exc_info:
            validate_file_upload('test.txt', 1024)
        
        assert exc_info.value.status_code == 400
        assert 'FILE_VALIDATION_FAILED' in str(exc_info.value.detail)


class TestSecurityStats:
    """보안 통계 테스트"""
    
    def test_get_security_stats(self):
        """보안 통계 조회 테스트"""
        stats = get_security_stats()
        
        assert 'rate_limit_config' in stats
        assert 'blocked_ips' in stats
        assert 'active_clients' in stats
        assert 'file_validation_config' in stats
        
        # Rate limit 설정 확인
        rate_config = stats['rate_limit_config']
        assert 'max_requests' in rate_config
        assert 'time_window' in rate_config
        assert 'block_duration' in rate_config
        
        # 파일 검증 설정 확인
        file_config = stats['file_validation_config']
        assert 'max_file_size_mb' in file_config
        assert 'allowed_extensions' in file_config
        assert 'allowed_mime_types' in file_config
    
    def test_clear_rate_limit_data(self):
        """Rate limit 데이터 초기화 테스트"""
        # 데이터 초기화는 예외가 발생하지 않아야 함
        try:
            clear_rate_limit_data()
        except Exception:
            pytest.fail("Rate limit 데이터 초기화에서 예외가 발생했습니다")


@pytest.fixture
def temp_wav_file():
    """임시 WAV 파일 생성"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # 간단한 WAV 헤더 작성 (실제 오디오 데이터는 없음)
        wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        f.write(wav_header)
        temp_path = f.name
    
    yield temp_path
    
    # 정리
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestIntegration:
    """통합 테스트"""
    
    def test_security_middleware_integration(self, temp_wav_file):
        """보안 미들웨어 통합 테스트"""
        from src.api.server import app
        
        client = TestClient(app)
        
        # 정상 요청
        with open(temp_wav_file, 'rb') as f:
            response = client.post(
                "/api/voice/process",
                files={"audio_file": ("test.wav", f, "audio/wav")}
            )
        
        # Rate limit 헤더가 포함되어야 함
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # 보안 헤더가 포함되어야 함
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_file_validation_integration(self):
        """파일 검증 통합 테스트"""
        from src.api.server import app
        
        client = TestClient(app)
        
        # 잘못된 파일 형식
        response = client.post(
            "/api/voice/process",
            files={"audio_file": ("test.txt", b"not a wav file", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "FILE_VALIDATION_FAILED" in response.json()["detail"]["error"]
    
    def test_security_endpoints(self):
        """보안 관련 엔드포인트 테스트"""
        from src.api.server import app
        
        client = TestClient(app)
        
        # 보안 통계 조회
        response = client.get("/api/security/stats")
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert "data" in response.json()
        
        # 보안 설정 조회
        response = client.get("/api/security/config")
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert "config" in response.json()
        
        # Rate limit 데이터 초기화
        response = client.post("/api/security/clear-rate-limit")
        assert response.status_code == 200
        assert response.json()["success"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])