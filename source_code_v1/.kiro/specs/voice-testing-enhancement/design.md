# Design Document

## Overview

이 설계는 현재 음성 기반 키오스크 AI 주문 시스템에 두 가지 핵심 기능을 추가합니다:

1. **자동화된 테스트케이스 생성 및 결과 분석 시스템**: 다양한 텍스트 입력에 대한 시스템 응답을 체계적으로 테스트하고 분석하는 기능
2. **실시간 마이크 입력 통합**: reference/input_as_mic.py의 VAD 기반 마이크 입력 기능을 메인 시스템에 통합

이 설계는 기존 VoiceKioskPipeline 클래스를 확장하고, 새로운 테스트 및 마이크 입력 모듈을 추가하여 시스템의 기능을 향상시킵니다.

## Architecture

### 시스템 구조 확장

```
기존 VoiceKioskPipeline
├── AudioProcessor
├── SpeechRecognizer  
├── IntentRecognizer
├── DialogueManager
├── OrderManager
└── TextResponseSystem

새로 추가되는 구조:
├── TestCaseManager (새로 추가)
│   ├── TestCaseGenerator
│   ├── TestRunner
│   └── ResultAnalyzer
├── MicrophoneInputManager (새로 추가)
│   ├── VADProcessor
│   ├── AudioRecorder
│   └── RealTimeProcessor
└── ReportGenerator (새로 추가)
    ├── TextReportGenerator
    └── MarkdownReportGenerator
```

### 데이터 흐름

#### 테스트케이스 실행 흐름
1. TestCaseGenerator → 테스트케이스 생성
2. TestRunner → 각 테스트케이스 실행
3. VoiceKioskPipeline.process_text_input() → 기존 파이프라인 활용
4. ResultAnalyzer → 결과 분석 및 통계 생성
5. ReportGenerator → 보고서 생성 (텍스트/마크다운)

#### 마이크 입력 처리 흐름
1. MicrophoneInputManager → 마이크 초기화 및 설정
2. VADProcessor → 음성 활동 감지
3. AudioRecorder → 음성 녹음 및 파일 생성
4. VoiceKioskPipeline.process_audio_input() → 기존 음성 처리 파이프라인 활용
5. RealTimeProcessor → 실시간 상태 표시 및 피드백

## Components and Interfaces

### 1. TestCaseManager

```python
class TestCaseManager:
    """테스트케이스 관리 및 실행을 담당하는 메인 클래스"""
    
    def __init__(self, pipeline: VoiceKioskPipeline):
        self.pipeline = pipeline
        self.generator = TestCaseGenerator()
        self.runner = TestRunner(pipeline)
        self.analyzer = ResultAnalyzer()
        self.report_generator = ReportGenerator()
    
    def generate_test_cases(self) -> List[TestCase]
    def run_all_tests(self, test_cases: List[TestCase]) -> TestResults
    def analyze_results(self, results: TestResults) -> TestAnalysis
    def generate_reports(self, analysis: TestAnalysis, output_dir: str)
```

### 2. TestCaseGenerator

```python
@dataclass
class TestCase:
    """개별 테스트케이스 데이터 모델"""
    id: str
    input_text: str
    expected_intent: Optional[IntentType]
    category: str  # "slang", "informal", "complex", "normal"
    description: str
    tags: List[str]

class TestCaseGenerator:
    """맥도날드 키오스크 환경에 특화된 테스트케이스 생성"""
    
    def generate_mcdonald_test_cases(self) -> List[TestCase]
    def generate_slang_cases(self) -> List[TestCase]  # "상스치콤", "베토디" 등
    def generate_informal_cases(self) -> List[TestCase]  # 반말 케이스
    def generate_complex_intent_cases(self) -> List[TestCase]  # 복합 의도
    def generate_edge_cases(self) -> List[TestCase]  # 엣지 케이스
```

### 3. TestRunner

```python
@dataclass
class TestResult:
    """개별 테스트 결과"""
    test_case: TestCase
    system_response: str
    detected_intent: IntentType
    processing_time: float
    success: bool
    error_message: Optional[str]
    confidence_score: float

class TestRunner:
    """테스트케이스 실행 엔진"""
    
    def __init__(self, pipeline: VoiceKioskPipeline):
        self.pipeline = pipeline
    
    def run_single_test(self, test_case: TestCase) -> TestResult
    def run_batch_tests(self, test_cases: List[TestCase]) -> List[TestResult]
    def setup_test_session(self) -> str
    def cleanup_test_session(self, session_id: str)
```

