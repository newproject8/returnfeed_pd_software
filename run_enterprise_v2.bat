@echo off
echo ========================================
echo PD Software - Enterprise Edition v2
echo ========================================
echo.

cd /d "%~dp0"

echo Starting Enterprise Edition v2...
venv\Scripts\python.exe enterprise\main_enterprise_v2.py

if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)