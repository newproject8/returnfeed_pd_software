#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 Enterprise Edition - FIXED VERSION
High-performance, zero GUI freezing, stable NDI display
Based on proven patterns from stable implementations
"""

import sys
import os
import logging
import json
import time
import socket
import threading
from typing import Optional, Dict, Any
import xml.etree.ElementTree as ET

# Platform setup
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.system('chcp 65001 > nul')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Logging setup
from pd_app.utils import setup_logger
logger = setup_logger("enterprise_fixed")

# Qt imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                            QWidget, QVBoxLayout, QStatusBar, QLabel)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QObject, QTimer, 
                         pyqtSlot, QCoreApplication)

# Fixed enterprise components
try:
    from enterprise.ndi_widget_enterprise_fixed import NDIWidgetEnterprise
    from enterprise.ndi_manager_enterprise_fixed import NDIManagerEnterprise
except ImportError:
    # Direct import
    import sys
    import os
    enterprise_path = os.path.join(os.path.dirname(__file__))
    if enterprise_path not in sys.path:
        sys.path.insert(0, enterprise_path)
    from ndi_widget_enterprise_fixed import NDIWidgetEnterprise
    from ndi_manager_enterprise_fixed import NDIManagerEnterprise

# Existing components
from pd_app.ui import LoginWidget, SRTWidget
from pd_app.core import AuthManager, SRTManager
from pd_app.network import WebSocketClient

# For Tally
import requests


class VmixTallyManager(QObject):
    """
    Enterprise Tally Manager using validated hybrid pattern from vMix_tcp_tally2.py
    TCP for instant detection + HTTP API for accurate state
    """
    
    # Signals
    tally_state_changed = pyqtSignal(dict)  # {input_number: state}
    connection_state_changed = pyqtSignal(bool)
    input_list_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.vmix_ip = "127.0.0.1"
        self.vmix_tcp_port = 8099
        self.vmix_http_port = 8088
        
        self.tcp_thread = None
        self.connected = False
        self.input_names = {}
        self.tally_states = {}
        
        # Debounce timer for HTTP requests
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._fetch_tally_state)
        self.update_timer.setSingleShot(True)
        
    def connect(self, ip: str = "127.0.0.1"):
        """Start Tally monitoring"""
        self.vmix_ip = ip
        
        if self.tcp_thread and self.tcp_thread.isRunning():
            self.disconnect()
            
        # Start TCP listener
        self.tcp_thread = TallyTCPListener(self.vmix_ip, self.vmix_tcp_port)
        self.tcp_thread.tally_changed.connect(self._on_tcp_tally_changed)
        self.tcp_thread.connection_changed.connect(self._on_tcp_connection_changed)
        self.tcp_thread.start()
        
    def disconnect(self):
        """Stop Tally monitoring"""
        if self.tcp_thread:
            self.tcp_thread.stop()
            self.tcp_thread.wait(2000)
            self.tcp_thread = None
            
        self.connected = False
        self.connection_state_changed.emit(False)
        
    @pyqtSlot()
    def _on_tcp_tally_changed(self):
        """TCP detected a change - fetch accurate state via HTTP"""
        # Debounce HTTP requests (wait 50ms for rapid changes)
        self.update_timer.stop()
        self.update_timer.start(50)
        
    @pyqtSlot(bool)
    def _on_tcp_connection_changed(self, connected: bool):
        """Handle TCP connection state change"""
        self.connected = connected
        self.connection_state_changed.emit(connected)
        
        if connected:
            # Fetch initial state
            self._fetch_tally_state()
            
    def _fetch_tally_state(self):
        """Fetch accurate Tally state via HTTP API"""
        try:
            # Get XML status from vMix
            url = f"http://{self.vmix_ip}:{self.vmix_http_port}/API/"
            response = requests.get(url, timeout=1.0)
            
            if response.status_code == 200:
                self._parse_vmix_state(response.text)
                
        except Exception as e:
            logger.error(f"Failed to fetch vMix state: {e}")
            self.error_occurred.emit(str(e))
            
    def _parse_vmix_state(self, xml_data: str):
        """Parse vMix XML state"""
        try:
            root = ET.fromstring(xml_data)
            
            # Get active/preview inputs
            active_input = int(root.find('active').text) if root.find('active') is not None else 0
            preview_input = int(root.find('preview').text) if root.find('preview') is not None else 0
            
            # Parse input list
            inputs = []
            new_states = {}
            
            for input_elem in root.findall('.//input'):
                number = int(input_elem.get('number', 0))
                name = input_elem.get('title', f"Input {number}")
                
                inputs.append({
                    'number': number,
                    'name': name,
                    'type': input_elem.get('type', 'Unknown')
                })
                
                # Determine state
                if number == active_input:
                    new_states[number] = 'PGM'
                elif number == preview_input:
                    new_states[number] = 'PVW'
                else:
                    new_states[number] = 'OFF'
                    
            # Update states
            if new_states != self.tally_states:
                self.tally_states = new_states
                self.tally_state_changed.emit(self.tally_states)
                
            # Update input list
            self.input_names = {inp['number']: inp['name'] for inp in inputs}
            self.input_list_updated.emit(inputs)
            
        except Exception as e:
            logger.error(f"Failed to parse vMix XML: {e}")


class TallyTCPListener(QThread):
    """TCP listener thread for instant Tally change detection"""
    
    tally_changed = pyqtSignal()
    connection_changed = pyqtSignal(bool)
    
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.ip = ip
        self.port = port
        self.running = False
        self.socket = None
        
    def run(self):
        """Main TCP listening loop"""
        self.running = True
        
        while self.running:
            try:
                # Connect to vMix
                self.socket = socket.create_connection((self.ip, self.port), timeout=5)
                self.socket.settimeout(1.0)
                self.connection_changed.emit(True)
                
                # Subscribe to Tally
                self.socket.sendall(b"SUBSCRIBE TALLY\r\n")
                
                # Signal initial state fetch
                self.tally_changed.emit()
                
                # Listen for changes
                buffer = ""
                while self.running:
                    try:
                        data = self.socket.recv(1024)
                        if not data:
                            break
                            
                        buffer += data.decode('utf-8', errors='ignore')
                        
                        # Process complete lines
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            
                            # Any TALLY OK means something changed
                            if line.startswith('TALLY OK'):
                                self.tally_changed.emit()
                                
                    except socket.timeout:
                        continue
                    except socket.error:
                        break
                        
            except Exception as e:
                logger.error(f"TCP listener error: {e}")
                
            finally:
                if self.socket:
                    self.socket.close()
                    self.socket = None
                    
                self.connection_changed.emit(False)
                
            # Reconnect delay
            if self.running:
                self.msleep(5000)
                
    def stop(self):
        """Stop the listener"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class TallyWidget(QWidget):
    """Enterprise Tally Widget with real-time display"""
    
    def __init__(self, tally_manager: VmixTallyManager):
        super().__init__()
        self.tally_manager = tally_manager
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Initialize UI"""
        from PyQt6.QtWidgets import (QGroupBox, QGridLayout, QPushButton, 
                                    QLineEdit, QScrollArea, QHBoxLayout, QFrame,
                                    QVBoxLayout, QLabel)
        
        layout = QVBoxLayout(self)
        
        # Connection panel
        conn_group = QGroupBox("vMix Connection")
        conn_layout = QVBoxLayout(conn_group)
        
        # IP input
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("vMix IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        ip_layout.addWidget(self.ip_input)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        ip_layout.addWidget(self.connect_btn)
        
        conn_layout.addLayout(ip_layout)
        layout.addWidget(conn_group)
        
        # Tally display area
        self.tally_group = QGroupBox("Tally Status")
        self.tally_layout = QGridLayout(self.tally_group)
        
        scroll = QScrollArea()
        scroll.setWidget(self.tally_group)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Status bar
        self.status_label = QLabel("Disconnected")
        layout.addWidget(self.status_label)
        
    def _connect_signals(self):
        """Connect signals"""
        self.tally_manager.connection_state_changed.connect(self._on_connection_changed)
        self.tally_manager.tally_state_changed.connect(self._on_tally_changed)
        self.tally_manager.input_list_updated.connect(self._on_inputs_updated)
        
    def _on_connect_clicked(self):
        """Handle connect button"""
        if self.tally_manager.connected:
            self.tally_manager.disconnect()
        else:
            self.tally_manager.connect(self.ip_input.text())
            
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        """Update UI on connection change"""
        if connected:
            self.connect_btn.setText("Disconnect")
            self.status_label.setText("Connected to vMix")
        else:
            self.connect_btn.setText("Connect")
            self.status_label.setText("Disconnected")
            
    @pyqtSlot(list)
    def _on_inputs_updated(self, inputs: list):
        """Update input display"""
        # Clear existing
        for i in reversed(range(self.tally_layout.count())):
            self.tally_layout.itemAt(i).widget().deleteLater()
            
        # Add inputs in grid
        for idx, inp in enumerate(inputs):
            row = idx // 4
            col = idx % 4
            
            # Create Tally indicator
            from PyQt6.QtWidgets import QFrame
            
            frame = QFrame()
            frame.setFixedSize(150, 80)
            frame.setFrameStyle(QFrame.Shape.Box)
            
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Input number
            num_label = QLabel(f"Input {inp['number']}")
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(num_label)
            
            # Input name
            name_label = QLabel(inp['name'][:20])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(name_label)
            
            # Store reference
            frame.setProperty("input_number", inp['number'])
            self.tally_layout.addWidget(frame, row, col)
            
    @pyqtSlot(dict)
    def _on_tally_changed(self, states: dict):
        """Update Tally colors"""
        # Color map
        colors = {
            'PGM': '#aa0000',  # Red
            'PVW': '#00aa00',  # Green  
            'OFF': '#333333'   # Dark gray
        }
        
        # Update all frames
        for i in range(self.tally_layout.count()):
            frame = self.tally_layout.itemAt(i).widget()
            if frame:
                input_num = frame.property("input_number")
                state = states.get(input_num, 'OFF')
                color = colors.get(state, '#333333')
                
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {color};
                        border: 2px solid #555;
                        border-radius: 5px;
                    }}
                    QLabel {{
                        color: white;
                    }}
                """)


