#!/usr/bin/env python3
"""
테스트 데이터 설정 파일 관리 유틸리티
홈 디렉토리의 test_data_config.json 파일을 관리합니다.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

class TestDataManager:
    """테스트 데이터 설정 파일 관리자"""
    
    def __init__(self):
        # 프로젝트 루트 디렉토리 찾기
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / "test_config" / "test_data_config.json"
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if not self.config_file.exists():
            print(f"설정 파일이 존재하지 않습니다: {self.config_file}")
            print("기본 설정으로 새로 생성합니다.")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            return self._get_default_config()
    
    def _save_config(self):
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            print(f"설정 파일 저장 완료: {self.config_file}")
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
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
                "치즈스틱": "모짜렐라 치즈스틱"
            },
            "menu_items": [
                "빅맥", "상하이 스파이시 치킨버거", "베이컨 토마토 디럭스",
                "치즈버거", "맥치킨", "불고기버거", "새우버거",
                "더블치즈버거", "쿼터파운더", "맥스파이시 상하이버거",
                "치킨 맥너겟", "감자튀김", "코카콜라", "스프라이트",
                "아이스 아메리카노", "핫 아메리카노", "카페라떼", "맥플러리"
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
    
    def show_status(self):
        """현재 설정 상태 표시"""
        print("📊 테스트 데이터 설정 상태")
        print("=" * 50)
        print(f"설정 파일: {self.config_file}")
        print(f"은어 매핑: {len(self.config_data.get('slang_mappings', {}))}개")
        print(f"메뉴 아이템: {len(self.config_data.get('menu_items', []))}개")
        print(f"수량 표현: {len(self.config_data.get('quantity_expressions', []))}개")
        print(f"옵션 표현: {len(self.config_data.get('option_expressions', []))}개")
        print(f"반말 패턴: {len(self.config_data.get('informal_patterns', []))}개")
        print(f"복합 패턴: {len(self.config_data.get('complex_patterns', []))}개")
        print(f"엣지 케이스: {len(self.config_data.get('edge_cases', []))}개")
        print()
    
    def add_slang(self, slang: str, full_name: str):
        """은어 추가"""
        if 'slang_mappings' not in self.config_data:
            self.config_data['slang_mappings'] = {}
        
        self.config_data['slang_mappings'][slang] = full_name
        print(f"✅ 은어 추가: '{slang}' → '{full_name}'")
        self._save_config()
    
    def remove_slang(self, slang: str):
        """은어 제거"""
        if 'slang_mappings' in self.config_data and slang in self.config_data['slang_mappings']:
            del self.config_data['slang_mappings'][slang]
            print(f"✅ 은어 제거: '{slang}'")
            self._save_config()
        else:
            print(f"❌ 은어를 찾을 수 없습니다: '{slang}'")
    
    def add_menu_item(self, menu: str):
        """메뉴 아이템 추가"""
        if 'menu_items' not in self.config_data:
            self.config_data['menu_items'] = []
        
        if menu not in self.config_data['menu_items']:
            self.config_data['menu_items'].append(menu)
            print(f"✅ 메뉴 추가: '{menu}'")
            self._save_config()
        else:
            print(f"⚠️ 메뉴가 이미 존재합니다: '{menu}'")
    
    def remove_menu_item(self, menu: str):
        """메뉴 아이템 제거"""
        if 'menu_items' in self.config_data and menu in self.config_data['menu_items']:
            self.config_data['menu_items'].remove(menu)
            print(f"✅ 메뉴 제거: '{menu}'")
            self._save_config()
        else:
            print(f"❌ 메뉴를 찾을 수 없습니다: '{menu}'")
    
    def add_edge_case(self, edge_case: str):
        """엣지 케이스 추가"""
        if 'edge_cases' not in self.config_data:
            self.config_data['edge_cases'] = []
        
        if edge_case not in self.config_data['edge_cases']:
            self.config_data['edge_cases'].append(edge_case)
            print(f"✅ 엣지 케이스 추가: '{edge_case}'")
            self._save_config()
        else:
            print(f"⚠️ 엣지 케이스가 이미 존재합니다: '{edge_case}'")
    
    def list_slangs(self):
        """은어 목록 표시"""
        print("🗣️ 은어 목록")
        print("-" * 30)
        slang_mappings = self.config_data.get('slang_mappings', {})
        if not slang_mappings:
            print("등록된 은어가 없습니다.")
            return
        
        for slang, full_name in slang_mappings.items():
            print(f"  {slang} → {full_name}")
        print()
    
    def list_menu_items(self):
        """메뉴 목록 표시"""
        print("🍔 메뉴 목록")
        print("-" * 30)
        menu_items = self.config_data.get('menu_items', [])
        if not menu_items:
            print("등록된 메뉴가 없습니다.")
            return
        
        for i, menu in enumerate(menu_items, 1):
            print(f"  {i:2d}. {menu}")
        print()
    
    def reset_to_default(self):
        """기본 설정으로 초기화"""
        self.config_data = self._get_default_config()
        self._save_config()
        print("✅ 기본 설정으로 초기화 완료")
    
    def backup_config(self, backup_name: str = None):
        """설정 파일 백업"""
        if backup_name is None:
            from datetime import datetime
            backup_name = f"test_data_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_file = self.project_root / "test_config" / backup_name
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 백업 완료: {backup_file}")
        except Exception as e:
            print(f"❌ 백업 실패: {e}")


def main():
    """메인 함수"""
    manager = TestDataManager()
    
    if len(sys.argv) < 2:
        print("🔧 테스트 데이터 관리 도구")
        print("=" * 40)
        print("사용법:")
        print("  python manage_test_data.py [명령] [옵션]")
        print()
        print("명령:")
        print("  status                    - 현재 상태 표시")
        print("  slang                     - 은어 목록 표시")
        print("  menu                      - 메뉴 목록 표시")
        print("  add-slang [은어] [전체명] - 은어 추가")
        print("  remove-slang [은어]       - 은어 제거")
        print("  add-menu [메뉴명]         - 메뉴 추가")
        print("  remove-menu [메뉴명]      - 메뉴 제거")
        print("  add-edge [케이스]         - 엣지 케이스 추가")
        print("  reset                     - 기본 설정으로 초기화")
        print("  backup [파일명]           - 설정 백업")
        print()
        manager.show_status()
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        manager.show_status()
    
    elif command == "slang":
        manager.list_slangs()
    
    elif command == "menu":
        manager.list_menu_items()
    
    elif command == "add-slang":
        if len(sys.argv) < 4:
            print("❌ 사용법: add-slang [은어] [전체명]")
            return
        manager.add_slang(sys.argv[2], sys.argv[3])
    
    elif command == "remove-slang":
        if len(sys.argv) < 3:
            print("❌ 사용법: remove-slang [은어]")
            return
        manager.remove_slang(sys.argv[2])
    
    elif command == "add-menu":
        if len(sys.argv) < 3:
            print("❌ 사용법: add-menu [메뉴명]")
            return
        manager.add_menu_item(sys.argv[2])
    
    elif command == "remove-menu":
        if len(sys.argv) < 3:
            print("❌ 사용법: remove-menu [메뉴명]")
            return
        manager.remove_menu_item(sys.argv[2])
    
    elif command == "add-edge":
        if len(sys.argv) < 3:
            print("❌ 사용법: add-edge [케이스]")
            return
        manager.add_edge_case(sys.argv[2])
    
    elif command == "reset":
        confirm = input("정말로 기본 설정으로 초기화하시겠습니까? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            manager.reset_to_default()
        else:
            print("취소되었습니다.")
    
    elif command == "backup":
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        manager.backup_config(backup_name)
    
    else:
        print(f"❌ 알 수 없는 명령: {command}")


if __name__ == "__main__":
    main() 