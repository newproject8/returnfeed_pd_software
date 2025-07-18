#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 Enterprise Edition - DIAGNOSTIC VERSION
상세한 로그를 통해 성능 문제 진단
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
import traceback
from datetime import datetime

# Performance profiling
import cProfile
import pstats
from io import StringIO

# Platform setup
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    os.system('chcp 65001 > nul')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enhanced logging setup
class TimedLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler with detailed format
        log_file = f"diagnostic_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Detailed formatter
        formatter = logging.Formatter(
            '%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
            datefmt='%H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
    def time_function(self, func_name):
        """Decorator to time function execution"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                self.logger.debug(f"[TIMING] {func_name} started")
                try:
                    result = func(*args, **kwargs)
                    elapsed = (time.perf_counter() - start) * 1000
                    self.logger.info(f"[TIMING] {func_name} completed in {elapsed:.2f}ms")
                    return result
                except Exception as e:
                    elapsed = (time.perf_counter() - start) * 1000
                    self.logger.error(f"[TIMING] {func_name} failed after {elapsed:.2f}ms: {e}")
                    self.logger.error(traceback.format_exc())
                    raise
            return wrapper
        return decorator

logger = TimedLogger("enterprise_diagnostic")

# Qt imports with timing
start_import = time.perf_counter()
logger.logger.info("[IMPORT] Starting Qt imports...")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                            QWidget, QVBoxLayout, QStatusBar, QLabel)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QObject, QTimer, 
                         pyqtSlot, QCoreApplication)

logger.logger.info(f"[IMPORT] Qt imports completed in {(time.perf_counter() - start_import)*1000:.2f}ms")

# Import diagnostics
def import_with_timing(module_name, import_func):
    start = time.perf_counter()
    try:
        result = import_func()
        elapsed = (time.perf_counter() - start) * 1000
        logger.logger.info(f"[IMPORT] {module_name} imported in {elapsed:.2f}ms")
        return result
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.logger.error(f"[IMPORT] {module_name} failed after {elapsed:.2f}ms: {e}")
        raise

# Fixed enterprise components with timing
try:
    ndi_widget = import_with_timing("NDIWidgetEnterprise", 
        lambda: __import__('enterprise.ndi_widget_enterprise_fixed', fromlist=['NDIWidgetEnterprise']))
    NDIWidgetEnterprise = ndi_widget.NDIWidgetEnterprise
    
    ndi_manager = import_with_timing("NDIManagerEnterprise",
        lambda: __import__('enterprise.ndi_manager_enterprise_fixed', fromlist=['NDIManagerEnterprise']))
    NDIManagerEnterprise = ndi_manager.NDIManagerEnterprise
except ImportError:
    logger.logger.warning("[IMPORT] Failed to import fixed versions, trying direct import")
    import sys
    import os
    enterprise_path = os.path.join(os.path.dirname(__file__))
    if enterprise_path not in sys.path:
        sys.path.insert(0, enterprise_path)
    from ndi_widget_enterprise_fixed import NDIWidgetEnterprise
    from ndi_manager_enterprise_fixed import NDIManagerEnterprise

# Existing components with timing
login_widget = import_with_timing("LoginWidget",
    lambda: __import__('pd_app.ui', fromlist=['LoginWidget']))
srt_widget = import_with_timing("SRTWidget", 
    lambda: __import__('pd_app.ui', fromlist=['SRTWidget']))
auth_manager = import_with_timing("AuthManager",
    lambda: __import__('pd_app.core', fromlist=['AuthManager']))
srt_manager = import_with_timing("SRTManager",
    lambda: __import__('pd_app.core', fromlist=['SRTManager']))
ws_client = import_with_timing("WebSocketClient",
    lambda: __import__('pd_app.network', fromlist=['WebSocketClient']))

from pd_app.ui import LoginWidget, SRTWidget
from pd_app.core import AuthManager, SRTManager
from pd_app.network import WebSocketClient

# For Tally
import requests


class PerformanceMonitor(QObject):
    """Monitor GUI performance and log issues"""
    
    performance_report = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.frame_times = []
        self.last_frame_time = time.perf_counter()
        self.freeze_threshold = 0.1  # 100ms = freeze
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_performance)
        self.monitor_timer.start(100)  # Check every 100ms
        
    def frame_rendered(self):
        """Call when a frame is rendered"""
        current_time = time.perf_counter()
        frame_time = current_time - self.last_frame_time
        self.frame_times.append(frame_time)
        
        if frame_time > self.freeze_threshold:
            logger.logger.warning(f"[PERFORMANCE] GUI freeze detected: {frame_time*1000:.2f}ms")
            
        self.last_frame_time = current_time
        
        # Keep only last 100 frames
        if len(self.frame_times) > 100:
            self.frame_times.pop(0)
            
    def check_performance(self):
        """Periodic performance check"""
        if not self.frame_times:
            return
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        max_frame_time = max(self.frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        report = {
            'avg_frame_time_ms': avg_frame_time * 1000,
            'max_frame_time_ms': max_frame_time * 1000,
            'fps': fps,
            'freeze_count': sum(1 for t in self.frame_times if t > self.freeze_threshold)
        }
        
        if report['freeze_count'] > 0:
            logger.logger.warning(f"[PERFORMANCE] {report['freeze_count']} freezes in last {len(self.frame_times)} frames")
            
        self.performance_report.emit(report)


class VmixTallyManager(QObject):
    """Tally Manager with diagnostic logging"""
    
    tally_state_changed = pyqtSignal(dict)
    connection_state_changed = pyqtSignal(bool)
    input_list_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        logger.logger.info("[TALLY] Initializing VmixTallyManager")
        self.vmix_ip = "127.0.0.1"
        self.vmix_tcp_port = 8099
        self.vmix_http_port = 8088
        
        self.tcp_thread = None
        self.connected = False
        self.input_names = {}
        self.tally_states = {}
        
        # Debounce timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._fetch_tally_state)
        self.update_timer.setSingleShot(True)
        
    @logger.time_function("tally_connect")
    def connect(self, ip: str = "127.0.0.1"):
        """Start Tally monitoring"""
        logger.logger.info(f"[TALLY] Connecting to {ip}")
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
        logger.logger.info("[TALLY] Disconnecting")
        if self.tcp_thread:
            self.tcp_thread.stop()
            self.tcp_thread.wait(2000)
            self.tcp_thread = None
            
        self.connected = False
        self.connection_state_changed.emit(False)
        
    @pyqtSlot()
    def _on_tcp_tally_changed(self):
        """TCP detected a change"""
        logger.logger.debug("[TALLY] TCP change detected, scheduling HTTP fetch")
        self.update_timer.stop()
        self.update_timer.start(50)
        
    @pyqtSlot(bool)
    def _on_tcp_connection_changed(self, connected: bool):
        """Handle TCP connection state change"""
        logger.logger.info(f"[TALLY] TCP connection changed: {connected}")
        self.connected = connected
        self.connection_state_changed.emit(connected)
        
        if connected:
            self._fetch_tally_state()
            
    @logger.time_function("fetch_tally_state")
    def _fetch_tally_state(self):
        """Fetch accurate Tally state via HTTP API"""
        try:
            url = f"http://{self.vmix_ip}:{self.vmix_http_port}/API/"
            logger.logger.debug(f"[TALLY] Fetching state from {url}")
            
            start = time.perf_counter()
            response = requests.get(url, timeout=1.0)
            elapsed = (time.perf_counter() - start) * 1000
            
            logger.logger.debug(f"[TALLY] HTTP request completed in {elapsed:.2f}ms")
            
            if response.status_code == 200:
                self._parse_vmix_state(response.text)
                
        except Exception as e:
            logger.logger.error(f"[TALLY] Failed to fetch vMix state: {e}")
            self.error_occurred.emit(str(e))
            
    def _parse_vmix_state(self, xml_data: str):
        """Parse vMix XML state"""
        try:
            start = time.perf_counter()
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
                    
            elapsed = (time.perf_counter() - start) * 1000
            logger.logger.debug(f"[TALLY] XML parsing completed in {elapsed:.2f}ms, found {len(inputs)} inputs")
            
            if new_states != self.tally_states:
                self.tally_states = new_states
                self.tally_state_changed.emit(self.tally_states)
                
            self.input_names = {inp['number']: inp['name'] for inp in inputs}
            self.input_list_updated.emit(inputs)
            
        except Exception as e:
            logger.logger.error(f"[TALLY] Failed to parse vMix XML: {e}")


class TallyTCPListener(QThread):
    """TCP listener with diagnostic logging"""
    
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
        logger.logger.info(f"[TALLY-TCP] Starting listener for {self.ip}:{self.port}")
        self.running = True
        
        while self.running:
            try:
                logger.logger.debug("[TALLY-TCP] Attempting connection...")
                start = time.perf_counter()
                self.socket = socket.create_connection((self.ip, self.port), timeout=5)
                elapsed = (time.perf_counter() - start) * 1000
                logger.logger.info(f"[TALLY-TCP] Connected in {elapsed:.2f}ms")
                
                self.socket.settimeout(1.0)
                self.connection_changed.emit(True)
                
                self.socket.sendall(b"SUBSCRIBE TALLY\r\n")
                logger.logger.debug("[TALLY-TCP] Subscribed to TALLY")
                
                self.tally_changed.emit()
                
                buffer = ""
                while self.running:
                    try:
                        data = self.socket.recv(1024)
                        if not data:
                            logger.logger.warning("[TALLY-TCP] Connection closed by server")
                            break
                            
                        buffer += data.decode('utf-8', errors='ignore')
                        
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            
                            if line.startswith('TALLY OK'):
                                logger.logger.debug(f"[TALLY-TCP] Received: {line}")
                                self.tally_changed.emit()
                                
                    except socket.timeout:
                        continue
                    except socket.error as e:
                        logger.logger.error(f"[TALLY-TCP] Socket error: {e}")
                        break
                        
            except Exception as e:
                logger.logger.error(f"[TALLY-TCP] Connection error: {e}")
                
            finally:
                if self.socket:
                    self.socket.close()
                    self.socket = None
                    
                self.connection_changed.emit(False)
                
            if self.running:
                logger.logger.debug("[TALLY-TCP] Reconnecting in 5 seconds...")
                self.msleep(5000)
                
    def stop(self):
        """Stop the listener"""
        logger.logger.info("[TALLY-TCP] Stopping listener")
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass


class TallyWidget(QWidget):
    """Tally Widget with performance monitoring"""
    
    def __init__(self, tally_manager: VmixTallyManager, perf_monitor: PerformanceMonitor):
        super().__init__()
        self.tally_manager = tally_manager
        self.perf_monitor = perf_monitor
        self._init_ui()
        self._connect_signals()
        
    @logger.time_function("tally_widget_init_ui")
    def _init_ui(self):
        """Initialize UI"""
        from PyQt6.QtWidgets import (QGroupBox, QGridLayout, QPushButton, 
                                    QLineEdit, QScrollArea, QHBoxLayout, QFrame,
                                    QVBoxLayout, QLabel)
        
        layout = QVBoxLayout(self)
        
        # Connection panel
        conn_group = QGroupBox("vMix Connection")
        conn_layout = QVBoxLayout(conn_group)
        
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
        self.perf_monitor.frame_rendered()
        if connected:
            self.connect_btn.setText("Disconnect")
            self.status_label.setText("Connected to vMix")
        else:
            self.connect_btn.setText("Connect")
            self.status_label.setText("Disconnected")
            
    @pyqtSlot(list)
    @logger.time_function("update_input_display")
    def _on_inputs_updated(self, inputs: list):
        """Update input display"""
        logger.logger.debug(f"[TALLY-UI] Updating {len(inputs)} inputs")
        
        # Clear existing
        for i in reversed(range(self.tally_layout.count())):
            self.tally_layout.itemAt(i).widget().deleteLater()
            
        # Add inputs in grid
        for idx, inp in enumerate(inputs):
            row = idx // 4
            col = idx % 4
            
            from PyQt6.QtWidgets import QFrame
            
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
            
        self.perf_monitor.frame_rendered()
            
    @pyqtSlot(dict)
    @logger.time_function("update_tally_colors")
    def _on_tally_changed(self, states: dict):
        """Update Tally colors"""
        logger.logger.debug(f"[TALLY-UI] Updating colors for {len(states)} states")
        
        colors = {
            'PGM': '#aa0000',
            'PVW': '#00aa00',  
            'OFF': '#333333'
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
                    }}
                """)
                
        self.perf_monitor.frame_rendered()


