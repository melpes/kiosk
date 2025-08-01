"""
대화 관리 시스템 테스트
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.conversation.dialogue import DialogueManager
from src.models.conversation_models import (
    Intent, IntentType, ConversationContext, DialogueResponse, Modification
)
from src.models.order_models import MenuItem, Order, OrderStatus, OrderResult, OrderSummary
from src.order.order import OrderManager
from src.order.menu import Menu


class TestDialogueManager:
    """DialogueManager 클래스 테스트"""
    
    @pytest.fixture
    def mock_menu(self):
        """테스트용 메뉴 모킹"""
        menu = Mock(spec=Menu)
        menu.get_item.return_value = Mock(
            name="빅맥",
            category="버거",
            price=5900,
            is_available=True,
            available_options=["콜라", "사이다", "오렌지주스"]
        )
        menu.validate_item.return_value = True
        return menu
    
    @pytest.fixture
    def mock_order_manager(self, mock_menu):
        """테스트용 주문 관리자"""
        order_manager = OrderManager(mock_menu)
        return order_manager
    
    @pytest.fixture
    def mock_openai_client(self):
        """테스트용 OpenAI 클라이언트 모킹"""
        client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "안녕하세요! 도움을 드리겠습니다."
        client.chat.completions.create.return_value = mock_response
        return client
    
    @pytest.fixture
    def dialogue_manager(self, mock_order_manager, mock_openai_client):
        """테스트용 DialogueManager 인스턴스"""
        with patch('src.conversation.dialogue.load_config') as mock_config:
            mock_config.return_value = {'openai': {'api_key': 'test-key'}}
            manager = DialogueManager(mock_order_manager, mock_openai_client)
            return manager
    
    def test_create_session(self, dialogue_manager):
        """세션 생성 테스트"""
        session_id = dialogue_manager.create_session()
        
        assert isinstance(session_id, str)
        assert session_id in dialogue_manager.active_contexts
        
        context = dialogue_manager.get_context(session_id)
        assert context is not None
        assert context.session_id == session_id
        assert context.conversation_history == []
    
    def test_get_context(self, dialogue_manager):
        """컨텍스트 가져오기 테스트"""
        session_id = dialogue_manager.create_session()
        context = dialogue_manager.get_context(session_id)
        
        assert context is not None
        assert context.session_id == session_id
        
        # 존재하지 않는 세션
        non_existent_context = dialogue_manager.get_context("non-existent")
        assert non_existent_context is None
    
    def test_handle_order_intent_success(self, dialogue_manager, mock_order_manager):
        """주문 의도 처리 성공 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 메뉴 아이템 생성
        menu_item = MenuItem(
            name="빅맥",
            category="버거",
            quantity=2,
            price=5900
        )
        
        # 주문 의도 생성
        intent = Intent(
            type=IntentType.ORDER,
            confidence=0.9,
            menu_items=[menu_item],
            raw_text="빅맥 2개 주문할게요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert isinstance(response, DialogueResponse)
        assert "주문에 추가되었습니다" in response.text
        assert not response.requires_confirmation
        assert "continue_ordering" in response.suggested_actions
    
    def test_handle_order_intent_no_items(self, dialogue_manager):
        """메뉴 아이템 없는 주문 의도 테스트"""
        session_id = dialogue_manager.create_session()
        
        # Intent 모델의 검증을 우회하기 위해 직접 생성
        intent = Intent.__new__(Intent)
        intent.type = IntentType.ORDER
        intent.confidence = 0.8
        intent.menu_items = None
        intent.modifications = None
        intent.cancel_items = None
        intent.payment_method = None
        intent.inquiry_text = None
        intent.raw_text = "주문하고 싶어요"
        intent.timestamp = datetime.now()
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "어떤 메뉴를 주문하시겠어요?" in response.text
        assert "specify_menu" in response.suggested_actions
    
    def test_handle_modify_intent_no_order(self, dialogue_manager, mock_order_manager):
        """주문 없이 변경 의도 처리 테스트"""
        session_id = dialogue_manager.create_session()
        
        intent = Intent(
            type=IntentType.MODIFY,
            confidence=0.8,
            modifications=[Modification(item_name="빅맥", action="remove")],
            raw_text="빅맥 빼주세요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "현재 진행 중인 주문이 없습니다" in response.text
        assert "start_order" in response.suggested_actions
    
    def test_handle_modify_intent_success(self, dialogue_manager, mock_order_manager):
        """변경 의도 처리 성공 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성하고 아이템을 추가
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 2)
        
        intent = Intent(
            type=IntentType.MODIFY,
            confidence=0.9,
            modifications=[Modification(item_name="빅맥", action="remove", new_quantity=1)],
            raw_text="빅맥 1개 빼주세요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "주문이 변경되었습니다" in response.text or "제거되었습니다" in response.text
        assert "continue_ordering" in response.suggested_actions
    
    def test_handle_cancel_intent_specific_items(self, dialogue_manager, mock_order_manager):
        """특정 아이템 취소 의도 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성하고 아이템을 추가
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 1)
        
        intent = Intent(
            type=IntentType.CANCEL,
            confidence=0.9,
            cancel_items=["빅맥"],
            raw_text="빅맥 취소해주세요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "1개 메뉴가 주문에서 제거되었습니다" in response.text
        assert "continue_ordering" in response.suggested_actions
    
    def test_handle_cancel_intent_all_order(self, dialogue_manager, mock_order_manager):
        """전체 주문 취소 의도 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성하고 아이템을 추가
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 1)
        
        # Intent 모델의 검증을 우회하기 위해 직접 생성
        intent = Intent.__new__(Intent)
        intent.type = IntentType.CANCEL
        intent.confidence = 0.9
        intent.menu_items = None
        intent.modifications = None
        intent.cancel_items = None  # 전체 취소의 경우 None
        intent.payment_method = None
        intent.inquiry_text = None
        intent.raw_text = "주문 전체 취소해주세요"
        intent.timestamp = datetime.now()
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "전체 주문을 취소하시겠습니까?" in response.text
        assert response.requires_confirmation
        assert "confirm_cancel" in response.suggested_actions
    
    def test_handle_payment_intent_success(self, dialogue_manager, mock_order_manager):
        """결제 의도 처리 성공 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성하고 아이템을 추가
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 1)
        
        intent = Intent(
            type=IntentType.PAYMENT,
            confidence=0.9,
            payment_method="카드",
            raw_text="결제할게요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "주문 내역을 확인해 주세요" in response.text
        assert "빅맥" in response.text
        assert response.requires_confirmation
        assert "confirm_payment" in response.suggested_actions
    
    def test_handle_payment_intent_no_order(self, dialogue_manager, mock_order_manager):
        """주문 없이 결제 의도 테스트"""
        session_id = dialogue_manager.create_session()
        
        intent = Intent(
            type=IntentType.PAYMENT,
            confidence=0.9,
            raw_text="결제할게요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "현재 진행 중인 주문이 없습니다" in response.text
        assert "start_order" in response.suggested_actions
    
    def test_handle_inquiry_intent_order_status(self, dialogue_manager, mock_order_manager):
        """주문 상태 문의 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성하고 아이템을 추가
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 1)
        
        intent = Intent(
            type=IntentType.INQUIRY,
            confidence=0.8,
            inquiry_text="현재 주문 상태가 어떻게 되나요?",
            raw_text="현재 주문 상태가 어떻게 되나요?"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "현재 주문 내역입니다" in response.text
        assert "빅맥" in response.text
    
    def test_handle_unknown_intent_low_confidence(self, dialogue_manager):
        """낮은 신뢰도의 알 수 없는 의도 테스트"""
        session_id = dialogue_manager.create_session()
        
        intent = Intent(
            type=IntentType.UNKNOWN,
            confidence=0.3,
            raw_text="음... 뭔가..."
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        assert "정확히 이해하지 못했습니다" in response.text
        assert "clarify" in response.suggested_actions
    
    def test_confirm_action_cancel(self, dialogue_manager, mock_order_manager):
        """취소 확인 액션 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 1)
        
        response = dialogue_manager.confirm_action(session_id, "confirm_cancel")
        
        assert "주문이 취소되었습니다" in response.text
        assert "start_order" in response.suggested_actions
    
    def test_confirm_action_payment(self, dialogue_manager, mock_order_manager):
        """결제 확인 액션 테스트"""
        session_id = dialogue_manager.create_session()
        
        # 먼저 주문을 생성하고 아이템을 추가
        mock_order_manager.create_new_order()
        mock_order_manager.add_item("빅맥", 1)
        
        response = dialogue_manager.confirm_action(session_id, "confirm_payment")
        
        assert "주문이 확정되었습니다" in response.text
        assert "감사합니다" in response.text
        assert "new_order" in response.suggested_actions
    
    def test_end_session(self, dialogue_manager):
        """세션 종료 테스트"""
        session_id = dialogue_manager.create_session()
        
        assert session_id in dialogue_manager.active_contexts
        
        dialogue_manager.end_session(session_id)
        
        assert session_id not in dialogue_manager.active_contexts
    
    def test_get_session_stats(self, dialogue_manager):
        """세션 통계 테스트"""
        session1 = dialogue_manager.create_session()
        session2 = dialogue_manager.create_session()
        
        stats = dialogue_manager.get_session_stats()
        
        assert stats['active_sessions'] == 2
        assert session1 in stats['session_ids']
        assert session2 in stats['session_ids']
    
    def test_conversation_history_tracking(self, dialogue_manager):
        """대화 기록 추적 테스트"""
        session_id = dialogue_manager.create_session()
        
        intent = Intent(
            type=IntentType.INQUIRY,
            confidence=0.8,
            inquiry_text="안녕하세요",
            raw_text="안녕하세요"
        )
        
        dialogue_manager.process_dialogue(session_id, intent)
        
        context = dialogue_manager.get_context(session_id)
        assert len(context.conversation_history) == 2  # user + assistant
        assert context.conversation_history[0]['role'] == 'user'
        assert context.conversation_history[1]['role'] == 'assistant'
    
    def test_error_handling(self, dialogue_manager, mock_order_manager):
        """오류 처리 테스트"""
        session_id = dialogue_manager.create_session()
        
        # mock_menu의 get_item이 None을 반환하도록 설정
        mock_order_manager.menu.get_item.return_value = None
        
        menu_item = MenuItem(name="존재하지않는메뉴", category="버거", quantity=1, price=5900)
        intent = Intent(
            type=IntentType.ORDER,
            confidence=0.9,
            menu_items=[menu_item],
            raw_text="존재하지않는메뉴 주문할게요"
        )
        
        response = dialogue_manager.process_dialogue(session_id, intent)
        
        # 메뉴를 찾을 수 없다는 오류 메시지가 포함되어야 함
        assert "메뉴를 찾을 수 없습니다" in response.text or "죄송합니다" in response.text
    
    def test_format_order_summary(self, dialogue_manager):
        """주문 요약 포맷팅 테스트"""
        from decimal import Decimal
        
        order_summary = OrderSummary(
            order_id="test-order",
            items=[
                MenuItem(name="빅맥", category="버거", quantity=2, price=5900, options={"음료": "콜라"}),
                MenuItem(name="감자튀김", category="사이드", quantity=1, price=2400)
            ],
            total_amount=Decimal('14200'),
            item_count=2,
            total_quantity=3,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        
        formatted = dialogue_manager._format_order_summary(order_summary)
        
        assert "빅맥 2개" in formatted
        assert "음료: 콜라" in formatted
        assert "감자튀김 1개" in formatted
        assert "14,200원" in formatted
    
    @patch('src.conversation.dialogue.load_config')
    def test_openai_client_creation_error(self, mock_config, mock_order_manager):
        """OpenAI 클라이언트 생성 오류 테스트"""
        mock_config.return_value = {}  # API 키 없음
        
        with pytest.raises(ValueError, match="OpenAI API 키가 설정되지 않았습니다"):
            DialogueManager(mock_order_manager)