### 4. MicrophoneInputManager

```python
@dataclass
class MicrophoneConfig:
    """마이크 입력 설정"""
    sample_rate: int = 16000
    frame_duration: float = 0.5
    max_silence_duration_start: float = 5.0
    max_silence_duration_end: float = 3.0
    min_record_duration: float = 1.0
    vad_threshold: float = 0.2
    output_filename: str = "mic_input.wav"

class MicrophoneInputManager:
    """실시간 마이크 입력 관리"""
    
    def __init__(self, config: MicrophoneConfig, pipeline: VoiceKioskPipeline):
        self.config = config
        self.pipeline = pipeline
        self.vad_processor = VADProcessor(config)
        self.audio_recorder = AudioRecorder(config)
        self.realtime_processor = RealTimeProcessor()
    
    def start_listening(self) -> str  # 녹음된 파일 경로 반환
    def stop_listening(self)
    def get_microphone_status(self) -> Dict[str, Any]
    def update_config(self, new_config: MicrophoneConfig)
```

### 5. VADProcessor

```python
class VADProcessor:
    """Voice Activity Detection 처리"""
    
    def __init__(self, config: MicrophoneConfig):
        self.config = config
        self.model = None
        self.utils = None
        self._load_vad_model()
    
    def _load_vad_model(self)  # Silero VAD 모델 로드
    def detect_speech(self, audio_tensor: torch.Tensor) -> bool
    def is_model_ready(self) -> bool
```

### 6. AudioRecorder

```python
class AudioRecorder:
    """오디오 녹음 및 파일 생성"""
    
    def __init__(self, config: MicrophoneConfig):
        self.config = config
        self.recorded_frames = []
        self.silence_buffer_start = deque()
        self.silence_buffer_end = deque()
        self.stream = None
    
    def start_recording(self)
    def stop_recording(self) -> str  # 저장된 파일 경로
    def add_audio_frame(self, audio_frame: np.ndarray, is_speech: bool)
    def save_recording(self) -> str
    def get_recording_info(self) -> Dict[str, Any]
```

### 7. ReportGenerator

```python
@dataclass
class TestAnalysis:
    """테스트 결과 분석 데이터"""
    total_tests: int
    success_rate: float
    average_processing_time: float
    intent_accuracy: Dict[str, float]
    category_performance: Dict[str, float]
    error_summary: Dict[str, int]
    detailed_results: List[TestResult]

class ReportGenerator:
    """테스트 결과 보고서 생성"""
    
    def generate_text_report(self, analysis: TestAnalysis, output_path: str)
    def generate_markdown_report(self, analysis: TestAnalysis, output_path: str)
    def generate_summary_report(self, analysis: TestAnalysis) -> str
    def _format_statistics(self, analysis: TestAnalysis) -> str
    def _format_error_details(self, analysis: TestAnalysis) -> str
```

## Data Models

### 확장된 데이터 모델

```python
# 기존 모델 확장
@dataclass
class ExtendedIntentResult:
    """확장된 의도 파악 결과"""
    type: IntentType
    confidence: float
    entities: Dict[str, Any]
    processing_time: float  # 새로 추가
    raw_text: str  # 새로 추가
    normalized_text: str  # 새로 추가

@dataclass
class MicrophoneStatus:
    """마이크 상태 정보"""
    is_listening: bool
    is_recording: bool
    current_volume_level: float
    recording_duration: float
    vad_status: str  # "waiting", "detecting", "recording", "processing"
    last_speech_detected: Optional[datetime]

@dataclass
class TestConfiguration:
    """테스트 설정"""
    include_slang: bool = True
    include_informal: bool = True
    include_complex: bool = True
    include_edge_cases: bool = True
    max_tests_per_category: int = 50
    output_directory: str = "test_results"
    generate_markdown: bool = True
    generate_text: bool = True
```

## Error Handling

### 테스트 시스템 오류 처리

1. **테스트케이스 생성 오류**
   - 메뉴 설정 파일 읽기 실패
   - 테스트케이스 템플릿 오류
   - 복구: 기본 테스트케이스 세트 사용

