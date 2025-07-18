# pd_app/ui/srt_widget_integrated.py
"""
Integrated SRT Widget with Resource Optimization
Coordinates NDI preview pause/resume with GPU-accelerated streaming
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QComboBox, QLabel, QLineEdit, QGroupBox,
                           QTextEdit, QSpinBox, QCheckBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ..core.srt_manager_gpu import GPUAcceleratedSRTManager
from .gpu_monitor_widget import GPUMonitorWidget, ResourceMonitorPanel
from .video_display_resource_aware import ResourceAwareVideoDisplay
from .srt_widget_adaptive import NetworkStatusWidget

class IntegratedSRTWidget(QWidget):
    """Complete SRT streaming widget with all features integrated"""
    
    # Signals
    ndi_preview_pause_requested = pyqtSignal()
    ndi_preview_resume_requested = pyqtSignal()
    video_display_update_requested = pyqtSignal(bool, str)  # is_streaming, stream_name
    
    def __init__(self, auth_manager, ndi_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.ndi_manager = ndi_manager
        
        # Create GPU-accelerated SRT manager
        self.srt_manager = GPUAcceleratedSRTManager()
        
        # Setup preview control callbacks
        self.srt_manager.set_preview_callbacks(
            self._pause_ndi_preview,
            self._resume_ndi_preview
        )
        
        self.init_ui()
        self.init_connections()
        
        # Update timers
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)
        
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self.update_duration)
        self.stream_start_time = 0
        
    def init_ui(self):
        """Initialize integrated UI"""
        layout = QVBoxLayout(self)
        
        # Top section: GPU Monitor + Network Status
        top_section = QHBoxLayout()
        
        # GPU Monitor (left)
        self.gpu_monitor = GPUMonitorWidget()
        self.gpu_monitor.setMaximumWidth(350)
        top_section.addWidget(self.gpu_monitor)
        
        # Network Status (right)
        self.network_status = NetworkStatusWidget()
        top_section.addWidget(self.network_status)
        
        layout.addLayout(top_section)
        
        # Resource optimization control
        opt_frame = QFrame()
        opt_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 5px;
                padding: 10px;
                margin: 5px 0;
            }
        """)
        opt_layout = QHBoxLayout(opt_frame)
        
        opt_icon = QLabel("🔋")
        opt_icon.setStyleSheet("font-size: 20px;")
        opt_layout.addWidget(opt_icon)
        
        opt_label = QLabel("Resource Optimization")
        opt_label.setStyleSheet("font-weight: bold; color: #fff;")
        opt_layout.addWidget(opt_label)
        
        self.resource_opt_check = QCheckBox("Auto-pause NDI preview during streaming")
        self.resource_opt_check.setChecked(True)
        self.resource_opt_check.setToolTip(
            "Automatically pauses NDI preview when streaming starts to save CPU/GPU resources.\n"
            "The preview will resume when streaming stops."
        )
        opt_layout.addWidget(self.resource_opt_check)
        
        opt_layout.addStretch()
        
        self.resource_monitor = ResourceMonitorPanel()
        opt_layout.addWidget(self.resource_monitor)
        
        layout.addWidget(opt_frame)
        
        # Source selection
        source_group = QGroupBox("Streaming Source")
        source_layout = QVBoxLayout()
        
        source_type_layout = QHBoxLayout()
        source_type_layout.addWidget(QLabel("Source:"))
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["NDI", "Screen Capture", "Camera"])
        source_type_layout.addWidget(self.source_type_combo)
        
        if self.ndi_manager:
            self.ndi_source_combo = QComboBox()
            self.ndi_source_combo.addItem("Select NDI Source")
            self._update_ndi_sources()
            source_type_layout.addWidget(self.ndi_source_combo)
        
        source_type_layout.addStretch()
        source_layout.addLayout(source_type_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Streaming settings
        settings_group = QGroupBox("Streaming Settings")
        settings_layout = QVBoxLayout()
        
        # Stream name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Stream:"))
        
        self.stream_name_input = QLineEdit()
        self.stream_name_input.setPlaceholderText("Auto-generated")
        name_layout.addWidget(self.stream_name_input)
        
        self.generate_button = QPushButton("Generate")
        name_layout.addWidget(self.generate_button)
        
        settings_layout.addLayout(name_layout)
        
        # Bitrate and quality
        quality_layout = QHBoxLayout()
        
        quality_layout.addWidget(QLabel("Bitrate:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems([
            "100 Kbps", "500 Kbps", "1 Mbps", "2 Mbps",
            "3 Mbps", "5 Mbps", "8 Mbps", "10 Mbps"
        ])
        self.bitrate_combo.setCurrentIndex(3)  # 2 Mbps default
        quality_layout.addWidget(self.bitrate_combo)
        
        quality_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(30)
        quality_layout.addWidget(self.fps_spin)
        
        quality_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["baseline", "main", "high"])
        self.profile_combo.setCurrentIndex(1)
        quality_layout.addWidget(self.profile_combo)
        
        quality_layout.addStretch()
        settings_layout.addLayout(quality_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🎬 Start Streaming")
        self.start_button.setMinimumHeight(45)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹ Stop Streaming")
        self.stop_button.setMinimumHeight(45)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
        
        # Status display
        status_group = QGroupBox("Streaming Status")
        status_layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(80)
        self.status_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        status_layout.addWidget(self.status_text)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def init_connections(self):
        """Initialize signal connections"""
        # SRT Manager signals
        self.srt_manager.stream_status_changed.connect(self.on_stream_status_changed)
        self.srt_manager.stream_error.connect(self.on_stream_error)
        self.srt_manager.stream_stats_updated.connect(self.on_stream_stats_updated)
        
        # Network monitor signals
        self.srt_manager.network_monitor.ping_updated.connect(self.network_status.update_ping)
        self.srt_manager.network_monitor.latency_updated.connect(self.network_status.update_latency)
        self.srt_manager.network_monitor.network_status_changed.connect(self.network_status.update_quality)
        
        # GPU monitor signals
        self.gpu_monitor.gpu_status_changed.connect(self.on_gpu_status_changed)
        
        # UI signals
        self.resource_opt_check.toggled.connect(self.on_resource_opt_changed)
        self.network_status.auto_checkbox.toggled.connect(self.srt_manager.set_adaptive_mode)
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.generate_button.clicked.connect(self.generate_stream_name)
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)
        
    def _pause_ndi_preview(self):
        """Pause NDI preview for resource optimization"""
        if self.resource_opt_check.isChecked():
            self.append_status("🔋 Pausing NDI preview to optimize resources...")
            self.ndi_preview_pause_requested.emit()
            
            # Update resource monitor state
            self.resource_monitor.set_streaming_state(False, True)  # preview paused, streaming active
            self.resource_monitor.update_resources(0, 0, True)  # Mark as optimized
            
    def _resume_ndi_preview(self):
        """Resume NDI preview after streaming"""
        self.append_status("▶️ Resuming NDI preview...")
        self.ndi_preview_resume_requested.emit()
        
        # Update resource monitor state
        self.resource_monitor.set_streaming_state(True, False)  # preview active, streaming stopped
        self.resource_monitor.update_resources(0, 0, False)  # Mark as normal
        
    def on_resource_opt_changed(self, checked):
        """Handle resource optimization toggle"""
        self.srt_manager.set_resource_optimization(checked)
        if checked:
            self.append_status("✅ Resource optimization enabled")
        else:
            self.append_status("❌ Resource optimization disabled")
            
    def on_source_type_changed(self, source_type):
        """Handle source type change"""
        if hasattr(self, 'ndi_source_combo'):
            self.ndi_source_combo.setVisible(source_type == "NDI")
            
    def _update_ndi_sources(self):
        """Update NDI source list from manager"""
        if not self.ndi_manager:
            return
            
        # This would get sources from NDI manager
        # For now, just placeholder
        self.ndi_source_combo.clear()
        self.ndi_source_combo.addItem("Select NDI Source")
        # Add actual sources here
        
    def generate_stream_name(self):
        """Generate unique stream name"""
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            stream_name = self.srt_manager.generate_stream_key(
                user_info['user_id'],
                user_info.get('unique_address', 'default')
            )
            self.stream_name_input.setText(stream_name)
            self.append_status(f"✅ Stream name generated: {stream_name}")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Login Required", "Please login to generate stream name.")
            
    def start_streaming(self):
        """Start GPU-accelerated streaming with resource optimization"""
        stream_name = self.stream_name_input.text().strip()
        if not stream_name:
            self.generate_stream_name()
            stream_name = self.stream_name_input.text().strip()
            
        if not stream_name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Please enter stream name.")
            return
            
        # Get GPU info
        gpu_status = self.srt_manager.get_gpu_status()
        self.gpu_monitor.update_gpu_info(gpu_status)
        
        # Build parameters
        params = {
            'bitrate': self._parse_bitrate(self.bitrate_combo.currentText()),
            'fps': self.fps_spin.value(),
            'h264_profile': self.profile_combo.currentText(),
            'keyframe_interval': 2,
            'audio_bitrate': '128k'
        }
        
        try:
            source_type = self.source_type_combo.currentText()
            
            # Signal video display to start streaming mode
            self.video_display_update_requested.emit(True, stream_name)
            
            if source_type == "NDI":
                ndi_source = self.ndi_source_combo.currentText() if hasattr(self, 'ndi_source_combo') else ""
                if ndi_source and ndi_source != "Select NDI Source":
                    self.srt_manager.start_ndi_streaming_gpu(ndi_source, stream_name, params)
                else:
                    raise ValueError("Please select NDI source")
                    
            elif source_type == "Screen Capture":
                # For screen capture, we don't need to pause anything
                self.srt_manager.resource_optimization = False
                self.srt_manager.start_screen_streaming_adaptive(stream_name, params)
                self.srt_manager.resource_optimization = self.resource_opt_check.isChecked()
                
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.source_type_combo.setEnabled(False)
            self.gpu_monitor.set_streaming_state(True)
            
            # Start duration timer
            import time
            self.stream_start_time = time.time()
            self.duration_timer.start(1000)
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Streaming Failed", str(e))
            self.video_display_update_requested.emit(False, "")
            
    def stop_streaming(self):
        """Stop streaming and resume preview"""
        self.srt_manager.stop_streaming()
        
        # Signal video display to stop streaming mode
        self.video_display_update_requested.emit(False, "")
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_type_combo.setEnabled(True)
        self.gpu_monitor.set_streaming_state(False)
        
        # Stop duration timer
        self.duration_timer.stop()
        
    def _parse_bitrate(self, bitrate_text: str) -> str:
        """Parse bitrate from combo box text"""
        parts = bitrate_text.split()
        if len(parts) >= 2:
            value = parts[0]
            unit = parts[1].lower()
            
            if unit == "kbps":
                return f"{value}k"
            elif unit == "mbps":
                return f"{value}M"
                
        return "2M"  # Default
        
    def on_stream_status_changed(self, status: str):
        """Handle stream status change"""
        self.append_status(f"📡 {status}")
        
    def on_stream_error(self, error: str):
        """Handle stream error"""
        self.append_status(f"❌ {error}")
        
    def on_stream_stats_updated(self, stats: dict):
        """Update streaming statistics"""
        # Forward to video display if connected
        pass
        
    def on_gpu_status_changed(self, stats: dict):
        """Handle GPU status updates"""
        # Could log or display additional GPU info
        pass
        
    def update_stats(self):
        """Update streaming statistics"""
        if self.srt_manager.is_streaming:
            stats = self.srt_manager.get_network_stats()
            # Update displays
            
    def update_duration(self):
        """Update streaming duration"""
        if self.stream_start_time > 0:
            import time
            duration = int(time.time() - self.stream_start_time)
            # Update video display with duration
            
    def append_status(self, message: str):
        """Append status message"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def connect_video_display(self, video_display):
        """Connect to video display widget"""
        if isinstance(video_display, ResourceAwareVideoDisplay):
            # Connect our signals to video display
            self.video_display_update_requested.connect(
                lambda streaming, name: (
                    video_display.start_streaming(name) if streaming 
                    else video_display.stop_streaming()
                )
            )