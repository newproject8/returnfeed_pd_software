# NDI 최적화 및 동적 비트레이트 계산 문서

## 개요

이 문서는 리턴피드 통합 소프트웨어의 NDI 처리 시스템과 동적 비트레이트 계산 알고리즘에 대한 기술적 분석을 제공합니다.

## NDI 압축 시스템 분석

### 같은 PC 내부 NDI 동작 원리

**핵심 발견사항:**
- 같은 PC 내부에서 NDI 송수신 시 (예: vMix → NDI Studio Monitor) 압축 단계를 건너뛰고 무압축 트래픽으로 처리될 수 있음
- 이는 기존의 임의 추론 기반 압축률 계산을 무효화함
- 실제 프레임 크기 기반 동적 계산이 필요함

### 압축 vs 무압축 감지 알고리즘

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
    
    # 해상도별 압축률 적용
    if width >= 1920:  # 1080p 이상
        if self.bandwidth_mode == "highest":
            return raw_mbps * 0.15  # 15% 압축률
        else:
            return raw_mbps * 0.05  # 5% 압축률 (프록시)
    elif width >= 1280:  # 720p
        if self.bandwidth_mode == "highest":
            return raw_mbps * 0.20
        else:
            return raw_mbps * 0.08
    else:  # 480p 이하
        if self.bandwidth_mode == "highest":
            return raw_mbps * 0.25
        else:
            return raw_mbps * 0.10
```

## 프레임 데이터 분석

### line_stride_in_bytes 활용

```python
def _process_frame_data(self, frame_data):
    """프레임 데이터 처리 및 크기 계산"""
    if hasattr(frame_data, 'line_stride_in_bytes') and frame_data.line_stride_in_bytes:
        # 실제 프레임 크기 계산
        height = frame_data.yres
        actual_frame_size = frame_data.line_stride_in_bytes * height
        
        # 동적 비트레이트 계산에 사용
        bitrate = self._calculate_dynamic_bitrate(
            frame_data.xres, 
            frame_data.yres, 
            fps, 
            actual_frame_size
        )
```

**핵심 데이터 포인트:**
- `line_stride_in_bytes`: 실제 라인당 바이트 수
- `xres`, `yres`: 해상도 정보
- 실제 프레임 크기 = line_stride_in_bytes × height

### 압축률 임계값 결정

```python
# 무압축 판정 기준
if actual_mbps > raw_mbps * 0.8:
    return actual_mbps  # 무압축으로 판정
```

**임계값 선택 근거:**
- 80% 이상: 무압축 또는 매우 낮은 압축률
- 이론적 raw 대비 실제 크기 비교
- 네트워크 오버헤드 고려

## 대역폭 모드별 최적화

### 일반 모드 (Highest Bandwidth)

```python
if self.bandwidth_mode == "highest":
    # 고품질 모드
    - 높은 비트레이트 허용
    - 더 나은 화질
    - 더 많은 네트워크 대역폭 사용
    
    # 프레임 버퍼 크기
    self.max_frame_buffer = 2  # 안정적인 버퍼링
```

### 프록시 모드 (Lowest Bandwidth)

```python
if self.bandwidth_mode == "lowest":
    # 저대역폭 모드
    - 낮은 비트레이트로 제한
    - 압축률 증가
    - 네트워크 효율성 우선
    
    # 프레임 버퍼 크기
    self.max_frame_buffer = 1  # 최소 버퍼로 지연 방지
```

### 프레임 보간 시스템

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

**프레임 보간 특징:**
- 프록시 모드에서 프레임 부족 시 이전 프레임 재사용
- 60fps 안정성 유지
- is_interpolated 플래그로 보간 프레임 표시

## 성능 최적화 전략

### 60fps 안정성 보장

```python
# 정확한 타이밍 타이머
self.frame_timer = QTimer()
self.frame_timer.timeout.connect(self._process_frame_queue)
self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
self.frame_timer.setInterval(16)  # 60fps = 16.67ms
```

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

**최적화 기법:**
- 스트리밍 시 불필요한 프레임 처리 생략
- 적응형 프레임 큐 크기
- 오래된 프레임 자동 폐기

## 실시간 비트레이트 표시

### UI 업데이트

```python
def update_frame_info(self, info):
    """프레임 정보 업데이트"""
    bitrate_str = info.get('bitrate', '계산 중...')
    self.bitrate_label.setText(f"비트레이트: {bitrate_str}")
    
    # 동적 색상 변경
    if "Mbps" in bitrate_str:
        try:
            mbps_value = float(bitrate_str.split()[0])
            if mbps_value > 100:
                self.bitrate_label.setStyleSheet("color: #F44336;")  # 빨간색 (높음)
            elif mbps_value > 50:
                self.bitrate_label.setStyleSheet("color: #FF9800;")  # 주황색 (중간)
            else:
                self.bitrate_label.setStyleSheet("color: #4CAF50;")  # 녹색 (낮음)
        except:
            pass
