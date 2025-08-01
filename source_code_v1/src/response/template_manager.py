"""
응답 템플릿 관리자
"""

from typing import Dict, List, Optional
import json
import os
from ..models import ResponseTemplate, ResponseType


class TemplateManager:
    """응답 템플릿 관리 클래스"""
    
    def __init__(self, template_config_path: Optional[str] = None):
        """
        템플릿 관리자 초기화
        
        Args:
            template_config_path: 템플릿 설정 파일 경로
        """
        self.templates: Dict[str, ResponseTemplate] = {}
        self.default_templates = self._get_default_templates()
        
        if template_config_path and os.path.exists(template_config_path):
            self._load_templates_from_file(template_config_path)
        else:
            self._load_default_templates()
    
    def _get_default_templates(self) -> Dict[str, Dict]:
        """기본 템플릿 정의"""
        return {
            "greeting": {
                "template_text": "안녕하세요! 음성 주문 키오스크입니다. 주문하실 메뉴를 말씀해 주세요.",
                "variables": {},
                "response_type": "greeting"
            },
            "order_added": {
                "template_text": "{menu_name} {quantity}개가 주문에 추가되었습니다. 현재 총 {total_amount}원입니다.",
                "variables": {"menu_name": "str", "quantity": "int", "total_amount": "int"},
                "response_type": "order_confirmation"
            },
            "order_summary": {
                "template_text": "현재 주문 내역입니다. {order_items}. 총 {total_amount}원입니다. 추가 주문이나 결제를 원하시면 말씀해 주세요.",
                "variables": {"order_items": "str", "total_amount": "int"},
                "response_type": "order_summary"
            },
            "payment_request": {
                "template_text": "총 {total_amount}원입니다. 결제를 진행하시겠습니까?",
                "variables": {"total_amount": "int"},
                "response_type": "payment_request"
            },
            "order_cancelled": {
                "template_text": "{menu_name}이(가) 주문에서 취소되었습니다. 현재 총 {total_amount}원입니다.",
                "variables": {"menu_name": "str", "total_amount": "int"},
                "response_type": "order_confirmation"
            },
            "clarification_needed": {
                "template_text": "죄송합니다. {clarification_reason} 다시 말씀해 주시겠어요?",
                "variables": {"clarification_reason": "str"},
                "response_type": "clarification"
            },
            "error_general": {
                "template_text": "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
                "variables": {},
                "response_type": "error"
            },
            "order_completion": {
                "template_text": "주문이 완료되었습니다. 결제 금액은 {total_amount}원입니다. 감사합니다!",
                "variables": {"total_amount": "int"},
                "response_type": "completion"
            },
            "menu_not_found": {
                "template_text": "죄송합니다. '{menu_name}' 메뉴를 찾을 수 없습니다. 다른 메뉴를 선택해 주세요.",
                "variables": {"menu_name": "str"},
                "response_type": "error"
            },
            "quantity_confirmation": {
                "template_text": "{menu_name}을(를) {quantity}개 주문하시는 것이 맞나요?",
                "variables": {"menu_name": "str", "quantity": "int"},
                "response_type": "clarification"
            }
        }
    
    def _load_default_templates(self):
        """기본 템플릿 로드"""
        for template_id, template_data in self.default_templates.items():
            self.templates[template_id] = ResponseTemplate(
                template_id=template_id,
                template_text=template_data["template_text"],
                variables=template_data["variables"],
                response_type=ResponseType(template_data["response_type"])
            )
    
    def _load_templates_from_file(self, file_path: str):
        """파일에서 템플릿 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            for template_id, template_info in template_data.items():
                self.templates[template_id] = ResponseTemplate(
                    template_id=template_id,
                    template_text=template_info["template_text"],
                    variables=template_info.get("variables", {}),
                    response_type=ResponseType(template_info["response_type"])
                )
        except Exception as e:
            print(f"템플릿 파일 로드 실패: {e}")
            self._load_default_templates()
    
    def get_template(self, template_id: str) -> Optional[ResponseTemplate]:
        """템플릿 조회"""
        return self.templates.get(template_id)
    
    def get_templates_by_type(self, response_type: ResponseType) -> List[ResponseTemplate]:
        """응답 타입별 템플릿 조회"""
        return [
            template for template in self.templates.values()
            if template.response_type == response_type
        ]
    
    def add_template(self, template: ResponseTemplate):
        """템플릿 추가"""
        self.templates[template.template_id] = template
    
    def remove_template(self, template_id: str) -> bool:
        """템플릿 제거"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    def list_templates(self) -> List[str]:
        """모든 템플릿 ID 목록 반환"""
        return list(self.templates.keys())