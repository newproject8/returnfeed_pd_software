"""
Enterprise-grade NDI Widget with non-blocking rendering
Optimized for smooth 60fps display without GUI freezing
"""

import time
import logging
from typing import Optional
from collections import deque

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QComboBox, QLabel, QGroupBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot, QSize, QRect, QPoint
from PyQt6.QtGui import QImage, QPainter, QColor, QFont, QPen

try:
    from .ndi_manager_enterprise import NDIManagerEnterprise
except ImportError:
    from ndi_manager_enterprise import NDIManagerEnterprise

logger = logging.getLogger(__name__)


class PerformanceOverlay:
    """Overlay for displaying performance metrics"""
    
    def __init__(self):
        self.fps = 0
        self.quality = "Full"
        self.dropped_frames = 0
        self.latency_ms = 0
        self.enabled = True
        
    def draw(self, painter: QPainter, width: int, height: int):
        """Draw performance overlay"""
        if not self.enabled:
            return
            
        # Setup
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(5, 5, 200, 80, QColor(0, 0, 0, 180))
        
        # Text
        painter.setPen(QPen(QColor(0, 255, 0)))
        painter.setFont(QFont("Arial", 10))
        
        y = 20
        painter.drawText(10, y, f"FPS: {self.fps:.1f}")
        y += 20
        painter.drawText(10, y, f"Quality: {self.quality}")
        y += 20
        painter.drawText(10, y, f"Dropped: {self.dropped_frames}")
        y += 20
        painter.drawText(10, y, f"Latency: {self.latency_ms:.1f}ms")
        
        painter.restore()


class NDIDisplayWidget(QWidget):
    """
    High-performance display widget with double buffering
    """
    
    def __init__(self):
        super().__init__()
        self.current_image: Optional[QImage] = None
        self.next_image: Optional[QImage] = None
        self.last_paint_time = 0
        self.paint_times = deque(maxlen=60)
        
        # Performance overlay
        self.overlay = PerformanceOverlay()
        
        # Display settings
        self.maintain_aspect_ratio = True
        self.smooth_scaling = True
        
        # Set widget properties for optimal rendering
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        
        # Minimum size
        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def set_image(self, image: QImage):
        """Set next image to display (non-blocking)"""
        self.next_image = image
        self.update()  # Schedule repaint
        
    def paintEvent(self, event):
        """Optimized paint event"""
        start_time = time.time()
        
        # Swap buffers
        if self.next_image:
            self.current_image = self.next_image
            self.next_image = None
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.smooth_scaling)
        
        # Black background
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        
        # Draw image
        if self.current_image and not self.current_image.isNull():
            # Calculate display rectangle
            if self.maintain_aspect_ratio:
                img_rect = self.current_image.rect()
                img_rect.moveCenter(self.rect().center())
                
                # Scale to fit
                scaled_size = img_rect.size().scaled(
                    self.size(), Qt.AspectRatioMode.KeepAspectRatio)
                target_rect = QRect(QPoint(0, 0), scaled_size)
                target_rect.moveCenter(self.rect().center())
            else:
                target_rect = self.rect()
                
            # Draw scaled image
            painter.drawImage(target_rect, self.current_image)
            
        # Draw overlay
        self.overlay.draw(painter, self.width(), self.height())
        
        # Track paint time
        paint_time = time.time() - start_time
        self.paint_times.append(paint_time)
        self.last_paint_time = time.time()
        
    def get_average_paint_time(self) -> float:
        """Get average paint time in milliseconds"""
        if not self.paint_times:
            return 0
        return sum(self.paint_times) / len(self.paint_times) * 1000


