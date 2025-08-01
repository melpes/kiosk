"""
FastAPI 기반 음성 처리 서버
"""

import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .voice_processing_api import VoiceProcessingAPI
from .error_handler import api_error_handler, handle_api_error
from .security import (
    SecurityConfig, SecurityMiddleware, RateLimitConfig, validate_file_upload, 
    get_security_stats, clear_rate_limit_data
)
from .monitoring import get_monitor, get_alert_manager
from ..logger import get_logger
from ..models.communication_models import ServerResponse


# FastAPI 앱 생성
app = FastAPI(
    title="Voice Kiosk API",
    description="음성 기반 키오스크 시스템 API",
    version="1.0.0"
)

# 보안 설정 생성
security_config = SecurityConfig(
    max_file_size=int(os.getenv('MAX_FILE_SIZE_MB', '10')) * 1024 * 1024,  # MB를 바이트로 변환
    allowed_file_types=os.getenv('ALLOWED_MIME_TYPES', 'audio/wav,audio/x-wav').split(','),
    allowed_extensions=os.getenv('ALLOWED_FILE_EXTENSIONS', '.wav').split(','),
    force_https=os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
    rate_limit=RateLimitConfig(
        max_requests=int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
        time_window=int(os.getenv('RATE_LIMIT_WINDOW', '3600')),
        block_duration=int(os.getenv('RATE_LIMIT_BLOCK', '3600'))
    ),
    trusted_proxies=[ip.strip() for ip in os.getenv('TRUSTED_PROXIES', '').split(',') if ip.strip()]
)

# 보안 미들웨어 추가
app.add_middleware(SecurityMiddleware, config=security_config)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 오류 처리 핸들러 등록
app.add_exception_handler(HTTPException, api_error_handler.create_http_exception_handler())
app.add_exception_handler(Exception, api_error_handler.create_general_exception_handler())

# 전역 변수
voice_api: Optional[VoiceProcessingAPI] = None
logger = get_logger(__name__)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 초기화"""
    global voice_api
    try:
        logger.info("음성 처리 API 서버 시작 중...")
        
        # TTS 설정 (환경변수에서 읽기)
        tts_provider = os.getenv('TTS_PROVIDER', 'openai')
        tts_config = {}
        
        # OpenAI TTS 설정
        if tts_provider == 'openai':
            tts_config = {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('TTS_MODEL', 'tts-1'),
                'voice': os.getenv('TTS_VOICE', 'alloy'),
                'speed': float(os.getenv('TTS_SPEED', '1.0')),
                'response_format': os.getenv('TTS_FORMAT', 'wav')
            }
        
        voice_api = VoiceProcessingAPI(
            tts_provider=tts_provider,
            tts_config=tts_config
        )
        logger.info(f"음성 처리 API 서버 시작 완료 (TTS: {tts_provider})")
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 정리"""
    global voice_api
    if voice_api:
        voice_api.cleanup_expired_files()
    logger.info("음성 처리 API 서버 종료")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Voice Kiosk API Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    tts_info = {}
    if voice_api:
        try:
            tts_info = voice_api.response_builder.get_tts_provider_info()
        except Exception as e:
            tts_info = {"error": str(e)}
    
    return {
        "status": "healthy",
        "api_initialized": voice_api is not None,
        "tts_provider": tts_info
    }


