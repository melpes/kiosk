# 🚀 실시간 VAD 음성 키오스크 빠른 시작 가이드

## 📖 개요

이 시스템은 **실시간 VAD(Voice Activity Detection)**를 사용하여 음성이 감지되면 자동으로 서버에 전송하고 주문을 처리하는 완전한 클라이언트-서버 솔루션입니다.

## 🎯 시나리오

1. **서버**: 메인 프로젝트가 있는 컴퓨터에서 음성 처리 서버 실행
2. **클라이언트**: `client_package`만 있는 로컬에서 실시간 VAD 음성 입력
3. **자동 처리**: 음성 감지 → 자동 녹음 → 서버 전송 → 응답 받기

---

## 🖥️ 서버 측 (메인 프로젝트)

### 1. 서버 시작
```bash
# 방법 1: Python 스크립트
python start_server.py

# 방법 2: Windows 배치 파일  
start_server.bat

# 방법 3: 수동 실행
python -m src.api.cli --host 0.0.0.0 --port 8000
```

### 2. 서버 확인
- 브라우저에서 `http://localhost:8000/health` 접속
- 다음과 같은 응답이 나와야 함:
```json
{
  "status": "healthy",
  "api_initialized": true
}
```

---

## 💻 클라이언트 측 (client_package)

### 1. 패키지 설치
```bash
cd client_package
pip install -r requirements.txt
```

### 2. 서버 주소 설정
`config.json` 파일에서 서버 URL 수정:
```json
{
  "server": {
    "url": "http://서버IP주소:8000"
  }
}
```

### 3. 클라이언트 실행
```bash
# 방법 1: 간편한 스크립트 (권장)
python start_realtime_client.py

# 방법 2: Windows 배치 파일
start_realtime_client.bat

# 방법 3: 기존 run_client 사용
python run_client.py --realtime-mic

# 방법 4: 완전한 예제
python examples/complete_realtime_client.py
```

---

## 🎤 사용법

### 1. 시스템 초기화
클라이언트 실행 시 자동으로:
- ✅ 서버 연결 확인
- ✅ 마이크 하드웨어 테스트
- ✅ VAD 모델 로드
- ✅ 세션 생성

### 2. 실시간 음성 주문
```
🎤 실시간 주문 대기 중... (VAD 모드)
⏳ 상태: waiting | 볼륨:          | VAD 모드

🗣️ 음성 감지됨! 녹음 시작...
🎙️ 상태: recording | 볼륨: ████      | VAD 모드
🔇 무음이 지속되어 녹음을 종료합니다.

🔄 음성을 처리하고 서버로 전송 중...
📡 서버로 음성 전송 중...

✅ 서버 응답:
   📝 응답 텍스트: 빅맥 세트 1개를 주문해드릴게요...
```

### 3. 연속 주문
- 한 번 실행하면 계속해서 음성 입력 대기
- 새로운 음성이 감지될 때마다 자동 처리
- `Ctrl+C`로 종료

---

## 🛠️ 문제 해결

### 서버 연결 실패
```bash
❌ 서버에 연결할 수 없습니다
```
**해결:**
- 서버가 실행 중인지 확인
- `config.json`에서 서버 주소 확인
- 방화벽 설정 확인

### 마이크 테스트 실패  
```bash
❌ 마이크 테스트 실패: 하드웨어 오류
```
**해결:**
- 마이크 연결 확인
- 마이크 권한 허용
- 다른 앱에서 마이크 사용 중인지 확인

### VAD 모델 로드 실패
```bash
⚠️ VAD 폴백 모드 (볼륨 기반 감지)
```
**설명:**
- 정상적인 폴백 동작
- 볼륨 기반으로 음성 감지
- 기능에는 문제없음

---

## ⚙️ 고급 옵션

### 서버 URL 동적 변경
```bash
python start_realtime_client.py --server-url http://192.168.1.100:8000
```

### 디버그 모드
```bash
python start_realtime_client.py --verbose
```

### 사용자 정의 설정
```bash
python start_realtime_client.py --config my_config.json
```

---

## ✨ 주요 특징

| 특징 | 설명 |
|------|------|
| 🎤 **실시간 VAD** | 음성 자동 감지 및 녹음 시작/종료 |
| 📡 **즉시 전송** | 녹음 완료 즉시 서버로 전송 |
| 🔄 **연속 처리** | 한 번 실행으로 여러 주문 처리 |
| ⚠️ **폴백 모드** | VAD 실패 시 볼륨 기반 감지 |
| 📊 **실시간 통계** | 성공률, 응답시간 등 실시간 표시 |
| 🛡️ **오류 복구** | 네트워크 오류 시 자동 재시도 |

---

## 📞 지원

더 자세한 사용법은 다음 문서를 참조하세요:
- 📖 **상세 가이드**: `client_package/REALTIME_USAGE.md`
- 📚 **클라이언트 README**: `client_package/README.md`
- 🔧 **API 문서**: 서버 실행 후 `/docs` 엔드포인트

---

**🎉 이제 완전한 실시간 VAD 음성 키오스크 시스템을 사용할 수 있습니다!**