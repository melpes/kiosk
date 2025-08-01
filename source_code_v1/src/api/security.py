"""
API 서버 보안 및 검증 미들웨어
"""

import time
import hashlib
from typing import Dict, List, Optional, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from ..logger import get_logger


logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting 설정"""
    max_requests: int = 100  # 최대 요청 수
    time_window: int = 3600  # 시간 창 (초)
    block_duration: int = 3600  # 차단 지속 시간 (초)


@dataclass
class SecurityConfig:
    """보안 설정"""
    max_file_size: int = 10 * 1024 * 1024  # 최대 파일 크기 (10MB)
    allowed_file_types: List[str] = field(default_factory=lambda: ['audio/wav', 'audio/x-wav'])
    allowed_extensions: List[str] = field(default_factory=lambda: ['.wav'])
    force_https: bool = False  # HTTPS 강제 여부
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    trusted_proxies: List[str] = field(default_factory=list)  # 신뢰할 수 있는 프록시 IP


class RateLimiter:
    """Rate limiting 구현"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        
    def get_client_ip(self, request: Request, trusted_proxies: List[str] = None) -> str:
        """클라이언트 IP 주소 추출"""
        if trusted_proxies is None:
            trusted_proxies = []
            
        # X-Forwarded-For 헤더 확인 (프록시 환경)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for and trusted_proxies:
            # 첫 번째 IP가 실제 클라이언트 IP
            client_ip = forwarded_for.split(',')[0].strip()
            return client_ip
            
        # X-Real-IP 헤더 확인
        real_ip = request.headers.get('X-Real-IP')
        if real_ip and trusted_proxies:
            return real_ip
            
        # 직접 연결된 클라이언트 IP
        return request.client.host if request.client else "unknown"
    
    def is_blocked(self, client_ip: str) -> bool:
        """IP가 차단되었는지 확인"""
        if client_ip in self.blocked_ips:
            block_time = self.blocked_ips[client_ip]
            if datetime.now() - block_time < timedelta(seconds=self.config.block_duration):
                return True
            else:
                # 차단 시간이 지났으면 해제
                del self.blocked_ips[client_ip]
        return False
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Rate limit 확인"""
        current_time = time.time()
        
        # 차단된 IP 확인
        if self.is_blocked(client_ip):
            return False
        
        # 요청 기록 정리 (시간 창 밖의 요청 제거)
        request_times = self.requests[client_ip]
        while request_times and current_time - request_times[0] > self.config.time_window:
            request_times.popleft()
        
        # 요청 수 확인
        if len(request_times) >= self.config.max_requests:
            # Rate limit 초과 - IP 차단
            self.blocked_ips[client_ip] = datetime.now()
            logger.warning(f"Rate limit 초과로 IP 차단: {client_ip}")
            return False
        
        # 현재 요청 기록
        request_times.append(current_time)
        return True
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """남은 요청 수 반환"""
        current_time = time.time()
        request_times = self.requests[client_ip]
        
        # 시간 창 내의 요청 수 계산
        valid_requests = sum(1 for req_time in request_times 
                           if current_time - req_time <= self.config.time_window)
        
        return max(0, self.config.max_requests - valid_requests)


class FileValidator:
    """파일 검증 클래스"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        
    def validate_file_size(self, file_size: Optional[int]) -> bool:
        """파일 크기 검증"""
        if file_size is None:
            return True  # 크기를 알 수 없는 경우 통과
        return file_size <= self.config.max_file_size
    
    def validate_file_extension(self, filename: str) -> bool:
        """파일 확장자 검증"""
        if not filename:
            return False
            
        filename_lower = filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.config.allowed_extensions)
    
    def validate_file_content(self, file_path: str) -> bool:
        """파일 내용 검증 (MIME 타입)"""
        if not MAGIC_AVAILABLE:
            # python-magic이 사용 불가능한 경우 파일 헤더로 간단 검증
            return self._validate_wav_header(file_path)
        
        try:
            # python-magic을 사용하여 실제 파일 타입 확인
            mime_type = magic.from_file(file_path, mime=True)
            return mime_type in self.config.allowed_file_types
        except Exception as e:
            logger.error(f"파일 내용 검증 실패: {e}")
            # magic 실패 시 헤더 검증으로 대체
            return self._validate_wav_header(file_path)
    
    def _validate_wav_header(self, file_path: str) -> bool:
        """WAV 파일 헤더 검증"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                if len(header) < 12:
                    return False
                
                # WAV 파일 헤더 확인: RIFF + 4바이트 크기 + WAVE
                return (header[:4] == b'RIFF' and 
                       header[8:12] == b'WAVE')
        except Exception as e:
            logger.error(f"WAV 헤더 검증 실패: {e}")
            return False
    
    def validate_filename_security(self, filename: str) -> bool:
        """파일명 보안 검증"""
        if not filename:
            return False
            
        # 위험한 문자 확인
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in filename for char in dangerous_chars):
            return False
            
        # 파일명 길이 확인
        if len(filename) > 255:
            return False
            
        return True


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 미들웨어"""
    
    def __init__(self, app, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        self.file_validator = FileValidator(self.config)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """미들웨어 메인 로직"""
        try:
            # HTTPS 강제 확인
            if self.config.force_https and request.url.scheme != "https":
                return JSONResponse(
                    status_code=status.HTTP_426_UPGRADE_REQUIRED,
                    content={
                        "error": "HTTPS_REQUIRED",
                        "message": "HTTPS 연결이 필요합니다",
                        "upgrade_to": "https"
                    }
                )
            
            # Rate limiting 확인
            client_ip = self.rate_limiter.get_client_ip(request, self.config.trusted_proxies)
            if not self.rate_limiter.check_rate_limit(client_ip):
                remaining_time = self.config.rate_limit.block_duration
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": "요청 한도를 초과했습니다",
                        "retry_after": remaining_time,
                        "client_ip": client_ip
                    },
                    headers={"Retry-After": str(remaining_time)}
                )
            
            # 요청 처리
            response = await call_next(request)
            
            # 보안 헤더 추가
            self._add_security_headers(response)
            
            # Rate limit 정보 헤더 추가
            remaining_requests = self.rate_limiter.get_remaining_requests(client_ip)
            response.headers["X-RateLimit-Limit"] = str(self.config.rate_limit.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.config.rate_limit.time_window))
            
            return response
            
        except Exception as e:
            logger.error(f"보안 미들웨어 오류: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "SECURITY_MIDDLEWARE_ERROR",
                    "message": "보안 검증 중 오류가 발생했습니다"
                }
            )
    
    def _add_security_headers(self, response: Response):
        """보안 헤더 추가"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value


class FileUploadValidator:
    """파일 업로드 검증 클래스"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.file_validator = FileValidator(self.config)
    
    def validate_upload_request(self, request: Request) -> Dict[str, str]:
        """업로드 요청 검증"""
        errors = {}
        
        # Content-Type 확인
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("multipart/form-data"):
            errors["content_type"] = "multipart/form-data 형식이 필요합니다"
        
        # Content-Length 확인
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.config.max_file_size:
                    errors["file_size"] = f"파일 크기가 {self.config.max_file_size / (1024*1024):.1f}MB를 초과합니다"
            except ValueError:
                errors["content_length"] = "잘못된 Content-Length 헤더"
        
        return errors
    
    def validate_uploaded_file(self, filename: str, file_size: Optional[int], file_path: str = None) -> Dict[str, str]:
        """업로드된 파일 검증"""
        errors = {}
        
        # 파일명 보안 검증
        if not self.file_validator.validate_filename_security(filename):
            errors["filename"] = "안전하지 않은 파일명입니다"
        
        # 파일 확장자 검증
        if not self.file_validator.validate_file_extension(filename):
            allowed_exts = ", ".join(self.config.allowed_extensions)
            errors["extension"] = f"허용되지 않는 파일 형식입니다. 허용 형식: {allowed_exts}"
        
        # 파일 크기 검증
        if not self.file_validator.validate_file_size(file_size):
            errors["size"] = f"파일 크기가 {self.config.max_file_size / (1024*1024):.1f}MB를 초과합니다"
        
        # 파일 내용 검증 (파일 경로가 제공된 경우)
        if file_path and not self.file_validator.validate_file_content(file_path):
            allowed_types = ", ".join(self.config.allowed_file_types)
            errors["content"] = f"허용되지 않는 파일 타입입니다. 허용 타입: {allowed_types}"
        
        return errors


