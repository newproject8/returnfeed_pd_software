@echo off
chcp 65001 > nul
echo ========================================
echo PD 소프트웨어 실행하기 (안전 버전)
echo ========================================
echo.
echo 어떤 버전을 실행하시겠습니까?
echo.
echo 1. 메인 버전 (가장 안정적, NDI 포함)
echo 2. Enterprise 간단 버전 (NDI 없음, 오류 없음) ← 추천!
echo 3. Enterprise 원본 버전
echo 4. 종료
echo.
set /p choice=번호를 입력하세요 (1-4): 

if "%choice%"=="1" (
    echo 메인 버전을 실행합니다...
    venv\Scripts\python.exe main.py
) else if "%choice%"=="2" (
    echo Enterprise 간단 버전을 실행합니다 (안전)...
    venv\Scripts\python.exe enterprise\main_enterprise_simple.py
) else if "%choice%"=="3" (
    echo Enterprise 원본 버전을 실행합니다...
    venv\Scripts\python.exe run_enterprise.py
) else if "%choice%"=="4" (
    echo 종료합니다.
    exit
) else (
    echo 잘못된 선택입니다.
    pause
)

pause