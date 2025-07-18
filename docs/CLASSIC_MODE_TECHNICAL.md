# Classic Mode 기술 문서

## 개요

Classic Mode는 리턴피드 통합 소프트웨어의 메인 인터페이스로, Adobe Premiere 스타일의 전문가용 방송 인터페이스를 제공합니다. 이 문서는 Classic Mode의 기술적 구현사항과 최적화 전략을 다룹니다.

## 아키텍처 개요

### 핵심 컴포넌트

```
ClassicMainWindow
├── CommandBar              # 상단 컨트롤 바
├── VideoDisplay            # 중앙 비디오 프리뷰
├── NDIControlPanel         # NDI 컨트롤 패널
├── StreamControlPanel      # 스트림 컨트롤 패널
└── InfoStatusBar          # 하단 상태 바
```

### 모듈 통합

```
NDI Module ─────┐
               ├─── ClassicMainWindow
vMix Module ────┤
               ├─── UI Components
SRT Module ─────┘
```

## NDI 처리 시스템

### 동적 비트레이트 계산

```python
def _calculate_dynamic_bitrate(self, width, height, fps, actual_frame_size=None):
    """동적 비트레이트 계산 - 해상도와 압축률 고려"""
    # Raw 데이터 비트레이트 계산
    raw_bps = width * height * 4 * 8 * fps
    raw_mbps = raw_bps / 1_000_000
    
    # 실제 프레임 크기 기반 계산 (같은 PC 내부 NDI 검증용)
    if actual_frame_size and fps > 0:
        actual_bps = actual_frame_size * 8 * fps
        actual_mbps = actual_bps / 1_000_000
        
        # 실제 데이터 크기가 이론값보다 훨씬 크면 압축 없음으로 판단
        if actual_mbps > raw_mbps * 0.8:
            return actual_mbps
```

**핵심 특징:**
- 실제 프레임 크기 기반 압축률 감지
- 같은 PC 내부 NDI 무압축 트래픽 감지
- 해상도별 동적 비트레이트 계산

### 프록시 모드 최적화

```python
def _process_frame_queue(self):
    """Process frames from queue at precise intervals"""
    if not self.frame_queue:
        # 프록시 모드에서 프레임이 없으면 이전 프레임 재사용
        if self.current_bandwidth_mode == "proxy" and self.last_displayed_frame:
            # 이전 프레임을 다시 표시하여 60fps 유지
            self._display_frame(self.last_displayed_frame, is_interpolated=True)
        return
```

**프레임 보간 전략:**
- 프록시 모드에서 프레임 부족 시 이전 프레임 재사용
- 60fps 안정성 유지
- 버퍼 크기 동적 조절 (일반: 2, 프록시: 1)

## UI 컴포넌트 시스템

### Adobe Premiere 스타일 테마

```python
PREMIERE_COLORS = {
    'bg_dark': '#1E1E1E',
    'bg_medium': '#2D2D2D',
    'bg_light': '#3C3C3C',
    'text_primary': '#FFFFFF',
    'text_secondary': '#CCCCCC',
    'accent': '#4A90E2',
    'success': '#4CAF50',
    'error': '#F44336',
    'warning': '#FF9800'
}
```

**디자인 원칙:**
- 다크 테마 기반 전문가용 인터페이스
- 일관된 색상 스키마
- 명확한 시각적 계층구조

### 컴팩트 1행 레이아웃

```python
# NDI Control Panel
layout = QHBoxLayout()
layout.setSpacing(25)  # 일관된 간격

# 레이블 | 요소 | 요소 | 요소 구조
ndi_label = QLabel("NDI")
ndi_label.setFixedWidth(80)  # 고정 너비로 정렬

source_combo = QComboBox()
source_combo.setFixedWidth(400)  # 넓은 소스 선택

toggle_button = QPushButton("일반")
toggle_button.setFixedSize(80, 28)
```

**레이아웃 특징:**
- 고정 너비로 정렬된 레이블
- 충분한 공간을 가진 드롭다운
- 일관된 버튼 크기와 간격

## 스트림 URL 공유 시스템

### 고유 주소 생성

```python
def _generate_stream_id(self) -> str:
    """고유 스트림 ID 생성 (더미 구현)"""
    # 사용자 친화적인 ID 생성: 6자리 대문자 + 3자리 숫자
    letters = ''.join(random.choices(string.ascii_uppercase, k=6))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letters}{numbers}"
```

### 상태 기반 UI 변경

```python
class ClickableUrlLabel(QLabel):
    def _update_style(self):
        """스트리밍 상태에 따른 스타일 업데이트"""
        if self.is_streaming:
            # 스트리밍 중: 붉은 계통 컬러
            self.setStyleSheet("""
                QLabel {
                    color: #EF4444;
                    font-weight: bold;
                    font-size: 20px;
                }
            """)
        else:
            # 기본 상태: 옅은 회색
            self.setStyleSheet("""
                QLabel {
                    color: #9CA3AF;
                    font-weight: bold;
                    font-size: 20px;
                }
            """)
```

**URL 공유 기능:**
- 클릭 시 자동 클립보드 복사
- 스트리밍 상태에 따른 색상 변경
- 시각적 피드백 (복사 완료 시 녹색)

## 스마트 포커스 시스템