class MainWindowEnterprise(QMainWindow):
    """Main Window with comprehensive diagnostics"""
    
    def __init__(self):
        super().__init__()
        logger.logger.info("[MAIN] Starting MainWindowEnterprise initialization")
        
        self.setWindowTitle("PD 통합 소프트웨어 - Enterprise Edition (Diagnostic)")
        self.setGeometry(100, 100, 1200, 800)
        
        # Performance monitor
        self.perf_monitor = PerformanceMonitor()
        self.perf_monitor.performance_report.connect(self._on_performance_report)
        
        # Core managers with timing
        logger.logger.info("[MAIN] Creating core managers...")
        
        self.auth_manager = logger.time_function("create_auth_manager")(lambda: AuthManager())()
        self.ndi_manager = logger.time_function("create_ndi_manager")(lambda: NDIManagerEnterprise())()
        self.tally_manager = logger.time_function("create_tally_manager")(lambda: VmixTallyManager())()
        self.srt_manager = logger.time_function("create_srt_manager")(lambda: SRTManager())()
        self.ws_client = logger.time_function("create_ws_client")(lambda: WebSocketClient())()
        
        # Initialize UI
        logger.time_function("init_ui")(self._init_ui)()
        
        # Connect signals
        logger.time_function("connect_signals")(self._connect_signals)()
        
        # Start services
        logger.time_function("start_services")(self._start_services)()
        
        logger.logger.info("[MAIN] MainWindowEnterprise initialization complete")
        
    def _init_ui(self):
        """Initialize user interface"""
        logger.logger.debug("[MAIN-UI] Creating central widget")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        self._create_tabs()
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Performance label
        self.perf_label = QLabel("Performance: Monitoring...")
        self.status_bar.addPermanentWidget(self.perf_label)
        
    @logger.time_function("create_tabs")
    def _create_tabs(self):
        """Create application tabs"""
        logger.logger.info("[MAIN-UI] Creating tabs...")
        
        # Login tab
        self.login_widget = LoginWidget(self.auth_manager)
        self.tab_widget.addTab(self.login_widget, "로그인")
        logger.logger.debug("[MAIN-UI] Login tab created")
        
        # NDI tab
        self.ndi_widget = NDIWidgetEnterprise(self.ndi_manager)
        self.tab_widget.addTab(self.ndi_widget, "NDI 프리뷰")
        logger.logger.debug("[MAIN-UI] NDI tab created")
        
        # Tally tab
        self.tally_widget = TallyWidget(self.tally_manager, self.perf_monitor)
        self.tab_widget.addTab(self.tally_widget, "Tally")
        logger.logger.debug("[MAIN-UI] Tally tab created")
        
        # SRT tab
        self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
        self.tab_widget.addTab(self.srt_widget, "SRT 스트리밍")
        logger.logger.debug("[MAIN-UI] SRT tab created")
        
    def _connect_signals(self):
        """Connect signals between components"""
        self.auth_manager.auth_state_changed.connect(self._on_auth_changed)
        self.tally_manager.tally_state_changed.connect(self._relay_tally_state)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
    def _start_services(self):
        """Start background services"""
        if hasattr(self.auth_manager, 'unique_address'):
            self.ws_client.set_unique_address(self.auth_manager.unique_address)
            
    @pyqtSlot(bool)
    def _on_auth_changed(self, authenticated: bool):
        """Handle authentication state change"""
        logger.logger.info(f"[MAIN] Auth state changed: {authenticated}")
        if authenticated:
            self.status_bar.showMessage("Authenticated")
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
        else:
            self.status_bar.showMessage("Not authenticated")
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
                
    @pyqtSlot(dict)
    def _relay_tally_state(self, states: dict):
        """Relay Tally state to WebSocket server"""
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
            
    @pyqtSlot(int)
    def _on_tab_changed(self, index: int):
        """Handle tab change"""
        logger.logger.info(f"[MAIN] Tab changed to index {index}")
        self.perf_monitor.frame_rendered()
        
    @pyqtSlot(dict)
    def _on_performance_report(self, report: dict):
        """Update performance display"""
        fps = report['fps']
        avg_ms = report['avg_frame_time_ms']
        freezes = report['freeze_count']
        
        status = "Good" if fps > 30 else "Poor"
        if freezes > 0:
            status = f"Freezing ({freezes})"
            
        self.perf_label.setText(f"FPS: {fps:.1f} | Frame: {avg_ms:.1f}ms | Status: {status}")
        
        if freezes > 5:
            logger.logger.error(f"[PERFORMANCE] Critical: {freezes} freezes detected!")
            
    def closeEvent(self, event):
        """Clean shutdown"""
        logger.logger.info("[MAIN] Shutting down...")
        
        self.perf_monitor.monitor_timer.stop()
        self.ndi_manager.stop()
        self.tally_manager.disconnect()
        self.ws_client.stop()
        
        event.accept()


