"""
음성 기반 키오스크 AI 주문 시스템 메인 실행 파일
"""

import sys
import time
import argparse
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python 경로에 추가 (직접 실행 시)
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# 환경 변수 로드
try:
    from .utils.env_loader import ensure_env_loaded
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
    from .models.config_models import AudioConfig
    from .models.conversation_models import IntentType
    from .models.response_models import ResponseType
    from .error.handler import ErrorHandler
except ImportError:
    # 직접 실행 시 절대 import 사용
    from src.utils.env_loader import ensure_env_loaded
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
    from src.models.config_models import AudioConfig
    from src.models.conversation_models import IntentType
    from src.models.response_models import ResponseType
    from src.error.handler import ErrorHandler

ensure_env_loaded()


class VoiceKioskPipeline:
    """음성 키오스크 파이프라인 클래스"""
    
    def __init__(self):
        """파이프라인 초기화"""
        self.logger = get_logger(__name__)
        self.error_handler = ErrorHandler()
        
        # 각 모듈 초기화
        self.audio_processor: Optional[AudioProcessor] = None
        self.speech_recognizer: Optional[SpeechRecognizer] = None
        self.intent_recognizer: Optional[IntentRecognizer] = None
        self.dialogue_manager: Optional[DialogueManager] = None
        self.order_manager: Optional[OrderManager] = None
        self.response_system: Optional[TextResponseSystem] = None
        
        # 현재 세션 ID
        self.current_session_id: Optional[str] = None
        
        # 시스템 상태
        self.is_initialized = False
        self.is_running = False
    
    def initialize_system(self) -> bool:
        """시스템 초기화"""
        try:
            self.logger.info("시스템 모듈 초기화 시작...")
            
            # 1. 메뉴 시스템 초기화
            self.logger.info("메뉴 시스템 초기화 중...")
            # 프로젝트 루트 기준으로 설정 파일 경로 설정
            project_root = Path(__file__).parent.parent
            menu_config_path = project_root / "config" / "menu_config.json"
            self.menu = Menu.from_config_file(str(menu_config_path))
            self.order_manager = OrderManager(self.menu)
            
            # 2. 음성 전처리 모듈 초기화
            self.logger.info("음성 전처리 모듈 초기화 중...")
            audio_config = AudioConfig(
                sample_rate=16000,
                chunk_size=1024,
                noise_reduction_enabled=True,
                noise_reduction_level=0.5,
                speaker_separation_enabled=True,
                speaker_separation_threshold=0.7
            )
            self.audio_processor = AudioProcessor(audio_config)
            
            # 3. 음성인식 모듈 초기화
            self.logger.info("음성인식 모듈 초기화 중...")
            try:
                # 설정에서 Whisper 모델 정보 가져오기
                audio_config = config_manager.get_audio_config()
                self.speech_recognizer = SpeechRecognizer(
                    model_name=audio_config.whisper_model,
                    language=audio_config.whisper_language,
                    device=audio_config.whisper_device
                )
                if not self.speech_recognizer.is_available():
                    self.logger.warning("Whisper 모델을 사용할 수 없습니다. 텍스트 입력 모드로 실행됩니다.")
            except Exception as e:
                self.logger.warning(f"음성인식 모듈 초기화 실패: {e}. 텍스트 입력 모드로 실행됩니다.")
                self.speech_recognizer = None
            
            # 4. 의도 파악 모듈 초기화
            self.logger.info("의도 파악 모듈 초기화 중...")
            try:
                # API 키 확인
                api_config = config_manager.load_api_config()
                if not api_config.api_key or api_config.api_key == "your_openai_api_key_here":
                    self.logger.error("OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
                    return False
                
                self.intent_recognizer = IntentRecognizer()
                self.logger.info("의도 파악 모듈 초기화 완료")
            except Exception as e:
                self.logger.error(f"의도 파악 모듈 초기화 실패: {e}")
                return False
            
            # 5. 대화 관리 모듈 초기화
            self.logger.info("대화 관리 모듈 초기화 중...")
            try:
                self.dialogue_manager = DialogueManager(self.order_manager)
                self.logger.info("대화 관리 모듈 초기화 완료")
            except Exception as e:
                self.logger.error(f"대화 관리 모듈 초기화 실패: {e}")
                return False
            
            # 6. 응답 시스템 초기화
            self.logger.info("응답 시스템 초기화 중...")
            self.response_system = TextResponseSystem()
            
            self.is_initialized = True
            self.logger.info("시스템 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"시스템 초기화 실패: {e}")
            return False
    
    def start_session(self) -> str:
        """새로운 세션 시작"""
        if not self.is_initialized:
            raise RuntimeError("시스템이 초기화되지 않았습니다.")
        
        self.current_session_id = self.dialogue_manager.create_session()
        self.logger.info(f"새로운 세션 시작: {self.current_session_id}")
        
        # 인사말 생성
        greeting_response = self.response_system.generate_greeting()
        self.logger.info(f"인사말: {greeting_response.formatted_text}")
        print(f"\n시스템: {greeting_response.formatted_text}")
        
        return self.current_session_id
    
    def process_audio_input(self, audio_file_path: str) -> str:
        """
        음성 파일 입력 처리 (AudioProcessor 포함한 완전한 파이프라인)
        Args:
            audio_file_path: 음성 파일 경로
        Returns:
            처리 결과 응답 텍스트
        """
        try:
            if not self.speech_recognizer:
                return "음성인식 기능을 사용할 수 없습니다. 텍스트로 입력해 주세요."

            self.logger.info(f"🎤 음성 파일 처리 시작: {audio_file_path}")
            print(f"\n🎤 음성 파일을 처리하고 있습니다: {audio_file_path}")

            # 1. AudioProcessor를 통한 전처리 (화자 분리 포함)
            try:
                if self.audio_processor:
                    print("🔧 AudioProcessor를 통한 전처리 시작...")
                    
                    # 오디오 파일 로드 및 전처리
                    audio_data = self.audio_processor.create_audio_data(audio_file_path)
                    processed_audio = self.audio_processor.process_audio(audio_data)
                    
                    print("✅ 전처리 완료 (화자 분리 포함)")
                else:
                    print("⚠️  AudioProcessor 없음, 원본 파일로 진행")
            except Exception as preprocess_error:
                self.logger.error(f"전처리 실패: {preprocess_error}")
                print(f"⚠️  전처리 실패, 원본으로 진행: {str(preprocess_error)[:50]}...")

            # 2. 음성 인식 (전처리 후)
            recognition_result = self.speech_recognizer.recognize_from_file(audio_file_path)
            recognized_text = recognition_result.text

            confidence_percent = recognition_result.confidence * 100
            processing_time = recognition_result.processing_time

            self.logger.info(f"✅ 음성인식 완료")
            self.logger.info(f"   📝 변환된 텍스트: '{recognized_text}'")
            self.logger.info(f"   📊 신뢰도: {confidence_percent:.1f}%")
            self.logger.info(f"   ⏱️ 처리시간: {processing_time:.2f}초")
            self.logger.info(f"   🤖 사용 모델: {recognition_result.model_version}")
            self.logger.info(f"   🌐 언어: {recognition_result.language}")

            print(f"\n📝 음성 → 텍스트 변환 결과:")
            print(f"   📄 텍스트: '{recognized_text}'")
            print(f"   📊 신뢰도: {confidence_percent:.1f}%")
            print(f"   ⏱️ 처리시간: {processing_time:.2f}초")
            print(f"   🤖 모델: {recognition_result.model_version}")

            if recognition_result.confidence >= 0.9:
                confidence_status = "매우 높음 ✅"
                self.logger.info(f"🎯 음성인식 신뢰도가 매우 높습니다 ({confidence_percent:.1f}%)")
            elif recognition_result.confidence >= 0.7:
                confidence_status = "높음 ✅"
                self.logger.info(f"👍 음성인식 신뢰도가 높습니다 ({confidence_percent:.1f}%)")
            elif recognition_result.confidence >= 0.5:
                confidence_status = "보통 ⚠️"
                self.logger.warning(f"⚠️ 음성인식 신뢰도가 보통입니다 ({confidence_percent:.1f}%). 결과를 확인해 주세요.")
                print(f"⚠️ 음성인식 신뢰도가 보통입니다 ({confidence_percent:.1f}%). 결과를 확인해 주세요.")
            else:
                confidence_status = "낮음 ❌"
                self.logger.warning(f"❌ 음성인식 신뢰도가 낮습니다 ({confidence_percent:.1f}%). 결과가 부정확할 수 있습니다.")
                print(f"❌ 음성인식 신뢰도가 낮습니다 ({confidence_percent:.1f}%). 결과가 부정확할 수 있습니다.")

            print(f"   🏆 신뢰도 상태: {confidence_status}")

            if not recognized_text.strip():
                self.logger.warning("⚠️ 음성에서 텍스트를 인식하지 못했습니다.")
                print("⚠️ 음성에서 텍스트를 인식하지 못했습니다. 다시 시도해 주세요.")
                return "죄송합니다. 음성을 인식하지 못했습니다. 다시 말씀해 주시거나 텍스트로 입력해 주세요."

            self.logger.info(f"💬 인식된 텍스트로 대화 처리 시작: '{recognized_text}'")
            return self.process_text_input(recognized_text, from_speech=True)

        except Exception as e:
            self.logger.error(f"❌ 음성 입력 처리 실패: {e}")
            print(f"❌ 음성 처리 중 오류가 발생했습니다: {e}")
            error_response = self.error_handler.handle_audio_error(e)
            return error_response.message
    
    def process_text_input(self, text: str, from_speech: bool = False) -> str:
        """
        텍스트 입력 처리
        
        Args:
            text: 사용자 입력 텍스트
            from_speech: 음성에서 변환된 텍스트인지 여부
            
        Returns:
            처리 결과 응답 텍스트
        """
        try:
            if not self.current_session_id:
                self.start_session()
            
            # 입력 소스에 따른 로그 메시지
            if from_speech:
                self.logger.info(f"🎤➡️💬 음성에서 변환된 텍스트 처리: '{text}'")
                print(f"\n💬 음성에서 변환된 텍스트로 대화를 처리합니다: '{text}'")
            else:
                self.logger.info(f"⌨️ 직접 입력된 텍스트 처리: '{text}'")
            
            # 1. 의도 파악
            context = self.dialogue_manager.get_context(self.current_session_id)
            intent = self.intent_recognizer.recognize_intent(text, context)
            
            self.logger.info(f"🎯 파악된 의도: {intent.type.value} (신뢰도: {intent.confidence:.2f})")
            
            # 2. 대화 처리
            dialogue_response = self.dialogue_manager.process_dialogue(
                self.current_session_id, intent
            )
            
            # 3. 응답 생성 및 포맷팅
            formatted_response = self._format_dialogue_response(dialogue_response, intent)
            
            self.logger.info(f"✅ 응답 생성 완료")
            self.logger.debug(f"응답 내용: {formatted_response}")
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"❌ 텍스트 입력 처리 실패: {e}")
            error_response = self.error_handler.handle_general_error(e, "dialogue")
            return error_response.message
    
    def _format_dialogue_response(self, dialogue_response, intent) -> str:
        """대화 응답을 포맷팅"""
        try:
            # 기본 응답 텍스트
            response_text = dialogue_response.text
            
            # 주문 상태가 있는 경우 추가 정보 제공
            if dialogue_response.order_state and intent.type in [IntentType.ORDER, IntentType.MODIFY]:
                order_summary = self.order_manager.get_order_summary()
                if order_summary and order_summary.items:
                    # 간단한 주문 요약 추가
                    item_count = len(order_summary.items)
                    total_amount = order_summary.total_amount
                    response_text += f"\n{item_count}개, {total_amount:,}원"
            
            # 확인이 필요한 경우
            if dialogue_response.requires_confirmation:
                response_text += "\n확인: 네/아니요"
            
            # 제안된 액션이 있는 경우 - 음성 출력에서 제외
            # if dialogue_response.suggested_actions:
            #     action_hints = {
            #         "continue_ordering": "추가 주문하시려면 메뉴를 말씀해 주세요.",
            #         "confirm_order": "주문을 확정하시려면 '결제'라고 말씀해 주세요.",
            #         "help": "도움이 필요하시면 '도움말'이라고 말씀해 주세요."
            #     }
            #     
            #     hints = []
            #     for action in dialogue_response.suggested_actions[:2]:  # 최대 2개만 표시
            #         if action in action_hints:
            #             hints.append(action_hints[action])
            #     
            #     if hints:
            #         response_text += f"\n\n💡 {' 또는 '.join(hints)}"
            
            return response_text
            
        except Exception as e:
            self.logger.error(f"응답 포맷팅 실패: {e}")
            return dialogue_response.text
    
    def run_test_mode(self, config=None):
        """테스트 모드 실행"""
        if not self.is_initialized:
            print("❌ 시스템이 초기화되지 않았습니다.")
            return
        
        try:
            # 테스트 모듈 import
            from src.testing import TestCaseManager
            from src.models.testing_models import TestConfiguration, TestCaseCategory
            from src.utils.env_loader import get_test_config
            
            print("\n" + "="*70)
            print("🧪 맥도날드 키오스크 테스트케이스 생성 및 실행 시스템")
            print("="*70)
            
            # 환경 변수에서 테스트 설정 로드
            from src.utils.env_loader import load_env_file
            load_env_file()  # 환경 변수 강제 새로고침
            env_config = get_test_config()
            
            # 명령행 인자로 전달된 설정 처리
            if config and isinstance(config, dict):
                # 명령행 인자로 전달된 설정이 있는 경우
                include_slang = 'slang' in config.get('categories', ['all']) or 'all' in config.get('categories', [])
                include_informal = 'formal' not in config.get('categories', ['all']) or 'all' in config.get('categories', [])
                include_complex = 'complex' in config.get('categories', ['all']) or 'all' in config.get('categories', [])
                include_edge_cases = 'edge' in config.get('categories', ['all']) or 'all' in config.get('categories', [])
                max_tests_per_category = config.get('max_tests', env_config.get('max_tests_per_category', 20))
                
                test_config = TestConfiguration(
                    include_slang=include_slang,
                    include_informal=include_informal,
                    include_complex=include_complex,
                    include_edge_cases=include_edge_cases,
                    max_tests_per_category=max_tests_per_category
                )
                
                print(f"📊 테스트 설정 (명령행 인자에서 로드):")
                print(f"  - 선택된 카테고리: {config.get('categories', ['all'])}")
                print(f"  - 최대 테스트 개수: {max_tests_per_category}개")
            else:
                # 기존 환경 변수 기반 설정
                test_config = config or TestConfiguration(
                    include_slang=env_config.get('include_slang', True),
                    include_informal=env_config.get('include_informal', True),
                    include_complex=env_config.get('include_complex', True),
                    include_edge_cases=env_config.get('include_edge_cases', True),
                    max_tests_per_category=env_config.get('max_tests_per_category', 20)
                )
                
                print(f"📊 테스트 설정 (환경 변수에서 로드):")
            
            # 테스트 매니저 초기화
            test_manager = TestCaseManager(self, test_config)
            
            print(f"📊 테스트 설정 (환경 변수에서 로드):")
            print(f"  - 은어 테스트 ('상스치콤', '베토디' 등): {'✅ 포함' if test_config.include_slang else '❌ 제외'}")
            print(f"  - 반말 테스트 ('빅맥 줘', '결제할게' 등): {'✅ 포함' if test_config.include_informal else '❌ 제외'}")
            print(f"  - 복합 의도 테스트 (주문+취소, 변경+추가 등): {'✅ 포함' if test_config.include_complex else '❌ 제외'}")
            print(f"  - 엣지 케이스 (빈 입력, 존재하지 않는 메뉴 등): {'✅ 포함' if test_config.include_edge_cases else '❌ 제외'}")
            print(f"  - 카테고리당 최대 테스트: {test_config.max_tests_per_category}개")
            print(f"  - API 요청 간 지연시간: {env_config.get('delay_between_requests', 2.0)}초")
            
            # 테스트케이스 생성
            print("\n🔄 맥도날드 특화 테스트케이스 생성 중...")
            test_cases = test_manager.generate_test_cases()
            
            # 테스트케이스 요약 출력
            summary = test_manager.get_test_case_summary()
            print(f"\n📋 생성된 테스트케이스 요약:")
            print(f"  - 📊 총 테스트케이스: {summary['total_test_cases']}개")
            
            category_names = {
                'slang': '🗣️ 은어 테스트',
                'informal': '💬 반말 테스트', 
                'complex': '🔄 복합 의도 테스트',
                'normal': '📝 일반 테스트',
                'edge': '⚠️ 엣지 케이스'
            }
            
            for category, count in summary['category_counts'].items():
                if count > 0:
                    category_display = category_names.get(category, category)
                    print(f"  - {category_display}: {count}개")
            
            # 주요 테스트 예시 표시
            print(f"\n💡 테스트 예시:")
            example_cases = test_cases[:3]  # 처음 3개만 표시
            for i, case in enumerate(example_cases, 1):
                print(f"  {i}. [{case.category.value}] '{case.input_text}' → {case.expected_intent.value if case.expected_intent else 'UNKNOWN'}")
            
            if len(test_cases) > 3:
                print(f"  ... 및 {len(test_cases) - 3}개 더")
            
            # 사용자 확인
            print(f"\n❓ {len(test_cases)}개의 테스트를 실행하시겠습니까?")
            print("   이 테스트는 기존 VoiceKioskPipeline.process_text_input()을 사용하여")
            print("   각 테스트케이스의 의도 파악 정확도와 시스템 응답을 검증합니다.")
            print(f"   ⏱️ API 속도 제한 방지를 위해 요청 간 {env_config.get('delay_between_requests', 2.0)}초 지연이 적용됩니다.")
            print(f"\n실행하시겠습니까? (y/n): ", end="")
            user_input = input().strip().lower()
            
            if user_input not in ['y', 'yes', '예', 'ㅇ']:
                print("❌ 테스트 실행이 취소되었습니다.")
                return
            
            # 테스트 실행
            print(f"\n🚀 테스트 실행 시작...")
            print("   각 테스트는 VoiceKioskPipeline을 통해 실제 시스템과 동일하게 처리됩니다.")
            print("="*70)
            
            results = test_manager.run_all_tests(test_cases)
            
            # 상세 결과 출력
            print("\n" + "="*70)
            print("📊 테스트 결과 상세 분석")
            print("="*70)
            print(f"📈 전체 통계:")
            print(f"  - 총 테스트: {results.total_tests}개")
            print(f"  - 성공: {results.successful_tests}개 ✅")
            print(f"  - 실패: {results.total_tests - results.successful_tests}개 ❌")
            print(f"  - 성공률: {results.success_rate*100:.1f}%")
            print(f"  - 평균 처리시간: {results.average_processing_time:.3f}초")
            print(f"  - 총 소요시간: {results.total_duration:.1f}초")
            
            # 카테고리별 성공률
            print(f"\n📊 카테고리별 성공률:")
            for category in ['slang', 'informal', 'complex', 'normal', 'edge']:
                category_results = results.get_results_by_category(TestCaseCategory(category))
                if category_results:
                    category_success = sum(1 for r in category_results if r.success)
                    category_rate = category_success / len(category_results) * 100
                    category_display = category_names.get(category, category)
                    print(f"  - {category_display}: {category_success}/{len(category_results)} ({category_rate:.1f}%)")
            
            # 실패한 테스트 상세 분석
            failed_results = results.get_failed_results()
            if failed_results:
                print(f"\n❌ 실패한 테스트 상세 분석 ({len(failed_results)}개):")
                
                # 실패 유형별 분류
                intent_failures = [r for r in failed_results if not r.intent_matches]
                confidence_failures = [r for r in failed_results if r.intent_matches and not r.confidence_meets_threshold]
                error_failures = [r for r in failed_results if r.error_message]
                
                if intent_failures:
                    print(f"  🎯 의도 파악 실패: {len(intent_failures)}개")
                if confidence_failures:
                    print(f"  📊 신뢰도 부족: {len(confidence_failures)}개")
                if error_failures:
                    print(f"  💥 실행 오류: {len(error_failures)}개")
                
                print(f"\n🔍 실패 사례 (최대 5개):")
                for i, failed_result in enumerate(failed_results[:5], 1):
                    print(f"  {i}. [{failed_result.test_case.category.value}] {failed_result.test_case.id}")
                    print(f"     입력: '{failed_result.test_case.input_text}'")
                    print(f"     예상: {failed_result.test_case.expected_intent.value if failed_result.test_case.expected_intent else 'N/A'}")
                    print(f"     실제: {failed_result.detected_intent.value}")
                    print(f"     신뢰도: {failed_result.confidence_score:.3f} (최소: {failed_result.test_case.expected_confidence_min})")
                    if failed_result.error_message:
                        print(f"     오류: {failed_result.error_message}")
                    print()
                
                if len(failed_results) > 5:
                    print(f"     ... 및 {len(failed_results) - 5}개 더")
            else:
                print(f"\n🎉 모든 테스트가 성공했습니다!")
            
            # 보고서 저장 옵션
            try:
                print(f"\n💾 상세 보고서를 파일로 저장하시겠습니까? (y/n): ", end="")
                save_input = input().strip().lower()
            except EOFError:
                # 파이프나 자동화 환경에서는 자동으로 저장
                print("자동 모드: 보고서를 자동으로 저장합니다.")
                save_input = 'y'
            
            if save_input in ['y', 'yes', '예', 'ㅇ']:
                try:
                    # ReportGenerator import
                    from src.testing.report_generator import ReportGenerator
                    from src.testing.result_analyzer import ResultAnalyzer
                    
                    print("📝 상세 보고서 생성 중...")
                    
                    # 결과 분석
                    analyzer = ResultAnalyzer()
                    analysis = analyzer.analyze_results(results)
                    
                    # 보고서 생성
                    generator = ReportGenerator(output_directory="test_results")
                    
                    # 텍스트 보고서 생성
                    text_report_path = generator.generate_text_report(analysis)
                    print(f"✅ 텍스트 보고서 저장 완료: {text_report_path}")
                    
                    # 마크다운 보고서 생성
                    markdown_report_path = generator.generate_markdown_report(analysis)
                    print(f"✅ 마크다운 보고서 저장 완료: {markdown_report_path}")
                    
                    print(f"\n📊 보고서 파일 정보:")
                    import os
                    if os.path.exists(text_report_path):
                        file_size = os.path.getsize(text_report_path)
                        print(f"  - 텍스트 보고서: {text_report_path} ({file_size} bytes)")
                    if os.path.exists(markdown_report_path):
                        file_size = os.path.getsize(markdown_report_path)
                        print(f"  - 마크다운 보고서: {markdown_report_path} ({file_size} bytes)")
                    
                    print(f"\n💡 보고서에는 다음 정보가 포함됩니다:")
                    print(f"  - 모든 테스트의 입력 텍스트와 출력 텍스트")
                    print(f"  - 의도 파악 결과 및 신뢰도")
                    print(f"  - 성공/실패 여부 및 처리 시간")
                    print(f"  - 카테고리별 성능 분석")
                    print(f"  - 오류 분석 및 개선 제안")
                    
                except Exception as e:
                    print(f"❌ 보고서 생성 중 오류 발생: {e}")
                    import traceback
                    print(f"상세 오류: {traceback.format_exc()}")
            else:
                print("📝 보고서 저장을 건너뜁니다.")
            
            print("\n✅ 맥도날드 키오스크 테스트 모드 완료")
            print("   테스트 결과를 통해 시스템의 의도 파악 정확도를 확인하실 수 있습니다.")
            
        except Exception as e:
            self.logger.error(f"테스트 모드 실행 실패: {e}")
            print(f"❌ 테스트 모드 실행 중 오류가 발생했습니다: {e}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
    
    def run_microphone_mode(self, config=None):
        """마이크 입력 모드는 제거되었습니다."""
        print("❌ 마이크 입력 모드는 더 이상 지원되지 않습니다.")
        print("💡 음성 파일 입력만 지원합니다. interactive 모드를 사용해주세요.")
        print("📁 사용법: 음성 파일 경로를 입력하세요 (예: ./audio/order.wav)")
    
    def run_interactive_mode(self):
        """음성 파일 입력 모드 실행"""
        if not self.is_initialized:
            print("❌ 시스템이 초기화되지 않았습니다.")
            return
        
        self.is_running = True
        self.start_session()
        
        print("\n" + "="*60)
        print("🎤 음성 파일 기반 키오스크 AI 주문 시스템")
        print("="*60)
        print("🎵 음성 파일 경로를 입력하세요 (예: ./audio/order.wav)")
        print("🚪 종료하려면 'quit', 'exit', '종료' 중 하나를 입력하세요")
        print("🔄 새 주문을 시작하려면 '새 주문' 또는 'new'를 입력하세요")
        
        # 음성인식 모델 정보 표시
        if self.speech_recognizer and self.speech_recognizer.is_available():
            model_info = self.speech_recognizer.get_model_info()
            print(f"🤖 음성인식 모델: {model_info['model_name']} ({model_info['model_type']}, {model_info['device']})")
        else:
            print("⚠️ 음성인식 기능을 사용할 수 없습니다.")
            return
        
        print("="*60)
        
        try:
            while self.is_running:
                try:
                    # 사용자 입력 받기
                    user_input = input("\n🎵 음성 파일 경로: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # 종료 명령 확인
                    if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                        print("\n👋 이용해 주셔서 감사합니다!")
                        break
                    
                    # 새 주문 시작
                    if user_input.lower() in ['새 주문', 'new', 'new order']:
                        self.start_session()
                        continue
                    
                    # 음성 파일 입력 처리만 지원
                    print(f"\n{'='*50}")
                    response = self.process_audio_input(user_input)
                    print(f"{'='*50}")
                    
                    # 응답 출력
                    print(f"\n🤖 시스템: {response}")
                    
                except KeyboardInterrupt:
                    print("\n\n👋 이용해 주셔서 감사합니다!")
                    break
                except Exception as e:
                    self.logger.error(f"입력 처리 중 오류: {e}")
                    print(f"\n❌ 처리 중 오류가 발생했습니다: {e}")
                    print("다시 시도해 주세요.")
        
        finally:
            self.is_running = False
            if self.current_session_id:
                self.dialogue_manager.end_session(self.current_session_id)
    
    def get_system_status(self) -> dict:
        """시스템 상태 정보 반환"""
        status = {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'current_session': self.current_session_id,
            'modules': {
                'audio_processor': self.audio_processor is not None,
                'speech_recognizer': self.speech_recognizer is not None and self.speech_recognizer.is_available(),
                'intent_recognizer': self.intent_recognizer is not None,
                'dialogue_manager': self.dialogue_manager is not None,
                'order_manager': self.order_manager is not None,
                'response_system': self.response_system is not None
            }
        }
        
        if self.order_manager:
            status['order_stats'] = self.order_manager.get_order_stats()
        
        if self.dialogue_manager:
            status['session_stats'] = self.dialogue_manager.get_session_stats()
        
        return status
    
    def shutdown(self):
        """시스템 종료"""
        self.logger.info("시스템 종료 시작...")
        
        self.is_running = False
        
        # 현재 세션 종료
        if self.current_session_id and self.dialogue_manager:
            self.dialogue_manager.end_session(self.current_session_id)
            self.current_session_id = None
        
        # 각 모듈 정리
        if self.speech_recognizer:
            del self.speech_recognizer
            self.speech_recognizer = None
        
        self.is_initialized = False
        self.logger.info("시스템 종료 완료")


def create_argument_parser():
    """명령행 인수 파서 생성"""
    parser = argparse.ArgumentParser(
        description='음성 파일 기반 키오스크 AI 주문 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python src/main.py                                    # 음성 파일 모드 선택
  python src/main.py --mode interactive                 # 음성 파일 모드
  python src/main.py --mode test --categories slang --max-tests 5  # 테스트 모드
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['interactive', 'test'],
        help='실행 모드 선택 (지정하지 않으면 음성 파일 모드로 선택)'
    )
    
    # 테스트 모드 관련 인자들
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['slang', 'formal', 'complex', 'edge', 'all'],
        help='테스트할 카테고리 선택 (테스트 모드에서만 사용)'
    )
    
    parser.add_argument(
        '--max-tests',
        type=int,
        help='최대 테스트 개수 (테스트 모드에서만 사용)'
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
        default='voice_kiosk.log',
        help='로그 파일 경로를 지정합니다 (기본값: voice_kiosk.log)'
    )
    
    return parser


def main():
    """메인 실행 함수 - 음성 파일 입력만 지원"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 로깅 시스템 초기화
    setup_logging(log_level=args.log_level, log_file=args.log_file)
    logger = get_logger("main")
    
    logger.info("음성 파일 기반 키오스크 AI 주문 시스템을 시작합니다.")
    
    try:
        # 설정 검증
        if not config_manager.validate_config():
            logger.error("설정 검증에 실패했습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        
        logger.info("설정 검증이 완료되었습니다.")
        
        # 파이프라인 초기화
        pipeline = VoiceKioskPipeline()
        
        if not pipeline.initialize_system():
            logger.error("시스템 초기화에 실패했습니다. 프로그램을 종료합니다.")
            sys.exit(1)
        
        # 시스템 상태 출력
        status = pipeline.get_system_status()
        logger.info(f"시스템 상태: {status}")
        
        # 명령행 인자로 모드가 지정된 경우
        if args.mode:
            if args.mode == "interactive":
                print("\n📁 음성 파일 입력 모드를 시작합니다...")
                pipeline.run_interactive_mode()
            elif args.mode == "microphone":
                print("\n❌ 마이크 모드는 더 이상 지원되지 않습니다.")
                print("💡 음성 파일 입력 모드를 사용해주세요.")
                pipeline.run_interactive_mode()
            elif args.mode == "test":
                print("\n🧪 테스트 모드를 시작합니다...")
                # 테스트 설정 구성
                test_config = {}
                if args.categories:
                    test_config['categories'] = args.categories
                if args.max_tests:
                    test_config['max_tests'] = args.max_tests
                pipeline.run_test_mode(test_config)
            return
        
        # 명령행 인자가 없는 경우 음성 파일 모드 직접 시작
        print("\n" + "="*70)
        print("🎤 음성 파일 기반 키오스크 AI 주문 시스템")
        print("="*70)
        print("지원하는 모드:")
        print()
        print("1. 📁 음성 파일 입력 모드")
        print("   - 로컬 음성 파일 경로를 입력하여 처리")
        print("   - 안정적이고 반복 테스트 가능")
        print()
        print("2. 🧪 테스트 모드")
        print("   - 자동화된 테스트케이스 실행")
        print("   - 시스템 성능 분석")
        print()
        print("="*70)
        
        while True:
            try:
                choice = input("모드를 선택하세요 (1-2): ").strip()
                
                if choice == "1":
                    print("\n📁 음성 파일 입력 모드를 시작합니다...")
                    pipeline.run_interactive_mode()
                    break
                elif choice == "2":
                    print("\n🧪 테스트 모드를 시작합니다...")
                    pipeline.run_test_mode()
                    break
                else:
                    print("❌ 잘못된 선택입니다. 1 또는 2를 입력해주세요.")
                    continue
                    
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                logger.error(f"모드 선택 중 오류: {e}")
                print(f"❌ 오류가 발생했습니다: {e}")
                print("다시 시도해주세요.")
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)
    finally:
        logger.info("음성 파일 기반 키오스크 AI 주문 시스템을 종료합니다.")


if __name__ == "__main__":
    main()