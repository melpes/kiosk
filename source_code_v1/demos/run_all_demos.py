#!/usr/bin/env python3
"""
모든 데모를 실행하는 통합 스크립트
"""

import sys
import subprocess
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_demo(demo_name, description):
    """개별 데모 실행"""
    print(f"\n{'='*60}")
    print(f"🎬 {description}")
    print(f"{'='*60}")
    
    try:
        demo_path = Path(__file__).parent / demo_name
        subprocess.run([sys.executable, str(demo_path)], check=True)
        print(f"✅ {description} 완료")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 실행 중 오류: {e}")
    except FileNotFoundError:
        print(f"❌ {demo_name} 파일을 찾을 수 없습니다")


def main():
    """메인 실행 함수"""
    print("🎯 음성 키오스크 시스템 데모 모음")
    print("=" * 60)
    
    demos = [
        ("demo_config_management.py", "설정 관리 시스템 데모"),
        ("demo_text_response.py", "텍스트 응답 시스템 데모"),
        ("demo_error_handling.py", "오류 처리 시스템 데모"),
        ("demo_main_pipeline.py", "메인 파이프라인 데모"),
        ("demo_cli_simple.py", "간단한 CLI 데모"),
    ]
    
    for demo_file, demo_desc in demos:
        run_demo(demo_file, demo_desc)
    
    print(f"\n{'='*60}")
    print("🎉 모든 데모가 완료되었습니다!")
    print("💡 개별 데모를 실행하려면 각 파일을 직접 실행하세요.")
    print("💡 전체 CLI 데모는 'python demos/demo_cli.py'를 실행하세요.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()