# 음성 처리 API 서버

이 모듈은 기존 VoiceKioskPipeline과 연동하여 HTTP API 서비스를 제공하는 FastAPI 기반 서버입니다.

## 주요 기능

- ~~**POST /api/voice/process**: 음성 파일 업로드 및 처리~~ (제거됨)
- **GET /api/voice/tts/{file_id}**: TTS 음성 파일 다운로드
- **GET /api/tts/providers**: TTS 제공자 정보 조회
- **POST /api/tts/switch**: TTS 제공자 교체
- **GET /health**: 서버 상태 및 TTS 제공자 정보 확인

> **⚠️ 중요**: 음성 파일 업로드 엔드포인트는 제거되었습니다. 
> 음성 처리는 로컬 파일 기반으로만 지원됩니다. (`src/main.py`의 `process_audio_input` 사용)

## TTS 기능 개선

### 지원하는 TTS 제공자
- **OpenAI TTS**: 고품질 음성 합성 (기본)
- 폴백 시스템: TTS 실패 시 더미 파일 생성

### OpenAI TTS 설정
- **모델**: `tts-1` (기본), `tts-1-hd` (고품질)
- **음성**: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **속도**: 0.25 ~ 4.0 (기본: 1.0)
- **형식**: wav, mp3, opus, aac, flac, pcm

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install fastapi uvicorn python-multipart
```

또는 프로젝트 루트에서:

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

#### 필수 환경 변수
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

#### 선택적 TTS 환경 변수
```bash
export TTS_PROVIDER="openai"        # TTS 제공자 (기본: openai)
export TTS_MODEL="tts-1"            # OpenAI TTS 모델 (기본: tts-1)
export TTS_VOICE="alloy"            # OpenAI TTS 음성 (기본: alloy)
export TTS_SPEED="1.0"              # OpenAI TTS 속도 (기본: 1.0)
export TTS_FORMAT="wav"             # OpenAI TTS 형식 (기본: wav)
```

### 3. 서버 실행

#### 개발 모드 (디버그 활성화)
```bash
python -m src.api.cli --debug
```

#### 운영 모드
```bash
python -m src.api.cli --host 0.0.0.0 --port 8000
```

#### 옵션
- `--host`: 서버 호스트 주소 (기본값: 0.0.0.0)
- `--port`: 서버 포트 번호 (기본값: 8000)
- `--debug`: 디버그 모드 활성화
- `--log-level`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)

### 4. 서버 테스트

#### API 서버 테스트
```bash
python -m src.api.test_server
```

특정 음성 파일로 테스트:
```bash
python -m src.api.test_server --audio-file your_audio.wav
```

#### TTS 기능 테스트
```bash
# 모든 TTS 테스트 실행
python src/api/cli_tts_test.py --test all

# 특정 테스트만 실행
python src/api/cli_tts_test.py --test direct    # OpenAI TTS 직접 테스트
python src/api/cli_tts_test.py --test builder   # ResponseBuilder 테스트
python src/api/cli_tts_test.py --test switch    # 제공자 교체 테스트
python src/api/cli_tts_test.py --test voices    # 다양한 음성 테스트
```

#### 단위 테스트
```bash
python src/api/test_tts_integration.py
```

## API 사용법

### ~~음성 파일 처리~~ (제거됨)

> **⚠️ 음성 파일 업로드 엔드포인트는 제거되었습니다.**
> 
> 음성 처리는 다음 방법으로 사용하세요:
> ```python
> from src.main import VoiceKioskPipeline
> 
> pipeline = VoiceKioskPipeline()
> pipeline.initialize_system()
> response = pipeline.process_audio_input("your_audio.wav")
> ```

### TTS 파일 다운로드

```bash
curl -X GET "http://localhost:8000/api/voice/tts/abc123-def456" \
  --output response.wav
```

### TTS 제공자 정보 조회

```bash
curl -X GET "http://localhost:8000/api/tts/providers"
```

### TTS 제공자 교체

```bash
curl -X POST "http://localhost:8000/api/tts/switch" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "config": {
      "api_key": "your_api_key",
      "model": "tts-1-hd",
      "voice": "nova",
      "speed": 1.2
    }
  }'
```

## 아키텍처

```
클라이언트 → FastAPI 서버 → VoiceProcessingAPI → VoiceKioskPipeline
                ↓
            TTS 파일 생성 및 캐싱
```

### 주요 컴포넌트

1. **server.py**: FastAPI 애플리케이션 및 엔드포인트
2. **voice_processing_api.py**: VoiceKioskPipeline과의 연동 로직
3. **cli.py**: 서버 실행을 위한 CLI 인터페이스
4. **test_server.py**: API 서버 테스트 스크립트

## 보안 고려사항

- ~~파일 업로드 크기 제한: 최대 10MB~~ (업로드 기능 제거됨)
- ~~지원 파일 형식: WAV만 허용~~ (업로드 기능 제거됨)
- TTS 파일 자동 만료: 1시간 후 삭제
- CORS 설정: 개발 환경에서는 모든 도메인 허용 (운영 환경에서는 제한 필요)

## 로깅

서버는 다음과 같은 로그를 생성합니다:

- 요청/응답 로그
- 처리 시간 측정
- 오류 및 예외 상황
- TTS 파일 생성/삭제

로그는 프로젝트의 로깅 설정을 따릅니다.

## TTS 비용 관리

OpenAI TTS API는 사용량에 따라 과금됩니다:
- **tts-1**: $15.00 / 1M characters
- **tts-1-hd**: $30.00 / 1M characters

비용 추정 기능을 통해 사전에 비용을 확인할 수 있습니다.

## 문제 해결

### 서버가 시작되지 않는 경우

1. 포트가 이미 사용 중인지 확인
2. VoiceKioskPipeline 초기화 오류 확인
3. 환경 변수 및 API 키 설정 확인

### ~~음성 처리가 실패하는 경우~~ (업로드 기능 제거됨)

> 음성 처리는 이제 로컬 파일 기반으로만 지원됩니다.
> `src/main.py`의 `VoiceKioskPipeline.process_audio_input()` 메서드를 사용하세요.

### TTS 관련 문제

#### TTS 초기화 실패
1. `OPENAI_API_KEY` 환경변수 확인
2. API 키 유효성 확인
3. 네트워크 연결 상태 확인

#### TTS 변환 실패
1. 텍스트 길이 확인 (최대 4096자)
2. 음성 설정 확인 (지원하는 음성인지)
3. 속도 설정 확인 (0.25-4.0 범위)

#### 폴백 모드 동작
TTS 제공자 초기화나 변환이 실패하면 자동으로 폴백 모드(더미 파일 생성)로 동작합니다.

### TTS 파일을 찾을 수 없는 경우

1. 파일 ID가 올바른지 확인
2. 파일이 만료되지 않았는지 확인 (1시간 제한)
3. 서버 재시작 시 캐시가 초기화됨

## 개발 가이드

### 새로운 엔드포인트 추가

1. `server.py`에 새로운 라우트 함수 추가
2. 필요한 경우 `voice_processing_api.py`에 로직 추가
3. `test_server.py`에 테스트 케이스 추가

### 응답 모델 수정

1. `src/models/communication_models.py`에서 모델 수정
2. API 응답 생성 로직 업데이트
3. 클라이언트 호환성 확인

## 성능 최적화

- TTS 파일 캐싱으로 중복 생성 방지
- 백그라운드 태스크로 임시 파일 정리
- 비동기 처리로 동시 요청 지원
- 파일 업로드 스트리밍 처리