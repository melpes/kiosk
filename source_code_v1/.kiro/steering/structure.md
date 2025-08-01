# 프로젝트 구조 및 조직

## 프로젝트 구조 개요
이 프로젝트는 음성 기반 식당 키오스크 시스템으로, 음성 전처리부터 TTS까지 파이프라인 구조로 설계되었습니다. 코드는 모듈화되어 있으며, 각 모듈은 독립적으로 개발 및 테스트가 가능합니다.

## 디렉토리 구조
```
voice_kiosk/
├── config/                  # 설정 파일
│   ├── api_keys.json        # API 키 설정 (gitignore에 추가)
│   └── menu_config.json     # 메뉴 및 도메인 설정
├── src/                     # 소스 코드
│   ├── audio/               # 음성 처리 관련 모듈
│   │   ├── preprocessing.py # 음성 전처리 및 다중화자인식
│   │   └── tts.py           # 텍스트-음성 변환
│   ├── speech/              # 음성인식 관련 모듈
│   │   └── recognition.py   # Whisper 기반 음성인식
│   ├── conversation/        # 대화 처리 관련 모듈
│   │   ├── intent.py        # 의도 파악
│   │   └── dialogue.py      # 대화 관리
│   ├── order/               # 주문 관리 관련 모듈
│   │   ├── menu.py          # 메뉴 관리
│   │   └── order.py         # 주문 처리
│   └── main.py              # 메인 실행 파일
├── tests/                   # 테스트 코드
│   ├── test_audio.py        # 음성 처리 테스트
│   ├── test_speech.py       # 음성인식 테스트
│   ├── test_conversation.py # 대화 처리 테스트
│   └── test_order.py        # 주문 관리 테스트
├── data/                    # 데이터 파일 (참고용, 실제 데이터는 별도 서버에 존재)
│   ├── audio_samples/       # 테스트용 음성 샘플
│   └── training/            # 모델 학습 데이터 참조 정보
└── models/                  # 학습된 모델 저장
    ├── whisper/             # 파인튜닝된 Whisper 모델
    └── speaker/             # 화자 구분 모델
```

## 핵심 모듈 구성

### 1. 음성 전처리 모듈 (`src/audio/preprocessing.py`)
- 다중화자인식/구분 기능
- 노이즈 제거 및 음성 품질 개선
- 주요 클래스: `AudioProcessor`

### 2. 음성인식 모듈 (`src/speech/recognition.py`)
- Whisper 기반 모델 활용
- 식당 주문 상황에 특화된 음성인식
- 주요 클래스: `SpeechRecognizer`

### 3. 대화 처리 모듈 (`src/conversation/`)
- 의도 파악 (`intent.py`)
- 대화 관리 (`dialogue.py`)
- LLM을 활용한 자연어 처리
- Tool calling을 통한 구조화된 출력
- 주요 클래스: `IntentRecognizer`, `DialogueManager`

### 4. 주문 관리 모듈 (`src/order/`)
- 메뉴 관리 (`menu.py`)
- 주문 처리 (`order.py`)
- 주요 클래스: `Menu`, `Order`

### 5. TTS 모듈 (`src/audio/tts.py`)
- 텍스트를 음성으로 변환
- 주요 클래스: `TTSGenerator`

## 데이터 흐름
1. 음성 입력 → `AudioProcessor` → 전처리된 음성
2. 전처리된 음성 → `SpeechRecognizer` → 텍스트
3. 텍스트 → `IntentRecognizer` → 의도 파악
4. 의도 → `DialogueManager` → 대화 처리
5. 대화 처리 → `Order` → 주문 관리
6. 응답 텍스트 → `TTSGenerator` → 음성 출력

## 설정 및 구성
- `config/api_keys.json`: OpenAI API 키 등 외부 서비스 접근 키 관리
- `config/menu_config.json`: 메뉴 정보 및 도메인 설정

## 테스트 전략
- 각 모듈별 단위 테스트
- 전체 파이프라인 통합 테스트
- 실제 환경에서의 사용자 테스트

## 확장성
- 다양한 식당 메뉴 및 환경에 적용 가능한 구조
- 모듈별 독립적인 개선 및 업데이트 가능
- 새로운 기능 추가가 용이한 모듈화된 설계