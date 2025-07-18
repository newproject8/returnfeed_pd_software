# NDI Proxy Mode Performance Regression Analysis

## Problem Statement
NDI proxy mode (RECV_BANDWIDTH_LOWEST) has regressed from achieving 56fps to only 43fps, causing visible stuttering and poor user experience.

## Current Symptoms
- Normal mode: 57-60fps (acceptable)
- Proxy mode: 43-50fps (unacceptable, was previously 56fps)
- Visual stuttering despite frame interpolation
- Frame delivery appears inconsistent

## Root Cause Analysis

### 1. **Critical Issue: Excessive Timeout Value**
**Location**: `/modules/ndi_module/ndi_receiver.py` lines 299-302
```python
if self.bandwidth_mode == "lowest":
    timeout_ms = 100  # TOO HIGH! This is 6x frame interval
else:
    timeout_ms = 50
```

**Problem**: 
- 60fps = 16.67ms per frame
- 100ms timeout means up to 100ms wait when no frame is available
- This alone can drop FPS from 60 to ~40fps

### 2. **Performance Overhead in Frame Processing Loop**
Multiple unnecessary operations in the hot path:
- Debug checks even when disabled (lines 316-317, 383-384)
- Frame interval tracking for all frames (lines 388-397)
- Sleep delays on errors (lines 484, 497, 499)

### 3. **Suboptimal Frame Data Copying**
Line 372-373: Frame data is copied even in proxy mode where frames are smaller
```python
frame_data_copy = np.array(v_frame.data, copy=True, order='C')
```

### 4. **Missing Display Timer Synchronization**
Unlike classic mode which has a 16ms QTimer for display updates, the regular mode relies solely on frame arrival timing.

## Historical Context
- Previous commits show proxy mode achieving 56fps
- Recent "optimizations" actually introduced performance regressions
- The 100ms timeout was added based on NDI SDK recommendations but is too conservative

## Recommended Solutions

### Immediate Fix (High Priority)
```python
# In ndi_receiver.py, change timeout:
if self.bandwidth_mode == "lowest":
    timeout_ms = 20  # Just slightly more than frame interval
else:
    timeout_ms = 50
```

### Performance Optimizations
1. **Remove Debug Overhead**:
   ```python
   # Comment out or use compile-time constant:
   # if self.debug_enabled:
   #     self._detailed_frame_analysis(v_frame)
   ```

2. **Optimize Frame Copying**:
   ```python
   if self.bandwidth_mode == "lowest":
       # Use view for proxy mode (smaller frames)
       frame_data_copy = np.asarray(v_frame.data, order='C')
   ```

3. **Remove Sleep Delays**:
   ```python
   # Replace all msleep() calls with continue
   continue  # No delay needed
   ```

### Testing Methodology
1. Run proxy mode and monitor actual FPS output
2. Check frame interval consistency
3. Verify CPU usage doesn't spike
4. Compare with previous commit performance

## Technical Details

### NDI Proxy Mode Characteristics
- Uses RECV_BANDWIDTH_LOWEST flag
- NOT the same as NDI|HX (different technology)
- Delivers lower resolution frames
- Should still achieve near 60fps with proper implementation

### Frame Processing Pipeline
1. `recv_capture_v2()` with timeout
2. Frame data copy/conversion
3. QImage creation
4. Signal emission to UI
5. Display update in main window

### Performance Impact Calculation
- 100ms timeout × multiple timeouts per second = significant FPS drop
- Each unnecessary operation adds ~0.1-1ms
- Cumulative effect drops FPS from 60 to 43

## Alternative Approaches
1. Use separate thread for frame capture with circular buffer
2. Implement frame timestamp-based display synchronization
3. Use zero-copy techniques where possible
4. Consider using NDI's async API if available

## Key Metrics to Monitor
- Actual frame receive rate (from NDI source)
- Frame processing time (capture to display)
- Timeout occurrence frequency
- CPU usage in frame processing thread

## Conclusion
The regression from 56fps to 43fps is primarily caused by the excessive 100ms timeout value introduced in recent changes. This should be reverted to 20ms for proxy mode. Additional performance optimizations can further improve frame delivery consistency.