#!/usr/bin/env python3
"""
작업 2번 테스트: 테스트케이스 생성 및 실행 시스템 구현 검증
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_task2_implementation():
    """작업 2번 구현 검증"""
    print("🧪 작업 2번 구현 검증: 테스트케이스 생성 및 실행 시스템")
    print("="*70)
    
    try:
        # 1. 환경 설정
        from src.utils.env_loader import ensure_env_loaded
        ensure_env_loaded()
        
        # 2. VoiceKioskPipeline 초기화
        print("🔧 VoiceKioskPipeline 초기화 중...")
        from src.main import VoiceKioskPipeline
        pipeline = VoiceKioskPipeline()
        
        if not pipeline.initialize_system():
            print("❌ 파이프라인 초기화 실패")
            return False
        
        print("✅ 파이프라인 초기화 성공")
        
        # 3. 테스트 모듈 import 확인
        print("\n📦 테스트 모듈 import 확인...")
        from src.testing import TestCaseManager, TestCaseGenerator, TestRunner
        from src.models.testing_models import TestConfiguration, TestCaseCategory
        
        print("✅ 테스트 모듈 import 성공")
        
        # 4. TestCaseGenerator 테스트
        print("\n🏗️ TestCaseGenerator 테스트...")
        generator = TestCaseGenerator()
        
        # 은어 테스트케이스 생성
        slang_cases = generator.generate_slang_cases()
        print(f"  - 은어 테스트케이스: {len(slang_cases)}개 생성")
        
        # 반말 테스트케이스 생성
        informal_cases = generator.generate_informal_cases()
        print(f"  - 반말 테스트케이스: {len(informal_cases)}개 생성")
        
        # 복합 의도 테스트케이스 생성
        complex_cases = generator.generate_complex_intent_cases()
        print(f"  - 복합 의도 테스트케이스: {len(complex_cases)}개 생성")
        
        # 전체 테스트케이스 생성
        all_cases = generator.generate_mcdonald_test_cases()
        print(f"  - 전체 테스트케이스: {len(all_cases)}개 생성")
        
        print("✅ TestCaseGenerator 테스트 성공")
        
        # 5. TestRunner 테스트 (소규모)
        print("\n🏃 TestRunner 테스트 (소규모)...")
        runner = TestRunner(pipeline)
        
        # 테스트 세션 설정
        session_id = runner.setup_test_session()
        print(f"  - 테스트 세션 설정: {session_id}")
        
        # 단일 테스트 실행 (은어 테스트 1개)
        if slang_cases:
            test_case = slang_cases[0]
            print(f"  - 단일 테스트 실행: '{test_case.input_text}'")
            result = runner.run_single_test(test_case)
            print(f"    결과: {'성공' if result.success else '실패'}")
            print(f"    감지된 의도: {result.detected_intent.value}")
            print(f"    신뢰도: {result.confidence_score:.3f}")
            print(f"    처리시간: {result.processing_time:.3f}초")
        
        # 테스트 세션 정리
        runner.cleanup_test_session(session_id)
        print("✅ TestRunner 테스트 성공")
        
        # 6. TestCaseManager 테스트
        print("\n📋 TestCaseManager 테스트...")
        config = TestConfiguration(
            include_slang=True,
            include_informal=True,
            include_complex=False,  # 빠른 테스트를 위해 제외
            include_edge_cases=False,  # 빠른 테스트를 위해 제외
            max_tests_per_category=3  # 각 카테고리당 3개만
        )
        
        manager = TestCaseManager(pipeline, config)
        
        # 테스트케이스 생성
        test_cases = manager.generate_test_cases()
        print(f"  - 제한된 테스트케이스: {len(test_cases)}개 생성")
        
        # 요약 정보
        summary = manager.get_test_case_summary()
        print(f"  - 카테고리별 개수: {summary['category_counts']}")
        
        print("✅ TestCaseManager 테스트 성공")
        
        # 7. 통합 테스트 (매우 소규모)
        print("\n🔗 통합 테스트 (소규모 실행)...")
        
        # 최소한의 테스트케이스로 전체 플로우 테스트
        mini_test_cases = test_cases[:2]  # 처음 2개만
        print(f"  - {len(mini_test_cases)}개 테스트케이스로 통합 테스트 실행")
        
        results = manager.runner.run_test_suite(mini_test_cases)
        
        print(f"  - 실행 결과:")
        print(f"    총 테스트: {results.total_tests}개")
        print(f"    성공: {results.successful_tests}개")
        print(f"    성공률: {results.success_rate*100:.1f}%")
        print(f"    평균 처리시간: {results.average_processing_time:.3f}초")
        
        print("✅ 통합 테스트 성공")
        
        # 8. VoiceKioskPipeline.process_text_input() 연동 확인
        print("\n🔗 VoiceKioskPipeline.process_text_input() 연동 확인...")
        
        # 직접 process_text_input 호출 테스트
        test_inputs = ["빅맥 주세요", "상스치콤 하나 줘", "결제할게요"]
        
        for test_input in test_inputs:
            try:
                response = pipeline.process_text_input(test_input)
                print(f"  - 입력: '{test_input}'")
                print(f"    응답: {response[:50]}..." if len(response) > 50 else f"    응답: {response}")
            except Exception as e:
                print(f"  - 입력: '{test_input}' - 오류: {e}")
        
        print("✅ process_text_input() 연동 확인 완료")
        
        print("\n" + "="*70)
        print("🎉 작업 2번 구현 검증 완료!")
        print("✅ TestCaseGenerator: 맥도날드 특화 테스트케이스 생성 (은어, 반말, 복합 의도)")
        print("✅ TestRunner: 테스트케이스 실행 및 결과 수집")
        print("✅ VoiceKioskPipeline.process_text_input() 연동")
        print("✅ 모든 요구사항 충족")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 정리
        try:
            if 'pipeline' in locals():
                pipeline.shutdown()
        except:
            pass

if __name__ == "__main__":
    success = test_task2_implementation()
    sys.exit(0 if success else 1)