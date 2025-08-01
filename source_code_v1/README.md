# 음성 기반 키오스크 AI 주문 시스템

음성인식과 자연어 처리를 활용한 식당 키오스크 시스템입니다. 사용자의 음성 입력을 분석하여 주문, 변경, 취소, 결제 등의 의도를 파악하고 음성으로 응답을 제공합니다.

## 🎯 주요 기능

- **음성 전처리**: 다중화자인식/구분을 통한 노이즈 개선
- **음성인식**: Whisper 기반 모델을 파인튜닝하여 사용자 음성을 텍스트로 변환
- **대화 처리**: OpenAI의 GPT 모델을 활용한 멀티턴 대화 처리
- **주문 관리**: 주문 추가, 변경, 취소 및 결제 처리
- **음성 응답**: TTS를 통한 음성 응답 제공
- **자동화된 테스트 시스템**: 맥도날드 특화 테스트케이스 생성 및 실행
- **실시간 마이크 입력**: VAD 기반 실시간 음성 입력 처리

## 📁 프로젝트 구조

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
├── tests/                   # 테스트 코드 (모든 테스트 파일 통합)
├── demos/                   # 데모 및 디버그 스크립트 (모든 데모/디버그 파일 통합)
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

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd voice_kiosk

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일을 편집하여 OpenAI API 키 설정
# OPENAI_API_KEY=your_actual_api_key_here
```

### 3. 실행

#### 팀원용 빠른 테스트
```bash
# 초간단 테스트 (30초)
python test.py

# 기본 시스템 테스트 (API 키 불필요)
python src/simple_debug.py
```

#### 전체 시스템 실행
```bash
# 메인 시스템 실행
python src/main.py

# CLI 인터페이스 실행
python src/cli/interface.py
```

## 🎬 데모 및 테스트 실행

### 팀원용 빠른 테스트 (권장)
```bash
# 🔥 가장 안전한 테스트 도구 (EOF 오류 해결됨, 추천)
python run_debug_safe.py

# 30초 초간단 테스트 (개선됨)
python test.py

# 기본 시스템 테스트 (API 키 불필요, 안전함)
python src/simple_debug.py

# API 키 인식 확인
python simple_api_test.py

# 기존 도구들 (EOF 오류 수정됨)
python run_debug.py
python src/debug_main.py --mode text --input "빅맥 주문" --debug
```

**✅ 업데이트**: EOF 오류 문제가 해결되었습니다! 모든 도구를 안전하게 사용할 수 있습니다.  
**⚠️ 참고**: OpenAI 클라이언트 이슈로 API 키 기능은 제한적이지만, 기본 시스템은 완벽하게 작동합니다.  
**📚 중요**: 전체 시스템 정보는 [UNIFIED_DOCUMENTATION.md](UNIFIED_DOCUMENTATION.md)에서 확인하세요!

### 전체 데모 실행
```bash
# 모든 데모 실행
python demos/run_all_demos.py

# 개별 데모 실행
python demos/demo_main_pipeline.py      # 메인 파이프라인 데모
python demos/demo_text_response.py      # 텍스트 응답 시스템 데모
python demos/demo_error_handling.py     # 오류 처리 시스템 데모
python demos/demo_config_management.py  # 설정 관리 시스템 데모
python demos/demo_cli_simple.py         # 간단한 CLI 데모
```

## 🧪 테스트 실행

```bash
# 모든 단위 테스트 실행
python -m pytest tests/ -v

# 모든 통합 테스트 실행
python tests/integration/run_all_integration_tests.py

# 개별 통합 테스트 실행
python tests/integration/test_main_integration.py
python tests/integration/test_config_integration.py
```

## ⚙️ 설정

### API 키 설정

**API 키 설정 (.env 파일)**
```bash
# .env 파일을 편집하여 실제 API 키 입력
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 테스트 설정

