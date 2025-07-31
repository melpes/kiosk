"""
테스트 시스템 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models.testing_models import TestCase, TestResult, TestResults, TestAnalysis, TestConfiguration


class ITestCaseGenerator(ABC):
    """테스트케이스 생성기 인터페이스"""
    
    @abstractmethod
    def generate_test_cases(self, config: TestConfiguration) -> List[TestCase]:
        """테스트케이스 생성"""
        pass
    
    @abstractmethod
    def generate_slang_cases(self) -> List[TestCase]:
        """은어 테스트케이스 생성"""
        pass
    
    @abstractmethod
    def generate_informal_cases(self) -> List[TestCase]:
        """반말 테스트케이스 생성"""
        pass
    
    @abstractmethod
    def generate_complex_intent_cases(self) -> List[TestCase]:
        """복합 의도 테스트케이스 생성"""
        pass


class ITestRunner(ABC):
    """테스트 실행기 인터페이스"""
    
    @abstractmethod
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """단일 테스트 실행"""
        pass
    
    @abstractmethod
    def run_batch_tests(self, test_cases: List[TestCase]) -> TestResults:
        """배치 테스트 실행"""
        pass
    
    @abstractmethod
    def setup_test_session(self) -> str:
        """테스트 세션 설정"""
        pass
    
    @abstractmethod
    def cleanup_test_session(self, session_id: str):
        """테스트 세션 정리"""
        pass


class IResultAnalyzer(ABC):
    """결과 분석기 인터페이스"""
    
    @abstractmethod
    def analyze_results(self, results: TestResults) -> TestAnalysis:
        """결과 분석"""
        pass
    
    @abstractmethod
    def calculate_intent_accuracy(self, results: List[TestResult]) -> Dict[str, float]:
        """의도별 정확도 계산"""
        pass
    
    @abstractmethod
    def calculate_category_performance(self, results: List[TestResult]) -> Dict[str, float]:
        """카테고리별 성능 계산"""
        pass


class IReportGenerator(ABC):
    """보고서 생성기 인터페이스"""
    
    @abstractmethod
    def generate_text_report(self, analysis: TestAnalysis, output_path: str):
        """텍스트 보고서 생성"""
        pass
    
    @abstractmethod
    def generate_markdown_report(self, analysis: TestAnalysis, output_path: str):
        """마크다운 보고서 생성"""
        pass
    
    @abstractmethod
    def generate_summary_report(self, analysis: TestAnalysis) -> str:
        """요약 보고서 생성"""
        pass