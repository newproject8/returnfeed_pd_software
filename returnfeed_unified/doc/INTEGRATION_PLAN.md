# ReturnFeed Unified Application Integration Plan

## 프로젝트 개요
두 개의 독립적인 PyQt 애플리케이션을 하나의 통합 GUI로 결합:
1. **main.py**: NDI 기반 애플리케이션 (PyQt6 사용)
2. **vMix_tcp_tally2.py**: vMix Tally Broadcaster (PyQt5 사용)

## 주요 과제 및 해결 방안

### 1. PyQt 버전 충돌
- **문제**: main.py는 PyQt6, vMix는 PyQt5 사용
- **해결**: PyQt6로 통일 (최신 버전으로 마이그레이션)

### 2. 모듈화 전략
- 각 애플리케이션의 핵심 기능을 독립적인 모듈로 분리
- 공통 UI 프레임워크에서 두 모듈을 통합

### 3. 아키텍처 설계

```
returnfeed_unified/
├── main.py                 # 통합 애플리케이션 진입점
├── doc/                    # 문서
│   ├── INTEGRATION_PLAN.md
│   └── API_DOCUMENTATION.md
├── modules/               
│   ├── ndi_module/        # NDI 기능 모듈
│   │   ├── __init__.py
│   │   ├── ndi_manager.py
│   │   └── ndi_ui.py
│   └── vmix_module/       # vMix 기능 모듈
│       ├── __init__.py
│       ├── vmix_manager.py
│       └── vmix_ui.py
├── ui/                    # 공통 UI 컴포넌트
│   ├── __init__.py
│   └── main_window.py
├── config/               # 설정 파일
│   └── settings.json
└── utils/               # 공통 유틸리티
    ├── __init__.py
    └── logger.py
```

## 구현 단계

### Phase 1: 준비 작업
1. 프로젝트 구조 생성 ✓
2. 의존성 분석 및 requirements.txt 작성
3. PyQt5 → PyQt6 마이그레이션 가이드 작성

### Phase 2: 모듈화
1. **NDI 모듈 분리**
   - NDI 초기화/종료 로직 분리
   - NDI UI 컴포넌트 분리
   - 업데이터 기능 분리

2. **vMix 모듈 분리**
   - TCP/WebSocket 통신 로직 분리
   - Tally 상태 관리 로직 분리
   - vMix UI 컴포넌트 분리

### Phase 3: 통합
1. 공통 메인 윈도우 생성
2. 탭 또는 도킹 위젯으로 두 모듈 UI 통합
3. 공통 설정 관리 시스템 구현
4. 통합 로깅 시스템 구현

### Phase 4: 테스트 및 최적화
1. 각 모듈 독립 테스트
2. 통합 테스트
3. 성능 최적화
4. 에러 처리 강화

## 주요 고려사항

### 1. 스레드 안전성
- 두 모듈이 별도 스레드에서 동작
- Qt 시그널/슬롯을 통한 안전한 통신

### 2. 리소스 관리
- NDI 라이브러리 초기화는 애플리케이션당 한 번만
- 소켓 연결 관리 및 정리

### 3. UI/UX 일관성
- 통일된 디자인 언어
- 공통 스타일시트 적용

### 4. 에러 처리
- 모듈별 독립적인 에러 처리
- 한 모듈의 오류가 다른 모듈에 영향 없도록

## 위험 요소 및 대응 방안

1. **DLL 충돌**
   - NDI SDK DLL 경로 관리 필요
   - 단일 초기화 보장

2. **이벤트 루프 충돌**
   - asyncio와 Qt 이벤트 루프 조화
   - 적절한 스레드 분리

3. **메모리 누수**
   - 적절한 리소스 정리
   - 약한 참조 사용 고려

## 다음 단계
1. PyQt6 마이그레이션 가이드 작성
2. 각 모듈의 핵심 기능 식별 및 인터페이스 설계
3. 프로토타입 구현