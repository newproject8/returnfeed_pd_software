@echo off
echo === TEST RUN.BAT ===
echo.

echo Current directory: %CD%
echo Script directory: %~dp0
echo.

echo Checking Python...
where python
if errorlevel 1 (
    echo ERROR: Python not found!
) else (
    echo Python found.
    python --version
)

echo.
echo Checking main.py...
if exist "%~dp0main.py" (
    echo main.py found at: %~dp0main.py
) else (
    echo ERROR: main.py not found!
    echo.
    echo Directory contents:
    dir "%~dp0" /b
)

echo.
echo Checking FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo FFmpeg not found.
) else (
    echo FFmpeg found.
)

echo.
echo === END TEST ===
pause