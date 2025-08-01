"""
테스트 시스템 사용 예제
"""

import os
import sys
import time
from typing import List, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.testing.test_case_generator import TestCaseGenerator
from src.testing.test_runner import TestRunner
from src.testing.test_case_manager import TestCaseManager
from src.testing.result_analyzer import ResultAnalyzer
from src.models.testing_models import TestCase, TestCaseCategory
from src.models.conversation_models import IntentType
from src.main import VoiceKioskPipeline


def example_1_basic_test_generation():
    """예제 1: 기본 테스트케이스 생성"""
    print("=== 예제 1: 기본 테스트케이스 생성 ===")
    
    # 테스트케이스 생성기 초기화
    generator = TestCaseGenerator()
    
    # 전체 테스트케이스 생성
    all_test_cases = generator.generate_mcdonald_test_cases()
    
    print(f"총 {len(all_test_cases)}개의 테스트케이스가 생성되었습니다.")
    
    # 카테고리별 분류
    category_counts = {}
    for test_case in all_test_cases:
        category = test_case.category
        category_counts[category] = category_counts.get(category, 0) + 1
    
    print("\n카테고리별 테스트케이스 수:")
    for category, count in category_counts.items():
        print(f"  {category.value}: {count}개")
    
    # 샘플 테스트케이스 출력
    print("\n샘플 테스트케이스 (처음 5개):")
    for i, test_case in enumerate(all_test_cases[:5]):
        print(f"  {i+1}. [{test_case.category.value}] {test_case.input_text}")
        print(f"     예상 의도: {test_case.expected_intent.value}")
        print(f"     태그: {', '.join(test_case.tags)}")
        print()


def example_2_category_specific_generation():
    """예제 2: 특정 카테고리 테스트케이스 생성"""
    print("=== 예제 2: 특정 카테고리 테스트케이스 생성 ===")
    
    generator = TestCaseGenerator()
    
    # 은어 테스트케이스만 생성
    slang_cases = generator.generate_slang_cases()
    print(f"은어 테스트케이스: {len(slang_cases)}개")
    
    print("\n은어 테스트케이스 샘플:")
    for case in slang_cases[:3]:
        print(f"  입력: {case.input_text}")
        print(f"  설명: {case.description}")
        print()
    
    # 복합 의도 테스트케이스 생성
    complex_cases = generator.generate_complex_intent_cases()
    print(f"복합 의도 테스트케이스: {len(complex_cases)}개")
    
    print("\n복합 의도 테스트케이스 샘플:")
    for case in complex_cases[:3]:
        print(f"  입력: {case.input_text}")
        print(f"  설명: {case.description}")
        print(f"  최소 신뢰도: {case.expected_confidence_min}")
        print()


def example_3_custom_test_case():
    """예제 3: 커스텀 테스트케이스 생성"""
    print("=== 예제 3: 커스텀 테스트케이스 생성 ===")
    
    generator = TestCaseGenerator()
    
    # 커스텀 테스트케이스들 생성
    custom_cases = [
        generator.generate_custom_test_case(
            input_text="오늘 특가 메뉴가 뭐예요?",
            expected_intent=IntentType.INQUIRY,
            category=TestCaseCategory.NORMAL,
            description="특가 메뉴 문의 테스트",
            tags=["inquiry", "special_offer"],
            expected_confidence_min=0.7
        ),
        generator.generate_custom_test_case(
            input_text="빅맥 두 개랑 감튀 라지 하나, 그리고 콜라도 주세요",
            expected_intent=IntentType.ORDER,
            category=TestCaseCategory.COMPLEX,
            description="복합 주문 테스트",
            tags=["order", "multiple_items", "complex"],
            expected_confidence_min=0.6
        ),
        generator.generate_custom_test_case(
            input_text="아까 주문한 거 다 취소하고 새로 주문할게요",
            expected_intent=IntentType.CANCEL,
            category=TestCaseCategory.COMPLEX,
            description="전체 취소 후 재주문 테스트",
            tags=["cancel", "reorder", "complex"],
            expected_confidence_min=0.5
        )
    ]
    
    print("생성된 커스텀 테스트케이스:")
    for i, case in enumerate(custom_cases):
        print(f"  {i+1}. ID: {case.id}")
        print(f"     입력: {case.input_text}")
        print(f"     예상 의도: {case.expected_intent.value}")
        print(f"     카테고리: {case.category.value}")
        print(f"     설명: {case.description}")
        print(f"     태그: {', '.join(case.tags)}")
        print(f"     최소 신뢰도: {case.expected_confidence_min}")
        print()


