"""
의도 파악 모듈
OpenAI GPT-4o API와 Tool calling을 활용한 사용자 의도 파악
"""

import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI

from ..models.conversation_models import Intent, IntentType, Modification, ConversationContext
from ..models.order_models import MenuItem
from ..models.error_models import IntentError, IntentErrorType


logger = logging.getLogger(__name__)


class IntentRecognizer:
    """
    LLM 기반 의도 파악 시스템
    OpenAI GPT-4o API와 Tool calling을 활용하여 사용자의 음성 입력에서 의도를 파악합니다.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        IntentRecognizer 초기화
        
        Args:
            api_key: OpenAI API 키 (None인 경우 설정 파일에서 로드)
            model: 사용할 모델명
        """
        # API 키 설정 - 환경 변수에서만 로드
        if api_key:
            self.api_key = api_key
        else:
            # 환경 변수에서 API 키 로드
            import os
            self.api_key = os.getenv('OPENAI_API_KEY')
            
            # API 키가 없거나 기본값이면 오류
            if not self.api_key or self.api_key in ["your_openai_api_key_here", ""]:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다. .env 파일에서 OPENAI_API_KEY를 설정하세요.")
        
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Tool calling 설정
        self.intent_tools = self._setup_intent_tools()
        
        logger.info(f"IntentRecognizer 초기화 완료 - 모델: {self.model}")
    
    def _setup_intent_tools(self) -> List[Dict[str, Any]]:
        """
        Tool calling을 위한 도구 정의
        
        Returns:
            도구 정의 리스트
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "recognize_order_intent",
                    "description": "주문 의도를 파악하고 메뉴 아이템을 추출합니다. 사용자가 여러 메뉴를 주문하는 경우 반드시 모든 메뉴를 배열에 포함하세요. '이랑', '하고', '그리고', ',', '추가로' 등의 연결어가 있으면 여러 메뉴로 인식하세요. 같은 메뉴라도 단품/세트가 다르면 별도 아이템으로 처리하세요.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "menu_items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "정확한 메뉴 이름 (예: 빅맥, 상하이버거)"},
                                        "category": {"type": "string", "description": "메뉴 카테고리 (단품, 세트, 라지세트)"},
                                        "quantity": {"type": "integer", "description": "수량", "minimum": 1},
                                        "options": {
                                            "type": "object",
                                            "description": "옵션 (음료 변경 등)",
                                            "additionalProperties": {"type": "string"}
                                        }
                                    },
                                    "required": ["name", "category", "quantity"]
                                },
                                "description": "주문할 메뉴 아이템들의 배열. 여러 메뉴가 언급된 경우 모두 포함하세요."
                            },
                            "confidence": {"type": "number", "description": "의도 파악 신뢰도 (0.0-1.0)", "minimum": 0.0, "maximum": 1.0}
                        },
                        "required": ["menu_items", "confidence"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                                    "name": "recognize_modify_intent",
                "description": "주문 변경 의도를 파악합니다. '단품으로 바꿔줘', '세트로 바꿔줘' 등의 옵션 변경 시 new_options는 반드시 포함되어야 합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "modifications": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "item_name": {"type": "string", "description": "변경할 아이템명. 명시되지 않으면 빈 문자열 사용"},
                                        "action": {
                                            "type": "string", 
                                            "enum": ["add", "remove", "change_quantity", "change_option"],
                                            "description": "변경 액션"
                                        },
                                        "new_quantity": {"type": "integer", "description": "새로운 수량"},
                                        "new_options": {
                                            "type": "object",
                                            "description": "새로운 옵션. change_option 액션 시 REQUIRED! '단품으로'->{\"type\":\"단품\"}, '세트로'->{\"type\":\"세트\"}, '라지세트로'->{\"type\":\"라지세트\"}",
                                            "additionalProperties": {"type": "string"}
                                        }
                                    },
                                    "required": ["item_name", "action"]
                                }
                            },
                            "confidence": {"type": "number", "description": "의도 파악 신뢰도 (0.0-1.0)"}
                        },
                        "required": ["modifications", "confidence"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                                    "name": "recognize_cancel_intent",
                "description": "주문 취소/삭제 의도를 파악합니다. '아니요', '취소' 등 간단한 부정 응답도 취소 의도로 처리하세요.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cancel_items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "취소할 아이템명들. 명시되지 않으면 빈 배열 사용 (전체 주문 취소 의미)"
                            },
                            "confidence": {"type": "number", "description": "의도 파악 신뢰도 (0.0-1.0)"}
                        },
                        "required": ["cancel_items", "confidence"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                                    "name": "recognize_payment_intent", 
                "description": "결제 의도를 파악합니다. '네', '예' 등 간단한 긍정 응답도 결제 진행 의도로 처리하세요.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payment_method": {
                                "type": "string",
                                "enum": ["card", "cash", "mobile"],
                                "description": "결제 방법"
                            },
                            "confidence": {"type": "number", "description": "의도 파악 신뢰도 (0.0-1.0)"}
                        },
                        "required": ["confidence"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recognize_inquiry_intent",
                    "description": "문의 의도를 파악합니다. 메뉴 문의, 주문 상태 확인, 가격 문의, 일반적인 질문 등을 포함합니다.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "inquiry_text": {
                                "type": "string", 
                                "description": "사용자의 실제 입력 텍스트를 그대로 사용하세요. 절대 해석하거나 변경하지 마세요."
                            },
                            "confidence": {
                                "type": "number", 
                                "description": "의도 파악 신뢰도 (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["inquiry_text", "confidence"]
                    }
                }
            }
        ]
    
    def _build_system_message(self, context: Optional[ConversationContext] = None) -> str:
        """
        시스템 메시지 구성
        
        Args:
            context: 대화 컨텍스트
            
        Returns:
            시스템 메시지
        """
        # 메뉴 정보 가져오기
        menu_info = self._get_menu_info_for_intent()
        
        base_message = """당신은 식당 음성 키오스크의 의도 파악 시스템입니다.

