# pd_app/ui/streaming_status_enhanced.py
"""
Enhanced Streaming Status Display
Professional visual feedback for streaming state with animations
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, 
                         QEasingCurve, QRect, QPoint, pyqtProperty)
from PyQt6.QtGui import (QPainter, QColor, QFont, QLinearGradient, 
                        QPen, QBrush, QPixmap)
import time
from typing import Dict, Optional


class PulsingDot(QWidget):
    """Animated pulsing status indicator"""
    
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.base_color = color
        self._pulse_value = 0
        
        # Pulse animation
        self.pulse_animation = QPropertyAnimation(self, b"pulse_value")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setStartValue(0)
        self.pulse_animation.setEndValue(100)
        self.pulse_animation.setLoopCount(-1)  # Infinite
        self.pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
    @pyqtProperty(int)
    def pulse_value(self):
        return self._pulse_value
        
    @pulse_value.setter
    def pulse_value(self, value):
        self._pulse_value = value
        self.update()
        
    def start_pulsing(self):
        self.pulse_animation.start()
        
    def stop_pulsing(self):
        self.pulse_animation.stop()
        self._pulse_value = 0
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate pulse effect
        pulse_factor = self._pulse_value / 100.0
        size = 8 + int(4 * pulse_factor)
        offset = (16 - size) // 2
        
        # Draw outer glow
        if self._pulse_value > 0:
            glow_color = QColor(self.base_color)
            glow_color.setAlpha(int(100 * (1 - pulse_factor)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawEllipse(offset - 2, offset - 2, size + 4, size + 4)
        
        # Draw main dot
        painter.setBrush(self.base_color)
        painter.drawEllipse(offset, offset, size, size)


class StreamingStatusEnhanced(QFrame):
    """Enhanced streaming status display with beautiful animations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StreamingStatusEnhanced")
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        
        # Status tracking
        self.is_streaming = False
        self.stream_start_time = 0
        self.stream_stats = {
            'bitrate': '0 Mbps',
            'fps': 0,
            'dropped_frames': 0,
            'latency': 0,
            'viewers': 0
        }
        
        self.init_ui()
        self.setup_animations()
        
        # Duration update timer
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)
        
    def init_ui(self):
        """Initialize the enhanced UI"""
        self.setStyleSheet("""
            #StreamingStatusEnhanced {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a, stop:1 #1e1e1e);
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Status header
        header_layout = QHBoxLayout()
        
        # Status indicator
        self.status_dot = PulsingDot(QColor("#4CAF50"))
        header_layout.addWidget(self.status_dot)
        
        # Status text
        self.status_label = QLabel("READY")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #4CAF50;
            letter-spacing: 2px;
        """)
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Duration display
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setStyleSheet("""
            font-family: monospace;
            font-size: 16px;
            color: #fff;
            background-color: rgba(0, 0, 0, 0.3);
            padding: 5px 10px;
            border-radius: 4px;
        """)
        self.duration_label.hide()
        header_layout.addWidget(self.duration_label)
        
        layout.addLayout(header_layout)
        
        # Stats container (hidden by default)
        self.stats_container = QFrame()
        self.stats_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                padding: 8px;
                margin-top: 5px;
            }
        """)
        stats_layout = QVBoxLayout(self.stats_container)
        
        # Bitrate and FPS row
        rate_layout = QHBoxLayout()
        
        # Bitrate
        bitrate_container = QVBoxLayout()
        bitrate_label = QLabel("BITRATE")
        bitrate_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        bitrate_container.addWidget(bitrate_label)
        
        self.bitrate_value = QLabel("0 Mbps")
        self.bitrate_value.setStyleSheet("color: #fff; font-size: 14px;")
        bitrate_container.addWidget(self.bitrate_value)
        rate_layout.addLayout(bitrate_container)
        
        # FPS
        fps_container = QVBoxLayout()
        fps_label = QLabel("FPS")
        fps_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        fps_container.addWidget(fps_label)
        
        self.fps_value = QLabel("0")
        self.fps_value.setStyleSheet("color: #fff; font-size: 14px;")
        fps_container.addWidget(self.fps_value)
        rate_layout.addLayout(fps_container)
        
        # Latency
        latency_container = QVBoxLayout()
        latency_label = QLabel("LATENCY")
        latency_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        latency_container.addWidget(latency_label)
        
        self.latency_value = QLabel("0 ms")
        self.latency_value.setStyleSheet("color: #fff; font-size: 14px;")
        latency_container.addWidget(self.latency_value)
        rate_layout.addLayout(latency_container)
        
        # Viewers (optional)
        viewers_container = QVBoxLayout()
        viewers_label = QLabel("VIEWERS")
        viewers_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        viewers_container.addWidget(viewers_label)
        
        self.viewers_value = QLabel("0")
        self.viewers_value.setStyleSheet("color: #fff; font-size: 14px;")
        viewers_container.addWidget(self.viewers_value)
        rate_layout.addLayout(viewers_container)
        
        rate_layout.addStretch()
        stats_layout.addLayout(rate_layout)
        
        # Quality indicators
        quality_layout = QHBoxLayout()
        
        # Network quality
        self.network_quality = QLabel("Network: Excellent")
        self.network_quality.setStyleSheet("color: #4CAF50; font-size: 11px;")
        quality_layout.addWidget(self.network_quality)
        
        quality_layout.addStretch()
        
        # Frame drops warning
        self.drops_warning = QLabel("⚠️ Frame drops detected")
        self.drops_warning.setStyleSheet("color: #FFA726; font-size: 11px;")
        self.drops_warning.hide()
        quality_layout.addWidget(self.drops_warning)
        
        stats_layout.addLayout(quality_layout)
        
        self.stats_container.hide()
        layout.addWidget(self.stats_container)
        
        # Message area
        self.message_label = QLabel("Click 'Start Streaming' to begin")
        self.message_label.setStyleSheet("""
            color: #888;
            font-size: 12px;
            font-style: italic;
            padding: 5px;
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        layout.addStretch()
        
    def setup_animations(self):
        """Setup smooth animations"""
        # Fade in/out for stats container
        self.stats_fade = QGraphicsOpacityEffect()
        self.stats_container.setGraphicsEffect(self.stats_fade)
        
        self.stats_animation = QPropertyAnimation(self.stats_fade, b"opacity")
        self.stats_animation.setDuration(300)
        
        # Slide animation for message
        self.message_animation = QPropertyAnimation(self.message_label, b"pos")
        self.message_animation.setDuration(500)
        self.message_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def start_streaming(self, stream_name: str):
        """Update display for streaming start"""
        self.is_streaming = True
        self.stream_start_time = time.time()
        
        # Update status
        self.status_label.setText("LIVE")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #f44336;
            letter-spacing: 2px;
        """)
        
        # Update indicator
        self.status_dot.base_color = QColor("#f44336")
        self.status_dot.start_pulsing()
        
        # Show duration
        self.duration_label.show()
        self.duration_timer.start(100)  # Update every 100ms for smooth display
        
        # Animate stats in
        self.stats_container.show()
        self.stats_animation.setStartValue(0)
        self.stats_animation.setEndValue(1)
        self.stats_animation.start()
        
        # Update message
        self.message_label.setText(f"Streaming: {stream_name}")
        self.message_label.setStyleSheet("""
            color: #fff;
            font-size: 12px;
            font-weight: bold;
            padding: 5px;
        """)
        
    def stop_streaming(self):
        """Update display for streaming stop"""
        self.is_streaming = False
        
        # Update status
        self.status_label.setText("READY")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #4CAF50;
            letter-spacing: 2px;
        """)
        
        # Update indicator
        self.status_dot.base_color = QColor("#4CAF50")
        self.status_dot.stop_pulsing()
        
        # Hide duration
        self.duration_timer.stop()
        self.duration_label.hide()
        
        # Animate stats out
        self.stats_animation.setStartValue(1)
        self.stats_animation.setEndValue(0)
        self.stats_animation.finished.connect(self.stats_container.hide)
        self.stats_animation.start()
        
        # Update message
        self.message_label.setText("Stream ended successfully")
        self.message_label.setStyleSheet("""
            color: #888;
            font-size: 12px;
            font-style: italic;
            padding: 5px;
        """)
        
    def update_stats(self, stats: Dict):
        """Update streaming statistics"""
        if 'bitrate' in stats:
            self.bitrate_value.setText(stats['bitrate'])
            
        if 'fps' in stats:
            self.fps_value.setText(f"{stats['fps']}")
            
        if 'latency' in stats:
            self.latency_value.setText(f"{stats['latency']} ms")
            
        if 'viewers' in stats:
            self.viewers_value.setText(f"{stats['viewers']}")
            
        if 'dropped_frames' in stats:
            if stats['dropped_frames'] > 0:
                self.drops_warning.show()
                self.drops_warning.setText(f"⚠️ {stats['dropped_frames']} frames dropped")
            else:
                self.drops_warning.hide()
                
        # Update network quality based on latency
        if 'latency' in stats:
            latency = stats['latency']
            if latency < 50:
                quality = "Excellent"
                color = "#4CAF50"
            elif latency < 100:
                quality = "Good"
                color = "#2196F3"
            elif latency < 200:
                quality = "Fair"
                color = "#FFA726"
            else:
                quality = "Poor"
                color = "#f44336"
                
            self.network_quality.setText(f"Network: {quality}")
            self.network_quality.setStyleSheet(f"color: {color}; font-size: 11px;")
            
    def update_duration(self):
        """Update streaming duration display"""
        if self.is_streaming and self.stream_start_time > 0:
            duration = int(time.time() - self.stream_start_time)
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
    def set_error(self, error_message: str):
        """Display error state"""
        self.status_label.setText("ERROR")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #f44336;
            letter-spacing: 2px;
        """)
        
        self.message_label.setText(error_message)
        self.message_label.setStyleSheet("""
            color: #f44336;
            font-size: 12px;
            font-weight: bold;
            padding: 5px;
        """)
        
    def set_connecting(self):
        """Display connecting state"""
        self.status_label.setText("CONNECTING")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #FFA726;
            letter-spacing: 2px;
        """)
        
        self.status_dot.base_color = QColor("#FFA726")
        self.status_dot.start_pulsing()
        
        self.message_label.setText("Establishing connection...")
        self.message_label.setStyleSheet("""
            color: #FFA726;
            font-size: 12px;
            font-style: italic;
            padding: 5px;
        """)