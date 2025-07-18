# NDI 프록시 모드 60fps 최적화 완료

## 문제 분석
- **현재 상태**: 프록시 모드 40fps (일반 모드는 정상)
- **마지막 커밋**: 프록시 모드 55fps
- **목표**: 프록시 모드 60fps 달성

## 발견된 차이점

### 1. 타임아웃 설정 (가장 중요!)
```python
# 마지막 커밋 (55fps)
if self.bandwidth_mode == "lowest":
    timeout_ms = 0  # Non-blocking

# 현재 코드 (40fps) - 문제!
if self.bandwidth_mode == "lowest":
    timeout_ms = 100  # 너무 긴 대기시간
```

### 2. FRAME_TYPE_NONE 처리
```python
# 마지막 커밋
elif frame_type == ndi.FRAME_TYPE_NONE:
    if self.bandwidth_mode == "lowest":
        self.msleep(8)  # CPU 사용률 제어
```

### 3. allow_video_fields 설정
```python
# 마지막 커밋
프록시: allow_video_fields = False
일반: allow_video_fields = True
```

## 적용된 최적화

### 1. 프록시 모드 비블로킹 타임아웃
- `timeout_ms = 0` (Non-blocking)
- 프레임을 최대한 빠르게 수신

### 2. CPU 사용률 제어
- FRAME_TYPE_NONE일 때 8ms 대기
- CPU 스피닝 방지하면서 성능 유지

### 3. 프레임 필드 설정
- 프록시 모드: `allow_video_fields = False`
- 일반 모드: `allow_video_fields = True`

### 4. 디버그 비활성화
- 프록시 모드에서 자동으로 디버그 비활성화
- `memory_monitor_enabled = False`

### 5. 메모리 복사 단순화
- 프록시 모드는 작은 프레임이므로 단순 복사 사용
- 복잡한 조건부 로직 제거

## 예상 결과
- 프록시 모드: 40fps → 60fps
- CPU 사용률 안정적
- 일반 모드 성능 유지

## 테스트 방법
1. 프록시 모드로 전환
2. 로그에서 FPS 확인
3. CPU 사용률 모니터링