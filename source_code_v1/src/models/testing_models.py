"""
테스트 관련 데이터 모델
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime

from .conversation_models import IntentType


class TestCaseCategory(Enum):
    """테스트케이스 카테고리"""
    SLANG = "slang"              # 은어 (상스치콤, 베토디 등)
    INFORMAL = "informal"        # 반말
    COMPLEX = "complex"          # 복합 의도
    NORMAL = "normal"            # 일반적인 케이스
    EDGE = "edge"                # 엣지 케이스


@dataclass
class TestCase:
    """개별 테스트케이스 데이터 모델"""
    id: str                                 # 테스트케이스 ID
    input_text: str                         # 입력 텍스트
    expected_intent: Optional[IntentType]   # 예상 의도
    category: TestCaseCategory              # 카테고리
    description: str                        # 설명
    tags: List[str] = field(default_factory=list)  # 태그들
    expected_entities: Optional[Dict[str, Any]] = None  # 예상 엔티티
    expected_confidence_min: float = 0.0    # 최소 예상 신뢰도
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.id:
            raise ValueError("테스트케이스 ID는 필수입니다")
        
        # 엣지 케이스가 아닌 경우에만 입력 텍스트 검증
        if self.category != TestCaseCategory.EDGE and not self.input_text.strip():
            raise ValueError("입력 텍스트는 필수입니다 (엣지 케이스 제외)")
        
        if not isinstance(self.category, TestCaseCategory):
            raise ValueError("카테고리는 TestCaseCategory 타입이어야 합니다")
        
        if not (0.0 <= self.expected_confidence_min <= 1.0):
            raise ValueError("예상 신뢰도는 0.0과 1.0 사이의 값이어야 합니다")
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'input_text': self.input_text,
            'expected_intent': self.expected_intent.value if self.expected_intent else None,
            'category': self.category.value,
            'description': self.description,
            'tags': self.tags,
            'expected_entities': self.expected_entities,
            'expected_confidence_min': self.expected_confidence_min,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TestResult:
    """개별 테스트 결과"""
    test_case: TestCase                     # 테스트케이스
    system_response: str                    # 시스템 응답
    detected_intent: IntentType             # 감지된 의도
    processing_time: float                  # 처리 시간 (초)
    success: bool                           # 성공 여부
    error_message: Optional[str] = None     # 오류 메시지
    confidence_score: float = 0.0           # 신뢰도 점수
    detected_entities: Optional[Dict[str, Any]] = None  # 감지된 엔티티
    session_id: Optional[str] = None        # 세션 ID
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 추가된 필드들
    input_text: str = ""                    # 입력 텍스트 (명시적 저장)
    output_text: str = ""                   # 출력 텍스트 (명시적 저장)
    
    def __post_init__(self):
        """데이터 검증"""
        if self.processing_time < 0:
            raise ValueError("처리 시간은 음수일 수 없습니다")
        
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("신뢰도 점수는 0.0과 1.0 사이의 값이어야 합니다")
    
    @property
    def intent_matches(self) -> bool:
        """의도가 예상과 일치하는지 확인"""
        if self.test_case.expected_intent is None:
            return True  # 예상 의도가 없으면 항상 성공
        return self.detected_intent == self.test_case.expected_intent
    
    @property
    def confidence_meets_threshold(self) -> bool:
        """신뢰도가 임계값을 만족하는지 확인"""
        return self.confidence_score >= self.test_case.expected_confidence_min
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'test_case': self.test_case.to_dict(),
            'system_response': self.system_response,
            'detected_intent': self.detected_intent.value,
            'processing_time': self.processing_time,
            'success': self.success,
            'error_message': self.error_message,
            'confidence_score': self.confidence_score,
            'detected_entities': self.detected_entities,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'intent_matches': self.intent_matches,
            'confidence_meets_threshold': self.confidence_meets_threshold,
            'input_text': self.input_text,
            'output_text': self.output_text
        }


@dataclass
class TestResults:
    """테스트 결과 컬렉션"""
    session_id: str                         # 테스트 세션 ID
    results: List[TestResult] = field(default_factory=list)  # 개별 결과들
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    def add_result(self, result: TestResult):
        """결과 추가"""
        self.results.append(result)
    
    def finish(self):
        """테스트 완료 처리"""
        self.end_time = datetime.now()
    
    @property
    def total_tests(self) -> int:
        """전체 테스트 수"""
        return len(self.results)
    
    @property
    def successful_tests(self) -> int:
        """성공한 테스트 수"""
        return sum(1 for result in self.results if result.success)
    
    @property
    def success_rate(self) -> float:
        """성공률"""
        if self.total_tests == 0:
            return 0.0
        return self.successful_tests / self.total_tests
    
    @property
    def average_processing_time(self) -> float:
        """평균 처리 시간"""
        if not self.results:
            return 0.0
        return sum(result.processing_time for result in self.results) / len(self.results)
    
    @property
    def total_duration(self) -> float:
        """전체 테스트 소요 시간 (초)"""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
    
    def get_results_by_category(self, category: TestCaseCategory) -> List[TestResult]:
        """카테고리별 결과 조회"""
        return [result for result in self.results if result.test_case.category == category]
    
    def get_failed_results(self) -> List[TestResult]:
        """실패한 결과들 조회"""
        return [result for result in self.results if not result.success]
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'session_id': self.session_id,
            'total_tests': self.total_tests,
            'successful_tests': self.successful_tests,
            'success_rate': self.success_rate,
            'average_processing_time': self.average_processing_time,
            'total_duration': self.total_duration,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'results': [result.to_dict() for result in self.results]
        }


@dataclass
class TestAnalysis:
    """테스트 결과 분석 데이터"""
    total_tests: int                        # 전체 테스트 수
    success_rate: float                     # 성공률
    average_processing_time: float          # 평균 처리 시간
    intent_accuracy: Dict[str, float]       # 의도별 정확도
    category_performance: Dict[str, float]  # 카테고리별 성능
    error_summary: Dict[str, int]           # 오류 요약
    detailed_results: List[TestResult]      # 상세 결과
    confidence_distribution: Dict[str, int] = field(default_factory=dict)  # 신뢰도 분포
    processing_time_stats: Dict[str, float] = field(default_factory=dict)  # 처리 시간 통계
    
    def __post_init__(self):
        """분석 데이터 계산"""
        if self.detailed_results:
            self._calculate_confidence_distribution()
            self._calculate_processing_time_stats()
    
    def _calculate_confidence_distribution(self):
        """신뢰도 분포 계산"""
        ranges = {
            'very_high': 0,  # 0.9 이상
            'high': 0,       # 0.7-0.9
            'medium': 0,     # 0.5-0.7
            'low': 0         # 0.5 미만
        }
        
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
        """처리 시간 통계 계산"""
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
        """표준편차 계산"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5


@dataclass
class TestConfiguration:
    """테스트 설정"""
    include_slang: bool = True              # 은어 테스트 포함
    include_informal: bool = True           # 반말 테스트 포함
    include_complex: bool = True            # 복합 의도 테스트 포함
    include_edge_cases: bool = True         # 엣지 케이스 포함
    max_tests_per_category: int = 50        # 카테고리당 최대 테스트 수
    output_directory: str = "test_results"  # 출력 디렉토리
    generate_markdown: bool = True          # 마크다운 보고서 생성
    generate_text: bool = True              # 텍스트 보고서 생성
    timeout_seconds: float = 30.0           # 테스트 타임아웃 (초)
    retry_failed_tests: bool = False        # 실패한 테스트 재시도
    parallel_execution: bool = False        # 병렬 실행 (현재 미지원)
    
    def __post_init__(self):
        """설정 검증"""
        if self.max_tests_per_category <= 0:
            raise ValueError("카테고리당 최대 테스트 수는 양수여야 합니다")
        
        if self.timeout_seconds <= 0:
            raise ValueError("타임아웃은 양수여야 합니다")
        
        if not self.output_directory.strip():
            raise ValueError("출력 디렉토리는 비어있을 수 없습니다")