# 음성 통신 통합 테스트

이 디렉토리는 실시간 음성 통신 기능의 통합 테스트를 포함합니다.

## 테스트 개요

### 테스트 범위
- **기본 통신 플로우**: 클라이언트-서버 간 음성 파일 전송 및 응답 처리
- **다양한 파일 형식**: WAV 파일 형식 지원 및 검증
- **오류 복구**: 네트워크 오류, 서버 오류, 타임아웃 등 다양한 오류 시나리오
- **성능 요구사항**: 3초 이내 응답 시간 보장
- **동시 요청 처리**: 다중 클라이언트 동시 접속 처리
- **보안 기능**: 파일 크기 제한, 형식 검증 등
- **모니터링**: 요청 추적, 성능 메트릭 수집

### Requirements 매핑
- **2.1, 2.2**: 실시간 처리 및 성능 요구사항
- **3.1, 3.2, 3.3, 3.4**: 오류 처리 및 복구 메커니즘
- **6.1, 6.2, 6.3, 6.4**: 로깅 및 모니터링

## 파일 구조

```
tests/integration/
├── test_voice_communication.py          # 메인 통합 테스트
├── test_voice_communication_runner.py   # 테스트 실행기
├── test_voice_communication_utils.py    # 테스트 유틸리티
├── run_voice_communication_tests.py     # 실행 스크립트
└── README.md                            # 이 파일
```

## 테스트 실행 방법

### 1. 전체 테스트 실행
```bash
# Python으로 실행
python tests/integration/run_voice_communication_tests.py

# 또는 pytest 직접 실행
pytest tests/integration/test_voice_communication.py -v
```

### 2. 특정 테스트 카테고리 실행
```bash
# 기본 통신 테스트
python tests/integration/run_voice_communication_tests.py basic

# 파일 형식 테스트
python tests/integration/run_voice_communication_tests.py format

# 오류 복구 테스트
python tests/integration/run_voice_communication_tests.py error

# 성능 테스트
python tests/integration/run_voice_communication_tests.py performance

# 통합 테스트
python tests/integration/run_voice_communication_tests.py integration

# 스트레스 테스트
python tests/integration/run_voice_communication_tests.py stress
```

### 3. 테스트 보고서 생성
```bash
# HTML 보고서 생성 (pytest-html 필요)
python tests/integration/run_voice_communication_tests.py report
```

### 4. 개별 테스트 실행
```bash
# 특정 테스트 함수 실행
pytest tests/integration/test_voice_communication.py::TestVoiceCommunicationIntegration::test_basic_voice_communication_flow -v

# 패턴으로 테스트 선택
pytest tests/integration/test_voice_communication.py -k "performance" -v
```

## 테스트 클래스

### TestVoiceCommunicationIntegration
메인 통합 테스트 클래스로 다음 테스트를 포함합니다:

- `test_basic_voice_communication_flow`: 기본 통신 플로우
- `test_session_continuity`: 세션 연속성
- `test_various_audio_file_formats`: 다양한 파일 형식 지원
- `test_invalid_file_format_handling`: 잘못된 파일 형식 처리
- `test_error_recovery_scenarios`: 오류 복구 시나리오
- `test_performance_requirements`: 성능 요구사항 (3초 이내)
- `test_concurrent_request_handling`: 동시 요청 처리
- `test_tts_file_download`: TTS 파일 다운로드
- `test_client_retry_mechanism`: 클라이언트 재시도 메커니즘
- `test_server_monitoring_integration`: 서버 모니터링 통합
- `test_security_integration`: 보안 기능 통합
- `test_end_to_end_workflow`: 전체 워크플로우 종단간 테스트

### TestVoiceCommunicationStress
스트레스 테스트 클래스:

- `test_high_load_scenario`: 고부하 시나리오 (50개 동시 요청)

## 테스트 환경 설정

### 필수 의존성
```bash
pip install pytest requests fastapi uvicorn
```

### 선택적 의존성 (보고서 생성용)
```bash
pip install pytest-html pytest-cov
```

### 환경 변수
테스트 실행 시 다음 환경 변수가 자동으로 설정됩니다:
- `TESTING=true`
- `TTS_PROVIDER=mock`
- `MAX_FILE_SIZE_MB=10`
- `RATE_LIMIT_REQUESTS=1000`

## 테스트 데이터

테스트는 다음과 같은 임시 데이터를 자동 생성합니다:
- 다양한 길이의 WAV 파일 (0.5초 ~ 3초)
- 다양한 샘플링 레이트 (16kHz, 22kHz, 44kHz)
- 잘못된 형식의 파일 (빈 파일, 텍스트 파일, 큰 파일)

모든 임시 파일은 테스트 완료 후 자동으로 정리됩니다.

## 성능 기준

### 응답 시간
- **최대 응답 시간**: 3초
- **평균 응답 시간**: 2초 이하 권장
- **동시 요청 시**: 5초 이하

### 성공률
- **일반 요청**: 95% 이상
- **동시 요청**: 80% 이상
- **고부하 상황**: 70% 이상

### 처리량
- **최소 처리량**: 5 req/s
- **권장 처리량**: 10 req/s 이상

## 모니터링 및 로깅

테스트 실행 중 다음 로그가 생성됩니다:
- `logs/voice_client.log`: 클라이언트 모니터링 로그
- `logs/voice_kiosk.log`: 서버 로그
- `test_results/reports/`: 테스트 보고서

## 문제 해결

### 일반적인 문제

1. **서버 연결 실패**
   - 서버가 실행 중인지 확인
   - 포트 8000이 사용 가능한지 확인

2. **파일 권한 오류**
   - 임시 디렉토리 쓰기 권한 확인
   - logs/ 디렉토리 생성 권한 확인

3. **의존성 오류**
   - requirements.txt의 모든 패키지 설치 확인
   - Python 버전 호환성 확인 (3.8+)

### 디버깅

상세한 로그를 보려면:
```bash
pytest tests/integration/test_voice_communication.py -v -s --log-cli-level=DEBUG
```

특정 테스트만 디버깅:
```bash
pytest tests/integration/test_voice_communication.py::test_function_name -v -s --pdb
```

## 기여 가이드

새로운 테스트를 추가할 때:

1. `TestVoiceCommunicationIntegration` 클래스에 메서드 추가
2. Requirements 주석으로 요구사항 매핑
3. 적절한 assert 문으로 검증
4. 임시 파일 정리 코드 포함
5. 로깅으로 테스트 진행 상황 기록

테스트 명명 규칙:
- `test_[기능]_[시나리오]` 형식 사용
- 명확하고 설명적인 이름 사용
- docstring으로 테스트 목적 설명