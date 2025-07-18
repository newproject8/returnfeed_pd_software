@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Testing ReturnFeed Classic Mode...
echo.

REM Test Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Test import
echo Testing imports...
python -c "from ui.classic_mode import ClassicMainWindow; print('Import successful')" 2>&1

pause