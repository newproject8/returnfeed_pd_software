@echo off
chcp 65001 >nul
title ReturnFeed Issue Fixer
color 0E
echo ════════════════════════════════════════════════
echo     ReturnFeed All-in-One Issue Fixer
echo ════════════════════════════════════════════════
echo.

REM 1. MediaMTX 확인 및 시작
echo [1/5] 📡 Checking MediaMTX...
netstat -an | findstr :8890 >nul
if %errorlevel%==1 (
    echo ❌ MediaMTX not running
    echo.
    echo Starting MediaMTX...
    if exist mediamtx_local\mediamtx.exe (
        cd mediamtx_local
        start /B mediamtx.exe mediamtx.yml
        cd ..
        timeout /t 3 >nul
        echo ✅ MediaMTX started
    ) else (
        echo ⚠️  MediaMTX not installed
        echo    Run INSTALL_MEDIAMTX_SIMPLE.bat first
    )
) else (
    echo ✅ MediaMTX is running
)

REM 2. 설정 파일 수정 (localhost 사용)
echo.
echo [2/5] 🔧 Fixing configuration...
(
echo {
echo   "NDIDiscovery": {
echo     "auto_refresh": true,
echo     "refresh_interval": 2000,
echo     "show_addresses": true
echo   },
echo   "vMixTally": {
echo     "vmix_ip": "127.0.0.1",
echo     "vmix_http_port": 8088,
echo     "vmix_tcp_port": 8099,
echo     "relay_server": "localhost",
echo     "relay_port": 8765,
echo     "use_ssl": false
echo   },
echo   "SRT": {
echo     "media_mtx_server": "localhost",
echo     "srt_port": 8890,
echo     "last_bitrate": "2M",
echo     "last_fps": 30,
echo     "auto_resume_preview": true
echo   }
echo }
) > config\settings.json
echo ✅ Configuration updated to use localhost

REM 3. vMix 상태 확인
echo.
echo [3/5] 🎬 Checking vMix...
netstat -an | findstr :8099 >nul
if %errorlevel%==1 (
    echo ⚠️  vMix not running on port 8099
    echo    Please start vMix if you want to use tally features
) else (
    echo ✅ vMix is running
)

REM 4. Python 의존성 확인
echo.
echo [4/5] 📦 Checking Python dependencies...
python -c "import PyQt6" >nul 2>&1
if %errorlevel%==1 (
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt
) else (
    echo ✅ Dependencies OK
)

REM 5. 상태 요약
echo.
echo [5/5] 📊 Status Summary:
echo ════════════════════════════════════════════════
python check_system_status.py
echo ════════════════════════════════════════════════

echo.
echo 🎯 Ready to start ReturnFeed!
echo    Run: run.bat
echo.
pause