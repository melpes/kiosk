"""
클라이언트 오류 처리 예제
다양한 오류 상황에 대한 처리 방법을 보여주는 예제
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from client_package.client.voice_client import VoiceClient
from client_package.client.config_manager import ClientConfig
from client_package.client.models.communication_models import ServerResponse, ErrorInfo, ErrorCode
from client_package.utils.logger import get_logger
from client_package.utils.audio_utils import AudioUtils


class ErrorHandlingDemo:
    """클라이언트 오류 처리 데모 클래스"""
    
    def __init__(self, config_path: str = None):
        """
        데모 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        # 설정 로드
        if config_path is None:
            config_path = project_root / "client_package" / "config.json"
        
        self.config = ClientConfig.load_from_file(config_path)
        self.logger = get_logger(f"{__name__}.ErrorHandlingDemo")
        self.audio_utils = AudioUtils()
        
        # 클라이언트 초기화
        self.client = VoiceClient(self.config)
        
        # 오류 통계
        self.error_stats = {
            'total_errors': 0,
            'error_types': {},
            'recovery_attempts': 0,
            'successful_recoveries': 0
        }
        
        self.logger.info("오류 처리 데모 초기화 완료")
    
    def run_all_demos(self):
        """모든 오류 처리 데모 실행"""
        print("=== 클라이언트 오류 처리 데모 시작 ===\n")
        
        demos = [
            ("네트워크 오류 처리", self.demo_network_errors),
            ("파일 검증 오류 처리", self.demo_file_validation_errors),
            ("서버 오류 응답 처리", self.demo_server_error_responses),
            ("타임아웃 오류 처리", self.demo_timeout_errors),
            ("재시도 로직 테스트", self.demo_retry_logic),
            ("복구 시나리오 테스트", self.demo_recovery_scenarios)
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n--- {demo_name} ---")
            try:
                demo_func()
                print(f"✅ {demo_name} 완료")
            except Exception as e:
                print(f"❌ {demo_name} 실패: {e}")
                self.logger.error(f"{demo_name} 실패", exc_info=True)
            
            time.sleep(1)  # 데모 간 간격
        
        # 최종 통계 출력
        self.print_error_statistics()
        print("\n=== 오류 처리 데모 완료 ===")
    
    def demo_network_errors(self):
        """네트워크 오류 처리 데모"""
        print("네트워크 오류 상황을 시뮬레이션합니다...")
        
        # 잘못된 서버 URL로 테스트
        original_url = self.config.server.url
        self.config.server.url = "http://invalid-server:8000"
        
        # 새 클라이언트 생성 (잘못된 URL로)
        invalid_client = VoiceClient(self.config)
        
        # 테스트 음성 파일 생성
        test_file = self.audio_utils.create_test_audio_file()
        
        try:
            print("잘못된 서버로 요청 전송 중...")
            response = invalid_client.send_audio_file(test_file)
            
            # 오류 응답 처리
            self._handle_error_response(response, "네트워크 연결 실패")
            
        finally:
            # 원래 URL 복원
            self.config.server.url = original_url
            invalid_client.close()
            self.audio_utils.cleanup_temp_files()
    
    def demo_file_validation_errors(self):
        """파일 검증 오류 처리 데모"""
        print("파일 검증 오류 상황을 테스트합니다...")
        
        test_cases = [
            ("존재하지 않는 파일", "/nonexistent/file.wav"),
            ("빈 파일", self._create_empty_file()),
            ("잘못된 형식", self._create_invalid_format_file()),
            ("크기 초과 파일", self._create_oversized_file())
        ]
        
        for test_name, file_path in test_cases:
            print(f"  테스트: {test_name}")
            
            try:
                response = self.client.send_audio_file(file_path)
                self._handle_error_response(response, test_name)
                
            except Exception as e:
                print(f"    예외 발생: {e}")
                self._record_error("파일 검증 오류", str(e))
    
    def demo_server_error_responses(self):
        """서버 오류 응답 처리 데모"""
        print("서버 오류 응답 처리를 테스트합니다...")
        
        # 서버가 실행 중인지 확인
        if not self.client.check_server_health():
            print("  서버가 실행되지 않음 - 오류 응답 시뮬레이션")
            
            # 모의 서버 오류 응답 생성
            mock_responses = [
                self._create_mock_server_error("음성 인식 실패", ErrorCode.SPEECH_RECOGNITION_ERROR),
                self._create_mock_server_error("의도 파악 실패", ErrorCode.INTENT_RECOGNITION_ERROR),
                self._create_mock_server_error("주문 처리 실패", ErrorCode.ORDER_PROCESSING_ERROR),
                self._create_mock_server_error("서버 내부 오류", ErrorCode.SERVER_ERROR)
            ]
            
            for response in mock_responses:
                print(f"  처리 중: {response.error_info.error_code}")
                self._handle_error_response(response, "서버 오류 시뮬레이션")
        else:
            print("  서버가 정상 실행 중 - 실제 테스트 수행")
            # 실제 서버와 테스트 (잘못된 파일로)
            test_file = self._create_corrupted_audio_file()
            response = self.client.send_audio_file(test_file)
            self._handle_error_response(response, "손상된 오디오 파일")
    
    def demo_timeout_errors(self):
        """타임아웃 오류 처리 데모"""
        print("타임아웃 오류 처리를 테스트합니다...")
        
        # 타임아웃 설정을 매우 짧게 변경
        original_timeout = self.config.server.timeout
        self.config.server.timeout = 0.1  # 100ms로 설정
        
        # 새 클라이언트 생성 (짧은 타임아웃으로)
        timeout_client = VoiceClient(self.config)
        
        try:
            # 큰 파일로 타임아웃 유발
            large_file = self._create_large_audio_file()
            print("  큰 파일로 타임아웃 유발 중...")
            
            response = timeout_client.send_audio_file(large_file)
            self._handle_error_response(response, "타임아웃 테스트")
            
        finally:
            # 원래 타임아웃 복원
            self.config.server.timeout = original_timeout
            timeout_client.close()
    
    def demo_retry_logic(self):
        """재시도 로직 테스트"""
        print("재시도 로직을 테스트합니다...")
        
        # 재시도 설정 확인
        max_retries = self.config.server.max_retries
        retry_delay = self.config.server.retry_delay
        
        print(f"  최대 재시도 횟수: {max_retries}")
        print(f"  재시도 간격: {retry_delay}초")
        
        # 간헐적으로 실패하는 상황 시뮬레이션
        # (실제로는 서버가 없는 상황에서 재시도 동작 확인)
        original_url = self.config.server.url
        self.config.server.url = "http://localhost:9999"  # 존재하지 않는 포트
        
        retry_client = VoiceClient(self.config)
        test_file = self.audio_utils.create_test_audio_file()
        
        try:
            start_time = time.time()
            print("  재시도 로직 실행 중...")
            
            response = retry_client.send_audio_file(test_file)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"  총 소요 시간: {total_time:.2f}초")
            self._handle_error_response(response, "재시도 로직 테스트")
            
        finally:
            self.config.server.url = original_url
            retry_client.close()
    
    def demo_recovery_scenarios(self):
        """복구 시나리오 테스트"""
        print("다양한 복구 시나리오를 테스트합니다...")
        
        recovery_scenarios = [
            {
                'name': '네트워크 복구',
                'error_type': ErrorCode.NETWORK_ERROR,
                'recovery_actions': ['네트워크 연결 확인', '서버 상태 확인', '재시도']
            },
            {
                'name': '음성 인식 복구',
                'error_type': ErrorCode.SPEECH_RECOGNITION_ERROR,
                'recovery_actions': ['더 명확하게 발음', '주변 소음 제거', '다시 녹음']
            },
            {
                'name': '주문 처리 복구',
                'error_type': ErrorCode.ORDER_PROCESSING_ERROR,
                'recovery_actions': ['주문 내용 재확인', '메뉴 다시 선택', '처음부터 주문']
            }
        ]
        
        for scenario in recovery_scenarios:
            print(f"  시나리오: {scenario['name']}")
            
            # 모의 오류 응답 생성
            mock_response = self._create_mock_error_response(
                scenario['error_type'],
                f"{scenario['name']} 테스트 오류",
                scenario['recovery_actions']
            )
            
            # 복구 시나리오 실행
            success = self._execute_recovery_scenario(mock_response, scenario)
            
            if success:
                print(f"    ✅ {scenario['name']} 복구 성공")
                self.error_stats['successful_recoveries'] += 1
            else:
                print(f"    ❌ {scenario['name']} 복구 실패")
            
            self.error_stats['recovery_attempts'] += 1
    
    def _handle_error_response(self, response: ServerResponse, context: str):
        """
        오류 응답 처리
        
        Args:
            response: 서버 응답
            context: 오류 컨텍스트
        """
        if not response.success and response.error_info:
            error_info = response.error_info
            
            print(f"    오류 코드: {error_info.error_code}")
            print(f"    오류 메시지: {error_info.error_message}")
            print(f"    복구 액션: {', '.join(error_info.recovery_actions)}")
            
            # UI 액션 처리
            if response.ui_actions:
                print(f"    UI 액션: {len(response.ui_actions)}개")
                for action in response.ui_actions:
                    print(f"      - {action.action_type}: {action.data}")
            
            # 오류 통계 기록
            self._record_error(error_info.error_code, context)
            
            # 자동 복구 시도
            if self._should_attempt_recovery(error_info):
                print("    자동 복구 시도 중...")
                self._attempt_automatic_recovery(error_info, context)
        else:
            print(f"    성공 응답: {response.message}")
    
    def _should_attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """
        자동 복구를 시도할지 결정
        
        Args:
            error_info: 오류 정보
            
        Returns:
            bool: 복구 시도 여부
        """
        # 복구 가능한 오류 타입들
        recoverable_errors = [
            ErrorCode.NETWORK_ERROR.value,
            ErrorCode.TIMEOUT_ERROR.value,
            ErrorCode.SPEECH_RECOGNITION_ERROR.value
        ]
        
        return error_info.error_code in recoverable_errors
    
    def _attempt_automatic_recovery(self, error_info: ErrorInfo, context: str):
        """
        자동 복구 시도
        
        Args:
            error_info: 오류 정보
            context: 오류 컨텍스트
        """
        recovery_actions = error_info.recovery_actions
        
        for i, action in enumerate(recovery_actions[:2]):  # 최대 2개 액션만 시도
            print(f"      복구 액션 {i+1}: {action}")
            
            # 실제 복구 로직 (시뮬레이션)
            if "다시 시도" in action:
                time.sleep(1)
                print("        재시도 완료")
            elif "연결 확인" in action:
                is_healthy = self.client.check_server_health()
                print(f"        서버 상태: {'정상' if is_healthy else '비정상'}")
            elif "파일 확인" in action:
                print("        파일 검증 완료")
            
            time.sleep(0.5)
    
    def _execute_recovery_scenario(self, response: ServerResponse, scenario: Dict[str, Any]) -> bool:
        """
        복구 시나리오 실행
        
        Args:
            response: 오류 응답
            scenario: 복구 시나리오 정보
            
        Returns:
            bool: 복구 성공 여부
        """
        try:
            # 복구 액션들을 순차적으로 실행
            for action in scenario['recovery_actions']:
                print(f"      실행 중: {action}")
                time.sleep(0.3)  # 시뮬레이션 지연
            
            # 복구 성공 시뮬레이션 (70% 확률)
            import random
            return random.random() > 0.3
            
        except Exception as e:
            print(f"      복구 실행 중 오류: {e}")
            return False
    
    def _record_error(self, error_type: str, context: str):
        """
        오류 통계 기록
        
        Args:
            error_type: 오류 타입
            context: 오류 컨텍스트
        """
        self.error_stats['total_errors'] += 1
        
        if error_type not in self.error_stats['error_types']:
            self.error_stats['error_types'][error_type] = {
                'count': 0,
                'contexts': []
            }
        
        self.error_stats['error_types'][error_type]['count'] += 1
        self.error_stats['error_types'][error_type]['contexts'].append(context)
    
    def _create_empty_file(self) -> str:
        """빈 파일 생성"""
        temp_file = self.audio_utils.create_temp_file(".wav")
        Path(temp_file).touch()
        return temp_file
    
    def _create_invalid_format_file(self) -> str:
        """잘못된 형식 파일 생성"""
        temp_file = self.audio_utils.create_temp_file(".txt")
        with open(temp_file, 'w') as f:
            f.write("This is not an audio file")
        return temp_file
    
    def _create_oversized_file(self) -> str:
        """크기 초과 파일 생성"""
        temp_file = self.audio_utils.create_temp_file(".wav")
        
        # 설정된 최대 크기보다 큰 파일 생성
        max_size = self.config.audio.max_file_size
        oversized_data = b'0' * (max_size + 1000)
        
        with open(temp_file, 'wb') as f:
            f.write(oversized_data)
        
        return temp_file
    
    def _create_corrupted_audio_file(self) -> str:
        """손상된 오디오 파일 생성"""
        temp_file = self.audio_utils.create_temp_file(".wav")
        
        # WAV 헤더만 있고 데이터가 손상된 파일
        corrupted_data = b'RIFF\x00\x00\x00\x00WAVEfmt \x00\x00\x00\x00'
        
        with open(temp_file, 'wb') as f:
            f.write(corrupted_data)
        
        return temp_file
    
    def _create_large_audio_file(self) -> str:
        """큰 오디오 파일 생성 (타임아웃 유발용)"""
        temp_file = self.audio_utils.create_temp_file(".wav")
        
        # 1MB 크기의 더미 오디오 데이터
        large_data = b'0' * (1024 * 1024)
        
        with open(temp_file, 'wb') as f:
            f.write(large_data)
        
        return temp_file
    
    def _create_mock_server_error(self, message: str, error_code: ErrorCode) -> ServerResponse:
        """모의 서버 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=error_code.value,
            error_message=message,
            recovery_actions=["다시 시도해주세요", "문제가 지속되면 관리자에게 문의해주세요"]
        )
        
        return ServerResponse.create_error_response(error_info)
    
    def _create_mock_error_response(self, error_code: ErrorCode, message: str, recovery_actions: List[str]) -> ServerResponse:
        """모의 오류 응답 생성"""
        error_info = ErrorInfo(
            error_code=error_code.value,
            error_message=message,
            recovery_actions=recovery_actions
        )
        
        return ServerResponse.create_error_response(error_info)
    
    def print_error_statistics(self):
        """오류 통계 출력"""
        print("\n=== 오류 처리 통계 ===")
        print(f"총 오류 수: {self.error_stats['total_errors']}")
        print(f"복구 시도 수: {self.error_stats['recovery_attempts']}")
        print(f"성공한 복구 수: {self.error_stats['successful_recoveries']}")
        
        if self.error_stats['recovery_attempts'] > 0:
            success_rate = (self.error_stats['successful_recoveries'] / self.error_stats['recovery_attempts']) * 100
            print(f"복구 성공률: {success_rate:.1f}%")
        
        print("\n오류 타입별 통계:")
        for error_type, stats in self.error_stats['error_types'].items():
            print(f"  {error_type}: {stats['count']}회")
            for context in stats['contexts'][:3]:  # 최대 3개만 표시
                print(f"    - {context}")
    
    def cleanup(self):
        """리소스 정리"""
        self.client.close()
        self.audio_utils.cleanup_temp_files()
        self.logger.info("오류 처리 데모 정리 완료")


def main():
    """메인 함수"""
    demo = None
    try:
        # 설정 파일 경로
        config_path = Path(__file__).parent.parent / "client_package" / "config.json"
        
        # 데모 실행
        demo = ErrorHandlingDemo(config_path)
        demo.run_all_demos()
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"데모 실행 중 오류 발생: {e}")
    finally:
        if demo:
            demo.cleanup()


if __name__ == "__main__":
    main()