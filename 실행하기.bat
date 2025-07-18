@echo off
chcp 65001 > nul
echo ========================================
echo PD 소프트웨어 실행하기
echo ========================================
echo.
echo 어떤 버전을 실행하시겠습니까?
echo.
echo 1. 메인 버전 (가장 안정적)
echo 2. Enterprise 버전
echo 3. Enterprise 수정 버전
echo 4. 종료
echo.
set /p choice=번호를 입력하세요 (1-4): 

if "%choice%"=="1" (
    echo 메인 버전을 실행합니다...
    venv\Scripts\python.exe main.py
) else if "%choice%"=="2" (
    echo Enterprise 버전을 실행합니다...
    venv\Scripts\python.exe run_enterprise.py
) else if "%choice%"=="3" (
    echo Enterprise 수정 버전을 실행합니다...
    venv\Scripts\python.exe run_enterprise_fixed.py
) else if "%choice%"=="4" (
    echo 종료합니다.
    exit
) else (
    echo 잘못된 선택입니다.
    pause
)

pause