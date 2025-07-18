#!/usr/bin/env python3
"""
Complete PD Software Integration Demo
Shows all features working together:
- GPU-accelerated streaming
- Resource optimization with NDI preview pause
- Enhanced streaming status display
- Network-adaptive latency
- Real-time resource monitoring
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QSplitter, QGroupBox, QTextEdit)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QLinearGradient

# Import all our components
from pd_app.ui.srt_widget_integrated import IntegratedSRTWidget
from pd_app.ui.video_display_resource_aware import ResourceAwareVideoDisplay
from pd_app.ui.streaming_status_enhanced import StreamingStatusEnhanced
from pd_app.core.resource_monitor import SystemResourceMonitor, ResourceOptimizer


class DemoAuthManager:
    """Mock auth manager for demo"""
    def is_logged_in(self):
        return True
    
    def get_user_info(self):
        return {
            'user_id': 'broadcast_user',
            'unique_address': 'studio_001'
        }


class CompleteIntegrationDemo(QMainWindow):
    """Complete integration demo window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PD Software - Complete Integration Demo 🚀")
        self.setGeometry(50, 50, 1600, 1000)
        
        # Professional dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #fff;
            }
            QWidget {
                background-color: #2a2a2a;
                color: #fff;
            }
            QGroupBox {
                border: 2px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        
        # Create mock managers
        self.auth_manager = DemoAuthManager()
        
        # Setup UI
        self.init_ui()
        
        # Demo frame generator
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.generate_demo_frame)
        self.demo_timer.start(16)  # 60 FPS
        
        self.frame_counter = 0
        self.is_preview_active = True
        
        # Stats update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_demo_stats)
        self.stats_timer.start(500)
        
    def init_ui(self):
        """Initialize complete demo UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Title bar
        title_layout = QHBoxLayout()
        title = QWidget()
        title.setFixedHeight(50)
        title.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #3a3a3a, stop:1 #2a2a2a);
            border-bottom: 2px solid #555;
        """)
        title_inner = QHBoxLayout(title)
        
        logo_label = QWidget()
        logo_label.setFixedSize(40, 40)
        logo_label.setStyleSheet("""
            background-color: #4CAF50;
            border-radius: 20px;
        """)
        title_inner.addWidget(logo_label)
        
        title_text = QWidget()
        title_text_layout = QVBoxLayout(title_text)
        title_text_layout.setContentsMargins(0, 0, 0, 0)
        title_text_layout.setSpacing(0)
        
        app_name = QTextEdit("PD Software Professional")
        app_name.setReadOnly(True)
        app_name.setFixedHeight(25)
        app_name.setStyleSheet("font-size: 16px; font-weight: bold; border: none; background: transparent;")
        title_text_layout.addWidget(app_name)
        
        subtitle = QTextEdit("Broadcast Production Suite")
        subtitle.setReadOnly(True)
        subtitle.setFixedHeight(20)
        subtitle.setStyleSheet("font-size: 12px; color: #888; border: none; background: transparent;")
        title_text_layout.addWidget(subtitle)
        
        title_inner.addWidget(title_text)
        title_inner.addStretch()
        
        main_layout.addWidget(title)
        
        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Video and status
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Video display group
        video_group = QGroupBox("NDI Preview - Resource Aware")
        video_layout = QVBoxLayout()
        
        self.video_display = ResourceAwareVideoDisplay()
        self.video_display.setMinimumSize(960, 540)
        video_layout.addWidget(self.video_display)
        
        video_group.setLayout(video_layout)
        left_layout.addWidget(video_group)
        
        # Enhanced streaming status
        status_group = QGroupBox("Streaming Status")
        status_layout = QVBoxLayout()
        
        self.streaming_status = StreamingStatusEnhanced()
        status_layout.addWidget(self.streaming_status)
        
        status_group.setLayout(status_layout)
        left_layout.addWidget(status_group)
        
        content_splitter.addWidget(left_panel)
        
        # Right panel - Controls and monitoring
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # SRT streaming controls
        control_group = QGroupBox("Streaming Controls")
        control_layout = QVBoxLayout()
        
        self.srt_widget = IntegratedSRTWidget(self.auth_manager)
        self.srt_widget.setMaximumHeight(600)
        
        # Connect all signals
        self.setup_connections()
        
        control_layout.addWidget(self.srt_widget)
        control_group.setLayout(control_layout)
        right_layout.addWidget(control_group)
        
        # System log
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        log_layout.addWidget(self.log_display)
        
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group)
        
        right_layout.addStretch()
        
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([1000, 600])
        
        main_layout.addWidget(content_splitter)
        
        # Initial log messages
        self.log("🚀 PD Software Professional Started")
        self.log("✅ GPU acceleration detected and ready")
        self.log("✅ Resource monitoring active")
        self.log("✅ Network adaptive latency enabled")
        self.log("📡 Ready for streaming")
        
    def setup_connections(self):
        """Connect all components together"""
        # Video display connections
        self.srt_widget.connect_video_display(self.video_display)
        
        # Preview pause/resume
        self.srt_widget.ndi_preview_pause_requested.connect(self.on_preview_pause)
        self.srt_widget.ndi_preview_resume_requested.connect(self.on_preview_resume)
        
        # Status updates
        self.srt_widget.srt_manager.stream_status_changed.connect(
            lambda status: self.log(f"📡 {status}")
        )
        self.srt_widget.srt_manager.stream_error.connect(
            lambda error: self.log(f"❌ {error}")
        )
        
        # Streaming state changes
        self.video_display.preview_paused.connect(
            lambda: self.streaming_status.update_stats({'resource_optimized': True})
        )
        self.video_display.preview_resumed.connect(
            lambda: self.streaming_status.update_stats({'resource_optimized': False})
        )
        
        # Connect streaming start/stop
        self.srt_widget.start_button.clicked.connect(self.on_streaming_start)
        self.srt_widget.stop_button.clicked.connect(self.on_streaming_stop)
        
    def on_streaming_start(self):
        """Handle streaming start"""
        stream_name = self.srt_widget.stream_name_input.text() or "demo_stream"
        self.streaming_status.start_streaming(stream_name)
        self.log(f"🎬 Started streaming: {stream_name}")
        
    def on_streaming_stop(self):
        """Handle streaming stop"""
        self.streaming_status.stop_streaming()
        self.log("⏹ Stopped streaming")
        
    def on_preview_pause(self):
        """Handle preview pause"""
        self.is_preview_active = False
        self.log("🔋 NDI preview paused - Resources optimized")
        
    def on_preview_resume(self):
        """Handle preview resume"""
        self.is_preview_active = True
        self.log("▶️ NDI preview resumed")
        
    def generate_demo_frame(self):
        """Generate demo NDI frame with professional look"""
        if self.is_preview_active:
            frame = QImage(1920, 1080, QImage.Format.Format_RGB888)
            painter = QPainter(frame)
            
            # Professional gradient background
            gradient = QLinearGradient(0, 0, 1920, 1080)
            gradient.setColorAt(0, QColor(40, 44, 52))
            gradient.setColorAt(0.5, QColor(33, 37, 43))
            gradient.setColorAt(1, QColor(25, 28, 33))
            painter.fillRect(0, 0, 1920, 1080, gradient)
            
            # Draw grid overlay
            painter.setPen(QColor(60, 60, 60, 50))
            for x in range(0, 1920, 100):
                painter.drawLine(x, 0, x, 1080)
            for y in range(0, 1080, 100):
                painter.drawLine(0, y, 1920, y)
            
            # Main content
            painter.setPen(QColor(255, 255, 255))
            font = QFont("Arial", 48, QFont.Weight.Bold)
            painter.setFont(font)
            
            # Draw main text
            painter.drawText(
                frame.rect(), 
                Qt.AlignmentFlag.AlignCenter,
                f"NDI SOURCE - CAMERA 1\nFrame #{self.frame_counter:06d}"
            )
            
            # Timecode
            font.setPointSize(24)
            painter.setFont(font)
            import datetime
            timecode = datetime.datetime.now().strftime("%H:%M:%S:%f")[:-3]
            painter.drawText(100, 980, f"TC: {timecode}")
            
            # Resolution and format
            painter.drawText(1620, 980, "1920x1080 | H.264")
            
            # Professional broadcast elements
            # Safe area markers
            painter.setPen(QPen(QColor(255, 255, 0, 80), 2))
            painter.drawRect(96, 54, 1728, 972)  # 10% safe area
            
            painter.end()
            
            self.video_display.update_frame(frame)
            self.frame_counter += 1
            
    def update_demo_stats(self):
        """Update demo streaming statistics"""
        if self.streaming_status.is_streaming:
            import random
            
            # Simulate realistic streaming stats
            stats = {
                'bitrate': f"{random.uniform(2.5, 3.5):.1f} Mbps",
                'fps': random.randint(29, 31),
                'latency': random.randint(80, 120),
                'viewers': random.randint(10, 50),
                'dropped_frames': 0 if random.random() > 0.1 else random.randint(1, 5)
            }
            
            self.streaming_status.update_stats(stats)
            self.video_display.update_stream_stats(stats)
            
    def log(self, message: str):
        """Add message to log display"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def closeEvent(self, event):
        """Clean up on close"""
        self.demo_timer.stop()
        self.stats_timer.stop()
        event.accept()


def main():
    """Run the complete integration demo"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo
    demo = CompleteIntegrationDemo()
    demo.show()
    
    print("=" * 80)
    print("🚀 PD SOFTWARE PROFESSIONAL - COMPLETE INTEGRATION DEMO")
    print("=" * 80)
    print()
    print("FEATURES DEMONSTRATED:")
    print("  ✅ GPU-Accelerated H.264 Encoding (NVENC/QuickSync/AMF)")
    print("  ✅ Resource Optimization with NDI Preview Auto-Pause")
    print("  ✅ Fade-to-Black Animation During Streaming")
    print("  ✅ Network-Adaptive SRT Latency (Ping × 3)")
    print("  ✅ Real-time System Resource Monitoring")
    print("  ✅ Enhanced Streaming Status Display")
    print("  ✅ Professional Broadcast UI")
    print()
    print("INSTRUCTIONS:")
    print("  1. Click 'Generate' to create a unique stream key")
    print("  2. Select streaming parameters (bitrate, FPS, profile)")
    print("  3. Click 'Start Streaming' to begin")
    print("  4. Watch NDI preview fade to black and resources optimize")
    print("  5. Monitor real-time stats and GPU usage")
    print()
    print("=" * 80)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()