@echo off
REM PD 통합 소프트웨어 실행 배치 파일
REM High DPI 문제 해결을 위한 환경 설정 포함

REM Qt High DPI 설정
set QT_ENABLE_HIGHDPI_SCALING=1
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough

REM Python 실행
echo PD 통합 소프트웨어를 시작합니다...
python run_pd_software.py

REM 오류 발생 시 창 유지
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 오류가 발생했습니다. 오류 코드: %ERRORLEVEL%
    pause
)