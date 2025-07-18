@echo off
chcp 65001 >nul
title ReturnFeed Unified
color 0A
echo 🚀 Starting ReturnFeed Unified Application...
echo.

REM 🚀 ULTRATHINK 크래시 해결: 환경 변수 설정
echo 🔧 Setting environment variables for NDI stability...
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false
echo ✅ OpenGL backend forced (WSL2 compatibility)
echo ✅ FFmpeg multimedia backend set
echo ✅ Qt logging optimized for performance
echo.

REM Check if Python is installed
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

REM Check FFmpeg installation
echo.
echo 🔍 Checking FFmpeg...

REM Check local FFmpeg first
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%~dp0ffmpeg\bin;%PATH%"
    echo ✅ FFmpeg found (local installation)
) else (
    REM Check system FFmpeg
    ffmpeg -version >nul 2>&1
    if errorlevel 1 (
        echo ⚠️  WARNING: FFmpeg not found!
        echo.
        echo FFmpeg를 자동으로 설치하시겠습니까? (Y/N)
        set /p INSTALL_FFMPEG=선택: 
        if /i "%INSTALL_FFMPEG%"=="Y" (
            echo.
            echo 📦 FFmpeg 설치를 시작합니다...
            call "%~dp0install_ffmpeg_portable.bat"
            echo.
            echo 🔄 run.bat을 다시 실행해주세요.
            pause
            exit /b 0
        ) else (
            echo.
            echo 📌 SRT 스트리밍을 사용하려면 FFmpeg가 필요합니다.
            echo    나중에 install_ffmpeg_portable.bat을 실행하여 설치할 수 있습니다.
        )
    ) else (
        echo ✅ FFmpeg found (system installation)
    )
)

REM Check if required packages are installed
echo.
echo 📦 Checking dependencies...
"python" -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PyQt6 not found. Installing required packages...
    "python" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
) else (
    echo ✅ PyQt6 found
)

REM Check additional dependencies
"python" -c "import ffmpeg" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing additional packages...
    "python" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install additional dependencies  
        echo SRT streaming may not work properly
    ) else (
        echo ✅ Additional dependencies installed
    )
) else (
    echo ✅ All dependencies verified
)

REM Ensure we're in the correct directory
cd /d "%~dp0"

REM Run the application
echo.
echo 🎯 Starting ReturnFeed Unified Application...
echo ════════════════════════════════════════════════
echo.
echo 🚀 ULTRATHINK Crash Prevention Mode Enabled:
echo   - QPainter Direct Rendering (No QVideoSink)
echo   - Bulletproof Memory Management
echo   - Real-time Performance Monitoring
echo ════════════════════════════════════════════════
echo.
echo 📂 Working directory: %CD%
echo.

REM Check if main.py exists
if not exist "main.py" (
    echo.
    echo ❌ ERROR: main.py not found in current directory!
    echo 📂 Current directory: %CD%
    echo.
    echo Files in directory:
    dir *.py
    echo.
    pause
    exit /b 1
)

REM Run Python with error output
echo 🐍 Running: python main.py
echo.
"python" main.py 2>&1

if errorlevel 1 (
    echo.
    echo ❌ Application exited with error
    echo.
    echo 🔧 Troubleshooting steps:
    echo 1. Check if NDI SDK is installed
    echo    - Path: C:\Program Files\NDI\NDI 6 SDK
    echo 2. Try running with elevated permissions
    echo 3. Check logs in the logs/ folder
    echo 4. Run diagnostic: python test_ndi_fix.py
    echo.
    echo 📝 Common fixes:
    echo - Disable antivirus temporarily
    echo - Close vMix if running
    echo - Update graphics drivers
    echo.
    pause
) else (
    echo.
    echo ✅ Application closed normally
    echo 🎉 Thank you for using ReturnFeed Unified!
)

pause

