#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 Enterprise Edition - SIMPLE VERSION
초보자를 위한 안정적인 버전 - NDI 오류 방지
"""

import sys
import os
import logging
import json
import time
import socket
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
logger = setup_logger("enterprise_simple")

# Qt imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                            QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QLineEdit, QTextEdit, QGroupBox,
                            QScrollArea, QFrame, QGridLayout, QComboBox,
                            QStatusBar, QMessageBox)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QObject, QTimer, 
                         pyqtSlot, QCoreApplication)

# Existing components
from pd_app.ui import LoginWidget, SRTWidget
from pd_app.core import AuthManager, SRTManager
from pd_app.network import WebSocketClient

# For Tally
import requests


class SimpleNDIWidget(QWidget):
    """간단한 NDI 위젯 - 오류 없이 작동"""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Info
        info_label = QLabel("NDI 기능은 현재 사용할 수 없습니다.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: yellow; font-size: 16px; padding: 20px;")
        layout.addWidget(info_label)
        
        # Alternative
        alt_label = QLabel("대신 다음 기능들을 사용할 수 있습니다:\n\n"
                          "• Tally - vMix 상태 모니터링\n"
                          "• SRT 스트리밍 - 원격 전송\n"
                          "• 로그인 - 인증 관리")
        alt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(alt_label)
        
        layout.addStretch()


class VmixTallyManager(QObject):
    """Tally Manager - 안정적인 버전"""
    
    tally_state_changed = pyqtSignal(dict)
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
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._fetch_tally_state)
        self.update_timer.setSingleShot(True)
        
    def connect(self, ip: str = "127.0.0.1"):
        """Start Tally monitoring"""
        self.vmix_ip = ip
        
        if self.tcp_thread and self.tcp_thread.isRunning():
            self.disconnect()
            
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
        self.update_timer.stop()
        self.update_timer.start(50)
        
    @pyqtSlot(bool)
    def _on_tcp_connection_changed(self, connected: bool):
        self.connected = connected
        self.connection_state_changed.emit(connected)
        
        if connected:
            self._fetch_tally_state()
            
    def _fetch_tally_state(self):
        """Fetch Tally state via HTTP"""
        try:
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
            
            active_input = int(root.find('active').text) if root.find('active') is not None else 0
            preview_input = int(root.find('preview').text) if root.find('preview') is not None else 0
            
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
                
                if number == active_input:
                    new_states[number] = 'PGM'
                elif number == preview_input:
                    new_states[number] = 'PVW'
                else:
                    new_states[number] = 'OFF'
                    
            if new_states != self.tally_states:
                self.tally_states = new_states
                self.tally_state_changed.emit(self.tally_states)
                
            self.input_names = {inp['number']: inp['name'] for inp in inputs}
            self.input_list_updated.emit(inputs)
            
        except Exception as e:
            logger.error(f"Failed to parse vMix XML: {e}")


class TallyTCPListener(QThread):
    """TCP listener thread"""
    
    tally_changed = pyqtSignal()
    connection_changed = pyqtSignal(bool)
    
    def __init__(self, ip: str, port: int):
        super().__init__()
        self.ip = ip
        self.port = port
        self.running = False
        self.socket = None
        
    def run(self):
        self.running = True
        
        while self.running:
            try:
                self.socket = socket.create_connection((self.ip, self.port), timeout=5)
                self.socket.settimeout(1.0)
                self.connection_changed.emit(True)
                
                self.socket.sendall(b"SUBSCRIBE TALLY\r\n")
                self.tally_changed.emit()
                
                buffer = ""
                while self.running:
                    try:
                        data = self.socket.recv(1024)
                        if not data:
                            break
                            
                        buffer += data.decode('utf-8', errors='ignore')
                        
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            
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
                
            if self.running:
                self.msleep(5000)
                
    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class TallyWidget(QWidget):
    """Tally Widget"""
    
    def __init__(self, tally_manager: VmixTallyManager):
        super().__init__()
        self.tally_manager = tally_manager
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection panel
        conn_group = QGroupBox("vMix 연결")
        conn_layout = QVBoxLayout(conn_group)
        
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("vMix IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        ip_layout.addWidget(self.ip_input)
        
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        ip_layout.addWidget(self.connect_btn)
        
        conn_layout.addLayout(ip_layout)
        layout.addWidget(conn_group)
        
        # Tally display area
        self.tally_group = QGroupBox("Tally 상태")
        self.tally_layout = QGridLayout(self.tally_group)
        
        scroll = QScrollArea()
        scroll.setWidget(self.tally_group)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Status bar
        self.status_label = QLabel("연결 안됨")
        layout.addWidget(self.status_label)
        
    def _connect_signals(self):
        self.tally_manager.connection_state_changed.connect(self._on_connection_changed)
        self.tally_manager.tally_state_changed.connect(self._on_tally_changed)
        self.tally_manager.input_list_updated.connect(self._on_inputs_updated)
        self.tally_manager.error_occurred.connect(self._on_error)
        
    def _on_connect_clicked(self):
        if self.tally_manager.connected:
            self.tally_manager.disconnect()
        else:
            self.tally_manager.connect(self.ip_input.text())
            
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        if connected:
            self.connect_btn.setText("연결 해제")
            self.status_label.setText("vMix에 연결됨")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.connect_btn.setText("연결")
            self.status_label.setText("연결 안됨")
            self.status_label.setStyleSheet("color: red;")
            
    @pyqtSlot(list)
    def _on_inputs_updated(self, inputs: list):
        # Clear existing
        for i in reversed(range(self.tally_layout.count())):
            self.tally_layout.itemAt(i).widget().deleteLater()
            
        # Add inputs in grid
        for idx, inp in enumerate(inputs):
            row = idx // 4
            col = idx % 4
            
            frame = QFrame()
            frame.setFixedSize(150, 80)
            frame.setFrameStyle(QFrame.Shape.Box)
            
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(5, 5, 5, 5)
            
            num_label = QLabel(f"Input {inp['number']}")
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(num_label)
            
            name_label = QLabel(inp['name'][:20])
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(name_label)
            
            frame.setProperty("input_number", inp['number'])
            self.tally_layout.addWidget(frame, row, col)
            
    @pyqtSlot(dict)
    def _on_tally_changed(self, states: dict):
        colors = {
            'PGM': '#ff0000',  # Red
            'PVW': '#00ff00',  # Green  
            'OFF': '#333333'   # Dark gray
        }
        
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
                        font-weight: bold;
                    }}
                """)
                
    @pyqtSlot(str)
    def _on_error(self, error: str):
        self.status_label.setText(f"오류: {error}")
        self.status_label.setStyleSheet("color: red;")


