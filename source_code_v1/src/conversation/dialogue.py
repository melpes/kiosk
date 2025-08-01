"""
대화 관리 시스템
"""

import json
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import OpenAI

from ..models.conversation_models import (
    Intent, IntentType, ConversationContext, DialogueResponse
)
from ..models.order_models import OrderResult
from ..models.error_models import ErrorResponse, ErrorAction
from ..error.handler import ErrorHandler
from ..order.order import OrderManager
import time


class DialogueManager:
    """대화 관리자 클래스"""
    
    def __init__(self, order_manager: OrderManager, openai_client: Optional[OpenAI] = None):
        """
        대화 관리자 초기화
        
        Args:
            order_manager: 주문 관리자
            openai_client: OpenAI 클라이언트 (선택사항)
        """
        self.order_manager = order_manager
        self.openai_client = openai_client or self._create_openai_client()
        self.error_handler = ErrorHandler()
        self.active_contexts: Dict[str, ConversationContext] = {}
        
        # 결제 상태 관리
        self.payment_confirmation_pending: Dict[str, bool] = {}
        
        # 응답 템플릿 - 간결하고 명확하게 수정
        self.response_templates = {
            'greeting': "주문 도와드릴게요. 메뉴 말씀해 주세요.",
            'order_added': "{item_name} {quantity}개 추가됐어요.",
            'order_modified': "{item_name} 수정됐어요.",
            'order_cancelled': "주문 취소됐어요.",
            'order_confirmed': "주문 확정. 결제해 주세요.",
            'clarification_needed': "다시 말씀해 주세요.",
            'menu_clarification': "메뉴명 말씀해 주세요.",
            'error_occurred': "오류 발생. 다시 시도해 주세요.",
            'order_summary': "주문 내역:\n{order_details}\n총 {total_amount}원",
            'payment_request': "결제?",
            'goodbye': "감사합니다!"
        }
    
    def _create_openai_client(self) -> OpenAI:
        """OpenAI 클라이언트 생성"""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에서 OPENAI_API_KEY를 설정하세요.")
        return OpenAI(api_key=api_key)
    
    def create_session(self) -> str:
        """새로운 대화 세션 생성"""
        session_id = str(uuid.uuid4())
        context = ConversationContext(
            session_id=session_id,
            conversation_history=[],
            current_order=None,
            user_preferences={},
            last_intent=None
        )
        self.active_contexts[session_id] = context
        return session_id
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """세션 컨텍스트 가져오기"""
        return self.active_contexts.get(session_id)
    
    def process_dialogue(self, session_id: str, intent: Intent) -> DialogueResponse:
        """
        대화 처리 및 응답 생성
        
        Args:
            session_id: 세션 ID
            intent: 사용자 의도
            
        Returns:
            DialogueResponse: 대화 응답
        """
        try:
            # 컨텍스트 가져오기 또는 생성
            context = self.active_contexts.get(session_id)
            if not context:
                context = ConversationContext(
                    session_id=session_id,
                    conversation_history=[],
                    current_order=self.order_manager.get_current_order(),
                    user_preferences={},
                    last_intent=None
                )
                self.active_contexts[session_id] = context
            
            # 현재 주문 ID 가져오기
            current_order = self.order_manager.get_current_order()
            order_id = current_order.order_id if current_order else None
            
            # 사용자 메시지를 대화 기록에 추가
            if intent.raw_text:
                context.add_message("user", intent.raw_text, order_id)
            
            # 의도별 처리
            response = self._handle_intent(intent, context)
            
            # 컨텍스트 업데이트
            context.last_intent = intent
            context.current_order = current_order
            
            # 시스템 응답을 대화 기록에 추가
            context.add_message("assistant", response.text, order_id)
            
            return response
            
        except Exception as e:
            error_response = self.error_handler.handle_general_error(e, "dialogue")
            return DialogueResponse(
                text=error_response.message,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["retry"],
                metadata={"error": str(e)}
            )
    
    def _handle_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """의도별 처리 로직"""
        
        print(f"🔍 [DEBUG] Intent 타입 처리: {intent.type}")
        
        if intent.type == IntentType.ORDER:
            print(f"🔍 [DEBUG] ORDER intent 처리")
            return self._handle_order_intent(intent, context)
        
        elif intent.type == IntentType.MODIFY:
            print(f"🔍 [DEBUG] MODIFY intent 처리")
            return self._handle_modify_intent(intent, context)
        
        elif intent.type == IntentType.CANCEL:
            print(f"🔍 [DEBUG] CANCEL intent 처리")
            return self._handle_cancel_intent(intent, context)
        
        elif intent.type == IntentType.PAYMENT:
            print(f"🔍 [DEBUG] PAYMENT intent 처리")
            return self._handle_payment_intent(intent, context)
        
        elif intent.type == IntentType.INQUIRY:
            print(f"🔍 [DEBUG] INQUIRY intent 처리")
            return self._handle_inquiry_intent(intent, context)
        
        else:
            print(f"🔍 [DEBUG] UNKNOWN intent 처리")
            return self._handle_unknown_intent(intent, context)
    
    def _handle_order_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """주문 의도 처리"""
        if not intent.menu_items:
            return DialogueResponse(
                text="메뉴 말씀해 주세요",
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["specify_menu"]
            )
        
        # 주문이 없으면 새로 생성
        if not self.order_manager.get_current_order():
            self.order_manager.create_new_order()
        
        results = []
        for menu_item in intent.menu_items:
            # 카테고리 정보를 옵션으로 변환
            options = menu_item.options.copy() if menu_item.options else {}
            
            # 카테고리가 단품/세트/라지세트인 경우 옵션으로 추가
            if menu_item.category in ["단품", "세트", "라지세트"]:
                options["type"] = menu_item.category
            
            result = self.order_manager.add_item(
                item_name=menu_item.name,
                quantity=menu_item.quantity,
                options=options
            )
            results.append(result)
        
        # 결과 처리
        successful_items = [r for r in results if r.success]
        failed_items = [r for r in results if not r.success]
        
        if successful_items and not failed_items:
            # 모든 아이템이 성공적으로 추가됨
            response_text = self._generate_order_success_response(successful_items)
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["continue_ordering", "confirm_order"]
            )
        
        elif successful_items and failed_items:
            # 일부만 성공
            success_text = self._generate_order_success_response(successful_items)
            error_text = self._generate_order_error_response(failed_items)
            response_text = f"{success_text}\n\n하지만 {error_text}"
            
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["retry_failed", "continue_ordering"]
            )
        
        else:
            # 모든 아이템이 실패
            error_text = self._generate_order_error_response(failed_items)
            return DialogueResponse(
                text=f"죄송합니다. {error_text}",
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["retry", "help"]
            )
    
    def _handle_modify_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """변경 의도 처리"""
        print(f"🔍 [DEBUG] modify_intent 처리 시작")
        print(f"🔍 [DEBUG] intent.modifications: {intent.modifications}")
        
        if not self.order_manager.get_current_order():
            return DialogueResponse(
                text="현재 진행 중인 주문이 없습니다. 먼저 주문을 해주세요.",
                order_state=None,
                requires_confirmation=False,
                suggested_actions=["start_order"]
            )
        
        if not intent.modifications:
            return DialogueResponse(
                text="어떤 것을 변경하시겠어요?",
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["specify_modification"]
            )
        
        results = []
        for modification in intent.modifications:
            print(f"🔍 [DEBUG] 변경 처리 중: {modification}")
            
            # 아이템명이 없는 경우 현재 주문의 첫 번째 아이템을 사용
            item_name = modification.item_name
            if not item_name or item_name.strip() == "":
                current_order = self.order_manager.get_current_order()
                if current_order and current_order.items:
                    item_name = current_order.items[0].name
                    print(f"🔍 [DEBUG] 아이템명 없음 - 첫 번째 아이템 사용: {item_name}")
                else:
                    print(f"🔍 [DEBUG] 현재 주문이 없거나 비어있음")
                    result = OrderResult(
                        success=False,
                        message="변경할 주문이 없습니다.",
                        order=self.order_manager.get_current_order()
                    )
                    results.append(result)
                    continue
            if modification.action == "add":
                result = self.order_manager.add_item(
                    item_name=item_name,
                    quantity=modification.new_quantity or 1,
                    options=modification.new_options
                )
            elif modification.action == "remove":
                result = self.order_manager.remove_item(
                    item_name=item_name,
                    quantity=modification.new_quantity
                )
            elif modification.action == "change_quantity":
                result = self.order_manager.modify_item(
                    item_name=item_name,
                    new_quantity=modification.new_quantity
                )
            elif modification.action == "change_option":
                print(f"🔍 [DEBUG] change_option 호출됨")
                print(f"🔍 [DEBUG] item_name: {item_name}")
                print(f"🔍 [DEBUG] new_quantity: {modification.new_quantity}")
                print(f"🔍 [DEBUG] new_options: {modification.new_options}")
                
                # new_options가 None인 경우 원본 텍스트에서 옵션 추출 (fallback 로직)
                new_options = modification.new_options
                if new_options is None and hasattr(intent, 'raw_text') and intent.raw_text:
                    original_text = intent.raw_text.lower()
                    print(f"🔍 [DEBUG] new_options가 None - 원본 텍스트에서 추출 시도: {original_text}")
                    
                    if "단품" in original_text:
                        new_options = {"type": "단품"}
                        print(f"🔍 [DEBUG] 단품으로 변경 감지")
                    elif "라지세트" in original_text:
                        new_options = {"type": "라지세트"}
                        print(f"🔍 [DEBUG] 라지세트로 변경 감지")
                    elif "세트" in original_text:
                        new_options = {"type": "세트"}
                        print(f"🔍 [DEBUG] 세트로 변경 감지")
                    
                    print(f"🔍 [DEBUG] fallback으로 추출된 new_options: {new_options}")
                
                result = self.order_manager.modify_item(
                    item_name=item_name,
                    new_quantity=modification.new_quantity or 1,
                    new_options=new_options
                )
                print(f"🔍 [DEBUG] modify_item 결과: {result}")
            else:
                result = OrderResult(
                    success=False,
                    message=f"알 수 없는 변경 액션입니다: {modification.action}",
                    order=self.order_manager.get_current_order()
                )
            
            results.append(result)
        
        # 결과 처리
        successful_changes = [r for r in results if r.success]
        failed_changes = [r for r in results if not r.success]
        
        print(f"🔍 [DEBUG] 성공한 변경: {len(successful_changes)}개")
        print(f"🔍 [DEBUG] 실패한 변경: {len(failed_changes)}개")
        
        if successful_changes and not failed_changes:
            response_text = "주문이 변경되었습니다."
            if len(successful_changes) == 1:
                response_text = successful_changes[0].message
            
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["continue_ordering", "confirm_order"]
            )
        
        else:
            error_messages = [r.message for r in failed_changes]
            response_text = f"변경 중 오류가 발생했습니다: {', '.join(error_messages)}"
            
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["retry", "help"]
            )
    
    def _handle_cancel_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """취소 의도 처리"""
        if not self.order_manager.get_current_order():
            return DialogueResponse(
                text="현재 진행 중인 주문이 없습니다.",
                order_state=None,
                requires_confirmation=False,
                suggested_actions=["start_order"]
            )
        
        if intent.cancel_items:
            # 특정 아이템 취소
            results = []
            for item_name in intent.cancel_items:
                result = self.order_manager.remove_item(item_name)
                results.append(result)
            
            successful_cancels = [r for r in results if r.success]
            failed_cancels = [r for r in results if not r.success]
            
            if successful_cancels and not failed_cancels:
                response_text = f"{len(successful_cancels)}개 메뉴가 주문에서 제거되었습니다."
            else:
                error_messages = [r.message for r in failed_cancels]
                response_text = f"취소 중 오류가 발생했습니다: {', '.join(error_messages)}"
            
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["continue_ordering", "confirm_order"]
            )
        
        else:
            # 전체 주문 취소
            return DialogueResponse(
                text="전체 주문을 취소하시겠습니까?",
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=True,
                suggested_actions=["confirm_cancel", "continue_ordering"]
            )
    
    def _handle_payment_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """결제 의도 처리 - Tool Calling 기반"""
        current_order = self.order_manager.get_current_order()
        print(f"🔍 [DEBUG] 결제 의도 처리 시작 - 주문: {current_order.order_id if current_order else 'None'}")
        
        if not current_order or not current_order.items:
            print(f"🔍 [DEBUG] 주문이 없음")
            return DialogueResponse(
                text="주문할 메뉴가 없어요. 먼저 메뉴를 주문해 주세요.",
                order_state=current_order,
                requires_confirmation=False,
                suggested_actions=["start_order"]
            )
        
        order_id = current_order.order_id
        print(f"🔍 [DEBUG] 처리할 주문 ID: {order_id}")
        
        # 현재 주문이 이미 결제 중인지 확인
        if self.is_order_in_payment(order_id):
            print(f"🔍 [DEBUG] 이미 결제 중인 주문 - 응답 처리")
            # 결제 중인 주문에 대한 사용자 응답 처리
            payment_result = self.handle_payment_processing(order_id, intent.raw_text or "")
            
            # 결제 진행 상황이 포함된 경우 metadata에 추가
            metadata = {}
            if "결제를 진행합니다" in payment_result:
                metadata["payment_progress"] = {
                    "steps": [
                        "결제를 진행합니다...",
                        "카드를 삽입해 주세요...",
                        "결제 승인 중...",
                        "결제가 완료되었습니다!"
                    ],
                    "step_delays": [1000, 1000, 1000, 0],  # 밀리초 단위
                    "total_amount": getattr(self.order_manager.get_order_summary(), 'total_amount', 0)
                }
            
            return DialogueResponse(
                text=payment_result,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["start_order"] if "완료" in payment_result else ["confirm", "cancel"],
                metadata=metadata
            )
        
        # 새로운 결제 요청
        print(f"🔍 [DEBUG] 새로운 결제 요청")
        
        # 주문 검증
        validation_result = self.order_manager.validate_order()
        if not validation_result.success:
            print(f"🔍 [DEBUG] 주문 검증 실패: {validation_result.message}")
            return DialogueResponse(
                text=f"주문을 확정할 수 없습니다: {validation_result.message}",
                order_state=current_order,
                requires_confirmation=False,
                suggested_actions=["fix_order", "help"]
            )
        
        order_summary = self.order_manager.get_order_summary()
        if order_summary:
            # 주문을 결제 중 상태로 설정
            print(f"🔍 [DEBUG] 주문을 결제 중 상태로 설정")
            self.set_order_payment_status(order_id, "processing")
            
            summary_text = self._format_order_summary(order_summary)
            response_text = f"{summary_text}\n결제하시겠어요?"
            
            return DialogueResponse(
                text=response_text,
                order_state=current_order,
                requires_confirmation=True,
                suggested_actions=["confirm", "cancel"]
            )
        
        else:
            print(f"🔍 [DEBUG] 주문 요약 생성 실패")
            return DialogueResponse(
                text="주문 요약을 생성할 수 없어요",
                order_state=current_order,
                requires_confirmation=False,
                suggested_actions=["retry", "help"]
            )
    
    def _handle_inquiry_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """문의 의도 처리"""
        inquiry_text = intent.inquiry_text or ""
        
        # 주문 상태 문의 - 더 넓은 범위의 키워드 매칭
        order_keywords = ["주문", "내역", "확인", "상태", "현재"]
        if any(keyword in inquiry_text for keyword in order_keywords):
            current_order = self.order_manager.get_current_order()
            if current_order:
                order_summary = self.order_manager.get_order_summary()
                summary_text = self._format_order_summary(order_summary)
                response_text = f"현재 주문 내역입니다:\n\n{summary_text}"
            else:
                response_text = "현재 진행 중인 주문이 없습니다."
            
            return DialogueResponse(
                text=response_text,
                order_state=current_order,
                requires_confirmation=False,
                suggested_actions=["continue_ordering", "start_order"]
            )
        
        # 메뉴 문의
        elif "메뉴" in inquiry_text:
            # 메뉴 정보를 직접 제공
            menu_info = self._get_formatted_menu_for_user()
            response_text = f"{menu_info}"
            
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["continue_ordering", "help"]
            )
        
        # 일반적인 문의
        else:
            response_text = self._generate_contextual_response(inquiry_text, context)
            
            return DialogueResponse(
                text=response_text,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["continue_ordering", "help"]
            )
    
    def _handle_unknown_intent(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """알 수 없는 의도 처리 - 결제 중 상태 우선 확인"""
        
        # 먼저 결제 중인 주문이 있는지 확인
        current_order = self.order_manager.get_current_order()
        if current_order and self.is_order_in_payment(current_order.order_id):
            # 결제 중인 주문에 대한 응답 처리
            payment_result = self.handle_payment_processing(current_order.order_id, intent.raw_text or "")
            
            # 결제 진행 상황이 포함된 경우 metadata에 추가
            metadata = {}
            if "결제를 진행합니다" in payment_result:
                metadata["payment_progress"] = {
                    "steps": [
                        "결제를 진행합니다...",
                        "카드를 삽입해 주세요...",
                        "결제 승인 중...",
                        "결제가 완료되었습니다!"
                    ],
                    "step_delays": [1000, 1000, 1000, 0],  # 밀리초 단위
                    "total_amount": getattr(self.order_manager.get_order_summary(), 'total_amount', 0)
                }
            
            return DialogueResponse(
                text=payment_result,
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["start_order"] if "완료" in payment_result else ["confirm", "cancel"],
                metadata=metadata
            )
        
        # 일반적인 경우 LLM으로 전달
        response_text = self._generate_contextual_response(intent.raw_text or "", context)
        
        return DialogueResponse(
            text=response_text,
            order_state=self.order_manager.get_current_order(),
            requires_confirmation=False,
            suggested_actions=["continue_ordering", "help"]
        )
    
    def _generate_contextual_response(self, user_input: str, context: ConversationContext) -> str:
        """컨텍스트 기반 응답 생성"""
        session_id = context.session_id
        
        # 현재 주문이 결제 중인지 확인 (새로운 tool calling 시스템)
        current_order = self.order_manager.get_current_order()
        if current_order and self.is_order_in_payment(current_order.order_id):
            # 결제 중인 주문에 대한 응답 처리
            payment_result = self.handle_payment_processing(current_order.order_id, user_input)
            return payment_result
        
        # 기존 결제 확인 대기 상태도 처리 (호환성 유지)
        if self.is_payment_confirmation_pending(session_id):
            # 현재 주문과 대화 히스토리를 함께 고려한 결제 처리
            order_id = current_order.order_id if current_order else None
            
            # 사용자 입력은 메인 플로우에서 추가됨
            
            # 긍정적 응답 패턴 매칭 강화
            positive_responses = [
                "네", "예", "알겠다", "확인", "좋아", "맞아", "그래", "응", 
                "오케이", "ok", "결제", "진행", "해주세요", "부탁", "합니다",
                "결제해", "결제할게", "결제하자", "결제진행", "결제해주세요",
                "맞습니다", "맞아요", "그렇습니다", "그래요", "좋습니다",
                "동의", "승인", "허가", "진행해", "계속", "yes", "y"
            ]
            
            # 부정적 응답 패턴
            negative_responses = [
                "아니", "안", "취소", "그만", "중단", "멈춰", "stop", "no", "n",
                "아니요", "아니야", "싫어", "안해", "안할래", "취소해", "취소할게"
            ]
            
            user_input_lower = user_input.lower().strip()
            user_input_clean = user_input_lower.replace(" ", "").replace(".", "").replace("!", "").replace("?", "")
            
            # 부정적 응답 먼저 확인 (더 명확한 의도)
            if any(response in user_input_clean for response in negative_responses):
                # 결제 상태 초기화
                self.clear_payment_confirmation_pending(session_id)
                if order_id:
                    self.set_order_payment_status(order_id, "pending")
                return "결제 취소됐어요"
            
            # 긍정적 응답 확인 (더 강화된 패턴 매칭)
            elif any(response in user_input_clean for response in positive_responses):
                # 직접 결제 처리
                order_summary = self.order_manager.get_order_summary()
                if order_summary:
                    # process_payment tool 호출
                    payment_result = self.process_payment(order_summary)
                    
                    # 주문 완료 처리
                    self.order_manager.confirm_order()
                    
                    # 결제 상태 초기화
                    self.clear_payment_confirmation_pending(session_id)
                    if order_id:
                        self.set_order_payment_status(order_id, "completed")
                    
                    # 새 주문 준비
                    self.order_manager.create_new_order()
                    
                    return payment_result
                else:
                    # 결제 상태 초기화
                    self.clear_payment_confirmation_pending(session_id)
                    if order_id:
                        self.set_order_payment_status(order_id, "pending")
                    return "주문 정보가 없어요"
            
            # 애매한 응답의 경우 재확인
            else:
                return "결제하시겠어요?"
        
        try:
            # 현재 주문 정보 가져오기
            current_order = self.order_manager.get_current_order()
            order_id = current_order.order_id if current_order else None
            
            # 사용자 입력은 메인 플로우에서 이미 추가됨
            
            # 메뉴 정보 가져오기
            menu_info = self._get_menu_info_for_llm()
            
            # 대화 기록 준비
            messages = [
                {
                    "role": "system",
                    "content": f"""당신은 식당 키오스크의 AI 어시스턴트입니다. 

                    ⚠️ 중요: 음성인식 오류를 고려한 응답
                    - 사용자 입력에서 발음이 유사한 단어를 실제 의도로 해석하세요
                    - 발음 유사도가 70% 이상인 경우 가장 유사한 의미로 이해하세요
                    - 문맥상 의미가 통하는 방향으로 해석하고 응답하세요
                    
                    현재 사용 가능한 메뉴:
                    {menu_info}
                    
                    응답 지침:
                    1. 모든 응답은 간결하고 명확하게 (1-2문장 이내)
                    2. 불분명한 요청: "잘 못 알아들었어요. 다시 말씀해 주세요"
                    3. 메뉴 문의: 위 메뉴 정보만 사용
                    4. 주문 유도: 간단하게 "메뉴 말씀해 주세요"
                    5. 길거나 복잡한 설명 금지
                    """
                }
            ]
            
            # 현재 주문 상태 정보 추가  
            if current_order and current_order.items:
                order_summary = self.order_manager.get_order_summary()
                order_info = self._format_order_summary(order_summary)
                messages.append({
                    "role": "system",
                    "content": f"현재 주문 상태:\n{order_info}"
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "현재 주문 상태: 주문된 메뉴가 없습니다."
                })
            
            # 현재 주문 ID의 대화 기록 추가 (모든 대화 포함)
            if current_order and current_order.order_id:
                order_messages = context.get_messages_by_order_id(current_order.order_id, 10)  # 더 많은 히스토리
                for msg in order_messages:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                # 현재 주문 대화 히스토리가 있는 경우 시스템 메시지에 추가
                if order_messages:
                    messages[0]["content"] += f"\n\n현재 주문({current_order.order_id})의 대화 기록을 참고하여 일관성 있게 응답하세요."
            else:
                # 주문 ID가 없는 경우 최근 대화 기록 추가
                recent_messages = context.get_recent_messages(5)
                for msg in recent_messages:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # 현재 사용자 입력 추가
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # OpenAI API 호출 - 간결한 응답을 위해 토큰 수 제한
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=50,  # 간결한 응답 유도
                temperature=0.3  # 일관성 있는 응답
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # LLM 응답은 메인 플로우에서 추가됨
            return response_text
            
        except Exception as e:
            # API 호출 실패 시 기본 응답
            return "다시 말씀해 주세요"
    
    def _generate_order_success_response(self, results: List[OrderResult]) -> str:
        """주문 성공 응답 생성 - 세부 옵션 표시"""
        menu_details = []
        
        for result in results:
            if result.success and result.added_item:
                # 추가된 특정 아이템 정보 사용
                added_item = result.added_item
                
                # 옵션 정보를 명확하게 포함하여 메뉴 표시
                option_text = ""
                if added_item.options and "type" in added_item.options:
                    option_text = f" {added_item.options['type']}"
                else:
                    # 옵션이 없는 경우 기본값으로 "단품" 표시
                    option_text = " 단품"
                
                # 각 항목의 옵션을 명확하게 구분하여 표시
                menu_detail = f"{added_item.name}{option_text} {added_item.quantity}개"
                menu_details.append(menu_detail)
        
        if menu_details:
            if len(menu_details) == 1:
                # 단일 항목의 경우도 세부 옵션 정보 포함
                return f"{menu_details[0]}이(가) 주문에 추가되었습니다."
            else:
                # 여러 항목의 경우 각 항목의 옵션을 명확하게 구분
                menu_list = ", ".join(menu_details)
                return f"{menu_list}이(가) 주문에 추가되었습니다."
        else:
            return f"{len(results)}개 메뉴가 주문에 추가되었습니다."
    
    def _generate_order_error_response(self, results: List[OrderResult]) -> str:
        """주문 오류 응답 생성"""
        error_messages = [r.message for r in results]
        return ", ".join(error_messages)
    
    def _format_order_summary(self, order_summary) -> str:
        """주문 요약 포맷팅 - 세부 옵션 표시"""
        if not order_summary or not order_summary.items:
            return "주문한 메뉴가 없습니다."
        
        lines = []
        for item in order_summary.items:
            # 옵션 정보를 명확하게 표시
            option_text = ""
            if item.options and "type" in item.options:
                option_text = f" {item.options['type']}"
            else:
                # 옵션이 없는 경우 기본값으로 "단품" 표시
                option_text = " 단품"
            
            line = f"- {item.name}{option_text} {item.quantity}개 - {item.price * item.quantity:,}원"
            lines.append(line)
        
        lines.append(f"\n총 금액: {order_summary.total_amount:,}원")
        return "\n".join(lines)
    
    def confirm_action(self, session_id: str, action: str) -> DialogueResponse:
        """사용자 확인 액션 처리"""
        context = self.active_contexts.get(session_id)
        if not context:
            return DialogueResponse(
                text="세션을 찾을 수 없습니다. 다시 시작해 주세요.",
                order_state=None,
                requires_confirmation=False,
                suggested_actions=["restart"]
            )
        
        if action == "confirm_cancel":
            # 전체 주문 취소 확인
            result = self.order_manager.clear_order()
            return DialogueResponse(
                text=result.message,
                order_state=result.order,
                requires_confirmation=False,
                suggested_actions=["start_order"] if result.success else ["retry"]
            )
        
        elif action == "confirm_payment":
            # 결제 확인
            result = self.order_manager.confirm_order()
            if result.success:
                response_text = f"{result.message} 감사합니다!"
                suggested_actions = ["new_order"]
            else:
                response_text = f"결제 처리 중 오류가 발생했습니다: {result.message}"
                suggested_actions = ["retry", "help"]
            
            return DialogueResponse(
                text=response_text,
                order_state=result.order,
                requires_confirmation=False,
                suggested_actions=suggested_actions
            )
        
        else:
            return DialogueResponse(
                text="알 수 없는 확인 액션입니다.",
                order_state=self.order_manager.get_current_order(),
                requires_confirmation=False,
                suggested_actions=["help"]
            )
    
    def end_session(self, session_id: str):
        """세션 종료"""
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
        
        # 결제 상태 정리
        self.clear_payment_confirmation_pending(session_id)
    
    def _get_menu_info_for_llm(self) -> str:
        """LLM에게 전달할 메뉴 정보 생성"""
        try:
            from ..config import config_manager
            menu_config = config_manager.load_menu_config()
            
            menu_lines = []
            menu_lines.append(f"식당명: {menu_config.restaurant_info.get('name', '테스트 식당')}")
            menu_lines.append(f"식당 유형: {menu_config.restaurant_info.get('type', 'fast_food')}")
            menu_lines.append("")
            menu_lines.append("=== 메뉴 목록 ===")
            
            # 카테고리별로 메뉴 정리
            for category in menu_config.categories:
                category_items = []
                for item_name, item_config in menu_config.menu_items.items():
                    if item_config.category == category:
                        item_info = f"{item_name}: {item_config.price:,}원"
                        if item_config.description:
                            item_info += f" - {item_config.description}"
                        if item_config.available_options:
                            item_info += f" (옵션: {', '.join(item_config.available_options)})"
                        category_items.append(item_info)
                
                if category_items:
                    menu_lines.append(f"\n[{category}]")
                    for item in category_items:
                        menu_lines.append(f"- {item}")
            
            # 세트 가격 정보
            if menu_config.set_pricing:
                menu_lines.append("\n=== 세트 추가 요금 ===")
                for set_type, price in menu_config.set_pricing.items():
                    menu_lines.append(f"- {set_type}: +{price:,}원")
            
            # 옵션 가격 정보
            if menu_config.option_pricing:
                menu_lines.append("\n=== 옵션 추가 요금 ===")
                for option, price in menu_config.option_pricing.items():
                    menu_lines.append(f"- {option}: +{price:,}원")
            
            return "\n".join(menu_lines)
            
        except Exception as e:
            return f"메뉴 정보를 불러올 수 없습니다: {e}"
    
    def _get_formatted_menu_for_user(self) -> str:
        """사용자에게 보여줄 메뉴 정보 생성"""
        try:
            from ..config import config_manager
            menu_config = config_manager.load_menu_config()
            
            menu_lines = []
            
            # 카테고리별로 메뉴 정리
            for category in menu_config.categories:
                category_items = []
                for item_name, item_config in menu_config.menu_items.items():
                    if item_config.category == category:
                        category_items.append(f"{item_name} ({item_config.price:,}원)")
                
                if category_items:
                    menu_lines.append(f"**{category}**")
                    menu_lines.append("- " + "\n- ".join(category_items))
                    menu_lines.append("")
            
            return "\n".join(menu_lines).strip()
            
        except Exception as e:
            return f"메뉴 정보를 불러올 수 없습니다: {e}"
    
    def process_payment(self, order_summary) -> str:
        """
        결제 프로세스 실행
        
        Args:
            order_summary: 주문 요약 정보
            
        Returns:
            결제 완료 메시지
        """
        print("결제를 진행합니다...")
        time.sleep(1)
        
        print("카드를 삽입해 주세요...")
        time.sleep(1)
        
        print("결제 승인 중...")
        time.sleep(1)
        
        print("결제가 완료되었습니다!")
        
        # 주문 요약 정보에서 총 금액 가져오기
        total_amount = getattr(order_summary, 'total_amount', 0)
        
        return f"결제가 완료되었습니다. 총 {total_amount:,}원이 결제되었습니다."
    
    def process_payment_with_progress(self, order_summary, progress_callback=None):
        """
        진행 상황을 콜백으로 전달하는 결제 프로세스
        
        Args:
            order_summary: 주문 요약 정보
            progress_callback: 진행 상황 콜백 함수
            
        Returns:
            결제 완료 메시지
        """
        steps = [
            "결제를 진행합니다...",
            "카드를 삽입해 주세요...",
            "결제 승인 중...",
            "결제가 완료되었습니다!"
        ]
        
        for i, step in enumerate(steps):
            print(step)
            if progress_callback:
                progress_callback(step, i + 1, len(steps))
            time.sleep(1)
        
        # 주문 요약 정보에서 총 금액 가져오기
        total_amount = getattr(order_summary, 'total_amount', 0)
        
        return f"결제가 완료되었습니다. 총 {total_amount:,}원이 결제되었습니다."
    
    def set_payment_confirmation_pending(self, session_id: str) -> None:
        """
        결제 확인 대기 상태 설정
        
        Args:
            session_id: 세션 ID
        """
        self.payment_confirmation_pending[session_id] = True
    
    def clear_payment_confirmation_pending(self, session_id: str) -> None:
        """
        결제 확인 대기 상태 해제
        
        Args:
            session_id: 세션 ID
        """
        if session_id in self.payment_confirmation_pending:
            del self.payment_confirmation_pending[session_id]
    
    def is_payment_confirmation_pending(self, session_id: str) -> bool:
        """
        결제 확인 대기 상태 확인
        
        Args:
            session_id: 세션 ID
            
        Returns:
            bool: 결제 확인 대기 중인지 여부
        """
        return self.payment_confirmation_pending.get(session_id, False)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 정보"""
        # order_payment_status 속성이 없으면 초기화
        if not hasattr(self, 'order_payment_status'):
            self.order_payment_status = {}
        
        return {
            'active_sessions': len(self.active_contexts),
            'session_ids': list(self.active_contexts.keys()),
            'payment_pending_sessions': len(self.payment_confirmation_pending),
            'orders_in_payment': len([status for status in self.order_payment_status.values() if status == "processing"])
        }
    
    # ============ Tool Calling Functions ============
    
    def set_order_payment_status(self, order_id: str, status: str) -> str:
        """
        주문의 결제 상태를 설정합니다.
        
        Args:
            order_id: 주문 ID
            status: 결제 상태 ("pending", "processing", "completed")
            
        Returns:
            결과 메시지
        """
        # order_payment_status 속성이 없으면 초기화
        if not hasattr(self, 'order_payment_status'):
            self.order_payment_status = {}
            print(f"🔍 [DEBUG] order_payment_status 속성 초기화")
        
        if status not in ["pending", "processing", "completed"]:
            return f"잘못된 결제 상태입니다: {status}"
        
        self.order_payment_status[order_id] = status
        print(f"🔍 [DEBUG] 주문 {order_id} 결제 상태 설정: {status}")
        print(f"🔍 [DEBUG] 현재 결제 상태 딕셔너리: {self.order_payment_status}")
        return f"주문 {order_id}의 결제 상태를 {status}로 설정했습니다."
    
    def get_order_payment_status(self, order_id: str) -> str:
        """
        주문의 결제 상태를 확인합니다.
        
        Args:
            order_id: 주문 ID
            
        Returns:
            결제 상태 ("pending", "processing", "completed", "not_found")
        """
        # order_payment_status 속성이 없으면 초기화
        if not hasattr(self, 'order_payment_status'):
            self.order_payment_status = {}
            print(f"🔍 [DEBUG] order_payment_status 속성 초기화")
        
        return self.order_payment_status.get(order_id, "not_found")
    
    def is_order_in_payment(self, order_id: str) -> bool:
        """
        주문이 결제 중인지 확인합니다.
        
        Args:
            order_id: 주문 ID
            
        Returns:
            결제 중 여부
        """
        # order_payment_status 속성이 없으면 초기화
        if not hasattr(self, 'order_payment_status'):
            self.order_payment_status = {}
            print(f"🔍 [DEBUG] order_payment_status 속성 초기화")
        
        status = self.order_payment_status.get(order_id)
        is_processing = status == "processing"
        print(f"🔍 [DEBUG] 주문 {order_id} 결제 상태 확인: {status}, 결제 중: {is_processing}")
        return is_processing
    
    def handle_payment_processing(self, order_id: str, user_input: str) -> str:
        """
        결제 중인 주문에 대한 사용자 입력을 처리합니다.
        
        Args:
            order_id: 주문 ID
            user_input: 사용자 입력
            
        Returns:
            응답 메시지
        """
        print(f"🔍 [DEBUG] 결제 처리 중 - 주문 ID: {order_id}, 사용자 입력: '{user_input}'")
        
        # 긍정적 응답 패턴
        positive_responses = ["네", "예", "좋아", "알겠다", "확인", "맞아", "그래", "응", "오케이", "ok", "yes"]
        negative_responses = ["아니", "아니요", "싫어", "안 할래", "취소", "no"]
        
        user_input_clean = user_input.lower().replace(" ", "").replace(".", "").replace("!", "").replace("?", "")
        print(f"🔍 [DEBUG] 정제된 입력: '{user_input_clean}'")
        
        # 부정적 응답 확인
        if any(response in user_input_clean for response in negative_responses):
            print(f"🔍 [DEBUG] 부정적 응답 감지")
            self.set_order_payment_status(order_id, "pending")
            return "결제가 취소되었습니다."
        
        # 긍정적 응답 확인
        elif any(response in user_input_clean for response in positive_responses):
            print(f"🔍 [DEBUG] 긍정적 응답 감지 - 결제 진행")
            # 실제 결제 처리
            order_summary = self.order_manager.get_order_summary()
            if order_summary:
                payment_result = self.process_payment_progressive(order_summary)
                self.order_manager.confirm_order()
                self.set_order_payment_status(order_id, "completed")
                self.order_manager.create_new_order()
                print(f"🔍 [DEBUG] 결제 완료: {payment_result}")
                return payment_result
            else:
                print(f"🔍 [DEBUG] 주문 정보 없음")
                self.set_order_payment_status(order_id, "pending")
                return "주문 정보가 없어서 결제할 수 없습니다."
        
        # 애매한 응답
        else:
            print(f"🔍 [DEBUG] 애매한 응답 - 재확인 요청")
            return "결제를 진행하시겠습니까? 네 또는 아니요로 답해주세요."
    
    def process_payment_progressive(self, order_summary) -> str:
        """
        단계별 결제 진행 - 각 단계를 클라이언트에 전달
        
        Args:
            order_summary: 주문 요약 정보
            
        Returns:
            결제 완료 메시지
        """
        # 진행 단계들을 순차적으로 클라이언트에 전달
        payment_steps = [
            "결제를 진행합니다...",
            "카드를 삽입해 주세요...", 
            "결제 승인 중...",
            "결제가 완료되었습니다!"
        ]
        
        # 각 단계를 print로 출력 (서버 콘솔용)
        for step in payment_steps:
            print(step)
            time.sleep(1)
        
        # 총 금액 가져오기
        total_amount = getattr(order_summary, 'total_amount', 0)
        
        # 최종 결제 완료 메시지에 모든 단계 포함
        all_steps = "\n".join(payment_steps)
        final_message = f"{all_steps}\n\n총 {total_amount:,}원이 결제되었습니다."
        
        return final_message