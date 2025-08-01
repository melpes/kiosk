#!/usr/bin/env python3
"""
팀원용 디버그 가능한 음성 키오스크 시스템 실행 파일
상세한 처리 과정을 단계별로 확인할 수 있습니다.
"""

import sys
import argparse
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import librosa
import numpy as np

# 프로젝트 루트를 Python 경로에 추가 (직접 실행 시)
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# 환경 변수 로드
try:
    from .utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key
    from .config import config_manager
    from .logger import setup_logging, get_logger
    from .audio.preprocessing import AudioProcessor
    from .speech.recognition import SpeechRecognizer
    from .conversation.intent import IntentRecognizer
    from .conversation.dialogue import DialogueManager
    from .order.menu import Menu
    from .order.order import OrderManager
    from .response.text_response import TextResponseSystem
    from .models.audio_models import AudioData
    from .models.conversation_models import IntentType
    from .models.response_models import ResponseType
except ImportError:
    # 직접 실행 시 절대 import 사용
    from src.utils.env_loader import ensure_env_loaded, get_api_key, validate_api_key
    from src.config import config_manager
    from src.logger import setup_logging, get_logger
    from src.audio.preprocessing import AudioProcessor
    from src.speech.recognition import SpeechRecognizer
    from src.conversation.intent import IntentRecognizer
    from src.conversation.dialogue import DialogueManager
    from src.order.menu import Menu
    from src.order.order import OrderManager
    from src.response.text_response import TextResponseSystem
    from src.models.audio_models import AudioData
    from src.models.conversation_models import IntentType
    from src.models.response_models import ResponseType

ensure_env_loaded()


@dataclass
class ProcessingResult:
    """처리 결과를 담는 데이터 클래스"""
    input_type: str
    input_data: str
    transcription: Optional[str] = None
    transcription_confidence: Optional[float] = None
    intent_type: Optional[str] = None
    intent_confidence: Optional[float] = None
    intent_details: Optional[Dict] = None
    dialogue_response: Optional[str] = None
    dialogue_details: Optional[Dict] = None
    order_state: Optional[Dict] = None
    order_changes: Optional[List] = None
    final_response: Optional[str] = None
    processing_time: Optional[float] = None
    errors: Optional[List] = None


