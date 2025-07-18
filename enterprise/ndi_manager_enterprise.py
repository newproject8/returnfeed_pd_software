"""
Enterprise-grade NDI Manager with event-driven architecture
Optimized for zero GUI freezing and efficient resource usage
"""

import time
import logging
import threading
from collections import deque
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex, QMutexLocker, QWaitCondition
from PyQt6.QtGui import QImage

try:
    import NDIlib as ndi
except ImportError:
    ndi = None
    
logger = logging.getLogger(__name__)


class FrameQuality(Enum):
    """Frame quality levels for adaptive processing"""
    FULL = "full"          # Original quality
    HIGH = "high"          # 1080p max
    MEDIUM = "medium"      # 720p max  
    LOW = "low"           # 480p max
    PREVIEW = "preview"    # 360p max


@dataclass
class NDIFrame:
    """Lightweight frame wrapper to minimize copying"""
    data: np.ndarray
    timestamp: float
    width: int
    height: int
    frame_number: int
    quality: FrameQuality = FrameQuality.FULL
    
    def release(self):
        """Explicitly release frame data"""
        self.data = None


class FrameBuffer:
    """
    Thread-safe ring buffer for frames
    Implements zero-copy semantics where possible
    """
    def __init__(self, max_size: int = 3):
        self.buffer = deque(maxlen=max_size)
        self.mutex = QMutex()
        self.not_empty = QWaitCondition()
        self.frame_count = 0
        self.dropped_frames = 0
        
    def push(self, frame: NDIFrame) -> bool:
        """Push frame to buffer, returns False if buffer was full"""
        with QMutexLocker(self.mutex):
            was_full = len(self.buffer) == self.buffer.maxlen
            if was_full:
                # Release oldest frame before dropping
                old_frame = self.buffer[0]
                old_frame.release()
                self.dropped_frames += 1
                
            self.buffer.append(frame)
            self.frame_count += 1
            self.not_empty.wakeOne()
            return not was_full
            
    def pop(self, timeout_ms: int = 100) -> Optional[NDIFrame]:
        """Pop frame from buffer with timeout"""
        with QMutexLocker(self.mutex):
            if not self.buffer:
                if not self.not_empty.wait(self.mutex, timeout_ms):
                    return None
                    
            if self.buffer:
                return self.buffer.popleft()
            return None
            
    def clear(self):
        """Clear all frames and release memory"""
        with QMutexLocker(self.mutex):
            for frame in self.buffer:
                frame.release()
            self.buffer.clear()
            
    def stats(self) -> Dict[str, int]:
        """Get buffer statistics"""
        with QMutexLocker(self.mutex):
            return {
                "current_size": len(self.buffer),
                "total_frames": self.frame_count,
                "dropped_frames": self.dropped_frames,
                "drop_rate": self.dropped_frames / max(1, self.frame_count)
            }


