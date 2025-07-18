# pd_app/ui/video_display_resource_aware.py
"""
Resource-aware Video Display Widget with Fade to Black
Automatically pauses NDI preview during SRT streaming to save resources
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtSignal, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont, QImage, QBrush, QPen
import time
from typing import Optional, Dict

class ResourceAwareVideoDisplay(QWidget):
    """Video display widget with resource management and fade effects"""
    
    # Signals
    preview_paused = pyqtSignal()
    preview_resumed = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Display properties
        self.setMinimumSize(640, 360)
        self.base_width = 1280
        self.base_height = 720
        
        # Background style
        self.setStyleSheet("""
            ResourceAwareVideoDisplay {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 8px;
            }
        """)
        
        # Frame management
        self.current_frame = None
        self.last_frame_before_pause = None
        self.is_preview_active = True
        self.is_streaming = False
        
        # Fade animation
        self.fade_opacity = 0.0
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._update_fade)
        self.fade_direction = 0  # 0: none, 1: fade in, -1: fade out
        self.fade_complete_callback = None
        
        # Streaming info
        self.stream_info = {
            'name': '',
            'bitrate': '',
            'duration': 0,
            'fps': 0,
            'latency': 0
        }
        
        # Resource monitoring
        self.resource_stats = {
            'cpu_saved': 0,
            'gpu_saved': 0,
            'frames_skipped': 0
        }
        
        # Performance settings
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        
    def paintEvent(self, event):
        """Paint event with fade effect support"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Draw background
            painter.fillRect(self.rect(), QColor(20, 20, 20))
            
            # Calculate 16:9 display area
            widget_rect = self.rect()
            display_rect = self._calculate_display_rect(widget_rect)
            
            # Draw black background for video area
            painter.fillRect(display_rect, Qt.GlobalColor.black)
            
            # Draw video frame or last frame
            frame_to_draw = self.current_frame if self.is_preview_active else self.last_frame_before_pause
            
            if frame_to_draw and not frame_to_draw.isNull():
                # Draw the frame
                painter.drawImage(display_rect, frame_to_draw)
                
                # Apply fade to black if needed
                if self.fade_opacity > 0:
                    painter.fillRect(display_rect, QColor(0, 0, 0, int(255 * self.fade_opacity)))
            else:
                # No frame - show placeholder
                painter.setPen(QColor(100, 100, 100))
                font = QFont()
                font.setPointSize(14)
                painter.setFont(font)
                painter.drawText(display_rect, Qt.AlignmentFlag.AlignCenter, 
                               "NDI Preview\nSelect a source to begin")
            
            # Draw streaming overlay if active
            if self.is_streaming:
                self._draw_streaming_overlay(painter, display_rect)
                
            # Draw resource savings if preview is paused
            if not self.is_preview_active and not self.is_streaming:
                self._draw_resource_info(painter, display_rect)
                
        except Exception as e:
            print(f"Paint error: {e}")
        finally:
            painter.end()
            
    def _calculate_display_rect(self, widget_rect) -> QRect:
        """Calculate 16:9 display rectangle centered in widget"""
        widget_width = widget_rect.width()
        widget_height = widget_rect.height()
        
        # Calculate 16:9 dimensions
        target_width = widget_width
        target_height = int(target_width * 9 / 16)
        
        if target_height > widget_height:
            target_height = widget_height
            target_width = int(target_height * 16 / 9)
            
        # Center the display
        x = (widget_width - target_width) // 2
        y = (widget_height - target_height) // 2
        
        return QRect(x, y, target_width, target_height)
        
    def _draw_streaming_overlay(self, painter, rect):
        """Draw streaming information overlay"""
        # Semi-transparent background
        overlay_color = QColor(0, 0, 0, 200)
        painter.fillRect(rect, overlay_color)
        
        # Red recording indicator
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(220, 20, 60))
        
        indicator_size = 12
        indicator_x = rect.right() - 100
        indicator_y = rect.top() + 30
        painter.drawEllipse(indicator_x, indicator_y, indicator_size, indicator_size)
        
        # REC text
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(indicator_x + 20, indicator_y + 10, "STREAMING")
        
        # Main message
        font.setPointSize(20)
        painter.setFont(font)
        center_rect = rect.adjusted(0, -50, 0, -50)
        painter.drawText(center_rect, Qt.AlignmentFlag.AlignCenter,
                        f"Streaming Active\n{self.stream_info['name']}")
        
        # Stats
        if self.stream_info['duration'] > 0:
            font.setPointSize(12)
            font.setBold(False)
            painter.setFont(font)
            
            duration = time.strftime('%H:%M:%S', time.gmtime(self.stream_info['duration']))
            stats_text = f"Duration: {duration} | "
            stats_text += f"Bitrate: {self.stream_info['bitrate']} | "
            stats_text += f"FPS: {self.stream_info['fps']} | "
            stats_text += f"Latency: {self.stream_info['latency']}ms"
            
            stats_rect = rect.adjusted(0, rect.height() - 60, 0, 0)
            painter.drawText(stats_rect, Qt.AlignmentFlag.AlignCenter, stats_text)
            
        # Resource savings
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QColor(100, 255, 100))
        
        savings_text = f"CPU Saved: ~{self.resource_stats['cpu_saved']}% | "
        savings_text += f"GPU Saved: ~{self.resource_stats['gpu_saved']}%"
        
        savings_rect = rect.adjusted(20, 20, -20, -rect.height() + 40)
        painter.drawText(savings_rect, Qt.AlignmentFlag.AlignLeft, savings_text)
        
    def _draw_resource_info(self, painter, rect):
        """Draw resource saving information when paused"""
        # Dimmed last frame with overlay
        overlay_color = QColor(0, 0, 0, 180)
        painter.fillRect(rect, overlay_color)
        
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(14)
        painter.setFont(font)
        
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter,
                        "NDI Preview Paused\nResources Optimized for Streaming")
        
    def update_frame(self, frame: QImage):
        """Update frame only if preview is active"""
        if self.is_preview_active and frame and not frame.isNull():
            self.current_frame = frame
            self.resource_stats['frames_skipped'] = 0
            self.update()
        else:
            # Count skipped frames for stats
            self.resource_stats['frames_skipped'] += 1
            
    def start_streaming(self, stream_name: str):
        """Start streaming - fade to black and pause preview"""
        if self.is_streaming:
            return
            
        self.is_streaming = True
        self.stream_info['name'] = stream_name
        self.stream_info['duration'] = 0
        
        # Save last frame before pausing
        if self.current_frame:
            self.last_frame_before_pause = self.current_frame.copy()
            
        # Start fade to black
        self.fade_complete_callback = self._on_fade_to_black_complete
        self._start_fade(fade_out=True)
        
        # Estimate resource savings
        self.resource_stats['cpu_saved'] = 15  # Estimated 15% CPU saved
        self.resource_stats['gpu_saved'] = 25  # Estimated 25% GPU saved
        
    def stop_streaming(self):
        """Stop streaming - fade from black and resume preview"""
        if not self.is_streaming:
            return
            
        self.is_streaming = False
        
        # Resume preview
        self.is_preview_active = True
        self.preview_resumed.emit()
        
        # Start fade from black
        self._start_fade(fade_out=False)
        
        # Reset resource stats
        self.resource_stats['cpu_saved'] = 0
        self.resource_stats['gpu_saved'] = 0
        
    def _start_fade(self, fade_out: bool):
        """Start fade animation"""
        self.fade_direction = -1 if fade_out else 1
        self.fade_timer.start(16)  # 60 FPS
        
    def _update_fade(self):
        """Update fade animation"""
        # Update opacity
        self.fade_opacity += self.fade_direction * 0.05
        
        # Clamp opacity
        self.fade_opacity = max(0.0, min(1.0, self.fade_opacity))
        
        # Check if animation complete
        if (self.fade_direction == 1 and self.fade_opacity >= 1.0) or \
           (self.fade_direction == -1 and self.fade_opacity <= 0.0):
            self.fade_timer.stop()
            self.fade_direction = 0
            
            # Call completion callback if set
            if self.fade_complete_callback:
                callback = self.fade_complete_callback
                self.fade_complete_callback = None
                callback()
                
        self.update()
        
    def _on_fade_to_black_complete(self):
        """Called when fade to black is complete"""
        # Pause NDI preview to save resources
        self.is_preview_active = False
        self.preview_paused.emit()
        
        # Clear current frame to free memory
        self.current_frame = None
        
    def update_stream_stats(self, stats: Dict):
        """Update streaming statistics"""
        if 'bitrate' in stats:
            self.stream_info['bitrate'] = stats['bitrate']
        if 'fps' in stats:
            self.stream_info['fps'] = stats['fps']
        if 'duration' in stats:
            self.stream_info['duration'] = stats['duration']
        if 'latency' in stats:
            self.stream_info['latency'] = stats['latency']
            
        if self.is_streaming:
            self.update()
            
    def set_preview_active(self, active: bool):
        """Manually control preview state"""
        if self.is_preview_active != active:
            self.is_preview_active = active
            
            if active:
                self.preview_resumed.emit()
            else:
                if self.current_frame:
                    self.last_frame_before_pause = self.current_frame.copy()
                self.preview_paused.emit()
                
            self.update()
            
    def clear_display(self):
        """Clear the display"""
        self.current_frame = None
        self.last_frame_before_pause = None
        self.update()


class StreamingStatusWidget(QWidget):
    """Widget to show streaming status and resource usage"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Title
        title = QLabel("Resource Management")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Status labels
        self.preview_status = QLabel("NDI Preview: Active")
        self.preview_status.setStyleSheet("color: #4CAF50;")
        
        self.resource_status = QLabel("Resources: Normal")
        self.resource_status.setStyleSheet("color: #2196F3;")
        
        layout.addWidget(self.preview_status)
        layout.addWidget(self.resource_status)
        
    def update_status(self, preview_active: bool, streaming: bool):
        """Update status display"""
        if preview_active:
            self.preview_status.setText("NDI Preview: Active")
            self.preview_status.setStyleSheet("color: #4CAF50;")
        else:
            self.preview_status.setText("NDI Preview: Paused")
            self.preview_status.setStyleSheet("color: #FF9800;")
            
        if streaming:
            self.resource_status.setText("Resources: Optimized for Streaming")
            self.resource_status.setStyleSheet("color: #FFC107;")
        else:
            self.resource_status.setText("Resources: Normal")
            self.resource_status.setStyleSheet("color: #2196F3;")