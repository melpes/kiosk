"""
텍스트 응답 시스템
"""

from typing import Dict, Any, Optional, List
from ..models import (
    TextResponse, FormattedResponse, ResponseType, ResponseFormat,
    ResponseTemplate, OrderSummary, MenuItem
)
from .template_manager import TemplateManager
from .formatter import ResponseFormatter


class TextResponseSystem:
    """텍스트 응답 시스템 메인 클래스"""
    
    def __init__(self, template_config_path: Optional[str] = None):
        """
        텍스트 응답 시스템 초기화
        
        Args:
            template_config_path: 템플릿 설정 파일 경로
        """
        self.template_manager = TemplateManager(template_config_path)
        self.formatter = ResponseFormatter()
    
    def generate_response(
        self,
        response_type: ResponseType,
        template_id: Optional[str] = None,
        **kwargs
    ) -> TextResponse:
        """
        응답 생성
        
        Args:
            response_type: 응답 타입
            template_id: 사용할 템플릿 ID (선택사항)
            **kwargs: 템플릿 변수
            
        Returns:
            TextResponse: 생성된 텍스트 응답
        """
        # 템플릿 선택
        if template_id:
            template = self.template_manager.get_template(template_id)
        else:
            # 응답 타입에 따른 기본 템플릿 선택
            template = self._select_default_template(response_type, **kwargs)
        
        if not template:
            # 템플릿이 없는 경우 기본 응답 생성
            text = self._generate_fallback_response(response_type, **kwargs)
        else:
            # 템플릿을 사용한 응답 생성
            try:
                text = template.format(**kwargs)
            except ValueError as e:
                print(f"템플릿 포맷팅 오류: {e}")
                text = self._generate_fallback_response(response_type, **kwargs)
        
        return TextResponse(
            text=text,
            response_type=response_type,
            format_type=ResponseFormat.TEMPLATE if template else ResponseFormat.TEXT,
            template_id=template.template_id if template else None
        )
    
    def format_response(self, response: TextResponse) -> FormattedResponse:
        """
        응답 포맷팅
        
        Args:
            response: 원본 텍스트 응답
            
        Returns:
            FormattedResponse: 포맷팅된 응답
        """
        return self.formatter.format_response(response)
    
    def generate_and_format_response(
        self,
        response_type: ResponseType,
        template_id: Optional[str] = None,
        **kwargs
    ) -> FormattedResponse:
        """
        응답 생성 및 포맷팅을 한번에 수행
        
        Args:
            response_type: 응답 타입
            template_id: 사용할 템플릿 ID (선택사항)
            **kwargs: 템플릿 변수
            
        Returns:
            FormattedResponse: 생성 및 포맷팅된 응답
        """
        response = self.generate_response(response_type, template_id, **kwargs)
        return self.format_response(response)
    
    def _select_default_template(self, response_type: ResponseType, **kwargs) -> Optional[ResponseTemplate]:
        """응답 타입에 따른 기본 템플릿 선택"""
        template_mapping = {
            ResponseType.GREETING: "greeting",
            ResponseType.ORDER_CONFIRMATION: self._select_order_template(**kwargs),
            ResponseType.ORDER_SUMMARY: "order_summary",
            ResponseType.PAYMENT_REQUEST: "payment_request",
            ResponseType.ERROR: self._select_error_template(**kwargs),
            ResponseType.CLARIFICATION: "clarification_needed",
            ResponseType.COMPLETION: "order_completion"
        }
        
        template_id = template_mapping.get(response_type)
        if template_id:
            return self.template_manager.get_template(template_id)
        return None
    
    def _select_order_template(self, **kwargs) -> str:
        """주문 관련 템플릿 선택"""
        if 'cancelled' in kwargs and kwargs['cancelled']:
            return "order_cancelled"
        elif 'quantity' in kwargs and kwargs.get('confirm_quantity', False):
            return "quantity_confirmation"
        else:
            return "order_added"
    
    def _select_error_template(self, **kwargs) -> str:
        """오류 관련 템플릿 선택"""
        if 'menu_name' in kwargs:
            return "menu_not_found"
        else:
            return "error_general"
    
    def _generate_fallback_response(self, response_type: ResponseType, **kwargs) -> str:
        """템플릿이 없을 때 사용할 기본 응답 생성"""
        fallback_responses = {
            ResponseType.GREETING: "안녕하세요! 주문을 도와드리겠습니다.",
            ResponseType.ORDER_CONFIRMATION: "주문이 처리되었습니다.",
            ResponseType.ORDER_SUMMARY: "주문 내역을 확인해 주세요.",
            ResponseType.PAYMENT_REQUEST: "결제를 진행하시겠습니까?",
            ResponseType.ERROR: "죄송합니다. 다시 시도해 주세요.",
            ResponseType.CLARIFICATION: "다시 말씀해 주시겠어요?",
            ResponseType.COMPLETION: "주문이 완료되었습니다. 감사합니다!"
        }
        
        return fallback_responses.get(response_type, "처리 중입니다.")
    
    # 편의 메서드들
    def generate_greeting(self) -> FormattedResponse:
        """인사말 생성"""
        return self.generate_and_format_response(ResponseType.GREETING)
    
    def generate_order_confirmation(
        self,
        menu_name: str,
        quantity: int,
        total_amount: int,
        cancelled: bool = False
    ) -> FormattedResponse:
        """주문 확인 응답 생성"""
        return self.generate_and_format_response(
            ResponseType.ORDER_CONFIRMATION,
            menu_name=menu_name,
            quantity=quantity,
            total_amount=total_amount,
            cancelled=cancelled
        )
    
    def generate_order_summary(self, order_summary: OrderSummary) -> FormattedResponse:
        """주문 요약 응답 생성"""
        # 주문 아이템 목록을 문자열로 변환
        order_items_text = self.formatter.format_menu_list(order_summary.items)
        
        return self.generate_and_format_response(
            ResponseType.ORDER_SUMMARY,
            order_items=order_items_text,
            total_amount=order_summary.total_amount
        )
    
    def generate_payment_request(self, total_amount: int) -> FormattedResponse:
        """결제 요청 응답 생성"""
        return self.generate_and_format_response(
            ResponseType.PAYMENT_REQUEST,
            total_amount=total_amount
        )
    
    def generate_error_response(
        self,
        error_message: Optional[str] = None,
        menu_name: Optional[str] = None
    ) -> FormattedResponse:
        """오류 응답 생성"""
        kwargs = {}
        if menu_name:
            kwargs['menu_name'] = menu_name
        if error_message:
            kwargs['error_message'] = error_message
            
        return self.generate_and_format_response(ResponseType.ERROR, **kwargs)
    
    def generate_clarification_request(self, reason: str) -> FormattedResponse:
        """명확화 요청 응답 생성"""
        return self.generate_and_format_response(
            ResponseType.CLARIFICATION,
            clarification_reason=reason
        )
    
    def generate_completion_response(self, total_amount: int) -> FormattedResponse:
        """완료 응답 생성"""
        return self.generate_and_format_response(
            ResponseType.COMPLETION,
            total_amount=total_amount
        )