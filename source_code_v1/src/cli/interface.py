"""
기본 CLI 인터페이스 모듈
개발 및 테스트용 간단한 CLI 인터페이스를 제공합니다.
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import argparse

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ..config import config_manager
from ..logger import setup_logging, get_logger
from ..main import VoiceKioskPipeline
from ..models.order_models import OrderStatus


class CLIInterface:
    """CLI 인터페이스 클래스"""
    
    def __init__(self):
        """CLI 인터페이스 초기화"""
        self.logger = get_logger(__name__)
        self.pipeline: Optional[VoiceKioskPipeline] = None
        self.is_running = False
        
        # CLI 명령어 매핑
        self.commands = {
            'help': self.show_help,
            '도움말': self.show_help,
            'status': self.show_status,
            '상태': self.show_status,
            'order': self.show_order,
            '주문확인': self.show_order,
            'menu': self.show_menu,
            '메뉴': self.show_menu,
            'clear': self.clear_order,
            '초기화': self.clear_order,
            'config': self.show_config,
            '설정': self.show_config,
            'quit': self.quit_system,
            'exit': self.quit_system,
            '종료': self.quit_system,
            'q': self.quit_system,
            'new': self.new_order,
            '새주문': self.new_order,
            'demo': self.run_demo,
            '데모': self.run_demo,
            'test': self.run_test,
            '테스트': self.run_test
        }
    
    def initialize(self) -> bool:
        """CLI 시스템 초기화"""
        try:
            self.logger.info("CLI 인터페이스 초기화 시작...")
            
            # 파이프라인 초기화
            self.pipeline = VoiceKioskPipeline()
            
            if not self.pipeline.initialize_system():
                self.logger.warning("파이프라인 초기화 실패, 제한된 기능으로 실행됩니다.")
                # 파이프라인 초기화가 실패해도 CLI는 계속 실행
                # 일부 기능만 제한됩니다.
            
            self.logger.info("CLI 인터페이스 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"CLI 초기화 중 오류: {e}")
            return False
    
    def show_welcome(self):
        """환영 메시지 출력"""
        print("\n" + "="*70)
        print("🎤 음성 기반 키오스크 AI 주문 시스템 - CLI 인터페이스")
        print("="*70)
        print("💡 사용법:")
        print("  • 텍스트로 주문하세요 (예: '빅맥 세트 하나 주세요')")
        print("  • 음성 파일 테스트: 'file:경로' 형식으로 입력")
        print("  • 명령어: help, status, order, menu, clear, config, demo, test")
        print("  • 종료: quit, exit, 종료, q")
        print("="*70)
        
        # 시스템 상태 간단히 표시
        if self.pipeline:
            status = self.pipeline.get_system_status()
            modules_status = status.get('modules', {})
            
            print("시스템 모듈 상태:")
            status_icons = {True: "OK", False: "NG"}
            
            print(f"  • 음성 처리: {status_icons.get(modules_status.get('audio_processor', False))}")
            print(f"  • 음성 인식: {status_icons.get(modules_status.get('speech_recognizer', False))}")
            print(f"  • 의도 파악: {status_icons.get(modules_status.get('intent_recognizer', False))}")
            print(f"  • 대화 관리: {status_icons.get(modules_status.get('dialogue_manager', False))}")
            print(f"  • 주문 관리: {status_icons.get(modules_status.get('order_manager', False))}")
            
            if not modules_status.get('speech_recognizer', False):
                print("⚠️  음성 인식 모듈을 사용할 수 없습니다. 텍스트 입력만 지원됩니다.")
        
        print("="*70)
    
    def show_help(self, args: List[str] = None):
        """도움말 표시"""
        print("\n사용 가능한 명령어:")
        print("-" * 50)
        
        commands_help = {
            'help, 도움말': '이 도움말을 표시합니다',
            'status, 상태': '시스템 상태를 표시합니다',
            'order, 주문확인': '현재 주문 내역을 표시합니다',
            'menu, 메뉴': '사용 가능한 메뉴를 표시합니다',
            'clear, 초기화': '현재 주문을 초기화합니다',
            'config, 설정': '시스템 설정 정보를 표시합니다',
            'new, 새주문': '새로운 주문을 시작합니다',
            'demo, 데모': '데모 시나리오를 실행합니다',
            'test, 테스트': '시스템 테스트를 실행합니다',
            'quit/exit/종료/q': '시스템을 종료합니다'
        }
        
        for cmd, desc in commands_help.items():
            print(f"  {cmd:<20} : {desc}")
        
        print("\n💬 주문 예시:")
        print("  • '빅맥 세트 하나 주세요'")
        print("  • '콜라를 사이다로 바꿔주세요'")
        print("  • '감자튀김 추가해주세요'")
        print("  • '결제할게요'")
        
        print("\n🎵 음성 파일 테스트:")
        print("  • 'file:audio_samples/order1.wav'")
        print("  • 'file:/path/to/audio.wav'")
    
    def show_status(self, args: List[str] = None):
        """시스템 상태 표시"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        try:
            status = self.pipeline.get_system_status()
        except Exception as e:
            print(f"시스템 상태를 가져올 수 없습니다: {e}")
            return
        
        print("\n시스템 상태:")
        print("-" * 40)
        print(f"초기화됨: {'OK' if status.get('initialized') else 'NG'}")
        print(f"실행 중: {'OK' if status.get('running') else 'NG'}")
        print(f"현재 세션: {status.get('current_session', 'None')}")
        
        print("\n🔧 모듈 상태:")
        modules = status.get('modules', {})
        for module_name, is_available in modules.items():
            status_icon = 'OK' if is_available else 'NG'
            module_display_name = {
                'audio_processor': '음성 처리',
                'speech_recognizer': '음성 인식',
                'intent_recognizer': '의도 파악',
                'dialogue_manager': '대화 관리',
                'order_manager': '주문 관리',
                'response_system': '응답 시스템'
            }.get(module_name, module_name)
            
            print(f"  {module_display_name}: {status_icon}")
        
        # 주문 통계
        order_stats = status.get('order_stats')
        if order_stats:
            print("\n📈 주문 통계:")
            print(f"  총 주문 수: {order_stats.get('total_orders', 0)}")
            print(f"  완료된 주문: {order_stats.get('completed_orders', 0)}")
            print(f"  취소된 주문: {order_stats.get('cancelled_orders', 0)}")
        
        # 세션 통계
        session_stats = status.get('session_stats')
        if session_stats:
            print("\n💬 세션 통계:")
            print(f"  활성 세션 수: {session_stats.get('active_sessions', 0)}")
            print(f"  총 세션 수: {session_stats.get('total_sessions', 0)}")
    
    def show_order(self, args: List[str] = None):
        """현재 주문 내역 표시"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        if not self.pipeline.order_manager:
            print("주문 관리자를 사용할 수 없습니다.")
            return
        
        try:
            order_summary = self.pipeline.order_manager.get_order_summary()
            
            if not order_summary or not order_summary.items:
                print("\n📝 현재 주문 내역이 없습니다.")
                return
            
            print("\n📝 현재 주문 내역:")
            print("-" * 50)
            
            for i, item in enumerate(order_summary.items, 1):
                print(f"{i}. {item.name}")
                print(f"   카테고리: {item.category}")
                print(f"   수량: {item.quantity}개")
                print(f"   가격: {item.price:,}원")
                
                if item.options:
                    print("   옵션:")
                    for option_name, option_value in item.options.items():
                        print(f"     - {option_name}: {option_value}")
                print()
            
            print("-" * 50)
            print(f"총 {len(order_summary.items)}개 메뉴")
            print(f"총 금액: {order_summary.total_amount:,}원")
            print(f"주문 상태: {order_summary.status.value}")
            
        except Exception as e:
            self.logger.error(f"주문 내역 표시 중 오류: {e}")
            print(f"주문 내역을 가져오는 중 오류가 발생했습니다: {e}")
    
    def show_menu(self, args: List[str] = None):
        """메뉴 표시"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        if not self.pipeline.order_manager:
            print("주문 관리자를 사용할 수 없습니다.")
            return
        
        try:
            menu = self.pipeline.order_manager.menu
            
            print("\n🍔 사용 가능한 메뉴:")
            print("=" * 60)
            
            # 카테고리별로 메뉴 표시
            for category in menu.categories:
                print(f"\n📂 {category}")
                print("-" * 40)
                
                category_items = menu.get_items_by_category(category)
                
                if not category_items:
                    print("  메뉴가 없습니다.")
                    continue
                
                for item in category_items:
                    print(f"  • {item.name}")
                    print(f"    가격: {item.price:,}원")
                    if item.description:
                        print(f"    설명: {item.description}")
                    
                    # 세트 옵션 표시
                    if hasattr(item, 'set_drink_options') and item.set_drink_options:
                        if isinstance(item.set_drink_options, (list, tuple)):
                            print(f"    음료 선택: {', '.join(item.set_drink_options)}")
                        else:
                            print(f"    음료 선택: {item.set_drink_options}")
                    
                    if hasattr(item, 'set_side_options') and item.set_side_options:
                        if isinstance(item.set_side_options, (list, tuple)):
                            print(f"    사이드 선택: {', '.join(item.set_side_options)}")
                        else:
                            print(f"    사이드 선택: {item.set_side_options}")
                    
                    print()
            
            print("=" * 60)
            
        except Exception as e:
            self.logger.error(f"메뉴 표시 중 오류: {e}")
            print(f"메뉴를 가져오는 중 오류가 발생했습니다: {e}")
    
    def clear_order(self, args: List[str] = None):
        """현재 주문 초기화"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        try:
            # 새로운 세션 시작 (기존 주문 초기화)
            self.pipeline.start_session()
            print("✅ 주문이 초기화되었습니다. 새로운 주문을 시작하세요.")
            
        except Exception as e:
            self.logger.error(f"주문 초기화 중 오류: {e}")
            print(f"주문 초기화 중 오류가 발생했습니다: {e}")
    
    def show_config(self, args: List[str] = None):
        """시스템 설정 정보 표시"""
        try:
            config_summary = config_manager.get_config_summary()
            
            print("\n⚙️ 시스템 설정:")
            print("=" * 50)
            
            # API 설정
            api_config = config_summary.get('api', {})
            print("🔑 API 설정:")
            print(f"  모델: {api_config.get('model', 'Unknown')}")
            print(f"  최대 토큰: {api_config.get('max_tokens', 'Unknown')}")
            print(f"  온도: {api_config.get('temperature', 'Unknown')}")
            print(f"  API 키 설정됨: {'OK' if api_config.get('api_key_set') else 'NG'}")
            
            # 메뉴 설정
            menu_config = config_summary.get('menu', {})
            print("\n🍔 메뉴 설정:")
            print(f"  식당명: {menu_config.get('restaurant_name', 'Unknown')}")
            print(f"  식당 타입: {menu_config.get('restaurant_type', 'Unknown')}")
            print(f"  메뉴 아이템 수: {menu_config.get('menu_items_count', 0)}")
            print(f"  카테고리 수: {menu_config.get('categories_count', 0)}")
            
            last_modified = menu_config.get('last_modified')
            if last_modified:
                print(f"  마지막 수정: {last_modified}")
            
            # 음성 설정
            audio_config = config_summary.get('audio', {})
            print("\n🎤 음성 설정:")
            print(f"  샘플링 레이트: {audio_config.get('sample_rate', 'Unknown')} Hz")
            print(f"  청크 크기: {audio_config.get('chunk_size', 'Unknown')}")
            print(f"  노이즈 감소 레벨: {audio_config.get('noise_reduction_level', 'Unknown')}")
            print(f"  화자 분리 임계값: {audio_config.get('speaker_separation_threshold', 'Unknown')}")
            
            # 시스템 설정
            system_config = config_summary.get('system', {})
            print("\n🖥️ 시스템 설정:")
            print(f"  로그 레벨: {system_config.get('log_level', 'Unknown')}")
            print(f"  언어: {system_config.get('language', 'Unknown')}")
            
            print("=" * 50)
            
        except Exception as e:
            self.logger.error(f"설정 정보 표시 중 오류: {e}")
            print(f"설정 정보를 가져오는 중 오류가 발생했습니다: {e}")
    
    def new_order(self, args: List[str] = None):
        """새로운 주문 시작"""
        self.clear_order()
    
    def quit_system(self, args: List[str] = None):
        """시스템 종료"""
        print("\n👋 시스템을 종료합니다...")
        self.is_running = False
        
        if self.pipeline:
            self.pipeline.shutdown()
        
        print("이용해 주셔서 감사합니다!")
    
    def run_demo(self, args: List[str] = None):
        """데모 시나리오 실행"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        print("\n🎬 데모 시나리오를 실행합니다...")
        print("=" * 50)
        
        demo_scenarios = [
            "빅맥 세트 하나 주세요",
            "콜라를 사이다로 바꿔주세요",
            "감자튀김 추가해주세요",
            "현재 주문 확인해주세요",
            "결제할게요"
        ]
        
        for i, scenario in enumerate(demo_scenarios, 1):
            print(f"\n{i}. 시나리오: '{scenario}'")
            print("-" * 30)
            
            try:
                response = self.pipeline.process_text_input(scenario)
                print(f"🤖 응답: {response}")
                
                # 잠시 대기
                time.sleep(1)
                
            except Exception as e:
                print(f"시나리오 실행 중 오류: {e}")
        
        print("\n데모 시나리오 완료!")
    
    def run_test(self, args: List[str] = None):
        """시스템 테스트 실행"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        print("\n🧪 시스템 테스트를 실행합니다...")
        print("=" * 50)
        
        test_cases = [
            {
                'name': '기본 주문 테스트',
                'input': '빅맥 세트 하나 주세요',
                'expected_intent': 'ORDER'
            },
            {
                'name': '주문 변경 테스트',
                'input': '콜라를 사이다로 바꿔주세요',
                'expected_intent': 'MODIFY'
            },
            {
                'name': '주문 취소 테스트',
                'input': '빅맥 취소해주세요',
                'expected_intent': 'CANCEL'
            },
            {
                'name': '결제 테스트',
                'input': '결제할게요',
                'expected_intent': 'PAYMENT'
            },
            {
                'name': '문의 테스트',
                'input': '메뉴 추천해주세요',
                'expected_intent': 'INQUIRY'
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print(f"입력: '{test_case['input']}'")
            
            try:
                # 새로운 세션으로 테스트
                session_id = self.pipeline.start_session()
                
                # 의도 파악 테스트
                context = self.pipeline.dialogue_manager.get_context(session_id)
                intent = self.pipeline.intent_recognizer.recognize_intent(
                    test_case['input'], context
                )
                
                expected_intent = test_case['expected_intent']
                actual_intent = intent.type.value
                
                if actual_intent == expected_intent:
                    print(f"✅ 통과 - 의도: {actual_intent}")
                    passed_tests += 1
                else:
                    print(f"실패 - 예상: {expected_intent}, 실제: {actual_intent}")
                
                # 전체 파이프라인 테스트
                response = self.pipeline.process_text_input(test_case['input'])
                print(f"응답: {response[:100]}...")  # 응답의 첫 100자만 표시
                
            except Exception as e:
                print(f"테스트 실행 중 오류: {e}")
        
        print(f"\n테스트 결과: {passed_tests}/{total_tests} 통과")
        success_rate = (passed_tests / total_tests) * 100
        print(f"성공률: {success_rate:.1f}%")
    
    def process_command(self, user_input: str) -> bool:
        """명령어 처리"""
        parts = user_input.strip().split()
        if not parts:
            return True
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if command in self.commands:
            try:
                self.commands[command](args)
            except Exception as e:
                self.logger.error(f"명령어 '{command}' 실행 중 오류: {e}")
                print(f"명령어 실행 중 오류가 발생했습니다: {e}")
            return True
        
        return False
    
    def run_interactive_mode(self):
        """대화형 모드 실행"""
        if not self.pipeline:
            print("파이프라인이 초기화되지 않았습니다.")
            return
        
        self.is_running = True
        self.show_welcome()
        
        # 첫 번째 세션 시작
        try:
            self.pipeline.start_session()
        except Exception as e:
            self.logger.error(f"초기 세션 시작 실패: {e}")
            print(f"초기 세션 시작에 실패했습니다: {e}")
            return
        
        try:
            while self.is_running:
                try:
                    # 사용자 입력 받기
                    user_input = input("\n👤 입력: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # 명령어 처리 시도
                    if self.process_command(user_input):
                        continue
                    
                    # 음성 파일 입력 처리
                    if user_input.startswith('file:'):
                        file_path = user_input[5:].strip()
                        if not os.path.exists(file_path):
                            print(f"파일을 찾을 수 없습니다: {file_path}")
                            continue
                        
                        print(f"🎵 음성 파일 처리 중: {file_path}")
                        response = self.pipeline.process_audio_input(file_path)
                    else:
                        # 일반 텍스트 입력 처리
                        response = self.pipeline.process_text_input(user_input)
                    
                    # 응답 출력
                    print(f"\n🤖 {response}")
                    
                except KeyboardInterrupt:
                    print("\n\n👋 이용해 주셔서 감사합니다!")
                    break
                except Exception as e:
                    self.logger.error(f"입력 처리 중 오류: {e}")
                    print(f"\n처리 중 오류가 발생했습니다: {e}")
                    print("다시 시도해 주세요.")
        
        finally:
            self.is_running = False
            if self.pipeline:
                self.pipeline.shutdown()


def create_argument_parser():
    """명령행 인수 파서 생성"""
    parser = argparse.ArgumentParser(
        description='음성 기반 키오스크 AI 주문 시스템 CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python -m src.cli.interface                    # 대화형 모드
  python -m src.cli.interface --demo             # 데모 실행
  python -m src.cli.interface --test             # 테스트 실행
  python -m src.cli.interface --status           # 상태 확인
        """
    )
    
    parser.add_argument(
        '--demo', 
        action='store_true',
        help='데모 시나리오를 실행합니다'
    )
    
    parser.add_argument(
        '--test',
        action='store_true', 
        help='시스템 테스트를 실행합니다'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='시스템 상태를 확인합니다'
    )
    
    parser.add_argument(
        '--config',
        action='store_true',
        help='시스템 설정을 표시합니다'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='로그 레벨을 설정합니다 (기본값: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='로그 파일 경로를 지정합니다'
    )
    
    return parser


def main():
    """메인 실행 함수"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    log_file = args.log_file or "logs/cli_interface.log"
    setup_logging(log_level=args.log_level, log_file=log_file)
    
    logger = get_logger("cli_main")
    logger.info("CLI 인터페이스를 시작합니다.")
    
    try:
        # CLI 인터페이스 초기화
        cli = CLIInterface()
        
        if not cli.initialize():
            print("CLI 시스템 초기화에 실패했습니다.")
            sys.exit(1)
        
        # 명령행 옵션에 따른 실행
        if args.demo:
            cli.run_demo()
        elif args.test:
            cli.run_test()
        elif args.status:
            cli.show_status()
        elif args.config:
            cli.show_config()
        else:
            # 기본 대화형 모드
            cli.run_interactive_mode()
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류가 발생했습니다: {e}")
        print(f"시스템 오류: {e}")
        sys.exit(1)
    finally:
        logger.info("CLI 인터페이스를 종료합니다.")


if __name__ == "__main__":
    main()