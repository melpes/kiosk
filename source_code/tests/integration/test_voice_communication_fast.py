"""
빠른 음성 통신 통합 테스트
실제 API 호출 없이 모의 처리로 빠르게 실행되는 테스트

Requirements: 2.1, 2.2, 3.1, 3.2, 3.3, 3.4
"""

import pytest
import time
import tempfile
import os
import json
from pathlib import Path
from typing import Dict, Any
import wave
import struct
from unittest.mock import Mock, patch, MagicMock

# 프로젝트 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.communication_models import ServerResponse, ErrorCode, ErrorInfo
from src.logger import get_logger
from fastapi.testclient import TestClient

logger = get_logger(__name__)


class TestVoiceCommunicationFast:
    """빠른 음성 통신 통합 테스트 클래스"""
    
    @pytest.fixture(scope="class")
    def test_client(self):
        """FastAPI 테스트 클라이언트 (모의 처리)"""
        # 테스트용 환경 변수 설정
        os.environ["TESTING"] = "true"
        os.environ["TTS_PROVIDER"] = "mock"
        os.environ["OPENAI_API_KEY"] = "test_key"
        
        # FastAPI 앱 import 및 테스트 클라이언트 생성
        from src.api.server import app
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def sample_wav_file(self):
        """테스트용 WAV 파일 생성"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        # 간단한 WAV 파일 생성 (0.1초, 16kHz, 모노)
        sample_rate = 16000
        duration = 0.1  # 매우 짧게
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            # 간단한 무음 데이터
            frames = b'\x00\x00' * int(sample_rate * duration)
            wav_file.writeframes(frames)
        
        yield temp_file.name
        
        # 정리
        try:
            os.unlink(temp_file.name)
        except:
            pass
    
    def test_basic_communication_fast(self, test_client, sample_wav_file):
        """
        기본 통신 테스트 (빠른 버전)
        Requirements: 1.2, 1.3, 4.1
        """
        logger.info("빠른 기본 통신 테스트 시작")
        
        # 서버 상태 확인
        response = test_client.get("/health")
        assert response.status_code == 200
        
        # 음성 파일 전송 (모의 처리로 빠름)
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            # 모의 응답 설정
            mock_response = ServerResponse.create_success_response(
                message="테스트 응답",
                processing_time=0.1
            )
            mock_process.return_value = mock_response
            
            with open(sample_wav_file, 'rb') as audio_file:
                files = {'audio_file': ('test.wav', audio_file, 'audio/wav')}
                response = test_client.post("/api/voice/process", files=files)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data['success']
            assert 'processing_time' in response_data
        
        logger.info("빠른 기본 통신 테스트 완료")
    
    def test_session_continuity_fast(self, test_client, sample_wav_file):
        """
        세션 연속성 테스트 (빠른 버전)
        Requirements: 4.2, 4.3
        """
        logger.info("빠른 세션 연속성 테스트 시작")
        
        session_id = "test_session_fast"
        
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            mock_response = ServerResponse.create_success_response(
                message="세션 테스트",
                session_id=session_id,
                processing_time=0.1
            )
            mock_process.return_value = mock_response
            
            # 첫 번째 요청
            with open(sample_wav_file, 'rb') as audio_file:
                files = {'audio_file': ('test1.wav', audio_file, 'audio/wav')}
                data = {'session_id': session_id}
                response1 = test_client.post("/api/voice/process", files=files, data=data)
            
            # 두 번째 요청
            with open(sample_wav_file, 'rb') as audio_file:
                files = {'audio_file': ('test2.wav', audio_file, 'audio/wav')}
                data = {'session_id': session_id}
                response2 = test_client.post("/api/voice/process", files=files, data=data)
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            response1_data = response1.json()
            response2_data = response2.json()
            
            assert response1_data['success']
            assert response2_data['success']
        
        logger.info("빠른 세션 연속성 테스트 완료")
    
    def test_file_format_handling_fast(self, test_client):
        """
        파일 형식 처리 테스트 (빠른 버전)
        Requirements: 5.1
        """
        logger.info("빠른 파일 형식 테스트 시작")
        
        # 지원되는 형식 테스트
        supported_formats = [
            ('test.wav', 'audio/wav'),
            ('test.WAV', 'audio/wav'),
        ]
        
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            mock_response = ServerResponse.create_success_response(
                message="파일 형식 테스트",
                processing_time=0.1
            )
            mock_process.return_value = mock_response
            
            for filename, content_type in supported_formats:
                # 임시 WAV 파일 생성
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                with wave.open(temp_file.name, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(b'\x00\x00' * 100)
                
                try:
                    with open(temp_file.name, 'rb') as audio_file:
                        files = {'audio_file': (filename, audio_file, content_type)}
                        response = test_client.post("/api/voice/process", files=files)
                    
                    assert response.status_code == 200
                    response_data = response.json()
                    assert response_data['success']
                    
                finally:
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
        
        logger.info("빠른 파일 형식 테스트 완료")
    
    def test_error_handling_fast(self, test_client, sample_wav_file):
        """
        오류 처리 테스트 (빠른 버전)
        Requirements: 3.1, 3.2, 3.3, 3.4
        """
        logger.info("빠른 오류 처리 테스트 시작")
        
        # 서버 오류 시뮬레이션
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            mock_process.side_effect = Exception("테스트 오류")
            
            with open(sample_wav_file, 'rb') as audio_file:
                files = {'audio_file': ('test.wav', audio_file, 'audio/wav')}
                response = test_client.post("/api/voice/process", files=files)
            
            # 오류 응답이지만 구조화된 형태로 와야 함
            assert response.status_code == 200  # 오류도 ServerResponse로 반환
            response_data = response.json()
            assert not response_data['success']
            assert 'error_info' in response_data
        
        logger.info("빠른 오류 처리 테스트 완료")
    
    def test_performance_fast(self, test_client, sample_wav_file):
        """
        성능 테스트 (빠른 버전)
        Requirements: 2.1, 2.2
        """
        logger.info("빠른 성능 테스트 시작")
        
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            mock_response = ServerResponse.create_success_response(
                message="성능 테스트",
                processing_time=0.1
            )
            mock_process.return_value = mock_response
            
            # 5번 테스트
            response_times = []
            for i in range(5):
                start_time = time.time()
                
                with open(sample_wav_file, 'rb') as audio_file:
                    files = {'audio_file': (f'test_{i}.wav', audio_file, 'audio/wav')}
                    response = test_client.post("/api/voice/process", files=files)
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                assert response.status_code == 200
                response_data = response.json()
                assert response_data['success']
                
                # 모의 처리이므로 매우 빨라야 함
                assert response_time <= 1.0, f"모의 처리 응답 시간 초과: {response_time:.2f}초"
            
            avg_response_time = sum(response_times) / len(response_times)
            logger.info(f"평균 응답 시간: {avg_response_time:.3f}초")
            
            # 모의 처리 환경에서의 성능 검증
            assert avg_response_time <= 0.5, f"모의 처리 평균 응답 시간 초과: {avg_response_time:.3f}초"
        
        logger.info("빠른 성능 테스트 완료")
    
    def test_concurrent_requests_fast(self, test_client, sample_wav_file):
        """
        동시 요청 처리 테스트 (빠른 버전)
        Requirements: 2.3
        """
        logger.info("빠른 동시 요청 테스트 시작")
        
        import concurrent.futures
        
        def send_request(request_id: int) -> Dict[str, Any]:
            """단일 요청 전송"""
            try:
                start_time = time.time()
                
                with open(sample_wav_file, 'rb') as audio_file:
                    files = {'audio_file': (f'concurrent_test_{request_id}.wav', audio_file, 'audio/wav')}
                    response = test_client.post("/api/voice/process", files=files)
                
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e)
                }
        
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            mock_response = ServerResponse.create_success_response(
                message="동시 요청 테스트",
                processing_time=0.1
            )
            mock_process.return_value = mock_response
            
            # 5개 동시 요청 (빠른 테스트용)
            concurrent_requests = 5
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [
                    executor.submit(send_request, i) 
                    for i in range(concurrent_requests)
                ]
                
                results = []
                for future in concurrent.futures.as_completed(futures, timeout=10):
                    result = future.result()
                    results.append(result)
            
            # 결과 분석
            successful_requests = [r for r in results if r['success']]
            success_rate = len(successful_requests) / len(results) * 100
            
            logger.info(f"동시 요청 결과: {len(successful_requests)}/{len(results)} 성공 ({success_rate:.1f}%)")
            
            # 모의 처리 환경에서는 높은 성공률 기대
            assert success_rate >= 80.0, f"동시 요청 성공률 부족: {success_rate:.1f}%"
        
        logger.info("빠른 동시 요청 테스트 완료")
    
    def test_end_to_end_fast(self, test_client, sample_wav_file):
        """
        전체 워크플로우 테스트 (빠른 버전)
        Requirements: 1.1, 1.2, 1.3, 2.1, 4.1, 4.2, 4.3, 4.4
        """
        logger.info("빠른 종단간 테스트 시작")
        
        session_id = "e2e_test_fast"
        
        with patch('src.api.voice_processing_api.VoiceProcessingAPI.process_audio_request') as mock_process:
            mock_response = ServerResponse.create_success_response(
                message="종단간 테스트",
                session_id=session_id,
                processing_time=0.1
            )
            mock_process.return_value = mock_response
            
            # 1. 서버 상태 확인
            health_response = test_client.get("/health")
            assert health_response.status_code == 200
            
            # 2. 첫 번째 음성 요청
            with open(sample_wav_file, 'rb') as audio_file:
                files = {'audio_file': ('order_start.wav', audio_file, 'audio/wav')}
                data = {'session_id': session_id}
                response1 = test_client.post("/api/voice/process", files=files, data=data)
            
            assert response1.status_code == 200
            response1_data = response1.json()
            assert response1_data['success']
            
            # 3. 두 번째 음성 요청
            with open(sample_wav_file, 'rb') as audio_file:
                files = {'audio_file': ('order_add.wav', audio_file, 'audio/wav')}
                data = {'session_id': session_id}
                response2 = test_client.post("/api/voice/process", files=files, data=data)
            
            assert response2.status_code == 200
            response2_data = response2.json()
            assert response2_data['success']
            
            # 4. 시스템 상태 최종 확인
            status_response = test_client.get("/api/system/status")
            assert status_response.status_code == 200
        
        logger.info("빠른 종단간 테스트 완료")


if __name__ == "__main__":
    # 빠른 테스트만 실행
    pytest.main([__file__, "-v", "--tb=short"])