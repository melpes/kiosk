# 웹 기반 실시간 음성 클라이언트 사용법

## 개요
기존 CLI 기반의 `start_realtime_client.py`를 웹 인터페이스로 변환한 버전입니다.
브라우저에서 간편하게 실시간 음성 인식 및 응답 시스템을 사용할 수 있습니다.

## 빠른 시작

### 1. 웹 서버 실행
```bash
# Windows
start_web_client.bat

# 또는 직접 실행
python web_client.py
```

### 2. 브라우저 접속
- http://localhost:5000 접속
- 웹 인터페이스에서 모든 기능 사용 가능

## 주요 기능

### 🎤 실시간 음성 세션
- **세션 시작**: 실시간 음성 인식 시작
- **세션 중지**: 현재 세션 종료
- **실시간 상태 표시**: 연결 상태 및 세션 상태 실시간 업데이트

### ⚙️ 설정 관리
- **서버 URL 변경**: 웹에서 직접 서버 주소 변경
- **실시간 설정 저장**: 변경사항 즉시 적용

### 📋 실시간 로그
- **음성 인식 결과**: 실시간 텍스트 변환 결과 및 신뢰도 표시
- **서버 응답**: AI 응답 내용 실시간 표시
- **TTS 음성 재생**: 서버에서 받은 음성 파일 자동 재생
- **시스템 상태**: 연결, 오류, 경고 메시지
- **처리 상태**: 음성 처리 진행 상황 표시

### 🔊 TTS 음성 재생
- **자동 재생**: 서버에서 TTS 음성 수신 시 자동 재생
- **수동 제어**: 오디오 플레이어로 재생/일시정지 제어
- **다중 재생**: 여러 음성 파일 동시 관리

### 📡 서버 정보 표시
- **실시간 연결 상태**: 서버 연결 여부 실시간 모니터링
- **서버 URL**: 현재 연결된 서버 주소 표시
- **마지막 응답 시간**: 최근 서버 응답 시각 표시
- **자동 상태 확인**: 10초마다 서버 상태 자동 확인

## 웹 인터페이스 구성

### 상단 헤더
- 애플리케이션 제목 및 설명

### 상태 표시
- 🟢 **연결됨**: 세션이 활성화된 상태
- 🔴 **연결 안됨**: 세션이 비활성화된 상태

### 제어 버튼
- **🚀 세션 시작**: 실시간 음성 인식 시작
- **⏹️ 세션 중지**: 현재 세션 종료

### 설정 섹션
- **서버 URL**: 음성 처리 서버 주소 설정
- **설정 저장**: 변경사항 config.json에 저장

### 로그 섹션
- **실시간 로그**: 모든 시스템 활동 실시간 표시
- **자동 스크롤**: 새 로그 자동으로 하단 표시
- **로그 타입별 색상**: 정보, 오류, 경고, 인식, 응답, 오디오 구분
- **신뢰도 바**: 음성 인식 신뢰도 시각적 표시
- **TTS 플레이어**: 음성 파일 인라인 재생 컨트롤

## 기술 스택

### 백엔드
- **Flask**: 웹 서버 프레임워크
- **Flask-SocketIO**: 실시간 양방향 통신
- **기존 클라이언트**: CompleteRealTimeClient 재사용

### 프론트엔드
- **HTML5**: 웹 인터페이스 구조
- **CSS3**: 반응형 디자인 및 스타일링
- **Socket.IO**: 실시간 통신 클라이언트
- **Vanilla JavaScript**: 동적 기능 구현

## 설정 파일 (config.json)
웹 클라이언트는 기존 `config.json` 파일을 그대로 사용합니다:

```json
{
  "server": {
    "url": "http://localhost:8001"
  },
  "audio": {
    "temp_dir": "temp_audio"
  }
}
```

## 포트 설정
- **웹 서버**: 5000번 포트 (기본값)
- **음성 처리 서버**: config.json에서 설정된 포트

## 브라우저 호환성
- Chrome, Firefox, Safari, Edge 최신 버전 지원
- WebSocket 지원 필요

## 문제 해결

### 웹 서버가 시작되지 않는 경우
```bash
pip install Flask Flask-SocketIO
```

### 음성 서버 연결 실패
1. 음성 처리 서버가 실행 중인지 확인
2. config.json의 서버 URL 확인
3. 방화벽 설정 확인

### 마이크 권한 문제
- 브라우저에서 마이크 권한 허용 필요
- HTTPS 환경에서 더 안정적 동작

## CLI vs 웹 버전 비교

| 기능 | CLI 버전 | 웹 버전 |
|------|----------|---------|
| 실행 방식 | 터미널 | 브라우저 |
| 사용자 인터페이스 | 텍스트 기반 | 그래픽 기반 |
| 실시간 로그 | 터미널 출력 | 웹 페이지 |
| 설정 변경 | 파일 수정 | 웹에서 직접 |
| 다중 사용자 | 불가능 | 가능 |
| 원격 접속 | 불가능 | 가능 |

## 향후 개선 사항
- [ ] 음성 파일 업로드 기능
- [ ] 설정 내보내기/가져오기
- [ ] 사용자 인증 시스템
- [ ] 세션 기록 저장
- [ ] 다국어 지원
- [ ] 모바일 최적화