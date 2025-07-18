@echo off
chcp 65001 >nul
title ReturnFeed Unified
color 0A

echo 🚀 Starting ReturnFeed Unified Application...
echo.

REM Python 3.10 명시적 사용
set PYTHON_PATH=C:\Users\newproject_user\AppData\Local\Programs\Python\Python310\python.exe

REM Python 확인
echo 🐍 Using Python 3.10...
"%PYTHON_PATH%" --version
echo.

REM 환경 변수 설정
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false
echo ✅ Environment variables set
echo.

REM 작업 디렉토리 설정
cd /d "%~dp0"
echo 📂 Working directory: %CD%
echo.

REM FFmpeg 경로 추가 (로컬 설치된 경우)
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    set PATH=%~dp0ffmpeg\bin;%PATH%
    echo ✅ Local FFmpeg added to PATH
)

REM main.py 실행
echo 🎯 Starting application...
echo ════════════════════════════════════════════════
echo.

"%PYTHON_PATH%" main.py

echo.
echo ════════════════════════════════════════════════
echo Exit code: %ERRORLEVEL%
echo.

pause