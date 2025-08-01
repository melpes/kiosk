"""
테스트케이스 관리 및 실행을 담당하는 메인 클래스
"""

from typing import List, Optional
from pathlib import Path

from .test_case_generator import TestCaseGenerator
from .test_runner import TestRunner
from ..models.testing_models import TestCase, TestResults, TestConfiguration, TestCaseCategory
from ..logger import get_logger
from ..utils.env_loader import get_test_config


class TestCaseManager:
    """테스트케이스 관리 및 실행을 담당하는 메인 클래스"""
    
    def __init__(self, pipeline, config: Optional[TestConfiguration] = None):
        """
        TestCaseManager 초기화
        
        Args:
            pipeline: VoiceKioskPipeline 인스턴스
            config: 테스트 설정 (선택사항)
        """
        self.pipeline = pipeline
        
        # 환경 변수에서 설정 로드 (강제 새로고침)
        if config is None:
            # 환경 변수 다시 로드
            from ..utils.env_loader import load_env_file
            load_env_file()
            
            env_config = get_test_config()
            config = TestConfiguration(
                include_slang=env_config.get('include_slang', True),
                include_informal=env_config.get('include_informal', True),
                include_complex=env_config.get('include_complex', True),
                include_edge_cases=env_config.get('include_edge_cases', True),
                max_tests_per_category=env_config.get('max_tests_per_category', 20)
            )
        
        self.config = config
        self.logger = get_logger(__name__)
        
        # 하위 모듈 초기화
        self.generator = TestCaseGenerator()
        self.runner = TestRunner(pipeline)
        
        # 생성된 테스트케이스 캐시
        self._cached_test_cases: Optional[List[TestCase]] = None
        
        self.logger.info("TestCaseManager 초기화 완료")
        self.logger.info(f"테스트 설정: 카테고리당 최대 {self.config.max_tests_per_category}개")
        self.logger.info(f"엣지 케이스 포함: {self.config.include_edge_cases}")
    
    def generate_test_cases(self, force_regenerate: bool = False) -> List[TestCase]:
        """
        테스트케이스 생성
        
        Args:
            force_regenerate: 강제 재생성 여부
            
        Returns:
            List[TestCase]: 생성된 테스트케이스 목록
        """
        # 캐시된 테스트케이스가 있고 강제 재생성이 아니면 캐시 반환
        if self._cached_test_cases and not force_regenerate:
            self.logger.info(f"캐시된 테스트케이스 반환: {len(self._cached_test_cases)}개")
            return self._cached_test_cases
        
        self.logger.info("테스트케이스 생성 시작")
        
        try:
            # 전체 테스트케이스 생성
            all_test_cases = self.generator.generate_mcdonald_test_cases()
            
            # 설정에 따라 필터링
            filtered_test_cases = self._filter_test_cases_by_config(all_test_cases)
            
            # 카테고리별 개수 제한 적용
            limited_test_cases = self._limit_test_cases_per_category(filtered_test_cases)
            
            # 캐시에 저장
            self._cached_test_cases = limited_test_cases
            
            # 결과 로그
            self._log_test_case_summary(limited_test_cases)
            
            return limited_test_cases
            
        except Exception as e:
            self.logger.error(f"테스트케이스 생성 실패: {e}")
            raise
    
    def run_all_tests(self, test_cases: Optional[List[TestCase]] = None) -> TestResults:
        """
        모든 테스트 실행
        
        Args:
            test_cases: 실행할 테스트케이스 목록 (None이면 자동 생성)
            
        Returns:
            TestResults: 테스트 실행 결과
        """
        try:
            # 테스트케이스가 제공되지 않으면 생성
            if test_cases is None:
                print("🔄 테스트케이스 생성 중...")
                test_cases = self.generate_test_cases()
            
            self.logger.info(f"전체 테스트 실행 시작: {len(test_cases)}개 테스트케이스")
            print(f"\n📋 테스트 실행 준비:")
            print(f"  - 총 테스트케이스: {len(test_cases)}개")
            
            # 카테고리별 개수 표시
            category_counts = {}
            for test_case in test_cases:
                category = test_case.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            for category, count in category_counts.items():
                print(f"  - {category}: {count}개")
            
            # 테스트 스위트 실행
            results = self.runner.run_test_suite(test_cases)
            
            # 실행 완료 메시지
            print(f"\n🎉 전체 테스트 실행 완료!")
            print(f"📊 최종 결과:")
            print(f"  - 총 테스트: {results.total_tests}개")
            print(f"  - 성공: {results.successful_tests}개")
            print(f"  - 실패: {results.total_tests - results.successful_tests}개")
            print(f"  - 성공률: {results.success_rate*100:.1f}%")
            print(f"  - 평균 처리시간: {results.average_processing_time:.3f}초")
            print(f"  - 총 소요시간: {results.total_duration:.1f}초")
            
            self.logger.info("전체 테스트 실행 완료")
            return results
            
        except Exception as e:
            self.logger.error(f"전체 테스트 실행 실패: {e}")
            print(f"❌ 테스트 실행 중 오류 발생: {e}")
            raise
    
    def run_tests_by_category(self, category: TestCaseCategory) -> TestResults:
        """
        카테고리별 테스트 실행
        
        Args:
            category: 실행할 테스트 카테고리
            
        Returns:
            TestResults: 테스트 실행 결과
        """
        try:
            # 전체 테스트케이스 생성
            all_test_cases = self.generate_test_cases()
            
            # 카테고리별 필터링
            category_test_cases = [
                test_case for test_case in all_test_cases 
                if test_case.category == category
            ]
            
            if not category_test_cases:
                self.logger.warning(f"카테고리 '{category.value}'에 해당하는 테스트케이스가 없습니다")
                # 빈 결과 반환
                from ..models.testing_models import TestResults
                import uuid
                empty_results = TestResults(session_id=f"empty_{uuid.uuid4().hex[:8]}")
                empty_results.finish()
                return empty_results
            
            self.logger.info(f"카테고리 '{category.value}' 테스트 실행: {len(category_test_cases)}개")
            
            # 테스트 실행
            results = self.runner.run_test_suite(category_test_cases)
            
            return results
            
        except Exception as e:
            self.logger.error(f"카테고리별 테스트 실행 실패: {e}")
            raise
    
    def run_single_test_by_id(self, test_id: str) -> Optional[TestResults]:
        """
        ID로 단일 테스트 실행
        
        Args:
            test_id: 테스트케이스 ID
            
        Returns:
            TestResults: 테스트 실행 결과 (찾지 못하면 None)
        """
        try:
            # 전체 테스트케이스에서 ID로 검색
            all_test_cases = self.generate_test_cases()
            target_test_case = None
            
            for test_case in all_test_cases:
                if test_case.id == test_id:
                    target_test_case = test_case
                    break
            
            if not target_test_case:
                self.logger.warning(f"테스트케이스 ID '{test_id}'를 찾을 수 없습니다")
                return None
            
            self.logger.info(f"단일 테스트 실행: {test_id}")
            
            # 단일 테스트 실행
            results = self.runner.run_test_suite([target_test_case])
            
            return results
            
        except Exception as e:
            self.logger.error(f"단일 테스트 실행 실패: {e}")
            raise
    
    def get_test_case_summary(self) -> dict:
        """테스트케이스 요약 정보 반환"""
        try:
            test_cases = self.generate_test_cases()
            
            # 카테고리별 개수 계산
            category_counts = {}
            for category in TestCaseCategory:
                count = sum(1 for tc in test_cases if tc.category == category)
                category_counts[category.value] = count
            
            # 태그별 개수 계산
            tag_counts = {}
            for test_case in test_cases:
                for tag in test_case.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # 의도별 개수 계산
            intent_counts = {}
            for test_case in test_cases:
                if test_case.expected_intent:
                    intent = test_case.expected_intent.value
                    intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            summary = {
                'total_test_cases': len(test_cases),
                'category_counts': category_counts,
                'tag_counts': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),  # 상위 10개
                'intent_counts': intent_counts,
                'config': {
                    'include_slang': self.config.include_slang,
                    'include_informal': self.config.include_informal,
                    'include_complex': self.config.include_complex,
                    'include_edge_cases': self.config.include_edge_cases,
                    'max_tests_per_category': self.config.max_tests_per_category
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"테스트케이스 요약 생성 실패: {e}")
            return {'error': str(e)}
    
    def save_test_cases_to_file(self, file_path: str, test_cases: Optional[List[TestCase]] = None):
        """테스트케이스를 파일로 저장"""
        try:
            if test_cases is None:
                test_cases = self.generate_test_cases()
            
            import json
            
            # 테스트케이스를 딕셔너리로 변환
            test_cases_data = [tc.to_dict() for tc in test_cases]
            
            # 파일로 저장
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(test_cases_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"테스트케이스 파일 저장 완료: {file_path} ({len(test_cases)}개)")
            
        except Exception as e:
            self.logger.error(f"테스트케이스 파일 저장 실패: {e}")
            raise
    
    def load_test_cases_from_file(self, file_path: str) -> List[TestCase]:
        """파일에서 테스트케이스 로드"""
        try:
            import json
            from ..models.conversation_models import IntentType
            
            with open(file_path, 'r', encoding='utf-8') as f:
                test_cases_data = json.load(f)
            
            test_cases = []
            for data in test_cases_data:
                # 딕셔너리에서 TestCase 객체로 변환
                test_case = TestCase(
                    id=data['id'],
                    input_text=data['input_text'],
                    expected_intent=IntentType(data['expected_intent']) if data['expected_intent'] else None,
                    category=TestCaseCategory(data['category']),
                    description=data['description'],
                    tags=data['tags'],
                    expected_entities=data.get('expected_entities'),
                    expected_confidence_min=data['expected_confidence_min']
                )
                test_cases.append(test_case)
            
            self.logger.info(f"테스트케이스 파일 로드 완료: {file_path} ({len(test_cases)}개)")
            return test_cases
            
        except Exception as e:
            self.logger.error(f"테스트케이스 파일 로드 실패: {e}")
            raise
    
    def _filter_test_cases_by_config(self, test_cases: List[TestCase]) -> List[TestCase]:
        """설정에 따라 테스트케이스 필터링"""
        filtered_cases = []
        
        for test_case in test_cases:
            include = True
            
            # 카테고리별 포함 여부 확인
            if test_case.category == TestCaseCategory.SLANG and not self.config.include_slang:
                include = False
            elif test_case.category == TestCaseCategory.INFORMAL and not self.config.include_informal:
                include = False
            elif test_case.category == TestCaseCategory.COMPLEX and not self.config.include_complex:
                include = False
            elif test_case.category == TestCaseCategory.EDGE and not self.config.include_edge_cases:
                include = False
            
            if include:
                filtered_cases.append(test_case)
        
        self.logger.info(f"설정 필터링 완료: {len(test_cases)} -> {len(filtered_cases)}개")
        return filtered_cases
    
    def _limit_test_cases_per_category(self, test_cases: List[TestCase]) -> List[TestCase]:
        """카테고리별 테스트케이스 개수 제한"""
        if self.config.max_tests_per_category <= 0:
            return test_cases
        
        # 카테고리별로 그룹화
        category_groups = {}
        for test_case in test_cases:
            category = test_case.category
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(test_case)
        
        # 각 카테고리에서 최대 개수만큼 선택
        limited_cases = []
        for category, cases in category_groups.items():
            if len(cases) <= self.config.max_tests_per_category:
                limited_cases.extend(cases)
            else:
                # 앞에서부터 최대 개수만큼 선택
                limited_cases.extend(cases[:self.config.max_tests_per_category])
                self.logger.info(f"카테고리 '{category.value}' 제한: {len(cases)} -> {self.config.max_tests_per_category}개")
        
        return limited_cases
    
    def _log_test_case_summary(self, test_cases: List[TestCase]):
        """테스트케이스 요약 로그 출력"""
        total = len(test_cases)
        
        # 카테고리별 개수
        category_counts = {}
        for category in TestCaseCategory:
            count = sum(1 for tc in test_cases if tc.category == category)
            if count > 0:
                category_counts[category.value] = count
        
        self.logger.info(f"테스트케이스 생성 완료: 총 {total}개")
        for category, count in category_counts.items():
            self.logger.info(f"  - {category}: {count}개")
    
    def update_config(self, new_config: TestConfiguration):
        """테스트 설정 업데이트"""
        self.config = new_config
        # 캐시 무효화
        self._cached_test_cases = None
        self.logger.info("테스트 설정 업데이트 완료")
    
    def get_manager_status(self) -> dict:
        """매니저 상태 정보 반환"""
        return {
            'config': {
                'include_slang': self.config.include_slang,
                'include_informal': self.config.include_informal,
                'include_complex': self.config.include_complex,
                'include_edge_cases': self.config.include_edge_cases,
                'max_tests_per_category': self.config.max_tests_per_category,
                'output_directory': self.config.output_directory
            },
            'cached_test_cases_count': len(self._cached_test_cases) if self._cached_test_cases else 0,
            'runner_status': self.runner.get_runner_status()
        }