class NDIWorkerEnterprise(QThread):
    """
    Enterprise-grade NDI worker thread
    Event-driven, zero-copy optimized
    """
    
    # Signals
    frame_ready = pyqtSignal(NDIFrame)  # Emits processed frames
    source_found = pyqtSignal(str)      # Emits when new source found
    error_occurred = pyqtSignal(str)    # Emits on errors
    stats_updated = pyqtSignal(dict)    # Performance statistics
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.source_name = None
        self.running = False
        self.frame_buffer = FrameBuffer(max_size=3)
        
        # Performance tracking
        self.last_frame_time = 0
        self.frame_times = deque(maxlen=60)  # Track last 60 frames
        self.processing_times = deque(maxlen=60)
        
        # Adaptive quality
        self.current_quality = FrameQuality.FULL
        self.target_fps = 60
        self.actual_fps = 0
        
        # Thread coordination
        self.source_lock = threading.Lock()
        self.stop_event = threading.Event()
        
    def set_source(self, source_name: str):
        """Thread-safe source setting"""
        with self.source_lock:
            self.source_name = source_name
            if self.receiver:
                # Disconnect current receiver
                self._cleanup_receiver()
                
    def run(self):
        """Main worker thread - event driven processing"""
        try:
            # Initialize NDI
            if not self._initialize_ndi():
                return
                
            self.running = True
            logger.info("NDI Worker started - Enterprise mode")
            
            # Main processing loop
            while self.running and not self.stop_event.is_set():
                # Process based on current state
                if not self.receiver and self.source_name:
                    self._connect_to_source()
                elif self.receiver:
                    self._process_frames()
                else:
                    # No source selected, efficient wait
                    self.stop_event.wait(0.1)
                    
                # Update statistics periodically
                if time.time() - self.last_frame_time > 1.0:
                    self._emit_statistics()
                    
        except Exception as e:
            logger.error(f"NDI Worker error: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            self._cleanup()
            logger.info("NDI Worker stopped")
            
    def _initialize_ndi(self) -> bool:
        """Initialize NDI library"""
        if not ndi:
            self.error_occurred.emit("NDI library not available")
            return False
            
        if not ndi.initialize():
            self.error_occurred.emit("Failed to initialize NDI")
            return False
            
        # Create finder with optimal settings
        self.finder = ndi.find_create_v2()
        if not self.finder:
            self.error_occurred.emit("Failed to create NDI finder")
            return False
            
        return True
        
    def _connect_to_source(self):
        """Connect to NDI source with non-blocking discovery"""
        with self.source_lock:
            if not self.source_name:
                return
                
        # Non-blocking source discovery
        sources = []
        start_time = time.time()
        
        while time.time() - start_time < 5.0:  # 5 second timeout
            if ndi.find_wait_for_sources(self.finder, 100):  # 100ms checks
                sources = ndi.find_get_current_sources(self.finder)
                if sources:
                    break
                    
        # Find requested source
        source = None
        for s in sources:
            if s.ndi_name == self.source_name:
                source = s
                break
                
        if not source:
            self.error_occurred.emit(f"Source not found: {self.source_name}")
            return
            
        # Create receiver with optimal settings
        recv_create = ndi.RecvCreateV3()
        recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
        recv_create.allow_video_fields = False
        
        self.receiver = ndi.recv_create_v3(recv_create)
        if not self.receiver:
            self.error_occurred.emit("Failed to create receiver")
            return
            
        # Connect
        ndi.recv_connect(self.receiver, source)
        logger.info(f"Connected to NDI source: {self.source_name}")
        
    def _process_frames(self):
        """Process frames with adaptive quality and zero-copy optimization"""
        if not self.receiver:
            return
            
        start_time = time.time()
        
        # Capture frame with minimal timeout
        frame_type = ndi.recv_capture_v2(self.receiver, 16)  # 16ms for 60fps
        
        if frame_type == ndi.FRAME_TYPE_VIDEO:
            # Get video frame
            v_frame = ndi.recv_get_video_data(self.receiver)
            if v_frame and v_frame.data is not None:
                # Create frame wrapper (no copy yet)
                frame = self._create_frame(v_frame)
                
                # Adaptive quality adjustment
                if self.actual_fps < self.target_fps * 0.8:
                    frame = self._reduce_quality(frame)
                    
                # Emit frame for processing
                self.frame_ready.emit(frame)
                
                # Free NDI frame
                ndi.recv_free_video_v2(self.receiver, v_frame)
                
                # Track timing
                process_time = time.time() - start_time
                self.processing_times.append(process_time)
                self.frame_times.append(time.time())
                
        elif frame_type == ndi.FRAME_TYPE_NONE:
            # No frame available - efficient wait
            self.stop_event.wait(0.001)  # 1ms wait
            
    def _create_frame(self, ndi_frame) -> NDIFrame:
        """Create frame wrapper with minimal copying"""
        # Only copy if we need to modify the data
        if self.current_quality == FrameQuality.FULL:
            # Zero-copy reference
            data = ndi_frame.data
        else:
            # Need to copy for resizing
            data = np.copy(ndi_frame.data)
            
        return NDIFrame(
            data=data,
            timestamp=time.time(),
            width=ndi_frame.xres,
            height=ndi_frame.yres,
            frame_number=ndi_frame.frame_number,
            quality=self.current_quality
        )
        
    def _reduce_quality(self, frame: NDIFrame) -> NDIFrame:
        """Reduce frame quality for better performance"""
        # Quality reduction logic
        quality_map = {
            FrameQuality.FULL: (1920, 1080),
            FrameQuality.HIGH: (1920, 1080),
            FrameQuality.MEDIUM: (1280, 720),
            FrameQuality.LOW: (854, 480),
            FrameQuality.PREVIEW: (640, 360)
        }
        
        max_width, max_height = quality_map[self.current_quality]
        
        if frame.width > max_width or frame.height > max_height:
            # Calculate scale
            scale = min(max_width / frame.width, max_height / frame.height)
            new_width = int(frame.width * scale)
            new_height = int(frame.height * scale)
            
            # Use optimized resize
            import cv2
            frame.data = cv2.resize(frame.data, (new_width, new_height), 
                                   interpolation=cv2.INTER_LINEAR)
            frame.width = new_width
            frame.height = new_height
            
        return frame
        
    def _emit_statistics(self):
        """Emit performance statistics"""
        if len(self.frame_times) > 1:
            # Calculate actual FPS
            time_diff = self.frame_times[-1] - self.frame_times[0]
            self.actual_fps = len(self.frame_times) / max(0.001, time_diff)
            
            # Average processing time
            avg_process_time = sum(self.processing_times) / max(1, len(self.processing_times))
            
            stats = {
                "fps": self.actual_fps,
                "target_fps": self.target_fps,
                "quality": self.current_quality.value,
                "avg_process_time_ms": avg_process_time * 1000,
                "buffer_stats": self.frame_buffer.stats()
            }
            
            self.stats_updated.emit(stats)
            
            # Adaptive quality adjustment
            if self.actual_fps < self.target_fps * 0.8:
                self._decrease_quality()
            elif self.actual_fps > self.target_fps * 0.95 and avg_process_time < 0.010:
                self._increase_quality()
                
        self.last_frame_time = time.time()
        
    def _decrease_quality(self):
        """Decrease quality for better performance"""
        quality_order = [FrameQuality.FULL, FrameQuality.HIGH, 
                        FrameQuality.MEDIUM, FrameQuality.LOW, FrameQuality.PREVIEW]
        current_idx = quality_order.index(self.current_quality)
        if current_idx < len(quality_order) - 1:
            self.current_quality = quality_order[current_idx + 1]
            logger.info(f"Decreased quality to {self.current_quality.value}")
            
    def _increase_quality(self):
        """Increase quality when performance allows"""
        quality_order = [FrameQuality.FULL, FrameQuality.HIGH, 
                        FrameQuality.MEDIUM, FrameQuality.LOW, FrameQuality.PREVIEW]
        current_idx = quality_order.index(self.current_quality)
        if current_idx > 0:
            self.current_quality = quality_order[current_idx - 1]
            logger.info(f"Increased quality to {self.current_quality.value}")
            
    def _cleanup_receiver(self):
        """Clean up current receiver"""
        if self.receiver:
            ndi.recv_destroy(self.receiver)
            self.receiver = None
            
    def _cleanup(self):
        """Clean up all resources"""
        self._cleanup_receiver()
        
        if self.finder:
            ndi.find_destroy(self.finder)
            self.finder = None
            
        self.frame_buffer.clear()
        
        if ndi:
            ndi.destroy()
            
    def stop(self):
        """Graceful stop"""
        self.running = False
        self.stop_event.set()
        self.frame_buffer.not_empty.wakeAll()
        
        # Wait for thread to finish
        if not self.wait(5000):  # 5 second timeout
            logger.warning("NDI Worker thread did not stop gracefully")
            self.terminate()


class NDIManagerEnterprise(QObject):
    """
    Enterprise-grade NDI Manager
    Event-driven, high-performance, production-ready
    """
    
    # Signals
    source_list_updated = pyqtSignal(list)
    frame_received = pyqtSignal(QImage)
    connection_state_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    performance_stats = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.sources = []
        self.connected = False
        self.discovery_thread = None
        self.discovery_running = False
        
        # Frame processing
        self.frame_processor = FrameProcessor()
        
        # Start discovery
        self.start_discovery()
        
    def start_discovery(self):
        """Start source discovery in background"""
        if not self.discovery_running:
            self.discovery_running = True
            self.discovery_thread = threading.Thread(target=self._discovery_loop)
            self.discovery_thread.daemon = True
            self.discovery_thread.start()
            
    def _discovery_loop(self):
        """Background source discovery"""
        if not ndi or not ndi.initialize():
            return
            
        finder = ndi.find_create_v2()
        if not finder:
            return
            
        try:
            while self.discovery_running:
                # Check for sources
                if ndi.find_wait_for_sources(finder, 1000):  # 1 second
                    sources = ndi.find_get_current_sources(finder)
                    if sources:
                        source_names = [s.ndi_name for s in sources]
                        if source_names != self.sources:
                            self.sources = source_names
                            self.source_list_updated.emit(self.sources)
                            
        finally:
            ndi.find_destroy(finder)
            
    def connect_to_source(self, source_name: str):
        """Connect to NDI source"""
        # Stop current worker if exists
        if self.worker:
            self.disconnect_source()
            
        # Create new worker
        self.worker = NDIWorkerEnterprise()
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.stats_updated.connect(self._on_stats_updated)
        
        # Set source and start
        self.worker.set_source(source_name)
        self.worker.start()
        
        self.connected = True
        self.connection_state_changed.emit(True)
        
    def disconnect_source(self):
        """Disconnect from current source"""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
            
        self.connected = False
        self.connection_state_changed.emit(False)
        
    def _on_frame_ready(self, frame: NDIFrame):
        """Process frame and emit for display"""
        try:
            # Convert to QImage
            qimage = self.frame_processor.convert_to_qimage(frame)
            if qimage:
                self.frame_received.emit(qimage)
        finally:
            # Always release frame
            frame.release()
            
    def _on_error(self, error_msg: str):
        """Handle worker errors"""
        logger.error(f"NDI Error: {error_msg}")
        self.error_occurred.emit(error_msg)
        self.disconnect_source()
        
    def _on_stats_updated(self, stats: dict):
        """Forward performance statistics"""
        self.performance_stats.emit(stats)
        
    def stop(self):
        """Stop all operations"""
        self.discovery_running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=2)
            
        self.disconnect_source()


class FrameProcessor:
    """Efficient frame processing utilities"""
    
    @staticmethod
    def convert_to_qimage(frame: NDIFrame) -> Optional[QImage]:
        """Convert NDI frame to QImage with zero-copy when possible"""
        try:
            if frame.data is None:
                return None
                
            height, width = frame.data.shape[:2]
            bytes_per_line = width * 4  # BGRA format
            
            # Create QImage without copying if possible
            qimage = QImage(frame.data.data, width, height, 
                           bytes_per_line, QImage.Format.Format_RGB32)
                           
            # Convert to RGB if needed
            if qimage.format() != QImage.Format.Format_RGB32:
                qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
                
            return qimage
            
        except Exception as e:
            logger.error(f"Frame conversion error: {e}")
            return None