class DebugVoiceKiosk:
    """디버그 가능한 음성 키오스크 시스템"""
    
    def __init__(self, debug_options: Dict[str, bool]):
        """
        Args:
            debug_options: 디버그 옵션 딕셔너리
        """
        self.debug_options = debug_options
        self.logger = get_logger(__name__)
        
        # 시스템 컴포넌트들
        self.audio_processor: Optional[AudioProcessor] = None
        self.speech_recognizer: Optional[SpeechRecognizer] = None
        self.intent_recognizer: Optional[IntentRecognizer] = None
        self.dialogue_manager: Optional[DialogueManager] = None
        self.order_manager: Optional[OrderManager] = None
        self.response_system: Optional[TextResponseSystem] = None
        
        self.current_session_id: Optional[str] = None
        self.is_initialized = False
    
    def initialize_system(self) -> bool:
        """시스템 초기화"""
        try:
            if self.debug_options.get('verbose'):
                print("🔧 시스템 초기화 시작...")
            
            # 설정 로드
            api_config = config_manager.load_api_config()
            menu_config = config_manager.load_menu_config()
            
            if self.debug_options.get('verbose'):
                print(f"✅ 설정 로드 완료 (API 키: {'설정됨' if api_config.api_key else '없음'})")
            
            # 메뉴 시스템 초기화
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
                print(f"✅ 메뉴 시스템 초기화 완료 ({len(menu_config.menu_items)}개 메뉴)")
            
            # 음성 관련 모듈 (선택적)
            try:
                audio_config = config_manager.get_audio_config()
                self.audio_processor = AudioProcessor(audio_config)
                # 설정에서 Whisper 모델 정보 가져와서 초기화
                self.speech_recognizer = SpeechRecognizer(
                    model_name=audio_config.whisper_model,
                    language=audio_config.whisper_language,
                    device=audio_config.whisper_device
                )
                if self.debug_options.get('verbose'):
                    print("✅ 음성 처리 모듈 초기화 완료")
            except Exception as e:
                if self.debug_options.get('verbose'):
                    print(f"⚠️ 음성 처리 모듈 초기화 실패: {e}")
                    print("   텍스트 모드로만 실행됩니다.")
            
            # 대화 관련 모듈
            if api_config.api_key and api_config.api_key != "your_openai_api_key_here":
                try:
                    # API 키 재확인
                    try:
                        from .utils.env_loader import get_api_key, validate_api_key
                    except ImportError:
                        from src.utils.env_loader import get_api_key, validate_api_key
                    actual_api_key = get_api_key()
                    
                    if not validate_api_key(actual_api_key):
                        if self.debug_options.get('verbose'):
                            print("❌ 유효한 OpenAI API 키를 찾을 수 없습니다.")
                        return False
                    
                    # OpenAI 클라이언트 초기화 (간단한 방법)
                    try:
                        from openai import OpenAI
                        openai_client = OpenAI(api_key=actual_api_key)
                    except Exception as client_error:
                        if self.debug_options.get('verbose'):
                            print(f"⚠️ OpenAI 클라이언트 초기화 실패: {client_error}")
                            print("   기본 설정으로 재시도합니다...")
                        # 기본 설정으로 재시도
                        import openai
                        openai.api_key = actual_api_key
                        openai_client = None  # 구버전 호환
                    
                    # 의도 인식기 초기화 (API 키만 전달)
                    self.intent_recognizer = IntentRecognizer(api_key=actual_api_key)
                    
                    # 대화 관리자 초기화 (클라이언트 없이)
                    self.dialogue_manager = DialogueManager(self.order_manager)
                    
                    if self.debug_options.get('verbose'):
                        print("✅ 대화 처리 모듈 초기화 완료")
                        
                except Exception as e:
                    if self.debug_options.get('verbose'):
                        print(f"❌ 대화 처리 모듈 초기화 실패: {e}")
                        print("   API 키 없이 기본 기능만 사용합니다.")
                    # API 키 없이도 기본 기능은 사용 가능하도록
                    pass
            else:
                if self.debug_options.get('verbose'):
                    print("❌ OpenAI API 키가 설정되지 않았습니다.")
                    print("   기본 기능만 사용합니다.")
            
            self.is_initialized = True
            if self.debug_options.get('verbose'):
                print("🎉 시스템 초기화 완료!")
            
            return True
            
        except Exception as e:
            self.logger.error(f"시스템 초기화 실패: {e}")
            if self.debug_options.get('verbose'):
                print(f"❌ 시스템 초기화 실패: {e}")
            return False
    
    def process_audio_input(self, audio_path: str) -> ProcessingResult:
        """음성 파일 입력 처리"""
        start_time = time.time()
        result = ProcessingResult(
            input_type="audio",
            input_data=audio_path,
            errors=[]
        )
        
        try:
            if self.debug_options.get('show_transcription') or self.debug_options.get('verbose'):
                print(f"\n🎤 음성 파일 처리: {audio_path}")
            
            # 1. 음성 파일 로드 및 전처리
            # 파일 경로를 절대 경로로 변환
            audio_file_path = Path(audio_path)
            if not audio_file_path.is_absolute():
                # 상대 경로인 경우 현재 작업 디렉토리 기준으로 절대 경로 생성
                audio_file_path = Path.cwd() / audio_file_path
            
            if not audio_file_path.exists():
                error_msg = f"음성 파일을 찾을 수 없습니다: {audio_file_path}"
                result.errors.append(error_msg)
                if self.debug_options.get('verbose'):
                    print(f"❌ {error_msg}")
                return result
            
            # 절대 경로를 문자열로 변환하여 사용
            audio_path = str(audio_file_path)
            
            # 음성 파일 정보 표시
            if self.debug_options.get('show_transcription'):
                try:
                    audio_data, sr = librosa.load(audio_path, sr=16000)
                    duration = len(audio_data) / sr
                    print(f"   📊 파일 정보: {duration:.1f}초, 샘플레이트: {sr}Hz")
                except Exception as e:
                    print(f"   ⚠️ 파일 정보 로드 실패: {e}")
            
            # 2. 음성 인식
            if self.speech_recognizer:
                try:
                    recognition_result = self.speech_recognizer.recognize_from_file(audio_path)
                    result.transcription = recognition_result.text
                    result.transcription_confidence = recognition_result.confidence
                    
                    if self.debug_options.get('show_transcription'):
                        print(f"   📝 변환된 텍스트: \"{result.transcription}\"")
                        print(f"   📊 신뢰도: {result.transcription_confidence:.2f}")
                    
                except Exception as e:
                    error_msg = f"음성 인식 실패: {e}"
                    result.errors.append(error_msg)
                    if self.debug_options.get('verbose'):
                        print(f"   ❌ {error_msg}")
                    return result
            else:
                error_msg = "음성 인식 모듈이 초기화되지 않았습니다"
                result.errors.append(error_msg)
                return result
            
            # 3. 텍스트 처리 (음성 인식 결과를 텍스트로 처리)
            if result.transcription:
                text_result = self.process_text_input(result.transcription)
                
                # 결과 병합
                result.intent_type = text_result.intent_type
                result.intent_confidence = text_result.intent_confidence
                result.intent_details = text_result.intent_details
                result.dialogue_response = text_result.dialogue_response
                result.dialogue_details = text_result.dialogue_details
                result.order_state = text_result.order_state
                result.order_changes = text_result.order_changes
                result.final_response = text_result.final_response
                result.errors.extend(text_result.errors or [])
            
        except Exception as e:
            error_msg = f"음성 처리 중 오류: {e}"
            result.errors.append(error_msg)
            if self.debug_options.get('verbose'):
                print(f"❌ {error_msg}")
        
        result.processing_time = time.time() - start_time
        return result
    
    def process_text_input(self, text: str) -> ProcessingResult:
        """텍스트 입력 처리"""
        start_time = time.time()
        result = ProcessingResult(
            input_type="text",
            input_data=text,
            errors=[]
        )
        
        try:
            if self.debug_options.get('verbose'):
                print(f"\n💬 텍스트 처리: \"{text}\"")
            
            # 1. 의도 파악
            original_intent = None
            if self.intent_recognizer:
                try:
                    try:
                        from .models.conversation_models import ConversationContext
                    except ImportError:
                        from src.models.conversation_models import ConversationContext
                    context = ConversationContext(session_id=self.current_session_id or "debug_session")
                    
                    original_intent = self.intent_recognizer.recognize_intent(text, context)
                    result.intent_type = original_intent.type.value if original_intent.type else None
                    result.intent_confidence = original_intent.confidence
                    result.intent_details = {
                        "type": result.intent_type,
                        "confidence": result.intent_confidence,
                        "menu_items": [asdict(item) for item in (original_intent.menu_items or [])],
                        "modifications": [asdict(mod) for mod in (original_intent.modifications or [])],
                        "cancel_items": original_intent.cancel_items,
                        "payment_method": original_intent.payment_method,
                        "inquiry_text": original_intent.inquiry_text
                    }
                    
                    if self.debug_options.get('show_llm_processing'):
                        print(f"   🧠 의도 파악: {result.intent_type} (신뢰도: {result.intent_confidence:.2f})")
                        if original_intent.menu_items:
                            print(f"   📋 메뉴 아이템: {[f'{item.name} x{item.quantity}' for item in original_intent.menu_items]}")
                        if original_intent.modifications:
                            print(f"   🔄 수정 사항: {[f'{mod.item_name} → {mod.action}' for mod in original_intent.modifications]}")
                    
                except Exception as e:
                    error_msg = f"의도 파악 실패: {e}"
                    result.errors.append(error_msg)
                    if self.debug_options.get('verbose'):
                        print(f"   ❌ {error_msg}")
                    return result
            
            # 2. 대화 처리
            if self.dialogue_manager and result.intent_type and original_intent:
                try:
                    # 세션 생성 (없는 경우)
                    if not self.current_session_id:
                        self.current_session_id = self.dialogue_manager.create_session()
                    
                    # 원본 Intent 객체를 그대로 사용
                    dialogue_response = self.dialogue_manager.process_dialogue(
                        self.current_session_id, original_intent
                    )
                    
                    result.dialogue_response = dialogue_response.text
                    result.dialogue_details = {
                        "text": dialogue_response.text,
                        "requires_confirmation": dialogue_response.requires_confirmation,
                        "suggested_actions": dialogue_response.suggested_actions,
                        "order_state": asdict(dialogue_response.order_state) if dialogue_response.order_state else None
                    }
                    
                    if self.debug_options.get('show_dialogue_details'):
                        print(f"   💭 대화 응답: \"{result.dialogue_response}\"")
                        print(f"   ❓ 확인 필요: {dialogue_response.requires_confirmation}")
                        if dialogue_response.suggested_actions:
                            print(f"   💡 제안 액션: {dialogue_response.suggested_actions}")
                    
                except Exception as e:
                    error_msg = f"대화 처리 실패: {e}"
                    result.errors.append(error_msg)
                    if self.debug_options.get('verbose'):
                        print(f"   ❌ {error_msg}")
            
            # 3. 주문 상태 확인
            if self.order_manager:
                try:
                    current_order = self.order_manager.get_current_order()
                    if current_order:
                        result.order_state = {
                            "order_id": current_order.order_id,
                            "items": [asdict(item) for item in current_order.items],
                            "total_amount": float(current_order.total_amount),
                            "status": current_order.status.value,
                            "item_count": len(current_order.items)
                        }
                    else:
                        result.order_state = {"items": [], "total_amount": 0, "item_count": 0}
                    
                    if self.debug_options.get('show_order_management'):
                        self._display_order_state(result.order_state)
                    
                except Exception as e:
                    error_msg = f"주문 상태 확인 실패: {e}"
                    result.errors.append(error_msg)
                    if self.debug_options.get('verbose'):
                        print(f"   ❌ {error_msg}")
            
            # 4. 최종 응답 생성
            if result.dialogue_response:
                result.final_response = result.dialogue_response
            else:
                result.final_response = "처리가 완료되었습니다."
            
            # show_dialogue_details가 활성화되지 않은 경우에만 최종 응답 출력
            # (중복 출력 방지)
            if (self.debug_options.get('show_response_generation') and 
                not self.debug_options.get('show_dialogue_details')):
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
    
    def _display_menu(self):
        """사용 가능한 메뉴를 표시"""
        print("   📋 사용 가능한 메뉴:")
        
        if not self.order_manager:
            print("      메뉴 정보를 불러올 수 없습니다.")
            return
        
        try:
            # 메뉴 설정 다시 로드
            menu_config = config_manager.load_menu_config()
            
            # 카테고리별로 메뉴 표시
            for category in menu_config.categories:
                items_in_category = []
                for item_name, item_config in menu_config.menu_items.items():
                    if item_config.category == category:
                        items_in_category.append(f"{item_name} ({item_config.price:,}원)")
                
                if items_in_category:
                    print(f"      {category}: {', '.join(items_in_category)}")
            
            print("   💡 메뉴명을 입력하여 주문하세요. 예: '빅맥 주문', '콜라 2개'")
            
        except Exception as e:
            print(f"      메뉴 정보 로드 중 오류: {e}")
    
    def run_interactive_mode(self):
        """대화형 모드 실행"""
        print("🎤 음성 키오스크 시스템 (대화형 모드)")
        print("=" * 50)
        
        if self.debug_options.get('debug'):
            print("🐛 디버그 모드가 활성화되었습니다.")
        
        print("💡 'quit' 또는 'exit'를 입력하면 종료됩니다.")
        print("💡 'clear'를 입력하면 주문을 초기화합니다.")
        print("💡 'status'를 입력하면 현재 주문 상태를 확인합니다.")
        print("💡 'menu' 또는 '메뉴'를 입력하면 사용 가능한 메뉴를 확인합니다.")
        print()
        
        # 세션 시작
        if self.dialogue_manager:
            self.current_session_id = self.dialogue_manager.create_session()
        
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
                
                if user_input.lower() in ['menu', '메뉴']:
                    self._display_menu()
                    continue
                
                # 텍스트 처리
                result = self.process_text_input(user_input)
                
                # 디버그 출력이 활성화되지 않은 경우에만 최종 응답 출력
                # (디버그 모드에서는 이미 상세 출력에서 응답을 보여줌)
                if result.final_response and not (
                    self.debug_options.get('show_dialogue_details') or 
                    self.debug_options.get('show_response_generation') or
                    self.debug_options.get('verbose')
                ):
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
        description="팀원용 디버그 가능한 음성 키오스크 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 음성 파일 처리 (모든 과정 표시)
  python src/debug_main.py --mode audio --input audio.wav --show-transcription --show-llm-processing --show-order-management

  # 텍스트 입력 처리 (LLM 과정만 표시)
  python src/debug_main.py --mode text --input "빅맥 주문" --show-llm-processing

  # 대화형 모드 (디버그 활성화)
  python src/debug_main.py --mode interactive --debug
        """
    )
    
    # 기본 옵션
    parser.add_argument('--mode', choices=['audio', 'text', 'interactive'], 
                       default='interactive', help='실행 모드 선택')
    parser.add_argument('--input', help='입력 파일 경로 또는 텍스트')
    
    # 디버그 옵션
    parser.add_argument('--debug', action='store_true', help='전체 디버그 모드 활성화')
    parser.add_argument('--verbose', action='store_true', help='상세 로그 출력')
    
    # 상세 출력 옵션
    parser.add_argument('--show-transcription', action='store_true', 
                       help='음성→텍스트 변환 결과 표시')
    parser.add_argument('--show-llm-processing', action='store_true', 
                       help='LLM 처리 과정 표시')
    parser.add_argument('--show-dialogue-details', action='store_true', 
                       help='대화 처리 세부사항 표시')
    parser.add_argument('--show-order-management', action='store_true', 
                       help='주문 관리 과정 표시')
    parser.add_argument('--show-response-generation', action='store_true', 
                       help='응답 생성 과정 표시')
    
    # 출력 형식 옵션
    parser.add_argument('--output-format', choices=['json', 'yaml', 'table'], 
                       default='table', help='출력 형식 선택')
    parser.add_argument('--save-log', help='로그를 파일로 저장')
    
    return parser


def format_output(result: ProcessingResult, format_type: str) -> str:
    """결과를 지정된 형식으로 포맷팅"""
    if format_type == 'json':
        return json.dumps(asdict(result), indent=2, ensure_ascii=False)
    elif format_type == 'yaml':
        try:
            import yaml
            return yaml.dump(asdict(result), allow_unicode=True, default_flow_style=False)
        except ImportError:
            return "YAML 출력을 위해 PyYAML을 설치하세요: pip install PyYAML"
    else:  # table
        return format_table_output(result)


def format_table_output(result: ProcessingResult) -> str:
    """테이블 형식으로 결과 포맷팅"""
    output = []
    output.append("=" * 60)
    output.append(f"📊 처리 결과 요약")
    output.append("=" * 60)
    
    output.append(f"입력 타입: {result.input_type}")
    output.append(f"입력 데이터: {result.input_data}")
    
    if result.transcription:
        output.append(f"음성 변환: {result.transcription} (신뢰도: {result.transcription_confidence:.2f})")
    
    if result.intent_type:
        output.append(f"의도 파악: {result.intent_type} (신뢰도: {result.intent_confidence:.2f})")
    
    if result.dialogue_response:
        output.append(f"대화 응답: {result.dialogue_response}")
    
    if result.order_state and result.order_state.get('items'):
        output.append(f"주문 상태: {len(result.order_state['items'])}개 아이템, 총 {result.order_state['total_amount']:,.0f}원")
    
    if result.final_response:
        output.append(f"최종 응답: {result.final_response}")
    
    if result.processing_time:
        output.append(f"처리 시간: {result.processing_time:.2f}초")
    
    if result.errors:
        output.append("오류:")
        for error in result.errors:
            output.append(f"  - {error}")
    
    output.append("=" * 60)
    return "\n".join(output)


def main():
    """메인 실행 함수"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 로깅 설정
    log_level = "DEBUG" if args.debug or args.verbose else "INFO"
    setup_logging(log_level=log_level, log_file=args.save_log)
    
    # 디버그 옵션 설정
    debug_options = {
        'debug': args.debug,
        'verbose': args.verbose or args.debug,
        'show_transcription': args.show_transcription or args.debug,
        'show_llm_processing': args.show_llm_processing or args.debug,
        'show_dialogue_details': args.show_dialogue_details or args.debug,
        'show_order_management': args.show_order_management or args.debug,
        'show_response_generation': args.show_response_generation or args.debug,
    }
    
    # 시스템 초기화
    kiosk = DebugVoiceKiosk(debug_options)
    
    if not kiosk.initialize_system():
        print("❌ 시스템 초기화에 실패했습니다.")
        sys.exit(1)
    
    # 모드별 실행
    if args.mode == 'interactive':
        kiosk.run_interactive_mode()
    
    elif args.mode == 'audio':
        if not args.input:
            print("❌ 음성 파일 경로를 --input 옵션으로 지정해주세요.")
            sys.exit(1)
        
        result = kiosk.process_audio_input(args.input)
        
        if args.output_format != 'table' or not debug_options['verbose']:
            print(format_output(result, args.output_format))
    
    elif args.mode == 'text':
        if not args.input:
            print("❌ 입력 텍스트를 --input 옵션으로 지정해주세요.")
            sys.exit(1)
        
        result = kiosk.process_text_input(args.input)
        
        if args.output_format != 'table' or not debug_options['verbose']:
            print(format_output(result, args.output_format))


if __name__ == "__main__":
    main()