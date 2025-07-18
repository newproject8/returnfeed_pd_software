@echo off
REM PD Enterprise Edition Launcher
REM High-performance, production-ready version

echo ========================================
echo PD Software - Enterprise Edition
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Run Enterprise Edition
echo Starting Enterprise Edition...
python enterprise\main_enterprise.py

REM If error, pause to see message
if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)

deactivate