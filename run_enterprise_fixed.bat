@echo off
chcp 65001 > nul
echo ============================================================
echo PD 통합 소프트웨어 - Enterprise Edition (Fixed)
echo ============================================================
echo.

REM 가상환경 활성화
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist venv_py312\Scripts\activate.bat (
    call venv_py312\Scripts\activate.bat
) else (
    echo 가상환경을 찾을 수 없습니다.
    echo 시스템 Python을 사용합니다.
)

REM 수정된 버전 실행
python enterprise\main_enterprise_fixed.py

pause