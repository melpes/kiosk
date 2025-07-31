"""
키오스크 클라이언트 데모
"""

import time
from pathlib import Path
from typing import List

from client import VoiceClient, ConfigManager, KioskUIManager
from utils.logger import get_logger


class KioskClientDemo:
    """키오스크 클라이언트 데모 클래스"""
    
    def __init__(self, config=None):
        """
        데모 초기화
        
        Args:
            config: 클라이언트 설정 (None이면 기본 설정 로드)
        """
        if config is None:
            config_path = Path(__file__).parent.parent / "config.json"
            config = ConfigManager.load_config(str(config_path))
        
        self.config = config
        self.client = VoiceClient(config)
        self.ui_manager = KioskUIManager(self.client)
        self.logger = get_logger(f"{__name__}.KioskClientDemo")
    
    def run_demo(self):
        """데모 실행"""
        print("🎤 키오스크 클라이언트 데모 시작")
        print("=" * 60)
        
        try:
            # 1. 시스템 정보 표시
            self._show_system_info()
            
            # 2. 서버 상태 확인
            if not self._check_server_connection():
                return
            
            # 3. 테스트 파일 확인
            test_files = self._find_test_audio_files()
            if not test_files:
                self._show_no_test_files_message()
                return
            
            # 4. 데모 시나리오 실행
            self._run_demo_scenarios(test_files)
            
        except Exception as e:
            self.logger.error(f"데모 실행 중 오류: {e}")
            print(f"❌ 데모 실행 실패: {e}")
        
        finally:
            print("\n🎉 데모 완료!")
            print("=" * 60)
    
    def _show_system_info(self):
        """시스템 정보 표시"""
        print("\n📊 시스템 정보:")
        print(f"   서버 URL: {self.config.server.url}")
        print(f"   세션 ID: {self.client.get_session_id()}")
        print(f"   타임아웃: {self.config.server.timeout}초")
        print(f"   최대 재시도: {self.config.server.max_retries}회")
        
        # 오디오 플레이어 정보
        available_players = self.ui_manager.audio_utils.get_available_players()
        if available_players:
            print(f"   오디오 플레이어: {', '.join(available_players)}")
        else:
            print("   오디오 플레이어: 없음 (시뮬레이션 모드)")
    
    def _check_server_connection(self) -> bool:
        """서버 연결 확인"""
        print("\n1. 서버 연결 확인...")
        
        if self.client.check_server_health():
            print("✅ 서버 연결 정상")
            return True
        else:
            print("❌ 서버에 연결할 수 없습니다.")
            print("💡 해결 방법:")
            print("   - 서버가 실행 중인지 확인하세요")
            print("   - 네트워크 연결을 확인하세요")
            print("   - 서버 URL이 올바른지 확인하세요")
            return False
    
    def _find_test_audio_files(self) -> List[str]:
        """테스트용 음성 파일 찾기"""
        test_files = []
        
        # 프로젝트 루트에서 .wav 파일 찾기
        project_root = Path(__file__).parent.parent.parent
        
        # 루트 디렉토리의 .wav 파일들
        for wav_file in project_root.glob("*.wav"):
            test_files.append(str(wav_file))
        
        # data 디렉토리의 .wav 파일들
        data_dir = project_root / "data"
        if data_dir.exists():
            for wav_file in data_dir.glob("**/*.wav"):
                test_files.append(str(wav_file))
        
        # examples/test_audio 디렉토리
        test_audio_dir = Path(__file__).parent / "test_audio"
        if test_audio_dir.exists():
            for wav_file in test_audio_dir.glob("*.wav"):
                test_files.append(str(wav_file))
        
        return sorted(test_files)[:3]  # 최대 3개까지만
    
    def _show_no_test_files_message(self):
        """테스트 파일이 없을 때 메시지 표시"""
        print("❌ 테스트용 음성 파일을 찾을 수 없습니다.")
        print("\n💡 테스트 파일 준비 방법:")
        print("   1. 프로젝트 루트에 .wav 파일을 복사하세요")
        print("   2. data/ 디렉토리에 .wav 파일을 추가하세요")
        print("   3. examples/test_audio/ 디렉토리를 만들고 파일을 추가하세요")
        print("\n📝 지원하는 파일 형식:")
        for fmt in self.config.audio.supported_formats:
            print(f"   - {fmt}")
        print(f"\n📏 최대 파일 크기: {self.config.audio.max_file_size:,} bytes")
    
    def _run_demo_scenarios(self, test_files: List[str]):
        """데모 시나리오 실행"""
        print(f"\n2. 테스트 파일 발견 ({len(test_files)}개)")
        for i, file_path in enumerate(test_files, 1):
            file_name = Path(file_path).name
            file_size = Path(file_path).stat().st_size
            print(f"   {i}. {file_name} ({file_size:,} bytes)")
        
        # 각 파일에 대해 테스트 수행
        for i, file_path in enumerate(test_files, 1):
            self._run_single_test(i, file_path, len(test_files))
            
            # 다음 테스트까지 대기 (마지막 테스트가 아닌 경우)
            if i < len(test_files):
                self._wait_between_tests()
    
    def _run_single_test(self, test_num: int, file_path: str, total_tests: int):
        """단일 테스트 실행"""
        file_name = Path(file_path).name
        
        print(f"\n3.{test_num} 음성 파일 처리 테스트: {file_name}")
        print("-" * 50)
        
        try:
            # 파일 정보 표시
            audio_info = self.ui_manager.audio_utils.get_audio_info(file_path)
            if audio_info:
                print(f"   📊 파일 정보:")
                print(f"      길이: {audio_info['duration']:.2f}초")
                print(f"      샘플링 레이트: {audio_info['samplerate']} Hz")
                print(f"      채널: {audio_info['channels']}개")
            
            # 음성 파일 전송
            print(f"   📤 서버로 전송 중...")
            start_time = time.time()
            
            response = self.client.send_audio_file(file_path)
            
            upload_time = time.time() - start_time
            print(f"   ⏱️  업로드 시간: {upload_time:.2f}초")
            
            # 응답 처리
            print(f"   📥 응답 처리 중...")
            self.ui_manager.handle_response(response)
            
            # 테스트 결과 요약
            self._show_test_result(test_num, response, upload_time)
            
        except Exception as e:
            print(f"❌ 테스트 {test_num} 실패: {e}")
            self.logger.error(f"테스트 {test_num} 실패: {e}")
    
    def _show_test_result(self, test_num: int, response, upload_time: float):
        """테스트 결과 표시"""
        print(f"\n   📋 테스트 {test_num} 결과:")
        
        if response.success:
            print(f"      ✅ 성공")
            print(f"      ⏱️  총 처리 시간: {response.processing_time:.2f}초")
            print(f"      📤 업로드 시간: {upload_time:.2f}초")
            print(f"      🔄 서버 처리 시간: {response.processing_time - upload_time:.2f}초")
            
            if response.order_data:
                print(f"      📋 주문 상태: {response.order_data.status}")
                print(f"      💰 주문 금액: {response.order_data.total_amount:,.0f}원")
            
            if response.ui_actions:
                print(f"      🎯 UI 액션: {len(response.ui_actions)}개")
        else:
            print(f"      ❌ 실패")
            if response.error_info:
                print(f"      🔍 오류 코드: {response.error_info.error_code}")
                print(f"      📝 오류 메시지: {response.error_info.error_message}")
    
    def _wait_between_tests(self):
        """테스트 간 대기"""
        wait_time = 3
        print(f"\n⏳ 다음 테스트까지 {wait_time}초 대기...")
        
        for i in range(wait_time, 0, -1):
            print(f"   {i}초 남음...", end="\r")
            time.sleep(1)
        print("   시작!      ")
    
    def show_final_summary(self):
        """최종 요약 표시"""
        print("\n📊 최종 상태:")
        self.ui_manager.show_status()
        
        # 세션 정보
        print(f"\n🔗 세션 정보:")
        print(f"   세션 ID: {self.client.get_session_id()}")
        
        # 현재 주문 정보
        current_order = self.ui_manager.get_current_order()
        if current_order:
            print(f"   현재 주문: {current_order.order_id}")
            print(f"   주문 상태: {current_order.status}")
            print(f"   주문 금액: {current_order.total_amount:,.0f}원")
        else:
            print("   현재 주문: 없음")
    
    def close(self):
        """데모 종료"""
        try:
            self.show_final_summary()
        except:
            pass
        
        self.client.close()
        self.logger.info("데모 종료")


def main():
    """메인 함수 (독립 실행용)"""
    demo = KioskClientDemo()
    try:
        demo.run_demo()
    finally:
        demo.close()


if __name__ == "__main__":
    main()