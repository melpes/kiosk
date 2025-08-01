"""
CLI 인터페이스 단위 테스트
"""

import unittest
import sys
import io
from unittest.mock import Mock, patch, MagicMock
from contextlib import redirect_stdout
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.cli.interface import CLIInterface, create_argument_parser


class TestCLIInterface(unittest.TestCase):
    """CLI 인터페이스 단위 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.cli = CLIInterface()
        
        # Mock 파이프라인 생성
        self.mock_pipeline = Mock()
        self.mock_pipeline.get_system_status.return_value = {
            'initialized': True,
            'running': False,
            'current_session': 'test_session_123',
            'modules': {
                'audio_processor': True,
                'speech_recognizer': True,
                'intent_recognizer': True,
                'dialogue_manager': True,
                'order_manager': True,
                'response_system': True
            },
            'order_stats': {
                'total_orders': 5,
                'completed_orders': 3,
                'cancelled_orders': 1
            },
            'session_stats': {
                'active_sessions': 1,
                'total_sessions': 10
            }
        }
        
        self.cli.pipeline = self.mock_pipeline
    
    def test_cli_initialization(self):
        """CLI 초기화 테스트"""
        cli = CLIInterface()
        
        # 기본 속성 확인
        self.assertIsNotNone(cli.logger)
        self.assertIsNone(cli.pipeline)
        self.assertFalse(cli.is_running)
        self.assertIsInstance(cli.commands, dict)
        
        # 명령어 매핑 확인
        expected_commands = [
            'help', '도움말', 'status', '상태', 'order', '주문확인',
            'menu', '메뉴', 'clear', '초기화', 'config', '설정',
            'quit', 'exit', '종료', 'q', 'new', '새주문',
            'demo', '데모', 'test', '테스트'
        ]
        
        for cmd in expected_commands:
            self.assertIn(cmd, cli.commands)
    
    def test_show_help(self):
        """도움말 표시 테스트"""
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_help()
        
        help_output = output.getvalue()
        
        # 도움말 내용 확인
        self.assertIn('사용 가능한 명령어', help_output)
        self.assertIn('help', help_output)
        self.assertIn('status', help_output)
        self.assertIn('주문 예시', help_output)
        self.assertIn('음성 파일 테스트', help_output)
    
    def test_show_status(self):
        """상태 표시 테스트"""
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_status()
        
        status_output = output.getvalue()
        
        # 상태 정보 확인
        self.assertIn('시스템 상태', status_output)
        self.assertIn('초기화됨: ✅', status_output)
        self.assertIn('test_session_123', status_output)
        self.assertIn('모듈 상태', status_output)
        self.assertIn('주문 통계', status_output)
        self.assertIn('세션 통계', status_output)
    
    def test_show_status_no_pipeline(self):
        """파이프라인 없을 때 상태 표시 테스트"""
        self.cli.pipeline = None
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_status()
        
        status_output = output.getvalue()
        self.assertIn('파이프라인이 초기화되지 않았습니다', status_output)
    
    def test_show_order(self):
        """주문 표시 테스트"""
        # Mock 주문 데이터 설정
        mock_order_summary = Mock()
        mock_order_summary.items = [
            Mock(
                name='빅맥 세트',
                category='세트',
                quantity=1,
                price=6500,
                options={'음료': '콜라', '사이드': '감자튀김'}
            ),
            Mock(
                name='치킨너겟',
                category='단품',
                quantity=2,
                price=3000,
                options={}
            )
        ]
        mock_order_summary.total_amount = 9500
        mock_order_summary.status = Mock(value='진행중')
        
        self.mock_pipeline.order_manager.get_order_summary.return_value = mock_order_summary
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_order()
        
        order_output = output.getvalue()
        
        # 주문 내역 확인
        self.assertIn('현재 주문 내역', order_output)
        self.assertIn('빅맥 세트', order_output)
        self.assertIn('치킨너겟', order_output)
        self.assertIn('9,500원', order_output)
        self.assertIn('진행중', order_output)
    
    def test_show_order_empty(self):
        """빈 주문 표시 테스트"""
        mock_order_summary = Mock()
        mock_order_summary.items = []
        
        self.mock_pipeline.order_manager.get_order_summary.return_value = mock_order_summary
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_order()
        
        order_output = output.getvalue()
        self.assertIn('현재 주문 내역이 없습니다', order_output)
    
    def test_show_menu(self):
        """메뉴 표시 테스트"""
        # Mock 메뉴 데이터 설정
        mock_menu = Mock()
        mock_menu.categories = ['세트', '단품', '음료']
        
        mock_menu_items = [
            Mock(name='빅맥 세트', price=6500, description='빅맥 + 감자튀김 + 음료'),
            Mock(name='치킨너겟', price=3000, description='바삭한 치킨너겟 6조각')
        ]
        
        mock_menu.get_items_by_category.side_effect = lambda cat: {
            '세트': [mock_menu_items[0]],
            '단품': [mock_menu_items[1]],
            '음료': []
        }.get(cat, [])
        
        self.mock_pipeline.order_manager.menu = mock_menu
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_menu()
        
        menu_output = output.getvalue()
        
        # 메뉴 내용 확인
        self.assertIn('사용 가능한 메뉴', menu_output)
        self.assertIn('세트', menu_output)
        self.assertIn('단품', menu_output)
        self.assertIn('빅맥 세트', menu_output)
        self.assertIn('치킨너겟', menu_output)
    
    def test_clear_order(self):
        """주문 초기화 테스트"""
        self.mock_pipeline.start_session.return_value = 'new_session_123'
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.clear_order()
        
        clear_output = output.getvalue()
        
        # 초기화 확인
        self.assertIn('주문이 초기화되었습니다', clear_output)
        self.mock_pipeline.start_session.assert_called_once()
    
    @patch('src.cli.interface.config_manager')
    def test_show_config(self, mock_config_manager):
        """설정 표시 테스트"""
        # Mock 설정 데이터
        mock_config_manager.get_config_summary.return_value = {
            'api': {
                'model': 'gpt-4o',
                'max_tokens': 1000,
                'temperature': 0.7,
                'api_key_set': True
            },
            'menu': {
                'restaurant_name': '테스트 식당',
                'restaurant_type': 'fast_food',
                'menu_items_count': 15,
                'categories_count': 3,
                'last_modified': '2024-01-01T12:00:00'
            },
            'audio': {
                'sample_rate': 16000,
                'chunk_size': 1024,
                'noise_reduction_level': 0.5,
                'speaker_separation_threshold': 0.7
            },
            'system': {
                'log_level': 'INFO',
                'language': 'ko'
            }
        }
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_config()
        
        config_output = output.getvalue()
        
        # 설정 정보 확인
        self.assertIn('시스템 설정', config_output)
        self.assertIn('API 설정', config_output)
        self.assertIn('메뉴 설정', config_output)
        self.assertIn('음성 설정', config_output)
        self.assertIn('gpt-4o', config_output)
        self.assertIn('테스트 식당', config_output)
    
    def test_process_command_valid(self):
        """유효한 명령어 처리 테스트"""
        with patch.object(self.cli, 'show_help') as mock_help:
            result = self.cli.process_command('help')
            self.assertTrue(result)
            mock_help.assert_called_once()
        
        with patch.object(self.cli, 'show_status') as mock_status:
            result = self.cli.process_command('status arg1 arg2')
            self.assertTrue(result)
            mock_status.assert_called_once_with(['arg1', 'arg2'])
    
    def test_process_command_invalid(self):
        """무효한 명령어 처리 테스트"""
        result = self.cli.process_command('invalid_command')
        self.assertFalse(result)
        
        result = self.cli.process_command('존재하지않는명령어')
        self.assertFalse(result)
    
    def test_process_command_empty(self):
        """빈 명령어 처리 테스트"""
        result = self.cli.process_command('')
        self.assertTrue(result)
        
        result = self.cli.process_command('   ')
        self.assertTrue(result)
    
    def test_quit_system(self):
        """시스템 종료 테스트"""
        self.cli.is_running = True
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.quit_system()
        
        quit_output = output.getvalue()
        
        # 종료 확인
        self.assertFalse(self.cli.is_running)
        self.assertIn('시스템을 종료합니다', quit_output)
        self.mock_pipeline.shutdown.assert_called_once()
    
    def test_run_demo(self):
        """데모 실행 테스트"""
        self.mock_pipeline.process_text_input.side_effect = [
            '빅맥 세트를 주문하겠습니다.',
            '음료를 사이다로 변경했습니다.',
            '감자튀김을 추가했습니다.',
            '현재 주문: 빅맥 세트 1개',
            '결제를 진행하겠습니다.'
        ]
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.run_demo()
        
        demo_output = output.getvalue()
        
        # 데모 실행 확인
        self.assertIn('데모 시나리오를 실행합니다', demo_output)
        self.assertIn('빅맥 세트 하나 주세요', demo_output)
        self.assertIn('데모 시나리오 완료', demo_output)
        
        # 모든 시나리오가 실행되었는지 확인
        self.assertEqual(self.mock_pipeline.process_text_input.call_count, 5)
    
    def test_run_test(self):
        """시스템 테스트 실행 테스트"""
        # Mock 의도 파악 결과
        mock_intents = [
            Mock(type=Mock(value='ORDER'), confidence=0.95),
            Mock(type=Mock(value='MODIFY'), confidence=0.90),
            Mock(type=Mock(value='CANCEL'), confidence=0.85),
            Mock(type=Mock(value='PAYMENT'), confidence=0.92),
            Mock(type=Mock(value='INQUIRY'), confidence=0.88)
        ]
        
        self.mock_pipeline.start_session.return_value = 'test_session'
        self.mock_pipeline.dialogue_manager.get_context.return_value = {}
        self.mock_pipeline.intent_recognizer.recognize_intent.side_effect = mock_intents
        self.mock_pipeline.process_text_input.return_value = '테스트 응답입니다.'
        
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.run_test()
        
        test_output = output.getvalue()
        
        # 테스트 실행 확인
        self.assertIn('시스템 테스트를 실행합니다', test_output)
        self.assertIn('테스트 결과', test_output)
        self.assertIn('5/5 통과', test_output)
        self.assertIn('성공률: 100.0%', test_output)


class TestArgumentParser(unittest.TestCase):
    """명령행 인수 파서 테스트"""
    
    def test_create_argument_parser(self):
        """인수 파서 생성 테스트"""
        parser = create_argument_parser()
        
        # 파서 기본 속성 확인
        self.assertIsNotNone(parser)
        
        # 기본 인수 파싱 테스트
        args = parser.parse_args([])
        self.assertFalse(args.demo)
        self.assertFalse(args.test)
        self.assertFalse(args.status)
        self.assertFalse(args.config)
        self.assertEqual(args.log_level, 'INFO')
        self.assertIsNone(args.log_file)
    
    def test_argument_parsing(self):
        """인수 파싱 테스트"""
        parser = create_argument_parser()
        
        # 데모 옵션
        args = parser.parse_args(['--demo'])
        self.assertTrue(args.demo)
        
        # 테스트 옵션
        args = parser.parse_args(['--test'])
        self.assertTrue(args.test)
        
        # 상태 옵션
        args = parser.parse_args(['--status'])
        self.assertTrue(args.status)
        
        # 설정 옵션
        args = parser.parse_args(['--config'])
        self.assertTrue(args.config)
        
        # 로그 레벨 옵션
        args = parser.parse_args(['--log-level', 'DEBUG'])
        self.assertEqual(args.log_level, 'DEBUG')
        
        # 로그 파일 옵션
        args = parser.parse_args(['--log-file', 'test.log'])
        self.assertEqual(args.log_file, 'test.log')
        
        # 복합 옵션
        args = parser.parse_args(['--demo', '--log-level', 'ERROR', '--log-file', 'demo.log'])
        self.assertTrue(args.demo)
        self.assertEqual(args.log_level, 'ERROR')
        self.assertEqual(args.log_file, 'demo.log')


if __name__ == '__main__':
    unittest.main()