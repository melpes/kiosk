"""
테스트 결과 보고서 생성기
"""

import os
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from ..models.testing_models import TestAnalysis, TestResult, TestCaseCategory
from ..logger import get_logger

class ReportGenerator:
    """테스트 결과 보고서 생성기"""
    
    def __init__(self, output_directory: str = "test_results"):
        self.output_directory = Path(output_directory)
        self.logger = get_logger(__name__)
        
        # 출력 디렉토리 생성
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.reports_dir = self.output_directory / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_text_report(self, analysis: TestAnalysis, output_path: str = None) -> str:
        """
        텍스트 형태의 보고서 생성
        
        Args:
            analysis: 분석 결과
            output_path: 출력 파일 경로 (None이면 자동 생성)
            
        Returns:
            str: 생성된 파일 경로
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.reports_dir / f"test_report_{timestamp}.txt"
            else:
                output_path = Path(output_path)
            
            self.logger.info(f"텍스트 보고서 생성 시작: {output_path}")
            
            # 보고서 내용 생성
            content = self._generate_text_content(analysis)
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"텍스트 보고서 생성 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"텍스트 보고서 생성 중 오류 발생: {e}")
            raise
    
    def generate_markdown_report(self, analysis: TestAnalysis, output_path: str = None) -> str:
        """
        마크다운 형태의 보고서 생성
        
        Args:
            analysis: 분석 결과
            output_path: 출력 파일 경로 (None이면 자동 생성)
            
        Returns:
            str: 생성된 파일 경로
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = self.reports_dir / f"test_report_{timestamp}.md"
            else:
                output_path = Path(output_path)
            
            self.logger.info(f"마크다운 보고서 생성 시작: {output_path}")
            
            # 보고서 내용 생성
            content = self._generate_markdown_content(analysis)
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"마크다운 보고서 생성 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"마크다운 보고서 생성 중 오류 발생: {e}")
            raise
    
    def generate_summary_report(self, analysis: TestAnalysis) -> str:
        """
        요약 보고서 생성 (콘솔 출력용)
        
        Args:
            analysis: 분석 결과
            
        Returns:
            str: 요약 보고서 내용
        """
        lines = []
        lines.append("=" * 60)
        lines.append("테스트 결과 요약")
        lines.append("=" * 60)
        lines.append("")
        
        # 기본 통계
        lines.append("📊 기본 통계")
        lines.append(f"  • 전체 테스트: {analysis.total_tests}개")
        lines.append(f"  • 성공률: {analysis.success_rate:.2%}")
        lines.append(f"  • 평균 처리 시간: {analysis.average_processing_time:.3f}초")
        lines.append("")
        
        # 카테고리별 성능
        if analysis.category_performance:
            lines.append("📈 카테고리별 성능")
            for category, performance in sorted(analysis.category_performance.items()):
                lines.append(f"  • {category}: {performance:.2%}")
            lines.append("")
        
        # 주요 오류
        if analysis.error_summary:
            lines.append("❌ 주요 오류")
            sorted_errors = sorted(analysis.error_summary.items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors[:3]:  # 상위 3개만 표시
                lines.append(f"  • {error_type}: {count}회")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_text_content(self, analysis: TestAnalysis) -> str:
        """텍스트 보고서 내용 생성"""
        lines = []
        
        # 헤더
        lines.append("=" * 80)
        lines.append("음성 키오스크 테스트 결과 보고서")
        lines.append("=" * 80)
        lines.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 전체 요약
        lines.append("1. 전체 요약")
        lines.append("-" * 40)
        lines.append(f"총 테스트 수: {analysis.total_tests}")
        lines.append(f"성공률: {analysis.success_rate:.2%}")
        lines.append(f"평균 처리 시간: {analysis.average_processing_time:.3f}초")
        lines.append(f"총 오류 수: {sum(analysis.error_summary.values())}")
        lines.append("")
        
        # 의도별 정확도
        if analysis.intent_accuracy:
            lines.append("2. 의도별 정확도")
            lines.append("-" * 40)
            for intent, accuracy in sorted(analysis.intent_accuracy.items()):
                lines.append(f"{intent}: {accuracy:.2%}")
            lines.append("")
        
        # 카테고리별 성능
        if analysis.category_performance:
            lines.append("3. 카테고리별 성능")
            lines.append("-" * 40)
            for category, performance in sorted(analysis.category_performance.items()):
                lines.append(f"{category}: {performance:.2%}")
            lines.append("")
        
        # 오류 분석
        if analysis.error_summary:
            lines.append("4. 오류 분석")
            lines.append("-" * 40)
            sorted_errors = sorted(analysis.error_summary.items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors:
                lines.append(f"{error_type}: {count}회")
            lines.append("")
        
        # 신뢰도 분포
        if hasattr(analysis, 'confidence_distribution') and analysis.confidence_distribution:
            lines.append("5. 신뢰도 분포")
            lines.append("-" * 40)
            for level, count in analysis.confidence_distribution.items():
                lines.append(f"{level}: {count}개")
            lines.append("")
        
        # 처리 시간 통계
        if hasattr(analysis, 'processing_time_stats') and analysis.processing_time_stats:
            lines.append("6. 처리 시간 통계")
            lines.append("-" * 40)
            stats = analysis.processing_time_stats
            lines.append(f"최소: {stats.get('min', 0):.3f}초")
            lines.append(f"최대: {stats.get('max', 0):.3f}초")
            lines.append(f"평균: {stats.get('mean', 0):.3f}초")
            lines.append(f"중앙값: {stats.get('median', 0):.3f}초")
            lines.append("")
        
        # 실패한 테스트 상세
        failed_tests = [r for r in analysis.detailed_results if not r.success]
        if failed_tests:
            lines.append("7. 실패한 테스트 상세")
            lines.append("-" * 40)
            for i, result in enumerate(failed_tests[:10], 1):  # 최대 10개만 표시
                lines.append(f"{i}. 테스트 ID: {result.test_case.id}")
                lines.append(f"   입력: {result.test_case.input_text}")
                lines.append(f"   카테고리: {result.test_case.category.value}")
                lines.append(f"   예상 의도: {result.test_case.expected_intent.value if result.test_case.expected_intent else 'N/A'}")
                lines.append(f"   감지된 의도: {result.detected_intent.value}")
                lines.append(f"   오류: {result.error_message}")
                lines.append(f"   신뢰도: {result.confidence_score:.3f}")
                lines.append(f"   처리 시간: {result.processing_time:.3f}초")
                lines.append("")
            
            if len(failed_tests) > 10:
                lines.append(f"... 및 {len(failed_tests) - 10}개 추가 실패 테스트")
                lines.append("")
        
        # 모든 테스트 상세 (입력/출력 포함)
        lines.append("8. 모든 테스트 상세")
        lines.append("-" * 40)
        for i, result in enumerate(analysis.detailed_results, 1):
            success_mark = "성공" if result.success else "실패"
            lines.append(f"{i}. 테스트 ID: {result.test_case.id}")
            lines.append(f"   입력 텍스트: {result.test_case.input_text}")
            lines.append(f"   출력 텍스트: {result.system_response}")
            lines.append(f"   감지된 의도: {result.detected_intent.value}")
            lines.append(f"   신뢰도: {result.confidence_score:.3f}")
            lines.append(f"   성공 여부: {success_mark}")
            lines.append(f"   처리 시간: {result.processing_time:.3f}초")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("보고서 끝")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_markdown_content(self, analysis: TestAnalysis) -> str:
        """마크다운 보고서 내용 생성"""
        lines = []
        
        # 헤더
        lines.append("# 음성 키오스크 테스트 결과 보고서")
        lines.append("")
        lines.append(f"**생성 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 전체 요약
        lines.append("## 1. 전체 요약")
        lines.append("")
        lines.append("| 항목 | 값 |")
        lines.append("|------|-----|")
        lines.append(f"| 총 테스트 수 | {analysis.total_tests} |")
        lines.append(f"| 성공률 | {analysis.success_rate:.2%} |")
        lines.append(f"| 평균 처리 시간 | {analysis.average_processing_time:.3f}초 |")
        lines.append(f"| 총 오류 수 | {sum(analysis.error_summary.values())} |")
        lines.append("")
        
        # 의도별 정확도
        if analysis.intent_accuracy:
            lines.append("## 2. 의도별 정확도")
            lines.append("")
            lines.append("| 의도 | 정확도 |")
            lines.append("|------|--------|")
            for intent, accuracy in sorted(analysis.intent_accuracy.items()):
                lines.append(f"| {intent} | {accuracy:.2%} |")
            lines.append("")
        
        # 카테고리별 성능
        if analysis.category_performance:
            lines.append("## 3. 카테고리별 성능")
            lines.append("")
            lines.append("| 카테고리 | 성공률 |")
            lines.append("|----------|--------|")
            for category, performance in sorted(analysis.category_performance.items()):
                lines.append(f"| {category} | {performance:.2%} |")
            lines.append("")
        
        # 오류 분석
        if analysis.error_summary:
            lines.append("## 4. 오류 분석")
            lines.append("")
            lines.append("| 오류 유형 | 발생 횟수 |")
            lines.append("|-----------|-----------|")
            sorted_errors = sorted(analysis.error_summary.items(), key=lambda x: x[1], reverse=True)
            for error_type, count in sorted_errors:
                lines.append(f"| {error_type} | {count} |")
            lines.append("")
        
        # 신뢰도 분포
        if hasattr(analysis, 'confidence_distribution') and analysis.confidence_distribution:
            lines.append("## 5. 신뢰도 분포")
            lines.append("")
            lines.append("| 신뢰도 수준 | 개수 |")
            lines.append("|-------------|------|")
            for level, count in analysis.confidence_distribution.items():
                lines.append(f"| {level} | {count} |")
            lines.append("")
        
        # 처리 시간 통계
        if hasattr(analysis, 'processing_time_stats') and analysis.processing_time_stats:
            lines.append("## 6. 처리 시간 통계")
            lines.append("")
            stats = analysis.processing_time_stats
            lines.append("| 통계 | 값 |")
            lines.append("|------|-----|")
            lines.append(f"| 최소 | {stats.get('min', 0):.3f}초 |")
            lines.append(f"| 최대 | {stats.get('max', 0):.3f}초 |")
            lines.append(f"| 평균 | {stats.get('mean', 0):.3f}초 |")
            lines.append(f"| 중앙값 | {stats.get('median', 0):.3f}초 |")
            lines.append("")
        
        # 실패한 테스트 상세
        failed_tests = [r for r in analysis.detailed_results if not r.success]
        if failed_tests:
            lines.append("## 7. 실패한 테스트 상세")
            lines.append("")
            for i, result in enumerate(failed_tests[:10], 1):  # 최대 10개만 표시
                lines.append(f"### 실패 테스트 {i}")
                lines.append("")
                lines.append(f"- **테스트 ID:** {result.test_case.id}")
                lines.append(f"- **입력:** {result.test_case.input_text}")
                lines.append(f"- **카테고리:** {result.test_case.category.value}")
                lines.append(f"- **예상 의도:** {result.test_case.expected_intent.value if result.test_case.expected_intent else 'N/A'}")
                lines.append(f"- **감지된 의도:** {result.detected_intent.value}")
                lines.append(f"- **오류:** {result.error_message}")
                lines.append(f"- **신뢰도:** {result.confidence_score:.3f}")
                lines.append(f"- **처리 시간:** {result.processing_time:.3f}초")
                lines.append("")
            
            if len(failed_tests) > 10:
                lines.append(f"*... 및 {len(failed_tests) - 10}개 추가 실패 테스트*")
                lines.append("")
        
        # 모든 테스트 상세 (입력/출력 포함)
        lines.append("## 8. 모든 테스트 상세")
        lines.append("")
        lines.append("| 테스트 ID | 입력 텍스트 | 출력 텍스트 | 의도 | 신뢰도 | 성공 | 처리시간 |")
        lines.append("|-----------|-------------|-------------|------|--------|------|----------|")
        
        for result in analysis.detailed_results:
            success_mark = "✅" if result.success else "❌"
            # 텍스트 전체 표시 (자르지 않음)
            input_text = result.test_case.input_text
            output_text = result.system_response
            lines.append(f"| {result.test_case.id} | {input_text} | {output_text} | {result.detected_intent.value} | {result.confidence_score:.3f} | {success_mark} | {result.processing_time:.3f}초 |")
        
        lines.append("")
        
        # 성능 인사이트
        lines.append("## 9. 성능 인사이트")
        lines.append("")
        insights = self._generate_performance_insights(analysis)
        for insight in insights:
            lines.append(f"- {insight}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _generate_performance_insights(self, analysis: TestAnalysis) -> List[str]:
        """성능 인사이트 생성"""
        insights = []
        
        # 전체 성공률 평가
        if analysis.success_rate >= 0.9:
            insights.append("✅ 전체 성공률이 90% 이상으로 우수합니다.")
        elif analysis.success_rate >= 0.8:
            insights.append("⚠️ 전체 성공률이 80-90%로 양호하지만 개선 여지가 있습니다.")
        else:
            insights.append("❌ 전체 성공률이 80% 미만으로 개선이 필요합니다.")
        
        # 처리 시간 평가
        if analysis.average_processing_time <= 1.0:
            insights.append("✅ 평균 처리 시간이 1초 이하로 빠릅니다.")
        elif analysis.average_processing_time <= 3.0:
            insights.append("⚠️ 평균 처리 시간이 1-3초로 보통입니다.")
        else:
            insights.append("❌ 평균 처리 시간이 3초 이상으로 느립니다.")
        
        # 카테고리별 성능 분석
        if analysis.category_performance:
            worst_category = min(analysis.category_performance.items(), key=lambda x: x[1])
            best_category = max(analysis.category_performance.items(), key=lambda x: x[1])
            
            insights.append(f"📊 가장 성능이 좋은 카테고리: {best_category[0]} ({best_category[1]:.1%})")
            insights.append(f"📊 가장 성능이 나쁜 카테고리: {worst_category[0]} ({worst_category[1]:.1%})")
        
        # 오류 분석
        if analysis.error_summary:
            most_common_error = max(analysis.error_summary.items(), key=lambda x: x[1])
            insights.append(f"🔍 가장 빈번한 오류: {most_common_error[0]} ({most_common_error[1]}회)")
        
        return insights
    
    def _format_statistics(self, analysis: TestAnalysis) -> str:
        """통계 데이터 포맷팅"""
        stats = []
        stats.append(f"총 테스트: {analysis.total_tests}")
        stats.append(f"성공률: {analysis.success_rate:.2%}")
        stats.append(f"평균 처리 시간: {analysis.average_processing_time:.3f}초")
        
        if analysis.error_summary:
            total_errors = sum(analysis.error_summary.values())
            stats.append(f"총 오류: {total_errors}")
        
        return " | ".join(stats)
    
    def _format_error_details(self, analysis: TestAnalysis) -> str:
        """오류 상세 정보 포맷팅"""
        if not analysis.error_summary:
            return "오류 없음"
        
        error_details = []
        sorted_errors = sorted(analysis.error_summary.items(), key=lambda x: x[1], reverse=True)
        
        for error_type, count in sorted_errors:
            error_details.append(f"{error_type}: {count}회")
        
        return ", ".join(error_details)