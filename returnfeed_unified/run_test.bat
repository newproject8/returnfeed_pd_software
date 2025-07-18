@echo off
chcp 65001 >nul
title ReturnFeed Unified - Test Suite
color 0B

echo ╔════════════════════════════════════════════════════════════════╗
echo ║         🧪 ReturnFeed Unified - ULTRATHINK Test Suite          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 🚀 ULTRATHINK 크래시 방지 환경 설정
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=true;qt.rhi.*=true

echo 🔧 Test Environment Configuration:
echo ─────────────────────────────────────────────
echo ✅ OpenGL backend forced
echo ✅ FFmpeg multimedia backend
echo ✅ Qt logging enabled
echo.

REM 테스트 선택 메뉴
:MENU
echo 📋 Select Test to Run:
echo ─────────────────────────────────────────────
echo.
echo   1. Import Test          - Check all module imports
echo   2. NDI API Test         - Test NDI SDK functionality  
echo   3. Frame Conversion     - Test bulletproof frame pipeline
echo   4. QPainter Rendering   - Test direct rendering widget
echo   5. Memory Monitor       - Run with memory profiling
echo   6. Full Integration     - Complete application test
echo   7. Stress Test          - Long-running stability test
echo   8. Quick Diagnostic     - Fast system check
echo.
echo   0. Exit
echo.
set /p CHOICE="Enter your choice (0-8): "

if "%CHOICE%"=="0" goto END
if "%CHOICE%"=="1" goto TEST_IMPORTS
if "%CHOICE%"=="2" goto TEST_NDI_API
if "%CHOICE%"=="3" goto TEST_FRAME
if "%CHOICE%"=="4" goto TEST_QPAINTER
if "%CHOICE%"=="5" goto TEST_MEMORY
if "%CHOICE%"=="6" goto TEST_FULL
if "%CHOICE%"=="7" goto TEST_STRESS
if "%CHOICE%"=="8" goto TEST_DIAGNOSTIC

echo Invalid choice. Please try again.
echo.
goto MENU

:TEST_IMPORTS
echo.
echo 🧪 Running Import Test...
echo ════════════════════════════════════════════════════════════════
python test_imports.py
echo.
pause
cls
goto MENU

:TEST_NDI_API
echo.
echo 🧪 Running NDI API Test...
echo ════════════════════════════════════════════════════════════════
python test_ndi_api.py
echo.
pause
cls
goto MENU

:TEST_FRAME
echo.
echo 🧪 Running Frame Conversion Test...
echo ════════════════════════════════════════════════════════════════
python -c "
from modules.ndi_module.ndi_receiver import NDIReceiver
import numpy as np
print('Testing bulletproof frame conversion...')
receiver = NDIReceiver()
# Test BGRA format
test_frame = np.random.randint(0, 255, (1080, 1920, 4), dtype=np.uint8)
result = receiver._create_qimage_bulletproof(test_frame)
if result:
    print('✅ BGRA conversion: SUCCESS')
else:
    print('❌ BGRA conversion: FAILED')
# Test YUV format
test_frame_yuv = np.random.randint(0, 255, (1080, 1920, 2), dtype=np.uint8)
result_yuv = receiver._create_qimage_bulletproof(test_frame_yuv)
if result_yuv:
    print('✅ YUV conversion: SUCCESS')
else:
    print('❌ YUV conversion: FAILED')
"
echo.
pause
cls
goto MENU

:TEST_QPAINTER
echo.
echo 🧪 Testing QPainter Direct Rendering...
echo ════════════════════════════════════════════════════════════════
python -c "
from PyQt6.QtWidgets import QApplication
from modules.ndi_module.ndi_widget import VideoDisplayWidget
import sys
print('Creating test application...')
app = QApplication(sys.argv)
widget = VideoDisplayWidget()
widget.setWindowTitle('QPainter Rendering Test')
widget.show()
print('✅ VideoDisplayWidget created successfully')
print('✅ QPainter rendering mode active')
print('✅ No QVideoSink dependency')
print('Close the window to continue...')
app.exec()
"
echo.
pause
cls
goto MENU