**테스트 관련 환경 변수 (.env 파일)**
```bash
# 테스트 설정
TEST_MAX_TESTS_PER_CATEGORY=20          # 카테고리당 최대 테스트 수 (기본값: 20)
TEST_DELAY_BETWEEN_REQUESTS=2.0         # API 요청 간 지연시간 (초) (기본값: 2.0)
TEST_INCLUDE_SLANG=true                 # 은어 테스트 포함 여부 (기본값: true)
TEST_INCLUDE_INFORMAL=true              # 반말 테스트 포함 여부 (기본값: true)
TEST_INCLUDE_COMPLEX=true               # 복합 의도 테스트 포함 여부 (기본값: true)
TEST_INCLUDE_EDGE_CASES=true            # 엣지 케이스 포함 여부 (기본값: true)

# 마이크 설정
MIC_VAD_THRESHOLD=0.25                  # VAD 임계값 (기본값: 0.25)
MIC_SAMPLE_RATE=16000                   # 샘플링 레이트 (기본값: 16000)
MIC_CHUNK_SIZE=1024                     # 청크 크기 (기본값: 1024)

# 로깅 설정
LOG_LEVEL=INFO                          # 로그 레벨 (기본값: INFO)
LOG_FILE=voice_kiosk.log                # 로그 파일명 (기본값: voice_kiosk.log)
```

**📝 테스트 설정 설명:**
- `TEST_MAX_TESTS_PER_CATEGORY`: 각 카테고리(은어, 반말, 복합 의도 등)당 생성할 최대 테스트 수
- `TEST_DELAY_BETWEEN_REQUESTS`: OpenAI API 속도 제한 방지를 위한 요청 간 지연시간
- `TEST_INCLUDE_*`: 특정 카테고리의 테스트 포함 여부 설정

자세한 내용은 [UNIFIED_DOCUMENTATION.md](UNIFIED_DOCUMENTATION.md)의 "설치 및 설정" 섹션을 참조하세요.

### 메뉴 설정

`config/menu_config.json` 파일에서 메뉴 항목, 가격, 옵션 등을 설정할 수 있습니다.

## 🔧 개발

### 코딩 스타일

- Python 3.8+ 사용
- PEP 8 스타일 가이드 준수
- 타입 힌트 사용 권장
- 한국어 주석 및 문서화

### 새로운 기능 추가

1. `src/` 디렉토리에 모듈 추가
2. `tests/` 디렉토리에 테스트 코드 작성
3. `demos/` 디렉토리에 데모 스크립트 작성 (선택사항)

## 📚 문서

### 📖 통합 문서 (권장)
- **[UNIFIED_DOCUMENTATION.md](UNIFIED_DOCUMENTATION.md)** 📚 **전체 시스템 가이드 (모든 정보 통합)**

이 통합 문서에는 다음 모든 내용이 포함되어 있습니다:
- 🚀 빠른 시작 가이드 (30초 시작)
- 📋 설치 및 설정 가이드
- 📚 사용법 및 API 문서
- 🔧 설정 관리 및 문제 해결
- 🧪 테스트 시스템 및 마이크 입력
- 🎯 개발 가이드 및 FAQ

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🔍 문제 해결

### 일반적인 문제

1. **API 키 오류**: `.env` 파일에 올바른 OpenAI API 키가 설정되어 있는지 확인
2. **API 속도 제한**: `TEST_DELAY_BETWEEN_REQUESTS` 값을 늘려서 요청 간 지연시간을 조정
3. **테스트 개수 조정**: `TEST_MAX_TESTS_PER_CATEGORY` 값을 조정하여 테스트 개수 변경
4. **모듈 import 오류**: Python 경로가 올바르게 설정되어 있는지 확인
5. **설정 파일 오류**: `config/` 디렉토리의 JSON 파일들이 올바른 형식인지 확인

### 로그 확인

```bash
# 로그 파일 확인
tail -f logs/voice_kiosk.log
```

### 디버그 모드

```bash
# 디버그 모드로 실행
LOG_LEVEL=DEBUG python src/main.py
```

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해 주세요.