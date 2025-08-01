"""
데이터 모델 단위 테스트
"""

import pytest
import numpy as np
from datetime import datetime
from decimal import Decimal

from src.models import (
    # Audio models
    AudioData, ProcessedAudio,
    
    # Speech models
    RecognitionResult,
    
    # Conversation models
    Intent, IntentType, Modification, ConversationContext, DialogueResponse,
    
    # Order models
    MenuItem, Order, OrderStatus, OrderResult, OrderSummary,
    
    # Config models
    MenuConfig, AudioConfig, TTSConfig, MenuItemConfig, SystemConfig,
    
    # Error models
    ErrorResponse, ErrorAction,
    AudioError, AudioErrorType,
    RecognitionError, RecognitionErrorType,
    IntentError, IntentErrorType,
    OrderError, OrderErrorType
)

from src.error.handler import ErrorHandler


class TestAudioModels:
    """음성 모델 테스트"""
    
    def test_audio_data_creation(self):
        """AudioData 생성 테스트"""
        data = np.random.random(16000)  # 1초 분량의 16kHz 오디오
        audio = AudioData(
            data=data,
            sample_rate=16000,
            channels=1,
            duration=1.0
        )
        
        assert audio.data is not None
        assert audio.sample_rate == 16000
        assert audio.channels == 1
        assert audio.duration == 1.0
    
    def test_audio_data_validation(self):
        """AudioData 검증 테스트"""
        # 빈 데이터
        with pytest.raises(ValueError, match="음성 데이터가 비어있습니다"):
            AudioData(data=np.array([]), sample_rate=16000, channels=1, duration=1.0)
        
        # 잘못된 샘플링 레이트
        with pytest.raises(ValueError, match="샘플링 레이트는 양수여야 합니다"):
            AudioData(data=np.array([1, 2, 3]), sample_rate=0, channels=1, duration=1.0)
        
        # 잘못된 채널 수
        with pytest.raises(ValueError, match="채널 수는 양수여야 합니다"):
            AudioData(data=np.array([1, 2, 3]), sample_rate=16000, channels=0, duration=1.0)
    
    def test_processed_audio_creation(self):
        """ProcessedAudio 생성 테스트"""
        features = np.random.random((80, 3000))  # Whisper 표준 특징 크기
        processed = ProcessedAudio(features=features)
        
        assert processed.features.shape == (80, 3000)
        assert processed.sample_rate == 16000
        assert processed.mel_filters == 80
        assert processed.time_steps == 3000
    
    def test_processed_audio_validation(self):
        """ProcessedAudio 검증 테스트"""
        # 잘못된 특징 크기
        with pytest.raises(ValueError, match="특징 크기가 올바르지 않습니다"):
            ProcessedAudio(features=np.random.random((40, 1500)))
        
        # 잘못된 샘플링 레이트
        with pytest.raises(ValueError, match="처리된 음성의 샘플링 레이트는 16kHz여야 합니다"):
            ProcessedAudio(features=np.random.random((80, 3000)), sample_rate=22050)


class TestSpeechModels:
    """음성인식 모델 테스트"""
    
    def test_recognition_result_creation(self):
        """RecognitionResult 생성 테스트"""
        result = RecognitionResult(
            text="안녕하세요",
            confidence=0.95,
            processing_time=1.5
        )
        
        assert result.text == "안녕하세요"
        assert result.confidence == 0.95
        assert result.processing_time == 1.5
        assert result.language == "ko"
        assert result.is_high_confidence is True
        assert result.is_low_confidence is False
    
    def test_recognition_result_validation(self):
        """RecognitionResult 검증 테스트"""
        # 잘못된 신뢰도
        with pytest.raises(ValueError, match="신뢰도는 0.0과 1.0 사이의 값이어야 합니다"):
            RecognitionResult(text="test", confidence=1.5, processing_time=1.0)
        
        # 음수 처리 시간
        with pytest.raises(ValueError, match="처리 시간은 음수일 수 없습니다"):
            RecognitionResult(text="test", confidence=0.8, processing_time=-1.0)