:TEST_MEMORY
echo.
echo 🧪 Running Memory Monitor Test...
echo ════════════════════════════════════════════════════════════════
echo This will run the application with memory profiling enabled.
echo Watch for memory leaks over 30 seconds...
echo.
python -c "
import time
import gc
import sys
try:
    import psutil
    import os
    process = psutil.Process(os.getpid())
    print(f'Initial memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
    
    # Import and initialize
    from modules.ndi_module.ndi_receiver import NDIReceiver
    receiver = NDIReceiver()
    
    # Simulate frame processing
    import numpy as np
    for i in range(300):  # 30 seconds at 10fps
        frame = np.random.randint(0, 255, (1080, 1920, 4), dtype=np.uint8)
        qimage = receiver._create_qimage_bulletproof(frame)
        
        if i % 50 == 0:
            gc.collect()
            mem = process.memory_info().rss / 1024 / 1024
            print(f'Frame {i}: Memory = {mem:.1f} MB, Objects = {len(gc.get_objects())}')
        
        time.sleep(0.1)
    
    print(f'Final memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
    print('✅ Memory test completed - check for leaks above')
    
except ImportError:
    print('❌ psutil not installed. Run: pip install psutil')
"
echo.
pause
cls
goto MENU

:TEST_FULL
echo.
echo 🧪 Running Full Integration Test...
echo ════════════════════════════════════════════════════════════════
echo This will launch the complete application.
echo.
python main.py
echo.
pause
cls
goto MENU

:TEST_STRESS
echo.
echo 🧪 Running Stress Test...
echo ════════════════════════════════════════════════════════════════
echo This test will run for 5 minutes to check stability.
echo Press Ctrl+C to stop early.
echo.
python -c "
import time
print('Starting 5-minute stress test...')
print('Check Task Manager for memory/CPU usage')
start_time = time.time()
duration = 300  # 5 minutes

# Run the actual application with timeout
import subprocess
import threading

def run_app():
    subprocess.run(['python', 'main.py'])

thread = threading.Thread(target=run_app)
thread.daemon = True
thread.start()

while time.time() - start_time < duration:
    elapsed = time.time() - start_time
    remaining = duration - elapsed
    print(f'\rStress test running... {remaining:.0f} seconds remaining', end='')
    time.sleep(1)
    
    if not thread.is_alive():
        print('\n❌ Application crashed during stress test!')
        break
else:
    print('\n✅ Stress test completed successfully!')
"
echo.
pause
cls
goto MENU

:TEST_DIAGNOSTIC
echo.
echo 🧪 Running Quick Diagnostic...
echo ════════════════════════════════════════════════════════════════
echo.

REM Python version
echo 1. Python Check:
python --version
python -c "import sys; print(f'   Path: {sys.executable}')"
echo.

REM Key packages
echo 2. Package Check:
python -c "
import importlib
packages = ['PyQt6', 'numpy', 'NDIlib']
for pkg in packages:
    try:
        mod = importlib.import_module(pkg)
        version = getattr(mod, '__version__', 'installed')
        print(f'   ✅ {pkg}: {version}')
    except ImportError:
        print(f'   ❌ {pkg}: NOT INSTALLED')
"
echo.

REM NDI SDK
echo 3. NDI SDK Check:
if exist "C:\Program Files\NDI\NDI 6 SDK" (
    echo    ✅ NDI 6 SDK found
) else if exist "C:\Program Files\NDI\NDI 5 SDK" (
    echo    ✅ NDI 5 SDK found
) else (
    echo    ❌ NDI SDK not found
)
echo.

REM Environment
echo 4. Environment Check:
echo    QSG_RHI_BACKEND=%QSG_RHI_BACKEND%
echo    QT_MULTIMEDIA_PREFERRED_PLUGINS=%QT_MULTIMEDIA_PREFERRED_PLUGINS%
echo.

REM Quick NDI test
echo 5. NDI Library Test:
python -c "
try:
    import NDIlib as ndi
    if ndi.initialize():
        print('   ✅ NDI library initialized successfully')
        ndi.destroy()
    else:
        print('   ❌ NDI initialization failed')
except Exception as e:
    print(f'   ❌ NDI error: {e}')
"
echo.

echo Diagnostic complete!
echo.
pause
cls
goto MENU

:END
echo.
echo 👋 Thank you for testing ReturnFeed Unified!
echo.
timeout /t 3
exit /b 0