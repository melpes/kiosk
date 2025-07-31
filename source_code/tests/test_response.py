"""
텍스트 응답 시스템 테스트
"""

import pytest
from unittest.mock import Mock, patch
from src.models import (
    ResponseType, ResponseFormat, ResponseTemplate,
    TextResponse, FormattedResponse, OrderSummary, MenuItem, OrderStatus
)
from src.response import TextResponseSystem, TemplateManager, ResponseFormatter


class TestTemplateManager:
    """템플릿 관리자 테스트"""
    
    def test_template_manager_initialization(self):
        """템플릿 관리자 초기화 테스트"""
        manager = TemplateManager()
        
        # 기본 템플릿들이 로드되었는지 확인
        assert len(manager.templates) > 0
        assert "greeting" in manager.templates
        assert "order_added" in manager.templates
        assert "order_summary" in manager.templates
    
    def test_get_template(self):
        """템플릿 조회 테스트"""
        manager = TemplateManager()
        
        # 존재하는 템플릿 조회
        template = manager.get_template("greeting")
        assert template is not None
        assert template.template_id == "greeting"
        assert template.response_type == ResponseType.GREETING
        
        # 존재하지 않는 템플릿 조회
        template = manager.get_template("nonexistent")
        assert template is None
    
    def test_get_templates_by_type(self):
        """응답 타입별 템플릿 조회 테스트"""
        manager = TemplateManager()
        
        greeting_templates = manager.get_templates_by_type(ResponseType.GREETING)
        assert len(greeting_templates) >= 1
        assert all(t.response_type == ResponseType.GREETING for t in greeting_templates)
    
    def test_add_template(self):
        """템플릿 추가 테스트"""
        manager = TemplateManager()
        
        new_template = ResponseTemplate(
            template_id="test_template",
            template_text="테스트 템플릿: {test_var}",
            variables={"test_var": "str"},
            response_type=ResponseType.GREETING
        )
        
        manager.add_template(new_template)
        
        retrieved = manager.get_template("test_template")
        assert retrieved is not None
        assert retrieved.template_id == "test_template"
    
    def test_remove_template(self):
        """템플릿 제거 테스트"""
        manager = TemplateManager()
        
        # 존재하는 템플릿 제거
        result = manager.remove_template("greeting")
        assert result is True
        assert manager.get_template("greeting") is None
        
        # 존재하지 않는 템플릿 제거
        result = manager.remove_template("nonexistent")
        assert result is False


class TestResponseFormatter:
    """응답 포맷터 테스트"""
    
    def test_formatter_initialization(self):
        """포맷터 초기화 테스트"""
        formatter = ResponseFormatter()
        assert formatter.formatting_rules is not None
        assert "currency_format" in formatter.formatting_rules
        assert "quantity_format" in formatter.formatting_rules
    
    def test_basic_formatting(self):
        """기본 포맷팅 테스트"""
        formatter = ResponseFormatter()
        
        response = TextResponse(
            text="테스트 메시지   입니다",
            response_type=ResponseType.ORDER_CONFIRMATION,  # GREETING이 아닌 다른 타입 사용
            format_type=ResponseFormat.TEXT
        )
        
        formatted = formatter.format_response(response)
        
        assert formatted.formatted_text == "테스트 메시지 입니다."
        assert formatted.formatting_applied is True
    
    def test_currency_formatting(self):
        """통화 포맷팅 테스트"""
        formatter = ResponseFormatter()
        
        response = TextResponse(
            text="총 5000원입니다",
            response_type=ResponseType.PAYMENT_REQUEST,
            format_type=ResponseFormat.TEXT
        )
        
        formatted = formatter.format_response(response)
        assert "5000원" in formatted.formatted_text
    
    def test_greeting_formatting(self):
        """인사말 포맷팅 테스트"""
        formatter = ResponseFormatter()
        
        response = TextResponse(
            text="주문을 도와드리겠습니다",
            response_type=ResponseType.GREETING,
            format_type=ResponseFormat.TEXT
        )
        
        formatted = formatter.format_response(response)
        assert "안녕하세요!" in formatted.formatted_text
    
    def test_error_message_formatting(self):
        """오류 메시지 포맷팅 테스트"""
        formatter = ResponseFormatter()
        
        response = TextResponse(
            text="다시 시도해 주세요",
            response_type=ResponseType.ERROR,
            format_type=ResponseFormat.TEXT
        )
        
        formatted = formatter.format_response(response)
        assert "죄송합니다." in formatted.formatted_text
    
    def test_format_menu_list(self):
        """메뉴 목록 포맷팅 테스트"""
        formatter = ResponseFormatter()
        
        # 빈 목록
        result = formatter.format_menu_list([])
        assert result == "주문 내역이 없습니다"
        
        # 단일 아이템
        item1 = Mock()
        item1.name = "빅맥"
        item1.quantity = 1
        result = formatter.format_menu_list([item1])
        assert result == "빅맥 1개"
        
        # 두 개 아이템
        item2 = Mock()
        item2.name = "감자튀김"
        item2.quantity = 2
        result = formatter.format_menu_list([item1, item2])
        assert result == "빅맥 1개와 감자튀김 2개"


