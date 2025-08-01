"""
TTS 통합 테스트
OpenAI TTS API와 TTS 관리자 기능 테스트
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from ..audio.tts_manager import TTSManager
from ..audio.tts_providers.openai_tts import OpenAITTSProvider
from ..audio.tts_providers.base_tts import TTSInitializationError, TTSConversionError
from .response_builder import ResponseBuilder
from ..models.communication_models import ServerResponse


class TestTTSIntegration(unittest.TestCase):
    """TTS 통합 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_text = "안녕하세요. 주문을 도와드리겠습니다."
        
    def tearDown(self):
        """테스트 정리"""
        # 임시 디렉토리 정리
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_tts_manager_initialization(self):
        """TTS 관리자 초기화 테스트"""
        # OpenAI API 키가 없는 경우 초기화 실패 테스트
        with self.assertRaises(TTSInitializationError):
            TTSManager(
                provider_name='openai',
                provider_config={'api_key': None},
                output_directory=str(self.temp_dir)
            )
    
    @patch('openai.OpenAI')
    def test_openai_tts_provider_mock(self, mock_openai):
        """OpenAI TTS 제공자 모킹 테스트"""
        # OpenAI 클라이언트 모킹
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # 모델 목록 모킹
        mock_client.models.list.return_value = []
        
        # TTS 응답 모킹
        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b'fake_audio_data']
        mock_client.audio.speech.create.return_value = mock_response
        
        # TTS 제공자 테스트
        provider = OpenAITTSProvider({
            'api_key': 'test_key',
            'model': 'tts-1',
            'voice': 'alloy'
        })
        
        # 초기화 테스트
        self.assertTrue(provider.initialize())
        self.assertTrue(provider.is_initialized)
        
        # TTS 변환 테스트
        output_path = self.temp_dir / "test_output.wav"
        success = provider.text_to_speech(self.test_text, str(output_path))
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        # OpenAI API 호출 확인
        mock_client.audio.speech.create.assert_called_once_with(
            model='tts-1',
            voice='alloy',
            input=self.test_text,
            speed=1.0,
            response_format='wav'
        )
    
    @patch('openai.OpenAI')
    def test_tts_manager_with_mock(self, mock_openai):
        """TTS 관리자 모킹 테스트"""
        # OpenAI 클라이언트 모킹
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = []
        
        # TTS 응답 모킹
        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b'fake_audio_data']
        mock_client.audio.speech.create.return_value = mock_response
        
        # TTS 관리자 테스트
        manager = TTSManager(
            provider_name='openai',
            provider_config={'api_key': 'test_key'},
            output_directory=str(self.temp_dir)
        )
        
        # TTS 변환 테스트
        file_id = manager.text_to_speech(self.test_text)
        self.assertIsNotNone(file_id)
        
        # 파일 경로 확인
        file_path = manager.get_file_path(file_id)
        self.assertIsNotNone(file_path)
        self.assertTrue(Path(file_path).exists())
        
        # 파일 정보 확인
        file_info = manager.get_file_info(file_id)
        self.assertIsNotNone(file_info)
        self.assertEqual(file_info['text'], self.test_text)
        self.assertEqual(file_info['provider'], 'openai')
    
    @patch('openai.OpenAI')
    def test_response_builder_with_tts(self, mock_openai):
        """ResponseBuilder TTS 통합 테스트"""
        # OpenAI 클라이언트 모킹
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.models.list.return_value = []
        
        # TTS 응답 모킹
        mock_response = MagicMock()
        mock_response.iter_bytes.return_value = [b'fake_audio_data']
        mock_client.audio.speech.create.return_value = mock_response
        
        # ResponseBuilder 테스트
        builder = ResponseBuilder(
            tts_provider='openai',
            tts_config={'api_key': 'test_key'}
        )
        
        # 성공 응답 생성 테스트
        response = builder.build_success_response(
            message=self.test_text,
            session_id="test_session"
        )
        
        self.assertIsInstance(response, ServerResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.message, self.test_text)
        self.assertIsNotNone(response.tts_audio_url)
        self.assertTrue(response.tts_audio_url.startswith("/api/voice/tts/"))
    
    def test_response_builder_fallback(self):
        """ResponseBuilder 폴백 테스트"""
        # 잘못된 설정으로 ResponseBuilder 생성 (폴백 모드)
        builder = ResponseBuilder(
            tts_provider='invalid_provider',
            tts_config={}
        )
        
        # 폴백 TTS로 응답 생성
        response = builder.build_success_response(
            message=self.test_text,
            session_id="test_session"
        )
        
        self.assertIsInstance(response, ServerResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.message, self.test_text)
        # 폴백 모드에서도 TTS URL이 생성되어야 함
        self.assertIsNotNone(response.tts_audio_url)
    
    def test_tts_provider_validation(self):
        """TTS 제공자 설정 검증 테스트"""
        # 잘못된 음성 설정
        with self.assertRaises(Exception):
            OpenAITTSProvider({
                'api_key': 'test_key',
                'voice': 'invalid_voice'
            })
        
        # 잘못된 속도 설정
        with self.assertRaises(Exception):
            OpenAITTSProvider({
                'api_key': 'test_key',
                'speed': 5.0  # 최대 4.0
            })
        
        # 잘못된 모델 설정
        with self.assertRaises(Exception):
            OpenAITTSProvider({
                'api_key': 'test_key',
                'model': 'invalid_model'
            })
    
    def test_text_validation(self):
        """텍스트 유효성 검증 테스트"""
        provider = OpenAITTSProvider({'api_key': 'test_key'})
        
        # 빈 텍스트
        self.assertFalse(provider.validate_text(""))
        self.assertFalse(provider.validate_text("   "))
        
        # 너무 긴 텍스트 (4096자 초과)
        long_text = "a" * 5000
        self.assertFalse(provider.validate_text(long_text))
        
        # 정상 텍스트
        self.assertTrue(provider.validate_text(self.test_text))
    
    def test_cost_estimation(self):
        """비용 추정 테스트"""
        provider = OpenAITTSProvider({'api_key': 'test_key'})
        
        # tts-1 모델 비용 추정
        cost = provider.estimate_cost(self.test_text, 'tts-1')
        self.assertGreater(cost, 0)
        
        # tts-1-hd 모델 비용 추정 (더 비싸야 함)
        cost_hd = provider.estimate_cost(self.test_text, 'tts-1-hd')
        self.assertGreater(cost_hd, cost)


def run_tts_integration_tests():
    """TTS 통합 테스트 실행"""
    unittest.main(module=__name__, verbosity=2)


if __name__ == "__main__":
    run_tts_integration_tests()