class TestConversationModels:
    """대화 모델 테스트"""
    
    def test_intent_creation(self):
        """Intent 생성 테스트"""
        menu_item = MenuItem(name="빅맥", category="버거", quantity=1, price=Decimal("5500"))
        intent = Intent(
            type=IntentType.ORDER,
            confidence=0.9,
            menu_items=[menu_item]
        )
        
        assert intent.type == IntentType.ORDER
        assert intent.confidence == 0.9
        assert len(intent.menu_items) == 1
        assert intent.is_high_confidence is True
    
    def test_intent_validation(self):
        """Intent 검증 테스트"""
        # 주문 의도인데 메뉴 아이템이 없음
        with pytest.raises(ValueError, match="주문 의도에는 메뉴 아이템이 필요합니다"):
            Intent(type=IntentType.ORDER, confidence=0.9)
        
        # 변경 의도인데 변경 사항이 없음
        with pytest.raises(ValueError, match="변경 의도에는 변경 사항이 필요합니다"):
            Intent(type=IntentType.MODIFY, confidence=0.9)
    
    def test_conversation_context(self):
        """ConversationContext 테스트"""
        context = ConversationContext(session_id="test_session")
        context.add_message("user", "빅맥 주문하고 싶어요")
        context.add_message("assistant", "빅맥 1개 주문하시겠습니까?")
        
        assert len(context.conversation_history) == 2
        recent = context.get_recent_messages(1)
        assert len(recent) == 1
        assert recent[0]["role"] == "assistant"


class TestOrderModels:
    """주문 모델 테스트"""
    
    def test_menu_item_creation(self):
        """MenuItem 생성 테스트"""
        item = MenuItem(
            name="빅맥",
            category="버거",
            quantity=2,
            price=Decimal("5500")
        )
        
        assert item.name == "빅맥"
        assert item.quantity == 2
        assert item.total_price == Decimal("11000")
    
    def test_menu_item_validation(self):
        """MenuItem 검증 테스트"""
        # 빈 메뉴명
        with pytest.raises(ValueError, match="메뉴명은 비어있을 수 없습니다"):
            MenuItem(name="", category="버거", quantity=1, price=Decimal("5500"))
        
        # 잘못된 수량
        with pytest.raises(ValueError, match="수량은 양수여야 합니다"):
            MenuItem(name="빅맥", category="버거", quantity=0, price=Decimal("5500"))
    
    def test_order_operations(self):
        """Order 작업 테스트"""
        order = Order()
        item1 = MenuItem(name="빅맥", category="버거", quantity=1, price=Decimal("5500"))
        item2 = MenuItem(name="감자튀김", category="사이드", quantity=1, price=Decimal("2000"))
        
        # 아이템 추가
        order.add_item(item1)
        order.add_item(item2)
        
        assert len(order.items) == 2
        assert order.total_amount == Decimal("7500")
        assert order.item_count == 2
        assert not order.is_empty
        
        # 아이템 제거
        order.remove_item("빅맥")
        assert len(order.items) == 1
        assert order.total_amount == Decimal("2000")
        
        # 주문 초기화
        order.clear()
        assert order.is_empty
        assert order.total_amount == Decimal("0")


