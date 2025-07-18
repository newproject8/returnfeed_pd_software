# SRT Streaming Module

## 설치 요구사항

### FFmpeg 설치 (필수)
SRT 스트리밍을 사용하려면 FFmpeg가 시스템에 설치되어 있어야 합니다.

#### Windows
1. https://ffmpeg.org/download.html 에서 Windows 빌드 다운로드
2. ZIP 파일을 C:\ffmpeg 같은 경로에 압축 해제
3. 시스템 환경 변수 PATH에 C:\ffmpeg\bin 추가
4. 명령 프롬프트에서 `ffmpeg -version` 실행하여 확인

#### 또는 Chocolatey 사용:
```cmd
choco install ffmpeg
```

### ffmpeg-python (선택사항)
더 나은 성능을 위해 설치 권장:
```cmd
pip install ffmpeg-python
```

## 사용 방법

1. ReturnFeed Unified 실행 (`run.bat`)
2. SRT Streaming 탭 선택
3. NDI 소스 선택 또는 화면 캡처 선택
4. 스트림 이름 입력 (또는 자동 생성)
5. 비트레이트와 FPS 설정
6. "스트리밍 시작" 버튼 클릭

## 기능

- **원본 NDI to SRT**: NDI 프리뷰를 거치지 않고 원본에서 직접 전송
- **자동 리소스 관리**: SRT 전송 시 NDI 프리뷰 자동 일시정지
- **시각적 피드백**: 프리뷰 창에 SRT 스트리밍 상태 표시
- **MediaMTX 서버**: returnfeed.net:8890으로 자동 전송

## 문제 해결

### "FFmpeg not found" 오류
- FFmpeg가 설치되지 않았거나 PATH에 없음
- 위의 설치 가이드 참조

### SRT 탭이 보이지 않음
- 모듈 초기화 실패
- 로그 파일 확인: logs/returnfeed_*.log