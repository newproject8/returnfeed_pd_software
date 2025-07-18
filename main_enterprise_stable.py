#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 Enterprise Edition - STABLE VERSION
main.py의 검증된 패턴을 사용한 안정적인 엔터프라이즈 버전
"""

import sys
import os
import logging

# Platform setup
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.system('chcp 65001 > nul')
    
    # NDI SDK 경로 추가 (main.py와 동일)
    ndi_sdk_paths = [
        "C:\\Program Files\\NDI\\NDI 6 SDK\\Bin\\x64",
        "C:\\Program Files\\NDI\\NDI 5 SDK\\Bin\\x64"
    ]
    for path in ndi_sdk_paths:
        if os.path.exists(path):
            try:
                os.add_dll_directory(path)
                print(f"Added to DLL search path: {path}")
                break
            except:
                pass

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("enterprise_stable")

# Qt imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                            QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QGroupBox, QStatusBar,
                            QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot

# PD App imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pd_app.ui import LoginWidget, SRTWidget
from pd_app.core import AuthManager, SRTManager, NDIProcessManager
from pd_app.network import WebSocketClient
from pd_app.ui import VideoDisplayWidget

# NDI 초기화 (main.py와 동일한 방식)
try:
    import ndi
    if ndi.initialize():
        logger.info("NDI initialized successfully")
    else:
        logger.error("Failed to initialize NDI")
        ndi = None
except Exception as e:
    logger.error(f"NDI import failed: {e}")
    ndi = None

# Tally imports
from enterprise.main_enterprise import VmixTallyManager, TallyWidget


class MainWindowStable(QMainWindow):
    """
    안정적인 Enterprise 메인 윈도우
    main.py의 검증된 구조 사용
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PD 통합 소프트웨어 - Enterprise (Stable)")
        self.resize(1200, 800)
        
        # NDI sources cache (main.py 방식)
        self.ndi_sources_cache = {}
        
        # Core managers
        self.auth_manager = AuthManager()
        self.ndi_manager = NDIProcessManager()  # main.py와 동일한 매니저 사용
        self.tally_manager = VmixTallyManager()
        self.srt_manager = SRTManager()
        self.ws_client = WebSocketClient()
        
        # Initialize UI
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Start NDI manager (main.py 방식)
        QTimer.singleShot(100, self.ndi_manager.start)
        
        logger.info("Stable Enterprise Main Window initialized")
        
    def _init_ui(self):
        """Initialize user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
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
        """Create application tabs"""
        # Login tab
        self.login_widget = LoginWidget(self.auth_manager)
        self.tab_widget.addTab(self.login_widget, "로그인")
        
        # NDI tab (main.py 방식)
        self.ndi_tab = self._create_ndi_tab()
        self.tab_widget.addTab(self.ndi_tab, "NDI 프리뷰")
        
        # Tally tab
        self.tally_widget = TallyWidget(self.tally_manager)
        self.tab_widget.addTab(self.tally_widget, "Tally")
        
        # SRT tab
        self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
        self.tab_widget.addTab(self.srt_widget, "SRT 스트리밍")
        
    def _create_ndi_tab(self):
        """Create NDI tab (main.py 방식)"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Control group
        control_group = QGroupBox("NDI 제어")
        control_layout = QVBoxLayout()
        
        # Source selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("NDI 소스:"))
        
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(300)
        source_layout.addWidget(self.source_combo, 1)
        
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self._on_refresh_sources)
        source_layout.addWidget(self.refresh_btn)
        
        control_layout.addLayout(source_layout)
        
        # Connect button
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("연결")
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        button_layout.addWidget(self.connect_btn)
        
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Video display (main.py의 VideoDisplayWidget 사용)
        self.video_widget = VideoDisplayWidget()
        layout.addWidget(self.video_widget, 1)
        
        return tab
        
    def _connect_signals(self):
        """Connect signals between components"""
        # Auth signals
        self.auth_manager.auth_state_changed.connect(self._on_auth_changed)
        
        # NDI signals (main.py 방식)
        self.ndi_manager.update_ndi_sources_gui.connect(self._update_ndi_sources_gui)
        self.ndi_manager.receiver_connected_gui.connect(self._on_receiver_connected)
        self.ndi_manager.receiver_disconnected_gui.connect(self._on_receiver_disconnected)
        self.ndi_manager.ndi_video_frame_received_gui.connect(
            self.video_widget.update_frame
        )
        
        # Tally signals
        self.tally_manager.tally_state_changed.connect(self._relay_tally_state)
        
    @pyqtSlot(list)
    def _update_ndi_sources_gui(self, sources):
        """Update NDI sources (main.py 방식)"""
        logger.debug(f"Updating NDI sources: {len(sources)} found")
        
        # Update cache
        self.ndi_sources_cache.clear()
        for source in sources:
            if isinstance(source, dict) and 'name' in source:
                self.ndi_sources_cache[source['name']] = source
        
        # Update combo box
        current_text = self.source_combo.currentText()
        self.source_combo.clear()
        self.source_combo.addItems(list(self.ndi_sources_cache.keys()))
        
        # Restore selection or auto-connect
        if current_text in self.ndi_sources_cache:
            self.source_combo.setCurrentText(current_text)
        elif self.source_combo.count() > 0 and not self.ndi_manager.receiver_connected:
            # Auto-connect to first source
            self.source_combo.setCurrentIndex(0)
            QTimer.singleShot(500, self._on_connect_clicked)
            
    def _on_refresh_sources(self):
        """Refresh NDI sources"""
        self.refresh_btn.setEnabled(False)
        QTimer.singleShot(1000, lambda: self.refresh_btn.setEnabled(True))
        # NDI manager automatically discovers sources
        
    def _on_connect_clicked(self):
        """Connect to selected NDI source"""
        if self.ndi_manager.receiver_connected:
            self.ndi_manager.disconnect_current_source()
        else:
            source_name = self.source_combo.currentText()
            if source_name and source_name in self.ndi_sources_cache:
                source_info = self.ndi_sources_cache[source_name]
                self.ndi_manager.connect_to_source(source_info)
                
    @pyqtSlot()
    def _on_receiver_connected(self):
        """Handle receiver connected"""
        self.connect_btn.setText("연결 해제")
        self.status_bar.showMessage("NDI 연결됨")
        
    @pyqtSlot()
    def _on_receiver_disconnected(self):
        """Handle receiver disconnected"""
        self.connect_btn.setText("연결")
        self.status_bar.showMessage("NDI 연결 해제됨")
        
    @pyqtSlot(bool)
    def _on_auth_changed(self, authenticated: bool):
        """Handle authentication state change"""
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
        """Relay Tally state to WebSocket server"""
        if self.ws_client.connected:
            import json
            import time
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
        """Clean shutdown"""
        logger.info("Shutting down Stable Enterprise application...")
        
        # Stop all services
        self.ndi_manager.stop()
        self.tally_manager.disconnect()
        self.ws_client.stop()
        
        # Destroy NDI
        if ndi:
            try:
                ndi.destroy()
            except:
                pass
                
        event.accept()


def main():
    """Main entry point"""
    logger.info("="*60)
    logger.info("PD 통합 소프트웨어 Enterprise Edition (Stable)")
    logger.info("="*60)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PD Software Enterprise Stable")
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
        QGroupBox {
            color: white;
            border: 1px solid #555;
            margin-top: 5px;
        }
        QGroupBox::title {
            color: white;
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
        QPushButton:pressed {
            background-color: #333;
        }
        QComboBox {
            background-color: #484848;
            color: white;
            border: 1px solid #555;
            padding: 5px;
        }
        QLabel {
            color: white;
        }
    """)
    
    # Check NDI
    if not ndi:
        QMessageBox.warning(
            None,
            "NDI 경고",
            "NDI가 초기화되지 않았습니다.\nNDI 기능이 제한될 수 있습니다."
        )
    
    # Create and show main window
    try:
        window = MainWindowStable()
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