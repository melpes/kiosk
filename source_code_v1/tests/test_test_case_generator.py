"""
TestCaseGenerator 클래스에 대한 기본 테스트
"""

import unittest
from unittest.mock import Mock, patch
from src.testing.test_case_generator import TestCaseGenerator
from src.models.testing_models import TestCase, TestCaseCategory
from src.models.conversation_models import IntentType


class TestTestCaseGenerator(unittest.TestCase):
    """TestCaseGenerator 테스트 클래스"""
    
    def setUp(self):
        """각 테스트 메서드 실행 전 설정"""
        self.generator = TestCaseGenerator()
    
    def test_initialization(self):
        """초기화 테스트"""
        self.assertIsNotNone(self.generator)
        self.assertTrue(hasattr(self.generator, 'slang_mappings'))
        self.assertTrue(hasattr(self.generator, 'menu_items'))
        self.assertGreater(len(self.generator.slang_mappings), 0)
        self.assertGreater(len(self.generator.menu_items), 0)
    
    def test_slang_mappings_content(self):
        """은어 매핑 내용 테스트"""
        # 주요 은어들이 포함되어 있는지 확인
        expected_slangs = ["상스치콤", "베토디", "빅맥콤", "치즈버거콤", "맥치킨콤"]
        for slang in expected_slangs:
            assert slang in self.generator.slang_mappings
            assert len(self.generator.slang_mappings[slang]) > 0
    
    def test_generate_slang_cases(self):
        """은어 테스트케이스 생성 테스트"""
        test_cases = self.generator.generate_slang_cases()
        
        # 기본 검증
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
        
        # 카테고리 검증
        assert all(tc.category == TestCaseCategory.SLANG for tc in test_cases)
        
        # 의도 검증 (대부분 ORDER 의도여야 함)
        order_cases = [tc for tc in test_cases if tc.expected_intent == IntentType.ORDER]
        assert len(order_cases) > 0
        
        # ID 유니크성 검증
        ids = [tc.id for tc in test_cases]
        assert len(ids) == len(set(ids))
        
        # 태그 검증
        assert all("slang" in tc.tags for tc in test_cases)
    
    def test_generate_informal_cases(self):
        """반말 테스트케이스 생성 테스트"""
        test_cases = self.generator.generate_informal_cases()
        
        # 기본 검증
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
        
        # 카테고리 검증
        assert all(tc.category == TestCaseCategory.INFORMAL for tc in test_cases)
        
        # 다양한 의도 포함 확인
        intents = set(tc.expected_intent for tc in test_cases)
        assert IntentType.ORDER in intents
        
        # 반말 패턴 확인
        informal_patterns = ["줘", "할게", "시킬게", "먹을래", "달라고"]
        has_informal = any(
            any(pattern in tc.input_text for pattern in informal_patterns)
            for tc in test_cases
        )
        assert has_informal
        
        # 태그 검증
        assert all("informal" in tc.tags for tc in test_cases)
    
    def test_generate_complex_intent_cases(self):
        """복합 의도 테스트케이스 생성 테스트"""
        test_cases = self.generator.generate_complex_intent_cases()
        
        # 기본 검증
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
        
        # 카테고리 검증
        assert all(tc.category == TestCaseCategory.COMPLEX for tc in test_cases)
        
        # 복합 의도 특성 확인 (낮은 신뢰도 임계값)
        low_confidence_cases = [tc for tc in test_cases if tc.expected_confidence_min <= 0.5]
        assert len(low_confidence_cases) > 0
        
        # 복합 태그 확인
        complex_tagged = [tc for tc in test_cases if "complex" in tc.tags]
        assert len(complex_tagged) == len(test_cases)
        
        # 다중 태그 확인 (복합 의도는 여러 태그를 가져야 함)
        multi_tag_cases = [tc for tc in test_cases if len(tc.tags) > 2]
        assert len(multi_tag_cases) > 0
    
    def test_generate_normal_cases(self):
        """일반 테스트케이스 생성 테스트"""
        test_cases = self.generator.generate_normal_cases()
        
        # 기본 검증
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
        
        # 카테고리 검증
        assert all(tc.category == TestCaseCategory.NORMAL for tc in test_cases)
        
        # 높은 신뢰도 임계값 확인 (일반 케이스는 높은 신뢰도를 가져야 함)
        high_confidence_cases = [tc for tc in test_cases if tc.expected_confidence_min >= 0.7]
        assert len(high_confidence_cases) > 0
        
        # 다양한 의도 포함 확인
        intents = set(tc.expected_intent for tc in test_cases)
        expected_intents = {IntentType.ORDER, IntentType.MODIFY, IntentType.CANCEL, 
                          IntentType.INQUIRY, IntentType.PAYMENT}
        assert len(intents.intersection(expected_intents)) >= 3
    
    def test_generate_edge_cases(self):
        """엣지 케이스 테스트케이스 생성 테스트"""
        test_cases = self.generator.generate_edge_cases()
        
        # 기본 검증
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
        
        # 카테고리 검증
        assert all(tc.category == TestCaseCategory.EDGE for tc in test_cases)
        
        # 빈 입력 케이스 확인
        empty_cases = [tc for tc in test_cases if tc.input_text == ""]
        assert len(empty_cases) > 0
        
        # UNKNOWN 의도 케이스 확인
        unknown_cases = [tc for tc in test_cases if tc.expected_intent == IntentType.UNKNOWN]
        assert len(unknown_cases) > 0
        
        # 낮은 신뢰도 케이스 확인
        low_confidence_cases = [tc for tc in test_cases if tc.expected_confidence_min <= 0.3]
        assert len(low_confidence_cases) > 0
    
    def test_generate_mcdonald_test_cases(self):
        """전체 맥도날드 테스트케이스 생성 테스트"""
        test_cases = self.generator.generate_mcdonald_test_cases()
        
        # 기본 검증
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)
        
        # 모든 카테고리 포함 확인
        categories = set(tc.category for tc in test_cases)
        expected_categories = {
            TestCaseCategory.SLANG, TestCaseCategory.INFORMAL,
            TestCaseCategory.COMPLEX, TestCaseCategory.NORMAL,
            TestCaseCategory.EDGE
        }
        assert categories == expected_categories
        
        # ID 유니크성 검증
        ids = [tc.id for tc in test_cases]
        assert len(ids) == len(set(ids))
        
        # 각 카테고리별 최소 개수 확인
        category_counts = {}
        for tc in test_cases:
            category_counts[tc.category] = category_counts.get(tc.category, 0) + 1
        
        for category in expected_categories:
            assert category_counts[category] > 0
    
    def test_generate_custom_test_case(self):
        """커스텀 테스트케이스 생성 테스트"""
        custom_case = self.generator.generate_custom_test_case(
            input_text="테스트 입력",
            expected_intent=IntentType.ORDER,
            category=TestCaseCategory.NORMAL,
            description="테스트 설명",
            tags=["test", "custom"],
            expected_confidence_min=0.8
        )
        
        # 기본 검증
        assert isinstance(custom_case, TestCase)
        assert custom_case.input_text == "테스트 입력"
        assert custom_case.expected_intent == IntentType.ORDER
        assert custom_case.category == TestCaseCategory.NORMAL
        assert custom_case.description == "테스트 설명"
        assert custom_case.tags == ["test", "custom"]
        assert custom_case.expected_confidence_min == 0.8
        assert custom_case.id.startswith("custom_")
    
    def test_test_case_structure(self):
        """생성된 테스트케이스 구조 검증"""
        test_cases = self.generator.generate_slang_cases()[:5]  # 처음 5개만 테스트
        
        for tc in test_cases:
            # 필수 필드 확인
            assert tc.id is not None and len(tc.id) > 0
            assert tc.input_text is not None
            assert tc.expected_intent is not None
            assert tc.category is not None
            assert tc.description is not None and len(tc.description) > 0
            assert isinstance(tc.tags, list)
            assert isinstance(tc.expected_confidence_min, (int, float))
            assert 0.0 <= tc.expected_confidence_min <= 1.0
    
    def test_slang_coverage(self):
        """은어 커버리지 테스트"""
        test_cases = self.generator.generate_slang_cases()
        
        # 주요 은어들이 테스트케이스에 포함되어 있는지 확인
        all_input_texts = " ".join(tc.input_text for tc in test_cases)
        
        key_slangs = ["상스치콤", "베토디", "빅맥콤", "감튀", "맥너겟"]
        for slang in key_slangs:
            assert slang in all_input_texts, f"은어 '{slang}'이 테스트케이스에 포함되지 않음"
    
    def test_menu_item_coverage(self):
        """메뉴 아이템 커버리지 테스트"""
        test_cases = self.generator.generate_normal_cases()
        
        # 주요 메뉴들이 테스트케이스에 포함되어 있는지 확인
        all_input_texts = " ".join(tc.input_text for tc in test_cases)
        
        key_menus = ["빅맥", "치즈버거", "맥치킨", "감자튀김", "코카콜라"]
        covered_menus = sum(1 for menu in key_menus if menu in all_input_texts)
        
        # 최소 60% 이상의 주요 메뉴가 커버되어야 함
        coverage_ratio = covered_menus / len(key_menus)
        self.assertGreaterEqual(coverage_ratio, 0.6, f"메뉴 커버리지가 낮음: {coverage_ratio:.2%}")
    
    @patch('src.testing.test_case_generator.get_logger')
    def test_logging(self, mock_get_logger):
        """로깅 기능 테스트"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        generator = TestCaseGenerator()
        test_cases = generator.generate_mcdonald_test_cases()
        
        # 로거가 호출되었는지 확인
        assert mock_get_logger.called
        assert mock_logger.info.called
        
        # 로그 메시지 확인
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("테스트케이스 생성" in msg for msg in log_calls)
        assert any("생성 완료" in msg for msg in log_calls)
    
    def test_performance(self):
        """성능 테스트 (기본적인 실행 시간 확인)"""
        import time
        
        start_time = time.time()
        test_cases = self.generator.generate_mcdonald_test_cases()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 5초 이내에 완료되어야 함
        assert execution_time < 5.0, f"테스트케이스 생성이 너무 오래 걸림: {execution_time:.2f}초"
        
        # 최소한의 테스트케이스가 생성되어야 함
        assert len(test_cases) >= 50, f"생성된 테스트케이스가 너무 적음: {len(test_cases)}개"