@echo off
chcp 65001 >nul
title ReturnFeed Unified
color 0A

echo 🚀 Starting ReturnFeed Unified Application...
echo.

REM 환경 변수 설정
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false
echo ✅ Environment variables set
echo.

REM Python 버전 확인
echo 🐍 Checking Python...
python --version
echo.

REM 작업 디렉토리 설정
cd /d "%~dp0"
echo 📂 Working directory: %CD%
echo.

REM main.py 실행
echo 🎯 Starting application...
echo ════════════════════════════════════════════════
echo.

python main.py

echo.
echo ════════════════════════════════════════════════
echo Exit code: %ERRORLEVEL%
echo.

pause