```

### 실시간 계산 표시

```python
def _format_bitrate(self, bitrate_mbps):
    """비트레이트 포맷팅"""
    if bitrate_mbps >= 1000:
        return f"{bitrate_mbps/1000:.1f} Gbps"
    elif bitrate_mbps >= 1:
        return f"{bitrate_mbps:.1f} Mbps"
    else:
        return f"{bitrate_mbps*1000:.0f} Kbps"
```

## 네트워크 최적화

### 대역폭 감지

```python
def _detect_network_bandwidth(self):
    """네트워크 대역폭 감지"""
    # 프레임 드롭 횟수 기반 대역폭 상태 판정
    if self.frame_skip_count > 10:  # 최근 10프레임 스킵
        # 네트워크 대역폭 부족 감지
        self._suggest_bandwidth_mode("proxy")
    elif self.frame_skip_count == 0:
        # 안정적인 네트워크 상태
        self._suggest_bandwidth_mode("normal")
```

### 자동 품질 조절

```python
def _adjust_quality_automatically(self):
    """자동 품질 조절"""
    current_fps = self.performance_monitor.get_current_fps()
    
    if current_fps < 50:  # 50fps 이하로 떨어지면
        if self.current_bandwidth_mode == "normal":
            self._switch_to_proxy_mode()
    elif current_fps > 58:  # 58fps 이상 안정적이면
        if self.current_bandwidth_mode == "proxy":
            self._switch_to_normal_mode()
```

## 디버깅 및 분석 도구

### 비트레이트 분석 로그

```python
def _log_bitrate_analysis(self, frame_data, calculated_bitrate):
    """비트레이트 분석 로그"""
    logger.debug(f"""
    NDI 프레임 분석:
    - 해상도: {frame_data.xres}x{frame_data.yres}
    - Line Stride: {frame_data.line_stride_in_bytes} bytes
    - 실제 프레임 크기: {frame_data.line_stride_in_bytes * frame_data.yres} bytes
    - 계산된 비트레이트: {calculated_bitrate:.2f} Mbps
    - 압축 모드: {'무압축' if calculated_bitrate > 100 else '압축됨'}
    """)
```

### 성능 메트릭

```python
class NDIPerformanceMetrics:
    def __init__(self):
        self.frame_count = 0
        self.total_frame_size = 0
        self.compression_ratio_history = []
        
    def add_frame(self, frame_size, calculated_bitrate):
        self.frame_count += 1
        self.total_frame_size += frame_size
        
        # 압축률 계산
        raw_size = frame_size * 8  # 이론적 raw 크기
        compression_ratio = calculated_bitrate / raw_size if raw_size > 0 else 0
        self.compression_ratio_history.append(compression_ratio)
        
    def get_average_compression_ratio(self):
        if not self.compression_ratio_history:
            return 0
        return sum(self.compression_ratio_history) / len(self.compression_ratio_history)
```

## 향후 개선 방향

### v2.4 계획
- 4K 해상도 지원
- 더 정확한 압축률 예측
- 기계학습 기반 품질 조절
- 네트워크 상태 자동 감지

### 성능 목표
- 4K 60fps 안정성
- 더 낮은 CPU 사용률
- 향상된 압축률 예측
- 실시간 네트워크 적응

## 결론

동적 비트레이트 계산 시스템은 다음과 같은 주요 이점을 제공합니다:

1. **정확한 대역폭 측정**: 실제 프레임 크기 기반 계산
2. **압축 상태 감지**: 같은 PC 내부 무압축 트래픽 감지
3. **성능 최적화**: 프록시 모드 프레임 보간으로 60fps 유지
4. **실시간 피드백**: 사용자에게 정확한 네트워크 상태 정보 제공

이 시스템은 기존의 임의 추론 기반 계산을 대체하여 더 정확하고 실용적인 NDI 대역폭 관리를 제공합니다.

---

**리턴피드 NDI 최적화 시스템 v2.3**  
실제 데이터 기반 동적 비트레이트 계산  
© 2025 ReturnFeed. All rights reserved.