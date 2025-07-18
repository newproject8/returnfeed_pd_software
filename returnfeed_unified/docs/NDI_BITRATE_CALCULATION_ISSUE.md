# NDI 비트레이트 계산 문제 상세 분석

## 현재 상황

### 증상
- GUI에서 비트레이트가 "<0.1 Mbps" 또는 매우 낮은 값으로 표시됨
- 실제 네트워크 트래픽과 일치하지 않는 값이 표시됨
- NDI 기술문서의 표준값(FHD 60fps = 160Mbps)과 큰 차이를 보임

### 현재 구현 방식
```python
# returnfeed_unified/modules/ndi_module/ndi_receiver.py

# 현재 방식: NDI 기술문서 기반 "추정" 비트레이트
if self.bandwidth_mode == "lowest":
    base_bitrate = 4.0  # FHD 프록시 모드
else:
    base_bitrate = 160.0  # FHD 일반 모드

# FPS 기반 조정
mbps = base_bitrate * (fps / 30.0)
```

## 근본적인 문제

### 1. NDI SDK의 한계
- **v_frame.data는 디코딩된 raw 데이터**: 네트워크로 전송된 압축 데이터가 아님
- **실제 네트워크 바이트를 측정할 방법이 없음**: NDI SDK에서 제공하지 않음
- **압축률을 알 수 없음**: SpeedHQ 코덱의 실시간 압축률은 콘텐츠에 따라 가변적

### 2. 계산 방식의 문제점

#### 시도했던 방법들:
1. **raw 데이터 크기 기반 계산**
   ```python
   raw_size = v_frame.data.nbytes  # 예: 1920x1080x4 = 8,294,400 bytes
   estimated_compressed = raw_size // 6  # 압축률 추정
   ```
   - 문제: 압축률이 고정값이 아님, 실제와 큰 차이

2. **프레임 수 기반 계산**
   ```python
   fps_frame_count += 1
   if elapsed >= 1.0:
       mbps = calculate_from_fps(fps_frame_count)
   ```
   - 문제: 프레임 드롭이나 버퍼링 시 부정확

3. **표준 비트레이트 사용 (현재)**
   - 문제: 실측값이 아닌 이론값만 표시

### 3. NDI의 실제 동작 방식
- **SpeedHQ 코덱**: 가변 비트레이트 (VBR) 사용
- **콘텐츠 적응형**: 복잡한 영상은 높은 비트레이트, 단순한 영상은 낮은 비트레이트
- **프록시 모드**: H.264 수준의 높은 압축률 (원본의 1/20~1/40)

## 가능한 해결 방안

### 방안 1: 네트워크 레벨 측정
```python
# psutil을 사용한 네트워크 인터페이스 모니터링
import psutil

# NDI가 사용하는 포트의 트래픽 측정
# 문제: NDI가 사용하는 정확한 연결을 식별하기 어려움
```

### 방안 2: NDI SDK 메타데이터 활용
```python
# NDI 메타데이터에서 비트레이트 정보 찾기
if hasattr(v_frame, 'metadata'):
    # 메타데이터에 비트레이트 정보가 있는지 확인
    pass
```

### 방안 3: 표시 방식 변경
- "측정 비트레이트" 대신 "예상 비트레이트" 또는 "표준 비트레이트"로 표시
- 또는 비트레이트 표시를 제거하고 해상도/FPS만 표시

### 방안 4: NDI Tools 연동
- NDI Studio Monitor가 표시하는 비트레이트 값 참조
- 문제: 외부 도구 의존성

## 기술적 제약사항

1. **NDI SDK 제한**
   - recv_capture_v2() 함수는 압축된 데이터 크기를 반환하지 않음
   - 네트워크 레벨 정보에 접근할 수 없음

2. **Python NDI 바인딩 제한**
   - C++ SDK의 모든 기능이 노출되지 않음
   - 저수준 네트워크 정보 접근 불가

3. **실시간 처리 요구사항**
   - 비트레이트 계산이 프레임 처리 성능에 영향을 주면 안 됨
   - 60fps 처리를 위해 16.67ms 내에 모든 작업 완료 필요

## 권장 사항

### 단기 해결책
1. 현재의 "표준 비트레이트" 표시를 유지하되, UI에 "약 ~Mbps" 또는 "표준: ~Mbps"로 표시
2. 툴팁에 "NDI 표준 비트레이트 기준" 설명 추가

### 장기 해결책
1. NDI SDK 업데이트 시 네트워크 통계 API 추가 여부 확인
2. 시스템 레벨 네트워크 모니터링 통합 고려
3. NDI 공식 포럼에 비트레이트 측정 방법 문의

## 참고 자료
- [NDI SDK Documentation](https://docs.ndi.video/)
- [SpeedHQ Codec Whitepaper](https://docs.ndi.video/docs/tech-ref/codec)
- NDI Studio Monitor 소스 코드 (있다면 참조)

## 결론
현재 NDI SDK의 제약으로 인해 **실제 네트워크 비트레이트를 정확히 측정하는 것은 불가능**합니다. 
표시되는 값은 NDI 기술문서 기반의 **이론적 표준값**이며, 실제 네트워크 사용량과는 차이가 있을 수 있습니다.