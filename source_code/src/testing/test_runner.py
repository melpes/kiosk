"""
테스트케이스 실행 엔진
"""

import time
import uuid
from typing import List, Optional
from datetime import datetime

from ..models.testing_models import TestCase, TestResult, TestResults
from ..models.conversation_models import IntentType
from ..logger import get_logger
from ..utils.env_loader import get_test_config


class TestRunner:
    """테스트케이스 실행 엔진"""
    
    def __init__(self, pipeline):
        """
        TestRunner 초기화
        
        Args:
            pipeline: VoiceKioskPipeline 인스턴스
        """
        self.pipeline = pipeline
        self.logger = get_logger(__name__)
        self.current_session_id: Optional[str] = None
        
        # 테스트 설정 로드
        self.test_config = get_test_config()
        self.delay_between_requests = self.test_config.get('delay_between_requests', 2.0)
        
    def setup_test_session(self) -> str:
        """테스트 세션 설정"""
        try:
            # 기존 세션이 있으면 종료
            if self.current_session_id and self.pipeline.dialogue_manager:
                self.pipeline.dialogue_manager.end_session(self.current_session_id)
            
            # 새로운 테스트 세션 시작
            if not self.pipeline.is_initialized:
                if not self.pipeline.initialize_system():
                    raise RuntimeError("파이프라인 초기화 실패")
            
            self.current_session_id = self.pipeline.start_session()
            self.logger.info(f"테스트 세션 설정 완료: {self.current_session_id}")
            return self.current_session_id
            
        except Exception as e:
            self.logger.error(f"테스트 세션 설정 실패: {e}")
            raise
    
    def cleanup_test_session(self, session_id: str):
        """테스트 세션 정리"""
        try:
            if session_id and self.pipeline.dialogue_manager:
                self.pipeline.dialogue_manager.end_session(session_id)
                self.logger.info(f"테스트 세션 정리 완료: {session_id}")
            
            if session_id == self.current_session_id:
                self.current_session_id = None
                
        except Exception as e:
            self.logger.error(f"테스트 세션 정리 실패: {e}")
    
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """
        단일 테스트케이스 실행
        
        Args:
            test_case: 실행할 테스트케이스
            
        Returns:
            TestResult: 테스트 실행 결과
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"테스트 실행 시작: {test_case.id} - '{test_case.input_text}'")
            
            # 테스트 세션이 없으면 생성
            if not self.current_session_id:
                self.setup_test_session()
            
            # 파이프라인을 통해 텍스트 입력 처리
            system_response = self.pipeline.process_text_input(test_case.input_text)
            
            # 의도 파악 결과 추출
            detected_intent, confidence_score = self._extract_intent_from_pipeline(test_case.input_text)
            
            # 처리 시간 계산
            processing_time = time.time() - start_time
            
            # 성공 여부 판단
            success = self._evaluate_test_success(test_case, detected_intent, confidence_score)
            
            # 시스템 응답 출력 (콘솔)
            print(f"\n📝 입력: '{test_case.input_text}'")
            print(f"🤖 출력: '{system_response}'")
            print(f"🎯 의도: {detected_intent.value} (신뢰도: {confidence_score:.3f})")
            print(f"✅ 성공: {'성공' if success else '실패'}")
            
            # 테스트 결과 생성
            result = TestResult(
                test_case=test_case,
                system_response=system_response,
                detected_intent=detected_intent,
                processing_time=processing_time,
                success=success,
                confidence_score=confidence_score,
                session_id=self.current_session_id,
                input_text=test_case.input_text,
                output_text=system_response
            )
            
            self.logger.info(f"테스트 완료: {test_case.id} - 성공: {success}, 신뢰도: {confidence_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"테스트 실행 중 오류: {test_case.id} - {e}")
            
            # 오류 결과 생성
            error_result = TestResult(
                test_case=test_case,
                system_response=f"실행 오류: {e}",
                detected_intent=IntentType.UNKNOWN,
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e),
                confidence_score=0.0,
                session_id=self.current_session_id,
                input_text=test_case.input_text,
                output_text=f"실행 오류: {e}"
            )
            return error_result
    
    def run_batch_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        """
        배치 테스트케이스 실행
        
        Args:
            test_cases: 실행할 테스트케이스 목록
            
        Returns:
            List[TestResult]: 테스트 실행 결과 목록
        """
        results = []
        total_tests = len(test_cases)
        
        self.logger.info(f"배치 테스트 시작: 총 {total_tests}개 테스트케이스")
        print(f"\n🚀 배치 테스트 실행 시작: 총 {total_tests}개 테스트케이스")
        print(f"⏱️ 요청 간 지연시간: {self.delay_between_requests}초 (API 속도 제한 방지)")
        
        try:
            # 테스트 세션 설정
            session_id = self.setup_test_session()
            
            for i, test_case in enumerate(test_cases, 1):
                try:
                    # 진행률 표시 (콘솔)
                    progress_percent = i / total_tests * 100
                    print(f"\r🔄 진행률: {i}/{total_tests} ({progress_percent:.1f}%) - {test_case.id}", end="", flush=True)
                    
                    self.logger.info(f"진행률: {i}/{total_tests} ({progress_percent:.1f}%) - 테스트: {test_case.id}")
                    
                    # 개별 테스트 실행
                    result = self.run_single_test(test_case)
                    results.append(result)
                    
                    # API 속도 제한 방지를 위한 지연 (마지막 테스트 제외)
                    if i < total_tests and self.delay_between_requests > 0:
                        print(f"\n⏳ API 속도 제한 방지를 위해 {self.delay_between_requests}초 대기 중...")
                        time.sleep(self.delay_between_requests)
                    
                    # 중간 결과 표시 (매 10개 또는 마지막)
                    if i % 10 == 0 or i == total_tests:
                        success_count = sum(1 for r in results if r.success)
                        success_rate = success_count / i * 100
                        print(f"\n📊 중간 결과: {i}개 완료, 성공률: {success_rate:.1f}%")
                        self.logger.info(f"중간 결과: {i}개 완료, 성공률: {success_rate:.1f}%")
                        
                        # 최근 실패한 테스트 표시
                        recent_failures = [r for r in results[-10:] if not r.success]
                        if recent_failures:
                            print(f"⚠️ 최근 실패: {len(recent_failures)}개")
                            for failure in recent_failures[-3:]:  # 최대 3개만 표시
                                print(f"   - {failure.test_case.id}: {failure.error_message or '의도 불일치'}")
                
                except Exception as e:
                    self.logger.error(f"테스트케이스 {test_case.id} 실행 중 오류: {e}")
                    print(f"\n❌ 테스트 {test_case.id} 실행 실패: {e}")
                    
                    # 오류 결과 생성하여 추가
                    error_result = TestResult(
                        test_case=test_case,
                        system_response=f"실행 오류: {e}",
                        detected_intent=IntentType.UNKNOWN,
                        processing_time=0.0,
                        success=False,
                        error_message=str(e),
                        confidence_score=0.0,
                        session_id=self.current_session_id
                    )
                    results.append(error_result)
                    continue
            
            print(f"\n✅ 배치 테스트 완료: {len(results)}개 결과 생성")
            self.logger.info(f"배치 테스트 완료: {len(results)}개 결과 생성")
            
        finally:
            # 테스트 세션 정리
            if self.current_session_id:
                self.cleanup_test_session(self.current_session_id)
        
        return results
    
    def run_test_suite(self, test_cases: List[TestCase]) -> TestResults:
        """
        테스트 스위트 실행 (TestResults 객체 반환)
        
        Args:
            test_cases: 실행할 테스트케이스 목록
            
        Returns:
            TestResults: 테스트 결과 컬렉션
        """
        # 테스트 세션 ID 생성
        test_session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        # TestResults 객체 생성
        test_results = TestResults(session_id=test_session_id)
        
        self.logger.info(f"테스트 스위트 시작: {test_session_id}")
        
        try:
            # 배치 테스트 실행
            results = self.run_batch_tests(test_cases)
            
            # 결과를 TestResults 객체에 추가
            for result in results:
                test_results.add_result(result)
            
            # 테스트 완료 처리
            test_results.finish()
            
            # 결과 요약 로그
            self.logger.info(f"테스트 스위트 완료:")
            self.logger.info(f"  - 총 테스트: {test_results.total_tests}개")
            self.logger.info(f"  - 성공: {test_results.successful_tests}개")
            self.logger.info(f"  - 성공률: {test_results.success_rate*100:.1f}%")
            self.logger.info(f"  - 평균 처리시간: {test_results.average_processing_time:.3f}초")
            self.logger.info(f"  - 총 소요시간: {test_results.total_duration:.1f}초")
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"테스트 스위트 실행 실패: {e}")
            test_results.finish()
            raise
    
    def _extract_intent_from_pipeline(self, input_text: str) -> tuple[IntentType, float]:
        """
        파이프라인에서 의도 파악 결과 추출
        
        Args:
            input_text: 입력 텍스트
            
        Returns:
            tuple: (detected_intent, confidence_score)
        """
        try:
            # 파이프라인의 의도 파악 모듈을 직접 사용
            if not self.pipeline.intent_recognizer:
                return IntentType.UNKNOWN, 0.0
            
            # 현재 대화 컨텍스트 가져오기
            context = None
            if self.pipeline.dialogue_manager and self.current_session_id:
                context = self.pipeline.dialogue_manager.get_context(self.current_session_id)
            
            # 의도 파악 실행
            intent_result = self.pipeline.intent_recognizer.recognize_intent(input_text, context)
            
            return intent_result.type, intent_result.confidence
            
        except Exception as e:
            self.logger.error(f"의도 추출 실패: {e}")
            return IntentType.UNKNOWN, 0.0
    
    def _evaluate_test_success(self, test_case: TestCase, detected_intent: IntentType, 
                             confidence_score: float) -> bool:
        """
        테스트 성공 여부 평가
        
        Args:
            test_case: 테스트케이스
            detected_intent: 감지된 의도
            confidence_score: 신뢰도 점수
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 1. 예상 의도와 일치하는지 확인
            intent_matches = True
            if test_case.expected_intent is not None:
                intent_matches = (detected_intent == test_case.expected_intent)
            
            # 2. 신뢰도가 최소 임계값을 만족하는지 확인
            confidence_meets_threshold = (confidence_score >= test_case.expected_confidence_min)
            
            # 3. 전체 성공 여부 판단
            success = intent_matches and confidence_meets_threshold
            
            # 디버그 로그
            self.logger.debug(f"테스트 평가 - {test_case.id}:")
            self.logger.debug(f"  예상 의도: {test_case.expected_intent}")
            self.logger.debug(f"  감지 의도: {detected_intent}")
            self.logger.debug(f"  의도 일치: {intent_matches}")
            self.logger.debug(f"  신뢰도: {confidence_score:.3f} (최소: {test_case.expected_confidence_min})")
            self.logger.debug(f"  신뢰도 만족: {confidence_meets_threshold}")
            self.logger.debug(f"  최종 성공: {success}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"테스트 평가 실패: {e}")
            return False
    
    def get_runner_status(self) -> dict:
        """테스트 러너 상태 정보 반환"""
        return {
            'current_session_id': self.current_session_id,
            'pipeline_initialized': self.pipeline.is_initialized if self.pipeline else False,
            'pipeline_running': self.pipeline.is_running if self.pipeline else False
        }