def example_4_single_test_execution():
    """예제 4: 단일 테스트 실행"""
    print("=== 예제 4: 단일 테스트 실행 ===")
    
    try:
        # 파이프라인 초기화 (실제 환경에서는 API 키 필요)
        print("VoiceKioskPipeline 초기화 중...")
        pipeline = VoiceKioskPipeline()
        
        # 테스트 러너 생성
        runner = TestRunner(pipeline)
        
        # 테스트케이스 생성
        generator = TestCaseGenerator()
        test_case = generator.generate_custom_test_case(
            input_text="빅맥 하나 주세요",
            expected_intent=IntentType.ORDER,
            category=TestCaseCategory.NORMAL,
            description="기본 빅맥 주문 테스트"
        )
        
        print(f"테스트 실행: {test_case.input_text}")
        
        # 테스트 실행
        start_time = time.time()
        result = runner.run_single_test(test_case)
        execution_time = time.time() - start_time
        
        # 결과 출력
        print(f"\n테스트 결과:")
        print(f"  성공: {'✅' if result.success else '❌'}")
        print(f"  감지된 의도: {result.detected_intent.value}")
        print(f"  신뢰도: {result.confidence_score:.3f}")
        print(f"  처리 시간: {result.processing_time:.3f}초")
        print(f"  실제 실행 시간: {execution_time:.3f}초")
        print(f"  시스템 응답: {result.system_response}")
        
        if result.error_message:
            print(f"  오류 메시지: {result.error_message}")
            
    except Exception as e:
        print(f"테스트 실행 중 오류 발생: {e}")
        print("참고: 실제 테스트 실행을 위해서는 OpenAI API 키가 필요합니다.")


def example_5_batch_test_execution():
    """예제 5: 배치 테스트 실행"""
    print("=== 예제 5: 배치 테스트 실행 ===")
    
    try:
        # 파이프라인 초기화
        print("VoiceKioskPipeline 초기화 중...")
        pipeline = VoiceKioskPipeline()
        
        # 테스트 러너 생성
        runner = TestRunner(pipeline)
        
        # 소규모 테스트케이스 생성 (데모용)
        generator = TestCaseGenerator()
        test_cases = generator.generate_normal_cases()[:5]  # 처음 5개만
        
        print(f"{len(test_cases)}개의 테스트케이스 실행 중...")
        
        # 배치 테스트 실행
        start_time = time.time()
        results = runner.run_batch_tests(test_cases)
        total_time = time.time() - start_time
        
        # 결과 분석
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(results) * 100
        avg_processing_time = sum(r.processing_time for r in results) / len(results)
        
        print(f"\n배치 테스트 결과:")
        print(f"  총 테스트: {len(results)}개")
        print(f"  성공: {success_count}개")
        print(f"  성공률: {success_rate:.1f}%")
        print(f"  평균 처리 시간: {avg_processing_time:.3f}초")
        print(f"  총 실행 시간: {total_time:.3f}초")
        
        # 개별 결과 출력
        print(f"\n개별 테스트 결과:")
        for i, (test_case, result) in enumerate(zip(test_cases, results)):
            status = "✅" if result.success else "❌"
            print(f"  {i+1}. {status} {test_case.input_text[:30]}...")
            print(f"     의도: {result.detected_intent.value} (신뢰도: {result.confidence_score:.3f})")
            
    except Exception as e:
        print(f"배치 테스트 실행 중 오류 발생: {e}")
        print("참고: 실제 테스트 실행을 위해서는 OpenAI API 키가 필요합니다.")


def example_6_full_test_suite():
    """예제 6: 전체 테스트 스위트 실행"""
    print("=== 예제 6: 전체 테스트 스위트 실행 ===")
    
    try:
        # 파이프라인 초기화
        print("VoiceKioskPipeline 초기화 중...")
        pipeline = VoiceKioskPipeline()
        
        # 테스트 매니저 생성
        manager = TestCaseManager(pipeline)
        
        # 출력 디렉토리 설정
        output_dir = "./example_test_results"
        
        print(f"전체 테스트 스위트 실행 중... (결과는 {output_dir}에 저장됩니다)")
        
        # 전체 테스트 실행
        start_time = time.time()
        summary = manager.run_full_test_suite(output_dir)
        total_time = time.time() - start_time
        
        # 요약 결과 출력
        print(f"\n전체 테스트 스위트 실행 완료!")
        print(f"  총 실행 시간: {total_time:.1f}초")
        print(f"  총 테스트: {summary['total_tests']}개")
        print(f"  성공률: {summary['success_rate']:.1f}%")
        print(f"  평균 처리 시간: {summary['average_processing_time']:.3f}초")
        
        # 카테고리별 성능
        if 'category_performance' in summary:
            print(f"\n카테고리별 성능:")
            for category, performance in summary['category_performance'].items():
                print(f"  {category}: {performance:.1f}%")
        
        # 의도별 정확도
        if 'intent_accuracy' in summary:
            print(f"\n의도별 정확도:")
            for intent, accuracy in summary['intent_accuracy'].items():
                print(f"  {intent}: {accuracy:.1f}%")
        
        print(f"\n상세 결과는 {output_dir} 디렉토리에서 확인할 수 있습니다.")
        
    except Exception as e:
        print(f"전체 테스트 스위트 실행 중 오류 발생: {e}")
        print("참고: 실제 테스트 실행을 위해서는 OpenAI API 키가 필요합니다.")