@logger.time_function("optimize_application")
def optimize_application():
    """Apply application-level optimizations"""
    logger.logger.info("[OPTIMIZE] Applying optimizations...")
    
    # High DPI
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        logger.logger.debug("[OPTIMIZE] High DPI policy set")
    except AttributeError:
        logger.logger.debug("[OPTIMIZE] High DPI already enabled in PyQt6")
    
    # Application attributes
    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        logger.logger.debug("[OPTIMIZE] OpenGL context sharing enabled")
    except AttributeError:
        logger.logger.debug("[OPTIMIZE] OpenGL attribute not available")
    
    # Process priority (Windows)
    if sys.platform == "win32":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetPriorityClass(handle, 0x80)
            logger.logger.info("[OPTIMIZE] Process priority set to HIGH")
        except Exception as e:
            logger.logger.error(f"[OPTIMIZE] Failed to set process priority: {e}")


def profile_startup():
    """Profile the application startup"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("PD Software Enterprise Diagnostic")
    app.setOrganizationName("ReturnFeed")
    app.setStyle('Fusion')
    
    # Create main window
    window = MainWindowEnterprise()
    
    profiler.disable()
    
    # Save profile results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    
    with open('startup_profile.txt', 'w') as f:
        f.write(s.getvalue())
    
    logger.logger.info("[PROFILE] Startup profile saved to startup_profile.txt")
    
    return app, window


def main():
    """Main entry point with diagnostics"""
    print("="*80)
    print("PD 통합 소프트웨어 Enterprise Edition - DIAGNOSTIC MODE")
    print("="*80)
    print("\nDetailed logging enabled. Check diagnostic_*.log files")
    print("\nStarting application with performance monitoring...")
    
    total_start = time.perf_counter()
    
    # Apply optimizations
    optimize_application()
    
    try:
        # Profile startup
        app, window = profile_startup()
        
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
        
        # Show window
        window.show()
        
        total_elapsed = (time.perf_counter() - total_start) * 1000
        logger.logger.info(f"[STARTUP] Total startup time: {total_elapsed:.2f}ms")
        print(f"\nStartup completed in {total_elapsed:.2f}ms")
        
        # Run event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.logger.critical(f"[FATAL] Application failed: {e}", exc_info=True)
        print(f"\nFATAL ERROR: {e}")
        print("\nCheck diagnostic logs for details")
        sys.exit(1)


if __name__ == '__main__':
    main()