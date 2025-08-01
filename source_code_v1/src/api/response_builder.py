"""
서버 응답 빌더 클래스
DialogueResponse를 ServerResponse로 변환하고 UI 액션을 생성하는 로직 구현
"""

import os
import uuid
import tempfile
import wave
import struct
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ..models.communication_models import (
    ServerResponse, OrderData, UIAction, MenuOption, PaymentData, ErrorInfo,
    UIActionType, ErrorCode, MenuItemData
)
from ..models.conversation_models import DialogueResponse, Intent
from ..models.order_models import Order, MenuItem, OrderSummary
from ..audio.tts_manager import TTSManager
from ..audio.tts_providers.base_tts import TTSError, TTSConversionError
from ..logger import get_logger
from .optimization import get_optimization_manager, OptimizationManager


class ResponseBuilder:
    """서버 응답 빌더 클래스"""
    
    def __init__(self, 
                 tts_base_url: str = "/api/voice/tts",
                 tts_provider: str = "openai",
                 tts_config: Optional[Dict[str, Any]] = None,
                 enable_optimization: bool = True):
        """
        ResponseBuilder 초기화
        
        Args:
            tts_base_url: TTS 파일 다운로드 기본 URL
            tts_provider: 사용할 TTS 제공자 (기본: openai)
            tts_config: TTS 제공자 설정
            enable_optimization: 최적화 기능 활성화 여부
        """
        self.logger = get_logger(__name__)
        self.tts_base_url = tts_base_url
        self.enable_optimization = enable_optimization
        
        # 최적화 관리자 초기화
        if self.enable_optimization:
            try:
                self.optimization_manager = get_optimization_manager()
                self.logger.info("최적화 관리자 연결 완료")
            except Exception as e:
                self.logger.error(f"최적화 관리자 연결 실패: {e}")
                self.optimization_manager = None
        else:
            self.optimization_manager = None
        
        # TTS 관리자 초기화
        try:
            self.tts_manager = TTSManager(
                provider_name=tts_provider,
                provider_config=tts_config
            )
            self.logger.info(f"TTS 관리자 초기화 완료 (제공자: {tts_provider})")
        except Exception as e:
            self.logger.error(f"TTS 관리자 초기화 실패: {e}")
            # 폴백으로 더미 TTS 사용
            self.tts_manager = None
            self._init_fallback_tts()
        
        self.logger.info("ResponseBuilder 초기화 완료")
    
    def _init_fallback_tts(self):
        """폴백 TTS 시스템 초기화 (더미 파일 생성)"""
        self.tts_directory = Path(tempfile.gettempdir()) / "voice_kiosk_tts"
        self.tts_directory.mkdir(exist_ok=True)
        self.tts_cache: Dict[str, Dict[str, Any]] = {}
        self.logger.warning("TTS 관리자 초기화 실패로 폴백 TTS 사용")
    
    def build_response_from_dialogue(self, 
                                   dialogue_response: DialogueResponse,
                                   session_id: Optional[str] = None,
                                   processing_time: float = 0.0) -> ServerResponse:
        """
        DialogueResponse를 ServerResponse로 변환
        
        Args:
            dialogue_response: 대화 응답 객체
            session_id: 세션 ID
            processing_time: 처리 시간 (초)
            
        Returns:
            ServerResponse: 변환된 서버 응답
        """
        try:
            self.logger.info("DialogueResponse를 ServerResponse로 변환 시작")
            
            # TTS 파일 생성
            tts_audio_url = self._generate_tts_file(dialogue_response.text)
            
            # 주문 상태 정보를 OrderData로 변환
            order_data = None
            if dialogue_response.order_state:
                order_data = self._convert_order_to_order_data(
                    dialogue_response.order_state,
                    dialogue_response.requires_confirmation
                )
            
            # UI 액션 생성
            ui_actions = self._generate_ui_actions_from_dialogue(
                dialogue_response, order_data
            )
            
            # ServerResponse 생성
            response = ServerResponse(
                success=True,
                message=dialogue_response.text,
                tts_audio_url=tts_audio_url,
                order_data=order_data,
                ui_actions=ui_actions,
                error_info=None,
                processing_time=processing_time,
                session_id=session_id
            )
            
            self.logger.info("DialogueResponse 변환 완료")
            return response
            
        except Exception as e:
            self.logger.error(f"DialogueResponse 변환 실패: {e}")
            return self._create_error_response(
                ErrorCode.SERVER_ERROR,
                e,
                session_id,
                processing_time
            )
    
    def build_success_response(self,
                             message: str,
                             order_data: Optional[OrderData] = None,
                             ui_actions: Optional[List[UIAction]] = None,
                             session_id: Optional[str] = None,
                             processing_time: float = 0.0) -> ServerResponse:
        """
        성공 응답 생성
        
        Args:
            message: 응답 메시지
            order_data: 주문 데이터
            ui_actions: UI 액션 리스트
            session_id: 세션 ID
            processing_time: 처리 시간
            
        Returns:
            ServerResponse: 성공 응답
        """
        try:
            # TTS 파일 생성
            tts_audio_url = self._generate_tts_file(message)
            
            # UI 액션이 없으면 기본 액션 생성
            if ui_actions is None:
                ui_actions = self._generate_default_ui_actions(message, order_data)
            
            return ServerResponse(
                success=True,
                message=message,
                tts_audio_url=tts_audio_url,
                order_data=order_data,
                ui_actions=ui_actions,
                error_info=None,
                processing_time=processing_time,
                session_id=session_id
            )
            
        except Exception as e:
            self.logger.error(f"성공 응답 생성 실패: {e}")
            return self._create_error_response(
                ErrorCode.SERVER_ERROR,
                e,
                session_id,
                processing_time
            )
    
    def build_error_response(self,
                           error_code: ErrorCode,
                           error_message: str,
                           recovery_actions: Optional[List[str]] = None,
                           session_id: Optional[str] = None,
                           processing_time: float = 0.0) -> ServerResponse:
        """
        오류 응답 생성
        
        Args:
            error_code: 오류 코드
            error_message: 오류 메시지
            recovery_actions: 복구 액션 리스트
            session_id: 세션 ID
            processing_time: 처리 시간
            
        Returns:
            ServerResponse: 오류 응답
        """
        if recovery_actions is None:
            recovery_actions = ["다시 시도해 주세요"]
        
        error_info = ErrorInfo(
            error_code=error_code.value,
            error_message=error_message,
            recovery_actions=recovery_actions
        )
        
        # 오류 메시지용 TTS 파일 생성
        tts_audio_url = self._generate_tts_file(error_message)
        
        # 오류 표시 UI 액션 생성
        ui_actions = [UIAction(
            action_type=UIActionType.SHOW_ERROR.value,
            data={
                "error_message": error_message,
                "recovery_actions": recovery_actions
            }
        )]
        
        return ServerResponse(
            success=False,
            message=error_message,
            tts_audio_url=tts_audio_url,
            order_data=None,
            ui_actions=ui_actions,
            error_info=error_info,
            processing_time=processing_time,
            session_id=session_id
        )
    
    def _convert_order_to_order_data(self, order: Order, requires_confirmation: bool = False) -> OrderData:
        """
        Order 객체를 OrderData로 변환
        
        Args:
            order: Order 객체
            requires_confirmation: 확인 필요 여부
            
        Returns:
            OrderData: 변환된 주문 데이터
        """
        try:
            # MenuItem을 딕셔너리로 변환
            items = []
            for item in order.items:
                item_dict = {
                    'item_id': item.item_id or str(uuid.uuid4()),
                    'name': item.name,
                    'category': item.category,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'options': item.options,
                    'total_price': float(item.total_price)
                }
                items.append(item_dict)
            
            return OrderData(
                order_id=order.order_id or str(uuid.uuid4()),
                items=items,
                total_amount=float(order.total_amount),
                status=order.status.value,
                requires_confirmation=requires_confirmation,
                item_count=order.item_count,
                created_at=order.created_at.isoformat(),
                updated_at=order.updated_at.isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Order를 OrderData로 변환 실패: {e}")
            raise
    
    def _generate_ui_actions_from_dialogue(self, 
                                         dialogue_response: DialogueResponse,
                                         order_data: Optional[OrderData]) -> List[UIAction]:
        """
        DialogueResponse에서 UI 액션 생성
        
        Args:
            dialogue_response: 대화 응답
            order_data: 주문 데이터
            
        Returns:
            List[UIAction]: UI 액션 리스트
        """
        ui_actions = []
        
        try:
            # 주문 상태 업데이트 액션
            if order_data:
                ui_actions.append(UIAction.update_order(order_data))
            
            # 확인 필요한 경우 확인 액션 추가
            if dialogue_response.requires_confirmation:
                confirmation_options = ["예", "아니오"]
                
                # 결제 확인인지 판단
                if "결제" in dialogue_response.text or "계산" in dialogue_response.text:
                    confirmation_options = ["결제 진행", "주문 수정", "취소"]
                
                ui_actions.append(UIAction.show_confirmation(
                    dialogue_response.text,
                    confirmation_options
                ))
            
            # 제안 액션들을 UI 액션으로 변환
            for action in dialogue_response.suggested_actions:
                if action == "show_menu":
                    # 메뉴 표시 액션
                    menu_options = self._get_available_menu_options()
                    if menu_options:
                        ui_actions.append(UIAction.show_menu(menu_options))
                    else:
                        ui_actions.append(UIAction(
                            action_type=UIActionType.SHOW_MENU.value,
                            data={"message": "메뉴를 확인해주세요"},
                            requires_user_input=True
                        ))
                
                elif action == "show_payment" and order_data:
                    # 결제 화면 표시 액션
                    payment_data = self._create_payment_data_from_order_data(order_data)
                    ui_actions.append(UIAction.show_payment(payment_data))
                
                elif action == "continue_ordering":
                    # 주문 계속 액션
                    ui_actions.append(UIAction(
                        action_type=UIActionType.SHOW_MENU.value,
                        data={"message": "추가로 주문하실 메뉴가 있으신가요?"},
                        requires_user_input=True
                    ))
            
            # 응답 텍스트 기반 추가 액션 생성
            response_text = dialogue_response.text.lower()
            
            # 메뉴 관련 키워드 감지
            if any(keyword in response_text for keyword in ["메뉴", "선택", "주문"]):
                if not any(action.action_type == UIActionType.SHOW_MENU.value for action in ui_actions):
                    menu_options = self._get_available_menu_options()
                    if menu_options:
                        ui_actions.append(UIAction.show_menu(menu_options))
            
            # 결제 관련 키워드 감지
            if any(keyword in response_text for keyword in ["결제", "계산", "지불"]) and order_data:
                if not any(action.action_type == UIActionType.SHOW_PAYMENT.value for action in ui_actions):
                    payment_data = self._create_payment_data_from_order_data(order_data)
                    ui_actions.append(UIAction.show_payment(payment_data))
            
            return ui_actions
            
        except Exception as e:
            self.logger.error(f"UI 액션 생성 실패: {e}")
            return []
    
    def _generate_default_ui_actions(self, message: str, order_data: Optional[OrderData]) -> List[UIAction]:
        """
        기본 UI 액션 생성
        
        Args:
            message: 응답 메시지
            order_data: 주문 데이터
            
        Returns:
            List[UIAction]: 기본 UI 액션 리스트
        """
        ui_actions = []
        
        try:
            # 주문 데이터가 있으면 주문 업데이트 액션 추가
            if order_data:
                ui_actions.append(UIAction.update_order(order_data))
            
            # 메시지 내용에 따른 액션 생성
            message_lower = message.lower()
            
            if "메뉴" in message_lower:
                menu_options = self._get_available_menu_options()
                if menu_options:
                    ui_actions.append(UIAction.show_menu(menu_options))
            
            elif "결제" in message_lower and order_data:
                payment_data = self._create_payment_data_from_order_data(order_data)
                ui_actions.append(UIAction.show_payment(payment_data))
            
            return ui_actions
            
        except Exception as e:
            self.logger.error(f"기본 UI 액션 생성 실패: {e}")
            return []
    
    def _get_available_menu_options(self) -> List[MenuOption]:
        """
        사용 가능한 메뉴 옵션 가져오기
        
        Returns:
            List[MenuOption]: 메뉴 옵션 리스트
        """
        try:
            # 메뉴 설정에서 메뉴 정보 가져오기
            from ..config import config_manager
            
            menu_config = config_manager.load_menu_config()
            menu_options = []
            
            for item_name, item_config in menu_config.menu_items.items():
                # available 속성이 없거나 True인 경우만 포함
                is_available = getattr(item_config, 'available', True)
                if is_available:
                    menu_option = MenuOption(
                        option_id=item_name,
                        display_text=item_name,
                        category=getattr(item_config, 'category', 'general'),
                        price=float(getattr(item_config, 'price', 0)),
                        description=getattr(item_config, 'description', ''),
                        available=is_available
                    )
                    menu_options.append(menu_option)
            
            return menu_options
            
        except Exception as e:
            self.logger.error(f"메뉴 옵션 가져오기 실패: {e}")
            # 기본 메뉴 옵션 반환
            return [
                MenuOption(
                    option_id="default_menu",
                    display_text="메뉴를 확인해주세요",
                    category="general",
                    available=True
                )
            ]
    
    def _create_payment_data_from_order_data(self, order_data: OrderData) -> PaymentData:
        """
        OrderData에서 PaymentData 생성
        
        Args:
            order_data: 주문 데이터
            
        Returns:
            PaymentData: 결제 데이터
        """
        return PaymentData(
            total_amount=order_data.total_amount,
            payment_methods=["카드", "현금", "모바일"],
            order_summary=order_data.items,
            tax_amount=order_data.total_amount * 0.1,  # 10% 세금
            service_charge=0.0,
            discount_amount=0.0
        )
    
    def _generate_tts_file(self, text: str) -> Optional[str]:
        """
        TTS 파일 생성 및 URL 반환 (최적화 기능 포함)
        
        Args:
            text: 변환할 텍스트
            
        Returns:
            TTS 파일 URL (실패 시 None)
        """
        try:
            if not text or not text.strip():
                return None
            
            # 최적화 관리자가 있으면 캐시 확인
            if self.optimization_manager and self.tts_manager:
                # TTS 설정 정보 가져오기
                tts_config = self.tts_manager.get_provider_info()
                voice_config = {
                    'provider': tts_config.get('provider', 'unknown'),
                    'model': tts_config.get('model', 'default'),
                    'voice': tts_config.get('voice', 'default'),
                    'speed': tts_config.get('speed', 1.0)
                }
                
                # 캐시에서 TTS 파일 확인
                cached_file_path = self.optimization_manager.get_cached_tts(text, voice_config)
                if cached_file_path and os.path.exists(cached_file_path):
                    # 캐시된 파일의 ID 생성 (파일명에서 추출)
                    file_id = Path(cached_file_path).stem.replace('tts_', '')
                    tts_url = f"{self.tts_base_url}/{file_id}"
                    self.logger.info(f"TTS 캐시 히트: {tts_url}")
                    return tts_url
            
            # TTS 관리자가 있으면 실제 TTS 사용
            if self.tts_manager:
                try:
                    file_id = self.tts_manager.text_to_speech(text)
                    
                    # 최적화 관리자가 있으면 캐시에 저장
                    if self.optimization_manager:
                        file_path = self.tts_manager.get_file_path(file_id)
                        if file_path and os.path.exists(file_path):
                            tts_config = self.tts_manager.get_provider_info()
                            voice_config = {
                                'provider': tts_config.get('provider', 'unknown'),
                                'model': tts_config.get('model', 'default'),
                                'voice': tts_config.get('voice', 'default'),
                                'speed': tts_config.get('speed', 1.0)
                            }
                            self.optimization_manager.cache_tts_file(text, voice_config, file_path)
                            self.logger.debug(f"TTS 파일 캐시 저장: {file_path}")
                    
                    tts_url = f"{self.tts_base_url}/{file_id}"
                    self.logger.info(f"TTS 파일 생성 완료: {tts_url}")
                    return tts_url
                    
                except TTSError as e:
                    self.logger.error(f"TTS 변환 실패, 폴백 사용: {e}")
                    # 폴백으로 더미 파일 생성
                    return self._generate_fallback_tts_file(text)
            else:
                # 폴백 TTS 사용
                return self._generate_fallback_tts_file(text)
            
        except Exception as e:
            self.logger.error(f"TTS 파일 생성 실패: {e}")
            return None
    
    def _generate_fallback_tts_file(self, text: str) -> Optional[str]:
        """
        폴백 TTS 파일 생성 (더미 파일)
        
        Args:
            text: 변환할 텍스트
            
        Returns:
            TTS 파일 URL (실패 시 None)
        """
        try:
            file_id = str(uuid.uuid4())
            file_name = f"tts_{file_id}.wav"
            file_path = self.tts_directory / file_name
            
            # 더미 WAV 파일 생성
            self._create_dummy_wav_file(str(file_path), text)
            
            # 캐시에 저장 (1시간 후 만료)
            expires_at = datetime.now() + timedelta(hours=1)
            self.tts_cache[file_id] = {
                "path": str(file_path),
                "text": text,
                "created_at": datetime.now(),
                "expires_at": expires_at
            }
            
            tts_url = f"{self.tts_base_url}/{file_id}"
            self.logger.info(f"폴백 TTS 파일 생성: {file_path} -> {tts_url}")
            
            return tts_url
            
        except Exception as e:
            self.logger.error(f"폴백 TTS 파일 생성 실패: {e}")
            return None
    
    def _create_dummy_wav_file(self, file_path: str, text: str):
        """
        더미 WAV 파일 생성 (TTS 모듈 구현 전까지 임시 사용)
        
        Args:
            file_path: 생성할 파일 경로
            text: 텍스트 내용
        """
        try:
            # 간단한 더미 오디오 데이터 생성 (무음)
            sample_rate = 16000
            duration = min(len(text) * 0.1, 10.0)  # 텍스트 길이에 비례, 최대 10초
            num_samples = int(sample_rate * duration)
            
            with wave.open(file_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # 모노
                wav_file.setsampwidth(2)  # 16비트
                wav_file.setframerate(sample_rate)
                
                # 무음 데이터 생성
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('<h', 0))
            
            self.logger.debug(f"더미 WAV 파일 생성 완료: {file_path}")
            
        except Exception as e:
            self.logger.error(f"더미 WAV 파일 생성 실패: {e}")
            raise
    
    def _create_error_response(self,
                             error_code: ErrorCode,
                             exception: Exception,
                             session_id: Optional[str] = None,
                             processing_time: float = 0.0) -> ServerResponse:
        """
        예외에서 오류 응답 생성
        
        Args:
            error_code: 오류 코드
            exception: 예외 객체
            session_id: 세션 ID
            processing_time: 처리 시간
            
        Returns:
            ServerResponse: 오류 응답
        """
        error_message = f"처리 중 오류가 발생했습니다: {str(exception)}"
        recovery_actions = ["다시 시도해 주세요", "음성을 더 명확하게 말씀해 주세요"]
        
        return self.build_error_response(
            error_code,
            error_message,
            recovery_actions,
            session_id,
            processing_time
        )
    
    def get_tts_file_path(self, file_id: str) -> Optional[str]:
        """
        TTS 파일 경로 반환
        
        Args:
            file_id: TTS 파일 ID
            
        Returns:
            파일 경로 (존재하지 않으면 None)
        """
        # TTS 관리자가 있으면 관리자를 통해 파일 경로 반환
        if self.tts_manager:
            return self.tts_manager.get_file_path(file_id)
        
        # 폴백 캐시에서 파일 경로 반환
        if file_id not in self.tts_cache:
            self.logger.warning(f"TTS 파일 ID를 찾을 수 없음: {file_id}")
            return None
        
        file_info = self.tts_cache[file_id]
        file_path = file_info["path"]
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            self.logger.warning(f"TTS 파일이 존재하지 않음: {file_path}")
            del self.tts_cache[file_id]
            return None
        
        # 만료 시간 확인
        if datetime.now() > file_info["expires_at"]:
            self.logger.info(f"TTS 파일 만료: {file_path}")
            try:
                os.remove(file_path)
            except OSError:
                pass
            del self.tts_cache[file_id]
            return None
        
        return file_path
    
    def cleanup_expired_files(self):
        """만료된 TTS 파일 정리"""
        try:
            # TTS 관리자가 있으면 관리자를 통해 정리
            if self.tts_manager:
                self.tts_manager.cleanup_expired_files()
            
            # 폴백 캐시도 정리
            if hasattr(self, 'tts_cache'):
                current_time = datetime.now()
                expired_files = []
                
                for file_id, file_info in self.tts_cache.items():
                    if current_time > file_info["expires_at"]:
                        expired_files.append(file_id)
                
                for file_id in expired_files:
                    file_info = self.tts_cache[file_id]
                    try:
                        if os.path.exists(file_info["path"]):
                            os.remove(file_info["path"])
                        del self.tts_cache[file_id]
                        self.logger.info(f"만료된 폴백 TTS 파일 삭제: {file_info['path']}")
                    except Exception as e:
                        self.logger.error(f"폴백 TTS 파일 삭제 실패: {e}")
            
        except Exception as e:
            self.logger.error(f"TTS 파일 정리 실패: {e}")
    
    def get_tts_provider_info(self) -> Dict[str, Any]:
        """
        현재 TTS 제공자 정보 반환
        
        Returns:
            TTS 제공자 정보
        """
        if self.tts_manager:
            return self.tts_manager.get_provider_info()
        else:
            return {
                'provider': 'fallback',
                'provider_class': 'DummyTTS',
                'initialized': True,
                'supported_voices': [],
                'supported_formats': ['wav'],
            }
    
    def switch_tts_provider(self, provider_name: str, provider_config: Optional[Dict[str, Any]] = None):
        """
        TTS 제공자 교체
        
        Args:
            provider_name: 새로운 제공자 이름
            provider_config: 새로운 제공자 설정
        """
        try:
            if self.tts_manager:
                self.tts_manager.switch_provider(provider_name, provider_config)
                self.logger.info(f"TTS 제공자 교체 완료: {provider_name}")
            else:
                # TTS 관리자가 없으면 새로 생성
                self.tts_manager = TTSManager(
                    provider_name=provider_name,
                    provider_config=provider_config
                )
                self.logger.info(f"TTS 관리자 생성 및 제공자 설정 완료: {provider_name}")
        except Exception as e:
            self.logger.error(f"TTS 제공자 교체 실패: {e}")
            raise