def example_7_result_analysis():
    """예제 7: 테스트 결과 분석"""
    print("=== 예제 7: 테스트 결과 분석 ===")
    
    # 가상의 테스트 결과 생성 (실제 환경에서는 실제 테스트 결과 사용)
    from src.models.testing_models import TestResult
    
    # 샘플 테스트 결과 생성
    generator = TestCaseGenerator()
    test_cases = generator.generate_normal_cases()[:10]
    
    # 가상의 결과 생성
    sample_results = []
    for i, test_case in enumerate(test_cases):
        # 가상의 결과 데이터
        success = i % 4 != 0  # 75% 성공률
        confidence = 0.8 if success else 0.3
        processing_time = 0.5 + (i * 0.1)
        
        result = TestResult(
            test_case=test_case,
            system_response=f"가상 응답 {i+1}",
            detected_intent=test_case.expected_intent if success else IntentType.UNKNOWN,
            processing_time=processing_time,
            success=success,
            error_message=None if success else "가상 오류",
            confidence_score=confidence
        )
        sample_results.append(result)
    
    # 결과 분석
    analyzer = ResultAnalyzer()
    analysis = analyzer.analyze_results(sample_results)
    
    print(f"분석 결과:")
    print(f"  총 테스트: {analysis.total_tests}개")
    print(f"  성공률: {analysis.success_rate:.1f}%")
    print(f"  평균 처리 시간: {analysis.average_processing_time:.3f}초")
    
    print(f"\n의도별 정확도:")
    for intent, accuracy in analysis.intent_accuracy.items():
        print(f"  {intent}: {accuracy:.1f}%")
    
    print(f"\n카테고리별 성능:")
    for category, performance in analysis.category_performance.items():
        print(f"  {category}: {performance:.1f}%")
    
    print(f"\n오류 요약:")
    for error_type, count in analysis.error_summary.items():
        print(f"  {error_type}: {count}개")


def example_8_configuration_examples():
    """예제 8: 설정 예제"""
    print("=== 예제 8: 설정 예제 ===")
    
    # 테스트 설정 예제
    print("테스트 설정 예제:")
    test_config = {
        "include_slang": True,           # 은어 테스트 포함
        "include_informal": True,        # 반말 테스트 포함
        "include_complex": True,         # 복합 의도 테스트 포함
        "include_edge_cases": False,     # 엣지 케이스 제외
        "max_tests_per_category": 20,    # 카테고리별 최대 20개
        "output_directory": "custom_test_results",
        "generate_markdown": True,
        "generate_text": False          # 텍스트 보고서 생성 안함
    }
    
    for key, value in test_config.items():
        print(f"  {key}: {value}")
    
    # 필터링 예제
    print(f"\n테스트케이스 필터링 예제:")
    generator = TestCaseGenerator()
    all_cases = generator.generate_mcdonald_test_cases()
    
    # 높은 신뢰도 케이스만 필터링
    high_confidence_cases = [
        case for case in all_cases 
        if case.expected_confidence_min >= 0.7
    ]
    print(f"  높은 신뢰도 케이스 (≥0.7): {len(high_confidence_cases)}개")
    
    # 특정 태그가 있는 케이스만 필터링
    order_cases = [
        case for case in all_cases 
        if "order" in case.tags
    ]
    print(f"  주문 관련 케이스: {len(order_cases)}개")
    
    # 특정 카테고리 제외
    non_edge_cases = [
        case for case in all_cases 
        if case.category != TestCaseCategory.EDGE
    ]
    print(f"  엣지 케이스 제외: {len(non_edge_cases)}개")


def main():
    """모든 예제 실행"""
    print("테스트 시스템 사용 예제 실행")
    print("=" * 50)
    
    examples = [
        example_1_basic_test_generation,
        example_2_category_specific_generation,
        example_3_custom_test_case,
        example_4_single_test_execution,
        example_5_batch_test_execution,
        example_6_full_test_suite,
        example_7_result_analysis,
        example_8_configuration_examples
    ]
    
    for i, example_func in enumerate(examples):
        try:
            example_func()
            print()
        except KeyboardInterrupt:
            print("\n사용자에 의해 중단되었습니다.")
            break
        except Exception as e:
            print(f"예제 {i+1} 실행 중 오류: {e}")
            print()
    
    print("모든 예제 실행 완료!")


if __name__ == "__main__":
    main()