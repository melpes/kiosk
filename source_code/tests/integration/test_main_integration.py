#!/usr/bin/env python3
"""
메인 파이프라인 통합 테스트
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import VoiceKioskPipeline
from src.models.audio_models import AudioData
from src.models.conversation_models import IntentType


class TestVoiceKioskPipeline(unittest.TestCase):
    """음성 키오스크 파이프라인 통합 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.pipeline = VoiceKioskPipeline()
    
    def test_system_initialization(self):
        """시스템 초기화 테스트"""
        # 초기 상태 확인
        self.assertFalse(self.pipeline.is_initialized)
        self.assertFalse(self.pipeline.is_running)
        
        # 시스템 초기화 (API 키 없이는 실패할 수 있음)
        try:
            result = self.pipeline.initialize_system()
            if result:
                self.assertTrue(self.pipeline.is_initialized)
                
                # 모듈 상태 확인
                status = self.pipeline.get_system_status()
                self.assertTrue(status['modules']['order_manager'])
                self.assertTrue(status['modules']['response_system'])
        except Exception as e:
            # API 키가 없는 경우 예상되는 실패
            self.assertIn("API", str(e))
    
    def test_session_management(self):
        """세션 관리 테스트"""
        # 초기화 없이 세션 시작 시도
        with self.assertRaises(RuntimeError):
            self.pipeline.start_session()
        
        # 시스템 초기화 후 세션 시작 (모킹 사용)
        with patch.object(self.pipeline, 'initialize_system', return_value=True):
            with patch.object(self.pipeline, 'dialogue_manager') as mock_dialogue:
                with patch.object(self.pipeline, 'response_system') as mock_response:
                    # 모킹 설정
                    mock_dialogue.create_session.return_value = "test-session-123"
                    mock_response.generate_greeting.return_value = Mock(formatted_text="안녕하세요!")
                    
                    self.pipeline.is_initialized = True
                    session_id = self.pipeline.start_session()
                    
                    self.assertEqual(session_id, "test-session-123")
                    self.assertEqual(self.pipeline.current_session_id, "test-session-123")
    
    def test_text_input_processing(self):
        """텍스트 입력 처리 테스트"""
        with patch.object(self.pipeline, 'initialize_system', return_value=True):
            with patch.object(self.pipeline, 'dialogue_manager') as mock_dialogue:
                with patch.object(self.pipeline, 'intent_recognizer') as mock_intent:
                    with patch.object(self.pipeline, 'response_system') as mock_response:
                        # 모킹 설정
                        self.pipeline.is_initialized = True
                        self.pipeline.current_session_id = "test-session"
                        
                        mock_intent_obj = Mock()
                        mock_intent_obj.type = IntentType.ORDER
                        mock_intent_obj.confidence = 0.9
                        mock_intent.recognize_intent.return_value = mock_intent_obj
                        
                        mock_dialogue_response = Mock()
                        mock_dialogue_response.text = "주문이 추가되었습니다."
                        mock_dialogue_response.order_state = None
                        mock_dialogue_response.requires_confirmation = False
                        mock_dialogue_response.suggested_actions = []
                        mock_dialogue.process_dialogue.return_value = mock_dialogue_response
                        
                        mock_response.generate_greeting.return_value = Mock(formatted_text="안녕하세요!")
                        
                        # 텍스트 입력 처리
                        result = self.pipeline.process_text_input("빅맥 주문")
                        
                        # 결과 확인
                        self.assertIsInstance(result, str)
                        self.assertIn("주문", result)
                        
                        # 메서드 호출 확인
                        mock_intent.recognize_intent.assert_called_once()
                        mock_dialogue.process_dialogue.assert_called_once()
    
    def test_system_status(self):
        """시스템 상태 확인 테스트"""
        status = self.pipeline.get_system_status()
        
        # 기본 상태 확인
        self.assertIn('initialized', status)
        self.assertIn('running', status)
        self.assertIn('modules', status)
        
        # 모듈 상태 확인
        modules = status['modules']
        self.assertIn('audio_processor', modules)
        self.assertIn('speech_recognizer', modules)
        self.assertIn('intent_recognizer', modules)
        self.assertIn('dialogue_manager', modules)
        self.assertIn('order_manager', modules)
        self.assertIn('response_system', modules)
    
    def test_shutdown(self):
        """시스템 종료 테스트"""
        # 초기 상태 설정
        self.pipeline.is_initialized = True
        self.pipeline.is_running = True
        self.pipeline.current_session_id = "test-session"
        
        # 모킹된 dialogue_manager 설정
        mock_dialogue = Mock()
        self.pipeline.dialogue_manager = mock_dialogue
        
        # 종료 실행
        self.pipeline.shutdown()
        
        # 상태 확인
        self.assertFalse(self.pipeline.is_initialized)
        self.assertFalse(self.pipeline.is_running)
        self.assertIsNone(self.pipeline.current_session_id)
        
        # 세션 종료 호출 확인
        mock_dialogue.end_session.assert_called_once_with("test-session")


