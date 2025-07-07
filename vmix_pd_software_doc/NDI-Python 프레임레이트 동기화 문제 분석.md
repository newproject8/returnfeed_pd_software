# NDI-Python 프레임레이트 동기화 문제 분석

## 발견된 주요 프로젝트들

### 1. buresu/ndi-python
- **URL**: https://github.com/buresu/ndi-python
- **특징**: 가장 인기 있는 NDI Python 래퍼 (164 stars)
- **지원 환경**: Windows x64, macOS x64/arm64, Linux x64/aarch64 (Python 3.7-3.10)
- **주요 예제들**:
  - `recv_cv.py`: OpenCV와 NDI 조합 예제
  - `recv_framesync.py`: 프레임 동기화 예제
  - `recv_framesync_resend.py`: 프레임 동기화 재전송 예제

### recv_cv.py 코드 분석
```python
# 핵심 부분
while True:
    t, v, _, _ = ndi.recv_capture_v2(ndi_recv, 5000)
    
    if t == ndi.FRAME_TYPE_VIDEO:
        print('Video data received (%dx%d).' % (v.xres, v.yres))
        frame = np.copy(v.data)
        cv.imshow('ndi image', frame)
        ndi.recv_free_video_v2(ndi_recv, v)
    
    if cv.waitKey(1) & 0xff == 27:
        break
```

**문제점 발견**:
1. `recv_capture_v2`에서 5000ms 타임아웃 사용 - 너무 긴 대기시간
2. 프레임레이트 제어 없음 - OpenCV의 `waitKey(1)`만 사용
3. NDI 스트림의 실제 프레임레이트를 고려하지 않음




### 2. nocarryr/cyndilib
- **URL**: https://github.com/nocarryr/cyndilib
- **특징**: Cython으로 작성된 고성능 NDI 래퍼 (25 stars)
- **장점**: 실시간 오디오/비디오 처리에 최적화된 Cython 구현
- **주요 예제들**:
  - `viewer.py`: Kivy GUI와 NDI 조합 예제 (398 lines)
  - `ffmpeg_sender.py`: FFmpeg 기반 송신 예제
  - `ffplay_receiver.py`: FFplay 기반 수신 예제

### viewer.py 코드 분석 (Kivy + NDI)
```python
# 주요 import들
from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.finder import Finder, Source
from cyndilib.receiver import Receiver, ReceiveFrameType
from cyndilib.video_frame import VideoFrameSync
from cyndilib.audio_frame import AudioFrameSync
from cyndilib.framesync import FrameSyncThread

# 핵심 특징
- Kivy GUI 프레임워크 사용
- FrameSyncThread를 통한 프레임 동기화
- VideoFrameSync, AudioFrameSync 클래스 활용
- 고성능 Cython 구현
```

**cyndilib의 장점**:
1. **FrameSyncThread**: 전용 스레드에서 프레임 동기화 처리
2. **VideoFrameSync**: 비디오 프레임 동기화 전용 클래스
3. **Cython 최적화**: 실시간 처리에 최적화된 성능
4. **정확한 타이밍**: NDI 스트림의 원본 프레임레이트 유지


## NDI SDK 공식 성능 가이드라인

### 비디오 수신 최적화 (NDI 공식 권장사항)
1. **별도 스레드 사용**: 오디오와 비디오를 위해 `NDIlib_recv_capture_v3`를 별도 스레드에서 호출
2. **멀티스레드 안전**: `NDIlib_recv_capture_v3`는 멀티스레드 안전하므로 여러 스레드가 동시에 대기 가능
3. **적절한 타임아웃**: 0 타임아웃으로 폴링하는 것보다 적절한 타임아웃 사용이 효율적
4. **최고 성능 컬러 포맷**: `NDIlib_recv_color_format_fastest` 사용 권장

### 주요 문제점 식별

#### 기존 코드의 문제점들:
1. **단일 스레드 처리**: GUI 스레드에서 NDI 수신 처리
2. **부적절한 타이밍**: `time.sleep(33/1000)` 같은 고정 딜레이 사용
3. **프레임레이트 무시**: NDI 스트림의 실제 프레임레이트를 고려하지 않음
4. **GUI 블로킹**: NDI 수신이 GUI를 블로킹할 수 있음

#### 해결해야 할 핵심 문제:
1. **프레임 드롭**: 원본 59.94fps → GUI에서 더 낮은 fps로 표시
2. **동기화 부족**: NDI 스트림의 타이밍과 GUI 업데이트 타이밍 불일치
3. **성능 최적화**: CPU 사용량과 메모리 대역폭 최적화 필요

