#!/usr/bin/env python3
"""
ResponseBuilder 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.response_builder import ResponseBuilder
from src.models.communication_models import ErrorCode, OrderData, UIAction
from src.models.conversation_models import DialogueResponse, Intent, IntentType
from src.models.order_models import Order, MenuItem, OrderStatus
from decimal import Decimal


def test_response_builder():
    """ResponseBuilder 기본 기능 테스트"""
    print("=== ResponseBuilder 테스트 시작 ===")
    
    # ResponseBuilder 초기화
    builder = ResponseBuilder()
    print("✓ ResponseBuilder 초기화 완료")
    
    # 1. 성공 응답 생성 테스트
    print("\n1. 성공 응답 생성 테스트")
    success_response = builder.build_success_response(
        message="주문이 성공적으로 추가되었습니다.",
        session_id="test_session_001",
        processing_time=1.5
    )
    
    print(f"  - 성공 여부: {success_response.success}")
    print(f"  - 메시지: {success_response.message}")
    print(f"  - TTS URL: {success_response.tts_audio_url}")
    print(f"  - 처리 시간: {success_response.processing_time}초")
    print(f"  - UI 액션 수: {len(success_response.ui_actions)}")
    
    # 2. 오류 응답 생성 테스트
    print("\n2. 오류 응답 생성 테스트")
    error_response = builder.build_error_response(
        error_code=ErrorCode.AUDIO_PROCESSING_ERROR,
        error_message="음성 파일을 처리할 수 없습니다.",
        recovery_actions=["다시 시도해 주세요", "음성을 더 명확하게 말씀해 주세요"],
        session_id="test_session_001",
        processing_time=0.5
    )
    
    print(f"  - 성공 여부: {error_response.success}")
    print(f"  - 메시지: {error_response.message}")
    print(f"  - 오류 코드: {error_response.error_info.error_code}")
    print(f"  - 복구 액션: {error_response.error_info.recovery_actions}")
    print(f"  - UI 액션 수: {len(error_response.ui_actions)}")
    
    # 3. DialogueResponse 변환 테스트
    print("\n3. DialogueResponse 변환 테스트")
    
    # 테스트용 주문 생성
    test_order = Order()
    test_item = MenuItem(
        name="빅맥",
        category="세트",
        quantity=1,
        price=Decimal("6500"),
        options={"type": "세트", "drink": "콜라"}
    )
    test_order.add_item(test_item)
    
    # DialogueResponse 생성
    dialogue_response = DialogueResponse(
        text="빅맥 세트 1개가 주문에 추가되었습니다. 추가로 주문하시겠어요?",
        order_state=test_order,
        requires_confirmation=False,
        suggested_actions=["continue_ordering", "show_menu"],
        metadata={"intent_type": "order"}
    )
    
    # DialogueResponse를 ServerResponse로 변환
    server_response = builder.build_response_from_dialogue(
        dialogue_response,
        session_id="test_session_002",
        processing_time=2.1
    )
    
    print(f"  - 성공 여부: {server_response.success}")
    print(f"  - 메시지: {server_response.message}")
    print(f"  - 주문 데이터 존재: {server_response.order_data is not None}")
    if server_response.order_data:
        print(f"  - 주문 아이템 수: {len(server_response.order_data.items)}")
        print(f"  - 총 금액: {server_response.order_data.total_amount}원")
    print(f"  - UI 액션 수: {len(server_response.ui_actions)}")
    for i, action in enumerate(server_response.ui_actions):
        print(f"    액션 {i+1}: {action.action_type}")
    
    # 4. JSON 직렬화 테스트
    print("\n4. JSON 직렬화 테스트")
    json_str = server_response.to_json()
    print(f"  - JSON 길이: {len(json_str)} 문자")
    print(f"  - JSON 미리보기: {json_str[:200]}...")
    
    # JSON 역직렬화 테스트
    from src.models.communication_models import ServerResponse
    restored_response = ServerResponse.from_json(json_str)
    print(f"  - 역직렬화 성공: {restored_response.success == server_response.success}")
    print(f"  - 메시지 일치: {restored_response.message == server_response.message}")
    
    # 5. TTS 파일 관리 테스트
    print("\n5. TTS 파일 관리 테스트")
    
    # TTS 파일 생성
    tts_url = builder._generate_tts_file("테스트 음성 메시지입니다.")
    if tts_url:
        print(f"  - TTS URL 생성: {tts_url}")
        
        # 파일 ID 추출
        file_id = tts_url.split('/')[-1]
        file_path = builder.get_tts_file_path(file_id)
        
        if file_path and os.path.exists(file_path):
            print(f"  - TTS 파일 존재 확인: {file_path}")
            file_size = os.path.getsize(file_path)
            print(f"  - 파일 크기: {file_size} 바이트")
        else:
            print("  - TTS 파일을 찾을 수 없음")
    else:
        print("  - TTS 파일 생성 실패")
    
    # 6. 파일 정리 테스트
    print("\n6. 파일 정리 테스트")
    cache_count_before = len(builder.tts_cache)
    print(f"  - 정리 전 캐시 파일 수: {cache_count_before}")
    
    builder.cleanup_expired_files()
    cache_count_after = len(builder.tts_cache)
    print(f"  - 정리 후 캐시 파일 수: {cache_count_after}")
    
    print("\n=== ResponseBuilder 테스트 완료 ===")


def test_ui_actions():
    """UI 액션 생성 테스트"""
    print("\n=== UI 액션 테스트 시작 ===")
    
    builder = ResponseBuilder()
    
    # 메뉴 옵션 테스트
    menu_options = builder._get_available_menu_options()
    print(f"사용 가능한 메뉴 옵션 수: {len(menu_options)}")
    
    if menu_options:
        for i, option in enumerate(menu_options[:3]):  # 처음 3개만 표시
            print(f"  메뉴 {i+1}: {option.display_text} - {option.price}원")
    
    # UI 액션 생성 테스트
    test_order_data = OrderData(
        order_id="test_order_001",
        items=[{
            'name': '빅맥',
            'category': '세트',
            'quantity': 1,
            'price': 6500,
            'options': {'type': '세트'}
        }],
        total_amount=6500,
        status='pending',
        requires_confirmation=False
    )
    
    # 결제 데이터 생성 테스트
    payment_data = builder._create_payment_data_from_order_data(test_order_data)
    print(f"\n결제 데이터:")
    print(f"  - 총 금액: {payment_data.total_amount}원")
    print(f"  - 세금: {payment_data.tax_amount}원")
    print(f"  - 결제 방법: {payment_data.payment_methods}")
    
    print("\n=== UI 액션 테스트 완료 ===")


if __name__ == "__main__":
    try:
        test_response_builder()
        test_ui_actions()
        print("\n모든 테스트가 성공적으로 완료되었습니다! ✓")
        
    except Exception as e:
        print(f"\n테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)