🚨 절대 규칙: 무조건 tool calling 수행!
- 음성인식 오류가 있어도 반드시 적절한 의도로 해석하여 tool을 호출하세요
- 이상한 단어 = 유사한 실제 단어로 자동 변환
- "본품" = "단품", "휴지" = "취소", "베그맥" = "빅맥"
- UNKNOWN intent 절대 금지! 항상 가장 유사한 의도로 tool calling하세요

💳 결제 상황 절대 규칙:
- "네", "예", "확인", "좋아요", "맞아요", "응", "ok" = 무조건 PAYMENT 의도
- "아니요", "안해요", "취소", "싫어요", "no" = 무조건 CANCEL 의도  
- 간단한 한 글자/단어 응답은 절대 INQUIRY 아님!
- 결제 문맥에서 INQUIRY intent 사용 절대 금지!

사용자의 음성 입력을 분석하여 다음 중 하나의 의도를 파악해야 합니다:

1. ORDER (주문): 새로운 메뉴를 주문하는 경우
2. MODIFY (변경): 기존 주문을 변경하는 경우  
3. CANCEL (취소): 주문을 취소/삭제하는 경우
4. PAYMENT (결제): 결제를 진행하려는 경우
5. INQUIRY (문의): 메뉴나 서비스에 대해 문의하는 경우

각 의도에 맞는 도구를 사용하여 구조화된 정보를 추출하세요.
신뢰도는 의도 파악의 확실성을 0.0-1.0 사이의 값으로 표현하세요.

중요 사항:
- 옵션 변경 요청(단품/세트/라지세트)은 MODIFY 의도로 처리
- 아이템명이 없으면 item_name에 빈 문자열("") 사용  
- change_option 액션 시 new_options 필드는 필수
- 발음 유사도를 고려하여 가장 적절한 의도 선택

현재 사용 가능한 메뉴:
""" + menu_info + """

