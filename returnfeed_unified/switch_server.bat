@echo off
chcp 65001 >nul
title Server Configuration Switcher
color 0E

echo ════════════════════════════════════════════════
echo    ReturnFeed Server Configuration Switcher
echo ════════════════════════════════════════════════
echo.
echo 현재 설정을 확인하는 중...

REM 현재 설정 확인
findstr /C:"localhost" config\settings.json >nul
if %errorlevel%==0 (
    echo 📍 현재 설정: LOCAL (localhost)
    set CURRENT=local
) else (
    echo 📍 현재 설정: REMOTE (returnfeed.net)
    set CURRENT=remote
)

echo.
echo 어느 서버를 사용하시겠습니까?
echo.
echo [1] 🏠 Local Server (localhost:8890)
echo [2] 🌐 Remote Server (returnfeed.net:8890)
echo [3] ❌ Cancel
echo.
set /p CHOICE=선택 (1-3): 

if "%CHOICE%"=="1" (
    echo.
    echo 🔄 로컬 서버로 전환 중...
    copy /Y config\settings_local.json config\settings.json >nul
    echo ✅ 로컬 서버 설정 완료!
    echo.
    echo 📌 MediaMTX 로컬 서버가 필요합니다.
    echo    start_local_mediamtx.bat 을 실행하세요.
) else if "%CHOICE%"=="2" (
    echo.
    echo 🔄 원격 서버로 전환 중...
    
    REM 원격 설정 파일 생성
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
    echo     "relay_server": "returnfeed.net",
    echo     "relay_port": 443,
    echo     "use_ssl": true
    echo   },
    echo   "SRT": {
    echo     "media_mtx_server": "returnfeed.net",
    echo     "srt_port": 8890,
    echo     "last_bitrate": "2M",
    echo     "last_fps": 30,
    echo     "auto_resume_preview": true
    echo   }
    echo }
    ) > config\settings.json
    
    echo ✅ 원격 서버 설정 완료!
) else (
    echo.
    echo ❌ 취소되었습니다.
)

echo.
pause