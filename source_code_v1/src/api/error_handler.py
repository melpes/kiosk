"""
API 오류 처리 로직
서버 측 오류 처리 및 복구 시스템
"""

import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

from ..models.communication_models import ServerResponse, ErrorInfo, ErrorCode, UIAction, UIActionType
from ..logger import get_logger


class ErrorSeverity(Enum):
    """오류 심각도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """오류 카테고리"""
    NETWORK = "network"
    VALIDATION = "validation"
    PROCESSING = "processing"
    SYSTEM = "system"
    EXTERNAL = "external"


class APIErrorHandler:
    """API 오류 처리 클래스"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.error_stats = {}  # 오류 통계
        
    def handle_exception(self, 
                        exception: Exception, 
                        request: Optional[Request] = None,
                        session_id: Optional[str] = None,
                        context: Optional[Dict[str, Any]] = None) -> ServerResponse:
        """
        예외를 처리하고 적절한 ServerResponse 생성
        
        Args:
            exception: 발생한 예외
            request: FastAPI 요청 객체
            session_id: 세션 ID
            context: 추가 컨텍스트 정보
            
        Returns:
            ServerResponse: 오류 응답
        """
        # 오류 분류 및 정보 수집
        error_info = self._classify_and_analyze_error(exception, request, context)
        
        # 오류 로깅
        self._log_error(error_info, exception, request, session_id)
        
        # 오류 통계 업데이트
        self._update_error_stats(error_info)
        
        # 복구 액션 생성
        recovery_actions = self._generate_recovery_actions(error_info, exception)
        
        # UI 액션 생성
        ui_actions = self._generate_ui_actions(error_info, recovery_actions)
        
        # ErrorInfo 객체 생성
        error_info_obj = ErrorInfo(
            error_code=error_info['error_code'].value,
            error_message=self._generate_user_friendly_message(error_info, exception),
            recovery_actions=recovery_actions,
            details=error_info.get('details', {}),
            timestamp=datetime.now()
        )
        
        # ServerResponse 생성
        return ServerResponse(
            success=False,
            message=error_info_obj.error_message,
            error_info=error_info_obj,
            ui_actions=ui_actions,
            session_id=session_id,
            timestamp=datetime.now()
        )
    
    def _classify_and_analyze_error(self, 
                                  exception: Exception, 
                                  request: Optional[Request] = None,
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        오류 분류 및 분석
        
        Args:
            exception: 발생한 예외
            request: FastAPI 요청 객체
            context: 추가 컨텍스트 정보
            
        Returns:
            Dict[str, Any]: 오류 정보
        """
        error_info = {
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'timestamp': datetime.now(),
            'context': context or {}
        }
        
        # 요청 정보 추가
        if request:
            error_info['request_info'] = {
                'method': request.method,
                'url': str(request.url),
                'client_host': request.client.host if request.client else None,
                'user_agent': request.headers.get('user-agent'),
                'content_type': request.headers.get('content-type')
            }
        
        # 예외 타입별 분류
        if isinstance(exception, HTTPException):
            error_info.update(self._analyze_http_exception(exception))
        elif isinstance(exception, FileNotFoundError):
            error_info.update(self._analyze_file_error(exception))
        elif isinstance(exception, PermissionError):
            error_info.update(self._analyze_permission_error(exception))
        elif isinstance(exception, TimeoutError):
            error_info.update(self._analyze_timeout_error(exception))
        elif isinstance(exception, ConnectionError):
            error_info.update(self._analyze_connection_error(exception))
        elif isinstance(exception, ValueError):
            error_info.update(self._analyze_validation_error(exception))
        elif isinstance(exception, ImportError):
            error_info.update(self._analyze_import_error(exception))
        else:
            error_info.update(self._analyze_generic_error(exception))
        
        return error_info
    
    def _analyze_http_exception(self, exception: HTTPException) -> Dict[str, Any]:
        """HTTP 예외 분석"""
        if exception.status_code == 400:
            return {
                'error_code': ErrorCode.VALIDATION_ERROR,
                'category': ErrorCategory.VALIDATION,
                'severity': ErrorSeverity.MEDIUM,
                'details': {'status_code': exception.status_code, 'detail': exception.detail}
            }
        elif exception.status_code == 404:
            return {
                'error_code': ErrorCode.VALIDATION_ERROR,
                'category': ErrorCategory.VALIDATION,
                'severity': ErrorSeverity.LOW,
                'details': {'status_code': exception.status_code, 'detail': exception.detail}
            }
        elif exception.status_code == 500:
            return {
                'error_code': ErrorCode.SERVER_ERROR,
                'category': ErrorCategory.SYSTEM,
                'severity': ErrorSeverity.HIGH,
                'details': {'status_code': exception.status_code, 'detail': exception.detail}
            }
        else:
            return {
                'error_code': ErrorCode.SERVER_ERROR,
                'category': ErrorCategory.SYSTEM,
                'severity': ErrorSeverity.MEDIUM,
                'details': {'status_code': exception.status_code, 'detail': exception.detail}
            }
    
    def _analyze_file_error(self, exception: FileNotFoundError) -> Dict[str, Any]:
        """파일 오류 분석"""
        return {
            'error_code': ErrorCode.VALIDATION_ERROR,
            'category': ErrorCategory.VALIDATION,
            'severity': ErrorSeverity.MEDIUM,
            'details': {'file_path': str(exception)}
        }
    
    def _analyze_permission_error(self, exception: PermissionError) -> Dict[str, Any]:
        """권한 오류 분석"""
        return {
            'error_code': ErrorCode.SERVER_ERROR,
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.HIGH,
            'details': {'permission_error': str(exception)}
        }
    
    def _analyze_timeout_error(self, exception: TimeoutError) -> Dict[str, Any]:
        """타임아웃 오류 분석"""
        return {
            'error_code': ErrorCode.TIMEOUT_ERROR,
            'category': ErrorCategory.NETWORK,
            'severity': ErrorSeverity.MEDIUM,
            'details': {'timeout_info': str(exception)}
        }
    
    def _analyze_connection_error(self, exception: ConnectionError) -> Dict[str, Any]:
        """연결 오류 분석"""
        return {
            'error_code': ErrorCode.NETWORK_ERROR,
            'category': ErrorCategory.NETWORK,
            'severity': ErrorSeverity.HIGH,
            'details': {'connection_info': str(exception)}
        }
    
    def _analyze_validation_error(self, exception: ValueError) -> Dict[str, Any]:
        """검증 오류 분석"""
        return {
            'error_code': ErrorCode.VALIDATION_ERROR,
            'category': ErrorCategory.VALIDATION,
            'severity': ErrorSeverity.MEDIUM,
            'details': {'validation_info': str(exception)}
        }
    
    def _analyze_import_error(self, exception: ImportError) -> Dict[str, Any]:
        """임포트 오류 분석"""
        return {
            'error_code': ErrorCode.SERVER_ERROR,
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.CRITICAL,
            'details': {'import_info': str(exception)}
        }
    
    def _analyze_generic_error(self, exception: Exception) -> Dict[str, Any]:
        """일반 오류 분석"""
        # 음성 처리 관련 오류 감지
        if any(keyword in str(exception).lower() for keyword in ['whisper', 'speech', 'audio', 'recognition']):
            return {
                'error_code': ErrorCode.SPEECH_RECOGNITION_ERROR,
                'category': ErrorCategory.PROCESSING,
                'severity': ErrorSeverity.HIGH,
                'details': {'processing_info': str(exception)}
            }
        
        # LLM 처리 관련 오류 감지
        if any(keyword in str(exception).lower() for keyword in ['openai', 'gpt', 'llm', 'intent']):
            return {
                'error_code': ErrorCode.INTENT_RECOGNITION_ERROR,
                'category': ErrorCategory.EXTERNAL,
                'severity': ErrorSeverity.HIGH,
                'details': {'llm_info': str(exception)}
            }
        
        # 주문 처리 관련 오류 감지
        if any(keyword in str(exception).lower() for keyword in ['order', 'menu', 'payment']):
            return {
                'error_code': ErrorCode.ORDER_PROCESSING_ERROR,
                'category': ErrorCategory.PROCESSING,
                'severity': ErrorSeverity.MEDIUM,
                'details': {'order_info': str(exception)}
            }
        
        # 기본 분류
        return {
            'error_code': ErrorCode.UNKNOWN_ERROR,
            'category': ErrorCategory.SYSTEM,
            'severity': ErrorSeverity.MEDIUM,
            'details': {'generic_info': str(exception)}
        }
    
    def _generate_recovery_actions(self, error_info: Dict[str, Any], exception: Exception) -> List[str]:
        """
        복구 액션 생성
        
        Args:
            error_info: 오류 정보
            exception: 발생한 예외
            
        Returns:
            List[str]: 복구 액션 목록
        """
        error_code = error_info['error_code']
        category = error_info['category']
        
        # 오류 코드별 복구 액션
        if error_code == ErrorCode.NETWORK_ERROR:
            return [
                "네트워크 연결을 확인해주세요",
                "잠시 후 다시 시도해주세요",
                "서버 상태를 확인해주세요"
            ]
        elif error_code == ErrorCode.TIMEOUT_ERROR:
            return [
                "요청 시간이 초과되었습니다",
                "음성 파일 크기를 줄여보세요",
                "네트워크 상태를 확인하고 다시 시도해주세요"
            ]
        elif error_code == ErrorCode.VALIDATION_ERROR:
            return [
                "입력 데이터를 확인해주세요",
                "올바른 파일 형식인지 확인해주세요",
                "파일 크기 제한을 확인해주세요"
            ]
        elif error_code == ErrorCode.SPEECH_RECOGNITION_ERROR:
            return [
                "음성을 더 명확하게 말씀해주세요",
                "주변 소음을 줄여주세요",
                "다시 녹음해서 시도해주세요"
            ]
        elif error_code == ErrorCode.INTENT_RECOGNITION_ERROR:
            return [
                "명령을 더 구체적으로 말씀해주세요",
                "다른 표현으로 다시 시도해주세요",
                "메뉴에서 직접 선택해주세요"
            ]
        elif error_code == ErrorCode.ORDER_PROCESSING_ERROR:
            return [
                "주문 내용을 다시 확인해주세요",
                "메뉴 선택을 다시 해주세요",
                "처음부터 다시 주문해주세요"
            ]
        elif error_code == ErrorCode.PAYMENT_ERROR:
            return [
                "결제 정보를 확인해주세요",
                "다른 결제 방법을 시도해주세요",
                "카드를 다시 삽입해주세요"
            ]
        elif error_code == ErrorCode.SERVER_ERROR:
            return [
                "서버에 일시적인 문제가 발생했습니다",
                "잠시 후 다시 시도해주세요",
                "문제가 지속되면 관리자에게 문의해주세요"
            ]
        else:
            return [
                "잠시 후 다시 시도해주세요",
                "문제가 지속되면 관리자에게 문의해주세요"
            ]
    
    def _generate_ui_actions(self, error_info: Dict[str, Any], recovery_actions: List[str]) -> List[UIAction]:
        """
        UI 액션 생성
        
        Args:
            error_info: 오류 정보
            recovery_actions: 복구 액션 목록
            
        Returns:
            List[UIAction]: UI 액션 목록
        """
        error_code = error_info['error_code']
        
        # 기본 오류 표시 액션
        ui_actions = [
            UIAction(
                action_type=UIActionType.SHOW_ERROR.value,
                data={
                    "error_code": error_code.value,
                    "error_message": self._generate_user_friendly_message(error_info, None),
                    "recovery_actions": recovery_actions,
                    "severity": error_info.get('severity', ErrorSeverity.MEDIUM).value
                },
                priority=1
            )
        ]
        
        # 특정 오류에 대한 추가 액션
        if error_code == ErrorCode.SPEECH_RECOGNITION_ERROR:
            ui_actions.append(
                UIAction(
                    action_type="show_voice_guide",
                    data={
                        "message": "음성 인식에 문제가 있습니다",
                        "guide_text": "마이크에 가까이서 천천히 말씀해주세요"
                    }
                )
            )
        elif error_code == ErrorCode.ORDER_PROCESSING_ERROR:
            ui_actions.append(
                UIAction(
                    action_type=UIActionType.SHOW_MENU.value,
                    data={
                        "message": "메뉴에서 직접 선택해주세요",
                        "show_categories": True
                    },
                    requires_user_input=True
                )
            )
        elif error_code == ErrorCode.NETWORK_ERROR:
            ui_actions.append(
                UIAction(
                    action_type="show_retry_button",
                    data={
                        "message": "네트워크 연결을 확인하고 다시 시도해주세요",
                        "retry_delay": 3
                    }
                )
            )
        
        return ui_actions
    
    def _generate_user_friendly_message(self, error_info: Dict[str, Any], exception: Optional[Exception]) -> str:
        """
        사용자 친화적 오류 메시지 생성
        
        Args:
            error_info: 오류 정보
            exception: 발생한 예외
            
        Returns:
            str: 사용자 친화적 메시지
        """
        error_code = error_info['error_code']
        
        # 오류 코드별 메시지
        messages = {
            ErrorCode.NETWORK_ERROR: "네트워크 연결에 문제가 있습니다. 연결 상태를 확인해주세요.",
            ErrorCode.TIMEOUT_ERROR: "요청 처리 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.VALIDATION_ERROR: "입력하신 정보에 문제가 있습니다. 다시 확인해주세요.",
            ErrorCode.SPEECH_RECOGNITION_ERROR: "음성 인식에 실패했습니다. 더 명확하게 말씀해주세요.",
            ErrorCode.INTENT_RECOGNITION_ERROR: "명령을 이해하지 못했습니다. 다른 방식으로 말씀해주세요.",
            ErrorCode.ORDER_PROCESSING_ERROR: "주문 처리 중 문제가 발생했습니다. 다시 시도해주세요.",
            ErrorCode.PAYMENT_ERROR: "결제 처리 중 문제가 발생했습니다. 결제 정보를 확인해주세요.",
            ErrorCode.SERVER_ERROR: "서버에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.AUDIO_PROCESSING_ERROR: "음성 파일 처리 중 문제가 발생했습니다. 다시 녹음해주세요.",
            ErrorCode.UNKNOWN_ERROR: "예상치 못한 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        }
        
        base_message = messages.get(error_code, "문제가 발생했습니다. 다시 시도해주세요.")
        
        # 심각도에 따른 메시지 조정
        severity = error_info.get('severity', ErrorSeverity.MEDIUM)
        if severity == ErrorSeverity.CRITICAL:
            base_message = f"심각한 오류: {base_message} 관리자에게 즉시 문의해주세요."
        elif severity == ErrorSeverity.HIGH:
            base_message = f"중요한 오류: {base_message}"
        
        return base_message
    
    def _log_error(self, 
                  error_info: Dict[str, Any], 
                  exception: Exception, 
                  request: Optional[Request] = None,
                  session_id: Optional[str] = None):
        """
        오류 로깅
        
        Args:
            error_info: 오류 정보
            exception: 발생한 예외
            request: FastAPI 요청 객체
            session_id: 세션 ID
        """
        severity = error_info.get('severity', ErrorSeverity.MEDIUM)
        
        # 로그 레벨 결정
        if severity == ErrorSeverity.CRITICAL:
            log_level = logging.CRITICAL
        elif severity == ErrorSeverity.HIGH:
            log_level = logging.ERROR
        elif severity == ErrorSeverity.MEDIUM:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        # 로그 메시지 구성
        log_data = {
            'error_code': error_info['error_code'].value,
            'category': error_info['category'].value,
            'severity': severity.value,
            'exception_type': error_info['exception_type'],
            'exception_message': error_info['exception_message'],
            'session_id': session_id,
            'timestamp': error_info['timestamp'].isoformat()
        }
        
        if request:
            log_data['request_info'] = error_info.get('request_info', {})
        
        # 스택 트레이스 추가 (높은 심각도의 경우)
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            log_data['stack_trace'] = traceback.format_exc()
        
        self.logger.log(log_level, f"API 오류 발생: {log_data}")
    
    def _update_error_stats(self, error_info: Dict[str, Any]):
        """
        오류 통계 업데이트
        
        Args:
            error_info: 오류 정보
        """
        error_code = error_info['error_code'].value
        category = error_info['category'].value
        
        # 오류 코드별 통계
        if error_code not in self.error_stats:
            self.error_stats[error_code] = {
                'count': 0,
                'first_occurrence': error_info['timestamp'],
                'last_occurrence': error_info['timestamp'],
                'categories': {}
            }
        
        self.error_stats[error_code]['count'] += 1
        self.error_stats[error_code]['last_occurrence'] = error_info['timestamp']
        
        # 카테고리별 통계
        if category not in self.error_stats[error_code]['categories']:
            self.error_stats[error_code]['categories'][category] = 0
        self.error_stats[error_code]['categories'][category] += 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        오류 통계 반환
        
        Returns:
            Dict[str, Any]: 오류 통계 정보
        """
        return {
            'error_stats': self.error_stats,
            'total_errors': sum(stats['count'] for stats in self.error_stats.values()),
            'generated_at': datetime.now().isoformat()
        }
    
    def create_http_exception_handler(self):
        """FastAPI용 HTTP 예외 핸들러 생성"""
        async def http_exception_handler(request: Request, exc: HTTPException):
            response = self.handle_exception(exc, request)
            return JSONResponse(
                status_code=exc.status_code,
                content=response.to_dict()
            )
        return http_exception_handler
    
    def create_general_exception_handler(self):
        """FastAPI용 일반 예외 핸들러 생성"""
        async def general_exception_handler(request: Request, exc: Exception):
            response = self.handle_exception(exc, request)
            return JSONResponse(
                status_code=500,
                content=response.to_dict()
            )
        return general_exception_handler


# 전역 오류 처리기 인스턴스
api_error_handler = APIErrorHandler()


def handle_api_error(exception: Exception, 
                    request: Optional[Request] = None,
                    session_id: Optional[str] = None,
                    context: Optional[Dict[str, Any]] = None) -> ServerResponse:
    """
    API 오류 처리 편의 함수
    
    Args:
        exception: 발생한 예외
        request: FastAPI 요청 객체
        session_id: 세션 ID
        context: 추가 컨텍스트 정보
        
    Returns:
        ServerResponse: 오류 응답
    """
    return api_error_handler.handle_exception(exception, request, session_id, context)


def get_error_stats() -> Dict[str, Any]:
    """
    오류 통계 반환 편의 함수
    
    Returns:
        Dict[str, Any]: 오류 통계 정보
    """
    return api_error_handler.get_error_stats()