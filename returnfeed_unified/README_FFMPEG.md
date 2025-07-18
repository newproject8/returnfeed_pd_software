# FFmpeg 자동 설치 가이드

## 자동 설치 방법

### 1. 포터블 설치 (권장) - 관리자 권한 불필요
```cmd
install_ffmpeg_portable.bat
```
- 현재 폴더에 FFmpeg 설치
- 관리자 권한 불필요
- ReturnFeed 전용으로 사용

### 2. 시스템 전체 설치 - 관리자 권한 필요
```cmd
install_ffmpeg.bat (관리자 권한으로 실행)
```
- Chocolatey를 통한 시스템 설치
- 모든 프로그램에서 사용 가능

## 설치 과정

1. `run.bat` 실행 시 FFmpeg가 없으면 자동 설치 제안
2. Y를 선택하면 포터블 버전 자동 다운로드 및 설치
3. 설치 완료 후 run.bat 재실행

## 수동 설치

FFmpeg 공식 사이트: https://ffmpeg.org/download.html

1. Windows builds by gyan.dev 선택
2. release essentials 다운로드
3. C:\ffmpeg에 압축 해제
4. 시스템 PATH에 C:\ffmpeg\bin 추가

## 설치 확인

```cmd
ffmpeg -version
```

## 문제 해결

- 다운로드 실패: 인터넷 연결 확인
- 압축 해제 실패: 디스크 공간 확인 (약 200MB 필요)
- PATH 오류: 새 명령 프롬프트 열기