class TestTextResponseSystem:
    """텍스트 응답 시스템 테스트"""
    
    def test_system_initialization(self):
        """시스템 초기화 테스트"""
        system = TextResponseSystem()
        
        assert system.template_manager is not None
        assert system.formatter is not None
    
    def test_generate_response_with_template(self):
        """템플릿을 사용한 응답 생성 테스트"""
        system = TextResponseSystem()
        
        response = system.generate_response(
            ResponseType.ORDER_CONFIRMATION,
            template_id="order_added",
            menu_name="빅맥",
            quantity=1,
            total_amount=5000
        )
        
        assert response.response_type == ResponseType.ORDER_CONFIRMATION
        assert response.format_type == ResponseFormat.TEMPLATE
        assert "빅맥" in response.text
        assert "1개" in response.text
        assert "5000원" in response.text
    
    def test_generate_response_without_template(self):
        """템플릿 없이 응답 생성 테스트"""
        system = TextResponseSystem()
        
        response = system.generate_response(ResponseType.GREETING)
        
        assert response.response_type == ResponseType.GREETING
        assert response.text is not None
        assert len(response.text) > 0
    
    def test_format_response(self):
        """응답 포맷팅 테스트"""
        system = TextResponseSystem()
        
        response = TextResponse(
            text="테스트 응답",
            response_type=ResponseType.GREETING,
            format_type=ResponseFormat.TEXT
        )
        
        formatted = system.format_response(response)
        
        assert isinstance(formatted, FormattedResponse)
        assert formatted.original_text == "테스트 응답"
        assert formatted.response_type == ResponseType.GREETING
    
    def test_generate_and_format_response(self):
        """응답 생성 및 포맷팅 통합 테스트"""
        system = TextResponseSystem()
        
        formatted = system.generate_and_format_response(
            ResponseType.ORDER_CONFIRMATION,
            menu_name="빅맥",
            quantity=1,
            total_amount=5000
        )
        
        assert isinstance(formatted, FormattedResponse)
        assert formatted.response_type == ResponseType.ORDER_CONFIRMATION
        assert "빅맥" in formatted.formatted_text
    
    def test_generate_greeting(self):
        """인사말 생성 테스트"""
        system = TextResponseSystem()
        
        greeting = system.generate_greeting()
        
        assert greeting.response_type == ResponseType.GREETING
        assert "안녕하세요" in greeting.formatted_text
    
    def test_generate_order_confirmation(self):
        """주문 확인 응답 생성 테스트"""
        system = TextResponseSystem()
        
        confirmation = system.generate_order_confirmation(
            menu_name="빅맥",
            quantity=2,
            total_amount=10000
        )
        
        assert confirmation.response_type == ResponseType.ORDER_CONFIRMATION
        assert "빅맥" in confirmation.formatted_text
        assert "2개" in confirmation.formatted_text
        assert "10000원" in confirmation.formatted_text
    
    def test_generate_order_summary(self):
        """주문 요약 응답 생성 테스트"""
        system = TextResponseSystem()
        
        # Mock 주문 요약 생성
        mock_item = Mock()
        mock_item.name = "빅맥"
        mock_item.quantity = 1
        
        from decimal import Decimal
        from datetime import datetime
        
        order_summary = OrderSummary(
            order_id="test_order_001",
            items=[mock_item],
            total_amount=Decimal('5000'),
            item_count=1,
            total_quantity=1,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        
        summary = system.generate_order_summary(order_summary)
        
        assert summary.response_type == ResponseType.ORDER_SUMMARY
        assert "빅맥" in summary.formatted_text
        assert "5000원" in summary.formatted_text
    
    def test_generate_payment_request(self):
        """결제 요청 응답 생성 테스트"""
        system = TextResponseSystem()
        
        payment_request = system.generate_payment_request(total_amount=15000)
        
        assert payment_request.response_type == ResponseType.PAYMENT_REQUEST
        assert "15000원" in payment_request.formatted_text
        assert "결제" in payment_request.formatted_text
    
    def test_generate_error_response(self):
        """오류 응답 생성 테스트"""
        system = TextResponseSystem()
        
        # 일반 오류
        error_response = system.generate_error_response()
        assert error_response.response_type == ResponseType.ERROR
        assert "죄송합니다" in error_response.formatted_text
        
        # 메뉴 없음 오류
        menu_error = system.generate_error_response(menu_name="존재하지않는메뉴")
        assert "존재하지않는메뉴" in menu_error.formatted_text
    
    def test_generate_clarification_request(self):
        """명확화 요청 응답 생성 테스트"""
        system = TextResponseSystem()
        
        clarification = system.generate_clarification_request("메뉴를 정확히 듣지 못했습니다.")
        
        assert clarification.response_type == ResponseType.CLARIFICATION
        assert "메뉴를 정확히 듣지 못했습니다" in clarification.formatted_text
        assert "다시 말씀해" in clarification.formatted_text
    
    def test_generate_completion_response(self):
        """완료 응답 생성 테스트"""
        system = TextResponseSystem()
        
        completion = system.generate_completion_response(total_amount=20000)
        
        assert completion.response_type == ResponseType.COMPLETION
        assert "20000원" in completion.formatted_text
        assert "완료" in completion.formatted_text
        assert "감사합니다" in completion.formatted_text
    
    def test_fallback_response_generation(self):
        """대체 응답 생성 테스트"""
        system = TextResponseSystem()
        
        # 존재하지 않는 템플릿 ID로 응답 생성
        response = system.generate_response(
            ResponseType.GREETING,
            template_id="nonexistent_template"
        )
        
        assert response.response_type == ResponseType.GREETING
        assert response.text is not None
        assert len(response.text) > 0


class TestResponseTemplate:
    """응답 템플릿 테스트"""
    
    def test_template_format(self):
        """템플릿 포맷팅 테스트"""
        template = ResponseTemplate(
            template_id="test",
            template_text="안녕하세요 {name}님, {quantity}개 주문하셨습니다.",
            variables={"name": "str", "quantity": "int"},
            response_type=ResponseType.GREETING
        )
        
        result = template.format(name="홍길동", quantity=2)
        assert result == "안녕하세요 홍길동님, 2개 주문하셨습니다."
    
    def test_template_format_missing_variable(self):
        """템플릿 변수 누락 테스트"""
        template = ResponseTemplate(
            template_id="test",
            template_text="안녕하세요 {name}님",
            variables={"name": "str"},
            response_type=ResponseType.GREETING
        )
        
        with pytest.raises(ValueError, match="템플릿 변수 누락"):
            template.format()  # name 변수 누락


if __name__ == "__main__":
    pytest.main([__file__])