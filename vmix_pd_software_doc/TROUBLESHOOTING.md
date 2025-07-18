# Troubleshooting Guide - PD Integrated Software

## Quick Diagnosis Checklist

Before diving into specific issues, run through this checklist:

1. ✓ Python version 3.8 or higher installed
2. ✓ All dependencies installed (`pip install -r requirements.txt`)
3. ✓ NDI SDK installed (or using simulator mode)
4. ✓ vMix running with Web Controller enabled
5. ✓ Firewall allows ports: 5353 (mDNS), 8088 (vMix HTTP), 8099 (vMix TCP), 8765 (WebSocket)
6. ✓ Running as Administrator (for network permissions)

## Common Issues and Solutions

### 1. NDI Preview Issues

#### No NDI Sources Found
**Symptoms:**
- Empty source list
- "No NDI sources found" message
- Discovery timeout

**Solutions:**
```bash
# 1. Check NDI service
ndi-directory-service.exe

# 2. Test with NDI Test Pattern
"C:\Program Files\NDI\NDI 6 SDK\Tools\x64\NDI Test Pattern.exe"

# 3. Enable NDI Simulator mode
python run_pd_complete.py --ndi-simulator
```

**Network Fixes:**
- Disable Windows Firewall temporarily
- Ensure devices on same subnet
- Check mDNS (port 5353) not blocked
- Try direct IP connection instead of discovery

#### Frame Rate Issues (Not Achieving 59.94fps)

**Problem Analysis:**
```python
# Timer-based approach (WRONG - limits to 30fps)
self.timer = QTimer()
self.timer.timeout.connect(self.update_frame)
self.timer.start(16)  # Still won't achieve 59.94fps
```

**Solution - Event-Driven Architecture:**
```python
# Correct implementation
class NDIReceiver(QThread):
    def run(self):
        while self.running:
            # Direct frame capture without timer
            frame = self.capture_frame()
            if frame:
                self.frame_signal.emit(frame)
                # No artificial delay
```

**Additional Optimizations:**
1. Set Windows multimedia timer to 1ms
2. Use high-priority thread for capture
3. Implement frame queue with size limit
4. Skip duplicate frames

#### 16:9 Aspect Ratio Not Maintained

**Solution:**
```python
def maintain_aspect_ratio(self, widget_size, aspect_ratio=16/9):
    width = widget_size.width()
    height = widget_size.height()
    
    if width / height > aspect_ratio:
        # Widget wider than 16:9
        new_height = height
        new_width = int(height * aspect_ratio)
    else:
        # Widget taller than 16:9
        new_width = width
        new_height = int(width / aspect_ratio)
    
    # Center in widget
    x = (width - new_width) // 2
    y = (height - new_height) // 2
    
    return QRect(x, y, new_width, new_height)
```

### 2. GUI Freezing Issues

#### Python GIL (Global Interpreter Lock) Problems

**Symptoms:**
- GUI becomes unresponsive during frame processing
- Mouse clicks delayed
- Window can't be moved smoothly

**Root Cause:**
Python's GIL prevents true parallel execution, causing GUI thread starvation.

**Solutions:**

1. **Move Heavy Processing to Threads:**
```python
class FrameProcessor(QThread):
    processed = pyqtSignal(QImage)
    
    def __init__(self):
        super().__init__()
        self.queue = Queue()
        
    def process(self, frame):
        # Don't block, queue it
        self.queue.put(frame)
        
    def run(self):
        while True:
            frame = self.queue.get()
            # Heavy processing here
            processed = self.heavy_process(frame)
            self.processed.emit(processed)
```

2. **Use Process Pool for CPU-Intensive Tasks:**
```python
from multiprocessing import Pool

class FrameProcessorMP:
    def __init__(self):
        self.pool = Pool(processes=4)
        
    def process_async(self, frame):
        # Bypass GIL completely
        future = self.pool.apply_async(process_frame_func, (frame,))
        return future
```

3. **Optimize Frame Processing:**
- Use NumPy vectorized operations
- Implement frame skipping
- Reduce unnecessary copies

### 3. vMix Connection Problems

#### Cannot Connect to vMix

**Diagnostic Steps:**
```python
# Test vMix connectivity
import requests

def test_vmix_connection(host='127.0.0.1', port=8088):
    try:
        response = requests.get(f'http://{host}:{port}/api', timeout=2)
        if response.status_code == 200:
            print("✓ vMix API accessible")
            return True
    except Exception as e:
        print(f"✗ vMix connection failed: {e}")
        return False
```

