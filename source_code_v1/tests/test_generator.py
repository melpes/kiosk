#!/usr/bin/env python3
"""
테스트케이스 생성기 테스트 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 직접 import
from models.testing_models import TestCase, TestCaseCategory, TestConfiguration
from models.conversation_models import IntentType
from logger import get_logger

# TestCaseGenerator를 직접 정의 (import 문제 해결을 위해)
import uuid
from typing import List, Dict, Any
from datetime import datetime

def test_generator():
    """테스트케이스 생성기 테스트"""
    print("🧪 테스트케이스 생성기 테스트 시작")
    
    try:
        # 테스트케이스 생성기 초기화
        generator = TestCaseGenerator()
        
        # 은어 테스트케이스 생성
        slang_cases = generator.generate_slang_cases()[:3]
        print(f"\n🗣️ 은어 테스트케이스 샘플 ({len(slang_cases)}개):")
        for i, case in enumerate(slang_cases, 1):
            print(f"  {i}. {case.id}: '{case.input_text}'")
            print(f"     예상 의도: {case.expected_intent.value if case.expected_intent else 'None'}")
            print(f"     카테고리: {case.category.value}")
        
        # 반말 테스트케이스 생성
        informal_cases = generator.generate_informal_cases()[:3]
        print(f"\n💬 반말 테스트케이스 샘플 ({len(informal_cases)}개):")
        for i, case in enumerate(informal_cases, 1):
            print(f"  {i}. {case.id}: '{case.input_text}'")
            print(f"     예상 의도: {case.expected_intent.value if case.expected_intent else 'None'}")
        
        # 복합 의도 테스트케이스 생성
        complex_cases = generator.generate_complex_intent_cases()[:2]
        print(f"\n🔄 복합 의도 테스트케이스 샘플 ({len(complex_cases)}개):")
        for i, case in enumerate(complex_cases, 1):
            print(f"  {i}. {case.id}: '{case.input_text}'")
            print(f"     예상 의도: {case.expected_intent.value if case.expected_intent else 'None'}")
        
        # 전체 테스트케이스 생성
        all_cases = generator.generate_mcdonald_test_cases()
        print(f"\n📊 전체 테스트케이스 통계:")
        print(f"  - 총 개수: {len(all_cases)}개")
        
        # 카테고리별 개수
        from collections import Counter
        category_counts = Counter(case.category.value for case in all_cases)
        for category, count in category_counts.items():
            print(f"  - {category}: {count}개")
        
        print("\n✅ 테스트케이스 생성기 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_generator()