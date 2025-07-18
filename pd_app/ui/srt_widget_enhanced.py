# pd_app/ui/srt_widget_enhanced.py
"""
Enhanced SRT Widget - Professional Broadcasting Grade (0.1-10 Mbps)
Supports H.264 streaming with flexible bitrate options
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QLineEdit, QGroupBox,
    QTextEdit, QSpinBox, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

class EnhancedSRTWidget(QWidget):
    """Enhanced SRT Streaming Widget with Professional Features"""
    
    # Custom signals
    bitrate_changed = pyqtSignal(str)
    
    def __init__(self, srt_manager, auth_manager):
        super().__init__()
        self.srt_manager = srt_manager
        self.auth_manager = auth_manager
        self.init_ui()
        self.init_connections()
        
        # Timer for statistics
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(5000)  # Update every 5 seconds
        
    def init_ui(self):
        """Initialize Professional UI"""
        layout = QVBoxLayout(self)
        
        # Source Selection Group
        source_group = QGroupBox("Streaming Source")
        source_layout = QVBoxLayout()
        
        # Source Type Selection
        source_type_layout = QHBoxLayout()
        source_type_layout.addWidget(QLabel("Source Type:"))
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["NDI", "Screen Capture", "Camera"])
        source_type_layout.addWidget(self.source_type_combo)
        
        source_type_layout.addStretch()
        source_layout.addLayout(source_type_layout)
        
        # NDI Source Selection
        self.ndi_source_layout = QHBoxLayout()
        self.ndi_source_layout.addWidget(QLabel("NDI Source:"))
        
        self.ndi_source_combo = QComboBox()
        self.ndi_source_combo.addItem("Select NDI Source")
        self.ndi_source_layout.addWidget(self.ndi_source_combo)
        
        self.refresh_ndi_button = QPushButton("Refresh")
        self.refresh_ndi_button.setMaximumWidth(80)
        self.ndi_source_layout.addWidget(self.refresh_ndi_button)
        
        source_layout.addLayout(self.ndi_source_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Professional Streaming Settings
        settings_group = QGroupBox("Professional Streaming Settings")
        settings_layout = QVBoxLayout()
        
        # Stream Name
        stream_name_layout = QHBoxLayout()
        stream_name_layout.addWidget(QLabel("Stream Name:"))
        
        self.stream_name_input = QLineEdit()
        self.stream_name_input.setPlaceholderText("Auto-generated")
        stream_name_layout.addWidget(self.stream_name_input)
        
        self.generate_name_button = QPushButton("Auto Generate")
        stream_name_layout.addWidget(self.generate_name_button)
        
        settings_layout.addLayout(stream_name_layout)
        
        # Bitrate Selection (0.1-10 Mbps)
        bitrate_layout = QVBoxLayout()
        bitrate_header = QHBoxLayout()
        bitrate_header.addWidget(QLabel("Bitrate:"))
        
        self.bitrate_preset_combo = QComboBox()
        self.bitrate_preset_combo.addItems([
            "Custom",
            "100 Kbps (Mobile)",
            "500 Kbps (Low)",
            "1 Mbps (Standard)",
            "2 Mbps (Good)",
            "3 Mbps (Better)",
            "5 Mbps (HD)",
            "8 Mbps (Full HD)",
            "10 Mbps (Professional)"
        ])
        self.bitrate_preset_combo.setCurrentIndex(3)  # Default 1 Mbps
        bitrate_header.addWidget(self.bitrate_preset_combo)
        
        self.bitrate_label = QLabel("1.0 Mbps")
        self.bitrate_label.setMinimumWidth(80)
        self.bitrate_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        font = QFont()
        font.setBold(True)
        self.bitrate_label.setFont(font)
        bitrate_header.addWidget(self.bitrate_label)
        
        bitrate_layout.addLayout(bitrate_header)
        
        # Custom Bitrate Slider (0.1-10 Mbps)
        self.bitrate_slider = QSlider(Qt.Orientation.Horizontal)
        self.bitrate_slider.setMinimum(1)      # 0.1 Mbps = 100 Kbps
        self.bitrate_slider.setMaximum(100)    # 10 Mbps = 10000 Kbps
        self.bitrate_slider.setValue(10)       # 1.0 Mbps default
        self.bitrate_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.bitrate_slider.setTickInterval(10)
        self.bitrate_slider.setEnabled(False)  # Disabled unless Custom selected
        bitrate_layout.addWidget(self.bitrate_slider)
        
        # Bitrate scale labels
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("0.1"))
        scale_layout.addStretch()
        scale_layout.addWidget(QLabel("1"))
        scale_layout.addStretch()
        scale_layout.addWidget(QLabel("5"))
        scale_layout.addStretch()
        scale_layout.addWidget(QLabel("10 Mbps"))
        bitrate_layout.addLayout(scale_layout)
        
        settings_layout.addLayout(bitrate_layout)
        
        # Advanced Settings
        advanced_layout = QHBoxLayout()
        
        # FPS Settings
        advanced_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(30)
        self.fps_spin.setSingleStep(5)
        advanced_layout.addWidget(self.fps_spin)
        
        # H.264 Profile
        advanced_layout.addWidget(QLabel("H.264 Profile:"))
        self.h264_profile_combo = QComboBox()
        self.h264_profile_combo.addItems(["baseline", "main", "high"])
        self.h264_profile_combo.setCurrentIndex(1)  # main profile
        advanced_layout.addWidget(self.h264_profile_combo)
        
        # H.264 Preset
        advanced_layout.addWidget(QLabel("Encoding:"))
        self.h264_preset_combo = QComboBox()
        self.h264_preset_combo.addItems([
            "ultrafast",
            "superfast", 
            "veryfast",
            "faster",
            "fast"
        ])
        self.h264_preset_combo.setCurrentIndex(0)  # ultrafast for low latency
        advanced_layout.addWidget(self.h264_preset_combo)
        
        advanced_layout.addStretch()
        settings_layout.addLayout(advanced_layout)
        
        # Network Settings
        network_layout = QHBoxLayout()
        
        # Key Frame Interval
        network_layout.addWidget(QLabel("Keyframe:"))
        self.keyframe_spin = QSpinBox()
        self.keyframe_spin.setRange(1, 10)
        self.keyframe_spin.setValue(2)
        self.keyframe_spin.setSuffix(" sec")
        network_layout.addWidget(self.keyframe_spin)
        
        # SRT Latency
        network_layout.addWidget(QLabel("SRT Latency:"))
        self.srt_latency_spin = QSpinBox()
        self.srt_latency_spin.setRange(20, 1000)
        self.srt_latency_spin.setValue(120)
        self.srt_latency_spin.setSingleStep(20)
        self.srt_latency_spin.setSuffix(" ms")
        network_layout.addWidget(self.srt_latency_spin)
        
        # Audio Settings
        network_layout.addWidget(QLabel("Audio:"))
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems(["64k", "96k", "128k", "192k", "256k"])
        self.audio_bitrate_combo.setCurrentIndex(2)  # 128k default
        network_layout.addWidget(self.audio_bitrate_combo)
        
        network_layout.addStretch()
        settings_layout.addLayout(network_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Streaming Controls
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Streaming")
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Streaming")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
        
        # Status Display
        status_group = QGroupBox("Streaming Status")
        status_layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(120)
        self.status_text.setStyleSheet("font-family: monospace;")
        status_layout.addWidget(self.status_text)
        
        # Real-time Statistics
        stats_layout = QHBoxLayout()
        
        self.bitrate_actual_label = QLabel("Bitrate: --")
        stats_layout.addWidget(self.bitrate_actual_label)
        
        self.fps_actual_label = QLabel("FPS: --")
        stats_layout.addWidget(self.fps_actual_label)
        
        self.dropped_label = QLabel("Dropped: 0")
        stats_layout.addWidget(self.dropped_label)
        
        self.latency_label = QLabel("Latency: -- ms")
        stats_layout.addWidget(self.latency_label)
        
        stats_layout.addStretch()
        status_layout.addLayout(stats_layout)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def init_connections(self):
        """Initialize signal connections"""
        # SRT Manager signals
        self.srt_manager.stream_status_changed.connect(self.on_stream_status_changed)
        self.srt_manager.stream_error.connect(self.on_stream_error)
        self.srt_manager.stream_stats_updated.connect(self.on_stream_stats_updated)
        
        # UI signals
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.bitrate_preset_combo.currentTextChanged.connect(self.on_bitrate_preset_changed)
        self.bitrate_slider.valueChanged.connect(self.on_bitrate_slider_changed)
        self.generate_name_button.clicked.connect(self.generate_stream_name)
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)
        self.refresh_ndi_button.clicked.connect(self.update_ndi_sources)
        
    def on_source_type_changed(self, source_type):
        """Handle source type change"""
        is_ndi = source_type == "NDI"
        self.ndi_source_combo.setVisible(is_ndi)
        self.refresh_ndi_button.setVisible(is_ndi)
        self.fps_spin.setEnabled(source_type != "NDI")  # NDI has its own FPS
        
        if is_ndi:
            self.update_ndi_sources()
            
    def on_bitrate_preset_changed(self, preset):
        """Handle bitrate preset change"""
        self.bitrate_slider.setEnabled(preset == "Custom")
        
        # Map preset to bitrate value
        preset_map = {
            "100 Kbps (Mobile)": 1,      # 0.1 Mbps
            "500 Kbps (Low)": 5,          # 0.5 Mbps
            "1 Mbps (Standard)": 10,      # 1.0 Mbps
            "2 Mbps (Good)": 20,          # 2.0 Mbps
            "3 Mbps (Better)": 30,        # 3.0 Mbps
            "5 Mbps (HD)": 50,            # 5.0 Mbps
            "8 Mbps (Full HD)": 80,       # 8.0 Mbps
            "10 Mbps (Professional)": 100 # 10.0 Mbps
        }
        
        if preset in preset_map:
            self.bitrate_slider.setValue(preset_map[preset])
            
    def on_bitrate_slider_changed(self, value):
        """Handle bitrate slider change"""
        mbps = value / 10.0
        self.bitrate_label.setText(f"{mbps:.1f} Mbps")
        self.bitrate_changed.emit(f"{int(mbps * 1000)}k")  # Convert to kbps
        
    def get_current_bitrate(self):
        """Get current bitrate in FFmpeg format"""
        value = self.bitrate_slider.value()
        mbps = value / 10.0
        
        if mbps < 1:
            return f"{int(mbps * 1000)}k"
        else:
            return f"{mbps:.1f}M"
            
    def update_ndi_sources(self):
        """Update NDI source list"""
        # TODO: Get NDI sources from NDI manager
        pass
        
    def generate_stream_name(self):
        """Generate unique stream name"""
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            stream_name = self.srt_manager.generate_stream_key(
                user_info['user_id'],
                user_info['unique_address']
            )
            self.stream_name_input.setText(stream_name)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Login Required", 
                              "Please login to generate stream name.")
            
    def start_streaming(self):
        """Start streaming with professional settings"""
        # Validate stream name
        stream_name = self.stream_name_input.text().strip()
        if not stream_name:
            self.generate_stream_name()
            stream_name = self.stream_name_input.text().strip()
            
        if not stream_name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Please enter stream name.")
            return
            
        # Get streaming parameters
        source_type = self.source_type_combo.currentText()
        bitrate = self.get_current_bitrate()
        fps = self.fps_spin.value()
        h264_profile = self.h264_profile_combo.currentText()
        h264_preset = self.h264_preset_combo.currentText()
        keyframe_interval = self.keyframe_spin.value()
        audio_bitrate = self.audio_bitrate_combo.currentText()
        srt_latency = self.srt_latency_spin.value()
        
        try:
            # Build FFmpeg parameters
            ffmpeg_params = {
                'bitrate': bitrate,
                'fps': fps,
                'h264_profile': h264_profile,
                'h264_preset': h264_preset,
                'keyframe_interval': keyframe_interval,
                'audio_bitrate': audio_bitrate,
                'srt_latency': srt_latency
            }
            
            if source_type == "NDI":
                ndi_source = self.ndi_source_combo.currentText()
                if ndi_source and ndi_source != "Select NDI Source":
                    self.srt_manager.start_ndi_streaming_enhanced(
                        ndi_source, stream_name, ffmpeg_params)
                else:
                    raise ValueError("Please select NDI source")
                    
            elif source_type == "Screen Capture":
                self.srt_manager.start_screen_streaming_enhanced(
                    stream_name, ffmpeg_params)
                    
            elif source_type == "Camera":
                # TODO: Implement camera streaming
                raise NotImplementedError("Camera streaming coming soon")
                
            # Update UI state
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.source_type_combo.setEnabled(False)
            self.settings_enabled(False)
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Streaming Failed", str(e))
            
    def stop_streaming(self):
        """Stop streaming"""
        self.srt_manager.stop_streaming()
        
        # Update UI state
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_type_combo.setEnabled(True)
        self.settings_enabled(True)
        
    def settings_enabled(self, enabled):
        """Enable/disable settings during streaming"""
        self.bitrate_preset_combo.setEnabled(enabled)
        self.bitrate_slider.setEnabled(enabled and 
                                      self.bitrate_preset_combo.currentText() == "Custom")
        self.fps_spin.setEnabled(enabled)
        self.h264_profile_combo.setEnabled(enabled)
        self.h264_preset_combo.setEnabled(enabled)
        self.keyframe_spin.setEnabled(enabled)
        self.srt_latency_spin.setEnabled(enabled)
        self.audio_bitrate_combo.setEnabled(enabled)
        
    def on_stream_status_changed(self, status):
        """Handle stream status change"""
        self.append_status(f"Status: {status}")
        
    def on_stream_error(self, error):
        """Handle stream error"""
        self.append_status(f"ERROR: {error}")
        
    def on_stream_stats_updated(self, stats):
        """Handle stream statistics update"""
        # Update real-time statistics display
        if 'bitrate' in stats:
            self.bitrate_actual_label.setText(f"Bitrate: {stats['bitrate']}")
        if 'fps' in stats:
            self.fps_actual_label.setText(f"FPS: {stats['fps']}")
        if 'dropped' in stats:
            self.dropped_label.setText(f"Dropped: {stats['dropped']}")
        if 'latency' in stats:
            self.latency_label.setText(f"Latency: {stats['latency']} ms")
            
    def append_status(self, message):
        """Append status message with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_stats(self):
        """Update streaming statistics"""
        if self.srt_manager.is_streaming:
            stream_info = self.srt_manager.get_stream_info()
            if stream_info['is_streaming']:
                self.srt_manager.request_stream_stats()