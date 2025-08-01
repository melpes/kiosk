# 기술 스택 및 개발 환경

## 주요 기술 스택
- **프로그래밍 언어**: Python
- **음성 전처리**: 다중화자인식/구분 기술
- **음성인식 모델**: Whisper 기반 모델 (파인튜닝 또는 LoRA 적용)
- **LLM**: OpenAI GPT-4o
- **TTS**: 미정 (추후 결정)

## 라이브러리 및 의존성
- `openai`: OpenAI API와 통신하기 위한 Python 클라이언트 라이브러리
- `sys`: 시스템 관련 기능 (프로그램 종료 등)
- `whisper`: OpenAI의 음성인식 모델
- 음성 전처리 관련 라이브러리 (예: librosa, pyaudio 등)
- 다중화자인식/구분 관련 라이브러리

## 환경 설정
- OpenAI API 키가 필요합니다
- Python 3.x 버전이 필요합니다
- GPU 환경 권장 (Whisper 모델 실행 및 파인튜닝)

## 실행 방법
```bash
python ourproject.py
```

## 개발 규칙
1. API 키는 코드에 직접 포함하지 않고 환경 변수나 별도의 설정 파일에서 로드합니다
2. 대화 처리 로직은 시스템 메시지(system_msg)와 사용자 메시지(user_msg)를 분리하여 관리합니다
3. 모델 응답은 적절한 예외 처리와 함께 처리해야 합니다
4. Tool calling을 적극 활용하여 프롬프트를 줄이고 구조화된 출력을 강제합니다
5. 모듈화된 구조로 개발하여 각 컴포넌트(음성 전처리, 음성인식, LLM, TTS)를 독립적으로 개선할 수 있도록 합니다

## 주요 기술적 요소
1. **다중화자인식/구분**: 키오스크에 입력되는 노이즈(크기가 더 작은 다른 사람의 목소리)를 개선하는 기술
2. **Whisper 모델 파인튜닝/LoRA**: 식당 주문 상황에 특화된 음성인식 모델 개발
3. **Tool Calling**: LLM의 구조화된 출력을 위한 기술 적용

## 학습 데이터
### AIHub 011 고객 응대 데이터
- **데이터 위치**: 별도 서버의 `/data/aihub011/` 디렉토리
- **도메인 분류**:
  - 구매 도메인(D50): 카페(J01), 식당(J02), 의류(J03), 소매(J04)
  - 예약 도메인(D51): 숙박(J05), 학원(J06), 독서실(J07), 미용실(J08), 여행(J09)
  - 생활 도메인(D52): 민원(J10), 세탁소(J11), 옷수선(J12), 여가오락(J13), 위치정보(J14)
- **주요 활용 데이터셋**:
  - `dataset_aihub011_D50_J02`: 식당 도메인 원본 데이터셋
  - `dataset_aihub011_D50_J02_processed`: 오디오 특징 추출 완료 데이터셋
  - `dataset_aihub011_D50_J02_processed_tokenized`: 텍스트 토큰화 완료 데이터셋

### 데이터 처리 파이프라인
1. **데이터 준비** (`step1_prepare.py`): 오디오 파일(.wav)과 텍스트 파일(.txt) 경로 수집 및 HuggingFace Dataset 형태로 변환
2. **오디오 특징 추출** (`step2_audio_fe.py`): Whisper Feature Extractor를 사용하여 16kHz로 리샘플링 및 Log-Mel spectrogram 변환
3. **텍스트 토큰화** (`step3_text_tokenize.py`): Whisper Tokenizer를 사용하여 한국어 텍스트를 토큰 ID로 변환

### Whisper 파인튜닝 설정
- **베이스 모델**: `openai/whisper-base`
- **언어**: 한국어
- **평가 메트릭**: CER (Character Error Rate)
- **학습 설정**: 최대 스텝 4000, 배치 크기 192 (train), 16 (eval)

## 성능 평가
- **주요 메트릭**: CER (Character Error Rate)
- **추가 고려 메트릭**: WER (Word Error Rate), BLEU
- **도메인별 성능 비교**: 각 도메인(카페, 식당 등)별 모델 성능 분석
- **요구되는 최소 성능치**: 추후 추가 예정