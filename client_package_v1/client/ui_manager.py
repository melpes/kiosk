"""
키오스크 UI 관리자
"""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models.communication_models import (
    ServerResponse, OrderData, UIAction, MenuOption, 
    PaymentData, ErrorInfo, UIActionType
)
from .voice_client import VoiceClient
from utils.logger import get_logger
from utils.audio_utils import AudioUtils


class KioskUIManager:
    """
    키오스크 UI 관리자
    서버 응답을 처리하고 UI를 갱신하는 클래스
    """
    
    def __init__(self, voice_client: VoiceClient):
        """
        UI 관리자 초기화
        
        Args:
            voice_client: 음성 클라이언트 인스턴스
        """
        self.voice_client = voice_client
        self.config = voice_client.config
        self.logger = get_logger(f"{__name__}.KioskUIManager")
        self.audio_utils = AudioUtils()
        
        # UI 상태
        self.current_order: Optional[OrderData] = None
        self.current_menu_options: List[MenuOption] = []
        self.current_payment_data: Optional[PaymentData] = None
        
        self.logger.info("KioskUIManager 초기화 완료")
    
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
        
        # UI 액션 처리
        if response.ui_actions:
            self._process_ui_actions(response.ui_actions)
    
    def _handle_success_response(self, response: ServerResponse):
        """성공 응답 처리"""
        print(f"\n✅ 처리 성공: {response.message}")
        print(f"⏱️  처리 시간: {response.processing_time:.2f}초")
        
        # 주문 데이터 업데이트
        if response.order_data:
            self.current_order = response.order_data
            self._display_order_info(response.order_data)
        
        # TTS 음성 파일 처리
        if response.tts_audio_url and self.config.ui.auto_play_tts:
            self._handle_tts_audio(response.tts_audio_url)
    
    def _handle_error_response(self, response: ServerResponse):
        """오류 응답 처리"""
        print(f"\n❌ 처리 실패: {response.message}")
        
        if response.error_info:
            self._display_error_info(response.error_info)
    
    def _process_ui_actions(self, ui_actions: List[UIAction]):
        """UI 액션들 처리"""
        # 우선순위별로 정렬
        sorted_actions = sorted(ui_actions, key=lambda x: x.priority, reverse=True)
        
        print(f"\n🎯 UI 액션 처리 ({len(sorted_actions)}개)")
        
        for i, action in enumerate(sorted_actions, 1):
            print(f"\n{i}. {action.action_type}")
            
            if action.action_type == UIActionType.SHOW_MENU.value:
                self._handle_show_menu_action(action)
            elif action.action_type == UIActionType.SHOW_PAYMENT.value:
                self._handle_show_payment_action(action)
            elif action.action_type == UIActionType.UPDATE_ORDER.value:
                self._handle_update_order_action(action)
            elif action.action_type == UIActionType.SHOW_CONFIRMATION.value:
                self._handle_show_confirmation_action(action)
            elif action.action_type == UIActionType.SHOW_ERROR.value:
                self._handle_show_error_action(action)
            elif action.action_type == UIActionType.SHOW_OPTIONS.value:
                self._handle_show_options_action(action)
            else:
                print(f"   ⚠️  알 수 없는 액션 타입: {action.action_type}")
            
            # 사용자 입력이 필요한 경우 대기
            if action.requires_user_input:
                self._wait_for_user_input(action)
    
    def _handle_show_menu_action(self, action: UIAction):
        """메뉴 표시 액션 처리"""
        data = action.data
        menu_options = data.get('menu_options', [])
        category = data.get('category')
        
        print("   📋 메뉴 표시")
        if category:
            print(f"   카테고리: {category}")
        
        if menu_options:
            self.current_menu_options = [MenuOption.from_dict(opt) for opt in menu_options]
            self._display_menu_options(self.current_menu_options)
        else:
            print("   (메뉴 옵션이 없습니다)")
    
    def _handle_show_payment_action(self, action: UIAction):
        """결제 화면 표시 액션 처리"""
        data = action.data
        self.current_payment_data = PaymentData.from_dict(data)
        
        print("   💳 결제 화면 표시")
        self._display_payment_info(self.current_payment_data)
        
        if action.timeout_seconds:
            print(f"   ⏰ 타임아웃: {action.timeout_seconds}초")
    
    def _handle_update_order_action(self, action: UIAction):
        """주문 업데이트 액션 처리"""
        data = action.data
        order_data = OrderData.from_dict(data)
        
        print("   🔄 주문 상태 업데이트")
        self.current_order = order_data
        self._display_order_info(order_data)
    
    def _handle_show_confirmation_action(self, action: UIAction):
        """확인 화면 표시 액션 처리"""
        data = action.data
        message = data.get('message', '')
        options = data.get('options', ['예', '아니오'])
        
        print("   ❓ 확인 요청")
        print(f"   메시지: {message}")
        print("   선택 옵션:")
        for i, option in enumerate(options, 1):
            print(f"     {i}. {option}")
        
        if action.timeout_seconds:
            print(f"   ⏰ 응답 시간: {action.timeout_seconds}초")
    
    def _handle_show_error_action(self, action: UIAction):
        """오류 표시 액션 처리"""
        data = action.data
        error_message = data.get('error_message', '')
        recovery_actions = data.get('recovery_actions', [])
        
        print("   ❌ 오류 표시")
        print(f"   오류 메시지: {error_message}")
        
        if recovery_actions:
            print("   💡 해결 방법:")
            for i, action_text in enumerate(recovery_actions, 1):
                print(f"     {i}. {action_text}")
    
    def _handle_show_options_action(self, action: UIAction):
        """옵션 표시 액션 처리"""
        data = action.data
        print("   ⚙️  옵션 표시")
        
        for key, value in data.items():
            print(f"     {key}: {value}")
    
    def _wait_for_user_input(self, action: UIAction):
        """사용자 입력 대기"""
        if not action.requires_user_input:
            return
        
        timeout = action.timeout_seconds or 30
        print(f"\n⏳ 사용자 입력 대기 중... (최대 {timeout}초)")
        print("   (실제 키오스크에서는 터치/음성 입력을 기다립니다)")
        
        # 시뮬레이션을 위한 짧은 대기
        time.sleep(2)
        print("   ✅ 입력 완료 (시뮬레이션)")
    
    def _display_order_info(self, order_data: OrderData):
        """주문 정보 표시"""
        print(f"\n📋 주문 정보:")
        print(f"   주문 ID: {order_data.order_id or '미생성'}")
        print(f"   상태: {order_data.status}")
        print(f"   총 금액: {order_data.total_amount:,.0f}원")
        print(f"   아이템 수: {order_data.item_count}")
        
        if order_data.requires_confirmation:
            print("   ⚠️  확인이 필요합니다")
        
        if order_data.items:
            print("   주문 내역:")
            for item in order_data.items:
                name = item.get('name', '알 수 없음')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)
                print(f"     - {name} x{quantity} ({price:,.0f}원)")
    
    def _display_menu_options(self, menu_options: List[MenuOption]):
        """메뉴 옵션 표시"""
        print("   메뉴 옵션:")
        
        # 카테고리별로 그룹화
        categories = {}
        for option in menu_options:
            category = option.category or "기타"
            if category not in categories:
                categories[category] = []
            categories[category].append(option)
        
        for category, options in categories.items():
            print(f"\n   📂 {category}")
            for option in options:
                price_text = f" ({option.price:,.0f}원)" if option.price else ""
                available_text = "" if option.available else " (품절)"
                print(f"     - {option.display_text}{price_text}{available_text}")
                
                if option.description:
                    print(f"       {option.description}")
    
    def _display_payment_info(self, payment_data: PaymentData):
        """결제 정보 표시"""
        print(f"\n💳 결제 정보:")
        print(f"   총 금액: {payment_data.total_amount:,.0f}원")
        
        if payment_data.tax_amount > 0:
            print(f"   세금: {payment_data.tax_amount:,.0f}원")
        if payment_data.service_charge > 0:
            print(f"   서비스 요금: {payment_data.service_charge:,.0f}원")
        if payment_data.discount_amount > 0:
            print(f"   할인: -{payment_data.discount_amount:,.0f}원")
        
        print("   결제 방법:")
        for i, method in enumerate(payment_data.payment_methods, 1):
            print(f"     {i}. {method}")
        
        if payment_data.order_summary:
            print("   주문 요약:")
            for item in payment_data.order_summary:
                name = item.get('name', '알 수 없음')
                quantity = item.get('quantity', 1)
                price = item.get('price', 0)
                print(f"     - {name} x{quantity} ({price:,.0f}원)")
    
    def _display_error_info(self, error_info: ErrorInfo):
        """오류 정보 표시"""
        print(f"🔍 오류 코드: {error_info.error_code}")
        print(f"📝 오류 메시지: {error_info.error_message}")
        print(f"🕐 발생 시간: {error_info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if error_info.recovery_actions:
            print("💡 해결 방법:")
            for i, action in enumerate(error_info.recovery_actions, 1):
                print(f"   {i}. {action}")
        
        if error_info.details and self.config.ui.show_detailed_logs:
            print("🔧 상세 정보:")
            for key, value in error_info.details.items():
                print(f"   {key}: {value}")
    
    def _handle_tts_audio(self, tts_url: str):
        """TTS 음성 처리"""
        print(f"🔊 TTS 음성: {tts_url}")
        
        # TTS 파일 다운로드
        audio_file = self.voice_client.download_tts_file(tts_url)
        
        if audio_file:
            print(f"💾 TTS 파일 저장: {audio_file}")
            
            # 음성 재생
            if self.config.ui.auto_play_tts:
                print("🔊 음성 재생 중...")
                success = self.audio_utils.play_audio_file(audio_file)
                
                if success:
                    print("✅ 음성 재생 완료")
                else:
                    print("⚠️  음성 재생 실패 (시뮬레이션 모드)")
            else:
                print("🔇 자동 재생 비활성화됨")
        else:
            print("❌ TTS 파일 다운로드 실패")
    
    def get_current_order(self) -> Optional[OrderData]:
        """현재 주문 정보 반환"""
        return self.current_order
    
    def get_current_menu_options(self) -> List[MenuOption]:
        """현재 메뉴 옵션 반환"""
        return self.current_menu_options
    
    def get_current_payment_data(self) -> Optional[PaymentData]:
        """현재 결제 정보 반환"""
        return self.current_payment_data
    
    def clear_current_state(self):
        """현재 상태 초기화"""
        self.current_order = None
        self.current_menu_options = []
        self.current_payment_data = None
        self.logger.info("UI 상태 초기화 완료")
    
    def show_status(self):
        """현재 상태 표시"""
        print("\n📊 현재 키오스크 상태:")
        print(f"   세션 ID: {self.voice_client.get_session_id()}")
        print(f"   서버 URL: {self.config.server.url}")
        
        if self.current_order:
            print(f"   주문 상태: {self.current_order.status}")
            print(f"   주문 금액: {self.current_order.total_amount:,.0f}원")
        else:
            print("   주문 상태: 없음")
        
        print(f"   메뉴 옵션: {len(self.current_menu_options)}개")
        print(f"   결제 정보: {'있음' if self.current_payment_data else '없음'}")
        
        # 오디오 플레이어 정보
        available_players = self.audio_utils.get_available_players()
        print(f"   사용 가능한 오디오 플레이어: {', '.join(available_players) if available_players else '없음'}")