class TestConfigModels:
    """설정 모델 테스트"""
    
    def test_menu_item_config(self):
        """MenuItemConfig 테스트"""
        config = MenuItemConfig(
            name="빅맥",
            category="버거",
            price=Decimal("5500"),
            available_options=["세트", "라지세트"]
        )
        
        assert config.name == "빅맥"
        assert config.price == Decimal("5500")
        assert config.is_available is True
    
    def test_menu_config(self):
        """MenuConfig 테스트"""
        item_config = MenuItemConfig(name="빅맥", category="버거", price=Decimal("5500"))
        menu_config = MenuConfig(
            restaurant_type="fast_food",
            menu_items={"빅맥": item_config},
            categories=["버거", "사이드", "음료"]
        )
        
        assert menu_config.restaurant_type == "fast_food"
        assert len(menu_config.categories) == 3
        assert menu_config.is_item_available("빅맥") is True
        
        burger_items = menu_config.get_items_by_category("버거")
        assert len(burger_items) == 1
        assert burger_items[0].name == "빅맥"
    
    def test_audio_config_validation(self):
        """AudioConfig 검증 테스트"""
        # 잘못된 노이즈 제거 레벨
        with pytest.raises(ValueError, match="노이즈 제거 레벨은 0.0과 1.0 사이여야 합니다"):
            AudioConfig(noise_reduction_level=1.5)
        
        # 잘못된 화자 분리 임계값
        with pytest.raises(ValueError, match="화자 분리 임계값은 0.0과 1.0 사이여야 합니다"):
            AudioConfig(speaker_separation_threshold=-0.1)
    
    def test_tts_config_validation(self):
        """TTSConfig 검증 테스트"""
        # 잘못된 속도
        with pytest.raises(ValueError, match="속도는 0.5와 2.0 사이여야 합니다"):
            TTSConfig(speed=3.0)
        
        # 잘못된 볼륨
        with pytest.raises(ValueError, match="볼륨은 0.0과 1.0 사이여야 합니다"):
            TTSConfig(volume=1.5)


class TestErrorModels:
    """오류 모델 테스트"""
    
    def test_error_response_creation(self):
        """ErrorResponse 생성 테스트"""
        response = ErrorResponse(
            message="음성이 명확하지 않습니다",
            action=ErrorAction.REQUEST_RETRY
        )
        
        assert response.message == "음성이 명확하지 않습니다"
        assert response.action == ErrorAction.REQUEST_RETRY
        assert response.retry_count == 0
        assert response.can_recover is True
    
    def test_error_handler_audio_error(self):
        """ErrorHandler 음성 오류 처리 테스트"""
        handler = ErrorHandler()
        error = AudioError(
            error_type=AudioErrorType.LOW_QUALITY,
            message="Low quality audio detected"
        )
        
        response = handler.handle_audio_error(error)
        assert "음성이 명확하지 않습니다" in response.message
        assert response.action == ErrorAction.REQUEST_RETRY
    
    def test_error_handler_recognition_error(self):
        """ErrorHandler 음성인식 오류 처리 테스트"""
        handler = ErrorHandler()
        error = RecognitionError(
            error_type=RecognitionErrorType.LOW_CONFIDENCE,
            message="Low confidence recognition",
            confidence=0.3
        )
        
        response = handler.handle_recognition_error(error)
        assert "정확히 듣지 못했습니다" in response.message
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
    
    def test_error_handler_intent_error(self):
        """ErrorHandler 의도 파악 오류 처리 테스트"""
        handler = ErrorHandler()
        error = IntentError(
            error_type=IntentErrorType.UNKNOWN_INTENT,
            message="Unknown intent detected"
        )
        
        response = handler.handle_intent_error(error)
        assert "이해하지 못한 요청입니다" in response.message
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
        assert len(response.suggested_alternatives) > 0
    
    def test_error_handler_order_error(self):
        """ErrorHandler 주문 오류 처리 테스트"""
        handler = ErrorHandler()
        error = OrderError(
            error_type=OrderErrorType.ITEM_NOT_FOUND,
            message="Item not found",
            item_name="존재하지않는메뉴"
        )
        
        response = handler.handle_order_error(error)
        assert "메뉴를 찾을 수 없습니다" in response.message
        assert response.action == ErrorAction.REQUEST_CLARIFICATION
    
    def test_error_count_management(self):
        """오류 카운트 관리 테스트"""
        handler = ErrorHandler()
        error_key = "test_error"
        
        # 초기 카운트는 0
        assert handler.get_error_count(error_key) == 0
        
        # 카운트 증가
        handler._get_and_increment_error_count(error_key)
        assert handler.get_error_count(error_key) == 1
        
        # 카운트 리셋
        handler.reset_error_count(error_key)
        assert handler.get_error_count(error_key) == 0


if __name__ == "__main__":
    pytest.main([__file__])