#!/usr/bin/env python3
"""
테스트 결과 분석 및 보고서 생성 기능 테스트
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.models.testing_models import (
    TestCase, TestResult, TestResults, TestAnalysis, TestCaseCategory
)
from src.models.conversation_models import IntentType
from src.testing.result_analyzer import ResultAnalyzer
from src.testing.report_generator import ReportGenerator


def create_sample_test_results() -> TestResults:
    """샘플 테스트 결과 생성"""
    test_results = TestResults(session_id="test_session_001")
    
    # 샘플 테스트케이스들 생성
    test_cases = [
        # 성공 케이스들
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
        # 실패 케이스들
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
        # 성공 케이스들
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
        # 실패 케이스들
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
            detected_intent=IntentType.ORDER,  # 잘못 감지됨
            processing_time=1.8,
            success=False,
            confidence_score=0.45,
            error_message="parsing_error: 복합 의도 처리 실패"
        )
    ]
    
    # 결과들을 TestResults에 추가
    for result in results:
        test_results.add_result(result)
    
    test_results.finish()
    return test_results


def test_result_analyzer():
    """ResultAnalyzer 테스트"""
    print("=" * 60)
    print("ResultAnalyzer 테스트 시작")
    print("=" * 60)
    
    # 샘플 데이터 생성
    test_results = create_sample_test_results()
    print(f"샘플 테스트 결과 생성 완료: {test_results.total_tests}개")
    
    # ResultAnalyzer 테스트
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
    
    print(f"\n처리 시간 통계:")
    for stat, value in analysis.processing_time_stats.items():
        print(f"- {stat}: {value:.3f}초")
    
    # 성능 인사이트 테스트
    insights = analyzer.get_performance_insights(analysis)
    print(f"\n성능 인사이트:")
    for insight in insights:
        print(f"- {insight}")
    
    # 실패한 테스트 상세 정보
    failed_details = analyzer.get_failed_test_details(analysis)
    print(f"\n실패한 테스트 상세 ({len(failed_details)}개):")
    for detail in failed_details:
        print(f"- {detail['test_id']}: {detail['input_text']}")
        print(f"  오류: {detail['error_message']}")
    
    return analysis


def test_report_generator(analysis: TestAnalysis):
    """ReportGenerator 테스트"""
    print("\n" + "=" * 60)
    print("ReportGenerator 테스트 시작")
    print("=" * 60)
    
    # ReportGenerator 테스트
    generator = ReportGenerator(output_directory="test_results")
    
    # 요약 보고서 테스트
    print("\n요약 보고서:")
    summary = generator.generate_summary_report(analysis)
    print(summary)
    
    # 텍스트 보고서 생성
    print("\n텍스트 보고서 생성 중...")
    text_report_path = generator.generate_text_report(analysis)
    print(f"텍스트 보고서 생성 완료: {text_report_path}")
    
    # 마크다운 보고서 생성
    print("\n마크다운 보고서 생성 중...")
    markdown_report_path = generator.generate_markdown_report(analysis)
    print(f"마크다운 보고서 생성 완료: {markdown_report_path}")
    
    # 생성된 파일들 확인
    print(f"\n생성된 파일들:")
    if os.path.exists(text_report_path):
        file_size = os.path.getsize(text_report_path)
        print(f"- {text_report_path} ({file_size} bytes)")
    
    if os.path.exists(markdown_report_path):
        file_size = os.path.getsize(markdown_report_path)
        print(f"- {markdown_report_path} ({file_size} bytes)")
    
    return text_report_path, markdown_report_path


def test_statistics_formatting():
    """통계 데이터 포맷팅 테스트"""
    print("\n" + "=" * 60)
    print("통계 데이터 포맷팅 테스트")
    print("=" * 60)
    
    # 샘플 데이터로 통계 생성
    test_results = create_sample_test_results()
    analyzer = ResultAnalyzer()
    analysis = analyzer.analyze_results(test_results)
    
    # 요약 통계 생성
    summary_stats = analyzer.generate_summary_statistics(analysis)
    
    print("요약 통계:")
    for section, data in summary_stats.items():
        print(f"\n{section}:")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {data}")


def main():
    """메인 테스트 함수"""
    print("테스트 결과 분석 및 보고서 생성 기능 테스트")
    print("=" * 80)
    
    try:
        # ResultAnalyzer 테스트
        analysis = test_result_analyzer()
        
        # ReportGenerator 테스트
        text_path, markdown_path = test_report_generator(analysis)
        
        # 통계 포맷팅 테스트
        test_statistics_formatting()
        
        print("\n" + "=" * 80)
        print("모든 테스트 완료!")
        print("=" * 80)
        
        # 생성된 보고서 파일 내용 일부 출력
        print(f"\n생성된 텍스트 보고서 미리보기:")
        print("-" * 40)
        if os.path.exists(text_path):
            with open(text_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:20]:  # 처음 20줄만 출력
                    print(line.rstrip())
                if len(lines) > 20:
                    print("...")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)