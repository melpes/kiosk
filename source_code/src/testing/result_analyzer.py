"""
테스트 결과 분석기
"""

from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime

from ..models.testing_models import (
    TestResults, TestResult, TestAnalysis, TestCaseCategory
)
from ..models.conversation_models import IntentType
from ..logger import get_logger


class ResultAnalyzer:
    """테스트 결과 분석기"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def analyze_results(self, test_results: TestResults) -> TestAnalysis:
        """
        테스트 결과를 종합적으로 분석
        
        Args:
            test_results: 분석할 테스트 결과
            
        Returns:
            TestAnalysis: 분석된 결과
        """
        try:
            self.logger.info(f"테스트 결과 분석 시작: {test_results.total_tests}개 결과")
            
            # 기본 통계 계산
            total_tests = test_results.total_tests
            success_rate = test_results.success_rate
            average_processing_time = test_results.average_processing_time
            
            # 의도별 정확도 분석
            intent_accuracy = self._analyze_intent_accuracy(test_results.results)
            
            # 카테고리별 성능 분석
            category_performance = self._analyze_category_performance(test_results.results)
            
            # 오류 요약 분석
            error_summary = self._analyze_error_summary(test_results.results)
            
            # 분석 결과 생성
            analysis = TestAnalysis(
                total_tests=total_tests,
                success_rate=success_rate,
                average_processing_time=average_processing_time,
                intent_accuracy=intent_accuracy,
                category_performance=category_performance,
                error_summary=error_summary,
                detailed_results=test_results.results
            )
            
            self.logger.info(f"테스트 결과 분석 완료: 성공률 {success_rate:.2%}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"테스트 결과 분석 중 오류 발생: {e}")
            # 기본 분석 결과 반환
            return TestAnalysis(
                total_tests=test_results.total_tests,
                success_rate=test_results.success_rate,
                average_processing_time=test_results.average_processing_time,
                intent_accuracy={},
                category_performance={},
                error_summary={},
                detailed_results=test_results.results
            )
    
    def _analyze_intent_accuracy(self, results: List[TestResult]) -> Dict[str, float]:
        """
        의도별 정확도 분석
        
        Args:
            results: 테스트 결과 리스트
            
        Returns:
            Dict[str, float]: 의도별 정확도
        """
        intent_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for result in results:
            if result.test_case.expected_intent is not None:
                intent_name = result.test_case.expected_intent.value
                intent_stats[intent_name]['total'] += 1
                
                if result.intent_matches:
                    intent_stats[intent_name]['correct'] += 1
        
        # 정확도 계산
        accuracy = {}
        for intent, stats in intent_stats.items():
            if stats['total'] > 0:
                accuracy[intent] = stats['correct'] / stats['total']
            else:
                accuracy[intent] = 0.0
        
        return accuracy
    
    def _analyze_category_performance(self, results: List[TestResult]) -> Dict[str, float]:
        """
        카테고리별 성능 분석
        
        Args:
            results: 테스트 결과 리스트
            
        Returns:
            Dict[str, float]: 카테고리별 성공률
        """
        category_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        
        for result in results:
            category_name = result.test_case.category.value
            category_stats[category_name]['total'] += 1
            
            if result.success:
                category_stats[category_name]['success'] += 1
        
        # 성공률 계산
        performance = {}
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                performance[category] = stats['success'] / stats['total']
            else:
                performance[category] = 0.0
        
        return performance
    
    def _analyze_error_summary(self, results: List[TestResult]) -> Dict[str, int]:
        """
        오류 요약 분석
        
        Args:
            results: 테스트 결과 리스트
            
        Returns:
            Dict[str, int]: 오류 유형별 개수
        """
        error_counter = Counter()
        
        for result in results:
            if not result.success and result.error_message:
                # 오류 메시지를 분류
                error_type = self._classify_error(result.error_message)
                error_counter[error_type] += 1
        
        return dict(error_counter)
    
    def _classify_error(self, error_message: str) -> str:
        """
        오류 메시지를 분류
        
        Args:
            error_message: 오류 메시지
            
        Returns:
            str: 오류 유형
        """
        error_message_lower = error_message.lower()
        
        if 'timeout' in error_message_lower:
            return 'timeout_error'
        elif 'connection' in error_message_lower:
            return 'connection_error'
        elif 'api' in error_message_lower:
            return 'api_error'
        elif 'intent' in error_message_lower:
            return 'intent_recognition_error'
        elif 'parsing' in error_message_lower or 'parse' in error_message_lower:
            return 'parsing_error'
        elif 'validation' in error_message_lower:
            return 'validation_error'
        else:
            return 'unknown_error'
    
    def generate_summary_statistics(self, analysis: TestAnalysis) -> Dict[str, Any]:
        """
        요약 통계 생성
        
        Args:
            analysis: 분석 결과
            
        Returns:
            Dict[str, Any]: 요약 통계
        """
        return {
            'overview': {
                'total_tests': analysis.total_tests,
                'success_rate': f"{analysis.success_rate:.2%}",
                'average_processing_time': f"{analysis.average_processing_time:.3f}s",
                'total_errors': sum(analysis.error_summary.values())
            },
            'intent_performance': {
                intent: f"{accuracy:.2%}" 
                for intent, accuracy in analysis.intent_accuracy.items()
            },
            'category_performance': {
                category: f"{performance:.2%}" 
                for category, performance in analysis.category_performance.items()
            },
            'confidence_distribution': analysis.confidence_distribution,
            'processing_time_stats': analysis.processing_time_stats,
            'top_errors': dict(Counter(analysis.error_summary).most_common(5))
        }
    
    def get_failed_test_details(self, analysis: TestAnalysis) -> List[Dict[str, Any]]:
        """
        실패한 테스트의 상세 정보 추출
        
        Args:
            analysis: 분석 결과
            
        Returns:
            List[Dict[str, Any]]: 실패한 테스트 상세 정보
        """
        failed_tests = []
        
        for result in analysis.detailed_results:
            if not result.success:
                failed_tests.append({
                    'test_id': result.test_case.id,
                    'input_text': result.test_case.input_text,
                    'category': result.test_case.category.value,
                    'expected_intent': result.test_case.expected_intent.value if result.test_case.expected_intent else None,
                    'detected_intent': result.detected_intent.value,
                    'error_message': result.error_message,
                    'confidence_score': result.confidence_score,
                    'processing_time': result.processing_time
                })
        
        return failed_tests
    
    def get_performance_insights(self, analysis: TestAnalysis) -> List[str]:
        """
        성능 인사이트 생성
        
        Args:
            analysis: 분석 결과
            
        Returns:
            List[str]: 성능 인사이트 목록
        """
        insights = []
        
        # 전체 성공률 평가
        if analysis.success_rate >= 0.9:
            insights.append("✅ 전체 성공률이 90% 이상으로 우수합니다.")
        elif analysis.success_rate >= 0.8:
            insights.append("⚠️ 전체 성공률이 80-90%로 양호하지만 개선 여지가 있습니다.")
        else:
            insights.append("❌ 전체 성공률이 80% 미만으로 개선이 필요합니다.")
        
        # 처리 시간 평가
        if analysis.average_processing_time <= 1.0:
            insights.append("✅ 평균 처리 시간이 1초 이하로 빠릅니다.")
        elif analysis.average_processing_time <= 3.0:
            insights.append("⚠️ 평균 처리 시간이 1-3초로 보통입니다.")
        else:
            insights.append("❌ 평균 처리 시간이 3초 이상으로 느립니다.")
        
        # 카테고리별 성능 분석
        if analysis.category_performance:
            worst_category = min(analysis.category_performance.items(), key=lambda x: x[1])
            best_category = max(analysis.category_performance.items(), key=lambda x: x[1])
            
            insights.append(f"📊 가장 성능이 좋은 카테고리: {best_category[0]} ({best_category[1]:.1%})")
            insights.append(f"📊 가장 성능이 나쁜 카테고리: {worst_category[0]} ({worst_category[1]:.1%})")
        
        # 오류 분석
        if analysis.error_summary:
            most_common_error = max(analysis.error_summary.items(), key=lambda x: x[1])
            insights.append(f"🔍 가장 빈번한 오류: {most_common_error[0]} ({most_common_error[1]}회)")
        
        # 신뢰도 분석
        if analysis.confidence_distribution:
            low_confidence = analysis.confidence_distribution.get('low', 0)
            total_tests = sum(analysis.confidence_distribution.values())
            if total_tests > 0:
                low_confidence_rate = low_confidence / total_tests
                if low_confidence_rate > 0.2:
                    insights.append(f"⚠️ 낮은 신뢰도(0.5 미만) 결과가 {low_confidence_rate:.1%}로 높습니다.")
        
        return insights