# 전역 보안 설정 및 검증기
default_security_config = SecurityConfig()
file_upload_validator = FileUploadValidator(default_security_config)


def create_security_middleware(config: SecurityConfig = None) -> SecurityMiddleware:
    """보안 미들웨어 생성"""
    return SecurityMiddleware(None, config or default_security_config)


def validate_file_upload(filename: str, file_size: Optional[int], file_path: str = None) -> None:
    """
    파일 업로드 검증 (예외 발생)
    
    Args:
        filename: 파일명
        file_size: 파일 크기
        file_path: 파일 경로 (내용 검증용)
        
    Raises:
        HTTPException: 검증 실패 시
    """
    errors = file_upload_validator.validate_uploaded_file(filename, file_size, file_path)
    
    if errors:
        error_messages = []
        for field, message in errors.items():
            error_messages.append(f"{field}: {message}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "FILE_VALIDATION_FAILED",
                "message": "파일 검증에 실패했습니다",
                "validation_errors": errors,
                "details": "; ".join(error_messages)
            }
        )


def get_security_stats() -> Dict:
    """보안 통계 정보 반환"""
    rate_limiter = create_security_middleware().rate_limiter
    
    return {
        "rate_limit_config": {
            "max_requests": rate_limiter.config.max_requests,
            "time_window": rate_limiter.config.time_window,
            "block_duration": rate_limiter.config.block_duration
        },
        "blocked_ips": len(rate_limiter.blocked_ips),
        "active_clients": len(rate_limiter.requests),
        "file_validation_config": {
            "max_file_size_mb": default_security_config.max_file_size / (1024 * 1024),
            "allowed_extensions": default_security_config.allowed_extensions,
            "allowed_mime_types": default_security_config.allowed_file_types
        }
    }


def clear_rate_limit_data():
    """Rate limit 데이터 초기화"""
    rate_limiter = create_security_middleware().rate_limiter
    rate_limiter.requests.clear()
    rate_limiter.blocked_ips.clear()
    logger.info("Rate limit 데이터 초기화 완료")