**Common Fixes:**
1. Enable vMix Web Controller (Settings → Web Controller)
2. Disable authentication or provide credentials
3. Check Windows Firewall exceptions
4. Verify vMix is running on expected port

#### Tally Updates Delayed or Missing

**Solutions:**
1. Reduce polling interval to 50ms
2. Use TCP connection instead of HTTP
3. Implement connection pooling
4. Check vMix performance (CPU usage)

### 4. Performance Problems

#### High CPU Usage

**Profiling Code:**
```python
import cProfile
import pstats

def profile_app():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run your app
    app.exec()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

**Common Culprits:**
1. Unnecessary frame copies
2. Inefficient color space conversions
3. Excessive logging
4. Memory allocation in hot loops

**Optimizations:**
```python
# Bad: Multiple copies
frame_copy = frame.copy()
rgb_frame = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
final_frame = rgb_frame.copy()

# Good: In-place operations
cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, dst=frame)
```

#### Memory Leaks

**Detection:**
```python
import tracemalloc
import gc

# Start tracing
tracemalloc.start()

# ... run for a while ...

# Take snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("[ Top 10 memory allocations ]")
for stat in top_stats[:10]:
    print(stat)
```

**Common Leak Sources:**
1. Circular references in callbacks
2. Unclosed NDI receivers
3. Growing frame queues
4. Event handlers not disconnected

### 5. Platform-Specific Issues

#### Windows High DPI Scaling

**Fix:**
```python
# Must be before QApplication creation
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
```

#### Console Encoding (Korean Text)

**Fix:**
```python
import sys
import io

# Set UTF-8 for console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### 6. Debugging Techniques

#### Enable Verbose Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

#### Frame Analysis

```python
def analyze_frame(frame):
    """Print detailed frame information"""
    print(f"Shape: {frame.shape}")
    print(f"Dtype: {frame.dtype}")
    print(f"Min/Max: {frame.min()}/{frame.max()}")
    print(f"Mean: {frame.mean():.2f}")
    
    # Check if frame is valid
    if frame.size == 0:
        print("WARNING: Empty frame!")
    if np.all(frame == frame[0, 0]):
        print("WARNING: Uniform frame (possible error)")
```

## Emergency Recovery

### Complete Reset

```bash
# 1. Stop all processes
taskkill /F /IM python.exe

# 2. Clear cache and settings
del /Q config\settings.json
rmdir /S /Q __pycache__

# 3. Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# 4. Start with simulator mode
python run_pd_complete.py --ndi-simulator --reset-config
```

### Safe Mode Startup

```python
# run_safe_mode.py
import os
os.environ['QT_LOGGING_RULES'] = '*=true'
os.environ['PYTHONFAULTHANDLER'] = '1'

# Disable hardware acceleration
os.environ['QT_QUICK_BACKEND'] = 'software'

# Run with minimal features
from pd_app import SafeModeApp
app = SafeModeApp(ndi_enabled=False, websocket_enabled=False)
app.run()
```

## Performance Benchmarking

### Frame Rate Test

```python
def benchmark_frame_rate():
    frame_times = []
    start_time = time.time()
    
    for i in range(300):  # 5 seconds at 60fps
        frame_start = time.perf_counter()
        
        # Your frame processing here
        process_frame()
        
        frame_time = time.perf_counter() - frame_start
        frame_times.append(frame_time)
        
    # Analysis
    avg_time = np.mean(frame_times)
    fps = 1.0 / avg_time
    
    print(f"Average FPS: {fps:.2f}")
    print(f"Frame time: {avg_time*1000:.2f}ms")
    print(f"99th percentile: {np.percentile(frame_times, 99)*1000:.2f}ms")
```

## Getting Help

### Collect Diagnostic Information

```bash
# Run diagnostic script
python diagnose_issues.py > diagnostic_report.txt
```

The script should collect:
- System information
- Python environment
- NDI sources detected
- vMix connection status
- Performance metrics
- Recent error logs

### Useful Resources

1. **NDI SDK Documentation**: https://ndi.video/for-developers/
2. **vMix Forums**: https://forums.vmix.com/
3. **PyQt5 Documentation**: https://doc.qt.io/qtforpython/
4. **Project Issues**: https://github.com/newproject8/returnfeed_pd_software/issues

### Contact Support

When reporting issues, include:
1. Diagnostic report
2. Steps to reproduce
3. Expected vs actual behavior
4. Screenshots/videos if applicable
5. Relevant log files