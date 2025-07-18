# PD 통합 소프트웨어 GUI 설계 문서
> Professional Broadcast Production Software GUI Design Document

## 목차
1. [설계 철학](#설계-철학)
2. [GUI 아키텍처](#gui-아키텍처)
3. [레이아웃 구성](#레이아웃-구성)
4. [핵심 UI 컴포넌트](#핵심-ui-컴포넌트)
5. [색상 체계 및 시각 디자인](#색상-체계-및-시각-디자인)
6. [인터랙션 디자인](#인터랙션-디자인)
7. [안정성 및 에러 방지](#안정성-및-에러-방지)
8. [성능 최적화](#성능-최적화)
9. [접근성 및 사용성](#접근성-및-사용성)
10. [확장성 및 커스터마이징](#확장성-및-커스터마이징)

---

## 1. 설계 철학

### 1.1 핵심 원칙
- **Situational Awareness First**: 방송 상황을 한눈에 파악 가능
- **Zero Cognitive Load**: 직관적이고 즉각적인 정보 전달
- **Fail-Safe Design**: 실수를 방지하고 빠른 복구 가능
- **Performance Critical**: 실시간 방송에 적합한 반응성
- **Professional Grade**: 장시간 사용에도 피로감 최소화

### 1.2 사용자 중심 설계
- **타겟 사용자**: PD, 카메라 오퍼레이터, 방송 스태프
- **사용 환경**: 어두운 방송 부조실, 멀티 모니터 환경
- **핵심 태스크**: 실시간 모니터링, 즉각적 상태 파악, 빠른 대응

---

## 2. GUI 아키텍처

### 2.1 전체 구조
```
┌─────────────────────────────────────────────────────────────┐
│                    상태바 (Status Bar)                       │
├─────────────────────────────────────────────────────────────┤
│  도구바  │                                     │   사이드   │
│ (Toolbar)│          메인 워크스페이스          │   패널    │
│          │         (Main Workspace)            │  (Side    │
│          │                                     │  Panel)   │
├──────────┴─────────────────────────────────────┴───────────┤
│                  하단 패널 (Bottom Panel)                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 레이아웃 시스템
- **Docking System**: 모든 패널은 도킹/언도킹 가능
- **Workspace Presets**: 작업 유형별 레이아웃 프리셋
- **Multi-Monitor Support**: 패널을 다른 모니터로 이동 가능
- **Responsive Scaling**: DPI-aware 자동 스케일링

---

## 3. 레이아웃 구성

### 3.1 메인 워크스페이스 (Main Workspace)
```
┌─────────────────────────────────────────────────┐
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │  NDI 1  │ │  NDI 2  │ │  NDI 3  │ │  NDI 4  ││
│  │ CAM-01  │ │ CAM-02  │ │ CAM-03  │ │ CAM-04  ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘│
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │  NDI 5  │ │  NDI 6  │ │  NDI 7  │ │  NDI 8  ││
│  │ GFX-01  │ │ GFX-02  │ │ PGM OUT │ │ PVW OUT ││
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘│
└─────────────────────────────────────────────────┘
```

#### 특징:
- **Grid Layout**: 2x4, 3x3, 4x4 등 유연한 그리드
- **Dynamic Sizing**: 중요 소스는 크게 표시 가능
- **Quick Switch**: 더블클릭으로 전체화면 전환
- **PiP Mode**: Picture-in-Picture 오버레이 지원

### 3.2 사이드 패널 (Side Panel)
```
┌─────────────────┐
│ [Tally Status]  │
├─────────────────┤
│ CAM-01  ● PGM  │
│ CAM-02  ○ PVW  │
│ CAM-03  ○ ---  │
│ CAM-04  ○ ---  │
│ GFX-01  ○ ---  │
│ GFX-02  ● PGM  │
├─────────────────┤
│ [SRT Streams]   │
├─────────────────┤
│ Stream-1 ● LIVE │
│ Stream-2 ○ IDLE │
│ Stream-3 ⚠ BUFF │
└─────────────────┘
```

### 3.3 하단 패널 (Bottom Panel)
```
┌─────────────────────────────────────────────────┐
│ [Timeline] [Logs] [Statistics] [Alerts]         │
├─────────────────────────────────────────────────┤
│ 실시간 이벤트 타임라인 / 로그 / 통계 정보      │
└─────────────────────────────────────────────────┘
```

---

## 4. 핵심 UI 컴포넌트

### 4.1 NDI 뷰어 컴포넌트
```
┌─────────────────────────────┐
│ ┌─────────────────────────┐ │
│ │                         │ │ <- 비디오 영역
│ │    [VIDEO PREVIEW]      │ │
│ │                         │ │
│ └─────────────────────────┘ │
│ CAM-01 │ 1920x1080 60fps   │ <- 소스 정보
│ ●PGM   │ 125Mbps │ -48dB   │ <- 상태 표시
└─────────────────────────────┘
```

#### 기능:
- **오버레이 정보**: 해상도, 프레임레이트, 비트레이트
- **오디오 미터**: 실시간 오디오 레벨 표시
- **탈리 상태**: PGM/PVW 상태를 테두리 색상으로 표시
- **컨텍스트 메뉴**: 우클릭으로 빠른 설정 접근

### 4.2 탈리 인디케이터
```
┌───────────────────┐
│  CAM-01  ● PGM   │ <- 빨간색 (On Air)
│  CAM-02  ● PVW   │ <- 녹색 (Preview)
│  CAM-03  ○ ---   │ <- 회색 (Standby)
│  CAM-04  ⚠ ERR   │ <- 노란색 (Warning)
└───────────────────┘
```

### 4.3 스트림 상태 패널
```
┌─────────────────────────────────┐
│ SRT Stream #1 - ReturnFeed      │
├─────────────────────────────────┤
│ Status: ● LIVE                  │
│ Bitrate: 8.5 Mbps ▂▃▅▇▆▅▃▂    │
│ Latency: 125ms                  │
│ Dropped: 0 frames               │
│ Duration: 02:34:56              │
└─────────────────────────────────┘
```

---

## 5. 색상 체계 및 시각 디자인

### 5.1 색상 팔레트
```
상태 색상:
- PGM (On Air):     #FF0000 (Red)      - 높은 명도로 주목성 확보
- PVW (Preview):    #00FF00 (Green)    - 안전한 준비 상태
- Standby:          #808080 (Gray)     - 중립적 대기 상태
- Warning:          #FFA500 (Orange)   - 주의 필요
- Error:            #FF00FF (Magenta)  - 긴급 대응 필요
- Connected:        #00BFFF (Cyan)     - 연결 상태

배경 색상:
- Main BG:          #1E1E1E (Dark Gray)
- Panel BG:         #252525 (Darker Gray)
- Active BG:        #2D2D2D (Light Dark Gray)
- Border:           #3E3E3E (Border Gray)
```

### 5.2 타이포그래피
```
- Main Font:        Segoe UI / 맑은 고딕
- Display Font:     Consolas (숫자, 타임코드)
- Icon Font:        Font Awesome 6 Pro
- Size Hierarchy:   
  - Title: 14pt Bold
  - Normal: 11pt Regular
  - Small: 9pt Regular
  - Micro: 8pt Regular
```

### 5.3 아이콘 시스템
- **Monochrome First**: 색맹 사용자도 구분 가능
- **Consistent Style**: 동일한 두께와 스타일
- **Status Icons**: ●(Live), ○(Off), ⚠(Warning), ✖(Error)
- **Action Icons**: ▶(Play), ■(Stop), ⟲(Refresh), ⚙(Settings)

---

## 6. 인터랙션 디자인

### 6.1 단축키 시스템
```
Global Shortcuts:
- F1-F12:          NDI 소스 빠른 전환
- Ctrl+1-9:        워크스페이스 프리셋
- Space:           선택된 뷰어 전체화면
- Ctrl+R:          모든 연결 새로고침
- Ctrl+Shift+S:    긴급 스트림 중지
- Alt+T:           탈리 패널 토글
```

### 6.2 드래그 앤 드롭
- **소스 재배치**: NDI 뷰어 위치 변경
- **패널 도킹**: 패널을 원하는 위치로 이동
- **프리셋 저장**: 현재 레이아웃을 드래그로 저장

### 6.3 컨텍스트 메뉴
```
NDI 뷰어 우클릭:
├── 전체화면 보기
├── 소스 설정
├── 오디오 모니터링
├── 녹화 시작/중지
├── 스냅샷 저장
└── 속성 보기
```

---

## 7. 안정성 및 에러 방지

### 7.1 확인 다이얼로그
```
┌─────────────────────────────┐
│     스트림을 중지하시겠습니까?   │
├─────────────────────────────┤
│ 현재 3명의 시청자가 있습니다.   │
│ 스트림 시간: 01:23:45         │
├─────────────────────────────┤
│ [취소] [5초 후 중지] [즉시 중지] │
└─────────────────────────────┘
```

### 7.2 상태 복구
- **Auto-Save**: 5분마다 레이아웃과 설정 자동 저장
- **Crash Recovery**: 비정상 종료 시 마지막 상태 복원
- **Connection Retry**: 네트워크 끊김 시 자동 재연결

### 7.3 경고 시스템
```
┌─────────────────────────────────────┐
│ ⚠ 주의: NDI 소스 프레임 드롭 감지    │
│   CAM-02: 15 frames dropped        │
│   [자세히 보기] [무시] [자동 수정]   │
└─────────────────────────────────────┘
```

---

## 8. 성능 최적화

### 8.1 렌더링 최적화
- **GPU 가속**: OpenGL 기반 비디오 렌더링
- **프레임 스킵**: GUI 과부하 시 지능적 프레임 스킵
- **LOD System**: 축소된 뷰어는 낮은 해상도로 표시
- **Lazy Loading**: 보이지 않는 컴포넌트는 렌더링 제외

### 8.2 메모리 관리
- **Frame Pool**: 프레임 버퍼 재사용
- **Garbage Collection**: 주기적 메모리 정리
- **Resource Limits**: 최대 메모리 사용량 제한

### 8.3 스레드 아키텍처
```
Main Thread (GUI)
├── NDI Receiver Thread #1-N
├── Tally Monitor Thread
├── SRT Streaming Thread #1-N
├── WebSocket Communication Thread
└── Performance Monitor Thread
```

---

## 9. 접근성 및 사용성

### 9.1 시각적 접근성
- **High Contrast Mode**: 고대비 모드 지원
- **Colorblind Safe**: 색상만으로 구분하지 않음
- **Scalable UI**: 125%, 150%, 200% 스케일링
- **Focus Indicators**: 명확한 포커스 표시

### 9.2 청각적 피드백
- **Alert Sounds**: 중요 이벤트 사운드 알림
- **Voice Alerts**: TTS 음성 경고 옵션
- **Visual Cues**: 소리 없이도 모든 정보 파악 가능

### 9.3 다국어 지원
```
지원 언어:
- 한국어 (기본)
- English
- 日本語
- 中文
```

---

## 10. 확장성 및 커스터마이징

### 10.1 플러그인 시스템
```python
class PluginInterface:
    def on_ndi_frame(self, source, frame): pass
    def on_tally_change(self, input, state): pass
    def on_stream_event(self, stream, event): pass
    def get_custom_panel(self): return None
```

### 10.2 테마 시스템
```json
{
  "theme": {
    "name": "Broadcast Dark",
    "colors": {
      "background": "#1E1E1E",
      "foreground": "#FFFFFF",
      "accent": "#00BFFF",
      "pgm": "#FF0000",
      "pvw": "#00FF00"
    }
  }
}
```

### 10.3 API 인터페이스
- **REST API**: 외부 시스템 연동
- **WebSocket API**: 실시간 상태 구독
- **OSC Protocol**: 조명 콘솔 등과 연동

---

## 구현 우선순위

### Phase 1: Core (필수)
1. 메인 레이아웃 시스템
2. NDI 뷰어 컴포넌트
3. 탈리 상태 표시
4. 기본 색상 체계

### Phase 2: Professional (전문성)
1. 멀티 모니터 지원
2. 단축키 시스템
3. 워크스페이스 프리셋
4. 고급 경고 시스템

### Phase 3: Advanced (고급)
1. 플러그인 시스템
2. 테마 커스터마이징
3. API 인터페이스
4. 음성 알림

---

## 결론

이 GUI 설계는 방송 제작 환경의 특수성을 고려하여 **안정성**, **실시간성**, **직관성**을 최우선으로 하였습니다. 전문 오퍼레이터가 스트레스 상황에서도 실수 없이 빠르게 대응할 수 있도록 설계되었으며, 장시간 사용에도 피로감을 최소화하는 것을 목표로 합니다.

핵심은 **"See Everything, Control Everything, Trust Everything"** - 모든 것을 볼 수 있고, 제어할 수 있으며, 신뢰할 수 있는 시스템입니다.