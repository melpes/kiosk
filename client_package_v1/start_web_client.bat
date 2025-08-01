@echo off
echo 🌐 웹 기반 실시간 음성 클라이언트 시작
echo =====================================
echo.

REM Python 가상환경 활성화 (있는 경우)
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 필요한 패키지 설치 확인
echo 필요한 패키지 확인 중...
pip install Flask Flask-SocketIO

REM 웹 서버 시작
echo.
echo 웹 서버 시작 중...
echo 브라우저에서 http://localhost:5000 접속하세요
echo.
python web_client.py

pause