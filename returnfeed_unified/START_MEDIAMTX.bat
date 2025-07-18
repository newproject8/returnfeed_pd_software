@echo off
title MediaMTX Server
color 0A
echo ════════════════════════════════════════════════
echo          MediaMTX Local Server Manager
echo ════════════════════════════════════════════════
echo.

REM 포트 사용 확인
echo 📍 Checking if MediaMTX is already running...
netstat -an | findstr :8890 >nul
if %errorlevel%==0 (
    echo ✅ MediaMTX seems to be running (port 8890 is in use)
    echo.
    echo Press any key to check status...
    pause >nul
    python check_mediamtx.py
    echo.
    pause
    exit /b
)

echo ❌ MediaMTX is not running
echo.
echo Starting MediaMTX server...
echo.

REM MediaMTX 실행 파일 확인
if not exist "mediamtx_local\mediamtx.exe" (
    echo 📦 MediaMTX not found. Installing...
    python setup_local_mediamtx.py
    if errorlevel 1 (
        echo ❌ Installation failed
        pause
        exit /b 1
    )
)

REM MediaMTX 시작
echo 🚀 Starting MediaMTX...
cd mediamtx_local
start /B mediamtx.exe mediamtx.yml
cd ..

REM 시작 확인
timeout /t 2 >nul
netstat -an | findstr :8890 >nul
if %errorlevel%==0 (
    echo ✅ MediaMTX started successfully!
    echo.
    echo 📡 Server is running on:
    echo    - SRT port: 8890
    echo    - API port: 9997
    echo.
    echo Press any key to check status...
    pause >nul
    python check_mediamtx.py
) else (
    echo ❌ Failed to start MediaMTX
    echo Check mediamtx_local\mediamtx.log for errors
)

echo.
pause