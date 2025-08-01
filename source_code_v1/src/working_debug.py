#!/usr/bin/env python3
"""
작동하는 디버그 도구 (커스텀 OpenAI 클라이언트 사용)
"""

import sys
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 프로젝트 루트를 Python 경로에 추가 (직접 실행 시)
if __name__ == "__main__":
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# 환경 변수 로드
try:
    from .utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key
    from .utils.openai_client import create_openai_client
    from .config import config_manager
    from .logger import setup_logging, get_logger
    from .order.menu import Menu
    from .order.order import OrderManager
    from .response.text_response import TextResponseSystem
except ImportError:
    # 직접 실행 시 절대 import 사용
    from src.utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key
    from src.utils.openai_client import create_openai_client
    from src.config import config_manager
    from src.logger import setup_logging, get_logger
    from src.order.menu import Menu
    from src.order.order import OrderManager
    from src.response.text_response import TextResponseSystem

ensure_env_loaded()


@dataclass
class ProcessingResult:
    """처리 결과"""
    input_text: str
    llm_response: Optional[str] = None
    order_state: Optional[Dict] = None
    final_response: Optional[str] = None
    processing_time: Optional[float] = None
    errors: Optional[list] = None


class WorkingDebugSystem:
    """작동하는 디버그 시스템"""
    
    def __init__(self, debug_options: Dict[str, bool]):
        self.debug_options = debug_options
        self.logger = get_logger(__name__)
        
        # 시스템 컴포넌트들
        self.openai_client = None
        self.order_manager = None
        self.response_system = None
        
        self.is_initialized = False
    
    def initialize_system(self) -> bool:
        """시스템 초기화"""
        try:
            if self.debug_options.get('verbose'):
                print("🔧 시스템 초기화 시작...")
            
            # 1. 설정 로드
            menu_config = config_manager.load_menu_config()
            if self.debug_options.get('verbose'):
                print(f"✅ 메뉴 설정 로드 완료 ({len(menu_config.menu_items)}개 메뉴)")
            
            # 2. 메뉴 시스템 초기화
            from dataclasses import asdict
            menu = Menu.from_dict({
                "restaurant_info": menu_config.restaurant_info,
                "categories": menu_config.categories,
                "menu_items": {name: asdict(item) for name, item in menu_config.menu_items.items()},
                "set_pricing": menu_config.set_pricing,
                "option_pricing": menu_config.option_pricing
            })
            
            self.order_manager = OrderManager(menu)
            self.response_system = TextResponseSystem()
            
            if self.debug_options.get('verbose'):
                print("✅ 기본 시스템 초기화 완료")
            
            # 3. OpenAI 클라이언트 초기화 (선택적)
            api_key = get_api_key()
            if api_key and validate_api_key(api_key):
                try:
                    self.openai_client = create_openai_client(api_key)
                    if self.debug_options.get('verbose'):
                        print("✅ OpenAI 클라이언트 초기화 완료")
                except Exception as e:
                    if self.debug_options.get('verbose'):
                        print(f"⚠️ OpenAI 클라이언트 초기화 실패: {e}")
                        print("   기본 기능만 사용합니다.")
            else:
                if self.debug_options.get('verbose'):
                    print("⚠️ API 키가 없어 기본 기능만 사용합니다.")
            
            self.is_initialized = True
            if self.debug_options.get('verbose'):
                print("🎉 시스템 초기화 완료!")
            
            return True
            
        except Exception as e:
            if self.debug_options.get('verbose'):
                print(f"❌ 시스템 초기화 실패: {e}")
            return False
    
    def process_text_with_llm(self, text: str) -> ProcessingResult:
        """텍스트를 LLM으로 처리"""
        start_time = time.time()
        result = ProcessingResult(
            input_text=text,
            errors=[]
        )
        
        try:
            if self.debug_options.get('verbose'):
                print(f"\n💬 텍스트 처리: \"{text}\"")
            
            # 1. LLM으로 의도 파악 (OpenAI 클라이언트 사용)
            if self.openai_client:
                try:
                    if self.debug_options.get('show_llm_processing'):
                        print("   🧠 LLM으로 의도 파악 중...")
                    
                    messages = [
                        {
                            "role": "system",
                            "content": """당신은 식당 키오스크 AI입니다. 사용자의 입력을 분석하여 의도를 파악하고 적절한 응답을 생성하세요.

가능한 의도:
- ORDER: 메뉴 주문
- MODIFY: 주문 수정
- CANCEL: 주문 취소
- INQUIRY: 문의
- PAYMENT: 결제

사용 가능한 메뉴: 빅맥, 상하이버거, 맥치킨, 감자튀김, 치킨너겟, 콜라, 사이다, 아이스크림

응답 형식:
의도: [의도]
메뉴: [메뉴명]
수량: [수량]
응답: [고객에게 할 응답]"""
                        },
                        {
                            "role": "user",
                            "content": text
                        }
                    ]
                    
                    response = self.openai_client.chat_completions_create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        max_tokens=200,
                        temperature=0.7
                    )
                    
                    result.llm_response = response.choices[0].message.content
                    
                    if self.debug_options.get('show_llm_processing'):
                        print(f"   🤖 LLM 응답: {result.llm_response}")
                    
                except Exception as e:
                    error_msg = f"LLM 처리 실패: {e}"
                    result.errors.append(error_msg)
                    if self.debug_options.get('verbose'):
                        print(f"   ❌ {error_msg}")
            
            # 2. 간단한 키워드 기반 주문 처리 (LLM 없이도 작동)
            if self.order_manager:
                try:
                    # 메뉴 키워드 찾기
                    menu_config = config_manager.load_menu_config()
                    found_menu = None
                    quantity = 1
                    
                    for menu_name in menu_config.menu_items.keys():
                        if menu_name in text:
                            found_menu = menu_name
                            break
                    
                    # 수량 추출
                    for word in text.split():
                        if word.isdigit():
                            quantity = int(word)
                            break
                    
                    if found_menu:
                        # 새 주문이 없으면 생성
                        if not self.order_manager.get_current_order():
                            self.order_manager.create_new_order()
                        
                        # 주문 추가
                        add_result = self.order_manager.add_item(found_menu, quantity)
                        
                        if add_result.success:
                            if self.debug_options.get('show_order_management'):
                                print(f"   ✅ {found_menu} {quantity}개 주문 추가 성공")
                            
                            # 주문 상태 업데이트
                            current_order = self.order_manager.get_current_order()
                            if current_order:
                                result.order_state = {
                                    "items": [asdict(item) for item in current_order.items],
                                    "total_amount": float(current_order.total_amount),
                                    "item_count": len(current_order.items)
                                }
                                
                                if self.debug_options.get('show_order_management'):
                                    self._display_order_state(result.order_state)
                            
                            # 응답 생성
                            if self.response_system:
                                confirmation = self.response_system.generate_order_confirmation(
                                    menu_name=found_menu,
                                    quantity=quantity,
                                    total_amount=int(current_order.total_amount) if current_order else 0
                                )
                                result.final_response = confirmation.formatted_text
                        else:
                            result.errors.append(f"주문 추가 실패: {add_result.message}")
                    else:
                        # 메뉴를 찾지 못한 경우
                        if self.response_system:
                            error_response = self.response_system.generate_error_response(
                                error_message="메뉴를 찾을 수 없습니다"
                            )
                            result.final_response = error_response.formatted_text
                        else:
                            result.final_response = "죄송합니다. 메뉴를 찾을 수 없습니다."
                
                except Exception as e:
                    error_msg = f"주문 처리 실패: {e}"
                    result.errors.append(error_msg)
                    if self.debug_options.get('verbose'):
                        print(f"   ❌ {error_msg}")
            
            # 3. 최종 응답 설정
            if not result.final_response:
                if result.llm_response:
                    result.final_response = result.llm_response
                else:
                    result.final_response = "처리가 완료되었습니다."
            
            if self.debug_options.get('show_response_generation'):
                print(f"   🗣️ 최종 응답: \"{result.final_response}\"")
        
        except Exception as e:
            error_msg = f"텍스트 처리 중 오류: {e}"
            result.errors.append(error_msg)
            if self.debug_options.get('verbose'):
                print(f"❌ {error_msg}")
        
        result.processing_time = time.time() - start_time
        return result
    
    def _display_order_state(self, order_state: Dict):
        """주문 상태를 테이블 형태로 표시"""
        print("   📋 현재 주문 상태:")
        
        if not order_state.get("items"):
            print("      (주문된 메뉴가 없습니다)")
            return
        
        # 테이블 헤더
        print("   ┌─────────────────┬──────┬──────────┬──────────┐")
        print("   │ 메뉴            │ 수량 │ 단가     │ 소계     │")
        print("   ├─────────────────┼──────┼──────────┼──────────┤")
        
        # 메뉴 아이템들
        for item in order_state["items"]:
            name = item["name"][:15]  # 이름 길이 제한
            quantity = item["quantity"]
            price = item["price"]
            subtotal = quantity * price
            
            print(f"   │ {name:<15} │ {quantity:>4} │ {price:>6,}원 │ {subtotal:>6,}원 │")
        
        # 테이블 푸터
        print("   └─────────────────┴──────┴──────────┴──────────┘")
        print(f"   💰 총 금액: {order_state['total_amount']:,.0f}원")
    
    def run_interactive_mode(self):
        """대화형 모드 실행"""
        print("🎤 작동하는 음성 키오스크 시스템 (대화형 모드)")
        print("=" * 60)
        
        if self.debug_options.get('debug'):
            print("🐛 디버그 모드가 활성화되었습니다.")
        
        if self.openai_client:
            print("🤖 OpenAI API 연동이 활성화되었습니다.")
        else:
            print("⚠️ OpenAI API 없이 기본 기능으로 실행됩니다.")
        
        print("💡 'quit' 또는 'exit'를 입력하면 종료됩니다.")
        print("💡 'clear'를 입력하면 주문을 초기화합니다.")
        print("💡 'status'를 입력하면 현재 주문 상태를 확인합니다.")
        print()
        
        # 인사말
        if self.response_system:
            greeting = self.response_system.generate_greeting()
            print(f"🤖 {greeting.formatted_text}")
        
        while True:
            try:
                user_input = input("\n👤 사용자: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("👋 시스템을 종료합니다.")
                    break
                
                if user_input.lower() in ['clear', '초기화']:
                    if self.order_manager:
                        self.order_manager.create_new_order()
                        print("🗑️ 주문이 초기화되었습니다.")
                    continue
                
                if user_input.lower() in ['status', '상태']:
                    if self.order_manager:
                        current_order = self.order_manager.get_current_order()
                        if current_order:
                            order_state = {
                                "items": [asdict(item) for item in current_order.items],
                                "total_amount": float(current_order.total_amount)
                            }
                            self._display_order_state(order_state)
                        else:
                            print("   📋 현재 주문된 메뉴가 없습니다.")
                    continue
                
                # 텍스트 처리
                result = self.process_text_with_llm(user_input)
                
                if result.final_response:
                    print(f"🤖 {result.final_response}")
                
                if result.errors:
                    for error in result.errors:
                        print(f"❌ 오류: {error}")
            
            except KeyboardInterrupt:
                print("\n👋 시스템을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 처리 중 오류가 발생했습니다: {e}")


def create_argument_parser():
    """명령행 인수 파서 생성"""
    parser = argparse.ArgumentParser(
        description="작동하는 음성 키오스크 디버그 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 기본 옵션
    parser.add_argument('--mode', choices=['text', 'interactive'], 
                       default='interactive', help='실행 모드 선택')
    parser.add_argument('--input', help='입력 텍스트')
    
    # 디버그 옵션
    parser.add_argument('--debug', action='store_true', help='전체 디버그 모드 활성화')
    parser.add_argument('--verbose', action='store_true', help='상세 로그 출력')
    
    # 상세 출력 옵션
    parser.add_argument('--show-llm-processing', action='store_true', 
                       help='LLM 처리 과정 표시')
    parser.add_argument('--show-order-management', action='store_true', 
                       help='주문 관리 과정 표시')
    parser.add_argument('--show-response-generation', action='store_true', 
                       help='응답 생성 과정 표시')
    
    return parser


def main():
    """메인 실행 함수"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    log_level = "DEBUG" if args.debug or args.verbose else "INFO"
    setup_logging(log_level=log_level)
    
    # 디버그 옵션 설정
    debug_options = {
        'debug': args.debug,
        'verbose': args.verbose or args.debug,
        'show_llm_processing': args.show_llm_processing or args.debug,
        'show_order_management': args.show_order_management or args.debug,
        'show_response_generation': args.show_response_generation or args.debug,
    }
    
    # 시스템 초기화
    system = WorkingDebugSystem(debug_options)
    
    if not system.initialize_system():
        print("❌ 시스템 초기화에 실패했습니다.")
        sys.exit(1)
    
    # 모드별 실행
    if args.mode == 'interactive':
        system.run_interactive_mode()
    
    elif args.mode == 'text':
        if not args.input:
            print("❌ 입력 텍스트를 --input 옵션으로 지정해주세요.")
            sys.exit(1)
        
        result = system.process_text_with_llm(args.input)
        
        if result.final_response:
            print(f"\n🤖 최종 응답: {result.final_response}")
        
        if result.errors:
            print("\n❌ 오류:")
            for error in result.errors:
                print(f"  - {error}")


if __name__ == "__main__":
    main()