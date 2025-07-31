"""
키오스크 클라이언트 예제
음성 파일을 서버로 전송하고 응답을 처리하는 클라이언트 구현
모니터링 기능이 통합된 버전
"""

import os
import time
import json
import requests
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

# 프로젝트 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.models.communication_models import ServerResponse, ErrorInfo, ErrorCode
from src.logger import get_logger
from examples.client_monitoring import get_client_monitor, monitor_request


@dataclass
class ClientConfig:
    """클라이언트 설정"""
    server_url: str = "http://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_formats: List[str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ['.wav']


class VoiceClient:
    """
    음성 키오스크 클라이언트
    서버와의 HTTP 통신을 담당하는 클래스
    """
    
    def __init__(self, config: ClientConfig = None):
        """
        클라이언트 초기화
        
        Args:
            config: 클라이언트 설정
        """
        self.config = config or ClientConfig()
        self.session = requests.Session()
        self.session_id: Optional[str] = None
        self.logger = get_logger(f"{__name__}.VoiceClient")
        
        # 요청 헤더 설정
        self.session.headers.update({
            'User-Agent': 'VoiceKioskClient/1.0'
        })
        
        self.logger.info(f"VoiceClient 초기화 완료 (서버: {self.config.server_url})")
    
    def send_audio_file(self, audio_file_path: str, session_id: str = None) -> ServerResponse:
        """
        음성 파일을 서버로 전송하고 응답을 받음 (모니터링 통합)
        
        Args:
            audio_file_path: 전송할 음성 파일 경로
            session_id: 세션 ID (선택사항)
            
        Returns:
            ServerResponse: 서버 응답
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            ValueError: 지원하지 않는 파일 형식인 경우
            requests.RequestException: 네트워크 오류
        """
        # 모니터링 시작
        request_id = str(uuid.uuid4())
        monitor = get_client_monitor()
        
        try:
            # 파일 검증
            self._validate_audio_file(audio_file_path)
            
            # 파일 크기 확인
            file_size = Path(audio_file_path).stat().st_size
            
            # 모니터링 시작 (Requirements: 6.1)
            monitor.start_request(request_id, file_size)
            
            # 세션 ID 설정
            if session_id:
                self.session_id = session_id
            
            # 재시도 로직으로 파일 전송
            for attempt in range(self.config.max_retries):
                try:
                    self.logger.info(f"음성 파일 전송 시도 {attempt + 1}/{self.config.max_retries}: {audio_file_path}")
                    
                    response = self._send_file_with_retry_monitored(audio_file_path, request_id)
                    
                    self.logger.info(f"음성 파일 전송 성공 (처리 시간: {response.processing_time:.2f}초)")
                    
                    # 모니터링 완료 (Requirements: 6.4)
                    monitor.complete_request(request_id)
                    
                    return response
                    
                except requests.exceptions.Timeout as e:
                    error_msg = f"요청 타임아웃 (시도 {attempt + 1}): {e}"
                    self.logger.warning(error_msg)
                    
                    if attempt == self.config.max_retries - 1:
                        # 모니터링 오류 기록 (Requirements: 6.3)
                        monitor.log_error(request_id, error_msg, "TIMEOUT_ERROR")
                        return self._create_timeout_error_response(str(e))
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    
                except requests.exceptions.ConnectionError as e:
                    error_msg = f"연결 오류 (시도 {attempt + 1}): {e}"
                    self.logger.warning(error_msg)
                    
                    if attempt == self.config.max_retries - 1:
                        # 모니터링 오류 기록 (Requirements: 6.3)
                        monitor.log_error(request_id, error_msg, "CONNECTION_ERROR")
                        return self._create_connection_error_response(str(e))
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    
                except requests.exceptions.RequestException as e:
                    error_msg = f"요청 오류 (시도 {attempt + 1}): {e}"
                    self.logger.error(error_msg)
                    
                    if attempt == self.config.max_retries - 1:
                        # 모니터링 오류 기록 (Requirements: 6.3)
                        monitor.log_error(request_id, error_msg, "REQUEST_ERROR")
                        return self._create_network_error_response(str(e))
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    
                except Exception as e:
                    error_msg = f"예상치 못한 오류: {e}"
                    self.logger.error(error_msg)
                    
                    # 모니터링 오류 기록 (Requirements: 6.3)
                    monitor.log_error(request_id, error_msg, "UNKNOWN_ERROR")
                    return self._create_unknown_error_response(str(e))
            
            # 모든 재시도 실패
            error_msg = "모든 재시도 실패"
            monitor.log_error(request_id, error_msg, "RETRY_EXHAUSTED")
            return self._create_network_error_response(error_msg)
            
        except Exception as e:
            # 초기 검증 오류 등
            error_msg = f"요청 초기화 실패: {e}"
            monitor.log_error(request_id, error_msg, "INITIALIZATION_ERROR")
            return self._create_unknown_error_response(str(e))
    
    def _send_file_with_retry_monitored(self, audio_file_path: str, request_id: str) -> ServerResponse:
        """
        모니터링이 통합된 파일 전송 수행
        
        Args:
            audio_file_path: 음성 파일 경로
            request_id: 요청 ID
            
        Returns:
            ServerResponse: 서버 응답
        """
        monitor = get_client_monitor()
        
        url = f"{self.config.server_url}/api/voice/process"
        
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
            
            # 파일 업로드 시작 모니터링
            monitor.start_file_upload(request_id)
            
            # HTTP 요청 전송
            start_time = time.time()
            response = self.session.post(
                url,
                files=files,
                data=data,
                timeout=self.config.timeout
            )
            request_time = time.time() - start_time
            
            # 파일 업로드 완료 모니터링
            monitor.complete_file_upload(request_id)
            
            self.logger.debug(f"HTTP 요청 완료 (상태: {response.status_code}, 시간: {request_time:.2f}초)")
            
            # 응답 처리
            if response.status_code == 200:
                response_data = response.json()
                server_response = self._parse_success_response(response_data)
                
                # 응답 수신 모니터링
                response_size = len(response.content)
                server_processing_time = response_data.get('processing_time', 0)
                monitor.receive_response(request_id, response_size, server_processing_time)
                
                return server_response
            else:
                return self._parse_error_response(response)
    
    def _send_file_with_retry(self, audio_file_path: str) -> ServerResponse:
        """
        실제 파일 전송 수행
        
        Args:
            audio_file_path: 음성 파일 경로
            
        Returns:
            ServerResponse: 서버 응답
        """
        url = f"{self.config.server_url}/api/voice/process"
        
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
                timeout=self.config.timeout
            )
            request_time = time.time() - start_time
            
            self.logger.debug(f"HTTP 요청 완료 (상태: {response.status_code}, 시간: {request_time:.2f}초)")
            
            # 응답 처리
            if response.status_code == 200:
                return self._parse_success_response(response.json())
            else:
                return self._parse_error_response(response)
    
    def _validate_audio_file(self, audio_file_path: str):
        """
        음성 파일 유효성 검증
        
        Args:
            audio_file_path: 검증할 파일 경로
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
            ValueError: 지원하지 않는 파일 형식인 경우
        """
        file_path = Path(audio_file_path)
        
        # 파일 존재 확인
        if not file_path.exists():
            raise FileNotFoundError(f"음성 파일을 찾을 수 없습니다: {audio_file_path}")
        
        # 파일 형식 확인
        if file_path.suffix.lower() not in self.config.supported_formats:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path.suffix}")
        
        # 파일 크기 확인
        file_size = file_path.stat().st_size
        if file_size > self.config.max_file_size:
            raise ValueError(f"파일 크기가 제한을 초과합니다: {file_size} bytes")
        
        self.logger.debug(f"파일 검증 완료: {audio_file_path} ({file_size} bytes)")
    
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
    
    def handle_response(self, response: ServerResponse) -> None:
        """
        서버 응답 처리
        
        Args:
            response: 처리할 서버 응답
        """
        self.logger.info(f"서버 응답 처리 시작 (성공: {response.success})")
        
        if response.success:
            self._handle_success_response(response)
        else:
            self._handle_error_response(response)
    
    def _handle_success_response(self, response: ServerResponse):
        """성공 응답 처리"""
        print(f"\n✅ 처리 성공: {response.message}")
        print(f"⏱️  처리 시간: {response.processing_time:.2f}초")
        
        # TTS 음성 파일 처리
        if response.tts_audio_url:
            print(f"🔊 TTS 음성: {response.tts_audio_url}")
            self._download_and_play_tts(response.tts_audio_url)
        
        # 주문 데이터 처리
        if response.order_data:
            print(f"\n📋 주문 정보:")
            print(f"   주문 ID: {response.order_data.order_id}")
            print(f"   상태: {response.order_data.status}")
            print(f"   총 금액: {response.order_data.total_amount:,.0f}원")
            print(f"   아이템 수: {response.order_data.item_count}")
            
            if response.order_data.items:
                print("   주문 내역:")
                for item in response.order_data.items:
                    print(f"     - {item['name']} x{item['quantity']} ({item['price']:,.0f}원)")
        
        # UI 액션 처리
        if response.ui_actions:
            print(f"\n🎯 UI 액션 ({len(response.ui_actions)}개):")
            for i, action in enumerate(response.ui_actions, 1):
                print(f"   {i}. {action.action_type}")
                if action.requires_user_input:
                    print(f"      (사용자 입력 필요)")
                if action.timeout_seconds:
                    print(f"      (타임아웃: {action.timeout_seconds}초)")
    
    def _handle_error_response(self, response: ServerResponse):
        """오류 응답 처리"""
        print(f"\n❌ 처리 실패: {response.message}")
        
        if response.error_info:
            print(f"🔍 오류 코드: {response.error_info.error_code}")
            print(f"📝 오류 메시지: {response.error_info.error_message}")
            
            if response.error_info.recovery_actions:
                print("💡 해결 방법:")
                for i, action in enumerate(response.error_info.recovery_actions, 1):
                    print(f"   {i}. {action}")
    
    def _download_and_play_tts(self, tts_url: str):
        """
        TTS 음성 파일 다운로드 및 재생
        
        Args:
            tts_url: TTS 파일 URL
        """
        try:
            # URL이 상대 경로인 경우 절대 URL로 변환
            if tts_url.startswith('/'):
                tts_url = f"{self.config.server_url}{tts_url}"
            
            self.logger.info(f"TTS 파일 다운로드: {tts_url}")
            
            # 파일 다운로드
            response = self.session.get(tts_url, timeout=10)
            response.raise_for_status()
            
            # 임시 파일로 저장
            temp_dir = Path.cwd() / "temp_audio"
            temp_dir.mkdir(exist_ok=True)
            
            temp_file = temp_dir / f"tts_{int(time.time())}.wav"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            print(f"💾 TTS 파일 저장: {temp_file}")
            
            # 실제 환경에서는 여기서 음성 재생
            # 예: pygame, playsound, 또는 시스템 명령어 사용
            print("🔊 음성 재생 시뮬레이션 (실제 환경에서는 음성이 재생됩니다)")
            
        except Exception as e:
            self.logger.error(f"TTS 파일 처리 실패: {e}")
            print(f"⚠️  TTS 파일 처리 실패: {e}")
    
    def check_server_health(self) -> bool:
        """
        서버 상태 확인
        
        Returns:
            bool: 서버가 정상인지 여부
        """
        try:
            url = f"{self.config.server_url}/health"
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
    
    def close(self):
        """클라이언트 종료"""
        self.session.close()
        self.logger.info("VoiceClient 종료")


