# 키오스크 클라이언트 배포 패키지

이 패키지는 음성 키오스크 클라이언트를 독립적으로 실행할 수 있도록 구성된 배포 패키지입니다.

## 패키지 구성

```
client_package/
├── README.md                    # 이 파일
├── requirements.txt             # 클라이언트 의존성
├── config.json                  # 클라이언트 설정
├── install.py                   # 설치 스크립트
├── run_client.py               # 클라이언트 실행 스크립트
├── client/                     # 클라이언트 소스 코드
│   ├── __init__.py
│   ├── voice_client.py         # 음성 클라이언트
│   ├── ui_manager.py           # UI 관리자
│   ├── config_manager.py       # 설정 관리자
│   └── models/                 # 데이터 모델
│       ├── __init__.py
│       └── communication_models.py
├── utils/                      # 유틸리티
│   ├── __init__.py
│   ├── logger.py              # 로깅 유틸리티
│   └── audio_utils.py         # 오디오 유틸리티
└── examples/                   # 사용 예제
    ├── basic_client.py         # 기본 클라이언트 예제
    ├── demo_client.py          # 데모 클라이언트
    └── test_audio/             # 테스트 오디오 파일
```

## 설치 방법

### 1. 자동 설치 (권장)

```bash
# 패키지 디렉토리로 이동
cd client_package

# 자동 설치 실행
python install.py
```

### 2. 수동 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 설정 파일 확인 및 수정
# config.json 파일에서 서버 URL 등을 확인하세요
```

## 실행 방법

### 1. 기본 실행

```bash
# 기본 데모 실행
python run_client.py

# 또는
python run_client.py --demo

# Windows 배치 파일 사용
run_client.bat --demo
```

### 2. 특정 음성 파일 전송

```bash
# 음성 파일 지정하여 실행
python run_client.py --audio-file path/to/audio.wav

# Windows
run_client.bat --audio-file path\to\audio.wav
```

### 3. 서버 URL 지정

```bash
# 다른 서버 URL 사용
python run_client.py --server-url http://192.168.1.100:8000
```

### 4. 설정 파일 사용

```bash
# 사용자 정의 설정 파일 사용
python run_client.py --config my_config.json
```

### 5. 실시간 마이크 입력 모드 (NEW!)

```bash
# 실시간 마이크 입력 모드 실행
python run_client.py --realtime-mic

# 또는 예제 스크립트 사용
python examples/realtime_mic_example.py
```

**새로운 기능:**
- 🎤 **실시간 마이크 입력**: VAD(Voice Activity Detection)를 통한 자동 음성 감지
- 🗣️ **자동 녹음 시작/종료**: 음성이 감지되면 자동으로 녹음 시작, 무음이 지속되면 자동 종료
- 📡 **즉시 서버 전송**: 녹음 완료 즉시 서버로 자동 전송
- 🔄 **연속 처리**: 한 번의 실행으로 여러 번의 주문 처리 가능
- ⚠️ **폴백 모드**: VAD 실패 시 볼륨 기반 감지로 자동 전환

**사용 방법:**
1. 실시간 마이크 모드 실행
2. 마이크에 대고 주문 내용 말하기 (예: "빅맥 세트 하나 주세요")
3. 음성 감지되면 자동 녹음 시작
4. 말을 마치면 자동으로 녹음 종료 및 서버 전송
5. 서버 응답을 실시간으로 확인
6. 계속해서 추가 주문 가능

### 6. 추가 옵션

```bash
# 서버 상태 확인
python run_client.py --check-health

# 현재 설정 표시
python run_client.py --show-config

# 상세 로그 출력
python run_client.py --demo --verbose

# TTS 자동 재생 비활성화
python run_client.py --demo --no-auto-play
```

## 설정 파일 (config.json)

```json
{
  "server": {
    "url": "http://localhost:8000",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1.0
  },
  "audio": {
    "max_file_size": 10485760,
    "supported_formats": [".wav"],
    "temp_dir": "temp_audio"
  },
  "ui": {
    "auto_play_tts": true,
    "show_detailed_logs": false,
    "language": "ko"
  },
  "logging": {
    "level": "INFO",
    "file": "client.log",
    "max_size": 1048576,
    "backup_count": 3
  }
}
```

## 사용 예제

### Python 코드에서 사용

```python
from client.voice_client import VoiceClient
from client.config_manager import ConfigManager

# 설정 로드
config = ConfigManager.load_config("config.json")

# 클라이언트 생성
client = VoiceClient(config)

# 음성 파일 전송
response = client.send_audio_file("test.wav")

# 응답 처리
client.handle_response(response)

# 클라이언트 종료
client.close()
```

### 명령줄에서 사용

```bash
# 데모 실행
python run_client.py --demo

# 특정 파일 전송
python run_client.py --audio-file recording.wav

# 서버 상태 확인
python run_client.py --check-health

# 설정 확인
python run_client.py --show-config
```

## 문제 해결

### 1. 서버 연결 실패

```bash
# 서버 상태 확인
python run_client.py --check-health

# 네트워크 연결 확인
ping [서버 IP]

# 방화벽 설정 확인
```

### 2. 음성 파일 처리 실패

- 지원되는 파일 형식: WAV
- 최대 파일 크기: 10MB
- 샘플링 레이트: 16kHz 권장

### 3. 의존성 오류

```bash
# 의존성 재설치
pip install -r requirements.txt --force-reinstall

# 가상환경 사용 권장
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 로그 확인

클라이언트 실행 로그는 다음 위치에 저장됩니다:

- 기본 로그 파일: `client.log`
- 설정에서 변경 가능: `config.json`의 `logging.file`

```bash
# 실시간 로그 확인
tail -f client.log

# 오류 로그만 확인
grep ERROR client.log
```

## 업데이트

새 버전의 클라이언트가 출시되면:

1. 새 패키지를 다운로드
2. 기존 설정 파일 백업
3. 새 패키지로 교체
4. 설정 파일 복원
5. 의존성 업데이트: `pip install -r requirements.txt --upgrade`

## 지원 및 문의

- 문제 발생 시 로그 파일과 함께 문의
- 서버 관리자에게 연결 정보 확인
- 네트워크 환경 및 방화벽 설정 확인

## 라이선스

이 소프트웨어는 [라이선스 정보]에 따라 배포됩니다.