# Design Document

## Overview

식당 음성 기반 키오스크 AI 주문 시스템은 음성 전처리 → 음성인식 모델 → LLM → TTS의 파이프라인 구조로 설계됩니다. 시스템은 모듈화된 아키텍처를 통해 각 컴포넌트를 독립적으로 개발하고 테스트할 수 있도록 구성되며, 다중화자인식/구분 기술을 핵심으로 하여 노이즈가 있는 환경에서도 안정적인 서비스를 제공합니다.

## Architecture

### High-Level Architecture

```
[음성 입력] → [AudioProcessor] → [SpeechRecognizer] → [IntentRecognizer] → [DialogueManager] → [TTSGenerator] → [음성 출력]
                     ↓                    ↓                    ↓                    ↓
              [다중화자인식/구분]    [Whisper 파인튜닝]    [Tool Calling]      [주문 관리]
```

### System Components

1. **Audio Processing Layer**
   - 음성 전처리 및 다중화자인식/구분
   - 노이즈 제거 및 음성 품질 개선

2. **Speech Recognition Layer**
   - Whisper 기반 음성인식 모델
   - 식당 도메인 특화 파인튜닝

3. **Natural Language Processing Layer**
   - 의도 파악 및 대화 관리
   - OpenAI GPT-4o 기반 LLM 처리

4. **Order Management Layer**
   - 주문 상태 관리 및 메뉴 처리
   - 설정 기반 메뉴 관리

5. **Text-to-Speech Layer**
   - 응답 텍스트의 음성 변환
   - 자연스러운 음성 출력

## Components and Interfaces

### 1. AudioProcessor Class

```python
class AudioProcessor:
    def __init__(self, config: AudioConfig):
        self.speaker_separation_model = self._load_speaker_model()
        self.noise_reduction = NoiseReduction()
    
    def process_audio(self, audio_input: AudioData) -> ProcessedAudio:
        """다중화자인식/구분 및 노이즈 제거 수행"""
        separated_audio = self.speaker_separation_model.separate(audio_input)
        cleaned_audio = self.noise_reduction.reduce(separated_audio)
        return self._resample_to_16khz(cleaned_audio)
    
    def extract_features(self, audio: ProcessedAudio) -> AudioFeatures:
        """Whisper Feature Extractor를 사용한 특징 추출"""
        return self.feature_extractor.extract(audio)  # (80, 3000) 형태
```

### 2. SpeechRecognizer Class

```python
class SpeechRecognizer:
    def __init__(self, model_path: str):
        self.whisper_model = self._load_finetuned_model(model_path)
        self.tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-base")
    
    def recognize(self, audio_features: AudioFeatures) -> RecognitionResult:
        """음성을 텍스트로 변환"""
        tokens = self.whisper_model.generate(audio_features)
        text = self.tokenizer.decode(tokens)
        confidence = self._calculate_confidence(tokens)
        return RecognitionResult(text=text, confidence=confidence)
```

### 3. IntentRecognizer Class

```python
class IntentRecognizer:
    def __init__(self, llm_client: OpenAIClient):
        self.llm_client = llm_client
        self.intent_tools = self._setup_intent_tools()
    
    def recognize_intent(self, text: str, context: ConversationContext) -> Intent:
        """Tool calling을 사용한 의도 파악"""
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            messages=self._build_messages(text, context),
            tools=self.intent_tools
        )
        return self._parse_intent_from_tools(response)
```

### 4. DialogueManager Class

```python
class DialogueManager:
    def __init__(self, llm_client: OpenAIClient, order_manager: OrderManager):
        self.llm_client = llm_client
        self.order_manager = order_manager
        self.conversation_history = []
    
    def process_dialogue(self, intent: Intent, context: ConversationContext) -> DialogueResponse:
        """대화 처리 및 응답 생성"""
        if intent.type == IntentType.ORDER:
            result = self.order_manager.add_order(intent.menu_items)
        elif intent.type == IntentType.MODIFY:
            result = self.order_manager.modify_order(intent.modifications)
        elif intent.type == IntentType.CANCEL:
            result = self.order_manager.cancel_order(intent.cancel_items)
        
        response_text = self._generate_response(intent, result, context)
        return DialogueResponse(text=response_text, order_state=result)
```

### 5. OrderManager Class

```python
class OrderManager:
    def __init__(self, menu_config: MenuConfig):
        self.menu = Menu.from_config(menu_config)
        self.current_order = Order()
    
    def add_order(self, menu_items: List[MenuItem]) -> OrderResult:
        """주문 추가 처리"""
        for item in menu_items:
            if self.menu.validate_item(item):
                self.current_order.add_item(item)
        return OrderResult(success=True, order=self.current_order)
    
    def get_order_summary(self) -> OrderSummary:
        """현재 주문 상태 반환"""
        return self.current_order.get_summary()
```

### 6. TTSGenerator Class

```python
class TTSGenerator:
    def __init__(self, tts_config: TTSConfig):
        self.tts_engine = self._initialize_tts_engine(tts_config)
    
    def generate_speech(self, text: str) -> AudioOutput:
        """텍스트를 음성으로 변환"""
        audio_data = self.tts_engine.synthesize(text)
        return AudioOutput(data=audio_data, format="wav", sample_rate=22050)
```