2. **테스트 실행 오류**
   - 개별 테스트 실패 시 다음 테스트 계속 진행
   - 파이프라인 오류 시 재시도 메커니즘
   - 타임아웃 처리

3. **결과 분석 오류**
   - 부분적 결과라도 분석 진행
   - 통계 계산 오류 시 기본값 사용

### 마이크 입력 오류 처리

1. **하드웨어 오류**
   - 마이크 장치 없음/접근 불가
   - 오디오 드라이버 문제
   - 복구: 텍스트 입력 모드로 전환

2. **VAD 모델 오류**
   - 모델 다운로드 실패
   - 모델 로딩 오류
   - 복구: 간단한 볼륨 기반 감지로 대체

3. **녹음 오류**
   - 디스크 공간 부족
   - 파일 저장 권한 문제
   - 복구: 임시 디렉토리 사용

## Testing Strategy

### 단위 테스트

1. **TestCaseGenerator 테스트**
   - 각 카테고리별 테스트케이스 생성 검증
   - 은어/반말 케이스 정확성 검증
   - 복합 의도 케이스 유효성 검증

2. **MicrophoneInputManager 테스트**
   - VAD 모델 로딩 테스트
   - 오디오 녹음 기능 테스트
   - 설정 변경 테스트

3. **ReportGenerator 테스트**
   - 보고서 포맷 검증
   - 통계 계산 정확성 검증
   - 파일 출력 테스트

### 통합 테스트

1. **전체 테스트 파이프라인**
   - 테스트케이스 생성 → 실행 → 분석 → 보고서 생성
   - 다양한 시나리오에서의 안정성 검증

2. **마이크 입력 통합**
   - 실제 마이크 입력 → 음성 처리 → 대화 처리
   - VAD 정확성 및 응답성 테스트

### 성능 테스트

1. **대량 테스트케이스 처리**
   - 100+ 테스트케이스 동시 실행
   - 메모리 사용량 모니터링
   - 처리 시간 측정

2. **실시간 마이크 입력**
   - 지연 시간 측정
   - CPU 사용률 모니터링
   - 장시간 사용 안정성

## Implementation Notes

### 기존 시스템과의 통합

1. **VoiceKioskPipeline 확장**
   - 기존 메서드는 수정하지 않고 새로운 메서드 추가
   - `run_test_mode()`, `run_microphone_mode()` 메서드 추가
   - 기존 `run_interactive_mode()`와 병행 사용 가능

2. **설정 시스템 활용**
   - 기존 ConfigManager를 확장하여 테스트 및 마이크 설정 추가
   - 환경 변수를 통한 설정 관리 유지

3. **로깅 시스템 통합**
   - 기존 로깅 시스템 활용
   - 테스트 및 마이크 입력 관련 로그 레벨 추가

### 파일 구조

```
src/
├── testing/                    # 새로 추가
│   ├── __init__.py
│   ├── test_case_manager.py
│   ├── test_case_generator.py
│   ├── test_runner.py
│   ├── result_analyzer.py
│   └── report_generator.py
├── microphone/                 # 새로 추가
│   ├── __init__.py
│   ├── microphone_manager.py
│   ├── vad_processor.py
│   ├── audio_recorder.py
│   └── realtime_processor.py
├── models/
│   ├── testing_models.py       # 새로 추가
│   └── microphone_models.py    # 새로 추가
└── main.py                     # 확장

test_results/                   # 새로 생성
├── test_cases/
├── reports/
└── audio_samples/
```

### 의존성 추가

```python
# requirements.txt에 추가될 패키지들
torch>=1.9.0                   # VAD 모델용
sounddevice>=0.4.0             # 마이크 입력용
scipy>=1.7.0                   # 오디오 처리용
numpy>=1.21.0                  # 기존에 있지만 버전 확인
```

### 성능 고려사항

1. **메모리 관리**
   - 대량 테스트 시 결과 데이터 스트리밍 처리
   - 오디오 버퍼 크기 최적화

2. **CPU 사용률**
   - VAD 모델 추론 최적화
   - 멀티스레딩을 통한 병렬 처리

3. **디스크 I/O**
   - 임시 오디오 파일 관리
   - 보고서 파일 비동기 쓰기