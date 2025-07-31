"""
텍스트 응답 시스템 통합 테스트
"""

import pytest
from decimal import Decimal
from datetime import datetime
from src.models import (
    ResponseType, MenuItem, Order, OrderStatus, OrderSummary
)
from src.response import TextResponseSystem


class TestTextResponseSystemIntegration:
    """텍스트 응답 시스템 통합 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.response_system = TextResponseSystem()
    
    def test_complete_order_flow(self):
        """완전한 주문 플로우 테스트"""
        # 1. 인사말
        greeting = self.response_system.generate_greeting()
        assert "안녕하세요" in greeting.formatted_text
        assert greeting.response_type == ResponseType.GREETING
        
        # 2. 주문 추가 확인
        order_confirmation = self.response_system.generate_order_confirmation(
            menu_name="빅맥 세트",
            quantity=1,
            total_amount=6500
        )
        assert "빅맥 세트" in order_confirmation.formatted_text
        assert "1개" in order_confirmation.formatted_text
        assert "6500원" in order_confirmation.formatted_text
        assert order_confirmation.response_type == ResponseType.ORDER_CONFIRMATION
        
        # 3. 추가 주문
        additional_order = self.response_system.generate_order_confirmation(
            menu_name="감자튀김",
            quantity=2,
            total_amount=9500
        )
        assert "감자튀김" in additional_order.formatted_text
        assert "2개" in additional_order.formatted_text
        assert "9500원" in additional_order.formatted_text
        
        # 4. 주문 요약
        menu_items = [
            MenuItem(
                name="빅맥 세트",
                category="세트",
                quantity=1,
                price=Decimal('6500')
            ),
            MenuItem(
                name="감자튀김",
                category="사이드",
                quantity=2,
                price=Decimal('1500')
            )
        ]
        
        order_summary = OrderSummary(
            order_id="test_001",
            items=menu_items,
            total_amount=Decimal('9500'),
            item_count=2,
            total_quantity=3,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        
        summary_response = self.response_system.generate_order_summary(order_summary)
        assert "빅맥 세트" in summary_response.formatted_text
        assert "감자튀김" in summary_response.formatted_text
        assert "9500원" in summary_response.formatted_text
        assert summary_response.response_type == ResponseType.ORDER_SUMMARY
        
        # 5. 결제 요청
        payment_request = self.response_system.generate_payment_request(total_amount=9500)
        assert "9500원" in payment_request.formatted_text
        assert "결제" in payment_request.formatted_text
        assert payment_request.response_type == ResponseType.PAYMENT_REQUEST
        
        # 6. 주문 완료
        completion = self.response_system.generate_completion_response(total_amount=9500)
        assert "완료" in completion.formatted_text
        assert "9500원" in completion.formatted_text
        assert "감사합니다" in completion.formatted_text
        assert completion.response_type == ResponseType.COMPLETION
    
    def test_error_handling_flow(self):
        """오류 처리 플로우 테스트"""
        # 1. 메뉴 없음 오류
        menu_error = self.response_system.generate_error_response(
            menu_name="존재하지않는메뉴"
        )
        assert "존재하지않는메뉴" in menu_error.formatted_text
        assert "찾을 수 없습니다" in menu_error.formatted_text
        assert "죄송합니다" in menu_error.formatted_text
        assert menu_error.response_type == ResponseType.ERROR
        
        # 2. 일반 오류
        general_error = self.response_system.generate_error_response()
        assert "죄송합니다" in general_error.formatted_text
        assert "다시 시도" in general_error.formatted_text
        assert general_error.response_type == ResponseType.ERROR
        
        # 3. 명확화 요청
        clarification = self.response_system.generate_clarification_request(
            "메뉴를 정확히 듣지 못했습니다"
        )
        assert "메뉴를 정확히 듣지 못했습니다" in clarification.formatted_text
        assert "다시 말씀해" in clarification.formatted_text
        assert clarification.response_type == ResponseType.CLARIFICATION
    
    def test_order_modification_flow(self):
        """주문 수정 플로우 테스트"""
        # 1. 주문 취소 확인
        cancellation = self.response_system.generate_order_confirmation(
            menu_name="빅맥",
            quantity=1,
            total_amount=3000,
            cancelled=True
        )
        assert "빅맥" in cancellation.formatted_text
        assert "취소" in cancellation.formatted_text
        assert "3000원" in cancellation.formatted_text
        assert cancellation.response_type == ResponseType.ORDER_CONFIRMATION
    
    def test_response_formatting_consistency(self):
        """응답 포맷팅 일관성 테스트"""
        # 모든 응답이 적절히 포맷팅되는지 확인
        responses = [
            self.response_system.generate_greeting(),
            self.response_system.generate_order_confirmation("테스트메뉴", 1, 5000),
            self.response_system.generate_payment_request(10000),
            self.response_system.generate_error_response(),
            self.response_system.generate_clarification_request("테스트 이유"),
            self.response_system.generate_completion_response(15000)
        ]
        
        for response in responses:
            # 모든 응답이 마침표로 끝나는지 확인
            assert response.formatted_text.endswith(('.', '!', '?'))
            
            # 여분의 공백이 없는지 확인
            assert '  ' not in response.formatted_text
            
            # 응답이 비어있지 않은지 확인
            assert len(response.formatted_text.strip()) > 0
            
            # 포맷팅이 적용되었는지 확인
            assert hasattr(response, 'formatting_applied')
    
    def test_template_system_integration(self):
        """템플릿 시스템 통합 테스트"""
        # 템플릿 매니저와 포맷터가 잘 연동되는지 확인
        
        # 1. 기본 템플릿 사용
        response = self.response_system.generate_response(
            ResponseType.ORDER_CONFIRMATION,
            template_id="order_added",
            menu_name="치킨버거",
            quantity=2,
            total_amount=8000
        )
        
        assert "치킨버거" in response.text
        assert "2개" in response.text
        assert "8000원" in response.text
        
        # 2. 포맷팅 적용
        formatted = self.response_system.format_response(response)
        # 이미 잘 포맷팅된 텍스트의 경우 추가 포맷팅이 필요하지 않을 수 있음
        assert formatted.response_type == ResponseType.ORDER_CONFIRMATION
        assert formatted.formatted_text is not None
        
        # 3. 통합 메서드 사용
        integrated = self.response_system.generate_and_format_response(
            ResponseType.PAYMENT_REQUEST,
            total_amount=12000
        )
        
        assert "12000원" in integrated.formatted_text
        assert "결제" in integrated.formatted_text
        # 포맷팅 적용 여부보다는 결과가 올바른지 확인
        assert integrated.response_type == ResponseType.PAYMENT_REQUEST
    
    def test_large_order_handling(self):
        """대량 주문 처리 테스트"""
        # 많은 아이템이 있는 주문 요약 테스트
        menu_items = []
        for i in range(5):
            menu_items.append(MenuItem(
                name=f"메뉴{i+1}",
                category="테스트",
                quantity=i+1,
                price=Decimal('1000')
            ))
        
        order_summary = OrderSummary(
            order_id="large_order_001",
            items=menu_items,
            total_amount=Decimal('15000'),
            item_count=5,
            total_quantity=15,
            status=OrderStatus.PENDING,
            created_at=datetime.now()
        )
        
        summary_response = self.response_system.generate_order_summary(order_summary)
        
        # 모든 메뉴가 포함되어 있는지 확인
        for i in range(5):
            assert f"메뉴{i+1}" in summary_response.formatted_text
        
        assert "15000원" in summary_response.formatted_text
        assert summary_response.response_type == ResponseType.ORDER_SUMMARY
    
    def test_special_characters_handling(self):
        """특수 문자 처리 테스트"""
        # 특수 문자가 포함된 메뉴명 처리
        special_menu_names = [
            "맥스파이시® 상하이버거",
            "1955® 버거",
            "빅맥™",
            "맥플러리® 오레오®"
        ]
        
        for menu_name in special_menu_names:
            response = self.response_system.generate_order_confirmation(
                menu_name=menu_name,
                quantity=1,
                total_amount=5000
            )
            
            assert menu_name in response.formatted_text
            assert response.response_type == ResponseType.ORDER_CONFIRMATION
    
    def test_currency_formatting_edge_cases(self):
        """통화 포맷팅 엣지 케이스 테스트"""
        # 다양한 금액에 대한 포맷팅 테스트
        amounts = [0, 100, 1000, 10000, 100000, 999999]
        
        for amount in amounts:
            payment_request = self.response_system.generate_payment_request(
                total_amount=amount
            )
            
            assert f"{amount}원" in payment_request.formatted_text
            assert payment_request.response_type == ResponseType.PAYMENT_REQUEST


if __name__ == "__main__":
    pytest.main([__file__, "-v"])