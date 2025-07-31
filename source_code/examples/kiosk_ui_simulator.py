"""
키오스크 UI 시뮬레이터
콘솔 기반으로 키오스크 인터페이스를 시뮬레이션하는 모듈
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess
import platform

# 프로젝트 모듈 import
sys.path.append(str(Path(__file__).parent.parent))

from src.models.communication_models import (
    ServerResponse, OrderData, UIAction, UIActionType, 
    MenuOption, PaymentData, ErrorInfo
)
from src.logger import get_logger
from examples.kiosk_client_example import VoiceClient, ClientConfig


@dataclass
class UIState:
    """UI 상태 정보"""
    current_screen: str = "welcome"  # welcome, menu, order, payment, confirmation, error
    order_data: Optional[OrderData] = None
    menu_options: List[MenuOption] = None
    payment_data: Optional[PaymentData] = None
    error_info: Optional[ErrorInfo] = None
    last_message: str = ""
    session_id: Optional[str] = None
    is_listening: bool = False


class KioskUISimulator:
    """
    키오스크 UI 시뮬레이터
    콘솔 기반으로 키오스크 화면을 시뮬레이션
    """
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        시뮬레이터 초기화
        
        Args:
            server_url: 서버 URL
        """
        self.server_url = server_url
        self.client = VoiceClient(ClientConfig(server_url=server_url))
        self.ui_state = UIState()
        self.logger = get_logger(f"{__name__}.KioskUISimulator")
        self.running = False
        self.audio_thread: Optional[threading.Thread] = None
        
        # 화면 크기 설정
        self.screen_width = 80
        self.screen_height = 25
        
        self.logger.info("키오스크 UI 시뮬레이터 초기화 완료")
    
    def start(self):
        """시뮬레이터 시작"""
        self.running = True
        self.logger.info("키오스크 UI 시뮬레이터 시작")
        
        try:
            self._show_welcome_screen()
            self._main_loop()
        except KeyboardInterrupt:
            print("\n\n👋 키오스크를 종료합니다...")
        except Exception as e:
            self.logger.error(f"시뮬레이터 실행 중 오류: {e}")
            print(f"\n❌ 오류 발생: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """시뮬레이터 종료"""
        self.running = False
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
        self.client.close()
        self.logger.info("키오스크 UI 시뮬레이터 종료")
    
    def _main_loop(self):
        """메인 루프"""
        while self.running:
            try:
                # 사용자 입력 대기
                user_input = input("\n명령어를 입력하세요 (help: 도움말): ").strip().lower()
                
                if user_input in ['quit', 'exit', 'q']:
                    break
                elif user_input == 'help':
                    self._show_help()
                elif user_input == 'voice':
                    self._start_voice_input()
                elif user_input == 'menu':
                    self._show_sample_menu()
                elif user_input == 'order':
                    self._show_sample_order()
                elif user_input == 'payment':
                    self._show_sample_payment()
                elif user_input == 'error':
                    self._show_sample_error()
                elif user_input == 'clear':
                    self._clear_screen()
                elif user_input == 'status':
                    self._show_status()
                elif user_input.startswith('file '):
                    # 음성 파일 직접 전송
                    file_path = user_input[5:].strip()
                    self._process_audio_file(file_path)
                else:
                    print("❓ 알 수 없는 명령어입니다. 'help'를 입력하여 도움말을 확인하세요.")
                    
            except EOFError:
                break
            except Exception as e:
                self.logger.error(f"메인 루프 오류: {e}")
                print(f"❌ 오류 발생: {e}")
    
    def _clear_screen(self):
        """화면 지우기"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _show_welcome_screen(self):
        """환영 화면 표시"""
        self._clear_screen()
        self._draw_header("🎤 음성 키오스크 시뮬레이터")
        
        welcome_text = [
            "안녕하세요! 음성 키오스크에 오신 것을 환영합니다.",
            "",
            "🎯 이 시뮬레이터는 다음 기능을 제공합니다:",
            "  • 음성 명령 처리 시뮬레이션",
            "  • 주문 상태 화면 갱신",
            "  • 메뉴 선택 옵션 표시",
            "  • 결제 정보 화면 표시",
            "  • TTS 음성 재생 시뮬레이션",
            "",
            "💡 'help' 명령어로 사용법을 확인하세요.",
            "💡 'voice' 명령어로 음성 입력을 시작하세요.",
        ]
        
        self._draw_content(welcome_text)
        self._draw_footer("준비 완료")
        
        self.ui_state.current_screen = "welcome"
    
    def _show_help(self):
        """도움말 표시"""
        self._clear_screen()
        self._draw_header("📖 도움말")
        
        help_text = [
            "사용 가능한 명령어:",
            "",
            "🎤 voice      - 음성 입력 시작 (시뮬레이션)",
            "📁 file <경로> - 음성 파일 직접 전송",
            "📋 menu       - 샘플 메뉴 화면 표시",
            "🛒 order      - 샘플 주문 화면 표시", 
            "💳 payment    - 샘플 결제 화면 표시",
            "❌ error      - 샘플 오류 화면 표시",
            "📊 status     - 현재 상태 정보 표시",
            "🧹 clear      - 화면 지우기",
            "❓ help       - 이 도움말 표시",
            "🚪 quit/exit  - 시뮬레이터 종료",
            "",
            "💡 팁:",
            "  • 음성 파일은 .wav 형식이어야 합니다",
            "  • 서버가 실행 중이어야 음성 처리가 가능합니다",
            "  • 프로젝트 루트의 .wav 파일들을 자동으로 감지합니다",
        ]
        
        self._draw_content(help_text)
        self._draw_footer("명령어 입력 대기")
    
    def _start_voice_input(self):
        """음성 입력 시작 (시뮬레이션)"""
        self._clear_screen()
        self._draw_header("🎤 음성 입력")
        
        # 사용 가능한 음성 파일 찾기
        audio_files = self._find_audio_files()
        
        if not audio_files:
            content = [
                "❌ 사용 가능한 음성 파일이 없습니다.",
                "",
                "💡 다음 위치에 .wav 파일을 추가해주세요:",
                "  • 프로젝트 루트 디렉토리",
                "  • data/ 디렉토리",
                "",
                "또는 'file <경로>' 명령어로 직접 파일을 지정하세요."
            ]
            self._draw_content(content)
            self._draw_footer("음성 파일 없음")
            return
        
        # 음성 파일 선택 메뉴 표시
        content = [
            "🎯 사용 가능한 음성 파일을 선택하세요:",
            ""
        ]
        
        for i, file_path in enumerate(audio_files, 1):
            file_name = Path(file_path).name
            file_size = Path(file_path).stat().st_size
            content.append(f"  {i}. {file_name} ({file_size:,} bytes)")
        
        content.extend([
            "",
            "📝 파일 번호를 입력하거나 'back'으로 돌아가세요:"
        ])
        
        self._draw_content(content)
        self._draw_footer("파일 선택 대기")
        
        # 사용자 선택 대기
        try:
            choice = input("선택: ").strip()
            
            if choice.lower() == 'back':
                return
            
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < len(audio_files):
                    selected_file = audio_files[file_index]
                    self._process_audio_file(selected_file)
                else:
                    print("❌ 잘못된 선택입니다.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
                
        except (EOFError, KeyboardInterrupt):
            return
    
    def _find_audio_files(self) -> List[str]:
        """음성 파일 찾기"""
        audio_files = []
        project_root = Path(__file__).parent.parent
        
        # 루트 디렉토리의 .wav 파일들
        for wav_file in project_root.glob("*.wav"):
            audio_files.append(str(wav_file))
        
        # data 디렉토리의 .wav 파일들
        data_dir = project_root / "data"
        if data_dir.exists():
            for wav_file in data_dir.glob("**/*.wav"):
                audio_files.append(str(wav_file))
        
        return sorted(audio_files)
    
    def _process_audio_file(self, file_path: str):
        """음성 파일 처리"""
        self._clear_screen()
        self._draw_header("🔄 음성 처리 중...")
        
        processing_content = [
            f"📁 파일: {Path(file_path).name}",
            f"📍 경로: {file_path}",
            "",
            "⏳ 서버로 전송 중...",
            "🎯 음성 인식 처리 중...",
            "🤖 AI 응답 생성 중...",
            "🔊 TTS 음성 생성 중...",
        ]
        
        self._draw_content(processing_content)
        self._draw_footer("처리 중... 잠시만 기다려주세요")
        
        try:
            # 음성 파일 전송
            start_time = time.time()
            response = self.client.send_audio_file(file_path, self.ui_state.session_id)
            processing_time = time.time() - start_time
            
            # 세션 ID 업데이트
            if response.session_id:
                self.ui_state.session_id = response.session_id
            
            # 응답 처리
            self._handle_server_response(response, processing_time)
            
        except Exception as e:
            self.logger.error(f"음성 파일 처리 오류: {e}")
            self._show_error_screen(f"음성 처리 실패: {str(e)}")
    
    def _handle_server_response(self, response: ServerResponse, processing_time: float):
        """서버 응답 처리"""
        self.ui_state.last_message = response.message
        
        if response.success:
            self._handle_success_response(response, processing_time)
        else:
            self._handle_error_response(response)
    
    def _handle_success_response(self, response: ServerResponse, processing_time: float):
        """성공 응답 처리"""
        self._clear_screen()
        self._draw_header("✅ 음성 처리 완료")
        
        # 기본 정보 표시
        content = [
            f"💬 응답: {response.message}",
            f"⏱️  처리 시간: {processing_time:.2f}초",
            f"🆔 세션 ID: {response.session_id or 'N/A'}",
            ""
        ]
        
        # TTS 음성 처리
        if response.tts_audio_url:
            content.append(f"🔊 TTS 음성: {response.tts_audio_url}")
            self._simulate_tts_playback(response.tts_audio_url)
            content.append("   → 음성 재생 시뮬레이션 완료")
            content.append("")
        
        # 주문 데이터 처리
        if response.order_data:
            self.ui_state.order_data = response.order_data
            content.extend(self._format_order_info(response.order_data))
        
        # UI 액션 처리
        if response.ui_actions:
            content.append(f"🎯 UI 액션 ({len(response.ui_actions)}개):")
            for i, action in enumerate(response.ui_actions, 1):
                content.append(f"   {i}. {action.action_type}")
                if action.requires_user_input:
                    content.append("      (사용자 입력 필요)")
                if action.timeout_seconds:
                    content.append(f"      (타임아웃: {action.timeout_seconds}초)")
            content.append("")
            
            # 첫 번째 UI 액션 실행
            self._execute_ui_action(response.ui_actions[0])
        
        self._draw_content(content)
        self._draw_footer("처리 완료 - 계속하려면 Enter를 누르세요")
        
        input()  # 사용자가 Enter를 누를 때까지 대기
    
    def _handle_error_response(self, response: ServerResponse):
        """오류 응답 처리"""
        self.ui_state.error_info = response.error_info
        error_message = response.message
        
        if response.error_info:
            error_message = response.error_info.error_message
        
        self._show_error_screen(error_message, response.error_info)
    
    def _execute_ui_action(self, action: UIAction):
        """UI 액션 실행"""
        action_type = action.action_type
        
        if action_type == UIActionType.SHOW_MENU.value:
            self._show_menu_from_action(action)
        elif action_type == UIActionType.SHOW_PAYMENT.value:
            self._show_payment_from_action(action)
        elif action_type == UIActionType.UPDATE_ORDER.value:
            self._update_order_display(action)
        elif action_type == UIActionType.SHOW_CONFIRMATION.value:
            self._show_confirmation_from_action(action)
        elif action_type == UIActionType.SHOW_ERROR.value:
            self._show_error_from_action(action)
    
    def _show_menu_from_action(self, action: UIAction):
        """액션에서 메뉴 표시"""
        menu_data = action.data
        menu_options = []
        
        if 'menu_options' in menu_data:
            for option_data in menu_data['menu_options']:
                menu_options.append(MenuOption.from_dict(option_data))
        
        self.ui_state.menu_options = menu_options
        self.ui_state.current_screen = "menu"
    
    def _show_payment_from_action(self, action: UIAction):
        """액션에서 결제 화면 표시"""
        payment_data = PaymentData.from_dict(action.data)
        self.ui_state.payment_data = payment_data
        self.ui_state.current_screen = "payment"
    
    def _update_order_display(self, action: UIAction):
        """주문 화면 업데이트"""
        order_data = OrderData.from_dict(action.data)
        self.ui_state.order_data = order_data
        self.ui_state.current_screen = "order"
    
    def _show_confirmation_from_action(self, action: UIAction):
        """확인 화면 표시"""
        confirmation_data = action.data
        message = confirmation_data.get('message', '확인이 필요합니다.')
        options = confirmation_data.get('options', ['예', '아니오'])
        
        print(f"\n🤔 {message}")
        print("선택 옵션:")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
    
    def _show_error_from_action(self, action: UIAction):
        """액션에서 오류 화면 표시"""
        error_data = action.data
        error_message = error_data.get('error_message', '오류가 발생했습니다.')
        recovery_actions = error_data.get('recovery_actions', [])
        
        self._show_error_screen(error_message, None, recovery_actions) 
   
    def _simulate_tts_playback(self, tts_url: str):
        """TTS 음성 재생 시뮬레이션"""
        try:
            # 실제 환경에서는 여기서 음성을 재생
            # 시뮬레이션에서는 간단한 표시만
            print("🔊 TTS 음성 재생 중...")
            time.sleep(1)  # 재생 시뮬레이션
            print("✅ 음성 재생 완료")
            
            # 실제 파일 다운로드 시뮬레이션 (선택사항)
            if tts_url.startswith('http'):
                print(f"📥 TTS 파일 다운로드: {tts_url}")
            else:
                print(f"📁 로컬 TTS 파일: {tts_url}")
                
        except Exception as e:
            self.logger.error(f"TTS 재생 시뮬레이션 오류: {e}")
            print(f"⚠️  TTS 재생 실패: {e}")
    
    def _show_sample_menu(self):
        """샘플 메뉴 화면 표시"""
        self._clear_screen()
        self._draw_header("📋 메뉴 선택")
        
        # 샘플 메뉴 옵션 생성
        sample_menu = [
            MenuOption("burger1", "빅맥", "버거", 6500.0, "클래식 빅맥 버거"),
            MenuOption("burger2", "치킨버거", "버거", 5500.0, "바삭한 치킨 버거"),
            MenuOption("side1", "감자튀김", "사이드", 2500.0, "바삭한 감자튀김"),
            MenuOption("drink1", "콜라", "음료", 2000.0, "시원한 콜라"),
            MenuOption("drink2", "커피", "음료", 3000.0, "따뜻한 아메리카노"),
        ]
        
        self.ui_state.menu_options = sample_menu
        self.ui_state.current_screen = "menu"
        
        content = [
            "🍔 버거 메뉴:",
            "  1. 빅맥 - 6,500원",
            "  2. 치킨버거 - 5,500원",
            "",
            "🍟 사이드 메뉴:",
            "  3. 감자튀김 - 2,500원",
            "",
            "🥤 음료 메뉴:",
            "  4. 콜라 - 2,000원",
            "  5. 커피 - 3,000원",
            "",
            "💡 음성으로 '빅맥 하나 주세요' 또는 '콜라 추가해주세요'라고 말해보세요."
        ]
        
        self._draw_content(content)
        self._draw_footer("메뉴 선택 화면")
    
    def _show_sample_order(self):
        """샘플 주문 화면 표시"""
        self._clear_screen()
        self._draw_header("🛒 현재 주문")
        
        # 샘플 주문 데이터 생성
        sample_order = OrderData(
            order_id="ORDER-001",
            items=[
                {
                    "name": "빅맥",
                    "category": "버거",
                    "quantity": 1,
                    "price": 6500.0,
                    "options": ["피클 제외"]
                },
                {
                    "name": "감자튀김",
                    "category": "사이드", 
                    "quantity": 1,
                    "price": 2500.0,
                    "options": []
                },
                {
                    "name": "콜라",
                    "category": "음료",
                    "quantity": 2,
                    "price": 2000.0,
                    "options": ["얼음 많이"]
                }
            ],
            total_amount=13000.0,
            status="진행중",
            requires_confirmation=False,
            item_count=4
        )
        
        self.ui_state.order_data = sample_order
        self.ui_state.current_screen = "order"
        
        content = self._format_order_info(sample_order)
        content.extend([
            "",
            "💡 음성으로 '주문 확인' 또는 '결제하기'라고 말해보세요."
        ])
        
        self._draw_content(content)
        self._draw_footer("주문 확인 화면")
    
    def _show_sample_payment(self):
        """샘플 결제 화면 표시"""
        self._clear_screen()
        self._draw_header("💳 결제 정보")
        
        # 샘플 결제 데이터 생성
        sample_payment = PaymentData(
            total_amount=13000.0,
            payment_methods=["카드", "현금", "모바일페이"],
            order_summary=[
                {"name": "빅맥", "quantity": 1, "price": 6500.0},
                {"name": "감자튀김", "quantity": 1, "price": 2500.0},
                {"name": "콜라", "quantity": 2, "price": 2000.0}
            ],
            tax_amount=1300.0,
            service_charge=0.0,
            discount_amount=0.0
        )
        
        self.ui_state.payment_data = sample_payment
        self.ui_state.current_screen = "payment"
        
        content = self._format_payment_info(sample_payment)
        content.extend([
            "",
            "💡 음성으로 '카드로 결제' 또는 '현금으로 결제'라고 말해보세요."
        ])
        
        self._draw_content(content)
        self._draw_footer("결제 대기 중")
    
    def _show_sample_error(self):
        """샘플 오류 화면 표시"""
        sample_error = ErrorInfo(
            error_code="SPEECH_RECOGNITION_ERROR",
            error_message="음성을 인식할 수 없습니다. 다시 말씀해주세요.",
            recovery_actions=[
                "더 크고 명확하게 말씀해주세요",
                "주변 소음을 줄여주세요",
                "다시 시도해주세요"
            ]
        )
        
        self._show_error_screen(sample_error.error_message, sample_error)
    
    def _show_error_screen(self, error_message: str, error_info: ErrorInfo = None, recovery_actions: List[str] = None):
        """오류 화면 표시"""
        self._clear_screen()
        self._draw_header("❌ 오류 발생")
        
        content = [
            f"🚨 오류 메시지: {error_message}",
            ""
        ]
        
        if error_info:
            content.append(f"🔍 오류 코드: {error_info.error_code}")
            content.append(f"⏰ 발생 시간: {error_info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            content.append("")
            
            if error_info.recovery_actions:
                content.append("💡 해결 방법:")
                for i, action in enumerate(error_info.recovery_actions, 1):
                    content.append(f"   {i}. {action}")
        elif recovery_actions:
            content.append("💡 해결 방법:")
            for i, action in enumerate(recovery_actions, 1):
                content.append(f"   {i}. {action}")
        
        self.ui_state.error_info = error_info
        self.ui_state.current_screen = "error"
        
        self._draw_content(content)
        self._draw_footer("오류 발생 - 계속하려면 Enter를 누르세요")
        
        input()  # 사용자가 Enter를 누를 때까지 대기
    
    def _show_status(self):
        """현재 상태 정보 표시"""
        self._clear_screen()
        self._draw_header("📊 시스템 상태")
        
        content = [
            f"🖥️  현재 화면: {self.ui_state.current_screen}",
            f"🆔 세션 ID: {self.ui_state.session_id or 'N/A'}",
            f"💬 마지막 메시지: {self.ui_state.last_message or 'N/A'}",
            f"🎤 음성 입력 상태: {'활성' if self.ui_state.is_listening else '비활성'}",
            f"🌐 서버 URL: {self.server_url}",
            ""
        ]
        
        # 주문 상태
        if self.ui_state.order_data:
            content.append("🛒 주문 상태:")
            content.append(f"   주문 ID: {self.ui_state.order_data.order_id}")
            content.append(f"   상태: {self.ui_state.order_data.status}")
            content.append(f"   총 금액: {self.ui_state.order_data.total_amount:,.0f}원")
            content.append(f"   아이템 수: {self.ui_state.order_data.item_count}")
        else:
            content.append("🛒 주문 상태: 없음")
        
        content.append("")
        
        # 메뉴 옵션 상태
        if self.ui_state.menu_options:
            content.append(f"📋 메뉴 옵션: {len(self.ui_state.menu_options)}개")
        else:
            content.append("📋 메뉴 옵션: 없음")
        
        # 결제 데이터 상태
        if self.ui_state.payment_data:
            content.append(f"💳 결제 데이터: 있음 ({self.ui_state.payment_data.total_amount:,.0f}원)")
        else:
            content.append("💳 결제 데이터: 없음")
        
        # 오류 정보 상태
        if self.ui_state.error_info:
            content.append(f"❌ 오류 정보: {self.ui_state.error_info.error_code}")
        else:
            content.append("❌ 오류 정보: 없음")
        
        self._draw_content(content)
        self._draw_footer("상태 정보")
    
    def _format_order_info(self, order_data: OrderData) -> List[str]:
        """주문 정보 포맷팅"""
        content = [
            f"🆔 주문 ID: {order_data.order_id}",
            f"📊 상태: {order_data.status}",
            f"📦 아이템 수: {order_data.item_count}",
            ""
        ]
        
        if order_data.items:
            content.append("📋 주문 내역:")
            total = 0
            for item in order_data.items:
                item_total = item['price'] * item['quantity']
                total += item_total
                
                options_str = ""
                if item.get('options'):
                    options_str = f" ({', '.join(item['options'])})"
                
                content.append(f"   • {item['name']} x{item['quantity']} - {item_total:,.0f}원{options_str}")
            
            content.append("")
            content.append(f"💰 총 금액: {order_data.total_amount:,.0f}원")
            
            if order_data.requires_confirmation:
                content.append("⚠️  확인이 필요합니다")
        
        return content
    
    def _format_payment_info(self, payment_data: PaymentData) -> List[str]:
        """결제 정보 포맷팅"""
        content = [
            "📋 주문 요약:",
            ""
        ]
        
        subtotal = 0
        for item in payment_data.order_summary:
            item_total = item['price'] * item['quantity']
            subtotal += item_total
            content.append(f"   • {item['name']} x{item['quantity']} - {item_total:,.0f}원")
        
        content.extend([
            "",
            f"💰 소계: {subtotal:,.0f}원",
            f"🏷️  세금: {payment_data.tax_amount:,.0f}원",
            f"🎁 할인: -{payment_data.discount_amount:,.0f}원",
            f"💳 총 결제 금액: {payment_data.total_amount:,.0f}원",
            "",
            "💳 결제 방법:"
        ])
        
        for i, method in enumerate(payment_data.payment_methods, 1):
            content.append(f"   {i}. {method}")
        
        return content
    
    def _draw_header(self, title: str):
        """헤더 그리기"""
        print("=" * self.screen_width)
        print(f"{title:^{self.screen_width}}")
        print("=" * self.screen_width)
    
    def _draw_content(self, content_lines: List[str]):
        """내용 그리기"""
        print()
        for line in content_lines:
            # 긴 줄은 자동으로 줄바꿈
            if len(line) > self.screen_width - 4:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) > self.screen_width - 4:
                        print(f"  {current_line}")
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line.strip():
                    print(f"  {current_line}")
            else:
                print(f"  {line}")
        print()
    
    def _draw_footer(self, status: str):
        """푸터 그리기"""
        print("-" * self.screen_width)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"{status} | {timestamp}"
        print(f"{footer_text:^{self.screen_width}}")
        print("-" * self.screen_width)


class KioskSimulatorDemo:
    """키오스크 시뮬레이터 데모 클래스"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        """
        데모 초기화
        
        Args:
            server_url: 서버 URL
        """
        self.server_url = server_url
        self.simulator = KioskUISimulator(server_url)
        self.logger = get_logger(f"{__name__}.KioskSimulatorDemo")
    
    def run_demo(self):
        """데모 실행"""
        print("🎤 키오스크 UI 시뮬레이터 데모 시작")
        print("=" * 50)
        
        try:
            # 서버 상태 확인
            print("\n1. 서버 상태 확인...")
            if not self.simulator.client.check_server_health():
                print("⚠️  서버에 연결할 수 없습니다.")
                print("💡 서버 없이도 UI 시뮬레이션은 가능합니다.")
                
                response = input("계속 진행하시겠습니까? (y/n): ").strip().lower()
                if response != 'y':
                    return
            else:
                print("✅ 서버 연결 정상")
            
            # 시뮬레이터 시작
            print("\n2. 키오스크 UI 시뮬레이터 시작...")
            self.simulator.start()
            
        except Exception as e:
            self.logger.error(f"데모 실행 오류: {e}")
            print(f"❌ 데모 실행 중 오류 발생: {e}")
        finally:
            self.simulator.stop()
    
    def run_automated_demo(self):
        """자동화된 데모 실행"""
        print("🤖 자동화된 키오스크 데모 시작")
        print("=" * 50)
        
        try:
            # 각 화면을 순서대로 시연
            screens = [
                ("환영 화면", self.simulator._show_welcome_screen),
                ("메뉴 화면", self.simulator._show_sample_menu),
                ("주문 화면", self.simulator._show_sample_order),
                ("결제 화면", self.simulator._show_sample_payment),
                ("오류 화면", self.simulator._show_sample_error),
                ("상태 정보", self.simulator._show_status)
            ]
            
            for screen_name, screen_func in screens:
                print(f"\n📺 {screen_name} 시연...")
                screen_func()
                
                print(f"\n⏳ 3초 후 다음 화면으로 이동...")
                time.sleep(3)
            
            print("\n🎉 자동화된 데모 완료!")
            
        except Exception as e:
            self.logger.error(f"자동화된 데모 오류: {e}")
            print(f"❌ 자동화된 데모 중 오류 발생: {e}")
        finally:
            self.simulator.stop()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="키오스크 UI 시뮬레이터")
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="서버 URL (기본값: http://localhost:8000)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="자동화된 데모 모드 실행"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="대화형 모드 실행 (기본값)"
    )
    
    args = parser.parse_args()
    
    # 기본값은 대화형 모드
    if not args.demo:
        args.interactive = True
    
    demo = KioskSimulatorDemo(args.server_url)
    
    try:
        if args.demo:
            demo.run_automated_demo()
        else:
            demo.run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 시뮬레이터를 종료합니다...")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == "__main__":
    main()