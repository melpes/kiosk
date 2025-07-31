#!/usr/bin/env python3
"""
오류 처리 시스템 데모

이 스크립트는 음성 키오스크 시스템의 오류 처리 기능을 시연합니다.
다양한 오류 상황을 시뮬레이션하고 ErrorHandler가 어떻게 처리하는지 보여줍니다.
"""

import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.error.handler import ErrorHandler, ErrorRecoveryManager
from src.models.error_models import (
    AudioError, AudioErrorType,
    RecognitionError, RecognitionErrorType,
    IntentError, IntentErrorType,
    OrderError, OrderErrorType,
    ValidationError, ConfigurationError
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_audio_errors():
    """음성 처리 오류 데모"""
    print("\n=== 음성 처리 오류 데모 ===")
    
    error_handler = ErrorHandler(max_retry_count=2)
    
    # 다양한 음성 오류 시뮬레이션
    audio_errors = [
        AudioError(AudioErrorType.LOW_QUALITY, "음성 품질이 낮습니다"),
        AudioError(AudioErrorType.NO_INPUT, "음성 입력이 감지되지 않았습니다"),
        AudioError(AudioErrorType.MULTIPLE_SPEAKERS, "여러 명이 동시에 말하고 있습니다"),
        AudioError(AudioErrorType.BACKGROUND_NOISE, "배경 소음이 심합니다"),
        AudioError(AudioErrorType.PROCESSING_FAILED, "음성 처리에 실패했습니다")
    ]
    
    for error in audio_errors:
        print(f"\n오류 발생: {error.error_type.value}")
        response = error_handler.handle_audio_error(error)
        print(f"사용자 메시지: {response.message}")
        print(f"권장 액션: {response.action.value}")
        print(f"복구 가능: {response.can_recover}")
        print(f"재시도 횟수: {response.retry_count}")

def demo_recognition_errors():
    """음성인식 오류 데모"""
    print("\n=== 음성인식 오류 데모 ===")
    
    error_handler = ErrorHandler(max_retry_count=2)
    
    recognition_errors = [
        RecognitionError(RecognitionErrorType.LOW_CONFIDENCE, "신뢰도가 낮습니다", confidence=0.3),
        RecognitionError(RecognitionErrorType.MODEL_NOT_LOADED, "모델이 로드되지 않았습니다"),
        RecognitionError(RecognitionErrorType.TIMEOUT, "처리 시간이 초과되었습니다"),
        RecognitionError(RecognitionErrorType.MODEL_ERROR, "모델에 오류가 발생했습니다")
    ]
    
    for error in recognition_errors:
        print(f"\n오류 발생: {error.error_type.value}")
        response = error_handler.handle_recognition_error(error)
        print(f"사용자 메시지: {response.message}")
        print(f"권장 액션: {response.action.value}")
        print(f"복구 가능: {response.can_recover}")
        if error.confidence:
            print(f"신뢰도: {error.confidence}")

def demo_intent_errors():
    """의도 파악 오류 데모"""
    print("\n=== 의도 파악 오류 데모 ===")
    
    error_handler = ErrorHandler(max_retry_count=2)
    
    intent_errors = [
        IntentError(IntentErrorType.AMBIGUOUS_INTENT, "의도가 모호합니다", raw_text="뭔가 주문하고 싶어요"),
        IntentError(IntentErrorType.UNKNOWN_INTENT, "알 수 없는 의도입니다", raw_text="시스템 종료해줘"),
        IntentError(IntentErrorType.LLM_API_ERROR, "LLM API 오류가 발생했습니다"),
        IntentError(IntentErrorType.CONTEXT_ERROR, "대화 맥락을 이해할 수 없습니다")
    ]
    
    for error in intent_errors:
        print(f"\n오류 발생: {error.error_type.value}")
        response = error_handler.handle_intent_error(error)
        print(f"사용자 메시지: {response.message}")
        print(f"권장 액션: {response.action.value}")
        print(f"복구 가능: {response.can_recover}")
        if response.suggested_alternatives:
            print(f"제안 대안: {', '.join(response.suggested_alternatives)}")
        if error.raw_text:
            print(f"원본 텍스트: {error.raw_text}")

def demo_order_errors():
    """주문 처리 오류 데모"""
    print("\n=== 주문 처리 오류 데모 ===")
    
    error_handler = ErrorHandler(max_retry_count=2)
    
    order_errors = [
        OrderError(OrderErrorType.ITEM_NOT_FOUND, "메뉴를 찾을 수 없습니다", item_name="비빔밥"),
        OrderError(OrderErrorType.ITEM_UNAVAILABLE, "메뉴가 품절되었습니다", item_name="치킨버거"),
        OrderError(OrderErrorType.INVALID_QUANTITY, "잘못된 수량입니다"),
        OrderError(OrderErrorType.NO_ACTIVE_ORDER, "활성 주문이 없습니다"),
        OrderError(OrderErrorType.PAYMENT_ERROR, "결제 처리 중 오류가 발생했습니다"),
        OrderError(OrderErrorType.SYSTEM_ERROR, "시스템 오류가 발생했습니다")
    ]
    
    for error in order_errors:
        print(f"\n오류 발생: {error.error_type.value}")
        response = error_handler.handle_order_error(error)
        print(f"사용자 메시지: {response.message}")
        print(f"권장 액션: {response.action.value}")
        print(f"복구 가능: {response.can_recover}")
        if error.item_name:
            print(f"관련 메뉴: {error.item_name}")

def demo_retry_mechanism():
    """재시도 메커니즘 데모"""
    print("\n=== 재시도 메커니즘 데모 ===")
    
    error_handler = ErrorHandler(max_retry_count=3)
    
    # 같은 오류를 여러 번 발생시켜 재시도 메커니즘 테스트
    error = AudioError(AudioErrorType.LOW_QUALITY, "음성 품질이 낮습니다")
    
    for i in range(5):  # 최대 재시도 횟수보다 많이 시도
        print(f"\n{i+1}번째 시도:")
        response = error_handler.handle_audio_error(error)
        print(f"사용자 메시지: {response.message}")
        print(f"권장 액션: {response.action.value}")
        print(f"복구 가능: {response.can_recover}")
        print(f"재시도 횟수: {response.retry_count}")
        
        if not response.can_recover:
            print("더 이상 복구할 수 없습니다. 직원을 호출합니다.")
            break

def demo_error_recovery():
    """오류 복구 데모"""
    print("\n=== 오류 복구 데모 ===")
    
    error_handler = ErrorHandler()
    recovery_manager = ErrorRecoveryManager(error_handler)
    
    # 다양한 복구 시나리오
    errors_and_responses = [
        AudioError(AudioErrorType.LOW_QUALITY, "음성 품질이 낮습니다"),
        RecognitionError(RecognitionErrorType.MODEL_NOT_LOADED, "모델이 로드되지 않았습니다"),
        IntentError(IntentErrorType.AMBIGUOUS_INTENT, "의도가 모호합니다"),
        OrderError(OrderErrorType.PAYMENT_ERROR, "결제 오류가 발생했습니다")
    ]
    
    for error in errors_and_responses:
        print(f"\n오류 발생: {error.error_type.value}")
        
        # ErrorHandler로 오류 처리
        if isinstance(error, AudioError):
            response = error_handler.handle_audio_error(error)
        elif isinstance(error, RecognitionError):
            response = error_handler.handle_recognition_error(error)
        elif isinstance(error, IntentError):
            response = error_handler.handle_intent_error(error)
        elif isinstance(error, OrderError):
            response = error_handler.handle_order_error(error)
        
        print(f"오류 응답: {response.message}")
        print(f"권장 액션: {response.action.value}")
        
        # ErrorRecoveryManager로 복구 시도
        recovery_success = recovery_manager.attempt_recovery(response)
        print(f"복구 시도 결과: {'성공' if recovery_success else '실패'}")

def demo_error_statistics():
    """오류 통계 데모"""
    print("\n=== 오류 통계 데모 ===")
    
    error_handler = ErrorHandler()
    
    # 여러 오류 발생시키기
    errors = [
        AudioError(AudioErrorType.LOW_QUALITY, "음성 품질 낮음"),
        AudioError(AudioErrorType.LOW_QUALITY, "음성 품질 낮음"),
        RecognitionError(RecognitionErrorType.LOW_CONFIDENCE, "낮은 신뢰도"),
        IntentError(IntentErrorType.UNKNOWN_INTENT, "알 수 없는 의도"),
        OrderError(OrderErrorType.ITEM_NOT_FOUND, "메뉴 없음", item_name="테스트메뉴")
    ]
    
    for error in errors:
        if isinstance(error, AudioError):
            error_handler.handle_audio_error(error)
        elif isinstance(error, RecognitionError):
            error_handler.handle_recognition_error(error)
        elif isinstance(error, IntentError):
            error_handler.handle_intent_error(error)
        elif isinstance(error, OrderError):
            error_handler.handle_order_error(error)
    
    # 통계 출력
    stats = error_handler.get_error_statistics()
    print(f"총 오류 수: {stats['total_errors']}")
    print("오류 타입별 카운트:")
    for error_key, count in stats['error_counts'].items():
        print(f"  {error_key}: {count}회")
    
    print(f"\n최근 오류 {len(stats['recent_errors'])}개:")
    for recent_error in stats['recent_errors']:
        print(f"  {recent_error['timestamp'].strftime('%H:%M:%S')} - "
              f"{recent_error['category']}.{recent_error['error_type']}")

def demo_validation_and_config_errors():
    """검증 및 설정 오류 데모"""
    print("\n=== 검증 및 설정 오류 데모 ===")
    
    error_handler = ErrorHandler()
    
    # 검증 오류
    validation_error = ValidationError(
        "수량은 1 이상이어야 합니다",
        details={"field": "quantity", "value": 0, "min_value": 1}
    )
    
    print("검증 오류 발생:")
    response = error_handler.handle_validation_error(validation_error)
    print(f"사용자 메시지: {response.message}")
    print(f"권장 액션: {response.action.value}")
    
    # 설정 오류
    config_error = ConfigurationError(
        "API 키가 설정되지 않았습니다",
        config_path="/.env",
        details={"missing_key": "OPENAI_API_KEY"}
    )
    
    print("\n설정 오류 발생:")
    response = error_handler.handle_configuration_error(config_error)
    print(f"사용자 메시지: {response.message}")
    print(f"권장 액션: {response.action.value}")
    print(f"복구 가능: {response.can_recover}")

def main():
    """메인 데모 함수"""
    print("🎤 음성 키오스크 오류 처리 시스템 데모")
    print("=" * 50)
    
    try:
        demo_audio_errors()
        demo_recognition_errors()
        demo_intent_errors()
        demo_order_errors()
        demo_retry_mechanism()
        demo_error_recovery()
        demo_error_statistics()
        demo_validation_and_config_errors()
        
        print("\n" + "=" * 50)
        print("✅ 모든 오류 처리 데모가 완료되었습니다!")
        
    except Exception as e:
        print(f"\n❌ 데모 실행 중 오류 발생: {str(e)}")
        logging.exception("Demo execution failed")

if __name__ == "__main__":
    main()