@echo off
REM Windows 배치 파일로 실시간 클라이언트 실행

echo 🚀 실시간 VAD 음성 클라이언트 시작
echo =====================================

REM Python 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화...
    call venv\Scripts\activate.bat
)

REM 실시간 클라이언트 실행
python start_realtime_client.py %*

pause