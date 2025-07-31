#!/usr/bin/env python3
"""
의도 파악 시스템 통합 테스트
실제 OpenAI API를 사용하지 않고 모킹을 통해 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
import json

from src.conversation.intent import IntentRecognizer
from src.models.conversation_models import IntentType, ConversationContext


def test_intent_recognition_integration():
    """의도 파악 통합 테스트"""
    
    # Mock OpenAI 클라이언트 설정
    with patch('src.conversation.intent.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # Mock 설정 로드
        with patch('src.conversation.intent.load_config') as mock_config:
            mock_config.return_value = {
                'openai': {
                    'api_key': 'test_api_key',
                    'model': 'gpt-4o'
                }
            }
            
            # IntentRecognizer 초기화
            recognizer = IntentRecognizer(api_key="test_key")
            
            # 테스트 케이스들
            test_cases = [
                {
                    'input': '빅맥 세트 2개 주문하고 싶어요',
                    'expected_type': IntentType.ORDER,
                    'mock_response': {
                        'function_name': 'recognize_order_intent',
                        'arguments': {
                            'menu_items': [
                                {
                                    'name': '빅맥',
                                    'category': '세트',
                                    'quantity': 2,
                                    'options': {'drink': '콜라'}
                                }
                            ],
                            'confidence': 0.9
                        }
                    }
                },
                {
                    'input': '빅맥을 1개로 변경해주세요',
                    'expected_type': IntentType.MODIFY,
                    'mock_response': {
                        'function_name': 'recognize_modify_intent',
                        'arguments': {
                            'modifications': [
                                {
                                    'item_name': '빅맥',
                                    'action': 'change_quantity',
                                    'new_quantity': 1
                                }
                            ],
                            'confidence': 0.85
                        }
                    }
                },
                {
                    'input': '감자튀김 취소해주세요',
                    'expected_type': IntentType.CANCEL,
                    'mock_response': {
                        'function_name': 'recognize_cancel_intent',
                        'arguments': {
                            'cancel_items': ['감자튀김'],
                            'confidence': 0.95
                        }
                    }
                },
                {
                    'input': '카드로 결제할게요',
                    'expected_type': IntentType.PAYMENT,
                    'mock_response': {
                        'function_name': 'recognize_payment_intent',
                        'arguments': {
                            'payment_method': 'card',
                            'confidence': 0.9
                        }
                    }
                },
                {
                    'input': '빅맥의 칼로리가 얼마나 되나요?',
                    'expected_type': IntentType.INQUIRY,
                    'mock_response': {
                        'function_name': 'recognize_inquiry_intent',
                        'arguments': {
                            'inquiry_text': '빅맥의 칼로리가 얼마나 되나요?',
                            'confidence': 0.8
                        }
                    }
                }
            ]
            
            print("=== 의도 파악 시스템 통합 테스트 ===\n")
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"테스트 {i}: {test_case['input']}")
                
                # Mock API 응답 설정
                mock_response = Mock()
                mock_message = Mock()
                mock_tool_call = Mock()
                
                mock_tool_call.function.name = test_case['mock_response']['function_name']
                mock_tool_call.function.arguments = json.dumps(test_case['mock_response']['arguments'])
                
                mock_message.tool_calls = [mock_tool_call]
                mock_response.choices = [Mock(message=mock_message)]
                mock_client.chat.completions.create.return_value = mock_response
                
                # 의도 파악 실행
                context = ConversationContext(session_id=f"test_session_{i}")
                intent = recognizer.recognize_intent(test_case['input'], context)
                
                # 결과 검증
                assert intent.type == test_case['expected_type'], f"예상 의도: {test_case['expected_type']}, 실제: {intent.type}"
                assert intent.confidence > 0.7, f"신뢰도가 너무 낮습니다: {intent.confidence}"
                assert recognizer.is_intent_reliable(intent), "의도 신뢰도가 임계값 이하입니다"
                
                print(f"  의도: {intent.type.value}")
                print(f"  신뢰도: {intent.confidence}")
                print(f"  신뢰할 수 있음: {recognizer.is_intent_reliable(intent)}")
                
                # 의도별 세부 정보 출력
                if intent.type == IntentType.ORDER and intent.menu_items:
                    for item in intent.menu_items:
                        print(f"  주문 아이템: {item.name} ({item.category}) x{item.quantity}")
                        if item.options:
                            print(f"    옵션: {item.options}")
                
                elif intent.type == IntentType.MODIFY and intent.modifications:
                    for mod in intent.modifications:
                        print(f"  변경: {mod.item_name} - {mod.action}")
                        if mod.new_quantity:
                            print(f"    새 수량: {mod.new_quantity}")
                
                elif intent.type == IntentType.CANCEL and intent.cancel_items:
                    print(f"  취소 아이템: {', '.join(intent.cancel_items)}")
                
                elif intent.type == IntentType.PAYMENT and intent.payment_method:
                    print(f"  결제 방법: {intent.payment_method}")
                
                elif intent.type == IntentType.INQUIRY and intent.inquiry_text:
                    print(f"  문의 내용: {intent.inquiry_text}")
                
                print()
            
            print("모든 테스트가 성공적으로 완료되었습니다!")


if __name__ == "__main__":
    test_intent_recognition_integration()