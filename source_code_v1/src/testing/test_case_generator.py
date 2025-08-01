"""
맥도날드 키오스크 환경에 특화된 테스트케이스 생성기
"""

import uuid
from typing import List, Dict, Any
from datetime import datetime

from ..models.testing_models import TestCase, TestCaseCategory
from ..models.conversation_models import IntentType
from ..logger import get_logger
from ..utils.env_loader import get_test_config


import json
import os
from pathlib import Path

class TestCaseGenerator:
    """맥도날드 키오스크 환경에 특화된 테스트케이스 생성"""
    
    def __init__(self, config_file_path=None):
        self.logger = get_logger(__name__)
        
        # 환경 변수에서 테스트 설정 로드
        self.test_config = get_test_config()
        
        # 설정 파일 경로 설정
        if config_file_path is None:
            # test_config 디렉토리의 기본 설정 파일 사용
            project_root = Path(__file__).parent.parent.parent
            config_file_path = project_root / "test_config" / "test_data_config.json"
        
        # 설정 파일에서 데이터 로드
        self.config_data = self._load_config(config_file_path)
        
        # 설정 데이터에서 각 항목들 추출
        self.slang_mappings = self.config_data.get("slang_mappings", {})
        self.menu_items = self.config_data.get("menu_items", [])
        self.quantity_expressions = self.config_data.get("quantity_expressions", [])
        self.option_expressions = self.config_data.get("option_expressions", [])
        self.informal_patterns = self.config_data.get("informal_patterns", [])
        self.complex_patterns = self.config_data.get("complex_patterns", [])
        self.edge_cases = self.config_data.get("edge_cases", [])
        self.test_config_data = self.config_data.get("test_config", {})
        
        self.logger.info(f"테스트 데이터 설정 파일 로드 완료: {config_file_path}")
        self.logger.info(f"은어 매핑: {len(self.slang_mappings)}개, 메뉴: {len(self.menu_items)}개")
        self.logger.info(f"환경 변수 설정: 엣지 케이스 포함={self.test_config.get('include_edge_cases', True)}")
    
    def _load_config(self, config_file_path):
        """설정 파일 로드"""
        try:
            if not os.path.exists(config_file_path):
                self.logger.warning(f"설정 파일이 존재하지 않습니다: {config_file_path}")
                self.logger.info("기본 설정으로 초기화합니다.")
                return self._get_default_config()
            
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.logger.info(f"설정 파일 로드 성공: {config_file_path}")
                return config_data
                
        except Exception as e:
            self.logger.error(f"설정 파일 로드 실패: {e}")
            self.logger.info("기본 설정으로 초기화합니다.")
            return self._get_default_config()
    
    def _get_default_config(self):
        """기본 설정 반환"""
        return {
            "slang_mappings": {
                "상스치콤": "상하이 스파이시 치킨버거 콤보",
                "베토디": "베이컨 토마토 디럭스",
                "빅맥콤": "빅맥 콤보",
                "치즈버거콤": "치즈버거 콤보",
                "맥치킨콤": "맥치킨 콤보",
                "불고기콤": "불고기버거 콤보",
                "새우콤": "새우버거 콤보",
                "치킨맥너겟": "치킨 맥너겟",
                "맥플러리": "맥플러리",
                "아이스아메": "아이스 아메리카노",
                "핫아메": "핫 아메리카노",
                "콜라": "코카콜라",
                "사이다": "스프라이트",
                "감튀": "감자튀김",
                "치즈스틱": "모짜렐라 치즈스틱",
                "더블치콤": "더블치즈버거 콤보",
                "쿼터파콤": "쿼터파운더 콤보",
                "맥스파이시콤": "맥스파이시 상하이버거 콤보",
                "치킨버거콤": "맥치킨 콤보",
                "새우버거콤": "새우버거 콤보",
                "맥너겟": "치킨 맥너겟",
                "너겟": "치킨 맥너겟",
                "아메": "아메리카노",
                "라떼": "카페라떼",
                "프라푸치노": "프라페",
                "맥카페": "맥카페 음료",
                "해피밀": "해피밀",
                "키즈밀": "해피밀"
            },
            "menu_items": [
                "빅맥", "상하이 스파이시 치킨버거", "베이컨 토마토 디럭스",
                "치즈버거", "맥치킨", "불고기버거", "새우버거",
                "더블치즈버거", "쿼터파운더", "맥스파이시 상하이버거",
                "치킨 맥너겟", "감자튀김", "코카콜라", "스프라이트",
                "아이스 아메리카노", "핫 아메리카노", "카페라떼", "맥플러리",
                "해피밀", "애플파이", "선데이", "맥카페 음료"
            ],
            "quantity_expressions": [
                "한 개", "하나", "1개", "두 개", "둘", "2개", "세 개", "셋", "3개",
                "네 개", "넷", "4개", "다섯 개", "5개"
            ],
            "option_expressions": [
                "라지로", "미디움으로", "스몰로", "업사이즈", "세트로", "콤보로",
                "매운맛으로", "순한맛으로", "얼음 많이", "얼음 적게", "뜨겁게", "차갑게"
            ],
            "informal_patterns": [
                "{menu} 줘",
                "{menu} 하나 줘",
                "{menu} 주문할게",
                "{menu} 시킬게",
                "{menu} 먹을래",
                "나 {menu} 먹고 싶어",
                "{menu} 달라고",
                "{menu} 가져다줘"
            ],
            "complex_patterns": [
                "빅맥 주문하고 치즈버거는 취소해주세요",
                "상스치콤 하나 주세요, 그리고 아까 주문한 감자튀김 빼주세요",
                "치즈버거를 빅맥으로 바꾸고 콜라도 추가해주세요",
                "맥치킨을 라지 세트로 업그레이드하고 아이스크림도 하나 주세요"
            ],
            "edge_cases": [
                "",
                "아아아아아",
                "123456789",
                "피자 주문하겠습니다",
                "초밥 두 개 주세요",
                "빅맥!!! 주세요@@@",
                "치즈버거... 하나... 주세요...",
                "빅맥 많이 주세요"
            ],
            "test_config": {
                "max_tests_per_category": 50,
                "include_slang": True,
                "include_informal": True,
                "include_complex": True,
                "include_edge_cases": True,
                "timeout_seconds": 30
            }
        }
    
    def generate_mcdonald_test_cases(self) -> List[TestCase]:
        """맥도날드 키오스크 환경에 특화된 전체 테스트케이스 생성"""
        self.logger.info("맥도날드 특화 테스트케이스 생성 시작")
        
        all_test_cases = []
        
        # 환경 변수 설정에 따라 카테고리별 테스트케이스 생성
        if self.test_config.get('include_slang', True):
            self.logger.info("은어 테스트케이스 생성 중...")
            all_test_cases.extend(self.generate_slang_cases())
        
        if self.test_config.get('include_informal', True):
            self.logger.info("반말 테스트케이스 생성 중...")
            all_test_cases.extend(self.generate_informal_cases())
        
        if self.test_config.get('include_complex', True):
            self.logger.info("복합 의도 테스트케이스 생성 중...")
            all_test_cases.extend(self.generate_complex_intent_cases())
        
        # 일반 테스트케이스는 항상 생성
        self.logger.info("일반 테스트케이스 생성 중...")
        all_test_cases.extend(self.generate_normal_cases())
        
        if self.test_config.get('include_edge_cases', True):
            self.logger.info("엣지 케이스 생성 중...")
            all_test_cases.extend(self.generate_edge_cases())
        else:
            self.logger.info("엣지 케이스 제외됨 (환경 변수 설정)")
        
        self.logger.info(f"총 {len(all_test_cases)}개의 테스트케이스 생성 완료")
        return all_test_cases
    
    def generate_slang_cases(self) -> List[TestCase]:
        """은어 테스트케이스 생성 ("상스치콤", "베토디" 등)"""
        test_cases = []
        max_tests = self.test_config.get('max_tests_per_category', 50)
        
        # 기본 은어 주문
        for slang, full_name in self.slang_mappings.items():
            if len(test_cases) >= max_tests:
                break
            test_cases.append(TestCase(
                id=f"slang_{len(test_cases)+1:03d}",
                input_text=f"{slang} 주세요",
                expected_intent=IntentType.ORDER,
                category=TestCaseCategory.SLANG,
                description=f"은어 '{slang}' 주문 테스트",
                tags=["slang", "order", "mcdonald"],
                expected_confidence_min=0.7
            ))
        
        # 은어 + 수량
        if len(test_cases) < max_tests:
            slang_items = list(self.slang_mappings.keys())[:5]  # 상위 5개만
            for slang in slang_items:
                if len(test_cases) >= max_tests:
                    break
                for quantity in ["두 개", "3개", "하나"]:
                    if len(test_cases) >= max_tests:
                        break
                    test_cases.append(TestCase(
                        id=f"slang_{len(test_cases)+1:03d}",
                        input_text=f"{slang} {quantity} 주세요",
                        expected_intent=IntentType.ORDER,
                        category=TestCaseCategory.SLANG,
                        description=f"은어 '{slang}' + 수량 주문 테스트",
                        tags=["slang", "order", "quantity"],
                        expected_confidence_min=0.6
                    ))
        
        # 은어 + 옵션
        if len(test_cases) < max_tests:
            for slang in slang_items[:3]:
                if len(test_cases) >= max_tests:
                    break
                for option in ["라지로", "세트로", "콤보로"]:
                    if len(test_cases) >= max_tests:
                        break
                    test_cases.append(TestCase(
                        id=f"slang_{len(test_cases)+1:03d}",
                        input_text=f"{slang} {option} 주세요",
                        expected_intent=IntentType.ORDER,
                        category=TestCaseCategory.SLANG,
                        description=f"은어 '{slang}' + 옵션 주문 테스트",
                        tags=["slang", "order", "option"],
                        expected_confidence_min=0.6
                    ))
        
        # 복합 은어 주문
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"slang_{len(test_cases)+1:03d}",
                    input_text="상스치콤 하나랑 베토디 하나 주세요",
                    expected_intent=IntentType.ORDER,
                    category=TestCaseCategory.SLANG,
                    description="복합 은어 주문 테스트",
                    tags=["slang", "order", "multiple"],
                    expected_confidence_min=0.6
                ),
                TestCase(
                    id=f"slang_{len(test_cases)+1:03d}",
                    input_text="빅맥콤 라지로 하나, 감튀 추가요",
                    expected_intent=IntentType.ORDER,
                    category=TestCaseCategory.SLANG,
                    description="은어 + 옵션 + 추가 주문 테스트",
                    tags=["slang", "order", "option", "additional"],
                    expected_confidence_min=0.5
                )
            ])
        
        self.logger.info(f"은어 테스트케이스 {len(test_cases)}개 생성 (최대 {max_tests}개)")
        return test_cases
    
    def generate_informal_cases(self) -> List[TestCase]:
        """반말 테스트케이스 생성"""
        test_cases = []
        max_tests = self.test_config.get('max_tests_per_category', 50)
        
        # 설정 파일에서 반말 패턴 로드
        informal_patterns = self.informal_patterns
        
        menu_samples = self.menu_items[:8]  # 상위 8개 메뉴만
        
        for i, pattern in enumerate(informal_patterns):
            if len(test_cases) >= max_tests:
                break
            menu = menu_samples[i % len(menu_samples)]
            test_cases.append(TestCase(
                id=f"informal_{len(test_cases)+1:03d}",
                input_text=pattern.format(menu=menu),
                expected_intent=IntentType.ORDER,
                category=TestCaseCategory.INFORMAL,
                description=f"반말 주문 패턴 '{pattern}' 테스트",
                tags=["informal", "order"],
                expected_confidence_min=0.6
            ))
        
        # 반말 + 수량
        if len(test_cases) < max_tests:
            for menu in menu_samples[:4]:
                if len(test_cases) >= max_tests:
                    break
                for quantity in ["두 개", "세 개"]:
                    if len(test_cases) >= max_tests:
                        break
                    test_cases.append(TestCase(
                        id=f"informal_{len(test_cases)+1:03d}",
                        input_text=f"{menu} {quantity} 줘",
                        expected_intent=IntentType.ORDER,
                        category=TestCaseCategory.INFORMAL,
                        description="반말 + 수량 주문 테스트",
                        tags=["informal", "order", "quantity"],
                        expected_confidence_min=0.6
                    ))
        
        # 반말 변경/취소
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"informal_{len(test_cases)+1:03d}",
                    input_text="빅맥 빼줘",
                    expected_intent=IntentType.CANCEL,
                    category=TestCaseCategory.INFORMAL,
                    description="반말 취소 테스트",
                    tags=["informal", "cancel"],
                    expected_confidence_min=0.7
                ),
                TestCase(
                    id=f"informal_{len(test_cases)+1:03d}",
                    input_text="치즈버거로 바꿔줘",
                    expected_intent=IntentType.MODIFY,
                    category=TestCaseCategory.INFORMAL,
                    description="반말 변경 테스트",
                    tags=["informal", "modify"],
                    expected_confidence_min=0.7
                ),
                TestCase(
                    id=f"informal_{len(test_cases)+1:03d}",
                    input_text="결제할게",
                    expected_intent=IntentType.PAYMENT,
                    category=TestCaseCategory.INFORMAL,
                    description="반말 결제 테스트",
                    tags=["informal", "payment"],
                    expected_confidence_min=0.8
                )
            ])
        
        # 반말 문의
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"informal_{len(test_cases)+1:03d}",
                    input_text="뭐 있어?",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.INFORMAL,
                    description="반말 메뉴 문의 테스트",
                    tags=["informal", "inquiry"],
                    expected_confidence_min=0.6
                ),
                TestCase(
                    id=f"informal_{len(test_cases)+1:03d}",
                    input_text="얼마야?",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.INFORMAL,
                    description="반말 가격 문의 테스트",
                    tags=["informal", "inquiry", "price"],
                    expected_confidence_min=0.7
                )
            ])
        
        self.logger.info(f"반말 테스트케이스 {len(test_cases)}개 생성 (최대 {max_tests}개)")
        return test_cases
    
    def generate_complex_intent_cases(self) -> List[TestCase]:
        """복합 의도 테스트케이스 생성 (주문+취소, 변경+추가 등)"""
        test_cases = []
        max_tests = self.test_config.get('max_tests_per_category', 50)
        
        # 설정 파일에서 복합 패턴 로드
        complex_patterns = self.complex_patterns
        
        # 복합 패턴들을 테스트케이스로 변환
        for i, pattern in enumerate(complex_patterns):
            if len(test_cases) >= max_tests:
                break
            # 패턴에 따라 의도 결정
            if "주문하고" in pattern and "취소" in pattern:
                expected_intent = IntentType.ORDER
            elif "바꾸고" in pattern or "업그레이드" in pattern:
                expected_intent = IntentType.MODIFY
            else:
                expected_intent = IntentType.ORDER
            
            test_cases.append(TestCase(
                id=f"complex_{len(test_cases)+1:03d}",
                input_text=pattern,
                expected_intent=expected_intent,
                category=TestCaseCategory.COMPLEX,
                description=f"복합 의도 테스트 - {pattern[:30]}...",
                tags=["complex", "multiple_intents"],
                expected_confidence_min=0.4
            ))
        
        # 문의 + 주문
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"complex_{len(test_cases)+1:03d}",
                    input_text="빅맥 가격이 얼마인지 알려주시고 하나 주문할게요",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.COMPLEX,
                    description="가격 문의 + 주문 복합 의도 테스트",
                    tags=["complex", "inquiry", "price", "order"],
                    expected_confidence_min=0.5
                ),
                TestCase(
                    id=f"complex_{len(test_cases)+1:03d}",
                    input_text="오늘 추천 메뉴가 뭔지 알려주시고 그걸로 주문하겠습니다",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.COMPLEX,
                    description="추천 문의 + 주문 복합 의도 테스트",
                    tags=["complex", "inquiry", "recommendation", "order"],
                    expected_confidence_min=0.4
                )
            ])
        
        # 다중 변경
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"complex_{len(test_cases)+1:03d}",
                    input_text="빅맥 수량을 2개로 늘리고 콜라를 사이다로 바꿔주세요",
                    expected_intent=IntentType.MODIFY,
                    category=TestCaseCategory.COMPLEX,
                    description="수량 변경 + 메뉴 변경 복합 의도 테스트",
                    tags=["complex", "modify", "quantity", "menu"],
                    expected_confidence_min=0.5
                ),
                TestCase(
                    id=f"complex_{len(test_cases)+1:03d}",
                    input_text="세트를 라지로 업사이즈하고 음료는 아이스 아메리카노로 변경해주세요",
                    expected_intent=IntentType.MODIFY,
                    category=TestCaseCategory.COMPLEX,
                    description="사이즈 업그레이드 + 음료 변경 복합 의도 테스트",
                    tags=["complex", "modify", "upsize", "drink"],
                    expected_confidence_min=0.4
                )
            ])
        
        # 조건부 주문
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"complex_{len(test_cases)+1:03d}",
                    input_text="만약 빅맥이 있으면 주문하고, 없으면 치즈버거 주세요",
                    expected_intent=IntentType.ORDER,
                    category=TestCaseCategory.COMPLEX,
                    description="조건부 주문 복합 의도 테스트",
                    tags=["complex", "order", "conditional"],
                    expected_confidence_min=0.3
                ),
                TestCase(
                    id=f"complex_{len(test_cases)+1:03d}",
                    input_text="할인되는 메뉴가 있으면 그걸로 주문하고, 아니면 상스치콤 주세요",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.COMPLEX,
                    description="할인 문의 + 조건부 주문 복합 의도 테스트",
                    tags=["complex", "inquiry", "discount", "conditional", "order"],
                    expected_confidence_min=0.3
                )
            ])
        
        self.logger.info(f"복합 의도 테스트케이스 {len(test_cases)}개 생성 (최대 {max_tests}개)")
        return test_cases
    
    def generate_normal_cases(self) -> List[TestCase]:
        """일반적인 테스트케이스 생성"""
        test_cases = []
        max_tests = self.test_config.get('max_tests_per_category', 50)
        
        # 기본 주문 패턴
        if len(test_cases) < max_tests:
            for menu in self.menu_items[:10]:
                test_cases.append(TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text=f"{menu} 주문하겠습니다",
                    expected_intent=IntentType.ORDER,
                    category=TestCaseCategory.NORMAL,
                    description=f"일반 주문 테스트 - {menu}",
                    tags=["normal", "order"],
                    expected_confidence_min=0.8
                ))
        
        # 수량 포함 주문
        if len(test_cases) < max_tests:
            for i, menu in enumerate(self.menu_items[:5]):
                quantity = self.quantity_expressions[i % len(self.quantity_expressions)]
                test_cases.append(TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text=f"{menu} {quantity} 주문해주세요",
                    expected_intent=IntentType.ORDER,
                    category=TestCaseCategory.NORMAL,
                    description=f"수량 포함 주문 테스트 - {menu}",
                    tags=["normal", "order", "quantity"],
                    expected_confidence_min=0.7
                ))
        
        # 기본 변경/취소
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text="빅맥을 치즈버거로 변경해주세요",
                    expected_intent=IntentType.MODIFY,
                    category=TestCaseCategory.NORMAL,
                    description="메뉴 변경 테스트",
                    tags=["normal", "modify"],
                    expected_confidence_min=0.8
                ),
                TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text="치즈버거 주문 취소해주세요",
                    expected_intent=IntentType.CANCEL,
                    category=TestCaseCategory.NORMAL,
                    description="주문 취소 테스트",
                    tags=["normal", "cancel"],
                    expected_confidence_min=0.8
                )
            ])
        
        # 기본 문의
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text="메뉴판을 보여주세요",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.NORMAL,
                    description="메뉴 문의 테스트",
                    tags=["normal", "inquiry", "menu"],
                    expected_confidence_min=0.8
                ),
                TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text="현재 주문 내역을 확인해주세요",
                    expected_intent=IntentType.INQUIRY,
                    category=TestCaseCategory.NORMAL,
                    description="주문 내역 확인 테스트",
                    tags=["normal", "inquiry", "order_status"],
                    expected_confidence_min=0.8
                )
            ])
        
        # 기본 결제
        if len(test_cases) < max_tests:
            test_cases.extend([
                TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text="결제하겠습니다",
                    expected_intent=IntentType.PAYMENT,
                    category=TestCaseCategory.NORMAL,
                    description="기본 결제 테스트",
                    tags=["normal", "payment"],
                    expected_confidence_min=0.9
                ),
                TestCase(
                    id=f"normal_{len(test_cases)+1:03d}",
                    input_text="카드로 결제할게요",
                    expected_intent=IntentType.PAYMENT,
                    category=TestCaseCategory.NORMAL,
                    description="카드 결제 테스트",
                    tags=["normal", "payment", "card"],
                    expected_confidence_min=0.8
                )
            ])
        
        self.logger.info(f"일반 테스트케이스 {len(test_cases)}개 생성 (최대 {max_tests}개)")
        return test_cases
    
    def generate_edge_cases(self) -> List[TestCase]:
        """엣지 케이스 테스트케이스 생성"""
        test_cases = []
        max_tests = self.test_config.get('max_tests_per_category', 50)
        
        # 설정 파일에서 엣지 케이스 로드
        edge_cases = self.edge_cases
        
        # 엣지 케이스들을 테스트케이스로 변환
        for i, edge_case in enumerate(edge_cases):
            if len(test_cases) >= max_tests:
                break
            # 빈 입력이나 의미 없는 입력은 UNKNOWN 의도
            if edge_case == "" or edge_case in ["아아아아아", "123456789"]:
                expected_intent = IntentType.UNKNOWN
                confidence_min = 0.0
            # 존재하지 않는 메뉴는 ORDER 의도 (시스템이 주문으로 인식할 수 있음)
            elif "피자" in edge_case or "초밥" in edge_case:
                expected_intent = IntentType.ORDER
                confidence_min = 0.5
            # 특수 문자나 모호한 표현은 ORDER 의도
            else:
                expected_intent = IntentType.ORDER
                confidence_min = 0.3
            
            test_cases.append(TestCase(
                id=f"edge_{len(test_cases)+1:03d}",
                input_text=edge_case,
                expected_intent=expected_intent,
                category=TestCaseCategory.EDGE,
                description=f"엣지 케이스 테스트 - {edge_case[:30]}...",
                tags=["edge", "special_case"],
                expected_confidence_min=confidence_min
            ))
        
        self.logger.info(f"엣지 케이스 테스트케이스 {len(test_cases)}개 생성 (최대 {max_tests}개)")
        return test_cases
    
    def generate_custom_test_case(self, input_text: str, expected_intent: IntentType, 
                                category: TestCaseCategory, description: str,
                                tags: List[str] = None, expected_confidence_min: float = 0.5) -> TestCase:
        """커스텀 테스트케이스 생성"""
        return TestCase(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            input_text=input_text,
            expected_intent=expected_intent,
            category=category,
            description=description,
            tags=tags or [],
            expected_confidence_min=expected_confidence_min
        )