class TestPipelineIntegration(unittest.TestCase):
    """파이프라인 통합 시나리오 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.pipeline = VoiceKioskPipeline()
    
    def test_basic_order_flow(self):
        """기본 주문 플로우 테스트"""
        with patch.object(self.pipeline, 'initialize_system', return_value=True):
            with patch.object(self.pipeline, 'dialogue_manager') as mock_dialogue:
                with patch.object(self.pipeline, 'intent_recognizer') as mock_intent:
                    with patch.object(self.pipeline, 'response_system') as mock_response:
                        with patch.object(self.pipeline, 'order_manager') as mock_order:
                            # 시스템 초기화
                            self.pipeline.is_initialized = True
                            
                            # 모킹 설정
                            mock_dialogue.create_session.return_value = "session-1"
                            mock_response.generate_greeting.return_value = Mock(formatted_text="안녕하세요!")
                            
                            # 주문 의도 모킹
                            order_intent = Mock()
                            order_intent.type = IntentType.ORDER
                            order_intent.confidence = 0.9
                            mock_intent.recognize_intent.return_value = order_intent
                            
                            # 대화 응답 모킹
                            dialogue_response = Mock()
                            dialogue_response.text = "빅맥이 주문에 추가되었습니다."
                            dialogue_response.order_state = Mock()
                            dialogue_response.requires_confirmation = False
                            dialogue_response.suggested_actions = ["continue_ordering"]
                            mock_dialogue.process_dialogue.return_value = dialogue_response
                            
                            # 주문 요약 모킹
                            order_summary = Mock()
                            order_summary.items = [Mock()]
                            order_summary.total_amount = 6500
                            mock_order.get_order_summary.return_value = order_summary
                            
                            # 시나리오 실행
                            session_id = self.pipeline.start_session()
                            self.assertEqual(session_id, "session-1")
                            
                            # 주문 처리
                            result = self.pipeline.process_text_input("빅맥 주문")
                            self.assertIn("빅맥", result)
                            
                            # 메서드 호출 확인
                            mock_intent.recognize_intent.assert_called()
                            mock_dialogue.process_dialogue.assert_called()
    
    def test_error_handling_flow(self):
        """오류 처리 플로우 테스트"""
        with patch.object(self.pipeline, 'initialize_system', return_value=True):
            with patch.object(self.pipeline, 'intent_recognizer') as mock_intent:
                # 시스템 초기화
                self.pipeline.is_initialized = True
                self.pipeline.current_session_id = "session-1"
                
                # 의도 파악 실패 시뮬레이션
                mock_intent.recognize_intent.side_effect = Exception("API 오류")
                
                # 오류 처리 테스트
                result = self.pipeline.process_text_input("테스트 입력")
                
                # 오류 메시지 확인
                self.assertIn("처리", result)
    
    def test_response_formatting(self):
        """응답 포맷팅 테스트"""
        with patch.object(self.pipeline, 'order_manager') as mock_order:
            # 대화 응답 모킹
            dialogue_response = Mock()
            dialogue_response.text = "주문이 추가되었습니다."
            dialogue_response.order_state = Mock()
            dialogue_response.requires_confirmation = True
            dialogue_response.suggested_actions = ["continue_ordering", "confirm_order"]
            
            # 주문 요약 모킹
            order_summary = Mock()
            order_summary.items = [Mock(), Mock()]
            order_summary.total_amount = 10000
            mock_order.get_order_summary.return_value = order_summary
            
            # 주문 의도 모킹
            intent = Mock()
            intent.type = IntentType.ORDER
            
            # 응답 포맷팅 테스트
            result = self.pipeline._format_dialogue_response(dialogue_response, intent)
            
            # 포맷팅 결과 확인
            self.assertIn("주문이 추가되었습니다", result)
            self.assertIn("현재 주문", result)
            self.assertIn("10,000원", result)
            self.assertIn("확인하시려면", result)
            self.assertIn("추가 주문", result)


def run_integration_tests():
    """통합 테스트 실행"""
    print("메인 파이프라인 통합 테스트 시작")
    print("=" * 50)
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestVoiceKioskPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestPipelineIntegration))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 출력
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("모든 통합 테스트가 성공했습니다!")
    else:
        print(f"{len(result.failures)} 실패, {len(result.errors)} 오류")
        
        if result.failures:
            print("\n실패한 테스트:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\n오류가 발생한 테스트:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)