class MainWindowEnterprise(QMainWindow):
    """
    Fixed Enterprise Main Window
    Non-blocking, high-performance, production-ready
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PD 통합 소프트웨어 - Enterprise Edition (Fixed)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Core managers
        self.auth_manager = AuthManager()
        self.ndi_manager = NDIManagerEnterprise()
        self.tally_manager = VmixTallyManager()
        self.srt_manager = SRTManager()
        self.ws_client = WebSocketClient()
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Start services
        self._start_services()
        
        logger.info("Fixed Enterprise Main Window initialized")
        
    def _init_ui(self):
        """Initialize user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_tabs()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def _create_tabs(self):
        """Create application tabs"""
        # Login tab
        self.login_widget = LoginWidget(self.auth_manager)
        self.tab_widget.addTab(self.login_widget, "로그인")
        
        # NDI tab
        self.ndi_widget = NDIWidgetEnterprise(self.ndi_manager)
        self.tab_widget.addTab(self.ndi_widget, "NDI 프리뷰")
        
        # Tally tab
        self.tally_widget = TallyWidget(self.tally_manager)
        self.tab_widget.addTab(self.tally_widget, "Tally")
        
        # SRT tab
        self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
        self.tab_widget.addTab(self.srt_widget, "SRT 스트리밍")
        
    def _connect_signals(self):
        """Connect signals between components"""
        # Auth signals
        self.auth_manager.auth_state_changed.connect(self._on_auth_changed)
        
        # WebSocket relay for Tally
        self.tally_manager.tally_state_changed.connect(self._relay_tally_state)
        
        # Tab change optimization
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
    def _start_services(self):
        """Start background services"""
        # WebSocket client
        if hasattr(self.auth_manager, 'unique_address'):
            self.ws_client.set_unique_address(self.auth_manager.unique_address)
            
    @pyqtSlot(bool)
    def _on_auth_changed(self, authenticated: bool):
        """Handle authentication state change"""
        if authenticated:
            self.status_bar.showMessage("Authenticated")
            # Enable tabs
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
        else:
            self.status_bar.showMessage("Not authenticated")
            # Disable tabs except login
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
                
    @pyqtSlot(dict)
    def _relay_tally_state(self, states: dict):
        """Relay Tally state to WebSocket server"""
        if self.ws_client.connected:
            # Format message
            message = {
                "type": "tally_update",
                "timestamp": time.time(),
                "data": {
                    "states": states,
                    "input_names": self.tally_manager.input_names
                }
            }
            
            # Send via WebSocket
            self.ws_client.send_message(json.dumps(message))
            
    @pyqtSlot(int)
    def _on_tab_changed(self, index: int):
        """Handle tab change - optimize resource usage"""
        # Pause NDI if not visible
        if index != 1 and self.ndi_manager.connected:
            # Could implement pause logic here
            pass
            
    def closeEvent(self, event):
        """Clean shutdown"""
        logger.info("Shutting down Fixed Enterprise application...")
        
        # Stop all services
        self.ndi_manager.stop()
        self.tally_manager.disconnect()
        self.ws_client.stop()
        
        # Save settings
        if hasattr(self, 'saveGeometry'):
            # Could save geometry here
            pass
            
        event.accept()


def optimize_application():
    """Apply application-level optimizations"""
    # High DPI - PyQt6에서는 기본 활성화됨
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass  # PyQt6에서는 필요없음
    
    # Application attributes - PyQt6 호환
    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    except AttributeError:
        pass  # 이 속성이 없으면 건너뛰기
    
    # Process priority (Windows)
    if sys.platform == "win32":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(handle, 0x80)  # HIGH_PRIORITY_CLASS
            logger.info("Set process priority to HIGH")
        except:
            pass


def main():
    """Main entry point"""
    logger.info("="*80)
    logger.info("PD 통합 소프트웨어 Enterprise Edition (FIXED)")
    logger.info("="*80)
    
    # Apply optimizations
    optimize_application()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PD Software Enterprise Fixed")
    app.setOrganizationName("ReturnFeed")
    app.setStyle('Fusion')
    
    # Apply dark theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
        }
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #2b2b2b;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            color: white;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #484848;
        }
        QStatusBar {
            background-color: #3c3c3c;
            color: white;
        }
    """)
    
    # Create and show main window
    try:
        window = MainWindowEnterprise()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()