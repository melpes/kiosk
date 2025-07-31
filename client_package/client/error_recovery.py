"""
클라이언트 오류 복구 매니저
다양한 오류 상황에 대한 자동 복구 및 사용자 가이드 제공
"""

import time
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum

from .models.communication_models import ServerResponse, ErrorInfo, ErrorCode, UIAction
from .config_manager import ClientConfig
from utils.logger import get_logger


class RecoveryStrategy(Enum):
    """복구 전략"""
    IMMEDIATE_RETRY = "immediate_retry"
    DELAYED_RETRY = "delayed_retry"
    USER_INTERVENTION = "user_intervention"
    FALLBACK_MODE = "fallback_mode"
    ESCALATE = "escalate"


class RecoveryResult(Enum):
    """복구 결과"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    REQUIRES_USER_ACTION = "requires_user_action"
    ESCALATED = "escalated"


class ErrorRecoveryManager:
    """오류 복구 관리자"""
    
    def __init__(self, config: ClientConfig, voice_client=None):
        """
        복구 관리자 초기화
        
        Args:
            config: 클라이언트 설정
            voice_client: VoiceClient 인스턴스
        """
        self.config = config
        self.voice_client = voice_client
        self.logger = get_logger(f"{__name__}.ErrorRecoveryManager")
        
        # 복구 통계
        self.recovery_stats = {
            'total_attempts': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'user_interventions': 0,
            'escalations': 0,
            'error_patterns': {}
        }
        
        # 복구 전략 매핑
        self.recovery_strategies = {
            ErrorCode.NETWORK_ERROR.value: [
                RecoveryStrategy.DELAYED_RETRY,
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.ESCALATE
            ],
            ErrorCode.TIMEOUT_ERROR.value: [
                RecoveryStrategy.IMMEDIATE_RETRY,
                RecoveryStrategy.DELAYED_RETRY,
                RecoveryStrategy.USER_INTERVENTION
            ],
            ErrorCode.VALIDATION_ERROR.value: [
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.FALLBACK_MODE
            ],
            ErrorCode.SPEECH_RECOGNITION_ERROR.value: [
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.IMMEDIATE_RETRY,
                RecoveryStrategy.FALLBACK_MODE
            ],
            ErrorCode.INTENT_RECOGNITION_ERROR.value: [
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.FALLBACK_MODE
            ],
            ErrorCode.ORDER_PROCESSING_ERROR.value: [
                RecoveryStrategy.IMMEDIATE_RETRY,
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.FALLBACK_MODE
            ],
            ErrorCode.SERVER_ERROR.value: [
                RecoveryStrategy.DELAYED_RETRY,
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.ESCALATE
            ],
            ErrorCode.AUDIO_PROCESSING_ERROR.value: [
                RecoveryStrategy.USER_INTERVENTION,
                RecoveryStrategy.IMMEDIATE_RETRY
            ]
        }
        
        # 복구 콜백 함수들
        self.recovery_callbacks = {}
        
        # 오류 패턴 추적
        self.error_history = []
        self.max_history_size = 100
        
        self.logger.info("오류 복구 관리자 초기화 완료")
    
    def handle_error(self, 
                    response: ServerResponse, 
                    context: Dict[str, Any] = None,
                    retry_callback: Callable = None) -> Dict[str, Any]:
        """
        오류 처리 및 복구 시도
        
        Args:
            response: 오류 응답
            context: 오류 컨텍스트 정보
            retry_callback: 재시도 콜백 함수
            
        Returns:
            Dict[str, Any]: 복구 결과
        """
        if not response.error_info:
            return {'result': RecoveryResult.SUCCESS, 'message': '오류 정보가 없습니다'}
        
        error_info = response.error_info
        self.logger.info(f"오류 복구 시작: {error_info.error_code}")
        
        # 오류 기록
        self._record_error(error_info, context)
        
        # 복구 전략 결정
        strategies = self._determine_recovery_strategies(error_info, context)
        
        # 복구 시도
        recovery_result = self._execute_recovery_strategies(
            error_info, strategies, context, retry_callback
        )
        
        # 결과 기록
        self._record_recovery_result(error_info, recovery_result)
        
        return recovery_result
    
    def _determine_recovery_strategies(self, 
                                     error_info: ErrorInfo, 
                                     context: Dict[str, Any] = None) -> List[RecoveryStrategy]:
        """
        복구 전략 결정
        
        Args:
            error_info: 오류 정보
            context: 컨텍스트 정보
            
        Returns:
            List[RecoveryStrategy]: 복구 전략 목록
        """
        error_code = error_info.error_code
        
        # 기본 전략
        strategies = self.recovery_strategies.get(error_code, [
            RecoveryStrategy.USER_INTERVENTION,
            RecoveryStrategy.ESCALATE
        ])
        
        # 컨텍스트 기반 전략 조정
        if context:
            # 재시도 횟수 확인
            retry_count = context.get('retry_count', 0)
            if retry_count >= self.config.server.max_retries:
                # 최대 재시도 횟수 초과 시 재시도 전략 제거
                strategies = [s for s in strategies if 'retry' not in s.value]
            
            # 오류 빈도 확인
            if self._is_frequent_error(error_code):
                # 빈번한 오류의 경우 즉시 에스컬레이션
                strategies = [RecoveryStrategy.ESCALATE]
        
        # 오류 패턴 분석 기반 조정
        pattern_adjustment = self._analyze_error_patterns(error_code)
        if pattern_adjustment:
            strategies = pattern_adjustment + strategies
        
        self.logger.debug(f"결정된 복구 전략: {[s.value for s in strategies]}")
        return strategies
    
    def _execute_recovery_strategies(self, 
                                   error_info: ErrorInfo,
                                   strategies: List[RecoveryStrategy],
                                   context: Dict[str, Any] = None,
                                   retry_callback: Callable = None) -> Dict[str, Any]:
        """
        복구 전략 실행
        
        Args:
            error_info: 오류 정보
            strategies: 복구 전략 목록
            context: 컨텍스트 정보
            retry_callback: 재시도 콜백 함수
            
        Returns:
            Dict[str, Any]: 복구 결과
        """
        self.recovery_stats['total_attempts'] += 1
        
        for i, strategy in enumerate(strategies):
            self.logger.info(f"복구 전략 실행 ({i+1}/{len(strategies)}): {strategy.value}")
            
            try:
                result = self._execute_single_strategy(
                    strategy, error_info, context, retry_callback
                )
                
                if result['result'] in [RecoveryResult.SUCCESS, RecoveryResult.PARTIAL_SUCCESS]:
                    self.recovery_stats['successful_recoveries'] += 1
                    return result
                elif result['result'] == RecoveryResult.REQUIRES_USER_ACTION:
                    self.recovery_stats['user_interventions'] += 1
                    return result
                elif result['result'] == RecoveryResult.ESCALATED:
                    self.recovery_stats['escalations'] += 1
                    return result
                
                # 다음 전략으로 계속
                self.logger.info(f"전략 {strategy.value} 실패, 다음 전략 시도")
                
            except Exception as e:
                self.logger.error(f"복구 전략 실행 중 오류: {e}")
                continue
        
        # 모든 전략 실패
        self.recovery_stats['failed_recoveries'] += 1
        return {
            'result': RecoveryResult.FAILED,
            'message': '모든 복구 전략이 실패했습니다',
            'error_code': error_info.error_code,
            'recovery_actions': error_info.recovery_actions
        }
    
    def _execute_single_strategy(self, 
                               strategy: RecoveryStrategy,
                               error_info: ErrorInfo,
                               context: Dict[str, Any] = None,
                               retry_callback: Callable = None) -> Dict[str, Any]:
        """
        단일 복구 전략 실행
        
        Args:
            strategy: 복구 전략
            error_info: 오류 정보
            context: 컨텍스트 정보
            retry_callback: 재시도 콜백 함수
            
        Returns:
            Dict[str, Any]: 실행 결과
        """
        if strategy == RecoveryStrategy.IMMEDIATE_RETRY:
            return self._immediate_retry(error_info, context, retry_callback)
        
        elif strategy == RecoveryStrategy.DELAYED_RETRY:
            return self._delayed_retry(error_info, context, retry_callback)
        
        elif strategy == RecoveryStrategy.USER_INTERVENTION:
            return self._request_user_intervention(error_info, context)
        
        elif strategy == RecoveryStrategy.FALLBACK_MODE:
            return self._activate_fallback_mode(error_info, context)
        
        elif strategy == RecoveryStrategy.ESCALATE:
            return self._escalate_error(error_info, context)
        
        else:
            return {
                'result': RecoveryResult.FAILED,
                'message': f'알 수 없는 복구 전략: {strategy.value}'
            }
    
    def _immediate_retry(self, 
                        error_info: ErrorInfo,
                        context: Dict[str, Any] = None,
                        retry_callback: Callable = None) -> Dict[str, Any]:
        """즉시 재시도"""
        if not retry_callback:
            return {
                'result': RecoveryResult.FAILED,
                'message': '재시도 콜백이 제공되지 않았습니다'
            }
        
        try:
            self.logger.info("즉시 재시도 실행")
            result = retry_callback()
            
            if result and result.success:
                return {
                    'result': RecoveryResult.SUCCESS,
                    'message': '즉시 재시도 성공',
                    'response': result
                }
            else:
                return {
                    'result': RecoveryResult.FAILED,
                    'message': '즉시 재시도 실패',
                    'response': result
                }
                
        except Exception as e:
            return {
                'result': RecoveryResult.FAILED,
                'message': f'즉시 재시도 중 오류: {str(e)}'
            }
    
    def _delayed_retry(self, 
                      error_info: ErrorInfo,
                      context: Dict[str, Any] = None,
                      retry_callback: Callable = None) -> Dict[str, Any]:
        """지연 재시도"""
        if not retry_callback:
            return {
                'result': RecoveryResult.FAILED,
                'message': '재시도 콜백이 제공되지 않았습니다'
            }
        
        # 지연 시간 계산
        retry_count = context.get('retry_count', 0) if context else 0
        delay = self.config.server.retry_delay * (2 ** retry_count)  # 지수 백오프
        delay = min(delay, 30)  # 최대 30초
        
        try:
            self.logger.info(f"지연 재시도 실행 ({delay}초 대기)")
            time.sleep(delay)
            
            result = retry_callback()
            
            if result and result.success:
                return {
                    'result': RecoveryResult.SUCCESS,
                    'message': f'지연 재시도 성공 ({delay}초 대기 후)',
                    'response': result
                }
            else:
                return {
                    'result': RecoveryResult.FAILED,
                    'message': f'지연 재시도 실패 ({delay}초 대기 후)',
                    'response': result
                }
                
        except Exception as e:
            return {
                'result': RecoveryResult.FAILED,
                'message': f'지연 재시도 중 오류: {str(e)}'
            }
    
    def _request_user_intervention(self, 
                                 error_info: ErrorInfo,
                                 context: Dict[str, Any] = None) -> Dict[str, Any]:
        """사용자 개입 요청"""
        self.logger.info("사용자 개입 요청")
        
        # 사용자 친화적 메시지 생성
        user_message = self._generate_user_friendly_message(error_info)
        
        # UI 액션 생성
        ui_actions = self._generate_user_intervention_actions(error_info)
        
        return {
            'result': RecoveryResult.REQUIRES_USER_ACTION,
            'message': user_message,
            'error_code': error_info.error_code,
            'recovery_actions': error_info.recovery_actions,
            'ui_actions': ui_actions,
            'user_guidance': self._generate_user_guidance(error_info)
        }
    
    def _activate_fallback_mode(self, 
                              error_info: ErrorInfo,
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
        """폴백 모드 활성화"""
        self.logger.info("폴백 모드 활성화")
        
        fallback_actions = []
        
        # 오류 타입별 폴백 액션
        if error_info.error_code == ErrorCode.SPEECH_RECOGNITION_ERROR.value:
            fallback_actions = [
                "텍스트 입력 모드로 전환",
                "메뉴에서 직접 선택",
                "터치 인터페이스 활성화"
            ]
        elif error_info.error_code == ErrorCode.INTENT_RECOGNITION_ERROR.value:
            fallback_actions = [
                "단순 명령어 모드로 전환",
                "메뉴 가이드 표시",
                "단계별 주문 진행"
            ]
        elif error_info.error_code == ErrorCode.ORDER_PROCESSING_ERROR.value:
            fallback_actions = [
                "기본 메뉴로 초기화",
                "단순 주문 모드 활성화",
                "관리자 호출"
            ]
        else:
            fallback_actions = [
                "기본 모드로 전환",
                "단순 인터페이스 활성화"
            ]
        
        return {
            'result': RecoveryResult.PARTIAL_SUCCESS,
            'message': '폴백 모드가 활성화되었습니다',
            'fallback_actions': fallback_actions,
            'mode': 'fallback'
        }
    
    def _escalate_error(self, 
                       error_info: ErrorInfo,
                       context: Dict[str, Any] = None) -> Dict[str, Any]:
        """오류 에스컬레이션"""
        self.logger.warning(f"오류 에스컬레이션: {error_info.error_code}")
        
        # 에스컬레이션 정보 생성
        escalation_info = {
            'error_code': error_info.error_code,
            'error_message': error_info.error_message,
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'recovery_attempts': self.recovery_stats['total_attempts'],
            'error_frequency': self._get_error_frequency(error_info.error_code)
        }
        
        # 관리자 알림 (실제 구현에서는 알림 시스템 연동)
        self._notify_administrator(escalation_info)
        
        return {
            'result': RecoveryResult.ESCALATED,
            'message': '문제가 관리자에게 보고되었습니다',
            'escalation_info': escalation_info,
            'support_contact': self._get_support_contact_info()
        }
    
    def _generate_user_friendly_message(self, error_info: ErrorInfo) -> str:
        """사용자 친화적 메시지 생성"""
        error_code = error_info.error_code
        
        messages = {
            ErrorCode.NETWORK_ERROR.value: "네트워크 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요.",
            ErrorCode.TIMEOUT_ERROR.value: "처리 시간이 초과되었습니다. 다시 시도해주세요.",
            ErrorCode.SPEECH_RECOGNITION_ERROR.value: "음성을 인식하지 못했습니다. 더 명확하게 말씀해주세요.",
            ErrorCode.INTENT_RECOGNITION_ERROR.value: "명령을 이해하지 못했습니다. 다른 방식으로 말씀해주세요.",
            ErrorCode.ORDER_PROCESSING_ERROR.value: "주문 처리 중 문제가 발생했습니다. 다시 시도해주세요.",
            ErrorCode.VALIDATION_ERROR.value: "입력하신 정보에 문제가 있습니다. 확인 후 다시 시도해주세요.",
            ErrorCode.SERVER_ERROR.value: "서버에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        }
        
        return messages.get(error_code, "문제가 발생했습니다. 다시 시도해주세요.")
    
    def _generate_user_intervention_actions(self, error_info: ErrorInfo) -> List[UIAction]:
        """사용자 개입 액션 생성"""
        error_code = error_info.error_code
        actions = []
        
        if error_code == ErrorCode.SPEECH_RECOGNITION_ERROR.value:
            actions.append(UIAction(
                action_type="show_voice_guide",
                data={
                    "title": "음성 인식 도움말",
                    "instructions": [
                        "마이크에 가까이서 말씀해주세요",
                        "주변 소음을 줄여주세요",
                        "천천히 명확하게 발음해주세요"
                    ]
                }
            ))
        
        elif error_code == ErrorCode.NETWORK_ERROR.value:
            actions.append(UIAction(
                action_type="show_network_status",
                data={
                    "title": "네트워크 상태 확인",
                    "check_items": [
                        "Wi-Fi 연결 상태",
                        "인터넷 연결 상태",
                        "서버 연결 상태"
                    ]
                }
            ))
        
        # 공통 재시도 버튼
        actions.append(UIAction(
            action_type="show_retry_button",
            data={
                "text": "다시 시도",
                "enabled": True
            }
        ))
        
        return actions
    
    def _generate_user_guidance(self, error_info: ErrorInfo) -> Dict[str, Any]:
        """사용자 가이드 생성"""
        error_code = error_info.error_code
        
        guidance = {
            'title': '문제 해결 가이드',
            'steps': error_info.recovery_actions,
            'tips': [],
            'alternatives': []
        }
        
        if error_code == ErrorCode.SPEECH_RECOGNITION_ERROR.value:
            guidance['tips'] = [
                "조용한 환경에서 시도해보세요",
                "마이크와 30cm 이내 거리를 유지하세요",
                "표준어로 말씀해주세요"
            ]
            guidance['alternatives'] = [
                "터치 스크린으로 주문하기",
                "직원 호출하기"
            ]
        
        elif error_code == ErrorCode.NETWORK_ERROR.value:
            guidance['tips'] = [
                "Wi-Fi 신호 강도를 확인하세요",
                "다른 기기의 인터넷 연결을 확인하세요"
            ]
            guidance['alternatives'] = [
                "직원에게 주문하기",
                "현금 결제로 변경하기"
            ]
        
        return guidance
    
    def _record_error(self, error_info: ErrorInfo, context: Dict[str, Any] = None):
        """오류 기록"""
        error_record = {
            'error_code': error_info.error_code,
            'timestamp': datetime.now(),
            'context': context or {}
        }
        
        self.error_history.append(error_record)
        
        # 히스토리 크기 제한
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)
        
        # 패턴 통계 업데이트
        error_code = error_info.error_code
        if error_code not in self.recovery_stats['error_patterns']:
            self.recovery_stats['error_patterns'][error_code] = {
                'count': 0,
                'first_occurrence': datetime.now(),
                'last_occurrence': datetime.now()
            }
        
        self.recovery_stats['error_patterns'][error_code]['count'] += 1
        self.recovery_stats['error_patterns'][error_code]['last_occurrence'] = datetime.now()
    
    def _record_recovery_result(self, error_info: ErrorInfo, result: Dict[str, Any]):
        """복구 결과 기록"""
        self.logger.info(f"복구 결과: {result['result'].value if isinstance(result['result'], RecoveryResult) else result['result']}")
    
    def _is_frequent_error(self, error_code: str, threshold: int = 5, window_minutes: int = 10) -> bool:
        """빈번한 오류 여부 확인"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        recent_errors = [
            record for record in self.error_history
            if record['error_code'] == error_code and record['timestamp'] >= window_start
        ]
        
        return len(recent_errors) >= threshold
    
    def _analyze_error_patterns(self, error_code: str) -> List[RecoveryStrategy]:
        """오류 패턴 분석"""
        # 간단한 패턴 분석 (실제로는 더 복잡한 ML 기반 분석 가능)
        if self._is_frequent_error(error_code):
            return [RecoveryStrategy.ESCALATE]
        
        return []
    
    def _get_error_frequency(self, error_code: str) -> int:
        """오류 빈도 조회"""
        return self.recovery_stats['error_patterns'].get(error_code, {}).get('count', 0)
    
    def _notify_administrator(self, escalation_info: Dict[str, Any]):
        """관리자 알림 (실제 구현에서는 알림 시스템 연동)"""
        self.logger.critical(f"관리자 알림: {escalation_info}")
        # 실제로는 이메일, SMS, 슬랙 등으로 알림 전송
    
    def _get_support_contact_info(self) -> Dict[str, str]:
        """지원 연락처 정보"""
        return {
            'phone': '1588-0000',
            'email': 'support@voicekiosk.com',
            'hours': '09:00-18:00 (평일)'
        }
    
    def register_recovery_callback(self, error_code: str, callback: Callable):
        """복구 콜백 등록"""
        if error_code not in self.recovery_callbacks:
            self.recovery_callbacks[error_code] = []
        self.recovery_callbacks[error_code].append(callback)
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """복구 통계 조회"""
        return {
            **self.recovery_stats,
            'success_rate': (
                self.recovery_stats['successful_recoveries'] / 
                max(self.recovery_stats['total_attempts'], 1)
            ) * 100
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.recovery_stats = {
            'total_attempts': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'user_interventions': 0,
            'escalations': 0,
            'error_patterns': {}
        }
        self.error_history.clear()
        self.logger.info("복구 통계 초기화 완료")