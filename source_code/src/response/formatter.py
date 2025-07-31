"""
응답 포맷터
"""

import re
from typing import Dict, Any, Optional
from ..models import TextResponse, FormattedResponse, ResponseType, ResponseFormat


class ResponseFormatter:
    """응답 포맷팅 클래스"""
    
    def __init__(self):
        """포맷터 초기화"""
        self.formatting_rules = self._get_default_formatting_rules()
    
    def _get_default_formatting_rules(self) -> Dict[str, Any]:
        """기본 포맷팅 규칙"""
        return {
            "currency_format": {
                "pattern": r"(\d+)원",
                "replacement": r"\1원"
            },
            "quantity_format": {
                "pattern": r"(\d+)개",
                "replacement": r"\1개"
            },
            "politeness": {
                "add_honorifics": True,
                "formal_ending": True
            },
            "punctuation": {
                "ensure_period": True,
                "remove_extra_spaces": True
            }
        }
    
    def format_response(self, response: TextResponse) -> FormattedResponse:
        """
        응답 포맷팅
        
        Args:
            response: 원본 텍스트 응답
            
        Returns:
            FormattedResponse: 포맷팅된 응답
        """
        formatted_text = response.text
        formatting_applied = False
        
        # 기본 포맷팅 적용
        formatted_text, applied = self._apply_basic_formatting(formatted_text)
        formatting_applied = formatting_applied or applied
        
        # 응답 타입별 특수 포맷팅
        formatted_text, applied = self._apply_type_specific_formatting(
            formatted_text, response.response_type
        )
        formatting_applied = formatting_applied or applied
        
        return FormattedResponse(
            original_text=response.text,
            formatted_text=formatted_text,
            response_type=response.response_type,
            formatting_applied=formatting_applied,
            formatting_rules=self.formatting_rules
        )
    
    def _apply_basic_formatting(self, text: str) -> tuple[str, bool]:
        """기본 포맷팅 적용"""
        original_text = text
        
        # 여분의 공백 제거
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 마침표 확인 및 추가
        if self.formatting_rules["punctuation"]["ensure_period"]:
            if not text.endswith(('.', '!', '?')):
                text += '.'
        
        # 통화 포맷팅
        currency_rule = self.formatting_rules["currency_format"]
        text = re.sub(currency_rule["pattern"], currency_rule["replacement"], text)
        
        # 수량 포맷팅
        quantity_rule = self.formatting_rules["quantity_format"]
        text = re.sub(quantity_rule["pattern"], quantity_rule["replacement"], text)
        
        return text, text != original_text
    
    def _apply_type_specific_formatting(self, text: str, response_type: ResponseType) -> tuple[str, bool]:
        """응답 타입별 특수 포맷팅"""
        original_text = text
        
        if response_type == ResponseType.GREETING:
            # 인사말 특수 포맷팅
            text = self._format_greeting(text)
        elif response_type == ResponseType.ORDER_CONFIRMATION:
            # 주문 확인 특수 포맷팅
            text = self._format_order_confirmation(text)
        elif response_type == ResponseType.PAYMENT_REQUEST:
            # 결제 요청 특수 포맷팅
            text = self._format_payment_request(text)
        elif response_type == ResponseType.ERROR:
            # 오류 메시지 특수 포맷팅
            text = self._format_error_message(text)
        
        return text, text != original_text
    
    def _format_greeting(self, text: str) -> str:
        """인사말 포맷팅"""
        # 정중한 표현 확인
        if not any(word in text for word in ['안녕하세요', '환영합니다', '감사합니다']):
            text = "안녕하세요! " + text
        return text
    
    def _format_order_confirmation(self, text: str) -> str:
        """주문 확인 포맷팅"""
        # 확인 표현 강화
        if '추가되었습니다' in text or '취소되었습니다' in text:
            # 이미 적절한 표현이 있음
            pass
        return text
    
    def _format_payment_request(self, text: str) -> str:
        """결제 요청 포맷팅"""
        # 정중한 결제 요청 표현
        if '결제' in text and '?' not in text:
            text = text.rstrip('.') + '?'
        return text
    
    def _format_error_message(self, text: str) -> str:
        """오류 메시지 포맷팅"""
        # 사과 표현 확인
        if not any(word in text for word in ['죄송합니다', '미안합니다', '실례합니다']):
            text = "죄송합니다. " + text
        return text
    
    def format_currency(self, amount: int) -> str:
        """통화 포맷팅"""
        return f"{amount:,}원"
    
    def format_quantity(self, quantity: int, unit: str = "개") -> str:
        """수량 포맷팅"""
        return f"{quantity}{unit}"
    
    def format_menu_list(self, menu_items: list) -> str:
        """메뉴 목록 포맷팅"""
        if not menu_items:
            return "주문 내역이 없습니다"
        
        formatted_items = []
        for item in menu_items:
            if hasattr(item, 'name') and hasattr(item, 'quantity'):
                formatted_items.append(f"{item.name} {item.quantity}개")
            else:
                formatted_items.append(str(item))
        
        if len(formatted_items) == 1:
            return formatted_items[0]
        elif len(formatted_items) == 2:
            return f"{formatted_items[0]}와 {formatted_items[1]}"
        else:
            return ", ".join(formatted_items[:-1]) + f", 그리고 {formatted_items[-1]}"