#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed NDI Widget Enterprise - Optimized for performance
Based on stable implementation patterns
"""

import logging
import numpy as np
from typing import Optional

# Qt imports
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QGroupBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QSize, QTimer
from PyQt6.QtGui import QImage, QPainter, QPixmap, QPaintEvent

# Setup logger
from pd_app.utils import setup_logger
logger = setup_logger("ndi_widget_fixed")


class NDIDisplayWidget(QWidget):
    """
    Optimized NDI display widget
    - No frame buffering
    - Direct painting
    - Automatic frame dropping via update coalescing
    """
    
    def __init__(self):
        super().__init__()
        self.current_frame = None
        self.pixmap = None
        
        # Display settings
        self.setMinimumSize(640, 360)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable optimizations
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # Frame rate limiter - prevent excessive updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.setSingleShot(True)
        self.update_pending = False
        
    def set_image(self, frame: np.ndarray):
        """Set new frame for display"""
        try:
            if frame is None or frame.size == 0:
                return
                
            # Store frame reference (no copy)
            self.current_frame = frame
            
            # Convert to QImage
            height, width = frame.shape[:2]
            bytes_per_line = width * 3
            
            # Create QImage without copying data
            qimage = QImage(
                frame.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            
            # Convert to pixmap for faster painting
            self.pixmap = QPixmap.fromImage(qimage)
            
            # Schedule update with rate limiting
            if not self.update_pending:
                self.update_pending = True
                self.update_timer.start(16)  # ~60fps max
                
        except Exception as e:
            logger.error(f"Failed to set image: {e}")
            
    def paintEvent(self, event: QPaintEvent):
        """Optimized paint event"""
        self.update_pending = False
        
        painter = QPainter(self)
        
        # Black background
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        
        # Draw frame if available
        if self.pixmap and not self.pixmap.isNull():
            # Calculate scaled size maintaining aspect ratio
            scaled_size = self.pixmap.size().scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the image
            x = (self.width() - scaled_size.width()) // 2
            y = (self.height() - scaled_size.height()) // 2
            
            # Draw scaled pixmap
            painter.drawPixmap(x, y, scaled_size.width(), scaled_size.height(), self.pixmap)
            
    def clear(self):
        """Clear the display"""
        self.current_frame = None
        self.pixmap = None
        self.update()
        
    def sizeHint(self) -> QSize:
        """Preferred size"""
        return QSize(1280, 720)


class NDIWidgetEnterprise(QWidget):
    """
    Fixed NDI Widget - Simple, stable UI
    Based on proven patterns
    """
    
    def __init__(self, ndi_manager):
        super().__init__()
        self.ndi_manager = ndi_manager
        self._init_ui()
        self._connect_signals()
        
        # Statistics update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics_display)
        self.stats_timer.start(1000)  # Update every second
        
        self.current_stats = {}
        
    def _init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Control panel
        control_group = QGroupBox("NDI Control")
        control_layout = QVBoxLayout(control_group)
        
        # Source selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(300)
        source_layout.addWidget(self.source_combo, 1)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        source_layout.addWidget(self.refresh_btn)
        
        control_layout.addLayout(source_layout)
        
        # Connect/Disconnect buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_btn)
        
        control_layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Status: Disconnected")
        control_layout.addWidget(self.status_label)
        
        # Statistics
        self.stats_label = QLabel("FPS: 0.0 | Frames: 0 | Dropped: 0 (0.0%)")
        control_layout.addWidget(self.stats_label)
        
        layout.addWidget(control_group)
        
        # Display area
        display_group = QGroupBox("NDI Preview")
        display_layout = QVBoxLayout(display_group)
        
        self.display_widget = NDIDisplayWidget()
        display_layout.addWidget(self.display_widget)
        
        layout.addWidget(display_group, 1)
        
    def _connect_signals(self):
        """Connect signals"""
        # NDI manager signals
        self.ndi_manager.frame_ready.connect(self._on_frame_received)
        self.ndi_manager.connection_changed.connect(self._on_connection_changed)
        self.ndi_manager.sources_updated.connect(self._on_sources_updated)
        self.ndi_manager.error_occurred.connect(self._on_error)
        self.ndi_manager.statistics_updated.connect(self._on_statistics_updated)
        
    @pyqtSlot()
    def _on_refresh_clicked(self):
        """Handle refresh button"""
        self.refresh_btn.setEnabled(False)
        self.ndi_manager.refresh_sources()
        
        # Re-enable after 1 second
        QTimer.singleShot(1000, lambda: self.refresh_btn.setEnabled(True))
        
    @pyqtSlot()
    def _on_connect_clicked(self):
        """Handle connect button"""
        source_name = self.source_combo.currentText()
        if source_name:
            self.status_label.setText("Status: Connecting...")
            self.ndi_manager.connect_to_source(source_name)
            
    @pyqtSlot()
    def _on_disconnect_clicked(self):
        """Handle disconnect button"""
        self.ndi_manager.disconnect()
        
    @pyqtSlot(np.ndarray)
    def _on_frame_received(self, frame: np.ndarray):
        """Handle received frame"""
        # Direct display - no buffering
        self.display_widget.set_image(frame)
        
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        """Handle connection state change"""
        if connected:
            self.status_label.setText("Status: Connected")
            self.status_label.setStyleSheet("color: green;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.source_combo.setEnabled(False)
        else:
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet("color: red;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.source_combo.setEnabled(True)
            self.display_widget.clear()
            
    @pyqtSlot(list)
    def _on_sources_updated(self, sources: list):
        """Handle source list update"""
        current_source = self.source_combo.currentText()
        
        self.source_combo.clear()
        self.source_combo.addItems(sources)
        
        # Restore selection if possible
        if current_source in sources:
            self.source_combo.setCurrentText(current_source)
            
        # Update status
        if sources:
            self.status_label.setText(f"Status: {len(sources)} sources found")
        else:
            self.status_label.setText("Status: No sources found")
            
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """Handle error"""
        self.status_label.setText(f"Error: {error}")
        self.status_label.setStyleSheet("color: red;")
        logger.error(f"NDI Error: {error}")
        
    @pyqtSlot(dict)
    def _on_statistics_updated(self, stats: dict):
        """Update statistics"""
        self.current_stats = stats
        
    def _update_statistics_display(self):
        """Update statistics display"""
        if self.current_stats:
            fps = self.current_stats.get('actual_fps', 0)
            frames = self.current_stats.get('frames_displayed', 0)
            dropped = self.current_stats.get('frames_dropped', 0)
            drop_rate = self.current_stats.get('drop_rate', 0)
            
            self.stats_label.setText(
                f"FPS: {fps:.1f} | Frames: {frames} | Dropped: {dropped} ({drop_rate:.1f}%)"
            )
            
    def closeEvent(self, event):
        """Clean up on close"""
        self.stats_timer.stop()
        if hasattr(self.ndi_manager, 'disconnect'):
            self.ndi_manager.disconnect()
        event.accept()