@echo off
chcp 65001 > nul
title FFmpeg 자동 설치
color 0A

echo ========================================
echo FFmpeg 자동 설치 프로그램
echo ========================================
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 이 스크립트는 관리자 권한이 필요합니다!
    echo.
    echo 다음 방법으로 실행하세요:
    echo 1. 이 파일을 마우스 오른쪽 클릭
    echo 2. "관리자 권한으로 실행" 선택
    echo.
    pause
    exit /b 1
)

REM FFmpeg 이미 설치되어 있는지 확인
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg가 이미 설치되어 있습니다!
    ffmpeg -version
    echo.
    pause
    exit /b 0
)

echo 🔍 FFmpeg가 설치되어 있지 않습니다.
echo.

REM Chocolatey 설치 확인
where choco >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Chocolatey가 설치되어 있습니다.
    echo 📦 FFmpeg를 설치합니다...
    echo.
    choco install ffmpeg -y
    if %errorlevel% equ 0 (
        echo.
        echo ✅ FFmpeg 설치 완료!
        echo.
        echo 🔄 환경 변수를 적용하려면 새 명령 프롬프트를 열어주세요.
        pause
        exit /b 0
    ) else (
        echo ❌ FFmpeg 설치 실패
        goto :manual_install
    )
) else (
    echo ⚠️  Chocolatey가 설치되어 있지 않습니다.
    echo.
    choice /C YN /M "Chocolatey를 설치하시겠습니까?"
    if %errorlevel% equ 1 (
        echo.
        echo 📦 Chocolatey 설치 중...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
        
        REM PATH 새로고침
        call refreshenv
        
        echo.
        echo 📦 FFmpeg 설치 중...
        choco install ffmpeg -y
        
        if %errorlevel% equ 0 (
            echo.
            echo ✅ FFmpeg 설치 완료!
            echo.
            echo 🔄 환경 변수를 적용하려면 새 명령 프롬프트를 열어주세요.
            pause
            exit /b 0
        ) else (
            goto :manual_install
        )
    ) else (
        goto :manual_install
    )
)

:manual_install
echo.
echo ========================================
echo 수동 설치 방법
echo ========================================
echo.
echo 1. 다음 URL에서 FFmpeg 다운로드:
echo    https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
echo.
echo 2. C:\ffmpeg 폴더에 압축 해제
echo.
echo 3. 시스템 환경 변수 PATH에 C:\ffmpeg\bin 추가
echo    - Windows + X → 시스템 → 고급 시스템 설정
echo    - 환경 변수 → Path 편집 → 새로 만들기
echo    - C:\ffmpeg\bin 추가
echo.
echo 4. 새 명령 프롬프트에서 ffmpeg -version 확인
echo.
pause