@app.post("/api/voice/process", response_model=ServerResponse)
async def process_voice(
    request: Request,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    음성 파일 처리 엔드포인트
    
    Args:
        request: FastAPI 요청 객체
        audio_file: 업로드된 음성 파일 (WAV 형식)
        session_id: 세션 ID (선택사항)
        
    Returns:
        ServerResponse: 처리 결과
    """
    temp_file_path = None
    request_id = str(uuid.uuid4())
    monitor = get_monitor()
    
    # 클라이언트 IP 추출
    client_ip = request.client.host
    if hasattr(request.state, 'client_ip'):
        client_ip = request.state.client_ip
    
    # 모니터링 시작 (Requirements: 6.1)
    monitor.start_request(request_id, client_ip, audio_file.size)
    
    try:
        if not voice_api:
            raise HTTPException(status_code=500, detail="음성 처리 API가 초기화되지 않았습니다")
        
        # 기본 파일 검증 (보안 미들웨어 사용)
        validate_file_upload(audio_file.filename, audio_file.size)
        
        # 임시 파일로 저장
        temp_file_path = _save_uploaded_file(audio_file)
        
        # 파일 내용 검증 (실제 파일 타입 확인)
        validate_file_upload(audio_file.filename, audio_file.size, temp_file_path)
        
        # 처리 상태 업데이트
        monitor.update_processing_status(request_id)
        
        # 음성 처리 시작 시간 기록
        processing_start = time.time()
        
        # 음성 처리
        response = voice_api.process_audio_request(temp_file_path, session_id)
        
        # 처리 시간 계산 (Requirements: 6.2)
        processing_time = time.time() - processing_start
        
        # 응답 크기 계산
        response_size = len(str(response.to_json()).encode('utf-8'))
        
        # 모니터링 완료 (Requirements: 6.4)
        monitor.complete_request(request_id, processing_time, response_size)
        
        # 백그라운드에서 임시 파일 삭제
        background_tasks.add_task(_cleanup_temp_file, temp_file_path)
        
        return response
        
    except HTTPException as http_exc:
        # HTTP 예외 모니터링 (Requirements: 6.3)
        monitor.log_error(request_id, f"HTTP {http_exc.status_code}: {http_exc.detail}", "HTTP_ERROR")
        
        if temp_file_path and os.path.exists(temp_file_path):
            background_tasks.add_task(_cleanup_temp_file, temp_file_path)
        raise
        
    except Exception as e:
        # 일반 예외 모니터링 (Requirements: 6.3)
        monitor.log_error(request_id, str(e), type(e).__name__)
        
        if temp_file_path and os.path.exists(temp_file_path):
            background_tasks.add_task(_cleanup_temp_file, temp_file_path)
        
        # 오류 처리기를 통해 ServerResponse 생성
        error_response = handle_api_error(
            exception=e,
            request=request,
            session_id=session_id,
            context={
                'endpoint': '/api/voice/process',
                'file_name': audio_file.filename,
                'file_size': audio_file.size,
                'request_id': request_id
            }
        )
        
        return error_response


@app.get("/api/voice/tts/{file_id}")
async def get_tts_file(file_id: str):
    """
    TTS 음성 파일 다운로드 엔드포인트
    
    Args:
        file_id: TTS 파일 ID
        
    Returns:
        FileResponse: 음성 파일
    """
    if not voice_api:
        raise HTTPException(status_code=500, detail="음성 처리 API가 초기화되지 않았습니다")
    
    file_path = voice_api.get_tts_file(file_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="TTS 파일을 찾을 수 없습니다")
    
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=f"tts_{file_id}.wav"
    )


@app.get("/api/tts/providers")
async def get_tts_providers():
    """
    사용 가능한 TTS 제공자 목록 반환
    
    Returns:
        TTS 제공자 목록
    """
    if not voice_api:
        raise HTTPException(status_code=500, detail="음성 처리 API가 초기화되지 않았습니다")
    
    try:
        from ..audio.tts_manager import TTSManager
        available_providers = TTSManager.AVAILABLE_PROVIDERS.keys()
        current_provider = voice_api.response_builder.get_tts_provider_info()
        
        return {
            "available_providers": list(available_providers),
            "current_provider": current_provider
        }
    except Exception as e:
        logger.error(f"TTS 제공자 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 제공자 정보 조회 실패: {str(e)}")


@app.post("/api/tts/switch")
async def switch_tts_provider(request: dict):
    """
    TTS 제공자 교체
    
    Args:
        request: 요청 데이터
            - provider: 새로운 제공자 이름
            - config: 제공자 설정 (선택사항)
    
    Returns:
        교체 결과
    """
    if not voice_api:
        raise HTTPException(status_code=500, detail="음성 처리 API가 초기화되지 않았습니다")
    
    provider_name = request.get('provider')
    provider_config = request.get('config', {})
    
    if not provider_name:
        raise HTTPException(status_code=400, detail="제공자 이름이 필요합니다")
    
    try:
        voice_api.response_builder.switch_tts_provider(provider_name, provider_config)
        new_provider_info = voice_api.response_builder.get_tts_provider_info()
        
        logger.info(f"TTS 제공자 교체 완료: {provider_name}")
        return {
            "success": True,
            "message": f"TTS 제공자가 {provider_name}로 교체되었습니다",
            "provider_info": new_provider_info
        }
    except Exception as e:
        logger.error(f"TTS 제공자 교체 실패: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 제공자 교체 실패: {str(e)}")


@app.get("/api/errors/stats")
async def get_error_statistics():
    """
    오류 통계 조회 엔드포인트
    
    Returns:
        오류 통계 정보
    """
    try:
        stats = api_error_handler.get_error_stats()
        return stats
    except Exception as e:
        logger.error(f"오류 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"오류 통계 조회 실패: {str(e)}")


@app.post("/api/errors/clear")
async def clear_error_statistics():
    """
    오류 통계 초기화 엔드포인트
    
    Returns:
        초기화 결과
    """
    try:
        api_error_handler.error_stats.clear()
        logger.info("오류 통계 초기화 완료")
        return {
            "success": True,
            "message": "오류 통계가 초기화되었습니다",
            "cleared_at": api_error_handler.get_error_stats()['generated_at']
        }
    except Exception as e:
        logger.error(f"오류 통계 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"오류 통계 초기화 실패: {str(e)}")


@app.get("/api/system/status")
async def get_system_status():
    """
    시스템 상태 조회 엔드포인트
    
    Returns:
        시스템 상태 정보
    """
    try:
        # 기본 상태 정보
        status_info = {
            "api_initialized": voice_api is not None,
            "server_status": "running",
            "error_stats": api_error_handler.get_error_stats(),
            "security_stats": get_security_stats()
        }
        
        # TTS 제공자 정보
        if voice_api:
            try:
                status_info["tts_provider"] = voice_api.response_builder.get_tts_provider_info()
            except Exception as e:
                status_info["tts_provider"] = {"error": str(e)}
        
        # 파이프라인 상태 정보
        if voice_api and voice_api.pipeline:
            try:
                status_info["pipeline_status"] = {
                    "session_active": voice_api.pipeline.current_session_id is not None,
                    "current_session": voice_api.pipeline.current_session_id
                }
            except Exception as e:
                status_info["pipeline_status"] = {"error": str(e)}
        
        return status_info
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시스템 상태 조회 실패: {str(e)}")


@app.get("/api/security/stats")
async def get_security_statistics():
    """
    보안 통계 조회 엔드포인트
    
    Returns:
        보안 통계 정보
    """
    try:
        stats = get_security_stats()
        return {
            "success": True,
            "data": stats,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"보안 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보안 통계 조회 실패: {str(e)}")


@app.post("/api/security/clear-rate-limit")
async def clear_security_data():
    """
    보안 데이터 초기화 엔드포인트 (Rate limit 데이터 등)
    
    Returns:
        초기화 결과
    """
    try:
        clear_rate_limit_data()
        logger.info("보안 데이터 초기화 완료")
        return {
            "success": True,
            "message": "보안 데이터가 초기화되었습니다",
            "cleared_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"보안 데이터 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보안 데이터 초기화 실패: {str(e)}")


@app.get("/api/security/config")
async def get_security_config():
    """
    보안 설정 조회 엔드포인트
    
    Returns:
        현재 보안 설정 정보
    """
    try:
        return {
            "success": True,
            "config": {
                "max_file_size_mb": security_config.max_file_size / (1024 * 1024),
                "allowed_file_types": security_config.allowed_file_types,
                "allowed_extensions": security_config.allowed_extensions,
                "force_https": security_config.force_https,
                "rate_limit": {
                    "max_requests": security_config.rate_limit.max_requests,
                    "time_window_seconds": security_config.rate_limit.time_window,
                    "block_duration_seconds": security_config.rate_limit.block_duration
                },
                "trusted_proxies": security_config.trusted_proxies
            }
        }
    except Exception as e:
        logger.error(f"보안 설정 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"보안 설정 조회 실패: {str(e)}")


@app.get("/api/optimization/stats")
async def get_optimization_stats():
    """
    최적화 통계 조회 엔드포인트
    
    Returns:
        최적화 통계 정보
    """
    try:
        from .optimization import get_optimization_manager
        
        optimization_manager = get_optimization_manager()
        stats = optimization_manager.get_optimization_stats()
        
        return {
            "success": True,
            "data": stats,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"최적화 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"최적화 통계 조회 실패: {str(e)}")


@app.post("/api/optimization/clear-cache")
async def clear_optimization_cache():
    """
    최적화 캐시 초기화 엔드포인트
    
    Returns:
        초기화 결과
    """
    try:
        from .optimization import get_optimization_manager
        
        optimization_manager = get_optimization_manager()
        optimization_manager.clear_cache()
        
        logger.info("최적화 캐시 초기화 완료")
        return {
            "success": True,
            "message": "최적화 캐시가 초기화되었습니다",
            "cleared_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"최적화 캐시 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"최적화 캐시 초기화 실패: {str(e)}")


@app.post("/api/optimization/compress-file")
async def compress_audio_file(audio_file: UploadFile = File(...)):
    """
    음성 파일 압축 테스트 엔드포인트
    
    Args:
        audio_file: 압축할 음성 파일
        
    Returns:
        압축 결과 정보
    """
    temp_file_path = None
    try:
        from .optimization import get_optimization_manager
        
        if not voice_api:
            raise HTTPException(status_code=500, detail="음성 처리 API가 초기화되지 않았습니다")
        
        # 기본 파일 검증
        validate_file_upload(audio_file.filename, audio_file.size)
        
        # 임시 파일로 저장
        temp_file_path = _save_uploaded_file(audio_file)
        
        # 최적화 관리자를 통한 파일 압축
        optimization_manager = get_optimization_manager()
        optimized_path, optimization_info = optimization_manager.optimize_audio_file(temp_file_path)
        
        return {
            "success": True,
            "original_file": audio_file.filename,
            "optimization_info": optimization_info,
            "message": "파일 압축이 완료되었습니다"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 압축 실패: {e}")
        raise HTTPException(status_code=500, detail=f"파일 압축 실패: {str(e)}")
    finally:
        # 임시 파일 정리
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {e}")


@app.get("/api/payment/progress/{order_id}")
async def get_payment_progress(order_id: str):
    """
    결제 진행 상황 조회 엔드포인트
    
    Args:
        order_id: 주문 ID
        
    Returns:
        결제 진행 상황 정보
    """
    try:
        if not voice_api:
            raise HTTPException(status_code=500, detail="음성 처리 API가 초기화되지 않았습니다")
        
        # DialogueManager에서 결제 상태 확인
        dialogue_manager = voice_api.pipeline.dialogue_manager
        payment_status = dialogue_manager.get_order_payment_status(order_id)
        
        # 결제 중인 경우 진행 단계 반환
        if payment_status == "processing":
            return {
                "order_id": order_id,
                "status": "processing", 
                "progress": {
                    "steps": [
                        "결제를 진행합니다...",
                        "카드를 삽입해 주세요...",
                        "결제 승인 중...",
                        "결제가 완료되었습니다!"
                    ],
                    "step_delays": [1000, 1000, 1000, 0],
                    "current_step": 0
                }
            }
        elif payment_status == "completed":
            return {
                "order_id": order_id,
                "status": "completed",
                "message": "결제가 완료되었습니다."
            }
        elif payment_status == "pending":
            return {
                "order_id": order_id,
                "status": "pending",
                "message": "결제 대기 중입니다."
            }
        else:
            return {
                "order_id": order_id,
                "status": "not_found",
                "message": "해당 주문을 찾을 수 없습니다."
            }
            
    except Exception as e:
        logger.error(f"결제 진행 상황 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"결제 진행 상황 조회 실패: {str(e)}")


@app.get("/api/monitoring/stats")
async def get_monitoring_stats():
    """
    모니터링 통계 조회 엔드포인트
    
    Returns:
        모니터링 통계 정보
    """
    try:
        monitor = get_monitor()
        current_metrics = monitor.get_current_metrics()
        performance_report = monitor.get_performance_report()
        
        return {
            "success": True,
            "current_metrics": current_metrics.to_dict(),
            "performance_report": performance_report,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모니터링 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모니터링 통계 조회 실패: {str(e)}")


@app.get("/api/monitoring/alerts")
async def get_monitoring_alerts():
    """
    모니터링 알림 조회 엔드포인트
    
    Returns:
        현재 알림 상태
    """
    try:
        monitor = get_monitor()
        alert_manager = get_alert_manager()
        
        alerts = alert_manager.check_alerts(monitor)
        current_metrics = monitor.get_current_metrics()
        
        return {
            "success": True,
            "alerts": alerts,
            "alert_count": len(alerts),
            "current_metrics": {
                "active_requests": current_metrics.active_requests,
                "total_errors": current_metrics.error_count,
                "avg_response_time": current_metrics.avg_response_time
            },
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모니터링 알림 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모니터링 알림 조회 실패: {str(e)}")


@app.post("/api/monitoring/export")
async def export_monitoring_logs(request: dict):
    """
    모니터링 로그 내보내기 엔드포인트
    
    Args:
        request: 요청 데이터
            - output_file: 출력 파일 경로 (선택사항)
    
    Returns:
        내보내기 결과
    """
    try:
        monitor = get_monitor()
        
        # 출력 파일 경로 설정
        output_file = request.get('output_file')
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"logs/monitoring_export_{timestamp}.json"
        
        # 로그 내보내기
        monitor.export_logs(output_file)
        
        return {
            "success": True,
            "message": "모니터링 로그가 성공적으로 내보내졌습니다",
            "output_file": output_file,
            "exported_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모니터링 로그 내보내기 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모니터링 로그 내보내기 실패: {str(e)}")


@app.get("/api/monitoring/performance")
async def get_performance_metrics():
    """
    성능 메트릭 조회 엔드포인트
    
    Returns:
        상세 성능 메트릭
    """
    try:
        monitor = get_monitor()
        performance_report = monitor.get_performance_report()
        
        # 추가 성능 분석
        with monitor.lock:
            recent_completed = list(monitor.completed_requests)[-100:]
            recent_errors = list(monitor.error_requests)[-50:]
            
            # 시간대별 요청 분포 (최근 24시간)
            current_time = time.time()
            hourly_requests = {}
            
            for req in recent_completed:
                hour_key = int((current_time - req.start_time) // 3600)  # 몇 시간 전
                if hour_key < 24:  # 24시간 이내만
                    hourly_requests[hour_key] = hourly_requests.get(hour_key, 0) + 1
            
            # 오류율 계산
            total_recent = len(recent_completed) + len(recent_errors)
            error_rate = (len(recent_errors) / total_recent * 100) if total_recent > 0 else 0
        
        return {
            "success": True,
            "performance_report": performance_report,
            "additional_metrics": {
                "hourly_request_distribution": hourly_requests,
                "error_rate_percentage": round(error_rate, 2),
                "total_recent_requests": total_recent
            },
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"성능 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"성능 메트릭 조회 실패: {str(e)}")


def _save_uploaded_file(upload_file: UploadFile) -> str:
    """
    업로드된 파일을 임시 디렉토리에 저장
    
    Args:
        upload_file: 업로드된 파일
        
    Returns:
        저장된 파일 경로
    """
    # 임시 파일 생성
    temp_dir = Path(tempfile.gettempdir()) / "voice_kiosk_uploads"
    temp_dir.mkdir(exist_ok=True)
    
    file_id = str(uuid.uuid4())
    temp_file_path = temp_dir / f"upload_{file_id}.wav"
    
    # 파일 저장
    with open(temp_file_path, "wb") as temp_file:
        content = upload_file.file.read()
        temp_file.write(content)
    
    logger.info(f"업로드 파일 저장: {temp_file_path}")
    return str(temp_file_path)


def _cleanup_temp_file(file_path: str):
    """
    임시 파일 삭제
    
    Args:
        file_path: 삭제할 파일 경로
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"임시 파일 삭제: {file_path}")
    except Exception as e:
        logger.error(f"임시 파일 삭제 실패: {e}")


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """
    서버 실행
    
    Args:
        host: 호스트 주소
        port: 포트 번호
        debug: 디버그 모드
    """
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    run_server(debug=True)