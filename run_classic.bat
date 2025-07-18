@echo off
chcp 65001 >nul
title ReturnFeed Classic Mode - Professional NDI Monitor
color 0A

echo.
echo ============================================================
echo.
echo     ReturnFeed Classic Mode v2.3 - Professional NDI Monitor
echo.
echo         Single-Channel Focus - Modern Dark Theme
echo.
echo ============================================================
echo.

REM Set environment variables for stability
echo 🔧 Configuring optimal environment...
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false
echo ✅ Environment configured for maximum stability
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    echo Download from: https://python.org
    pause
    exit /b 1
)

echo ✅ Python found: 
python --version
echo.

REM Check FFmpeg
echo 🔍 Checking FFmpeg...
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%~dp0ffmpeg\bin;%PATH%"
    echo ✅ FFmpeg found (local installation)
) else (
    ffmpeg -version >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  FFmpeg not found - 리턴피드 스트리밍 will not be available
    ) else (
        echo ✅ FFmpeg found (system installation)
    )
)
echo.

REM Check dependencies
echo 📦 Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing required packages...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
)
echo ✅ All dependencies verified
echo.

REM Change to returnfeed_unified directory
cd /d "%~dp0returnfeed_unified"

REM Launch Classic Mode
echo ================================================================
echo.
echo 🚀 Launching ReturnFeed Classic Mode v2.3...
echo.
echo 📌 Features:
echo    • Single NDI channel monitoring (60fps)
echo    • Professional broadcast interface (Adobe Premiere style)
echo    • Real-time tally display (8.3ms response)
echo    • 리턴피드 스트리밍 support with unique URLs
echo    • Smart focus system and animations
echo    • Dynamic bitrate calculation
echo.
echo ================================================================
echo.

REM Run Classic Mode
python main_classic.py 2>&1

if errorlevel 1 (
    echo.
    echo ❌ Application exited with error
    echo.
    echo 🔧 Troubleshooting:
    echo    1. Ensure NDI SDK is installed
    echo    2. Check if vMix is running (for tally)
    echo    3. Verify network connectivity
    echo    4. Check logs folder for details
    echo.
) else (
    echo.
    echo ✅ Thank you for using ReturnFeed Classic Mode v2.3!
)

pause