@echo off
chcp 65001 >nul
title ReturnFeed Classic Mode - Professional NDI Monitor
color 0A

echo.
echo ============================================================
echo.
echo     ReturnFeed Classic Mode - Professional NDI Monitor
echo.
echo         Single-Channel Focus - Modern Dark Theme
echo.
echo ============================================================
echo.

REM Set environment variables for stability
echo [*] Configuring optimal environment...
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false
echo [OK] Environment configured for maximum stability
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    echo Download from: https://python.org
    pause
    exit /b 1
)

echo [OK] Python found: 
python --version
echo.

REM Check FFmpeg
echo [*] Checking FFmpeg...
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%~dp0ffmpeg\bin;%PATH%"
    echo [OK] FFmpeg found (local installation)
) else (
    ffmpeg -version >nul 2>&1
    if errorlevel 1 (
        echo [!] FFmpeg not found - SRT streaming will not be available
    ) else (
        echo [OK] FFmpeg found (system installation)
    )
)
echo.

REM Check dependencies
echo [*] Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [!] Installing required packages...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] All dependencies verified
echo.

REM Change to script directory
cd /d "%~dp0"

REM Launch Classic Mode
echo ============================================================
echo.
echo [*] Launching ReturnFeed Classic Mode...
echo.
echo Features:
echo    - Single NDI channel monitoring
echo    - Professional broadcast interface
echo    - Real-time tally display
echo    - SRT streaming support
echo    - Keyboard shortcuts for efficiency
echo.
echo ============================================================
echo.

REM Run Classic Mode
python main_classic.py 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with error
    echo.
    echo Troubleshooting:
    echo    1. Ensure NDI SDK is installed
    echo    2. Check if vMix is running (for tally)
    echo    3. Verify network connectivity
    echo    4. Check logs folder for details
    echo.
) else (
    echo.
    echo [OK] Thank you for using ReturnFeed Classic Mode!
)

pause