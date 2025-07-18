@echo off
chcp 65001 >nul
title ReturnFeed Unified - Debug Mode
color 0E

echo ╔════════════════════════════════════════════════════════════════╗
echo ║         🔍 ReturnFeed Unified - ULTRATHINK Debug Mode          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 🚀 ULTRATHINK 크래시 방지 + 디버그 환경 설정
echo 🔧 Configuring debug environment...
echo ─────────────────────────────────────────────

REM 필수 크래시 방지 설정
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
echo ✅ Crash prevention settings applied

REM 상세 디버깅 로그 설정
set QT_LOGGING_RULES=*=true
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
echo ✅ Full debug logging enabled

REM Qt 디버그 정보
set QT_DEBUG_PLUGINS=1
set QML_IMPORT_TRACE=1
echo ✅ Qt plugin debugging enabled

REM NDI 디버그 (환경변수가 있다면)
set NDI_LOG_LEVEL=verbose
echo ✅ NDI verbose logging enabled

REM Python 경로 및 버전 정보
echo.
echo 📊 System Information:
echo ─────────────────────────────────────────────
echo Python Path: %PATH%
echo.
python --version
python -c "import sys; print(f'Python Executable: {sys.executable}')"
python -c "import sys; print(f'Python Path: {sys.path[0]}')"

REM 의존성 버전 확인
echo.
echo 📦 Package Versions:
echo ─────────────────────────────────────────────
python -c "import PyQt6.QtCore; print(f'PyQt6: {PyQt6.QtCore.PYQT_VERSION_STR}')"
python -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python -c "try: import psutil; print(f'psutil: {psutil.__version__}')
except: print('psutil: Not installed (optional)')"

REM NDI 라이브러리 확인
echo.
echo 🎬 NDI Check:
echo ─────────────────────────────────────────────
python -c "try: import NDIlib as ndi; print('NDI Python: Available'); print(f'NDI Path: {ndi.__file__}')
except Exception as e: print(f'NDI Python: Not available - {e}')"

if exist "C:\Program Files\NDI\NDI 6 SDK\Bin\x64\Processing.NDI.Lib.x64.dll" (
    echo NDI SDK DLL: Found
    echo Location: C:\Program Files\NDI\NDI 6 SDK\Bin\x64\
) else (
    echo NDI SDK DLL: Not found at default location
)

REM 로그 폴더 생성
if not exist logs mkdir logs
echo.
echo 📝 Log files will be saved to: %cd%\logs\
echo ─────────────────────────────────────────────

REM 디버그 모드 실행
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                  🐛 Starting in Debug Mode                      ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🔍 Debug Features Active:
echo   ✓ Verbose logging to console and file
echo   ✓ Memory usage monitoring every 5 seconds
echo   ✓ Frame-by-frame analysis (first 5 frames)
echo   ✓ Performance metrics (FPS, queue size)
echo   ✓ Crash stack trace capture
echo.
echo 💡 Watch for:
echo   - 🔍 Frame analysis logs
echo   - 🚀 PERFORMANCE logs every 5 seconds
echo   - ❌ Error messages
echo   - ⚠️  Warning messages
echo.
echo ════════════════════════════════════════════════════════════════
echo.

REM 디버그 실행 with 에러 추적
python -u main.py 2>&1 | tee logs\debug_session_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log

REM 종료 코드 저장
set EXIT_CODE=%ERRORLEVEL%

echo.
echo ════════════════════════════════════════════════════════════════
echo Exit Code: %EXIT_CODE%
echo.

if %EXIT_CODE% NEQ 0 (
    echo ❌ Application exited with error code: %EXIT_CODE%
    echo.
    echo 🔍 Debug Information:
    echo ───────────────────────────────────────
    echo.
    echo Error Codes:
    echo   -1073741819 (0xC0000005): Access Violation (Memory Error)
    echo   -1073741676 (0xC0000094): Integer Division by Zero
    echo   -1073741571 (0xC00000FD): Stack Overflow
    echo   1: General Python Exception
    echo   2: Import Error
    echo   3: NDI Initialization Failed
    echo.
    echo Check the debug log for detailed information.
    echo.
) else (
    echo ✅ Application exited normally
    echo.
)

echo 📝 Debug session log saved to logs folder
echo.
echo Press any key to view the log file...
pause >nul

REM 로그 파일 열기 (가장 최근 것)
for /f "delims=" %%i in ('dir /b /od logs\debug_session_*.log 2^>nul') do set "LATEST_LOG=%%i"
if defined LATEST_LOG (
    notepad "logs\%LATEST_LOG%"
) else (
    echo No log file found.
)

exit /b %EXIT_CODE%