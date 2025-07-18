#!/usr/bin/env python3
"""
Demo: PD Software Resource Optimization
Shows real-time resource monitoring and NDI preview auto-pause during streaming
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPainter, QColor, QFont

# Import our components
from pd_app.ui.srt_widget_integrated import IntegratedSRTWidget
from pd_app.ui.video_display_resource_aware import ResourceAwareVideoDisplay, StreamingStatusWidget
from pd_app.core.resource_monitor import SystemResourceMonitor, ResourceOptimizer


class DemoAuthManager:
    """Mock auth manager for demo"""
    def is_logged_in(self):
        return True
    
    def get_user_info(self):
        return {
            'user_id': 'demo_user',
            'unique_address': 'demo123'
        }


class DemoNDIManager:
    """Mock NDI manager for demo"""
    def __init__(self):
        self.sources = ['Camera 1', 'Camera 2', 'Graphics PC']


class ResourceOptimizationDemo(QMainWindow):
    """Demo window showing resource optimization in action"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PD Software - Resource Optimization Demo")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #fff;
            }
            QWidget {
                background-color: #2a2a2a;
                color: #fff;
            }
        """)
        
        # Create mock managers
        self.auth_manager = DemoAuthManager()
        self.ndi_manager = DemoNDIManager()
        
        # Setup UI
        self.init_ui()
        
        # Demo timer for simulated NDI frames
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.generate_demo_frame)
        self.demo_timer.start(16)  # 60 FPS
        
        self.frame_counter = 0
        
    def init_ui(self):
        """Initialize demo UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # Left side - Video display and status
        left_layout = QVBoxLayout()
        
        # Video display with resource awareness
        self.video_display = ResourceAwareVideoDisplay()
        self.video_display.setMinimumSize(960, 540)
        left_layout.addWidget(self.video_display)
        
        # Streaming status widget
        self.status_widget = StreamingStatusWidget()
        left_layout.addWidget(self.status_widget)
        
        left_layout.addStretch()
        main_layout.addLayout(left_layout)
        
        # Right side - Controls
        right_layout = QVBoxLayout()
        
        # Integrated SRT widget with all features
        self.srt_widget = IntegratedSRTWidget(self.auth_manager, self.ndi_manager)
        self.srt_widget.setMaximumWidth(500)
        
        # Connect video display signals
        self.srt_widget.connect_video_display(self.video_display)
        
        # Connect preview pause/resume
        self.srt_widget.ndi_preview_pause_requested.connect(self.on_preview_pause)
        self.srt_widget.ndi_preview_resume_requested.connect(self.on_preview_resume)
        
        # Connect status updates
        self.video_display.preview_paused.connect(
            lambda: self.status_widget.update_status(False, True)
        )
        self.video_display.preview_resumed.connect(
            lambda: self.status_widget.update_status(True, False)
        )
        
        right_layout.addWidget(self.srt_widget)
        right_layout.addStretch()
        
        main_layout.addLayout(right_layout)
        
        # Resource optimizer tips
        self.resource_optimizer = ResourceOptimizer()
        self.resource_monitor = SystemResourceMonitor()
        self.resource_monitor.resources_updated.connect(self.check_optimization_tips)
        self.resource_monitor.start_monitoring()
        
    def generate_demo_frame(self):
        """Generate demo NDI frame"""
        if self.video_display.is_preview_active:
            # Create a demo frame
            frame = QImage(1920, 1080, QImage.Format.Format_RGB888)
            painter = QPainter(frame)
            
            # Background gradient
            gradient = painter.createLinearGradient(0, 0, 1920, 1080)
            gradient.setColorAt(0, QColor(30, 30, 40))
            gradient.setColorAt(1, QColor(60, 40, 80))
            painter.fillRect(0, 0, 1920, 1080, gradient)
            
            # Draw demo content
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(48)
            painter.setFont(font)
            
            painter.drawText(
                frame.rect(), 
                Qt.AlignmentFlag.AlignCenter,
                f"NDI Demo Frame #{self.frame_counter}\nResource Optimization Active"
            )
            
            # Add timestamp
            font.setPointSize(24)
            painter.setFont(font)
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            painter.drawText(100, 100, f"Time: {timestamp}")
            
            # Show resource usage
            stats = self.resource_monitor.get_current_stats()
            painter.drawText(100, 150, f"CPU: {stats['cpu_percent']:.1f}%")
            painter.drawText(100, 200, f"Memory: {stats['memory_percent']:.1f}%")
            
            if self.video_display.is_streaming:
                painter.drawText(100, 250, "🎥 Streaming Active - Preview will pause soon")
            
            painter.end()
            
            # Update video display
            self.video_display.update_frame(frame)
            self.frame_counter += 1
            
    def on_preview_pause(self):
        """Handle preview pause request"""
        print("📍 NDI Preview Pause Requested - Saving Resources")
        self.video_display.is_preview_active = False
        
    def on_preview_resume(self):
        """Handle preview resume request"""
        print("📍 NDI Preview Resume Requested")
        self.video_display.is_preview_active = True
        
    def check_optimization_tips(self, stats):
        """Check and display optimization tips"""
        tips = self.resource_optimizer.get_optimization_tips(stats)
        for tip in tips:
            self.srt_widget.append_status(f"💡 {tip}")
            
    def closeEvent(self, event):
        """Clean up on close"""
        self.demo_timer.stop()
        self.resource_monitor.stop_monitoring()
        event.accept()


def main():
    """Run the demo"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo
    demo = ResourceOptimizationDemo()
    demo.show()
    
    print("🚀 PD Software Resource Optimization Demo")
    print("=" * 50)
    print("Features demonstrated:")
    print("1. Real-time resource monitoring (CPU, Memory, GPU)")
    print("2. NDI preview auto-pause during streaming")
    print("3. Fade-to-black animation")
    print("4. GPU acceleration detection")
    print("5. Network-adaptive latency")
    print("6. Resource optimization recommendations")
    print("=" * 50)
    print("Try starting a stream to see resource optimization in action!")
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()