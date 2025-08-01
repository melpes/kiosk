"""
음성 처리 API 클래스
기존 VoiceKioskPipeline과 연동하여 HTTP API 서비스 제공
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..main import VoiceKioskPipeline
from ..logger import get_logger
from ..models.communication_models import ServerResponse, OrderData, UIAction, ErrorInfo, ErrorCode
from .response_builder import ResponseBuilder


class VoiceProcessingAPI:
    """음성 처리 API 클래스"""
    
    def __init__(self, 
                 pipeline: Optional[VoiceKioskPipeline] = None,
                 tts_provider: str = "openai",
                 tts_config: Optional[Dict[str, Any]] = None):
        """
        API 초기화
        
        Args:
            pipeline: 기존 VoiceKioskPipeline 인스턴스 (None인 경우 새로 생성)
            tts_provider: 사용할 TTS 제공자 (기본: openai)
            tts_config: TTS 제공자 설정
        """
        self.logger = get_logger(__name__)
        
        # 파이프라인 초기화
        if pipeline is None:
            self.pipeline = VoiceKioskPipeline()
            if not self.pipeline.initialize_system():
                raise RuntimeError("VoiceKioskPipeline 초기화 실패")
        else:
            self.pipeline = pipeline
        
        # ResponseBuilder 초기화 (TTS 설정 및 최적화 포함)
        self.response_builder = ResponseBuilder(
            tts_provider=tts_provider,
            tts_config=tts_config,
            enable_optimization=True
        )
        
        self.logger.info("VoiceProcessingAPI 초기화 완료")
    
    def process_audio_request(self, audio_file_path: str, session_id: Optional[str] = None) -> ServerResponse:
        """
        음성 파일 처리 요청 (최적화 기능 포함)
        
        Args:
            audio_file_path: 업로드된 음성 파일 경로
            session_id: 세션 ID (None인 경우 새 세션 생성)
            
        Returns:
            ServerResponse: 처리 결과
        """
        start_time = datetime.now()
        optimized_file_path = None
        
        try:
            self.logger.info(f"음성 처리 요청 시작: {audio_file_path}")
            
            # 최적화 관리자를 통한 파일 최적화
            try:
                from .optimization import get_optimization_manager
                optimization_manager = get_optimization_manager()
                
                # 파일 압축 해제 (필요한 경우)
                if audio_file_path.endswith('.gz'):
                    optimized_file_path = optimization_manager.compressor.decompress_audio_file(audio_file_path)
                    self.logger.info(f"압축 파일 해제: {audio_file_path} -> {optimized_file_path}")
                else:
                    optimized_file_path = audio_file_path
                    
            except Exception as e:
                self.logger.warning(f"파일 최적화 실패, 원본 파일 사용: {e}")
                optimized_file_path = audio_file_path
            
            # 세션 관리 - 세션만 생성하고 인사말은 생략
            if session_id is None:
                session_id = self.pipeline.dialogue_manager.create_session()
                self.pipeline.current_session_id = session_id
                self.logger.info(f"새로운 세션 생성: {session_id}")
            else:
                self.pipeline.current_session_id = session_id
                self.logger.info(f"기존 세션 사용: {session_id}")
            
            # 음성 처리 - AudioProcessor를 거쳐 화자 분리 포함 전처리 수행
            if not self.pipeline.speech_recognizer:
                response_text = "음성인식 기능을 사용할 수 없습니다. 텍스트로 입력해 주세요."
            else:
                try:
                    print(f"\n🎤 음성 처리 파이프라인 시작: {optimized_file_path}")
                    
                    # 1. 오디오 파일 로드 및 AudioData 생성
                    audio_data = self.pipeline.audio_processor.create_audio_data(optimized_file_path)
                    print(f"📊 오디오 로드 완료: {audio_data.duration:.2f}초, {audio_data.sample_rate}Hz")
                    
                    # 2. AudioProcessor를 통한 전처리 (화자 분리 포함!)
                    processed_audio = self.pipeline.audio_processor.process_audio(audio_data)
                    print(f"✅ 전처리 완료 (화자 분리 포함)")
                    
                    # 3. 전처리된 오디오로 음성 인식
                    # processed_audio.features는 Mel spectrogram이므로 원본 데이터로 인식
                    # 임시로 원본 파일 사용 (향후 processed audio 직접 사용으로 개선 가능)
                    recognition_result = self.pipeline.speech_recognizer.recognize_from_file(optimized_file_path)
                    recognized_text = recognition_result.text.strip()
                    
                    if not recognized_text:
                        response_text = "죄송합니다. 음성을 인식하지 못했습니다. 다시 말씀해 주세요."
                    else:
                        print(f"🎯 음성 인식 완료: '{recognized_text}'")
                        # 직접 텍스트 처리 호출 (인사말 없이)
                        response_text = self.pipeline.process_text_input(recognized_text, from_speech=True)
                        
                except Exception as audio_error:
                    self.logger.error(f"음성 전처리 실패: {audio_error}")
                    print(f"⚠️  전처리 실패, 원본으로 직접 인식 시도: {str(audio_error)[:50]}...")
                    
                    # 전처리 실패시 원본 파일로 직접 인식
                    recognition_result = self.pipeline.speech_recognizer.recognize_from_file(optimized_file_path)
                    recognized_text = recognition_result.text.strip()
                    
                    if not recognized_text:
                        response_text = "죄송합니다. 음성을 인식하지 못했습니다. 다시 말씀해 주세요."
                    else:
                        response_text = self.pipeline.process_text_input(recognized_text, from_speech=True)
            
            # 처리 시간 계산
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # ResponseBuilder를 사용하여 응답 생성
            response = self.response_builder.build_success_response(
                message=response_text,
                order_data=self._get_current_order_data(),
                session_id=session_id,
                processing_time=processing_time
            )
            
            self.logger.info(f"음성 처리 완료 (처리시간: {processing_time:.2f}초)")
            return response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"음성 처리 실패: {e}")
            
            # ResponseBuilder를 사용하여 오류 응답 생성
            return self.response_builder.build_error_response(
                error_code=ErrorCode.AUDIO_PROCESSING_ERROR,
                error_message=f"음성 처리 중 오류가 발생했습니다: {str(e)}",
                recovery_actions=["다시 시도해 주세요", "음성을 더 명확하게 말씀해 주세요"],
                session_id=session_id,
                processing_time=processing_time
            )
        finally:
            # 최적화로 생성된 임시 파일 정리
            if optimized_file_path and optimized_file_path != audio_file_path and os.path.exists(optimized_file_path):
                try:
                    os.remove(optimized_file_path)
                    self.logger.debug(f"최적화 임시 파일 삭제: {optimized_file_path}")
                except Exception as e:
                    self.logger.warning(f"최적화 임시 파일 삭제 실패: {e}")
    
    def get_tts_file(self, file_id: str) -> Optional[str]:
        """
        TTS 파일 경로 반환
        
        Args:
            file_id: TTS 파일 ID
            
        Returns:
            파일 경로 (존재하지 않으면 None)
        """
        # ResponseBuilder의 TTS 파일 관리 기능 사용
        return self.response_builder.get_tts_file_path(file_id)
    

    
    def _get_current_order_data(self) -> Optional[OrderData]:
        """
        현재 주문 상태 데이터 가져오기
        
        Returns:
            OrderData 또는 None
        """
        try:
            if not self.pipeline.order_manager:
                return None
            
            current_order = self.pipeline.order_manager.get_current_order()
            if not current_order or not current_order.items:
                return None
            
            # ResponseBuilder를 사용하여 Order를 OrderData로 변환
            return self.response_builder._convert_order_to_order_data(current_order)
            
        except Exception as e:
            self.logger.error(f"주문 데이터 가져오기 실패: {e}")
            return None
    
    def process_dialogue_response(self, dialogue_response, session_id: Optional[str] = None, processing_time: float = 0.0) -> ServerResponse:
        """
        DialogueResponse를 ServerResponse로 변환
        
        Args:
            dialogue_response: DialogueResponse 객체
            session_id: 세션 ID
            processing_time: 처리 시간
            
        Returns:
            ServerResponse: 변환된 응답
        """
        try:
            return self.response_builder.build_response_from_dialogue(
                dialogue_response,
                session_id,
                processing_time
            )
        except Exception as e:
            self.logger.error(f"DialogueResponse 처리 실패: {e}")
            return self.response_builder.build_error_response(
                error_code=ErrorCode.SERVER_ERROR,
                error_message=f"응답 처리 중 오류가 발생했습니다: {str(e)}",
                session_id=session_id,
                processing_time=processing_time
            )
    
    def cleanup_expired_files(self):
        """만료된 TTS 파일 정리"""
        # ResponseBuilder의 파일 정리 기능 사용
        self.response_builder.cleanup_expired_files()