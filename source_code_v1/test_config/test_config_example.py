#!/usr/bin/env python3
"""
테스트 데이터 설정 파일 사용 예제
홈 디렉토리의 test_data_config.json 파일을 사용하여 테스트케이스를 생성합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가 (실제 프로젝트 경로로 수정 필요)
# sys.path.append("/path/to/your/project")

def test_custom_config():
    """커스텀 설정 파일을 사용한 테스트케이스 생성 예제"""
    print("🧪 커스텀 설정 파일을 사용한 테스트케이스 생성 예제")
    print("=" * 60)
    
    try:
        # TestCaseGenerator import (실제 프로젝트에서 사용할 때)
        # from src.testing.test_case_generator import TestCaseGenerator
        
        # 프로젝트 루트 디렉토리 찾기
        project_root = Path(__file__).parent.parent
        config_file = project_root / "test_config" / "test_data_config.json"
        
        print(f"📁 설정 파일 경로: {config_file}")
        
        if not config_file.exists():
            print("❌ 설정 파일이 존재하지 않습니다.")
            print("먼저 manage_test_data.py를 실행하여 설정 파일을 생성하세요.")
            return
        
        print("✅ 설정 파일 발견!")
        
        # TestCaseGenerator 초기화 (커스텀 설정 파일 사용)
        # generator = TestCaseGenerator(config_file_path=str(config_file))
        
        # 테스트케이스 생성
        # test_cases = generator.generate_mcdonald_test_cases()
        
        # 결과 출력 (실제로는 위의 코드를 사용)
        print("\n📊 생성된 테스트케이스 예시:")
        print("  - 은어 테스트: '상스치콤 주세요'")
        print("  - 반말 테스트: '빅맥 줘'")
        print("  - 복합 의도: '빅맥 주문하고 치즈버거는 취소해주세요'")
        print("  - 엣지 케이스: '피자 주문하겠습니다'")
        
        print("\n✅ 테스트케이스 생성 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


def show_config_usage():
    """설정 파일 사용법 안내"""
    print("\n📖 설정 파일 사용법")
    print("=" * 40)
    print("1. 설정 파일 위치: test_config/test_data_config.json")
    print("2. 관리 도구: python test_config/manage_test_data.py")
    print("3. 설정 파일 수정 후 테스트 실행")
    print()
    print("🔧 관리 도구 명령어:")
    print("  python test_config/manage_test_data.py status     # 상태 확인")
    print("  python test_config/manage_test_data.py slang      # 은어 목록")
    print("  python test_config/manage_test_data.py menu       # 메뉴 목록")
    print("  python test_config/manage_test_data.py add-slang '새은어' '전체메뉴명'")
    print("  python test_config/manage_test_data.py add-menu '새메뉴'")
    print("  python test_config/manage_test_data.py add-edge '새엣지케이스'")
    print()


def show_config_structure():
    """설정 파일 구조 설명"""
    print("\n📋 설정 파일 구조")
    print("=" * 40)
    print("""
{
  "slang_mappings": {
    "상스치콤": "상하이 스파이시 치킨버거 콤보",
    "베토디": "베이컨 토마토 디럭스",
    ...
  },
  "menu_items": [
    "빅맥", "상하이 스파이시 치킨버거", ...
  ],
  "quantity_expressions": [
    "한 개", "하나", "1개", ...
  ],
  "option_expressions": [
    "라지로", "미디움으로", ...
  ],
  "informal_patterns": [
    "{menu} 줘", "{menu} 하나 줘", ...
  ],
  "complex_patterns": [
    "빅맥 주문하고 치즈버거는 취소해주세요", ...
  ],
  "edge_cases": [
    "", "아아아아아", "피자 주문하겠습니다", ...
  ],
  "test_config": {
    "max_tests_per_category": 50,
    "include_slang": true,
    ...
  }
}
    """)


def main():
    """메인 함수"""
    print("🎯 테스트 데이터 설정 파일 사용 예제")
    print("=" * 50)
    
    # 설정 파일 사용 예제
    test_custom_config()
    
    # 사용법 안내
    show_config_usage()
    
    # 설정 파일 구조 설명
    show_config_structure()
    
    print("\n💡 팁:")
    print("- 설정 파일을 수정한 후에는 테스트를 다시 실행하세요.")
    print("- 새로운 은어나 메뉴를 추가하면 자동으로 테스트케이스에 포함됩니다.")
    print("- 백업을 정기적으로 생성하는 것을 권장합니다.")
    print("- 설정 파일이 없으면 기본 설정으로 자동 생성됩니다.")


if __name__ == "__main__":
    main() 