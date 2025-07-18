@echo off
cd /d "%~dp0"

REM Set environment variables
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false

REM Add local FFmpeg if exists
if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
    set PATH=%~dp0ffmpeg\bin;%PATH%
)

REM Run Python
python main.py

REM Keep window open
if %ERRORLEVEL% neq 0 pause
pause