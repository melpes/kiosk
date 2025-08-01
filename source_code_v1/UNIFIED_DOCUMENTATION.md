# 음성 기반 키오스크 AI 주문 시스템 - 통합 문서

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [빠른 시작 가이드](#빠른-시작-가이드)
4. [설치 및 설정](#설치-및-설정)
5. [사용법](#사용법)
6. [API 문서](#api-문서)
7. [설정 관리](#설정-관리)
8. [테스트 시스템](#테스트-시스템)
9. [마이크 입력 시스템](#마이크-입력-시스템)
10. [Whisper 모델 설정](#whisper-모델-설정)
11. [문제 해결](#문제-해결)
12. [개발 가이드](#개발-가이드)

---

## 프로젝트 개요

### 🎯 주요 기능

음성인식과 자연어 처리를 활용한 식당 키오스크 시스템입니다. 사용자의 음성 입력을 분석하여 주문, 변경, 취소, 결제 등의 의도를 파악하고 음성으로 응답을 제공합니다.

- **음성 전처리**: 다중화자인식/구분을 통한 노이즈 개선
- **음성인식**: Whisper 기반 모델을 파인튜닝하여 사용자 음성을 텍스트로 변환
- **대화 처리**: OpenAI의 GPT 모델을 활용한 멀티턴 대화 처리
- **주문 관리**: 주문 추가, 변경, 취소 및 결제 처리
- **음성 응답**: TTS를 통한 음성 응답 제공
- **자동화된 테스트 시스템**: 맥도날드 특화 테스트케이스 생성 및 실행
- **실시간 마이크 입력**: VAD 기반 실시간 음성 입력 처리

### 🏗️ 기술 스택

- **프로그래밍 언어**: Python 3.8+
- **음성인식**: OpenAI Whisper (파인튜닝 지원)
- **LLM**: OpenAI GPT-4o
- **TTS**: OpenAI TTS (선택사항)
- **음성 처리**: librosa, pyaudio
- **VAD**: Silero VAD
- **로깅**: loguru

### 📁 프로젝트 구조

```
voice_kiosk/
├── config/                  # 설정 파일
│   └── menu_config.json     # 메뉴 및 도메인 설정
├── src/                     # 소스 코드
│   ├── audio/               # 음성 처리 관련 모듈
│   ├── speech/              # 음성인식 관련 모듈
│   ├── conversation/        # 대화 처리 관련 모듈
│   ├── order/               # 주문 관리 관련 모듈
│   ├── response/            # 응답 생성 관련 모듈
│   ├── testing/             # 테스트 시스템 모듈
│   ├── microphone/          # 마이크 입력 시스템 모듈
│   ├── error/               # 오류 처리 관련 모듈
│   ├── utils/               # 유틸리티 모듈
│   ├── models/              # 데이터 모델
│   ├── cli/                 # CLI 인터페이스
│   ├── config.py            # 설정 관리
│   ├── logger.py            # 로깅 설정
│   └── main.py              # 메인 실행 파일
├── tests/                   # 테스트 코드
├── demos/                   # 데모 스크립트
├── data/                    # 데이터 파일 (참고용)
├── models/                  # 학습된 모델 저장
├── logs/                    # 로그 파일
├── test_results/            # 테스트 결과 보고서
├── .env                     # 환경 변수 설정
├── .env.example             # 환경 변수 템플릿
├── README.md                # 프로젝트 개요 및 빠른 시작
├── UNIFIED_DOCUMENTATION.md # 📚 통합 문서 (전체 가이드)
└── requirements.txt         # 의존성 패키지
```

---

## 시스템 아키텍처

### 데이터 흐름

```
음성 입력 → AudioProcessor → SpeechRecognizer → IntentRecognizer → DialogueManager → OrderManager → TextResponseSystem → 음성 출력
```

### 핵심 모듈 구성

1. **음성 전처리 모듈** (`src/audio/preprocessing.py`)
   - 다중화자인식/구분 기능
   - 노이즈 제거 및 음성 품질 개선

2. **음성인식 모듈** (`src/speech/recognition.py`)
   - Whisper 기반 모델 활용
   - 식당 주문 상황에 특화된 음성인식

3. **대화 처리 모듈** (`src/conversation/`)
   - 의도 파악 및 대화 관리
   - LLM을 활용한 자연어 처리
   - Tool calling을 통한 구조화된 출력

4. **주문 관리 모듈** (`src/order/`)
   - 메뉴 관리 및 주문 처리

5. **테스트 시스템** (`src/testing/`)
   - 자동화된 테스트케이스 생성
   - 맥도날드 특화 은어 및 반말 테스트
   - 성능 분석 및 보고서 생성

6. **마이크 입력 시스템** (`src/microphone/`)
   - 실시간 마이크 입력 처리
   - VAD 기반 음성 활동 감지
   - 자동 녹음 시작/종료

---

## 빠른 시작 가이드

### ⚡ 30초 시작하기

#### 1. 환경 설정 (최초 1회)
```bash
# 의존성 설치
pip install -r requirements.txt

# API 키는 이미 .env 파일에 설정되어 있습니다
# 필요시 .env 파일에서 OPENAI_API_KEY 값을 수정하세요
```

#### 2. 즉시 테스트 시작

**🔥 가장 안전한 테스트 도구 (추천)**
```bash
python run_debug_safe.py
```

**메인 시스템 실행**
```bash
python src/main.py
```

**전체 기능 테스트**
```bash
python run_debug.py
```

**현재 사용 가능한 모드들:**
- 대화형 모드 (기본): 텍스트 및 음성 파일 입력
- 테스트 모드: 자동화된 테스트케이스 실행
- 마이크 모드: 실시간 마이크 입력 (실험적)

### 🎯 주요 사용법

#### 방법 1: 간단한 테스트 (API 키 불필요, 추천)
```bash
python src/simple_debug.py
```
- 기본 시스템 동작 확인
- 메뉴 검색 테스트
- 간단한 대화형 주문 테스트

#### 방법 2: 전체 기능 테스트 (API 키 필요)
```bash
python run_debug.py
```
메뉴에서 원하는 테스트 방법을 선택:
- `1`: 대화형 디버그 모드
- `2`: 텍스트 입력 테스트  
- `3`: 음성 파일 테스트
- `4`: 시스템 상태 확인

#### 방법 3: 직접 명령어 사용

**텍스트 테스트 (가장 간단)**
```bash
python src/debug_main.py --mode text --input "빅맥 세트 주문해주세요" --debug
```

**대화형 모드 (연속 테스트)**
```bash
python src/debug_main.py --mode interactive --debug
```

---

## 설치 및 설정

### 시스템 요구사항

#### 하드웨어 요구사항
- **CPU**: Intel i5 이상 또는 동급 AMD 프로세서
- **메모리**: 최소 8GB RAM (16GB 권장)
- **저장공간**: 최소 5GB 여유 공간
- **GPU**: CUDA 지원 GPU (선택사항, 성능 향상용)
- **마이크**: 음성 입력을 위한 마이크 (테스트용)

#### 소프트웨어 요구사항
- **운영체제**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8 이상 (3.9 권장)
- **Git**: 버전 관리 및 소스 코드 다운로드용

### 설치 과정

#### 1. 저장소 클론
```bash
git clone <repository-url>
cd voice-kiosk-system
```

#### 2. Python 가상환경 생성

**Windows**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. 추가 시스템 의존성 설치

**Windows**
```cmd
pip install pipwin
pipwin install pyaudio
```

**macOS**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian**
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev
```

### 환경 설정

#### 1. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정:

```bash
cp .env.example .env
```

`.env` 파일 주요 설정:
```env
# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# 음성 처리 설정
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024
NOISE_REDUCTION_LEVEL=0.5

# 마이크 설정
MIC_VAD_THRESHOLD=0.2
MIC_MAX_SILENCE_START=5.0
MIC_MAX_SILENCE_END=3.0

# 테스트 설정
TEST_MAX_TESTS_PER_CATEGORY=50
TEST_TIMEOUT_SECONDS=30

# 시스템 설정
LOG_LEVEL=INFO
RESTAURANT_NAME=테스트 식당
LANGUAGE=ko
```

#### 2. API 키 설정

**OpenAI API 키 획득**
1. [OpenAI 웹사이트](https://platform.openai.com/)에 가입
2. API 키 생성
3. `.env` 파일의 `OPENAI_API_KEY`에 실제 API 키 설정

**⚠️ 보안 주의사항**: `.env` 파일은 `.gitignore`에 포함되어 있습니다. 실제 API 키를 커밋하지 마세요.

#### 3. 메뉴 설정

`config/menu_config.json` 파일에서 메뉴를 설정:

```json
{
  "restaurant_info": {
    "name": "테스트 식당",
    "type": "fast_food",
    "description": "음성 주문 테스트용 식당"
  },
  "categories": ["버거", "사이드", "음료", "디저트"],
  "menu_items": {
    "빅맥": {
      "category": "버거",
      "price": 6500,
      "description": "빅맥 버거",
      "available_options": ["단품", "세트", "라지세트"],
      "set_drink_options": ["콜라", "사이다", "오렌지주스"],
      "set_side_options": ["감자튀김", "치킨너겟"]
    }
  }
}
```

### 설치 검증

#### 1. 설정 검증
```bash
python -c "from src.config import config_manager; print(config_manager.validate_config())"
```

#### 2. 시스템 초기화 테스트
```bash
python -c "from src.main import VoiceKioskPipeline; p = VoiceKioskPipeline(); print('초기화 성공' if p.initialize_system() else '초기화 실패')"
```

#### 3. 기본 실행 테스트
```bash
python src/main.py
```

---

## 사용법

### 기본 실행

#### 메인 시스템 실행 (대화형 모드)
```bash
python src/main.py
```

시스템이 시작되면 다음과 같은 화면이 나타납니다:
```
============================================================
🎤 음성 기반 키오스크 AI 주문 시스템
============================================================
💬 텍스트로 주문하세요
🎵 음성 파일은 'file:경로' 형식으로 입력 (예: file:./audio/order.wav)
🚪 종료하려면 'quit', 'exit', '종료' 중 하나를 입력하세요
🔄 새 주문을 시작하려면 '새 주문' 또는 'new'를 입력하세요
🤖 음성인식 모델: base (whisper, auto)
============================================================

시스템: 안녕하세요! 테스트 식당에 오신 것을 환영합니다. 주문하실 메뉴를 말씀해 주세요.

👤 입력: 
```

#### 특별 모드 실행

**테스트 모드 (맥도날드 특화 테스트)**
```bash
python src/main.py --mode test
```

**마이크 입력 모드 (실시간 음성 입력)**
```bash
python src/main.py --mode microphone
```

#### CLI 인터페이스 실행
```bash
python src/cli/interface.py
```

### 텍스트 주문 예시

#### 기본 주문
```
👤 입력: 빅맥 세트 하나 주세요
🤖 빅맥 세트 1개를 주문에 추가했습니다. 음료는 콜라로 하시겠어요?

👤 입력: 네, 콜라로 해주세요
🤖 빅맥 세트(콜라)가 주문에 추가되었습니다. 추가로 주문하실 것이 있으신가요?
```

#### 옵션 변경
```
👤 입력: 콜라를 사이다로 바꿔주세요
🤖 음료를 사이다로 변경했습니다. 현재 주문: 빅맥 세트(사이다) 1개
```

#### 결제
```
👤 입력: 결제할게요
🤖 주문을 확정하시겠습니까? 총 금액은 6,500원입니다. 확인하시려면 '네'라고 말씀해 주세요.

👤 입력: 네
🤖 결제가 완료되었습니다. 주문번호는 #001입니다. 이용해 주셔서 감사합니다!
```

### 음성 파일 입력

음성 파일을 테스트하려면 `file:` 접두사를 사용:

```
👤 입력: file:audio_samples/order1.wav
🎵 음성 파일 처리 중: audio_samples/order1.wav
🤖 빅맥 세트 1개를 주문에 추가했습니다. 음료는 어떻게 하시겠어요?
```

지원되는 음성 파일 형식: WAV, MP3, M4A, FLAC

### CLI 명령어

#### 시스템 상태 확인
```
👤 입력: status
또는
👤 입력: 상태
```

#### 현재 주문 확인
```
👤 입력: order
또는
👤 입력: 주문확인
```

#### 메뉴 보기
```
👤 입력: menu
또는
👤 입력: 메뉴
```

---

## API 문서

### VoiceKioskPipeline

메인 파이프라인 클래스로 전체 시스템을 관리합니다.

#### 초기화
```python
from src.main import VoiceKioskPipeline

pipeline = VoiceKioskPipeline()
```

#### 주요 메서드

##### `initialize_system() -> bool`
시스템의 모든 모듈을 초기화합니다.

```python
if pipeline.initialize_system():
    print("시스템 초기화 성공")
else:
    print("시스템 초기화 실패")
```

##### `process_text_input(text: str) -> str`
텍스트 입력을 처리하여 응답을 생성합니다.

```python
response = pipeline.process_text_input("빅맥 세트 하나 주세요")
print(f"응답: {response}")
```

##### `process_audio_input(audio_file_path: str) -> str`
음성 파일을 처리하여 응답을 생성합니다.

```python
response = pipeline.process_audio_input("audio/order.wav")
print(f"응답: {response}")
```

### 데이터 모델

#### Intent
```python
@dataclass
class Intent:
    type: IntentType                    # 의도 타입
    menu_items: List[MenuItem] = None   # 주문 메뉴 아이템
    modifications: List[Modification] = None  # 수정 사항
    cancel_items: List[str] = None      # 취소 아이템
    confidence: float = 0.0             # 신뢰도
```

#### IntentType (Enum)
```python
class IntentType(Enum):
    ORDER = "order"           # 주문
    MODIFY = "modify"         # 수정
    CANCEL = "cancel"         # 취소
    PAYMENT = "payment"       # 결제
    INQUIRY = "inquiry"       # 문의
    GREETING = "greeting"     # 인사
    HELP = "help"            # 도움말
    UNKNOWN = "unknown"       # 알 수 없음
```

---

## 설정 관리

### 환경변수 기반 설정 시스템

모든 설정값들이 `.env` 파일로 통합되어 환경변수 기반으로 관리됩니다.

### 주요 설정 카테고리

#### OpenAI API 설정
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7
API_TIMEOUT=60.0
API_RETRY_COUNT=3
```

#### 음성 처리 설정
```env
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024
NOISE_REDUCTION_LEVEL=0.5
SPEAKER_SEPARATION_THRESHOLD=0.7
```

#### 마이크 입력 설정
```env
MIC_VAD_THRESHOLD=0.2
MIC_MAX_SILENCE_START=5.0
MIC_MAX_SILENCE_END=3.0
MIC_MIN_RECORD_DURATION=1.0
```

#### 테스트 시스템 설정
```env
TEST_INCLUDE_SLANG=true
TEST_INCLUDE_INFORMAL=true
TEST_INCLUDE_COMPLEX=true
TEST_MAX_TESTS_PER_CATEGORY=50
TEST_TIMEOUT_SECONDS=30
```

### 환경별 최적화 설정

#### 개발 환경
```env
LOG_LEVEL=DEBUG
TEST_MAX_TESTS_PER_CATEGORY=10
DEBUG_MODE=true
```

#### 프로덕션 환경
```env
LOG_LEVEL=INFO
ENABLE_CACHING=true
OPTIMIZE_MEMORY=true
```

### 설정 확인 방법

```bash
# 설정 확인 데모 실행
python demos/demo_config_management.py

# 환경변수 테스트
python test_env_config.py
```

---

## 테스트 시스템

### 자동화된 테스트 시스템

맥도날드 키오스크 환경에 특화된 테스트케이스를 자동으로 생성하고 실행하는 시스템입니다.

### 테스트 실행 방법

#### 기본 테스트 실행
```bash
python src/main.py --mode test
```

#### 특정 카테고리 테스트
```bash
python src/main.py --mode test --categories slang,informal
```

### 테스트 카테고리

1. **slang**: 맥도날드 은어 테스트 ("상스치콤", "베토디" 등)
2. **informal**: 반말 입력 테스트
3. **complex**: 복합 의도 테스트 (주문+취소, 변경+추가 등)
4. **normal**: 일반적인 주문 패턴 테스트
5. **edge**: 엣지 케이스 테스트 (빈 입력, 특수문자 등)

### TestCaseGenerator API

#### 전체 테스트케이스 생성
```python
from src.testing.test_case_generator import TestCaseGenerator

generator = TestCaseGenerator()
test_cases = generator.generate_mcdonald_test_cases()
print(f"총 {len(test_cases)}개의 테스트케이스 생성됨")
```

#### 커스텀 테스트케이스 생성
```python
custom_case = generator.generate_custom_test_case(
    input_text="빅맥 하나 주세요",
    expected_intent=IntentType.ORDER,
    category=TestCaseCategory.NORMAL,
    description="빅맥 주문 테스트"
)
```

### TestRunner API

#### 단일 테스트 실행
```python
from src.testing.test_runner import TestRunner

runner = TestRunner(pipeline)
result = runner.run_single_test(test_case)
print(f"성공: {result.success}, 처리시간: {result.processing_time:.2f}초")
```

#### 배치 테스트 실행
```python
results = runner.run_batch_tests(test_cases)
success_count = sum(1 for r in results if r.success)
print(f"성공률: {success_count/len(results)*100:.1f}%")
```

### 테스트 결과 분석

테스트 완료 후 `test_results/` 디렉토리에 다음 파일들이 생성됩니다:

- `test_report.txt`: 텍스트 형태의 상세 보고서
- `test_report.md`: 마크다운 형태의 보고서
- `test_cases.json`: 실행된 테스트케이스 목록
- `detailed_results.json`: 상세한 테스트 결과

#### 주요 지표
- **성공률**: 전체 테스트 중 성공한 비율
- **평균 처리 시간**: 각 테스트케이스 처리에 걸린 평균 시간
- **의도별 정확도**: 각 의도(주문, 취소, 변경 등)별 정확도
- **카테고리별 성능**: 각 테스트 카테고리별 성능

---

## 마이크 입력 시스템

### 실시간 마이크 입력 기능

VAD(Voice Activity Detection) 기반의 실시간 마이크 입력 처리 시스템입니다.

### 마이크 모드 실행

#### 기본 마이크 모드
```bash
python src/main.py --mode microphone
```

### 사용 순서

1. **시스템 시작**: 마이크 모드를 선택하면 VAD 모델이 로딩됩니다
2. **음성 감지 대기**: "주문을 말씀해주세요" 메시지가 표시됩니다
3. **음성 입력**: 말을 시작하면 자동으로 녹음이 시작됩니다
4. **자동 종료**: 말을 멈추고 일정 시간이 지나면 녹음이 자동 종료됩니다
5. **처리 및 응답**: 음성이 텍스트로 변환되고 시스템이 응답합니다

### 마이크 상태 표시

화면에 표시되는 상태 기호:
- ⏳ **waiting**: 음성 입력 대기 중
- 🗣️ **detecting**: 음성 감지됨
- 🎙️ **recording**: 녹음 중
- ⚙️ **processing**: 음성 처리 중

### MicrophoneInputManager API

#### 클래스 초기화
```python
from src.microphone.microphone_manager import MicrophoneInputManager
from src.models.microphone_models import MicrophoneConfig

config = MicrophoneConfig(
    sample_rate=16000,
    vad_threshold=0.2,
    max_silence_duration_end=3.0
)
manager = MicrophoneInputManager(config)
```

#### 주요 메서드

##### `start_listening() -> str`
마이크 입력을 시작하고 녹음된 파일 경로를 반환합니다.

```python
try:
    audio_file = manager.start_listening()
    print(f"녹음 완료: {audio_file}")
except MicrophoneError as e:
    print(f"마이크 오류: {e}")
```

##### `get_microphone_status() -> Dict[str, Any]`
현재 마이크 상태를 반환합니다.

```python
status = manager.get_microphone_status()
print(f"VAD 상태: {status['vad_status']}")
print(f"볼륨 레벨: {status['current_volume_level']:.3f}")
```

##### `test_microphone() -> Dict[str, Any]`
마이크 테스트를 실행합니다.

```python
test_result = manager.test_microphone()
if test_result["overall_success"]:
    print("마이크 테스트 성공")
else:
    print("마이크 테스트 실패")
```

### 마이크 설정 조정

마이크 감도나 녹음 시간을 조정하려면 환경변수를 수정:

```env
MIC_VAD_THRESHOLD=0.2      # VAD 감도 (0.1-0.5, 낮을수록 민감)
MIC_MAX_SILENCE_START=5.0  # 시작 대기 시간 (초)
MIC_MAX_SILENCE_END=3.0    # 종료 대기 시간 (초)
MIC_MIN_RECORD_DURATION=1.0 # 최소 녹음 시간 (초)
```

### 환경별 마이크 설정

#### 조용한 환경 (사무실, 집)
```env
MIC_VAD_THRESHOLD=0.1
MIC_MAX_SILENCE_START=3.0
MIC_MAX_SILENCE_END=2.0
```

#### 시끄러운 환경 (카페, 식당)
```env
MIC_VAD_THRESHOLD=0.4
MIC_MAX_SILENCE_START=7.0
MIC_MAX_SILENCE_END=4.0
```

#### 키오스크 환경
```env
MIC_VAD_THRESHOLD=0.3
MIC_MAX_SILENCE_START=5.0
MIC_MAX_SILENCE_END=3.0
```

---

## Whisper 모델 설정

### 지원하는 모델 타입

#### 1. 기본 OpenAI Whisper 모델
```env
WHISPER_MODEL=tiny     # 39MB, 가장 빠름, 낮은 정확도
WHISPER_MODEL=base     # 74MB, 균형잡힌 성능 (기본값)
WHISPER_MODEL=small    # 244MB, 더 정확함, 조금 느림
WHISPER_MODEL=medium   # 769MB, 높은 정확도, 느림
WHISPER_MODEL=large    # 1550MB, 최고 정확도, 가장 느림
```

#### 2. 허깅페이스 모델
```env
# 공식 OpenAI 모델
WHISPER_MODEL=openai/whisper-base
WHISPER_MODEL=openai/whisper-small
WHISPER_MODEL=openai/whisper-large-v3

# 커뮤니티 파인튜닝 모델
WHISPER_MODEL=your-username/korean-whisper-model
```

#### 3. 로컬 파인튜닝된 모델
```env
# 상대 경로
WHISPER_MODEL=./models/whisper/fine_tuned_model.pt

# 절대 경로
WHISPER_MODEL=/home/user/models/whisper_korean.pt
```

### 성능 고려사항

| 모델 크기 | 메모리 사용량 | 처리 속도 | 정확도 | 권장 용도 |
|-----------|---------------|-----------|--------|-----------|
| tiny      | ~1GB         | 매우 빠름 | 낮음   | 테스트/프로토타입 |
| base      | ~1GB         | 빠름      | 보통   | 일반적인 용도 |
| small     | ~2GB         | 보통      | 좋음   | 균형잡힌 성능 |
| medium    | ~5GB         | 느림      | 매우 좋음 | 높은 정확도 필요 |
| large     | ~10GB        | 매우 느림 | 최고   | 최고 품질 필요 |

### 권장 설정

#### 개발/테스트 환경
```env
WHISPER_MODEL=base
WHISPER_LANGUAGE=ko
WHISPER_DEVICE=cpu
```

#### 프로덕션 환경 (GPU 있음)
```env
WHISPER_MODEL=small
WHISPER_LANGUAGE=ko
WHISPER_DEVICE=cuda
```

#### 파인튜닝된 모델 (권장)
```env
WHISPER_MODEL=./models/whisper/aihub_restaurant_finetuned.pt
WHISPER_LANGUAGE=ko
WHISPER_DEVICE=cuda
```

---

## 문제 해결

### 현재 알려진 이슈

#### ⚠️ OpenAI 클라이언트 초기화 문제
**증상**: `Client.__init__() got an unexpected keyword argument 'proxies'` 오류

**현재 상태**: API 키는 정상적으로 인식되지만, OpenAI 클라이언트 초기화에서 라이브러리 충돌 발생

**임시 해결책**:
1. **API 키 없이 기본 시스템 테스트** (추천)
   ```bash
   python src/simple_debug.py
   ```

2. **OpenAI 라이브러리 재설치**
   ```bash
   pip uninstall openai
   pip install openai==1.12.0
   ```

3. **가상환경 새로 생성**
   ```bash
   python -m venv new_env
   new_env\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

### 일반적인 문제들

#### 1. API 키 관련 문제
**증상**: API 키 인식 문제

**해결방법**:
- `.env` 파일에 올바른 API 키가 설정되어 있는지 확인
- API 키에 충분한 크레딧이 있는지 확인
- API 키 형식이 올바른지 확인 (sk-proj-로 시작)

#### 2. 마이크가 인식되지 않음
**증상**: "사용 가능한 마이크 장치가 없습니다" 오류

**해결방법**:
1. 마이크가 올바르게 연결되어 있는지 확인
2. 시스템 오디오 설정에서 마이크 활성화
3. 마이크 권한 허용 확인
4. 다른 프로그램에서 마이크를 사용 중인지 확인

#### 3. VAD 모델 로딩 실패
**증상**: "VAD 모델 로딩 실패, 폴백 모드로 전환" 메시지

**해결방법**:
1. 인터넷 연결 확인 (모델 다운로드용)
2. 충분한 메모리 확보 (최소 2GB)
3. 폴백 모드에서도 기본 기능은 사용 가능

#### 4. 음성 인식 정확도가 낮음
**해결방법**:
1. 조용한 환경에서 사용
2. 마이크에 가까이서 명확하게 발음
3. VAD 임계값 조정 (더 민감하게 설정)
4. 마이크 품질 확인

#### 5. PyAudio 설치 오류
**증상**: `PyAudio` 설치 실패

**해결방법**:
- Windows: `pipwin install pyaudio` 사용
- macOS: `brew install portaudio` 후 재시도
- Linux: `sudo apt-get install python3-pyaudio portaudio19-dev`

#### 6. Whisper 모델 다운로드 오류
**증상**: 첫 실행 시 모델 다운로드 실패

**해결방법**:
- 인터넷 연결 확인
- 충분한 저장 공간 확인 (약 1GB 필요)
- 방화벽 설정 확인

### 로그 확인

문제 발생 시 다음 로그 파일들을 확인하세요:

- `logs/voice_kiosk.log`: 전체 시스템 로그
- `logs/test_execution.log`: 테스트 실행 로그
- `logs/microphone.log`: 마이크 관련 로그

```bash
# 실시간 로그 확인
tail -f logs/voice_kiosk.log

# 최근 로그 확인
tail -n 100 logs/voice_kiosk.log
```

### 진단 도구

시스템 상태를 확인하려면:

```bash
python src/main.py --mode diagnostic
```

이 명령어는 다음 정보를 제공합니다:
- 하드웨어 상태
- VAD 모델 상태
- 설정 유효성
- 최근 오류 기록

### 디버그 모드

더 자세한 정보를 보려면 디버그 모드로 실행:

```bash
export LOG_LEVEL=DEBUG
python src/main.py
```

---

## 개발 가이드

### 코딩 스타일

- Python 3.8+ 사용
- PEP 8 스타일 가이드 준수
- 타입 힌트 사용 권장
- 한국어 주석 및 문서화

### 새로운 기능 추가

1. `src/` 디렉토리에 모듈 추가
2. `tests/` 디렉토리에 테스트 코드 작성
3. `demos/` 디렉토리에 데모 스크립트 작성 (선택사항)

### 테스트 실행

```bash
# 모든 단위 테스트 실행
python -m pytest tests/ -v

# 통합 테스트 실행
python tests/integration/run_all_integration_tests.py

# 개별 테스트 실행
python tests/integration/test_main_integration.py
```

### 성능 최적화

#### 1. 응답 속도 개선
- OpenAI API 설정에서 `max_tokens` 값을 줄임
- 불필요한 로깅 레벨을 높임 (`LOG_LEVEL=WARNING`)
- GPU 사용 설정 (CUDA 지원 시)

#### 2. 메모리 사용량 최적화
- Whisper 모델 크기를 작게 설정 (`tiny`, `base`)
- 동시 세션 수 제한
- 주기적인 세션 정리

#### 3. 정확도 개선
- 메뉴 설정을 더 상세하게 작성
- 동의어 및 별칭 추가
- 도메인 특화 용어 학습

### 확장성

시스템은 다음과 같은 확장이 가능합니다:

1. **새로운 음성인식 모델**: SpeechRecognizer 인터페이스 구현
2. **다른 LLM 모델**: IntentRecognizer에서 다른 API 사용
3. **TTS 시스템**: 음성 출력 모듈 추가
4. **다른 식당 도메인**: 메뉴 설정 파일 변경

### 기여 방법

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

---

## FAQ

### Q1: 현재 API 키 문제로 전체 기능을 사용할 수 없나요?
**A**: API 키는 정상적으로 설정되어 있지만, OpenAI 클라이언트 초기화 문제로 일부 기능이 제한됩니다. 하지만 기본 시스템 테스트(`python src/simple_debug.py`)는 완벽하게 작동합니다.

### Q2: 테스트는 얼마나 오래 걸리나요?
**A**: 전체 테스트는 보통 5-10분 정도 소요됩니다. 테스트 수와 시스템 성능에 따라 달라질 수 있습니다.

### Q3: 마이크 없이도 시스템을 사용할 수 있나요?
**A**: 네, 기존의 텍스트 입력 모드와 오디오 파일 입력 모드는 여전히 사용 가능합니다.

### Q4: 다른 언어로도 테스트할 수 있나요?
**A**: 현재는 한국어만 지원합니다. 다른 언어 지원은 향후 업데이트에서 추가될 예정입니다.

### Q5: 테스트 결과를 어떻게 해석해야 하나요?
**A**: 
- **성공률 90% 이상**: 우수한 성능
- **성공률 80-90%**: 양호한 성능
- **성공률 80% 미만**: 개선 필요

### Q6: 마이크 감도를 어떻게 조정하나요?
**A**: `.env` 파일의 `MIC_VAD_THRESHOLD` 값을 조정하세요:
- 더 민감하게: 0.1-0.15
- 기본값: 0.2 (현재 설정)
- 덜 민감하게: 0.3-0.5

### Q7: 시스템이 느려졌을 때는 어떻게 하나요?
**A**: 
1. 시스템 재시작
2. 불필요한 프로그램 종료
3. 메모리 확보
4. 진단 모드로 상태 확인

### Q8: EOF 오류가 발생하면 어떻게 하나요?
**A**: EOF 오류는 이미 해결되었습니다. `run_debug_safe.py`를 사용하면 안전하게 테스트할 수 있습니다.

---

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 지원 및 문의

문제가 발생하거나 질문이 있으시면:

1. **로그 파일 확인**: `logs/` 디렉토리의 로그 파일들
2. **진단 실행**: `python src/main.py --mode diagnostic`
3. **이슈 리포트**: GitHub Issues에 문제 상황과 로그 첨부

---

## 현재 프로젝트 상태 (2025.01.30 기준)

### ✅ 완전히 작동하는 기능들
- **기본 시스템 테스트**: `python src/simple_debug.py` (API 키 불필요)
- **메뉴 시스템**: 완전 구현 및 테스트 완료
- **주문 관리 시스템**: 완전 구현 및 테스트 완료
- **응답 생성 시스템**: 완전 구현 및 테스트 완료
- **환경변수 기반 설정 시스템**: 완전 구현 및 테스트 완료
- **EOF 오류 해결**: 모든 입력 처리 도구 안전성 확보

### ⚠️ 제한적으로 작동하는 기능들
- **OpenAI LLM 연동**: API 키는 인식되지만 클라이언트 초기화 문제
- **음성인식 기능**: Whisper 모델 로딩 가능하지만 LLM 연동 제한
- **테스트 시스템**: 기본 구조는 완성되었으나 LLM 연동 필요
- **마이크 입력 시스템**: 기본 구조는 완성되었으나 LLM 연동 필요

### 🔧 현재 해결 중인 이슈
- **OpenAI 클라이언트 초기화 문제**: `proxies` 인수 오류
- **라이브러리 호환성**: OpenAI 라이브러리 버전 충돌

### 📋 즉시 사용 가능한 도구들
1. **`python src/simple_debug.py`** - 기본 시스템 완전 테스트
2. **`python run_debug_safe.py`** - 안전한 통합 테스트 도구
3. **`python demos/demo_config_management.py`** - 설정 시스템 테스트
4. **`python test_env_config.py`** - 환경변수 설정 테스트

### 🎯 권장 사용 순서
1. **첫 번째**: `python src/simple_debug.py` (기본 시스템 확인)
2. **두 번째**: `python test_env_config.py` (설정 시스템 확인)
3. **세 번째**: `python run_debug_safe.py` (통합 테스트)
4. **네 번째**: OpenAI 클라이언트 문제 해결 후 전체 기능 테스트

---

**🎯 목표**: 1분 안에 시스템을 실행하고 테스트를 시작할 수 있어야 합니다!

**📅 마지막 업데이트**: 2025년 1월 30일  
**📝 참고**: 이 문서는 시스템 업데이트에 따라 변경될 수 있습니다. 최신 버전을 확인해주세요.