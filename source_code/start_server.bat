@echo off
REM Windows 배치 파일로 서버 실행

echo 🎤 음성 키오스크 서버 시작
echo ===========================

REM Python 가상환경 확인
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화...
    call venv\Scripts\activate.bat
)

REM 서버 실행
python start_server.py %*

pause