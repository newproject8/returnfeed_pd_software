# PD 통합 소프트웨어 실행 가이드

## 📋 실행 전 확인사항

### 1. 시스템 요구사항
- Windows 10/11 (64bit)
- Python 3.8 이상
- NDI SDK (선택사항)

### 2. 가상환경 확인
프로젝트에는 이미 `venv` 폴더가 포함되어 있습니다.

## 🚀 실행 방법

### Windows PowerShell 또는 명령 프롬프트에서:

```bash
# 1. 프로젝트 디렉토리로 이동
cd C:\coding\returnfeed_tally_fresh

# 2. 가상환경 활성화
venv\Scripts\activate

# 3. 프로그램 실행
python main_integrated.py
```

### 또는 한 줄로 실행:

```bash
cd C:\coding\returnfeed_tally_fresh && venv\Scripts\python.exe main_integrated.py
```

## 🔧 문제 해결

### PyQt6 오류가 발생하는 경우:

```bash
# 가상환경 활성화 후
pip install -r requirements.txt
```

### NDI 관련 오류가 발생하는 경우:
- NDI SDK가 설치되어 있지 않아도 프로그램은 시뮬레이터 모드로 실행됩니다.
- NDI SDK 설치: https://www.ndi.tv/tools/

### 로그 확인:
- 로그 파일은 `logs` 폴더에 생성됩니다.
- 파일명: `pd_app_YYYYMMDD_HHMMSS.log`

## 📝 주요 수정 사항

### 1. **NDI 소스 검색 오류 수정**
- list 타입을 먼저 확인하도록 순서 변경
- 시뮬레이터 모드 개선

### 2. **WebSocket 연결 개선**
- 서버 연결 실패 시 자동 재연결
- 더 자세한 오류 로깅

### 3. **설정 저장 오류 수정**
- QByteArray JSON 직렬화 문제 해결
- 설정 파일 안정성 향상

### 4. **로깅 시스템 개선**
- 더 자세한 오류 추적
- 파일명, 줄 번호, 함수명 포함
- 전역 예외 핸들러 추가

## 🎯 실행 후 확인사항

1. **메인 창이 표시되는지 확인**
2. **NDI 탭**: 시뮬레이터 모드로 작동 (NDI SDK 없는 경우)
3. **Tally 탭**: vMix 연결 테스트
4. **SRT 탭**: 스트리밍 설정 확인

## 💡 추가 정보

- 프로그램 종료 시 설정이 자동 저장됩니다.
- 문제 발생 시 로그 파일을 확인하세요.
- WSL 환경에서는 GUI를 실행할 수 없으므로 Windows에서 실행하세요.