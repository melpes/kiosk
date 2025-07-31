#!/usr/bin/env python3
"""
간단한 테스트 결과 분석 및 보고서 생성 테스트
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

# 필요한 모델들을 직접 정의
class IntentType(Enum):
    ORDER = "order"
    MODIFY = "modify"
    CANCEL = "cancel"
    PAYMENT = "payment"
    INQUIRY = "inquiry"
    UNKNOWN = "unknown"

class TestCaseCategory(Enum):
    SLANG = "slang"
    INFORMAL = "informal"
    COMPLEX = "complex"
    NORMAL = "normal"
    EDGE = "edge"

@dataclass
class TestCase:
    id: str
    input_text: str
    expected_intent: IntentType
    category: TestCaseCategory
    description: str
    tags: List[str] = field(default_factory=list)

@dataclass
class TestResult:
    test_case: TestCase
    system_response: str
    detected_intent: IntentType
    processing_time: float
    success: bool
    error_message: str = None
    confidence_score: float = 0.0
    
    @property
    def intent_matches(self) -> bool:
        return self.detected_intent == self.test_case.expected_intent

@dataclass
class TestResults:
    session_id: str
    results: List[TestResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = None
    
    def add_result(self, result: TestResult):
        self.results.append(result)
    
    def finish(self):
        self.end_time = datetime.now()
    
    @property
    def total_tests(self) -> int:
        return len(self.results)
    
    @property
    def successful_tests(self) -> int:
        return sum(1 for result in self.results if result.success)
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return self.successful_tests / self.total_tests
    
    @property
    def average_processing_time(self) -> float:
        if not self.results:
            return 0.0
        return sum(result.processing_time for result in self.results) / len(self.results)

@dataclass
class TestAnalysis:
    total_tests: int
    success_rate: float
    average_processing_time: float
    intent_accuracy: Dict[str, float]
    category_performance: Dict[str, float]
    error_summary: Dict[str, int]
    detailed_results: List[TestResult]
    confidence_distribution: Dict[str, int] = field(default_factory=dict)
    processing_time_stats: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.detailed_results:
            self._calculate_confidence_distribution()
            self._calculate_processing_time_stats()
    
    def _calculate_confidence_distribution(self):
        ranges = {'very_high': 0, 'high': 0, 'medium': 0, 'low': 0}
        for result in self.detailed_results:
            confidence = result.confidence_score
            if confidence >= 0.9:
                ranges['very_high'] += 1
            elif confidence >= 0.7:
                ranges['high'] += 1
            elif confidence >= 0.5:
                ranges['medium'] += 1
            else:
                ranges['low'] += 1
        self.confidence_distribution = ranges
    
    def _calculate_processing_time_stats(self):
        if not self.detailed_results:
            return
        times = [result.processing_time for result in self.detailed_results]
        self.processing_time_stats = {
            'min': min(times),
            'max': max(times),
            'median': sorted(times)[len(times) // 2],
            'std_dev': self._calculate_std_dev(times)
        }
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

# ResultAnalyzer 클래스
class ResultAnalyzer:
    def __init__(self):
        pass
    
    def analyze_results(self, test_results: TestResults) -> TestAnalysis:
        print(f"테스트 결과 분석 시작: {test_results.total_tests}개 결과")
        
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
        
        print(f"테스트 결과 분석 완료: 성공률 {success_rate:.2%}")
        return analysis
    
    def _analyze_intent_accuracy(self, results: List[TestResult]) -> Dict[str, float]:
        intent_stats = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        for result in results:
            if result.test_case.expected_intent is not None:
                intent_name = result.test_case.expected_intent.value
                intent_stats[intent_name]['total'] += 1
                
                if result.intent_matches:
                    intent_stats[intent_name]['correct'] += 1
        
        accuracy = {}
        for intent, stats in intent_stats.items():
            if stats['total'] > 0:
                accuracy[intent] = stats['correct'] / stats['total']
            else:
                accuracy[intent] = 0.0
        
        return accuracy
    
    def _analyze_category_performance(self, results: List[TestResult]) -> Dict[str, float]:
        category_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        
        for result in results:
            category_name = result.test_case.category.value
            category_stats[category_name]['total'] += 1
            
            if result.success:
                category_stats[category_name]['success'] += 1
        
        performance = {}
        for category, stats in category_stats.items():
            if stats['total'] > 0:
                performance[category] = stats['success'] / stats['total']
            else:
                performance[category] = 0.0
        
        return performance
    
    def _analyze_error_summary(self, results: List[TestResult]) -> Dict[str, int]:
        error_counter = Counter()
        
        for result in results:
            if not result.success and result.error_message:
                error_type = self._classify_error(result.error_message)
                error_counter[error_type] += 1
        
        return dict(error_counter)
    
    def _classify_error(self, error_message: str) -> str:
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
    
    def get_performance_insights(self, analysis: TestAnalysis) -> List[str]:
        insights = []
        
        if analysis.success_rate >= 0.9:
            insights.append("✅ 전체 성공률이 90% 이상으로 우수합니다.")
        elif analysis.success_rate >= 0.8:
            insights.append("⚠️ 전체 성공률이 80-90%로 양호하지만 개선 여지가 있습니다.")
        else:
            insights.append("❌ 전체 성공률이 80% 미만으로 개선이 필요합니다.")
        
        if analysis.average_processing_time <= 1.0:
            insights.append("✅ 평균 처리 시간이 1초 이하로 빠릅니다.")
        elif analysis.average_processing_time <= 3.0:
            insights.append("⚠️ 평균 처리 시간이 1-3초로 보통입니다.")
        else:
            insights.append("❌ 평균 처리 시간이 3초 이상으로 느립니다.")
        
        if analysis.category_performance:
            worst_category = min(analysis.category_performance.items(), key=lambda x: x[1])
            best_category = max(analysis.category_performance.items(), key=lambda x: x[1])
            
            insights.append(f"📊 가장 성능이 좋은 카테고리: {best_category[0]} ({best_category[1]:.1%})")
            insights.append(f"📊 가장 성능이 나쁜 카테고리: {worst_category[0]} ({worst_category[1]:.1%})")
        
        if analysis.error_summary:
            most_common_error = max(analysis.error_summary.items(), key=lambda x: x[1])
            insights.append(f"🔍 가장 빈번한 오류: {most_common_error[0]} ({most_common_error[1]}회)")
        
        return insights

# ReportGenerator 클래스
class ReportGenerator:
    def __init__(self, output_directory: str = "test_results"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.reports_dir = self.output_directory / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_text_report(self, analysis: TestAnalysis, output_path: str = None) -> str:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"test_report_{timestamp}.txt"
        else:
            output_path = Path(output_path)
        
        print(f"텍스트 보고서 생성 시작: {output_path}")
        
        content = self._generate_text_content(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"텍스트 보고서 생성 완료: {output_path}")
        return str(output_path)
    
    def generate_markdown_report(self, analysis: TestAnalysis, output_path: str = None) -> str:
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"test_report_{timestamp}.md"
        else:
            output_path = Path(output_path)
        
        print(f"마크다운 보고서 생성 시작: {output_path}")
        
        content = self._generate_markdown_content(analysis)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"마크다운 보고서 생성 완료: {output_path}")
        return str(output_path)
    
    def generate_summary_report(self, analysis: TestAnalysis) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("테스트 결과 요약")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append("📊 기본 통계")
        lines.append(f"  • 전체 테스트: {analysis.total_tests}개")
        lines.append(f"  • 성공률: {analysis.success_rate:.2%}")
        lines.append(f"  • 평균 처리 시간: {analysis.average_processing_time:.3f}초")
        lines.append("")
        
        if analysis.category_performance:
            lines.append("📈 카테고리별 성능")
            for category, performance in sorted(analysis.category_performance.items()):
                lines.append(f"  • {category}: {performance:.2%}")
            lines.append("")
        
        if analysis.error_summary:
            lines.append("❌ 주요 오류")
            sorted_errors = sorted(analysis.error_summary.items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors[:3]:
                lines.append(f"  • {error_type}: {count}회")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_text_content(self, analysis: TestAnalysis) -> str:
        lines = []
        
        lines.append("=" * 80)
        lines.append("음성 키오스크 테스트 결과 보고서")
        lines.append("=" * 80)
        lines.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("1. 전체 요약")
        lines.append("-" * 40)
        lines.append(f"총 테스트 수: {analysis.total_tests}")
        lines.append(f"성공률: {analysis.success_rate:.2%}")
        lines.append(f"평균 처리 시간: {analysis.average_processing_time:.3f}초")
        lines.append(f"총 오류 수: {sum(analysis.error_summary.values())}")
        lines.append("")
        
        if analysis.intent_accuracy:
            lines.append("2. 의도별 정확도")
            lines.append("-" * 40)
            for intent, accuracy in sorted(analysis.intent_accuracy.items()):
                lines.append(f"{intent}: {accuracy:.2%}")
            lines.append("")
        
        if analysis.category_performance:
            lines.append("3. 카테고리별 성능")
            lines.append("-" * 40)
            for category, performance in sorted(analysis.category_performance.items()):
                lines.append(f"{category}: {performance:.2%}")
            lines.append("")
        
        if analysis.error_summary:
            lines.append("4. 오류 분석")
            lines.append("-" * 40)
            sorted_errors = sorted(analysis.error_summary.items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors:
                lines.append(f"{error_type}: {count}회")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("보고서 끝")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_markdown_content(self, analysis: TestAnalysis) -> str:
        lines = []
        
        lines.append("# 음성 키오스크 테스트 결과 보고서")
        lines.append("")
        lines.append(f"**생성 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        lines.append("## 1. 전체 요약")
        lines.append("")
        lines.append("| 항목 | 값 |")
        lines.append("|------|-----|")
        lines.append(f"| 총 테스트 수 | {analysis.total_tests} |")
        lines.append(f"| 성공률 | {analysis.success_rate:.2%} |")
        lines.append(f"| 평균 처리 시간 | {analysis.average_processing_time:.3f}초 |")
        lines.append(f"| 총 오류 수 | {sum(analysis.error_summary.values())} |")
        lines.append("")
        
        if analysis.intent_accuracy:
            lines.append("## 2. 의도별 정확도")
            lines.append("")
            lines.append("| 의도 | 정확도 |")
            lines.append("|------|--------|")
            for intent, accuracy in sorted(analysis.intent_accuracy.items()):
                lines.append(f"| {intent} | {accuracy:.2%} |")
            lines.append("")
        
        if analysis.category_performance:
            lines.append("## 3. 카테고리별 성능")
            lines.append("")
            lines.append("| 카테고리 | 성공률 |")
            lines.append("|----------|--------|")
            for category, performance in sorted(analysis.category_performance.items()):
                lines.append(f"| {category} | {performance:.2%} |")
            lines.append("")
        
        return "\n".join(lines)

def create_sample_test_results() -> TestResults:
    """샘플 테스트 결과 생성"""
    test_results = TestResults(session_id="test_session_001")
    
    # 샘플 테스트케이스들 생성
    test_cases = [
        TestCase(
            id="test_001",
            input_text="빅맥 세트 하나 주세요",
            expected_intent=IntentType.ORDER,
            category=TestCaseCategory.NORMAL,
            description="일반적인 주문"
        ),
        TestCase(
            id="test_002", 
            input_text="상스치콤 하나",
            expected_intent=IntentType.ORDER,
            category=TestCaseCategory.SLANG,
            description="은어 사용 주문"
        ),
        TestCase(
            id="test_003",
            input_text="빅맥 빼고 싶어",
            expected_intent=IntentType.CANCEL,
            category=TestCaseCategory.INFORMAL,
            description="반말 취소 요청"
        ),
        TestCase(
            id="test_004",
            input_text="뭐가 맛있어?",
            expected_intent=IntentType.INQUIRY,
            category=TestCaseCategory.NORMAL,
            description="메뉴 문의"
        ),
        TestCase(
            id="test_005",
            input_text="베토디 추가하고 콜라는 빼줘",
            expected_intent=IntentType.MODIFY,
            category=TestCaseCategory.COMPLEX,
            description="복합 의도 - 추가와 제거"
        )
    ]
    
    # 테스트 결과들 생성
    results = [
        TestResult(
            test_case=test_cases[0],
            system_response="빅맥 세트 1개를 주문하시겠습니까?",
            detected_intent=IntentType.ORDER,
            processing_time=0.85,
            success=True,
            confidence_score=0.95
        ),
        TestResult(
            test_case=test_cases[1],
            system_response="상하이 스파이시 치킨 버거 콤보 1개를 주문하시겠습니까?",
            detected_intent=IntentType.ORDER,
            processing_time=1.2,
            success=True,
            confidence_score=0.88
        ),
        TestResult(
            test_case=test_cases[2],
            system_response="빅맥을 주문에서 제거하겠습니다.",
            detected_intent=IntentType.CANCEL,
            processing_time=0.75,
            success=True,
            confidence_score=0.92
        ),
        TestResult(
            test_case=test_cases[3],
            system_response="죄송합니다. 이해하지 못했습니다.",
            detected_intent=IntentType.UNKNOWN,
            processing_time=2.1,
            success=False,
            confidence_score=0.35,
            error_message="intent_recognition_error: 의도 파악 실패"
        ),
        TestResult(
            test_case=test_cases[4],
            system_response="주문을 처리할 수 없습니다.",
            detected_intent=IntentType.ORDER,
            processing_time=1.8,
            success=False,
            confidence_score=0.45,
            error_message="parsing_error: 복합 의도 처리 실패"
        )
    ]
    
    for result in results:
        test_results.add_result(result)
    
    test_results.finish()
    return test_results

def main():
    """메인 테스트 함수"""
    print("테스트 결과 분석 및 보고서 생성 기능 테스트")
    print("=" * 80)
    
    try:
        # 샘플 데이터 생성
        test_results = create_sample_test_results()
        print(f"샘플 테스트 결과 생성 완료: {test_results.total_tests}개")
        
        # ResultAnalyzer 테스트
        print("\n" + "=" * 60)
        print("ResultAnalyzer 테스트 시작")
        print("=" * 60)
        
        analyzer = ResultAnalyzer()
        analysis = analyzer.analyze_results(test_results)
        
        print(f"\n분석 결과:")
        print(f"- 전체 테스트: {analysis.total_tests}")
        print(f"- 성공률: {analysis.success_rate:.2%}")
        print(f"- 평균 처리 시간: {analysis.average_processing_time:.3f}초")
        
        print(f"\n의도별 정확도:")
        for intent, accuracy in analysis.intent_accuracy.items():
            print(f"- {intent}: {accuracy:.2%}")
        
        print(f"\n카테고리별 성능:")
        for category, performance in analysis.category_performance.items():
            print(f"- {category}: {performance:.2%}")
        
        print(f"\n오류 요약:")
        for error_type, count in analysis.error_summary.items():
            print(f"- {error_type}: {count}회")
        
        print(f"\n신뢰도 분포:")
        for level, count in analysis.confidence_distribution.items():
            print(f"- {level}: {count}개")
        
        # 성능 인사이트 테스트
        insights = analyzer.get_performance_insights(analysis)
        print(f"\n성능 인사이트:")
        for insight in insights:
            print(f"- {insight}")
        
        # ReportGenerator 테스트
        print("\n" + "=" * 60)
        print("ReportGenerator 테스트 시작")
        print("=" * 60)
        
        generator = ReportGenerator(output_directory="test_results")
        
        # 요약 보고서 테스트
        print("\n요약 보고서:")
        summary = generator.generate_summary_report(analysis)
        print(summary)
        
        # 텍스트 보고서 생성
        text_report_path = generator.generate_text_report(analysis)
        
        # 마크다운 보고서 생성
        markdown_report_path = generator.generate_markdown_report(analysis)
        
        # 생성된 파일들 확인
        print(f"\n생성된 파일들:")
        if os.path.exists(text_report_path):
            file_size = os.path.getsize(text_report_path)
            print(f"- {text_report_path} ({file_size} bytes)")
        
        if os.path.exists(markdown_report_path):
            file_size = os.path.getsize(markdown_report_path)
            print(f"- {markdown_report_path} ({file_size} bytes)")
        
        print("\n" + "=" * 80)
        print("모든 테스트 완료!")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)