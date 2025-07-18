# 현재 비트레이트 표시 버그 상세 분석

## 버그 증상
- 비트레이트가 지속적으로 "<0.1 Mbps"로 표시됨
- 로그에는 정상적인 FPS (프록시: 60fps, 일반: 40-50fps)가 표시됨
- 하지만 비트레이트는 거의 0에 가까운 값으로 계산됨

## 현재 코드 분석

### ndi_receiver.py의 비트레이트 계산 부분
```python
# 406줄부터
if hasattr(v_frame, 'xres') and hasattr(v_frame, 'yres'):
    width, height = v_frame.xres, v_frame.yres
    
    # 비트레이트 계산
    fps = max(int(self.current_fps), 1)  # 최소 1fps
    
    # 표준 비트레이트 설정
    if self.bandwidth_mode == "lowest":
        base_bitrate = 4.0  # FHD 프록시
    else:
        base_bitrate = 160.0  # FHD 일반
    
    # FPS 기반 조정
    mbps = base_bitrate * (fps / 30.0)
```

## 문제점 발견

### 1. 타이밍 이슈
- `self.current_fps`가 아직 계산되지 않은 시점에 비트레이트를 계산할 가능성
- 초기값이 0이므로 `max(int(0), 1) = 1`이 되어 매우 낮은 값 계산

### 2. FPS 계산 위치
```python
# 369줄 - FPS 계산
if self.fps_calc_start_time == 0:
    self.fps_calc_start_time = current_time
    self.fps_frame_count = 0
elif current_time - self.fps_calc_start_time >= 1.0:
    self.current_fps = self.fps_frame_count / (current_time - self.fps_calc_start_time)
```
- FPS는 1초마다 업데이트되지만, 비트레이트는 매 프레임마다 계산됨

### 3. 비트레이트 계산 주기
- 현재: 매 프레임마다 계산 (불필요한 오버헤드)
- 문제: FPS가 업데이트되기 전에 계산되면 이전 값 사용

### 4. 초기화 문제
```python
# 69-72줄
self.current_fps = 0.0
self.current_bitrate = "0 Mbps"
```
- 초기값이 0이므로 첫 1초 동안은 항상 낮은 비트레이트 표시

## 실제 동작 시나리오

1. **프로그램 시작**
   - current_fps = 0.0
   - 비트레이트 계산: base_bitrate * (1 / 30.0) = 매우 작은 값

2. **첫 1초 동안**
   - 프레임은 수신되지만 FPS는 아직 0
   - 비트레이트는 계속 최소값으로 계산

3. **1초 후**
   - FPS가 업데이트되지만 비트레이트 계산 로직이 잘못되어 있을 가능성

## 해결 방안

### 즉시 적용 가능한 수정
1. 비트레이트 계산을 FPS 업데이트와 동기화
2. 초기 1초 동안은 "계산 중..." 표시
3. FPS가 0일 때는 비트레이트 계산 건너뛰기

### 코드 수정 제안
```python
# FPS가 계산된 후에만 비트레이트 업데이트
if self.current_fps > 0:
    # 비트레이트 계산
    fps = int(self.current_fps)
    # ... 나머지 계산
else:
    self.current_bitrate = "계산 중..."
```

## 디버깅 제안
1. 로그 추가하여 각 단계의 값 확인
   - current_fps 값
   - base_bitrate 값
   - 최종 mbps 값

2. 비트레이트 계산 주기를 FPS 계산과 동일하게 (1초마다)

3. 프레임별 데이터 크기 누적하여 실제 처리량 계산 시도