class MainWindowSimple(QMainWindow):
    """간단하고 안정적인 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PD 통합 소프트웨어 - Enterprise (Simple)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Core managers
        self.auth_manager = AuthManager()
        self.tally_manager = VmixTallyManager()
        self.srt_manager = SRTManager()
        self.ws_client = WebSocketClient()
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        logger.info("Simple Enterprise Main Window initialized")
        
    def _init_ui(self):
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
        self.status_bar.showMessage("준비됨")
        
    def _create_tabs(self):
        # Login tab
        self.login_widget = LoginWidget(self.auth_manager)
        self.tab_widget.addTab(self.login_widget, "로그인")
        
        # NDI tab (placeholder)
        self.ndi_widget = SimpleNDIWidget()
        self.tab_widget.addTab(self.ndi_widget, "NDI 프리뷰")
        
        # Tally tab
        self.tally_widget = TallyWidget(self.tally_manager)
        self.tab_widget.addTab(self.tally_widget, "Tally")
        
        # SRT tab
        self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
        self.tab_widget.addTab(self.srt_widget, "SRT 스트리밍")
        
    def _connect_signals(self):
        # Auth signals
        self.auth_manager.auth_state_changed.connect(self._on_auth_changed)
        
        # WebSocket relay for Tally
        self.tally_manager.tally_state_changed.connect(self._relay_tally_state)
        
    @pyqtSlot(bool)
    def _on_auth_changed(self, authenticated: bool):
        if authenticated:
            self.status_bar.showMessage("인증됨")
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
        else:
            self.status_bar.showMessage("인증 안됨")
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
                
    @pyqtSlot(dict)
    def _relay_tally_state(self, states: dict):
        if self.ws_client.connected:
            message = {
                "type": "tally_update",
                "timestamp": time.time(),
                "data": {
                    "states": states,
                    "input_names": self.tally_manager.input_names
                }
            }
            self.ws_client.send_message(json.dumps(message))
            
    def closeEvent(self, event):
        logger.info("Shutting down Simple Enterprise application...")
        
        self.tally_manager.disconnect()
        self.ws_client.stop()
        
        event.accept()


def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("PD 통합 소프트웨어 Enterprise Edition (Simple)")
    logger.info("="*60)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PD Software Enterprise Simple")
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
        QTabBar::tab:disabled {
            background-color: #2b2b2b;
            color: #666;
        }
        QStatusBar {
            background-color: #3c3c3c;
            color: white;
        }
        QGroupBox {
            color: white;
            border: 1px solid #555;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            color: white;
            subcontrol-origin: margin;
            padding: 0 5px;
        }
        QPushButton {
            background-color: #484848;
            color: white;
            border: 1px solid #555;
            padding: 5px 15px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #555;
        }
        QLineEdit {
            background-color: #3c3c3c;
            color: white;
            border: 1px solid #555;
            padding: 5px;
        }
        QLabel {
            color: white;
        }
        QFrame {
            color: white;
        }
    """)
    
    # Create and show main window
    try:
        window = MainWindowSimple()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "시작 오류",
            f"애플리케이션을 시작할 수 없습니다:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == '__main__':
    main()