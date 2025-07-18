@echo off
chcp 65001 > nul
title FFmpeg 포터블 설치
color 0A

echo ========================================
echo FFmpeg 포터블 자동 설치 (관리자 권한 불필요)
echo ========================================
echo.

REM 현재 디렉토리에 ffmpeg 폴더 생성
set FFMPEG_DIR=%~dp0ffmpeg
set FFMPEG_BIN=%FFMPEG_DIR%\bin

REM FFmpeg 이미 설치되어 있는지 확인
if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo ✅ FFmpeg가 이미 설치되어 있습니다!
    "%FFMPEG_BIN%\ffmpeg.exe" -version
    echo.
    pause
    exit /b 0
)

echo 📦 FFmpeg 다운로드 및 설치를 시작합니다...
echo    설치 위치: %FFMPEG_DIR%
echo.

REM ffmpeg 디렉토리 생성
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"

REM PowerShell을 사용하여 다운로드
echo 📥 FFmpeg 다운로드 중... (약 100MB, 시간이 걸릴 수 있습니다)
powershell -Command "& {
    $ProgressPreference = 'SilentlyContinue'
    $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
    $output = '%FFMPEG_DIR%\ffmpeg.zip'
    
    try {
        Invoke-WebRequest -Uri $url -OutFile $output
        Write-Host '✅ 다운로드 완료' -ForegroundColor Green
    } catch {
        Write-Host '❌ 다운로드 실패: ' $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}"

if %errorlevel% neq 0 (
    echo.
    echo ❌ FFmpeg 다운로드 실패
    echo.
    echo 수동으로 다운로드하세요:
    echo https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    echo.
    pause
    exit /b 1
)

echo.
echo 📂 압축 해제 중...
powershell -Command "& {
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = '%FFMPEG_DIR%\ffmpeg.zip'
        $temp = '%FFMPEG_DIR%\temp'
        
        # 임시 폴더에 압축 해제
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $temp)
        
        # ffmpeg 폴더 찾기 및 이동
        $ffmpegFolder = Get-ChildItem -Path $temp -Filter 'ffmpeg-*' -Directory | Select-Object -First 1
        if ($ffmpegFolder) {
            Move-Item -Path (Join-Path $ffmpegFolder.FullName '*') -Destination '%FFMPEG_DIR%' -Force
            Remove-Item -Path $temp -Recurse -Force
        }
        
        Remove-Item -Path $zip -Force
        Write-Host '✅ 압축 해제 완료' -ForegroundColor Green
    } catch {
        Write-Host '❌ 압축 해제 실패: ' $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}"

if %errorlevel% neq 0 (
    echo.
    echo ❌ 압축 해제 실패
    pause
    exit /b 1
)

REM 설치 확인
if exist "%FFMPEG_BIN%\ffmpeg.exe" (
    echo.
    echo ✅ FFmpeg 설치 완료!
    echo.
    "%FFMPEG_BIN%\ffmpeg.exe" -version | findstr /i "version"
    echo.
    echo 📝 환경 변수 설정 안내:
    echo    ReturnFeed는 자동으로 이 위치의 FFmpeg를 사용합니다.
    echo    위치: %FFMPEG_BIN%
    echo.
    
    REM run.bat 업데이트하여 로컬 ffmpeg 사용하도록 설정
    echo 🔧 run.bat 업데이트 중...
    powershell -Command "& {
        $content = Get-Content '%~dp0run.bat' -Raw
        $newLine = 'set PATH=%~dp0ffmpeg\bin;%%PATH%%'
        if ($content -notmatch [regex]::Escape($newLine)) {
            $lines = $content -split "`r?`n"
            $newContent = @()
            $added = $false
            foreach ($line in $lines) {
                if ($line -match '^echo.*Starting ReturnFeed' -and -not $added) {
                    $newContent += ''
                    $newContent += 'REM Add local FFmpeg to PATH'
                    $newContent += $newLine
                    $added = $true
                }
                $newContent += $line
            }
            $newContent -join "`r`n" | Set-Content '%~dp0run.bat' -NoNewline
            Write-Host '✅ run.bat 업데이트 완료' -ForegroundColor Green
        }
    }"
    
    echo.
    echo ✅ 모든 설정이 완료되었습니다!
    echo    이제 run.bat을 실행하면 SRT 스트리밍을 사용할 수 있습니다.
) else (
    echo.
    echo ❌ FFmpeg 설치 확인 실패
    echo    %FFMPEG_BIN% 폴더를 확인해주세요.
)

echo.
pause