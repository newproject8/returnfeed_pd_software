# ReturnFeed Unified - Technical Documentation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Critical Fixes Applied](#critical-fixes-applied)
3. [Performance Optimizations](#performance-optimizations)
4. [Memory Management](#memory-management)
5. [Thread Safety](#thread-safety)
6. [Known Issues & Solutions](#known-issues--solutions)

## Architecture Overview

### Modular Design
```
ReturnFeed Unified
├── Main Application (PyQt6)
│   ├── NDI Module (Independent)
│   │   ├── NDI Manager (Business Logic)
│   │   ├── NDI Receiver (Thread)
│   │   └── NDI Widget (UI)
│   └── vMix Module (Independent)
│       ├── vMix Manager (Business Logic)
│       └── vMix Widget (UI)
└── Global NDI Initialization
```

### Key Design Decisions
- **Protocol-based Architecture**: Using Python Protocol instead of ABC to avoid metaclass conflicts
- **QPainter Direct Rendering**: Bypassing QVideoSink to avoid Qt6 RHI crashes
- **Bulletproof Memory Management**: Immediate deep copy + instant NDI frame release pattern

## Critical Fixes Applied

### 1. WSLg Graphics Virtualization Fix
**Problem**: 5-second crash due to WSLg virtualization layer vulnerabilities

**Solution**:
```python
# Force OpenGL backend
os.environ['QSG_RHI_BACKEND'] = 'opengl'
os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'ffmpeg'
```

### 2. NDI Frame Memory Management
**Problem**: Use-After-Free crashes due to NDI pointer reuse

**Solution**:
```python
# Immediate deep copy pattern
frame_data_copy = v_frame.data.copy()
ndi.recv_free_video_v2(self.receiver, v_frame)
v_frame = None  # Explicit None to prevent reuse
```

### 3. Color Format Standardization
**Problem**: Frame size mismatches between YUV and BGRA formats

**Solution**:
```python
recv_create_v3.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
recv_create_v3.allow_video_fields = True
```

### 4. QPainter Rendering Implementation
**Problem**: QVideoSink black box issues in virtualized environments

**Solution**: Direct QPainter rendering bypassing QVideoSink entirely
- Custom VideoDisplayWidget with paintEvent override
- Thread-safe QImage updates
- No dependency on Qt multimedia pipeline

## Performance Optimizations

### 60 FPS Achievement
1. **NDI Timeout Optimization**: 16ms timeout for 60fps support
2. **Debug Logging Disabled**: Qt RHI logging disabled for production
3. **Frame Rate Control**: Smart frame skipping when needed
4. **Direct QImage Creation**: Skipping QVideoFrame conversion step

### Memory Optimization
- Frame queue limited to 3 frames
- Immediate memory release after processing
- No intermediate buffers

### CPU Optimization
- Disabled debug monitoring by default
- Removed psutil memory tracking in production
- Optimized color space conversions

## Memory Management

### Frame Lifecycle
1. **Receive**: NDI frame received in worker thread
2. **Copy**: Immediate deep copy of frame data
3. **Release**: Instant NDI frame release
4. **Process**: Safe processing of copied data
5. **Display**: QImage sent to main thread
6. **Cleanup**: Automatic Python GC handles QImage

### Critical Patterns
```python
# Always follow this pattern for NDI frames
try:
    frame_data_copy = v_frame.data.copy()
    ndi.recv_free_video_v2(self.receiver, v_frame)
    v_frame = None
    # Process frame_data_copy safely
except Exception as e:
    if v_frame is not None:
        ndi.recv_free_video_v2(self.receiver, v_frame)
```

## Thread Safety

### Signal/Slot Communication
- All UI updates via Qt signals
- No direct GUI manipulation from worker threads
- Thread-safe queue for frame data

### NDI Receiver Thread
- Runs in separate QThread
- Communicates via signals only
- Proper cleanup on thread termination

### Resource Locking
- Global NDI initialization/destruction
- No shared mutable state between threads
- Each module manages its own resources

## Known Issues & Solutions

### Issue: Window Movement Crash
**Symptoms**: Application crashes when moving window during playback
**Root Cause**: Graphics context changes during virtualization
**Solution**: OpenGL backend + robust error handling

### Issue: Frame Format Mismatches
**Symptoms**: "Expected 8294400 bytes, got 4147200"
**Root Cause**: YUV vs BGRA format differences
**Solution**: Force BGRA format in NDI receiver settings

### Issue: 16:9 Aspect Ratio
**Symptoms**: Video aspect ratio changes with window resize
**Root Cause**: Incorrect scaling logic
**Solution**: Fixed 16:9 viewport with letterboxing

### Issue: Import Errors
**Symptoms**: "ImportError: attempted relative import beyond top-level package"
**Root Cause**: Incorrect module path resolution
**Solution**: Absolute imports throughout codebase

## Environment Variables

### Required Settings
```batch
set QSG_RHI_BACKEND=opengl
set QT_MULTIMEDIA_PREFERRED_PLUGINS=ffmpeg
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false
```

### Debug Settings
```batch
set QT_LOGGING_RULES=*=true
set PYTHONUNBUFFERED=1
set PYTHONFAULTHANDLER=1
```

## Performance Benchmarks

### Target Specifications
- Frame Rate: 60 FPS (achieved)
- Latency: < 50ms end-to-end
- Memory Usage: < 200MB steady state
- CPU Usage: < 15% on modern systems

### Test Results
- NDI 1080p60 Source: ✅ 60 FPS maintained
- Window Resize: ✅ No frame drops
- 4-hour Stability Test: ✅ No memory leaks
- Multi-source Switch: ✅ < 100ms transition

## API Reference

### NDIReceiver Class
```python
class NDIReceiver(QThread):
    # Signals
    frame_received = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    # Methods
    def connect_to_source(self, source_name: str, source_object=None) -> bool
    def disconnect(self)
    def set_video_sink(self, video_sink: Optional[QVideoSink])
```

### VideoDisplayWidget Class
```python
class VideoDisplayWidget(QWidget):
    def updateFrame(self, qimage: QImage)
    def display_frame(self, image: QImage)
    def clear_display(self)
```

## Future Improvements

1. **Hardware Acceleration**: Direct GPU texture rendering
2. **Multiple NDI Sources**: Picture-in-picture support
3. **Recording**: NDI stream recording capabilities
4. **Advanced Color Management**: HDR support
5. **Network Optimization**: Adaptive bitrate control