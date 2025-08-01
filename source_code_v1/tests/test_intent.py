"""
의도 파악 시스템 단위 테스트
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.conversation.intent import IntentRecognizer
from src.models.conversation_models import Intent, IntentType, ConversationContext, Modification
from src.models.order_models import MenuItem
from src.models.error_models import IntentError, IntentErrorType


class TestIntentRecognizer:
    """IntentRecognizer 클래스 테스트"""
    
    @pytest.fixture
    def mock_openai_client(self):
        """OpenAI 클라이언트 모킹"""
        with patch('src.conversation.intent.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_config(self):
        """설정 모킹"""
        with patch('src.conversation.intent.load_config') as mock_load_config:
            mock_load_config.return_value = {
                'openai': {
                    'api_key': 'test_api_key',
                    'model': 'gpt-4o'
                }
            }
            yield mock_load_config
    
    @pytest.fixture
    def intent_recognizer(self, mock_openai_client, mock_config):
        """IntentRecognizer 인스턴스"""
        return IntentRecognizer(api_key="test_api_key")
    
    def test_init_with_api_key(self, mock_openai_client, mock_config):
        """API 키로 초기화 테스트"""
        recognizer = IntentRecognizer(api_key="custom_api_key")
        assert recognizer.api_key == "custom_api_key"
        assert recognizer.model == "gpt-4o"
    
    def test_init_without_api_key(self, mock_openai_client, mock_config):
        """설정 파일에서 API 키 로드 테스트"""
        recognizer = IntentRecognizer()
        assert recognizer.api_key == "test_api_key"
    
    def test_init_invalid_api_key(self, mock_openai_client, mock_config):
        """잘못된 API 키 처리 테스트"""
        mock_config.return_value = {
            'openai': {
                'api_key': 'your_openai_api_key_here'
            }
        }
        
        with pytest.raises(ValueError, match="OpenAI API 키가 설정되지 않았습니다"):
            IntentRecognizer()
    
    def test_setup_intent_tools(self, intent_recognizer):
        """Tool 설정 테스트"""
        tools = intent_recognizer._setup_intent_tools()
        
        assert len(tools) == 5
        tool_names = [tool['function']['name'] for tool in tools]
        expected_names = [
            'recognize_order_intent',
            'recognize_modify_intent',
            'recognize_cancel_intent',
            'recognize_payment_intent',
            'recognize_inquiry_intent'
        ]
        
        for name in expected_names:
            assert name in tool_names
    
    def test_build_system_message_basic(self, intent_recognizer):
        """기본 시스템 메시지 구성 테스트"""
        message = intent_recognizer._build_system_message()
        
        assert "식당 음성 키오스크의 의도 파악 시스템" in message
        assert "ORDER (주문)" in message
        assert "MODIFY (변경)" in message
        assert "CANCEL (취소)" in message
        assert "PAYMENT (결제)" in message
        assert "INQUIRY (문의)" in message
    
    def test_build_system_message_with_context(self, intent_recognizer):
        """컨텍스트가 있는 시스템 메시지 구성 테스트"""
        context = ConversationContext(session_id="test_session")
        context.add_message("user", "빅맥 세트 주문하고 싶어요")
        context.add_message("assistant", "빅맥 세트 주문을 도와드리겠습니다")
        
        message = intent_recognizer._build_system_message(context)
        
        assert "최근 대화 기록" in message
        assert "빅맥 세트 주문하고 싶어요" in message
    
    def test_build_messages(self, intent_recognizer):
        """메시지 구성 테스트"""
        text = "빅맥 세트 하나 주문할게요"
        messages = intent_recognizer._build_messages(text)
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == text
    
    def test_recognize_order_intent(self, intent_recognizer, mock_openai_client):
        """주문 의도 파악 테스트"""
        # Mock API 응답
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        
        mock_tool_call.function.name = "recognize_order_intent"
        mock_tool_call.function.arguments = json.dumps({
            "menu_items": [
                {
                    "name": "빅맥",
                    "category": "세트",
                    "quantity": 1,
                    "options": {"drink": "콜라"}
                }
            ],
            "confidence": 0.9
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_response.choices = [Mock(message=mock_message)]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # 테스트 실행
        text = "빅맥 세트 하나 주문할게요"
        intent = intent_recognizer.recognize_intent(text)
        
        # 검증
        assert intent.type == IntentType.ORDER
        assert intent.confidence == 0.9
        assert len(intent.menu_items) == 1
        assert intent.menu_items[0].name == "빅맥"
        assert intent.menu_items[0].category == "세트"
        assert intent.menu_items[0].quantity == 1
        assert intent.menu_items[0].options == {"drink": "콜라"}
        assert intent.raw_text == text
    
    def test_recognize_modify_intent(self, intent_recognizer, mock_openai_client):
        """변경 의도 파악 테스트"""
        # Mock API 응답
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        
        mock_tool_call.function.name = "recognize_modify_intent"
        mock_tool_call.function.arguments = json.dumps({
            "modifications": [
                {
                    "item_name": "빅맥",
                    "action": "change_quantity",
                    "new_quantity": 2
                }
            ],
            "confidence": 0.8
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_response.choices = [Mock(message=mock_message)]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # 테스트 실행
        text = "빅맥을 2개로 변경해주세요"
        intent = intent_recognizer.recognize_intent(text)
        
        # 검증
        assert intent.type == IntentType.MODIFY
        assert intent.confidence == 0.8
        assert len(intent.modifications) == 1
        assert intent.modifications[0].item_name == "빅맥"
        assert intent.modifications[0].action == "change_quantity"
        assert intent.modifications[0].new_quantity == 2
    
    def test_recognize_cancel_intent(self, intent_recognizer, mock_openai_client):
        """취소 의도 파악 테스트"""
        # Mock API 응답
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        
        mock_tool_call.function.name = "recognize_cancel_intent"
        mock_tool_call.function.arguments = json.dumps({
            "cancel_items": ["빅맥", "감자튀김"],
            "confidence": 0.95
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_response.choices = [Mock(message=mock_message)]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # 테스트 실행
        text = "빅맥이랑 감자튀김 취소해주세요"
        intent = intent_recognizer.recognize_intent(text)
        
        # 검증
        assert intent.type == IntentType.CANCEL
        assert intent.confidence == 0.95
        assert intent.cancel_items == ["빅맥", "감자튀김"]
    
    def test_recognize_payment_intent(self, intent_recognizer, mock_openai_client):
        """결제 의도 파악 테스트"""
        # Mock API 응답
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        
        mock_tool_call.function.name = "recognize_payment_intent"
        mock_tool_call.function.arguments = json.dumps({
            "payment_method": "card",
            "confidence": 0.9
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_response.choices = [Mock(message=mock_message)]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # 테스트 실행
        text = "카드로 결제할게요"
        intent = intent_recognizer.recognize_intent(text)
        
        # 검증
        assert intent.type == IntentType.PAYMENT
        assert intent.confidence == 0.9
        assert intent.payment_method == "card"
    
    def test_recognize_inquiry_intent(self, intent_recognizer, mock_openai_client):
        """문의 의도 파악 테스트"""
        # Mock API 응답
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        
        mock_tool_call.function.name = "recognize_inquiry_intent"
        mock_tool_call.function.arguments = json.dumps({
            "inquiry_text": "빅맥의 칼로리가 얼마나 되나요?",
            "confidence": 0.85
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_response.choices = [Mock(message=mock_message)]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # 테스트 실행
        text = "빅맥의 칼로리가 얼마나 되나요?"
        intent = intent_recognizer.recognize_intent(text)
        
        # 검증
        assert intent.type == IntentType.INQUIRY
        assert intent.confidence == 0.85
        assert intent.inquiry_text == "빅맥의 칼로리가 얼마나 되나요?"
    
    def test_recognize_unknown_intent(self, intent_recognizer, mock_openai_client):
        """알 수 없는 의도 처리 테스트"""
        # Mock API 응답 (tool_calls 없음)
        mock_response = Mock()
        mock_message = Mock()
        mock_message.tool_calls = None
        mock_response.choices = [Mock(message=mock_message)]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        # 테스트 실행
        text = "알 수 없는 입력"
        intent = intent_recognizer.recognize_intent(text)
        
        # 검증
        assert intent.type == IntentType.UNKNOWN
        assert intent.confidence == 0.0
        assert intent.raw_text == text
    
    def test_recognize_intent_api_error(self, intent_recognizer, mock_openai_client):
        """API 오류 처리 테스트"""
        # API 오류 시뮬레이션
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        # 테스트 실행 및 검증
        with pytest.raises(IntentError) as exc_info:
            intent_recognizer.recognize_intent("테스트 텍스트")
        
        assert exc_info.value.error_type == IntentErrorType.RECOGNITION_FAILED
        assert "의도 파악에 실패했습니다" in str(exc_info.value)
    
    def test_batch_recognize_intents(self, intent_recognizer, mock_openai_client):
        """일괄 의도 파악 테스트"""
        # Mock API 응답들
        responses = []
        for i in range(2):
            mock_response = Mock()
            mock_message = Mock()
            mock_tool_call = Mock()
            
            mock_tool_call.function.name = "recognize_order_intent"
            mock_tool_call.function.arguments = json.dumps({
                "menu_items": [{"name": f"메뉴{i}", "category": "단품", "quantity": 1}],
                "confidence": 0.8
            })
            
            mock_message.tool_calls = [mock_tool_call]
            mock_response.choices = [Mock(message=mock_message)]
            responses.append(mock_response)
        
        mock_openai_client.chat.completions.create.side_effect = responses
        
        # 테스트 실행
        texts = ["메뉴0 주문", "메뉴1 주문"]
        intents = intent_recognizer.batch_recognize_intents(texts)
        
        # 검증
        assert len(intents) == 2
        for i, intent in enumerate(intents):
            assert intent.type == IntentType.ORDER
            assert intent.menu_items[0].name == f"메뉴{i}"
    
    def test_batch_recognize_intents_with_error(self, intent_recognizer, mock_openai_client):
        """일괄 의도 파악 중 오류 처리 테스트"""
        # 첫 번째는 성공, 두 번째는 실패
        mock_response = Mock()
        mock_message = Mock()
        mock_tool_call = Mock()
        
        mock_tool_call.function.name = "recognize_order_intent"
        mock_tool_call.function.arguments = json.dumps({
            "menu_items": [{"name": "메뉴", "category": "단품", "quantity": 1}],
            "confidence": 0.8
        })
        
        mock_message.tool_calls = [mock_tool_call]
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_openai_client.chat.completions.create.side_effect = [
            mock_response,
            Exception("API Error")
        ]
        
        # 테스트 실행
        texts = ["메뉴 주문", "오류 텍스트"]
        intents = intent_recognizer.batch_recognize_intents(texts)
        
        # 검증
        assert len(intents) == 2
        assert intents[0].type == IntentType.ORDER
        assert intents[1].type == IntentType.UNKNOWN  # 오류 시 UNKNOWN으로 처리
    
    def test_get_intent_confidence_threshold(self, intent_recognizer):
        """의도별 신뢰도 임계값 테스트"""
        assert intent_recognizer.get_intent_confidence_threshold(IntentType.ORDER) == 0.7
        assert intent_recognizer.get_intent_confidence_threshold(IntentType.MODIFY) == 0.8
        assert intent_recognizer.get_intent_confidence_threshold(IntentType.CANCEL) == 0.9
        assert intent_recognizer.get_intent_confidence_threshold(IntentType.PAYMENT) == 0.8
        assert intent_recognizer.get_intent_confidence_threshold(IntentType.INQUIRY) == 0.6
        assert intent_recognizer.get_intent_confidence_threshold(IntentType.UNKNOWN) == 0.0
    
    def test_is_intent_reliable(self, intent_recognizer):
        """의도 신뢰도 검증 테스트"""
        # 높은 신뢰도 의도
        high_confidence_intent = Intent(
            type=IntentType.ORDER,
            confidence=0.9,
            menu_items=[MenuItem(name="테스트", category="단품", quantity=1, price=0)]
        )
        assert intent_recognizer.is_intent_reliable(high_confidence_intent) is True
        
        # 낮은 신뢰도 의도
        low_confidence_intent = Intent(
            type=IntentType.ORDER,
            confidence=0.5,
            menu_items=[MenuItem(name="테스트", category="단품", quantity=1, price=0)]
        )
        assert intent_recognizer.is_intent_reliable(low_confidence_intent) is False
    
    def test_create_intent_from_tool_call_unknown_function(self, intent_recognizer):
        """알 수 없는 함수 호출 처리 테스트"""
        intent = intent_recognizer._create_intent_from_tool_call(
            "unknown_function",
            {"confidence": 0.5},
            "테스트 텍스트"
        )
        
        assert intent.type == IntentType.UNKNOWN
        assert intent.confidence == 0.0
        assert intent.raw_text == "테스트 텍스트"


class TestIntentRecognitionIntegration:
    """의도 파악 통합 테스트"""
    
    @pytest.fixture
    def mock_config(self):
        """설정 모킹"""
        with patch('src.conversation.intent.load_config') as mock_load_config:
            mock_load_config.return_value = {
                'openai': {
                    'api_key': 'test_api_key',
                    'model': 'gpt-4o'
                }
            }
            yield mock_load_config
    
    def test_full_order_recognition_flow(self, mock_config):
        """전체 주문 인식 플로우 테스트"""
        with patch('src.conversation.intent.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock API 응답
            mock_response = Mock()
            mock_message = Mock()
            mock_tool_call = Mock()
            
            mock_tool_call.function.name = "recognize_order_intent"
            mock_tool_call.function.arguments = json.dumps({
                "menu_items": [
                    {
                        "name": "빅맥",
                        "category": "세트",
                        "quantity": 2,
                        "options": {"drink": "콜라", "side": "감자튀김"}
                    }
                ],
                "confidence": 0.95
            })
            
            mock_message.tool_calls = [mock_tool_call]
            mock_response.choices = [Mock(message=mock_message)]
            mock_client.chat.completions.create.return_value = mock_response
            
            # 테스트 실행
            recognizer = IntentRecognizer(api_key="test_key")
            context = ConversationContext(session_id="test_session")
            
            intent = recognizer.recognize_intent("빅맥 세트 2개 주문하고 싶어요", context)
            
            # 검증
            assert intent.type == IntentType.ORDER
            assert intent.confidence == 0.95
            assert recognizer.is_intent_reliable(intent) is True
            assert len(intent.menu_items) == 1
            
            menu_item = intent.menu_items[0]
            assert menu_item.name == "빅맥"
            assert menu_item.category == "세트"
            assert menu_item.quantity == 2
            assert menu_item.options["drink"] == "콜라"
            assert menu_item.options["side"] == "감자튀김"