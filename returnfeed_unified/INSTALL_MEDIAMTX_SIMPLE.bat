@echo off
title MediaMTX Quick Installer
color 0A
echo ════════════════════════════════════════════════
echo        MediaMTX Quick Installation
echo ════════════════════════════════════════════════
echo.

REM 디렉토리 생성
echo 📁 Creating directory...
if not exist mediamtx_local mkdir mediamtx_local
cd mediamtx_local

REM 다운로드 URL
set URL=https://github.com/bluenviron/mediamtx/releases/download/v1.4.0/mediamtx_v1.4.0_windows_amd64.zip
set FILE=mediamtx.zip

REM 다운로드
echo 📥 Downloading MediaMTX...
echo    This may take a few minutes...
echo.
powershell -Command "Invoke-WebRequest -Uri '%URL%' -OutFile '%FILE%' -UseBasicParsing"

if not exist %FILE% (
    echo ❌ Download failed!
    echo.
    echo Please download manually from:
    echo https://github.com/bluenviron/mediamtx/releases
    echo.
    cd ..
    pause
    exit /b 1
)

REM 압축 해제
echo 📦 Extracting files...
powershell -Command "Expand-Archive -Path '%FILE%' -DestinationPath '.' -Force"

REM 설정 파일 생성
echo 📝 Creating configuration...
(
echo # MediaMTX Configuration
echo logLevel: info
echo logDestinations: [stdout, file]
echo logFile: mediamtx.log
echo 
echo api: yes
echo apiAddress: :9997
echo 
echo # SRT server
echo srt: yes
echo srtAddress: :8890
echo 
echo # Disable other protocols
echo rtsp: no
echo rtmp: no
echo hls: no
echo webrtc: no
echo 
echo # Path configuration
echo paths:
echo   all:
echo     source: publisher
echo     srtReadTimeout: 10s
echo     srtWriteTimeout: 10s
) > mediamtx.yml

echo ✅ Installation complete!
echo.
echo 📡 MediaMTX is ready to run
echo    Use START_MEDIAMTX.bat to start the server
echo.
cd ..
pause