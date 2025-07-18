@echo off
chcp 65001 >nul
title ReturnFeed Unified - Local Test Mode
color 0A
echo 🚀 Starting ReturnFeed Unified in LOCAL TEST MODE...
echo.

REM 환경 변수 설정
echo 🔧 Setting environment variables...
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false

REM 로컬 설정 파일 사용
echo 📝 Using local settings file...
if exist config\settings.json (
    move config\settings.json config\settings_backup.json >nul 2>&1
)
copy config\settings_local.json config\settings.json >nul 2>&1

REM MediaMTX 서버 확인
echo.
echo 🔍 Checking MediaMTX server...
curl -s http://localhost:9997/v3/config/get >nul 2>&1
if errorlevel 1 (
    echo ❌ MediaMTX server not running!
    echo.
    echo 로컬 MediaMTX 서버를 시작하시겠습니까? (Y/N)
    set /p START_MEDIAMTX=선택: 
    if /i "%START_MEDIAMTX%"=="Y" (
        echo.
        echo 📦 Starting local MediaMTX server...
        start "MediaMTX Server" python setup_local_mediamtx.py
        echo ⏳ Waiting for server to start...
        timeout /t 5 >nul
    )
) else (
    echo ✅ MediaMTX server is running
)

REM Python 확인
echo.
echo 🐍 Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found!
    pause
    exit /b 1
)

REM 의존성 확인
echo.
echo 📦 Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

REM 애플리케이션 시작
echo.
echo 🎯 Starting ReturnFeed Unified (Local Mode)...
echo ════════════════════════════════════════════════
echo 📌 Local Test Configuration:
echo    - WebSocket Relay: DISABLED
echo    - MediaMTX Server: localhost:8890
echo    - vMix: localhost:8099
echo ════════════════════════════════════════════════
echo.

python main.py

REM 설정 파일 복원
if exist config\settings_backup.json (
    move /y config\settings_backup.json config\settings.json >nul 2>&1
)

echo.
echo ✅ Application closed
pause