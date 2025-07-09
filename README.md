# PD 통합 소프트웨어

<div align="center">
  <h3>NDI 프리뷰 · vMix Tally · SRT 스트리밍 통합 솔루션</h3>
  <p>
    <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
    <img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python">
    <img src="https://img.shields.io/badge/license-proprietary-red.svg" alt="License">
  </p>
</div>

## 📌 개요

PD 통합 소프트웨어는 방송 제작을 위한 올인원 솔루션입니다. NDI 비디오 프리뷰, vMix Tally 시스템, SRT 스트리밍을 하나의 애플리케이션으로 통합하여 효율적인 방송 워크플로우를 제공합니다.

### 주요 특징

- 🎥 **NDI 프리뷰**: 네트워크상의 NDI 소스 실시간 모니터링
- 🔴 **vMix Tally**: PGM/PVW 상태를 모든 스태프에게 실시간 전달
- 📡 **SRT 스트리밍**: MediaMTX 서버를 통한 안정적인 스트리밍
- 🔐 **통합 인증**: PD 로그인 및 고유 주소 시스템
- 🌐 **릴레이 시스템**: WebSocket 기반 실시간 정보 공유

## 🚀 빠른 시작

### 실행 파일 사용 (권장)

1. [Releases](https://github.com/newproject8/returnfeed_pd_software/releases)에서 최신 버전 다운로드
2. 압축 해제 후 `PD_Software.exe` 실행
3. PD 계정으로 로그인

### 소스코드 실행

```bash
# 저장소 클론
git clone https://github.com/newproject8/returnfeed_pd_software.git
cd returnfeed_pd_software

# 의존성 설치
pip install -r requirements.txt

# 실행
python main_integrated.py
```

## 📋 시스템 요구사항

### 최소 요구사항
- Windows 10 64bit (버전 1909 이상)
- Intel Core i5 또는 동급
- 8GB RAM
- 100Mbps 네트워크

### 권장 요구사항
- Windows 11 64bit
- Intel Core i7 이상
- 16GB RAM 이상
- 1Gbps 네트워크

### 필수 소프트웨어
- **FFmpeg**: SRT 스트리밍용 (필수)
- **NDI Tools**: NDI 프리뷰용 (선택)
- **vMix**: Tally 시스템용 (선택)

## 🏗️ 시스템 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│    vMix     │────▶│   PD 앱     │────▶│ 릴레이 서버  │
│ TCP:8099    │     │             │     │   :8765      │
│ HTTP:8088   │     │             │     └──────┬───────┘
└─────────────┘     │             │            │
                    │             │     ┌──────▼───────┐
                    │             │     │ 카메라맨 앱  │
                    │             │     └──────────────┘
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  MediaMTX    │
                    │   :8890      │
                    └─────────────┘
```

## 📁 프로젝트 구조

```
returnfeed_pd_software/
├── main_integrated.py      # 메인 진입점
├── pd_app/
│   ├── core/              # 핵심 관리자 모듈
│   │   ├── ndi_manager.py
│   │   ├── vmix_manager.py
│   │   ├── srt_manager.py
│   │   └── auth_manager.py
│   ├── ui/                # GUI 위젯
│   │   ├── main_window.py
│   │   ├── ndi_widget.py
│   │   ├── tally_widget.py
│   │   └── srt_widget.py
│   ├── network/           # 네트워크 통신
│   │   ├── websocket_client.py
│   │   └── tcp_client.py
│   └── config/            # 설정 관리
├── test_*.py              # 테스트 스크립트
└── docs/                  # 문서
```

## 🔧 주요 기능

### 1. NDI 프리뷰
- 자동 소스 검색
- 실시간 비디오 프리뷰
- 최적화된 NDIlib 사용

### 2. vMix Tally
- TCP + HTTP 하이브리드 방식
- 실시간 PGM/PVW 상태 감지
- WebSocket으로 모든 스태프에게 전달

### 3. SRT 스트리밍
- NDI 소스 스트리밍
- 화면 캡처 스트리밍
- MediaMTX 서버 연동

### 4. 릴레이 시스템
- 실시간 Tally 정보 브로드캐스트
- 입력 목록 동기화
- 새 클라이언트 자동 업데이트

## 📝 문서

- [사용자 가이드](사용자_가이드.md)
- [설치 가이드](설치_가이드.md)
- [통합 프로젝트 계획서](통합_프로젝트_계획서.md)
- [디버깅 보고서](디버깅_보고서.md)

## 🧪 테스트

```bash
# 시스템 전체 테스트
python test_system.py

# 백엔드 통합 테스트
python test_backend_integration.py

# 모듈 단위 테스트
python test_modules.py

# Tally 릴레이 테스트
python test_tally_relay.py
```

## 🔨 빌드

```bash
# 실행 파일 빌드
python build_exe.py
```

## 🤝 기여

이 프로젝트는 ReturnFeed 내부 프로젝트입니다. 기여 방법:

1. 이슈 등록
2. 기능 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

## 📞 지원

- **이메일**: support@returnfeed.net
- **문서**: https://docs.returnfeed.net
- **이슈**: [GitHub Issues](https://github.com/newproject8/returnfeed_pd_software/issues)

## 📄 라이선스

이 소프트웨어는 ReturnFeed의 독점 소프트웨어입니다. 무단 복제 및 배포를 금지합니다.

---

<div align="center">
  <p>
    Made with ❤️ by PD Software Team<br>
    © 2025 ReturnFeed. All rights reserved.
  </p>
</div>