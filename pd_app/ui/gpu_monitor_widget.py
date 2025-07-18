# pd_app/ui/gpu_monitor_widget.py
"""
GPU Monitor Widget - Beautiful visualization of GPU acceleration
Shows users their GPU is being utilized smartly for streaming
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QPen, QBrush
import math
from typing import Optional, Dict

from ..core.resource_monitor import SystemResourceMonitor

class CircularProgressBar(QWidget):
    """Beautiful circular progress indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.value = 0
        self.max_value = 100
        self.thickness = 8
        self.color = QColor("#4CAF50")
        
    def setValue(self, value):
        self.value = min(value, self.max_value)
        self.update()
        
    def setColor(self, color):
        self.color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background circle
        pen = QPen(QColor(60, 60, 60), self.thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(
            self.thickness // 2, 
            self.thickness // 2,
            -self.thickness // 2, 
            -self.thickness // 2
        )
        
        painter.drawArc(rect, 90 * 16, -360 * 16)
        
        # Draw progress arc
        if self.value > 0:
            pen = QPen(self.color, self.thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            span_angle = int(-360 * (self.value / self.max_value) * 16)
            painter.drawArc(rect, 90 * 16, span_angle)
        
        # Draw percentage text
        painter.setPen(Qt.GlobalColor.white)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        text = f"{int(self.value)}%"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


class GPUMonitorWidget(QFrame):
    """GPU monitoring widget with beautiful visualizations"""
    
    gpu_status_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setObjectName("GPUMonitorWidget")
        self.init_ui()
        
        # Create resource monitor
        self.resource_monitor = SystemResourceMonitor()
        self.resource_monitor.resources_updated.connect(self.on_resources_updated)
        
        # Animation for GPU usage
        self.usage_animation = QPropertyAnimation(self, b"gpu_usage")
        self.usage_animation.setDuration(500)
        self.usage_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Current values
        self._gpu_usage = 0
        self.gpu_encoder = "CPU"
        self.is_streaming = False
        
        # Start monitoring
        self.resource_monitor.start_monitoring()
        
    def init_ui(self):
        """Initialize the beautiful UI"""
        self.setStyleSheet("""
            #GPUMonitorWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2a2a2a, stop:1 #1a1a1a);
                border: 2px solid #333;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        
        # Title with GPU icon
        title_layout = QHBoxLayout()
        
        gpu_icon = QLabel("🎮")
        gpu_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(gpu_icon)
        
        title = QLabel("GPU Acceleration")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #fff;")
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
        title_layout.addWidget(self.status_indicator)
        
        self.encoder_label = QLabel("Ready")
        self.encoder_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        title_layout.addWidget(self.encoder_label)
        
        layout.addLayout(title_layout)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Circular progress for GPU usage
        self.gpu_usage_circle = CircularProgressBar()
        content_layout.addWidget(self.gpu_usage_circle)
        
        # Stats panel
        stats_layout = QVBoxLayout()
        
        # Encoder info
        encoder_frame = QFrame()
        encoder_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        encoder_layout = QVBoxLayout(encoder_frame)
        
        self.encoder_type_label = QLabel("Encoder: Detecting...")
        self.encoder_type_label.setStyleSheet("color: #bbb; font-size: 11px;")
        encoder_layout.addWidget(self.encoder_type_label)
        
        self.acceleration_label = QLabel("Acceleration: OFF")
        self.acceleration_label.setStyleSheet("color: #ffa726; font-weight: bold;")
        encoder_layout.addWidget(self.acceleration_label)
        
        stats_layout.addWidget(encoder_frame)
        
        # Performance metrics
        perf_frame = QFrame()
        perf_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        perf_layout = QVBoxLayout(perf_frame)
        
        self.speed_label = QLabel("Speed: --x")
        self.speed_label.setStyleSheet("color: #bbb; font-size: 11px;")
        perf_layout.addWidget(self.speed_label)
        
        self.power_label = QLabel("Power: -- W")
        self.power_label.setStyleSheet("color: #bbb; font-size: 11px;")
        perf_layout.addWidget(self.power_label)
        
        self.temp_label = QLabel("Temp: -- °C")
        self.temp_label.setStyleSheet("color: #bbb; font-size: 11px;")
        perf_layout.addWidget(self.temp_label)
        
        stats_layout.addWidget(perf_frame)
        
        stats_layout.addStretch()
        content_layout.addLayout(stats_layout)
        
        layout.addLayout(content_layout)
        
        # Bottom message
        self.message_label = QLabel("GPU resources ready for streaming")
        self.message_label.setStyleSheet("""
            color: #888;
            font-size: 11px;
            font-style: italic;
            padding: 5px;
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
    @property
    def gpu_usage(self):
        return self._gpu_usage
        
    @gpu_usage.setter
    def gpu_usage(self, value):
        self._gpu_usage = value
        self.gpu_usage_circle.setValue(value)
        
        # Update color based on usage
        if value < 30:
            color = QColor("#4CAF50")  # Green
        elif value < 70:
            color = QColor("#FFC107")  # Amber
        else:
            color = QColor("#F44336")  # Red
            
        self.gpu_usage_circle.setColor(color)
        
    def update_gpu_info(self, gpu_info: Dict):
        """Update GPU information display"""
        if gpu_info.get('gpu_available'):
            encoder = gpu_info.get('selected_encoder', 'Unknown')
            
            # Map encoder to friendly name
            encoder_names = {
                'h264_nvenc': 'NVIDIA NVENC',
                'h264_qsv': 'Intel QuickSync',
                'h264_amf': 'AMD AMF',
                'h264_videotoolbox': 'Apple VideoToolbox',
                'libx264': 'CPU (x264)'
            }
            
            friendly_name = encoder_names.get(encoder, encoder)
            self.gpu_encoder = friendly_name
            
            self.encoder_type_label.setText(f"Encoder: {friendly_name}")
            self.encoder_label.setText("GPU Ready")
            self.encoder_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
            
            if encoder != 'libx264':
                self.acceleration_label.setText("Acceleration: ON 🚀")
                self.acceleration_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.message_label.setText("GPU acceleration active - Enjoy faster encoding!")
            else:
                self.acceleration_label.setText("Acceleration: OFF")
                self.acceleration_label.setStyleSheet("color: #ffa726; font-weight: bold;")
                self.message_label.setText("Using CPU encoding - Consider GPU upgrade")
        else:
            self.encoder_label.setText("CPU Only")
            self.encoder_label.setStyleSheet("color: #ffa726; font-weight: bold;")
            self.status_indicator.setStyleSheet("color: #ffa726; font-size: 16px;")
            
    def on_resources_updated(self, stats: Dict):
        """Handle real resource updates"""
        if self.is_streaming:
            # Update GPU usage with animation
            if self.gpu_encoder != "CPU (x264)":
                new_usage = stats.get('gpu_percent', 0)
                if new_usage != self._gpu_usage:
                    self.usage_animation.setStartValue(self._gpu_usage)
                    self.usage_animation.setEndValue(new_usage)
                    self.usage_animation.start()
                
                # Update stats display
                power = stats.get('gpu_power', 0)
                if power > 0:
                    self.power_label.setText(f"Power: {power:.0f} W")
                else:
                    self.power_label.setText("Power: --")
                
                temp = stats.get('gpu_temperature', 0)
                if temp > 0:
                    self.temp_label.setText(f"Temp: {temp} °C")
                else:
                    self.temp_label.setText("Temp: --")
                
                # Calculate encoding speed based on usage
                if new_usage > 0:
                    speed = 1.0 + (new_usage / 100.0) * 2.0  # 1.0x to 3.0x
                    self.speed_label.setText(f"Speed: {speed:.1f}x")
                else:
                    self.speed_label.setText("Speed: --")
                
                # Emit status
                self.gpu_status_changed.emit({
                    'usage': new_usage,
                    'speed': speed if new_usage > 0 else 1.0,
                    'power': power,
                    'temperature': temp
                })
            else:
                # CPU encoding - show CPU usage instead
                cpu_usage = stats.get('cpu_percent', 0)
                self.gpu_usage = 0
                self.speed_label.setText("Speed: 1.0x")
                self.power_label.setText(f"CPU: {cpu_usage:.0f}%")
                self.temp_label.setText("Temp: N/A")
            
    def set_streaming_state(self, is_streaming: bool):
        """Update display based on streaming state"""
        self.is_streaming = is_streaming
        
        if is_streaming:
            self.message_label.setText("🎯 GPU working hard for your stream!")
            if self.gpu_encoder != "CPU (x264)":
                # Start pulsing animation for the indicator
                self.start_pulse_animation()
        else:
            self.message_label.setText("GPU resources ready for streaming")
            self.gpu_usage = 0
            
    def start_pulse_animation(self):
        """Create a pulsing effect for the status indicator"""
        # This would implement a pulsing animation
        pass


class ResourceMonitorPanel(QFrame):
    """Combined resource monitoring panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResourceMonitorPanel")
        self.init_ui()
        
        # Resource monitor
        self.resource_monitor = SystemResourceMonitor()
        self.resource_monitor.resources_updated.connect(self.on_resources_updated)
        
    def init_ui(self):
        """Initialize UI"""
        self.setStyleSheet("""
            #ResourceMonitorPanel {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(self)
        
        # CPU indicator
        cpu_layout = QVBoxLayout()
        cpu_label = QLabel("CPU")
        cpu_label.setStyleSheet("color: #888; font-size: 10px;")
        cpu_layout.addWidget(cpu_label)
        
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setTextVisible(False)
        self.cpu_bar.setFixedHeight(8)
        self.cpu_bar.setStyleSheet("""
            QProgressBar {
                background-color: #444;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 4px;
            }
        """)
        cpu_layout.addWidget(self.cpu_bar)
        
        layout.addLayout(cpu_layout)
        
        # Memory indicator
        mem_layout = QVBoxLayout()
        mem_label = QLabel("Memory")
        mem_label.setStyleSheet("color: #888; font-size: 10px;")
        mem_layout.addWidget(mem_label)
        
        self.mem_bar = QProgressBar()
        self.mem_bar.setMaximum(100)
        self.mem_bar.setTextVisible(False)
        self.mem_bar.setFixedHeight(8)
        self.mem_bar.setStyleSheet("""
            QProgressBar {
                background-color: #444;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #9C27B0;
                border-radius: 4px;
            }
        """)
        mem_layout.addWidget(self.mem_bar)
        
        layout.addLayout(mem_layout)
        
        # Resource savings
        self.savings_label = QLabel("Resources: Normal")
        self.savings_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.savings_label)
        
        layout.addStretch()
        
        # State tracking
        self.is_optimized = False
        self.preview_active = True
        self.is_streaming = False
        
        # Start monitoring
        self.resource_monitor.start_monitoring()
        
    def on_resources_updated(self, stats: Dict):
        """Handle real resource updates"""
        self.cpu_bar.setValue(int(stats.get('cpu_percent', 0)))
        self.mem_bar.setValue(int(stats.get('memory_percent', 0)))
        
        # Update savings display if optimized
        if self.is_optimized:
            savings = self.resource_monitor.calculate_resource_savings(
                self.preview_active, self.is_streaming
            )
            if savings['cpu_saved'] > 0:
                self.savings_label.setText(f"Saved: CPU -{savings['cpu_saved']}% Mem -{savings['memory_saved']}% ✨")
                self.savings_label.setStyleSheet("color: #FFC107; font-weight: bold; font-size: 11px;")
        
    def update_resources(self, cpu: int, memory: int, optimized: bool):
        """Update resource display (legacy method for compatibility)"""
        self.is_optimized = optimized
        
        if optimized:
            self.savings_label.setText("Resources: Optimized ✨")
            self.savings_label.setStyleSheet("color: #FFC107; font-weight: bold; font-size: 11px;")
        else:
            self.savings_label.setText("Resources: Normal")
            self.savings_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 11px;")
            
    def set_streaming_state(self, preview_active: bool, is_streaming: bool):
        """Update streaming state for accurate savings calculation"""
        self.preview_active = preview_active
        self.is_streaming = is_streaming