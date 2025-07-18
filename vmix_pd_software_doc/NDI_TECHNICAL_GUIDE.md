# NDI Technical Implementation Guide

## Table of Contents
1. [NDI Technology Overview](#ndi-technology-overview)
2. [Python NDI Libraries Comparison](#python-ndi-libraries-comparison)
3. [Frame Rate Implementation (59.94fps)](#frame-rate-implementation)
4. [16:9 Aspect Ratio Implementation](#aspect-ratio-implementation)
5. [Performance Optimization](#performance-optimization)
6. [Common Issues and Solutions](#common-issues-and-solutions)
7. [Code Examples](#code-examples)

## NDI Technology Overview

### What is NDI?
Network Device Interface (NDI) is a royalty-free software standard developed by NewTek to enable video-compatible products to communicate, deliver, and receive high-definition video over a computer network in real-time with low latency.

### Key Features
- **Low Latency**: Typically 1-2 frames of delay
- **High Quality**: Supports up to 4K resolution at 60fps
- **Network Efficient**: Uses compression to minimize bandwidth
- **Discovery**: Automatic source discovery on the network
- **Bi-directional**: Supports video, audio, and metadata

### NDI in Broadcasting
NDI has become the de facto standard for IP video in broadcasting due to:
- Easy integration with existing infrastructure
- Support from major broadcast software (vMix, OBS, Wirecast)
- Scalability from small studios to large facilities
- Cost-effectiveness compared to traditional SDI

## Python NDI Libraries Comparison

### 1. ndi-python
**Pros:**
- More Pythonic API design
- Better memory management
- Automatic garbage collection
- Easier frame data access

**Cons:**
- Limited to 30fps in some implementations
- Less control over low-level operations
- May have threading limitations

**Installation:**
```bash
pip install ndi-python
```

### 2. cyndilib
**Pros:**
- Direct wrapper of NDI SDK
- Full 59.94fps support
- Better performance for high frame rates
- More control over NDI operations

**Cons:**
- More complex API
- Manual memory management required
- Steeper learning curve

**Installation:**
```bash
pip install cyndilib
```

### Library Selection Guide
- **Choose ndi-python** if:
  - You need quick prototyping
  - 30fps is sufficient
  - Ease of use is priority

- **Choose cyndilib** if:
  - You need 59.94fps support
  - Performance is critical
  - You need full NDI SDK features

## Frame Rate Implementation

### Understanding 59.94fps
The 59.94fps frame rate (actually 60000/1001) is a broadcast standard derived from NTSC color television. Supporting this rate is crucial for professional broadcast applications.

### Implementation Strategy

#### 1. Event-Driven Architecture
```python
class FrameProcessor:
    def __init__(self):
        self.frame_queue = Queue(maxsize=3)
        self.processing = True
        
    def on_frame_received(self, frame):
        """Called immediately when frame arrives"""
        if not self.frame_queue.full():
            self.frame_queue.put(frame)
            self.process_frame_signal.emit()
```

#### 2. Timer Resolution Optimization
```python
if platform.system() == "Windows":
    # Set Windows multimedia timer to 1ms resolution
    import ctypes
    winmm = ctypes.WinDLL('winmm')
    winmm.timeBeginPeriod(1)
```

#### 3. Frame Timing Calculation
```python
def calculate_frame_timing(self, fps=59.94):
    """Calculate precise frame timing"""
    self.frame_duration = 1000.0 / fps  # 16.683ms for 59.94fps
    self.target_frame_time = 1.0 / fps
    self.frame_tolerance = self.frame_duration * 0.1  # 10% tolerance
```

### Frame Drop Prevention

#### 1. Triple Buffering
```python
class TripleBuffer:
    def __init__(self):
        self.buffers = [None, None, None]
        self.write_index = 0
        self.read_index = 0
        self.lock = threading.Lock()
```

#### 2. Adaptive Frame Skipping
```python
def should_skip_frame(self, current_time, last_frame_time):
    """Determine if frame should be skipped"""
    elapsed = current_time - last_frame_time
    if elapsed < self.min_frame_interval:
        return True  # Too soon, skip
    return False
```

## 16:9 Aspect Ratio Implementation

### Fixed Aspect Ratio Widget
```python
class FixedAspectRatioWidget(QLabel):
    def __init__(self, aspect_ratio=16/9):
        super().__init__()
        self.aspect_ratio = aspect_ratio
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        
    def resizeEvent(self, event):
        """Maintain aspect ratio during resize"""
        size = event.size()
        width = size.width()
        height = size.height()
        
        if width / height > self.aspect_ratio:
            # Window is wider than 16:9
            new_width = int(height * self.aspect_ratio)
            new_height = height
        else:
            # Window is taller than 16:9
            new_width = width
            new_height = int(width / self.aspect_ratio)
            
        # Center the video in the widget
        x = (width - new_width) // 2
        y = (height - new_height) // 2
        
        self.video_rect = QRect(x, y, new_width, new_height)
```

### Letterboxing Implementation
```python
def apply_letterbox(self, frame, target_size):
    """Apply letterbox to maintain aspect ratio"""
    h, w = frame.shape[:2]
    target_w, target_h = target_size
    
    # Calculate scaling factor
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # Create black background
    result = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    
    # Calculate position
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    
    # Resize and place frame
    resized = cv2.resize(frame, (new_w, new_h))
    result[y:y+new_h, x:x+new_w] = resized
    
    return result
```

## Performance Optimization

### 1. Memory Management

#### Pre-allocation
```python
class FrameBufferPool:
    def __init__(self, size=10, frame_size=(1920, 1080, 3)):
        self.pool = []
        self.frame_size = frame_size
        
        # Pre-allocate buffers
        for _ in range(size):
            buffer = np.empty(frame_size, dtype=np.uint8)
            self.pool.append(buffer)
```

#### Zero-Copy Operations
```python
def process_frame_zero_copy(self, ndi_frame):
    """Process frame without copying data"""
    # Create view instead of copy
    frame_view = np.frombuffer(
        ndi_frame.data, 
        dtype=np.uint8
    ).reshape((ndi_frame.height, ndi_frame.width, 4))
    
    # Process using view
    return frame_view[:, :, :3]  # BGR only, no alpha
```

### 2. CPU Optimization

#### Thread Affinity
```python
def set_thread_affinity(self, cpu_cores):
    """Pin thread to specific CPU cores"""
    if platform.system() == "Windows":
        import win32api, win32process
        handle = win32api.GetCurrentThread()
        mask = sum(1 << core for core in cpu_cores)
        win32process.SetThreadAffinityMask(handle, mask)
```

#### SIMD Operations
```python
# Use NumPy for SIMD-optimized operations
def convert_color_space_optimized(self, frame):
    """Optimized color conversion using NumPy"""
    # NumPy automatically uses SIMD instructions
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
```

### 3. Frame Processing Pipeline

#### Parallel Processing
```python
class ParallelFrameProcessor:
    def __init__(self, num_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.futures = []
        
    def process_frame_async(self, frame):
        """Process frame in parallel"""
        future = self.executor.submit(self.process_single_frame, frame)
        self.futures.append(future)
        
        # Clean up completed futures
        self.futures = [f for f in self.futures if not f.done()]
```

## Common Issues and Solutions

### 1. Frame Rate Drops

**Symptoms:**
- Actual FPS lower than source
- Stuttering playback
- Increasing latency

**Solutions:**
```python
# 1. Increase receiver bandwidth
receiver.set_bandwidth(cyndilib.RecvBandwidth.highest)

# 2. Optimize frame queue
frame_queue = Queue(maxsize=2)  # Smaller queue for lower latency

# 3. Skip duplicate frames
last_frame_hash = None
current_hash = hash(frame.tobytes())
if current_hash == last_frame_hash:
    continue  # Skip duplicate
```

### 2. Memory Leaks

**Prevention:**
```python
class NDIReceiver:
    def __del__(self):
        """Ensure proper cleanup"""
        if hasattr(self, 'receiver'):
            self.receiver.destroy()
        if hasattr(self, 'finder'):
            self.finder.destroy()
```

### 3. Color Space Issues

**BGRA to BGR Conversion:**
```python
def convert_ndi_frame(self, ndi_frame):
    """Properly convert NDI frame format"""
    # NDI provides BGRA, Qt needs BGR
    bgra = np.frombuffer(ndi_frame.data, dtype=np.uint8)
    bgra = bgra.reshape((ndi_frame.height, ndi_frame.width, 4))
    
    # Remove alpha channel
    bgr = bgra[:, :, :3]
    
    # Ensure continuous memory
    return np.ascontiguousarray(bgr)
```

## Code Examples

### Complete NDI Receiver Implementation
```python
import cyndilib as ndi
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

class NDIReceiver(QThread):
    frame_received = pyqtSignal(np.ndarray)
    
    def __init__(self, source_name):
        super().__init__()
        self.source_name = source_name
        self.running = False
        
        # Initialize NDI
        if not ndi.initialize():
            raise RuntimeError("Failed to initialize NDI")
            
        # Create finder
        self.finder = ndi.Finder()
        
    def find_source(self):
        """Find NDI source by name"""
        sources = self.finder.find_sources(timeout=5000)
        for source in sources:
            if self.source_name in source.name:
                return source
        return None
        
    def run(self):
        """Main receiver loop"""
        source = self.find_source()
        if not source:
            return
            
        # Create receiver
        self.receiver = ndi.Receiver(source)
        self.receiver.set_bandwidth(ndi.RecvBandwidth.highest)
        
        self.running = True
        while self.running:
            # Receive frame
            frame_type, video, audio, metadata = self.receiver.capture(100)
            
            if frame_type == ndi.FrameType.video:
                # Convert and emit
                frame = self.convert_frame(video)
                self.frame_received.emit(frame)
                
    def stop(self):
        """Stop receiver"""
        self.running = False
        self.wait()
```

### Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.frame_times = deque(maxlen=100)
        self.last_time = time.perf_counter()
        
    def record_frame(self):
        """Record frame timing"""
        current_time = time.perf_counter()
        elapsed = current_time - self.last_time
        self.frame_times.append(elapsed)
        self.last_time = current_time
        
    def get_fps(self):
        """Calculate current FPS"""
        if len(self.frame_times) < 2:
            return 0.0
        avg_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_time if avg_time > 0 else 0.0
```

## Best Practices

1. **Always use event-driven processing** instead of polling
2. **Pre-allocate buffers** for consistent performance
3. **Monitor performance metrics** to detect issues early
4. **Handle errors gracefully** with fallback options
5. **Test with actual broadcast sources** at target frame rates
6. **Profile your application** to identify bottlenecks
7. **Use native color formats** to minimize conversions

## References

- [NDI SDK Documentation](https://ndi.video/for-developers/ndi-sdk/)
- [cyndilib Documentation](https://github.com/nocarryr/cyndilib)
- [Broadcast Frame Rates Explained](https://en.wikipedia.org/wiki/Frame_rate)
- [Python Performance Optimization](https://docs.python.org/3/howto/optimization.html)