class KioskClientDemo:
    """키오스크 클라이언트 데모 클래스"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        데모 초기화
        
        Args:
            server_url: 서버 URL
        """
        config = ClientConfig(server_url=server_url)
        self.client = VoiceClient(config)
        self.logger = get_logger(f"{__name__}.KioskClientDemo")
    
    def run_demo(self):
        """데모 실행"""
        print("🎤 키오스크 클라이언트 데모 시작")
        print("=" * 50)
        
        # 서버 상태 확인
        print("\n1. 서버 상태 확인...")
        if not self.client.check_server_health():
            print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
            return
        print("✅ 서버 연결 정상")
        
        # 테스트 음성 파일 찾기
        test_files = self._find_test_audio_files()
        if not test_files:
            print("❌ 테스트용 음성 파일을 찾을 수 없습니다.")
            print("💡 프로젝트 루트에 .wav 파일을 추가하거나 data/ 디렉토리를 확인해주세요.")
            return
        
        print(f"\n2. 테스트 파일 발견 ({len(test_files)}개)")
        for i, file_path in enumerate(test_files, 1):
            print(f"   {i}. {file_path}")
        
        # 각 파일에 대해 테스트 수행
        for i, file_path in enumerate(test_files, 1):
            print(f"\n3.{i} 음성 파일 처리 테스트: {Path(file_path).name}")
            print("-" * 40)
            
            try:
                # 음성 파일 전송
                response = self.client.send_audio_file(file_path)
                
                # 응답 처리
                self.client.handle_response(response)
                
                # 잠시 대기
                if i < len(test_files):
                    print("\n⏳ 다음 테스트까지 3초 대기...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ 테스트 실패: {e}")
                self.logger.error(f"데모 테스트 실패: {e}")
        
        print("\n🎉 데모 완료!")
        print("=" * 50)
    
    def _find_test_audio_files(self) -> List[str]:
        """테스트용 음성 파일 찾기"""
        test_files = []
        
        # 프로젝트 루트에서 .wav 파일 찾기
        project_root = Path(__file__).parent.parent
        
        # 루트 디렉토리의 .wav 파일들
        for wav_file in project_root.glob("*.wav"):
            test_files.append(str(wav_file))
        
        # data 디렉토리의 .wav 파일들
        data_dir = project_root / "data"
        if data_dir.exists():
            for wav_file in data_dir.glob("**/*.wav"):
                test_files.append(str(wav_file))
        
        return sorted(test_files)[:3]  # 최대 3개까지만
    
    def close(self):
        """데모 종료"""
        self.client.close()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="키오스크 클라이언트 예제")
    parser.add_argument(
        "--server-url", 
        default="http://localhost:8000",
        help="서버 URL (기본값: http://localhost:8000)"
    )
    parser.add_argument(
        "--audio-file",
        help="전송할 음성 파일 경로"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="데모 모드 실행"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        # 데모 모드
        demo = KioskClientDemo(args.server_url)
        try:
            demo.run_demo()
        finally:
            demo.close()
    
    elif args.audio_file:
        # 단일 파일 테스트
        config = ClientConfig(server_url=args.server_url)
        client = VoiceClient(config)
        
        try:
            print(f"🎤 음성 파일 전송: {args.audio_file}")
            response = client.send_audio_file(args.audio_file)
            client.handle_response(response)
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            client.close()
    
    else:
        # 기본 데모 실행
        demo = KioskClientDemo(args.server_url)
        try:
            demo.run_demo()
        finally:
            demo.close()


if __name__ == "__main__":
    main()