class NDIWidgetEnterprise(QWidget):
    """
    Enterprise-grade NDI Widget
    Production-ready with full error handling and performance monitoring
    """
    
    # Signals
    source_connected = pyqtSignal(str)
    source_disconnected = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ndi_manager: Optional[NDIManagerEnterprise] = None):
        super().__init__()
        
        # Create or use provided manager
        self.ndi_manager = ndi_manager or NDIManagerEnterprise()
        
        # Frame timing
        self.frame_times = deque(maxlen=60)
        self.last_frame_time = 0
        self.frame_skip_counter = 0
        self.target_display_fps = 30  # Display at 30fps even if source is 60fps
        
        # Statistics
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(1000)  # Update every second
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Display widget
        self.display_widget = NDIDisplayWidget()
        layout.addWidget(self.display_widget, 1)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #333; }")
        layout.addWidget(self.status_label)
        
    def _create_control_panel(self) -> QWidget:
        """Create control panel"""
        panel = QGroupBox("NDI Control")
        layout = QHBoxLayout(panel)
        
        # Source selector
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(200)
        self.source_combo.addItem("Select NDI Source...")
        layout.addWidget(QLabel("Source:"))
        layout.addWidget(self.source_combo)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_btn)
        
        # Performance settings
        layout.addWidget(QLabel("Display FPS:"))
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60", "30", "24", "15"])
        self.fps_combo.setCurrentText("30")
        self.fps_combo.currentTextChanged.connect(self._on_fps_changed)
        layout.addWidget(self.fps_combo)
        
        # Overlay toggle
        self.overlay_btn = QPushButton("Stats: ON")
        self.overlay_btn.setCheckable(True)
        self.overlay_btn.setChecked(True)
        self.overlay_btn.toggled.connect(self._on_overlay_toggled)
        layout.addWidget(self.overlay_btn)
        
        layout.addStretch()
        return panel
        
    def _connect_signals(self):
        """Connect NDI manager signals"""
        self.ndi_manager.source_list_updated.connect(self._on_sources_updated)
        self.ndi_manager.frame_received.connect(self._on_frame_received)
        self.ndi_manager.connection_state_changed.connect(self._on_connection_changed)
        self.ndi_manager.error_occurred.connect(self._on_error)
        self.ndi_manager.performance_stats.connect(self._on_performance_stats)
        
    @pyqtSlot(list)
    def _on_sources_updated(self, sources: list):
        """Update source list"""
        current_text = self.source_combo.currentText()
        
        self.source_combo.clear()
        self.source_combo.addItem("Select NDI Source...")
        self.source_combo.addItems(sources)
        
        # Restore selection if still available
        index = self.source_combo.findText(current_text)
        if index >= 0:
            self.source_combo.setCurrentIndex(index)
            
    @pyqtSlot(QImage)
    def _on_frame_received(self, image: QImage):
        """Handle received frame with smart skipping"""
        current_time = time.time()
        
        # Calculate if we should display this frame
        if self.last_frame_time > 0:
            elapsed = current_time - self.last_frame_time
            target_interval = 1.0 / self.target_display_fps
            
            if elapsed < target_interval * 0.9:  # Skip frame
                self.frame_skip_counter += 1
                return
                
        # Display frame
        self.display_widget.set_image(image)
        self.frame_times.append(current_time)
        self.last_frame_time = current_time
        self.frame_skip_counter = 0
        
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        """Handle connection state change"""
        if connected:
            self.connect_btn.setText("Disconnect")
            self.source_combo.setEnabled(False)
            self.status_label.setText("Connected")
            self.source_connected.emit(self.source_combo.currentText())
        else:
            self.connect_btn.setText("Connect")
            self.source_combo.setEnabled(True)
            self.status_label.setText("Disconnected")
            self.source_disconnected.emit()
            
    @pyqtSlot(str)
    def _on_error(self, error_msg: str):
        """Handle errors"""
        logger.error(f"NDI Error: {error_msg}")
        self.status_label.setText(f"Error: {error_msg}")
        self.error_occurred.emit(error_msg)
        
    @pyqtSlot(dict)
    def _on_performance_stats(self, stats: dict):
        """Update performance overlay"""
        overlay = self.display_widget.overlay
        overlay.fps = stats.get("fps", 0)
        overlay.quality = stats.get("quality", "Unknown")
        overlay.dropped_frames = stats.get("buffer_stats", {}).get("dropped_frames", 0)
        
        # Calculate display latency
        if self.frame_times:
            overlay.latency_ms = self.display_widget.get_average_paint_time()
            
    def _on_connect_clicked(self):
        """Handle connect button click"""
        if self.ndi_manager.connected:
            self.ndi_manager.disconnect_source()
        else:
            source = self.source_combo.currentText()
            if source and source != "Select NDI Source...":
                self.ndi_manager.connect_to_source(source)
                
    def _on_fps_changed(self, fps_text: str):
        """Handle FPS selection change"""
        try:
            self.target_display_fps = int(fps_text)
        except ValueError:
            pass
            
    def _on_overlay_toggled(self, checked: bool):
        """Toggle overlay display"""
        self.display_widget.overlay.enabled = checked
        self.overlay_btn.setText(f"Stats: {'ON' if checked else 'OFF'}")
        self.display_widget.update()
        
    def _update_statistics(self):
        """Update display statistics"""
        if len(self.frame_times) > 1:
            # Calculate actual display FPS
            time_span = self.frame_times[-1] - self.frame_times[0]
            display_fps = len(self.frame_times) / max(0.001, time_span)
            
            # Update status
            status_parts = [
                f"Display: {display_fps:.1f} FPS",
                f"Target: {self.target_display_fps} FPS"
            ]
            
            if self.ndi_manager.connected:
                status_parts.insert(0, "Connected")
                
            self.status_label.setText(" | ".join(status_parts))
            
    def closeEvent(self, event):
        """Clean shutdown"""
        self.stats_timer.stop()
        self.ndi_manager.stop()
        event.accept()
        
    def set_preview_quality(self, quality: str):
        """Set preview quality (Full, High, Medium, Low, Preview)"""
        # This would be passed to the NDI manager/worker
        pass