## Data Models

### Core Data Models

```python
@dataclass
class AudioData:
    data: np.ndarray
    sample_rate: int
    channels: int
    duration: float

@dataclass
class ProcessedAudio:
    features: np.ndarray  # (80, 3000) Log-Mel spectrogram
    sample_rate: int = 16000

@dataclass
class RecognitionResult:
    text: str
    confidence: float
    processing_time: float

@dataclass
class Intent:
    type: IntentType  # ORDER, MODIFY, CANCEL, PAYMENT, INQUIRY
    menu_items: List[MenuItem] = None
    modifications: List[Modification] = None
    cancel_items: List[str] = None
    confidence: float = 0.0

@dataclass
class MenuItem:
    name: str
    category: str  # 단품, 세트, 라지세트
    quantity: int
    options: Dict[str, str] = None  # 음료 변경 등

@dataclass
class Order:
    items: List[MenuItem]
    total_amount: float
    status: OrderStatus
    created_at: datetime
    
    def add_item(self, item: MenuItem):
        self.items.append(item)
        self._update_total()
    
    def remove_item(self, item_name: str, quantity: int = 1):
        # 아이템 제거 로직
        pass
```

### Configuration Models

```python
@dataclass
class MenuConfig:
    restaurant_type: str
    menu_items: Dict[str, MenuItemConfig]
    categories: List[str]
    
@dataclass
class MenuItemConfig:
    name: str
    category: str
    price: float
    available_options: List[str]

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_size: int = 1024
    noise_reduction_level: float = 0.5
    speaker_separation_threshold: float = 0.7
```

## Error Handling

### Error Types and Handling Strategy

1. **Audio Processing Errors**
   - 음성 입력 실패: 재입력 요청
   - 다중화자 분리 실패: 단일 화자 모드로 fallback
   - 노이즈 제거 실패: 원본 오디오로 진행

2. **Speech Recognition Errors**
   - 낮은 신뢰도: 재입력 요청 또는 확인 질문
   - 모델 로딩 실패: 백업 모델 사용
   - 토큰화 오류: 오류 로깅 및 사용자 알림

3. **Intent Recognition Errors**
   - 의도 파악 실패: 명확화 질문
   - LLM API 오류: 재시도 로직 및 fallback 응답
   - Tool calling 오류: 기본 텍스트 파싱으로 fallback

4. **Order Management Errors**
   - 메뉴 아이템 없음: 유사 메뉴 제안
   - 주문 상태 불일치: 주문 초기화 및 재시작
   - 결제 처리 오류: 오류 상태 표시 및 직원 호출

### Error Recovery Mechanisms

```python
class ErrorHandler:
    def handle_audio_error(self, error: AudioError) -> ErrorResponse:
        if error.type == AudioErrorType.LOW_QUALITY:
            return ErrorResponse(
                message="음성이 명확하지 않습니다. 다시 말씀해 주세요.",
                action=ErrorAction.REQUEST_RETRY
            )
    
    def handle_recognition_error(self, error: RecognitionError) -> ErrorResponse:
        if error.confidence < 0.5:
            return ErrorResponse(
                message="정확히 듣지 못했습니다. 다시 주문해 주세요.",
                action=ErrorAction.REQUEST_CLARIFICATION
            )
```

## Testing Strategy

### Unit Testing

1. **AudioProcessor Testing**
   - 다중화자 분리 정확도 테스트
   - 노이즈 제거 효과 측정
   - 특징 추출 결과 검증

2. **SpeechRecognizer Testing**
   - 음성인식 정확도 (CER, WER) 측정
   - 다양한 음성 조건에서의 성능 테스트
   - 파인튜닝 모델 vs 베이스 모델 성능 비교

3. **IntentRecognizer Testing**
   - 의도 분류 정확도 테스트
   - Tool calling 결과 검증
   - 다양한 표현 방식에 대한 강건성 테스트

### Integration Testing

1. **End-to-End Pipeline Testing**
   - 전체 파이프라인 처리 시간 측정
   - 각 모듈 간 데이터 전달 검증
   - 오류 전파 및 복구 테스트

2. **Real-world Scenario Testing**
   - 실제 식당 환경에서의 성능 테스트
   - 다양한 사용자 음성에 대한 테스트
   - 동시 다발적 주문 상황 테스트

### Performance Testing

1. **Latency Requirements**
   - 음성 입력부터 응답까지 3초 이내
   - 각 모듈별 처리 시간 모니터링
   - 실시간 처리 성능 검증

2. **Accuracy Requirements**
   - 음성인식 정확도: CER < 5%
   - 의도 파악 정확도: > 95%
   - 주문 처리 정확도: > 99%

### Test Data and Environments

1. **Test Data Sources**
   - AIHub 011 고객 응대 데이터 (식당 도메인)
   - 실제 식당 환경에서 수집한 음성 데이터
   - 다양한 노이즈 조건의 합성 데이터

2. **Test Environments**
   - 조용한 환경 (배경 소음 < 40dB)
   - 일반적인 식당 환경 (배경 소음 40-60dB)
   - 시끄러운 환경 (배경 소음 > 60dB)