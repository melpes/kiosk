"""
음성 키오스크 클라이언트
"""

import os
import time
import uuid
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading
from urllib.parse import urljoin

from .config_manager import ClientConfig
from .models.communication_models import ServerResponse, ErrorInfo, ErrorCode
from .error_recovery import ErrorRecoveryManager
from utils.logger import get_logger
from utils.audio_utils import AudioUtils


class VoiceClient:
    """
    음성 키오스크 클라이언트
    서버와의 HTTP 통신을 담당하는 클래스
    """
    
    def __init__(self, config: ClientConfig):
        """
        클라이언트 초기화
        
        Args:
            config: 클라이언트 설정
        """
        self.config = config
        self.session = requests.Session()
        self.session_id: Optional[str] = None
        self.logger = get_logger(f"{__name__}.VoiceClient")
        self.audio_utils = AudioUtils()
        
        # 오류 복구 관리자 초기화
        self.error_recovery = ErrorRecoveryManager(config, self)
        
        # 세션 ID 자동 생성
        if self.config.session.auto_generate_id:
            self.session_id = str(uuid.uuid4())
        
        # 요청 헤더 설정
        self.session.headers.update({
            'User-Agent': 'VoiceKioskClient/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        # 연결 풀 설정
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=self.config.performance.connection_pool_size,
            pool_maxsize=self.config.performance.connection_pool_size
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.logger.info(f"VoiceClient 초기화 완료 (서버: {self.config.server.url}, 세션: {self.session_id})")
    
    def send_audio_file(self, audio_file_path: str, session_id: str = None, enable_recovery: bool = True) -> ServerResponse:
        """
        음성 파일을 서버로 전송하고 응답을 받음
        
        Args:
            audio_file_path: 전송할 음성 파일 경로
            session_id: 세션 ID (선택사항)
            enable_recovery: 오류 복구 활성화 여부
            
        Returns:
            ServerResponse: 서버 응답
        """
        # 파일 검증
        is_valid, error_msg = self._validate_audio_file(audio_file_path)
        if not is_valid:
            error_response = self._create_validation_error_response(error_msg)
            if enable_recovery:
                return self._handle_error_with_recovery(error_response, {
                    'audio_file_path': audio_file_path,
                    'validation_error': error_msg
                })
            return error_response
        
        # 세션 ID 설정
        if session_id:
            self.session_id = session_id
        
        # 재시도 로직으로 파일 전송
        for attempt in range(self.config.server.max_retries):
            try:
                self.logger.info(f"음성 파일 전송 시도 {attempt + 1}/{self.config.server.max_retries}: {audio_file_path}")
                
                response = self._send_file_with_retry(audio_file_path)
                
                # 성공 응답 처리
                if response.success:
                    self.logger.info(f"음성 파일 전송 성공 (처리 시간: {response.processing_time:.2f}초)")
                    return response
                else:
                    # 서버 오류 응답 처리
                    if enable_recovery:
                        return self._handle_error_with_recovery(response, {
                            'audio_file_path': audio_file_path,
                            'attempt': attempt + 1,
                            'retry_count': attempt
                        })
                    return response
                
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"요청 타임아웃 (시도 {attempt + 1}): {e}")
                if attempt == self.config.server.max_retries - 1:
                    error_response = self._create_timeout_error_response(str(e))
                    if enable_recovery:
                        return self._handle_error_with_recovery(error_response, {
                            'audio_file_path': audio_file_path,
                            'retry_count': attempt + 1,
                            'timeout_duration': self.config.server.timeout
                        })
                    return error_response
                time.sleep(self.config.server.retry_delay * (attempt + 1))
                
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"연결 오류 (시도 {attempt + 1}): {e}")
                if attempt == self.config.server.max_retries - 1:
                    error_response = self._create_connection_error_response(str(e))
                    if enable_recovery:
                        return self._handle_error_with_recovery(error_response, {
                            'audio_file_path': audio_file_path,
                            'retry_count': attempt + 1,
                            'server_url': self.config.server.url
                        })
                    return error_response
                time.sleep(self.config.server.retry_delay * (attempt + 1))
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"요청 오류 (시도 {attempt + 1}): {e}")
                if attempt == self.config.server.max_retries - 1:
                    error_response = self._create_network_error_response(str(e))
                    if enable_recovery:
                        return self._handle_error_with_recovery(error_response, {
                            'audio_file_path': audio_file_path,
                            'retry_count': attempt + 1
                        })
                    return error_response
                time.sleep(self.config.server.retry_delay * (attempt + 1))
                
            except Exception as e:
                self.logger.error(f"예상치 못한 오류: {e}")
                error_response = self._create_unknown_error_response(str(e))
                if enable_recovery:
                    return self._handle_error_with_recovery(error_response, {
                        'audio_file_path': audio_file_path,
                        'retry_count': attempt + 1
                    })
                return error_response
        
        # 모든 재시도 실패
        error_response = self._create_network_error_response("모든 재시도 실패")
        if enable_recovery:
            return self._handle_error_with_recovery(error_response, {
                'audio_file_path': audio_file_path,
                'retry_count': self.config.server.max_retries,
                'all_retries_failed': True
            })
        return error_response
    
    def _send_file_with_retry(self, audio_file_path: str) -> ServerResponse:
        """
        실제 파일 전송 수행
        
        Args:
            audio_file_path: 음성 파일 경로
            
        Returns:
            ServerResponse: 서버 응답
        """
        url = urljoin(self.config.server.url, "/api/voice/process")
        
        # 파일 준비
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'audio_file': (
                    Path(audio_file_path).name,
                    audio_file,
                    'audio/wav'
                )
            }
            
            # 요청 데이터 준비
            data = {}
            if self.session_id:
                data['session_id'] = self.session_id
            
            # HTTP 요청 전송
            start_time = time.time()
            response = self.session.post(
                url,
                files=files,
                data=data,
                timeout=self.config.server.timeout
            )
            request_time = time.time() - start_time
            
            self.logger.debug(f"HTTP 요청 완료 (상태: {response.status_code}, 시간: {request_time:.2f}초)")
            
            # 응답 처리
            if response.status_code == 200:
                return self._parse_success_response(response.json())
            else:
                return self._parse_error_response(response)
    
    def _validate_audio_file(self, audio_file_path: str) -> tuple[bool, str]:
        """
        음성 파일 유효성 검증
        
        Args:
            audio_file_path: 검증할 파일 경로
            
        Returns:
            tuple[bool, str]: (유효성, 오류 메시지)
        """
        file_path = Path(audio_file_path)
        
        # 파일 존재 확인
        if not file_path.exists():
            return False, f"음성 파일을 찾을 수 없습니다: {audio_file_path}"
        
        # 파일 형식 확인
        if file_path.suffix.lower() not in self.config.audio.supported_formats:
            return False, f"지원하지 않는 파일 형식입니다: {file_path.suffix}"
        
        # 파일 크기 확인
        file_size = file_path.stat().st_size
        if file_size > self.config.audio.max_file_size:
            return False, f"파일 크기가 제한을 초과합니다: {file_size} bytes"
        
        if file_size == 0:
            return False, "파일이 비어있습니다"
        
        # 오디오 유틸리티로 추가 검증
        is_valid, error_msg = self.audio_utils.validate_audio_file(audio_file_path)
        if not is_valid:
            return False, error_msg
        
        self.logger.debug(f"파일 검증 완료: {audio_file_path} ({file_size} bytes)")
        return True, "유효한 파일입니다"
    
    def _parse_success_response(self, response_data: Dict[str, Any]) -> ServerResponse:
        """
        성공 응답 파싱
        
        Args:
            response_data: 응답 데이터
            
        Returns:
            ServerResponse: 파싱된 응답
        """
        try:
            return ServerResponse.from_dict(response_data)
        except Exception as e:
            self.logger.error(f"응답 파싱 오류: {e}")
            return self._create_unknown_error_response(f"응답 파싱 실패: {str(e)}")
    
    def _parse_error_response(self, response: requests.Response) -> ServerResponse:
        """
        오류 응답 파싱
        
        Args:
            response: HTTP 응답
            
        Returns:
            ServerResponse: 오류 응답
        """
        try:
            error_data = response.json()
            error_message = error_data.get('detail', f'HTTP {response.status_code} 오류')
        except:
            error_message = f'HTTP {response.status_code} 오류'
        
        error_info = ErrorInfo(
            error_code=ErrorCode.SERVER_ERROR.value,
            error_message=error_message,
            recovery_actions=["서버 상태를 확인하고 다시 시도해주세요"]
        )
        
        return ServerResponse.create_error_response(error_info, self.session_id)
    
    def _create_validation_error_response(self, error_message: str) -> ServerResponse:
        """검증 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=ErrorCode.VALIDATION_ERROR.value,
            error_message=f"파일 검증 실패: {error_message}",
            recovery_actions=[
                "올바른 오디오 파일인지 확인해주세요",
                "파일 크기가 제한을 초과하지 않는지 확인해주세요",
                "지원하는 파일 형식인지 확인해주세요"
            ]
        )
        return ServerResponse.create_error_response(error_info, self.session_id)
    
    def _create_timeout_error_response(self, error_message: str) -> ServerResponse:
        """타임아웃 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=ErrorCode.TIMEOUT_ERROR.value,
            error_message=f"요청 타임아웃: {error_message}",
            recovery_actions=[
                "네트워크 연결을 확인해주세요",
                "잠시 후 다시 시도해주세요",
                "음성 파일 크기를 줄여보세요"
            ]
        )
        return ServerResponse.create_error_response(error_info, self.session_id)
    
    def _create_connection_error_response(self, error_message: str) -> ServerResponse:
        """연결 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=ErrorCode.NETWORK_ERROR.value,
            error_message=f"서버 연결 실패: {error_message}",
            recovery_actions=[
                "서버가 실행 중인지 확인해주세요",
                "네트워크 연결을 확인해주세요",
                "서버 주소가 올바른지 확인해주세요"
            ]
        )
        return ServerResponse.create_error_response(error_info, self.session_id)
    
    def _create_network_error_response(self, error_message: str) -> ServerResponse:
        """네트워크 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=ErrorCode.NETWORK_ERROR.value,
            error_message=f"네트워크 오류: {error_message}",
            recovery_actions=[
                "네트워크 연결을 확인해주세요",
                "잠시 후 다시 시도해주세요"
            ]
        )
        return ServerResponse.create_error_response(error_info, self.session_id)
    
    def _create_unknown_error_response(self, error_message: str) -> ServerResponse:
        """알 수 없는 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=ErrorCode.UNKNOWN_ERROR.value,
            error_message=f"알 수 없는 오류: {error_message}",
            recovery_actions=[
                "잠시 후 다시 시도해주세요",
                "문제가 지속되면 관리자에게 문의해주세요"
            ]
        )
        return ServerResponse.create_error_response(error_info, self.session_id)
    
    def download_tts_file(self, tts_url: str, save_path: str = None) -> Optional[str]:
        """
        TTS 음성 파일 다운로드
        
        Args:
            tts_url: TTS 파일 URL
            save_path: 저장할 경로 (None이면 임시 파일)
            
        Returns:
            Optional[str]: 저장된 파일 경로 (실패시 None)
        """
        try:
            # URL이 상대 경로인 경우 절대 URL로 변환
            if tts_url.startswith('/'):
                tts_url = urljoin(self.config.server.url, tts_url)
            
            self.logger.info(f"TTS 파일 다운로드: {tts_url}")
            
            # 파일 다운로드
            response = self.session.get(
                tts_url, 
                timeout=self.config.performance.download_timeout
            )
            response.raise_for_status()
            
            # 저장 경로 결정
            if save_path is None:
                save_path = self.audio_utils.create_temp_file(".wav")
            
            # 파일 저장
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"TTS 파일 저장 완료: {save_path}")
            return str(save_path)
            
        except Exception as e:
            self.logger.error(f"TTS 파일 다운로드 실패: {e}")
            return None
    
    def check_server_health(self) -> bool:
        """
        서버 상태 확인
        
        Returns:
            bool: 서버가 정상인지 여부
        """
        try:
            url = urljoin(self.config.server.url, "/health")
            response = self.session.get(url, timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                self.logger.info(f"서버 상태 확인 완료: {health_data}")
                return health_data.get('status') == 'healthy'
            else:
                self.logger.warning(f"서버 상태 확인 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"서버 상태 확인 오류: {e}")
            return False
    
    def get_session_id(self) -> Optional[str]:
        """현재 세션 ID 반환"""
        return self.session_id
    
    def set_session_id(self, session_id: str):
        """세션 ID 설정"""
        self.session_id = session_id
        self.logger.info(f"세션 ID 변경: {session_id}")
    
    def _handle_error_with_recovery(self, error_response: ServerResponse, context: Dict[str, Any]) -> ServerResponse:
        """
        오류 복구 시스템을 통한 오류 처리
        
        Args:
            error_response: 오류 응답
            context: 오류 컨텍스트
            
        Returns:
            ServerResponse: 복구 처리된 응답
        """
        try:
            # 재시도 콜백 함수 정의
            def retry_callback():
                audio_file_path = context.get('audio_file_path')
                if audio_file_path:
                    return self.send_audio_file(audio_file_path, self.session_id, enable_recovery=False)
                return None
            
            # 오류 복구 시도
            recovery_result = self.error_recovery.handle_error(
                error_response, context, retry_callback
            )
            
            # 복구 결과에 따른 처리
            if recovery_result.get('response') and recovery_result['response'].success:
                # 복구 성공
                return recovery_result['response']
            else:
                # 복구 실패 또는 사용자 개입 필요
                # 원본 오류 응답에 복구 정보 추가
                if error_response.error_info:
                    error_response.error_info.details = error_response.error_info.details or {}
                    error_response.error_info.details['recovery_result'] = recovery_result
                
                # UI 액션 추가
                if recovery_result.get('ui_actions'):
                    error_response.ui_actions.extend(recovery_result['ui_actions'])
                
                return error_response
                
        except Exception as e:
            self.logger.error(f"오류 복구 처리 중 예외 발생: {e}")
            return error_response
    
    def get_error_recovery_stats(self) -> Dict[str, Any]:
        """
        오류 복구 통계 조회
        
        Returns:
            Dict[str, Any]: 복구 통계
        """
        return self.error_recovery.get_recovery_stats()
    
    def reset_error_recovery_stats(self):
        """오류 복구 통계 초기화"""
        self.error_recovery.reset_stats()
    
    def close(self):
        """클라이언트 종료"""
        self.session.close()
        self.audio_utils.cleanup_temp_files()
        self.logger.info("VoiceClient 종료")