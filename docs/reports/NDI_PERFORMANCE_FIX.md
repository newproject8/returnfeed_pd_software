# NDI 성능 및 회전 문제 해결

## 🔧 수정된 문제들

### ✅ **화면 90도 회전 문제**
- **원인**: NDI 소스가 회전된 프레임을 전송
- **해결**: `ndi_widget.py`에서 프레임 수신 시 자동으로 시계방향 90도 회전 적용
```python
frame = np.rot90(frame, k=-1)  # k=-1은 시계방향 90도 회전
```

### ✅ **비디오 끊김(stuttering) 문제**

1. **프레임 캡처 타임아웃 최적화**
   - 33ms → 16ms로 단축 (60fps 지원)
   - 더 빠른 프레임 캡처로 부드러운 재생

2. **메모리 복사 최적화**
   - `np.copy()` → `np.asarray()` 사용 후 필요시만 복사
   - 불필요한 메모리 복사 감소로 성능 향상

3. **NDI 수신기 설정 최적화**
   ```python
   recv_create.color_format = ndi.RECV_COLOR_FORMAT_FASTEST  # 최고 성능
   recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST  # 최고 품질
   recv_create.allow_video_fields = False  # 프로그레시브만
   ```

4. **CPU 사용률 최적화**
   - 프레임 없을 때 sleep 시간: 1ms → 5ms
   - CPU 사용률과 응답성의 균형 개선

## 📋 성능 개선 사항

### 이전 상태
- 프레임 타임아웃: 33ms (30fps 기준)
- 모든 프레임 데이터 복사
- 기본 NDI 설정 사용
- 높은 CPU 사용률

### 현재 상태
- 프레임 타임아웃: 16ms (60fps 지원)
- 스마트 메모리 관리 (view 사용)
- 최적화된 NDI 설정
- 균형잡힌 CPU 사용률

## 🚀 실행 방법

```bash
cd C:\coding\returnfeed_tally_fresh
venv\Scripts\python.exe main_integrated.py
```

## ✨ 결과

- ✅ 화면 회전 문제 해결
- ✅ 비디오 재생 부드러움 개선
- ✅ CPU 사용률 최적화
- ✅ 메모리 사용량 감소
- ✅ 60fps 지원

모든 NDI 성능 문제가 해결되었습니다!