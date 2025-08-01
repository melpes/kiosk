# Design Document

## Overview

이 설계는 키오스크 디바이스(클라이언트)와 음성 처리 서버 간의 실시간 통신 시스템을 정의합니다. 클라이언트에서 VAD를 통해 생성된 음성 파일을 서버로 전송하고, 서버의 기존 음성 처리 파이프라인(음성 인식 → LLM → TTS)을 통해 처리된 결과를 다시 클라이언트로 반환하는 구조입니다.

## Architecture

### 시스템 구성 요소

```
[키오스크 클라이언트] ←→ [통신 인터페이스] ←→ [음성 처리 서버]
     ↓                                           ↓
[VAD + UI 갱신]                          [기존 파이프라인]
                                         (Whisper → LLM → TTS)
```

### 통신 흐름

1. **음성 입력 단계**
   - 클라이언트: VAD가 음성을 감지하여 WAV 파일 생성
   - 클라이언트: HTTP POST로 음성 파일을 서버에 전송

2. **서버 처리 단계**
   - 서버: 기존 VoiceKioskPipeline.process_audio_input() 활용
   - 서버: 음성 인식 → 의도 파악 → 대화 처리 → TTS 생성

3. **응답 반환 단계**
   - 서버: 구조화된 JSON 응답 생성 (음성 파일 + 메타데이터)
   - 클라이언트: 응답 수신 후 UI 갱신 및 음성 재생

## Components and Interfaces

### 1. 클라이언트 컴포넌트

#### VoiceClient
```python
class VoiceClient:
    def __init__(self, server_url: str, timeout: int = 30)
    def send_audio_file(self, audio_file_path: str) -> ServerResponse
    def handle_response(self, response: ServerResponse) -> None
```

#### KioskUIManager
```python
class KioskUIManager:
    def update_order_display(self, order_data: OrderData) -> None
    def show_menu_options(self, options: List[MenuOption]) -> None
    def display_payment_info(self, payment_data: PaymentData) -> None
    def play_tts_audio(self, audio_file_path: str) -> None
```

### 2. 서버 컴포넌트

#### VoiceProcessingAPI
```python
class VoiceProcessingAPI:
    def __init__(self, pipeline: VoiceKioskPipeline)
    def process_audio_request(self, audio_file: UploadFile) -> ServerResponse
    def generate_tts_response(self, text: str) -> str  # 음성 파일 경로 반환
```

#### ResponseBuilder
```python
class ResponseBuilder:
    def build_response(self, dialogue_response: DialogueResponse, 
                      tts_file_path: str, 
                      order_state: Optional[Order]) -> ServerResponse
```

### 3. 통신 인터페이스

#### HTTP API 엔드포인트
- `POST /api/voice/process` - 음성 파일 처리 요청
- `GET /api/voice/tts/{file_id}` - TTS 음성 파일 다운로드

## Data Models

### 클라이언트-서버 통신 모델

```python
@dataclass
class ServerResponse:
    """서버 응답 데이터"""
    success: bool
    message: str
    tts_audio_url: Optional[str]  # TTS 음성 파일 URL
    order_data: Optional[OrderData]
    ui_actions: List[UIAction]
    error_info: Optional[ErrorInfo]
    processing_time: float

@dataclass
class OrderData:
    """주문 상태 데이터"""
    order_id: Optional[str]
    items: List[MenuItem]
    total_amount: float
    status: str
    requires_confirmation: bool

@dataclass
class UIAction:
    """UI 액션 정보"""
    action_type: str  # "show_menu", "show_payment", "show_options"
    data: Dict[str, Any]

@dataclass
class MenuOption:
    """메뉴 선택 옵션"""
    option_id: str
    display_text: str
    category: str
    price: Optional[float]

@dataclass
class PaymentData:
    """결제 정보"""
    total_amount: float
    payment_methods: List[str]
    order_summary: List[MenuItem]

@dataclass
class ErrorInfo:
    """오류 정보"""
    error_code: str
    error_message: str
    recovery_actions: List[str]
```

### 기존 모델 활용

서버 내부에서는 기존 프로젝트의 모델들을 그대로 활용:
- `Intent`, `DialogueResponse` (conversation_models.py)
- `Order`, `MenuItem`, `OrderSummary` (order_models.py)
- `TextResponse`, `FormattedResponse` (response_models.py)

## Error Handling

### 오류 유형 및 처리

1. **네트워크 오류**
   - 연결 실패: 재시도 로직 (최대 3회)
   - 타임아웃: 30초 후 오류 응답
   - 응답 형식 오류: 기본 오류 메시지 표시

2. **서버 처리 오류**
   - 음성 인식 실패: 재입력 요청
   - LLM 처리 오류: 기본 응답 제공
   - TTS 생성 실패: 텍스트만 표시

3. **파일 처리 오류**
   - 파일 업로드 실패: 재전송 시도
   - 파일 형식 오류: 지원 형식 안내
   - 파일 크기 초과: 압축 또는 분할 처리

### 오류 복구 전략

```python
class ErrorRecoveryManager:
    def handle_network_error(self, error: NetworkError) -> RecoveryAction
    def handle_server_error(self, error: ServerError) -> RecoveryAction
    def handle_file_error(self, error: FileError) -> RecoveryAction
```

## Testing Strategy

### 단위 테스트
- VoiceClient의 HTTP 통신 테스트
- ResponseBuilder의 응답 생성 테스트
- KioskUIManager의 UI 갱신 테스트

### 통합 테스트
- 클라이언트-서버 간 전체 통신 플로우 테스트
- 다양한 음성 파일 형식 처리 테스트
- 오류 상황별 복구 시나리오 테스트

### 성능 테스트
- 음성 파일 전송 속도 측정
- 서버 응답 시간 측정 (목표: 3초 이내)
- 동시 요청 처리 능력 테스트

### 실제 환경 테스트
- 다양한 네트워크 환경에서의 안정성 테스트
- 키오스크 하드웨어에서의 실제 동작 테스트
- 사용자 시나리오 기반 E2E 테스트

## Implementation Notes

### 기존 코드 활용 방안

1. **서버 측 구현**
   - 기존 `VoiceKioskPipeline` 클래스를 그대로 활용
   - `process_audio_input()` 메서드를 HTTP API로 래핑
   - 기존 모델들(`Intent`, `Order` 등)을 JSON 직렬화하여 전송

2. **TTS 처리**
   - 서버에서 TTS 생성 후 임시 파일로 저장
   - 파일 URL을 응답에 포함하여 클라이언트가 다운로드
   - 또는 Base64 인코딩하여 JSON에 직접 포함

3. **세션 관리**
   - 기존 `DialogueManager`의 세션 관리 기능 활용
   - 클라이언트에서 세션 ID를 유지하여 연속 대화 지원

### 보안 고려사항

- HTTPS 통신 강제
- 파일 업로드 크기 제한 (최대 10MB)
- 요청 빈도 제한 (Rate Limiting)
- 임시 파일 자동 정리 (TTL: 1시간)