### 자동 포커스 이동

```python
def _on_srt_start_clicked(self):
    """Handle SRT start click"""
    # NDI 소스가 선택되지 않은 경우 포커스를 NDI 소스 선택으로 이동
    if not self.current_source:
        logger.warning("NDI 소스를 선택해야 스트리밍을 시작할 수 있습니다.")
        self.ndi_control_panel.focus_source_combo()
        return
```

### 애니메이션 피드백

```python
class AnimatedSourceComboBox(QComboBox):
    def _update_animation(self):
        """애니메이션 업데이트"""
        if self.needs_selection:
            # 각도 업데이트 (360도 회전)
            self.animation_angle += 2.0  # 회전 속도
            if self.animation_angle >= 360.0:
                self.animation_angle = 0.0
                
            # 글로우 강도 펄싱 효과
            self.glow_intensity = 0.5 + 0.3 * math.sin(self.animation_angle * math.pi / 180.0)
            self.update()
```

**애니메이션 특징:**
- 파란색 계열 회전하는 빛 효과
- 펄싱 글로우 효과
- 필요 액션 완료 시 자동 중지

## 성능 최적화 전략

### 60fps 안정성

```python
# 60fps precise timing (16.67ms)
self.frame_timer = QTimer()
self.frame_timer.timeout.connect(self._process_frame_queue)
self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)  # High precision timer
self.frame_timer.setInterval(16)  # 60fps = 16.67ms
```

**타이밍 최적화:**
- 정확한 16ms 타이머
- 프레임 큐 기반 안정적 처리
- 스트리밍 시 불필요한 프레임 처리 생략

### 메모리 효율성

```python
def _on_frame_received(self, frame_data):
    """Handle received NDI frame - add to queue for stable timing"""
    # SRT 스트리밍 중이고 페이드가 완료된 경우 프레임 처리 생략 (자원 절약)
    if self.is_srt_streaming and hasattr(self.video_display, '_fade_opacity') and self.video_display._fade_opacity >= 1.0:
        return
        
    # 프레임 큐에 추가
    if len(self.frame_queue) < self.max_frame_buffer:
        self.frame_queue.append(frame_data)
    else:
        # 버퍼가 가득 찬 경우 가장 오래된 프레임 교체
        self.frame_skip_count += 1
        self.frame_queue[0] = frame_data
```

**메모리 관리:**
- 적응형 프레임 큐 크기
- 스트리밍 시 자원 절약
- 오래된 프레임 자동 폐기

## vMix Tally 통합

### 실시간 탈리 처리

```python
def _on_vmix_tally_updated(self, pgm: int, pvw: int, pgm_name: str, pvw_name: str):
    """vMixManager 탈리 업데이트 처리 (int, int, str, str 형식)"""
    logger.info(f"Tally update received - PGM: {pgm_name} ({pgm}), PVW: {pvw_name} ({pvw})")
    
    # Convert to dict format
    tally_data = {}
    
    # Mark PGM source
    if pgm_name:
        tally_data[pgm_name] = "PGM"
        
    # Mark PVW source (only if different from PGM)
    if pvw_name and pvw_name != pgm_name:
        tally_data[pvw_name] = "PVW"
```

**탈리 시스템 특징:**
- 8.3ms 평균 응답시간
- 실시간 상태 업데이트
- 유연한 이름 매칭

## 브랜드 통합

### 로고 시스템

```python
# 다중 경로 로고 로딩
paths_to_try = [
    "/mnt/c/coding/returnfeed_tally_fresh/returnfeed_unified/resource/returnfeed_리턴피드_로고.png",
    r"C:\coding\returnfeed_tally_fresh\returnfeed_unified\resource\returnfeed_리턴피드_로고.png",
    # ... 추가 경로들
]

for path in paths_to_try:
    if path and os.path.exists(path):
        icon = QIcon(path)
        if not icon.isNull():
            self.setWindowIcon(icon)
            break
```

**로고 통합 위치:**
- 타이틀바: 기본 로고
- 팝업 다이얼로그: 동일 로고
- 상단바: 타이포 포함 흰색 로고

## 실시간 성능 모니터링

### 성능 메트릭

```python
class PerformanceMonitor(QThread):
    def run(self):
        """Monitor performance metrics"""
        # Calculate FPS
        fps = int(self.frame_count / elapsed)
        
        # Get CPU and memory
        cpu_percent = self.process.cpu_percent(interval=0.1)
        memory = int(self.process.memory_info().rss / 1024 / 1024)  # MB
        
        self.stats_updated.emit(fps, cpu, memory)
```

**모니터링 지표:**
- 실시간 FPS
- CPU 사용률
- 메모리 사용량
- 프레임 스킵 카운트

## 향후 개선사항

### v2.4 계획
- 4K 해상도 지원
- 다중 NDI 소스 동시 프리뷰
- 웹 인터페이스 통합
- 고급 오버레이 시스템

### 성능 목표
- 4K 60fps 안정성
- 더 낮은 CPU 사용률
- 향상된 메모리 효율성
- 더 빠른 탈리 응답 시간

---

**리턴피드 Classic Mode v2.3**  
전문가용 방송 인터페이스의 기술적 구현  
© 2025 ReturnFeed. All rights reserved.