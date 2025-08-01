@echo off
echo 🌐 간단 웹 클라이언트 시작
echo ========================
echo.

REM Python 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 웹 서버 시작
echo 웹 서버 시작 중...
echo 브라우저에서 http://localhost:5000 접속하세요
echo.
python web_client_simple.py

pause