메뉴 카테고리: 단품, 세트, 라지세트
- 같은 메뉴라도 카테고리가 다르면 별도 아이템으로 처리
- 여러 메뉴 언급 시 모두 배열에 포함  
- 연결어("이랑", "하고" 등) 인식하여 다중 메뉴 처리
"""
        
        if context and context.current_order:
            order_summary = []
            for item in context.current_order.items:
                if item.options:
                    options_parts = []
                    for k, v in item.options.items():
                        options_parts.append(k + ": " + str(v))
                    options_str = ", ".join(options_parts)
                else:
                    options_str = "옵션 없음"
                
                item_line = "- " + str(item.name) + " (" + options_str + ") x" + str(item.quantity)
                order_summary.append(item_line)
            
            base_message += "\n\n현재 주문 상태:\n" + "\n".join(order_summary)
            base_message += "\n총 " + str(len(context.current_order.items)) + "개 아이템, 총액: " + str(context.current_order.total_amount) + "원"
            
            # 대화 히스토리에서 결제 상황 확인
            if context and context.current_order and context.current_order.order_id:
                recent_messages = context.get_messages_by_order_id(context.current_order.order_id, 3)
                payment_context_found = False
                for msg in recent_messages:
                    if msg.get("role") == "assistant" and any(keyword in msg.get("content", "").lower() 
                                                            for keyword in ["결제", "진행하시겠", "계산"]):
                        payment_context_found = True
                        break
                
                if payment_context_found:
                    base_message += "\n\n🚨 CRITICAL: 결제 상황 감지!"
                    base_message += "\n- 현재 결제 확인을 기다리는 중입니다"
                    base_message += "\n- '네', '예', '확인', '좋아요' → recognize_payment_intent 호출"
                    base_message += "\n- '아니요', '취소', '안해요' → recognize_cancel_intent 호출"  
                    base_message += "\n- INQUIRY intent 절대 금지! 반드시 PAYMENT 또는 CANCEL로 처리!"
        
        # 현재 주문 ID의 대화 히스토리만 포함
        if context and context.current_order and context.current_order.order_id:
            order_messages = context.get_messages_by_order_id(context.current_order.order_id, 5)
            if order_messages:
                history_parts = []
                for msg in order_messages:
                    history_parts.append(str(msg['role']) + ": " + str(msg['content']))
                history_text = "\n".join(history_parts)
                base_message += "\n\n현재 주문(" + str(context.current_order.order_id) + ")의 대화 기록:\n" + history_text
        
        return base_message
    
    def _build_messages(self, text: str, context: Optional[ConversationContext] = None) -> List[Dict[str, str]]:
        """
        API 호출을 위한 메시지 구성
        
        Args:
            text: 사용자 입력 텍스트
            context: 대화 컨텍스트
            
        Returns:
            메시지 리스트
        """
        messages = [
            {"role": "system", "content": self._build_system_message(context)},
            {"role": "user", "content": text}
        ]
        
        return messages
    
    def recognize_intent(self, text: str, context: Optional[ConversationContext] = None) -> Intent:
        """
        사용자 입력에서 의도를 파악합니다
        
        Args:
            text: 사용자 입력 텍스트
            context: 대화 컨텍스트
            
        Returns:
            파악된 의도
            
        Raises:
            IntentError: 의도 파악 실패 시
        """
        try:
            logger.info(f"의도 파악 시작: {text}")
            print(f"🔍 [DEBUG] Intent 인식 시작 - 입력 텍스트: '{text}'")
            
            # OpenAI API 호출
            messages = self._build_messages(text, context)
            print(f"🔍 [DEBUG] 생성된 메시지 수: {len(messages)}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.intent_tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1000
            )
            
            print(f"🔍 [DEBUG] OpenAI 응답 받음")
            print(f"🔍 [DEBUG] 툴 호출 개수: {len(response.choices[0].message.tool_calls or [])}")
            
            # Tool calling 결과 파싱
            intent = self._parse_intent_from_response(response, text)
            
            print(f"🔍 [DEBUG] 파싱된 Intent: type={intent.type}, modifications={intent.modifications}")
            logger.info(f"의도 파악 완료: {intent.type.value} (신뢰도: {intent.confidence})")
            return intent
            
        except Exception as e:
            logger.error(f"의도 파악 실패: {str(e)}")
            raise IntentError(
                error_type=IntentErrorType.RECOGNITION_FAILED,
                message=f"의도 파악에 실패했습니다: {str(e)}",
                raw_text=text
            )
    
    def _parse_intent_from_response(self, response, original_text: str) -> Intent:
        """
        OpenAI API 응답에서 의도를 파싱합니다
        
        Args:
            response: OpenAI API 응답
            original_text: 원본 텍스트
            
        Returns:
            파악된 의도
        """
        message = response.choices[0].message
        print(f"🔍 [DEBUG] 응답 메시지 파싱 시작")
        print(f"🔍 [DEBUG] tool_calls 존재: {bool(message.tool_calls)}")
        
        # Tool calling이 사용된 경우
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            print(f"🔍 [DEBUG] 호출된 함수: {function_name}")
            print(f"🔍 [DEBUG] 함수 인수: {arguments}")
            
            return self._create_intent_from_tool_call(function_name, arguments, original_text)
        
        # Tool calling이 사용되지 않은 경우 - 발음 유사도 고려하여 재시도 유도
        print(f"🔍 [DEBUG] Tool calling 없음 - UNKNOWN intent 반환")
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.7,  # 발음 유사도 처리 LLM이 적극 처리하도록 신뢰도 증가
            raw_text=original_text
        )
    
    def _create_intent_from_tool_call(self, function_name: str, arguments: Dict[str, Any], original_text: str) -> Intent:
        """
        Tool call 결과로부터 Intent 객체를 생성합니다
        
        Args:
            function_name: 호출된 함수명
            arguments: 함수 인자
            original_text: 원본 텍스트
            
        Returns:
            Intent 객체
        """
        confidence = arguments.get('confidence', 0.0)
        
        if function_name == "recognize_order_intent":
            menu_items = []
            for item_data in arguments.get('menu_items', []):
                menu_item = MenuItem(
                    name=item_data['name'],
                    category=item_data['category'],
                    quantity=item_data['quantity'],
                    price=0,  # 의도 파악 단계에서는 가격을 0으로 설정, 나중에 메뉴 관리에서 실제 가격 설정
                    options=item_data.get('options', {})
                )
                menu_items.append(menu_item)
            
            return Intent(
                type=IntentType.ORDER,
                confidence=confidence,
                menu_items=menu_items,
                raw_text=original_text
            )
        
        elif function_name == "recognize_modify_intent":
            print(f"🔍 [DEBUG] recognize_modify_intent 툴 호출됨")
            print(f"🔍 [DEBUG] arguments: {arguments}")
            
            modifications = []
            for i, mod_data in enumerate(arguments.get('modifications', [])):
                print(f"🔍 [DEBUG] modification {i}: {mod_data}")
                modification = Modification(
                    item_name=mod_data['item_name'],
                    action=mod_data['action'],
                    new_quantity=mod_data.get('new_quantity'),
                    new_options=mod_data.get('new_options')
                )
                print(f"🔍 [DEBUG] 생성된 modification: {modification}")
                modifications.append(modification)
            
            print(f"🔍 [DEBUG] 총 {len(modifications)}개 modification 생성됨")
            return Intent(
                type=IntentType.MODIFY,
                confidence=confidence,
                modifications=modifications,
                raw_text=original_text
            )
        
        elif function_name == "recognize_cancel_intent":
            return Intent(
                type=IntentType.CANCEL,
                confidence=confidence,
                cancel_items=arguments.get('cancel_items', []),
                raw_text=original_text
            )
        
        elif function_name == "recognize_payment_intent":
            return Intent(
                type=IntentType.PAYMENT,
                confidence=confidence,
                payment_method=arguments.get('payment_method'),
                raw_text=original_text
            )
        
        elif function_name == "recognize_inquiry_intent":
            return Intent(
                type=IntentType.INQUIRY,
                confidence=confidence,
                inquiry_text=arguments.get('inquiry_text'),
                raw_text=original_text
            )
        
        else:
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=original_text
            )
    
    def batch_recognize_intents(self, texts: List[str], context: Optional[ConversationContext] = None) -> List[Intent]:
        """
        여러 텍스트에 대해 일괄 의도 파악
        
        Args:
            texts: 텍스트 리스트
            context: 대화 컨텍스트
            
        Returns:
            의도 리스트
        """
        intents = []
        for text in texts:
            try:
                intent = self.recognize_intent(text, context)
                intents.append(intent)
            except IntentError as e:
                logger.warning(f"텍스트 '{text}'의 의도 파악 실패: {e}")
                # 실패한 경우 UNKNOWN 의도로 처리
                intents.append(Intent(
                    type=IntentType.UNKNOWN,
                    confidence=0.0,
                    raw_text=text
                ))
        
        return intents
    
    def get_intent_confidence_threshold(self, intent_type: IntentType) -> float:
        """
        의도 타입별 신뢰도 임계값 반환
        
        Args:
            intent_type: 의도 타입
            
        Returns:
            신뢰도 임계값
        """
        thresholds = {
            IntentType.ORDER: 0.7,
            IntentType.MODIFY: 0.8,
            IntentType.CANCEL: 0.9,
            IntentType.PAYMENT: 0.8,
            IntentType.INQUIRY: 0.6,
            IntentType.UNKNOWN: 0.0
        }
        
        return thresholds.get(intent_type, 0.7)
    
    def _get_menu_info_for_intent(self) -> str:
        """의도 파악을 위한 메뉴 정보 생성"""
        try:
            from ..config import config_manager
            menu_config = config_manager.load_menu_config()
            
            menu_lines = []
            
            # 카테고리별로 메뉴 정리
            for category in menu_config.categories:
                category_items = []
                for item_name, item_config in menu_config.menu_items.items():
                    if item_config.category == category:
                        price_formatted = "{:,}".format(item_config.price)
                        category_items.append(str(item_name) + " (" + price_formatted + "원)")
                
                if category_items:
                    menu_lines.append("[" + str(category) + "]: " + ", ".join(category_items))
            
            return "\n".join(menu_lines)
            
        except Exception as e:
            return "메뉴 정보를 불러올 수 없습니다: " + str(e)
    
    def is_intent_reliable(self, intent: Intent) -> bool:
        """
        의도의 신뢰도가 충분한지 확인
        
        Args:
            intent: 의도 객체
            
        Returns:
            신뢰도 충분 여부
        """
        threshold = self.get_intent_confidence_threshold(intent.type)
        return intent.confidence >= threshold