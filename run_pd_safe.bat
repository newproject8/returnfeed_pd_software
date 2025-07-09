@echo off
REM PD 통합 소프트웨어 안전 실행 배치 파일
REM 문자 인코딩 및 환경 설정 포함

REM 콘솔 UTF-8 설정
chcp 65001 > nul

REM Qt High DPI 설정
set QT_ENABLE_HIGHDPI_SCALING=1
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough

REM Python UTF-8 모드
set PYTHONIOENCODING=utf-8

echo ============================================================
echo PD 통합 소프트웨어 v1.0.0
echo ============================================================
echo.

REM Python 실행
python run_pd_safe.py

REM 오류 발생 시 창 유지
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 오류가 발생했습니다. 오류 코드: %ERRORLEVEL%
    pause
)