#!/usr/bin/env python3
"""
대화 관리 시스템 통합 테스트
실제 시나리오를 통해 전체 대화 플로우를 테스트합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
import json

from src.conversation.dialogue import DialogueManager
from src.conversation.intent import IntentRecognizer
from src.order.order import OrderManager
from src.order.menu import Menu
from src.models.conversation_models import Intent, IntentType, Modification
from src.models.order_models import MenuItem


def create_test_menu():
    """테스트용 메뉴 생성"""
    menu_config = {
        "restaurant_type": "패스트푸드",
        "categories": ["버거", "세트", "사이드", "음료"],
        "menu_items": {
            "빅맥": {
                "name": "빅맥",
                "category": "버거",
                "price": 5900,
                "is_available": True,
                "available_options": ["콜라", "사이다", "오렌지주스"]
            },
            "빅맥세트": {
                "name": "빅맥세트",
                "category": "세트",
                "price": 7900,
                "is_available": True,
                "available_options": ["콜라", "사이다", "오렌지주스", "감자튀김", "치킨너겟"]
            },
            "감자튀김": {
                "name": "감자튀김",
                "category": "사이드",
                "price": 2400,
                "is_available": True,
                "available_options": []
            },
            "콜라": {
                "name": "콜라",
                "category": "음료",
                "price": 1900,
                "is_available": True,
                "available_options": []
            }
        }
    }
    return Menu.from_dict(menu_config)


def test_dialogue_flow():
    """대화 플로우 통합 테스트"""
    
    # Mock OpenAI 클라이언트 설정
    with patch('src.conversation.dialogue.load_config') as mock_config:
        mock_config.return_value = {
            'openai': {
                'api_key': 'test_api_key'
            }
        }
        
        # 테스트 컴포넌트 초기화
        menu = create_test_menu()
        order_manager = OrderManager(menu)
        
        # Mock OpenAI 클라이언트
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "네, 도움을 드리겠습니다."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        dialogue_manager = DialogueManager(order_manager, mock_openai_client)
        
        print("=== 대화 관리 시스템 통합 테스트 ===\n")
        
        # 세션 시작
        session_id = dialogue_manager.create_session()
        print(f"세션 시작: {session_id}\n")
        
        # 테스트 시나리오
        scenarios = [
            {
                'step': 1,
                'description': '빅맥세트 2개 주문',
                'intent': Intent(
                    type=IntentType.ORDER,
                    confidence=0.9,
                    menu_items=[MenuItem(name="빅맥세트", category="세트", quantity=2, price=7900)],
                    raw_text="빅맥세트 2개 주문할게요"
                )
            },
            {
                'step': 2,
                'description': '감자튀김 1개 추가 주문',
                'intent': Intent(
                    type=IntentType.ORDER,
                    confidence=0.85,
                    menu_items=[MenuItem(name="감자튀김", category="사이드", quantity=1, price=2400)],
                    raw_text="감자튀김도 1개 추가해주세요"
                )
            },
            {
                'step': 3,
                'description': '현재 주문 상태 문의',
                'intent': Intent(
                    type=IntentType.INQUIRY,
                    confidence=0.8,
                    inquiry_text="현재 주문 내역이 어떻게 되나요?",
                    raw_text="현재 주문 내역이 어떻게 되나요?"
                )
            },
            {
                'step': 4,
                'description': '빅맥세트 수량을 1개로 변경',
                'intent': Intent(
                    type=IntentType.MODIFY,
                    confidence=0.9,
                    modifications=[Modification(
                        item_name='빅맥세트',
                        action='change_quantity',
                        new_quantity=1
                    )],
                    raw_text="빅맥세트를 1개로 변경해주세요"
                )
            },
            {
                'step': 5,
                'description': '결제 요청',
                'intent': Intent(
                    type=IntentType.PAYMENT,
                    confidence=0.95,
                    payment_method="카드",
                    raw_text="카드로 결제할게요"
                )
            }
        ]
        
        # 시나리오 실행
        for scenario in scenarios:
            print(f"--- 단계 {scenario['step']}: {scenario['description']} ---")
            print(f"사용자 입력: \"{scenario['intent'].raw_text}\"")
            
            # 대화 처리
            response = dialogue_manager.process_dialogue(session_id, scenario['intent'])
            
            print(f"시스템 응답: {response.text}")
            print(f"확인 필요: {response.requires_confirmation}")
            print(f"제안 액션: {response.suggested_actions}")
            
            # 주문 상태 출력
            current_order = order_manager.get_current_order()
            if current_order:
                print(f"현재 주문 아이템 수: {len(current_order.items)}")
                print(f"총 금액: {current_order.total_amount:,}원")
            else:
                print("현재 주문 없음")
            
            print()
        
        # 결제 확인
        print("--- 결제 확인 ---")
        confirm_response = dialogue_manager.confirm_action(session_id, "confirm_payment")
        print(f"확인 응답: {confirm_response.text}")
        print(f"제안 액션: {confirm_response.suggested_actions}")
        
        # 최종 주문 상태
        final_order = order_manager.get_current_order()
        if final_order:
            print(f"최종 주문 상태: {final_order.status.value}")
        else:
            print("주문 완료됨")
        
        print()
        
        # 세션 통계
        stats = dialogue_manager.get_session_stats()
        print(f"활성 세션 수: {stats['active_sessions']}")
        
        # 대화 기록 확인
        context = dialogue_manager.get_context(session_id)
        if context:
            print(f"대화 기록 수: {len(context.conversation_history)}")
            print("최근 대화:")
            for msg in context.get_recent_messages(3):
                print(f"  {msg['role']}: {msg['content'][:50]}...")
        
        # 세션 종료
        dialogue_manager.end_session(session_id)
        print(f"\n세션 종료: {session_id}")
        
        print("\n모든 대화 플로우 테스트가 성공적으로 완료되었습니다!")


def test_error_scenarios():
    """오류 시나리오 테스트"""
    
    with patch('src.conversation.dialogue.load_config') as mock_config:
        mock_config.return_value = {
            'openai': {
                'api_key': 'test_api_key'
            }
        }
        
        menu = create_test_menu()
        order_manager = OrderManager(menu)
        
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "죄송합니다. 다시 시도해 주세요."
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        dialogue_manager = DialogueManager(order_manager, mock_openai_client)
        
        print("\n=== 오류 시나리오 테스트 ===\n")
        
        session_id = dialogue_manager.create_session()
        
        # 오류 시나리오들
        error_scenarios = [
            {
                'description': '존재하지 않는 메뉴 주문',
                'intent': Intent(
                    type=IntentType.ORDER,
                    confidence=0.8,
                    menu_items=[MenuItem(name="존재하지않는메뉴", category="버거", quantity=1, price=0)],
                    raw_text="존재하지않는메뉴 주문할게요"
                )
            },
            {
                'description': '주문 없이 결제 시도',
                'intent': Intent(
                    type=IntentType.PAYMENT,
                    confidence=0.9,
                    raw_text="결제할게요"
                )
            },
            {
                'description': '낮은 신뢰도 의도',
                'intent': Intent(
                    type=IntentType.UNKNOWN,
                    confidence=0.3,
                    raw_text="음... 뭔가..."
                )
            }
        ]
        
        for i, scenario in enumerate(error_scenarios, 1):
            print(f"오류 시나리오 {i}: {scenario['description']}")
            print(f"사용자 입력: \"{scenario['intent'].raw_text}\"")
            
            response = dialogue_manager.process_dialogue(session_id, scenario['intent'])
            
            print(f"시스템 응답: {response.text}")
            print(f"제안 액션: {response.suggested_actions}")
            print()
        
        dialogue_manager.end_session(session_id)
        print("오류 시나리오 테스트 완료!")


if __name__ == "__main__":
    test_dialogue_flow()
    test_error_scenarios()