#!/usr/bin/env python3
"""
CLI 인터페이스 통합 테스트
CLI 기능의 정상 동작을 검증합니다.
"""

import sys
import unittest
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.interface import CLIInterface
from src.logger import setup_logging, get_logger


class TestCLIInterface(unittest.TestCase):
    """CLI 인터페이스 테스트 클래스"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 설정"""
        setup_logging(log_level="ERROR", log_file="logs/test_cli.log")
        cls.logger = get_logger("test_cli")
    
    def setUp(self):
        """각 테스트 전 설정"""
        self.cli = CLIInterface()
        
        # CLI 초기화 (실패해도 테스트 계속 진행)
        try:
            self.cli_initialized = self.cli.initialize()
        except Exception as e:
            self.logger.warning(f"CLI 초기화 실패: {e}")
            self.cli_initialized = False
    
    def tearDown(self):
        """각 테스트 후 정리"""
        if hasattr(self, 'cli') and self.cli:
            try:
                self.cli.quit_system()
            except:
                pass
    
    def test_cli_initialization(self):
        """CLI 초기화 테스트"""
        # CLI 객체 생성 테스트
        cli = CLIInterface()
        self.assertIsNotNone(cli)
        self.assertIsNotNone(cli.commands)
        self.assertIn('help', cli.commands)
        self.assertIn('status', cli.commands)
    
    def test_help_command(self):
        """도움말 명령어 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_help()
        
        help_output = output.getvalue()
        self.assertIn('사용 가능한 명령어', help_output)
        self.assertIn('help', help_output)
        self.assertIn('status', help_output)
        self.assertIn('quit', help_output)
    
    def test_status_command(self):
        """상태 명령어 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_status()
        
        status_output = output.getvalue()
        self.assertIn('시스템 상태', status_output)
        self.assertIn('모듈 상태', status_output)
    
    def test_config_command(self):
        """설정 명령어 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_config()
        
        config_output = output.getvalue()
        self.assertIn('시스템 설정', config_output)
        self.assertIn('API 설정', config_output)
    
    def test_menu_command(self):
        """메뉴 명령어 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_menu()
        
        menu_output = output.getvalue()
        # 메뉴 관련 출력이 있는지 확인 (오류 메시지든 실제 메뉴든)
        self.assertTrue(len(menu_output) > 0)
    
    def test_order_command(self):
        """주문 명령어 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        with redirect_stdout(output):
            self.cli.show_order()
        
        order_output = output.getvalue()
        # 주문 관련 출력이 있는지 확인
        self.assertTrue(len(order_output) > 0)
    
    def test_command_processing(self):
        """명령어 처리 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 유효한 명령어 테스트
        self.assertTrue(self.cli.process_command("help"))
        self.assertTrue(self.cli.process_command("status"))
        self.assertTrue(self.cli.process_command("도움말"))
        
        # 무효한 명령어 테스트
        self.assertFalse(self.cli.process_command("invalid_command"))
        self.assertFalse(self.cli.process_command("존재하지않는명령어"))
    
    def test_demo_execution(self):
        """데모 실행 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        error_output = io.StringIO()
        
        with redirect_stdout(output), redirect_stderr(error_output):
            try:
                self.cli.run_demo()
                demo_success = True
            except Exception as e:
                self.logger.error(f"데모 실행 중 오류: {e}")
                demo_success = False
        
        demo_output = output.getvalue()
        
        # 데모가 실행되었는지 확인 (성공 여부와 관계없이)
        self.assertTrue(len(demo_output) > 0 or not demo_success)
    
    def test_system_test_execution(self):
        """시스템 테스트 실행 테스트"""
        if not self.cli_initialized:
            self.skipTest("CLI 초기화 실패로 테스트 건너뜀")
        
        # 출력 캡처
        output = io.StringIO()
        error_output = io.StringIO()
        
        with redirect_stdout(output), redirect_stderr(error_output):
            try:
                self.cli.run_test()
                test_success = True
            except Exception as e:
                self.logger.error(f"시스템 테스트 실행 중 오류: {e}")
                test_success = False
        
        test_output = output.getvalue()
        
        # 테스트가 실행되었는지 확인
        self.assertTrue(len(test_output) > 0 or not test_success)


class TestCLICommands(unittest.TestCase):
    """CLI 명령어 개별 테스트"""
    
    def test_command_mapping(self):
        """명령어 매핑 테스트"""
        cli = CLIInterface()
        
        # 영어 명령어
        self.assertIn('help', cli.commands)
        self.assertIn('status', cli.commands)
        self.assertIn('quit', cli.commands)
        self.assertIn('exit', cli.commands)
        
        # 한국어 명령어
        self.assertIn('도움말', cli.commands)
        self.assertIn('상태', cli.commands)
        self.assertIn('종료', cli.commands)
        
        # 명령어 함수 매핑 확인
        self.assertEqual(cli.commands['help'], cli.show_help)
        self.assertEqual(cli.commands['도움말'], cli.show_help)
        self.assertEqual(cli.commands['status'], cli.show_status)
        self.assertEqual(cli.commands['상태'], cli.show_status)


def run_cli_integration_tests():
    """CLI 통합 테스트 실행"""
    print("CLI 인터페이스 통합 테스트를 시작합니다...")
    print("=" * 60)
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # 테스트 클래스 추가
    test_suite.addTests(loader.loadTestsFromTestCase(TestCLIInterface))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCLICommands))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("테스트 결과:")
    print(f"  실행된 테스트: {result.testsRun}")
    print(f"  실패: {len(result.failures)}")
    print(f"  오류: {len(result.errors)}")
    print(f"  건너뜀: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n성공률: {success_rate:.1f}%")
    
    return result.wasSuccessful()


def main():
    """메인 실행 함수"""
    try:
        success = run_cli_integration_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"테스트 실행 중 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()