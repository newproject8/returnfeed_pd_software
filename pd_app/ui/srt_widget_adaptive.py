# pd_app/ui/srt_widget_adaptive.py
"""
Adaptive SRT Widget - Professional broadcasting with network-aware latency
Real-time ping monitoring and automatic SRT latency adjustment
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QLineEdit, QGroupBox,
    QTextEdit, QSpinBox, QSlider, QCheckBox,
    QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
import time

from ..core.srt_manager_adaptive import AdaptiveSRTManager, AdaptiveStreamingController

class NetworkStatusWidget(QFrame):
    """Network status display widget"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize network status UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("🌐 Network Status")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        
        self.auto_checkbox = QCheckBox("Auto")
        self.auto_checkbox.setChecked(True)
        self.auto_checkbox.setToolTip("Automatically adjust SRT latency based on network ping")
        title_layout.addStretch()
        title_layout.addWidget(self.auto_checkbox)
        
        layout.addLayout(title_layout)
        
        # Network stats grid
        stats_layout = QHBoxLayout()
        
        # Ping display
        ping_frame = self._create_stat_frame(
            "Ping",
            "-- ms",
            "#2196F3"  # Blue
        )
        self.ping_label = ping_frame.findChild(QLabel, "value_label")
        stats_layout.addWidget(ping_frame)
        
        # Latency display
        latency_frame = self._create_stat_frame(
            "SRT Latency",
            "-- ms",
            "#4CAF50"  # Green
        )
        self.latency_label = latency_frame.findChild(QLabel, "value_label")
        stats_layout.addWidget(latency_frame)
        
        # Quality indicator
        quality_frame = self._create_stat_frame(
            "Quality",
            "---",
            "#FF9800"  # Orange
        )
        self.quality_label = quality_frame.findChild(QLabel, "value_label")
        stats_layout.addWidget(quality_frame)
        
        layout.addLayout(stats_layout)
        
        # Latency formula display
        self.formula_label = QLabel("Latency = Ping × 3")
        self.formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.formula_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.formula_label)
        
        # Network preset selector
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Network:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Auto Detect", "Local LAN", "Regional", "Global", "Satellite"])
        preset_layout.addWidget(self.preset_combo)
        
        layout.addLayout(preset_layout)
        
    def _create_stat_frame(self, title: str, initial_value: str, color: str) -> QFrame:
        """Create a statistics display frame"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(initial_value)
        value_label.setObjectName("value_label")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(value_label)
        
        return frame
        
    def update_ping(self, ping_ms: float):
        """Update ping display"""
        self.ping_label.setText(f"{ping_ms:.1f} ms")
        
        # Color code based on ping
        if ping_ms < 10:
            color = "#4CAF50"  # Green
        elif ping_ms < 30:
            color = "#8BC34A"  # Light green
        elif ping_ms < 50:
            color = "#FFC107"  # Amber
        elif ping_ms < 100:
            color = "#FF9800"  # Orange
        else:
            color = "#F44336"  # Red
            
        self.ping_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        
    def update_latency(self, latency_ms: int):
        """Update latency display"""
        self.latency_label.setText(f"{latency_ms} ms")
        
    def update_quality(self, quality: str):
        """Update quality indicator"""
        self.quality_label.setText(quality)
        
        # Color based on quality
        colors = {
            "Excellent": "#4CAF50",
            "Good": "#8BC34A",
            "Fair": "#FFC107",
            "Poor": "#FF9800",
            "Bad": "#F44336"
        }
        color = colors.get(quality, "#999")
        self.quality_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")


class AdaptiveSRTWidget(QWidget):
    """Enhanced SRT Widget with adaptive network-based latency"""
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        
        # Use adaptive SRT manager
        self.srt_manager = AdaptiveSRTManager()
        self.controller = AdaptiveStreamingController(self.srt_manager)
        
        self.init_ui()
        self.init_connections()
        
        # Start UI update timer
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_network_display)
        self.ui_timer.start(1000)  # Update every second
        
    def init_ui(self):
        """Initialize adaptive UI"""
        layout = QVBoxLayout(self)
        
        # Network Status Widget (Top)
        self.network_status = NetworkStatusWidget()
        layout.addWidget(self.network_status)
        
        # Source Selection
        source_group = QGroupBox("Streaming Source")
        source_layout = QVBoxLayout()
        
        source_type_layout = QHBoxLayout()
        source_type_layout.addWidget(QLabel("Source:"))
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["NDI", "Screen Capture", "Camera"])
        source_type_layout.addWidget(self.source_type_combo)
        
        self.refresh_ndi_button = QPushButton("🔄")
        self.refresh_ndi_button.setMaximumWidth(30)
        self.refresh_ndi_button.setToolTip("Refresh NDI sources")
        source_type_layout.addWidget(self.refresh_ndi_button)
        
        source_type_layout.addStretch()
        source_layout.addLayout(source_type_layout)
        
        # NDI Source selector
        self.ndi_source_combo = QComboBox()
        self.ndi_source_combo.addItem("Select NDI Source")
        source_layout.addWidget(self.ndi_source_combo)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Streaming Settings
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
        
        # Bitrate selection
        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(QLabel("Bitrate:"))
        
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems([
            "100 Kbps", "500 Kbps", "1 Mbps", "2 Mbps", 
            "3 Mbps", "5 Mbps", "8 Mbps", "10 Mbps"
        ])
        self.bitrate_combo.setCurrentIndex(2)  # 1 Mbps default
        bitrate_layout.addWidget(self.bitrate_combo)
        
        # Quality settings
        bitrate_layout.addWidget(QLabel("Quality:"))
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast"])
        bitrate_layout.addWidget(self.quality_combo)
        
        bitrate_layout.addStretch()
        settings_layout.addLayout(bitrate_layout)
        
        # Advanced settings (collapsible)
        advanced_layout = QHBoxLayout()
        
        advanced_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(30)
        advanced_layout.addWidget(self.fps_spin)
        
        advanced_layout.addWidget(QLabel("Keyframe:"))
        self.keyframe_spin = QSpinBox()
        self.keyframe_spin.setRange(1, 10)
        self.keyframe_spin.setValue(2)
        self.keyframe_spin.setSuffix("s")
        advanced_layout.addWidget(self.keyframe_spin)
        
        advanced_layout.addWidget(QLabel("Audio:"))
        self.audio_combo = QComboBox()
        self.audio_combo.addItems(["64k", "96k", "128k", "192k"])
        self.audio_combo.setCurrentIndex(2)
        advanced_layout.addWidget(self.audio_combo)
        
        advanced_layout.addStretch()
        settings_layout.addLayout(advanced_layout)
        
        # Manual latency override
        manual_layout = QHBoxLayout()
        
        self.manual_latency_check = QCheckBox("Manual Latency:")
        self.manual_latency_check.setEnabled(False)  # Disabled when auto is on
        manual_layout.addWidget(self.manual_latency_check)
        
        self.manual_latency_spin = QSpinBox()
        self.manual_latency_spin.setRange(20, 1000)
        self.manual_latency_spin.setValue(120)
        self.manual_latency_spin.setSuffix(" ms")
        self.manual_latency_spin.setEnabled(False)
        manual_layout.addWidget(self.manual_latency_spin)
        
        manual_layout.addStretch()
        settings_layout.addLayout(manual_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶ Start Streaming")
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⬛ Stop Streaming")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
        
        # Status display
        status_group = QGroupBox("Streaming Status")
        status_layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        status_layout.addWidget(self.status_text)
        
        # Real-time stats
        stats_layout = QHBoxLayout()
        
        self.stats_labels = {
            'bitrate': QLabel("Bitrate: --"),
            'fps': QLabel("FPS: --"),
            'dropped': QLabel("Dropped: 0"),
            'viewers': QLabel("Viewers: 0")
        }
        
        for label in self.stats_labels.values():
            label.setStyleSheet("font-family: monospace;")
            stats_layout.addWidget(label)
            
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
        self.srt_manager.latency_auto_adjusted.connect(self.on_latency_adjusted)
        
        # Network monitor signals
        self.srt_manager.network_monitor.ping_updated.connect(self.network_status.update_ping)
        self.srt_manager.network_monitor.latency_updated.connect(self.network_status.update_latency)
        self.srt_manager.network_monitor.network_status_changed.connect(self.network_status.update_quality)
        
        # UI signals
        self.network_status.auto_checkbox.toggled.connect(self.on_auto_mode_changed)
        self.network_status.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        self.manual_latency_check.toggled.connect(self.on_manual_latency_toggled)
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.generate_button.clicked.connect(self.generate_stream_name)
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)
        self.refresh_ndi_button.clicked.connect(self.refresh_ndi_sources)
        
    def on_auto_mode_changed(self, checked: bool):
        """Handle auto mode toggle"""
        self.srt_manager.set_adaptive_mode(checked)
        self.manual_latency_check.setEnabled(not checked)
        self.manual_latency_spin.setEnabled(not checked and self.manual_latency_check.isChecked())
        
        if checked:
            self.append_status("✓ Automatic latency adjustment enabled")
            # Update formula display
            self.network_status.formula_label.setText("Latency = Ping × 3")
        else:
            self.append_status("✗ Automatic latency adjustment disabled")
            
    def on_preset_changed(self, preset: str):
        """Handle network preset change"""
        if preset == "Auto Detect":
            # Get recommendation
            optimal = self.controller.get_optimal_settings()
            recommended = optimal['recommended_preset']
            self.controller.apply_preset(recommended)
            self.append_status(f"Auto-detected network type: {recommended}")
        elif preset == "Local LAN":
            self.controller.apply_preset('local')
        elif preset == "Regional":
            self.controller.apply_preset('regional')
        elif preset == "Global":
            self.controller.apply_preset('global')
        elif preset == "Satellite":
            self.controller.apply_preset('satellite')
            
    def on_manual_latency_toggled(self, checked: bool):
        """Handle manual latency toggle"""
        self.manual_latency_spin.setEnabled(checked)
        if checked:
            # Disable auto mode
            self.network_status.auto_checkbox.setChecked(False)
            
    def on_latency_adjusted(self, new_latency: int, ping: float):
        """Handle automatic latency adjustment"""
        self.append_status(f"⚡ Latency auto-adjusted: {new_latency}ms (ping: {ping:.1f}ms)")
        
    def on_source_type_changed(self, source_type: str):
        """Handle source type change"""
        self.ndi_source_combo.setVisible(source_type == "NDI")
        self.refresh_ndi_button.setVisible(source_type == "NDI")
        
    def refresh_ndi_sources(self):
        """Refresh NDI source list"""
        # TODO: Integrate with NDI discovery
        self.append_status("🔍 Searching for NDI sources...")
        
    def generate_stream_name(self):
        """Generate unique stream name"""
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            stream_name = self.srt_manager.generate_stream_key(
                user_info['user_id'],
                user_info.get('unique_address', 'default')
            )
            self.stream_name_input.setText(stream_name)
            self.append_status(f"✓ Stream name generated: {stream_name}")
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Login Required", "Please login to generate stream name.")
            
    def start_streaming(self):
        """Start adaptive streaming"""
        stream_name = self.stream_name_input.text().strip()
        if not stream_name:
            self.generate_stream_name()
            stream_name = self.stream_name_input.text().strip()
            
        if not stream_name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Please enter stream name.")
            return
            
        # Build parameters
        params = {
            'bitrate': self._parse_bitrate(self.bitrate_combo.currentText()),
            'fps': self.fps_spin.value(),
            'h264_preset': self.quality_combo.currentText(),
            'h264_profile': 'main',
            'keyframe_interval': self.keyframe_spin.value(),
            'audio_bitrate': self.audio_combo.currentText()
        }
        
        # Add manual latency if specified
        if self.manual_latency_check.isChecked():
            params['srt_latency'] = self.manual_latency_spin.value()
            
        try:
            source_type = self.source_type_combo.currentText()
            
            if source_type == "NDI":
                ndi_source = self.ndi_source_combo.currentText()
                if ndi_source and ndi_source != "Select NDI Source":
                    self.srt_manager.start_ndi_streaming_adaptive(
                        ndi_source, stream_name, params)
                else:
                    raise ValueError("Please select NDI source")
                    
            elif source_type == "Screen Capture":
                self.srt_manager.start_screen_streaming_adaptive(
                    stream_name, params)
                    
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.source_type_combo.setEnabled(False)
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Streaming Failed", str(e))
            
    def stop_streaming(self):
        """Stop streaming"""
        self.srt_manager.stop_streaming()
        
        # Update UI
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_type_combo.setEnabled(True)
        
    def _parse_bitrate(self, bitrate_text: str) -> str:
        """Parse bitrate from combo box text"""
        # Extract number and unit
        parts = bitrate_text.split()
        if len(parts) >= 2:
            value = parts[0]
            unit = parts[1].lower()
            
            if unit == "kbps":
                return f"{value}k"
            elif unit == "mbps":
                return f"{value}M"
                
        return "1M"  # Default
        
    def on_stream_status_changed(self, status: str):
        """Handle stream status change"""
        self.append_status(f"📡 {status}")
        
    def on_stream_error(self, error: str):
        """Handle stream error"""
        self.append_status(f"❌ {error}")
        
    def on_stream_stats_updated(self, stats: dict):
        """Update streaming statistics"""
        if 'bitrate' in stats:
            self.stats_labels['bitrate'].setText(f"Bitrate: {stats['bitrate']}")
        if 'fps' in stats:
            self.stats_labels['fps'].setText(f"FPS: {stats['fps']}")
        if 'dropped' in stats:
            self.stats_labels['dropped'].setText(f"Dropped: {stats['dropped']}")
        if 'readers' in stats:
            self.stats_labels['viewers'].setText(f"Viewers: {stats['readers']}")
            
    def append_status(self, message: str):
        """Append status message"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_network_display(self):
        """Update network statistics display"""
        if self.srt_manager.is_streaming:
            stats = self.srt_manager.get_network_stats()
            # Additional UI updates if needed
            
    def closeEvent(self, event):
        """Cleanup on close"""
        self.srt_manager.cleanup()
        event.accept()