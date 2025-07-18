# pd_app 모듈 타입 스텁 파일
"""PD App modules type stubs"""

from typing import Any, Optional, Dict, List
from PyQt6.QtCore import QObject, QThread, pyqtSignal

# NDI 관련 클래스들
class NDIWorkerThread(QThread):
    frame_received: pyqtSignal
    sources_updated: pyqtSignal
    status_changed: pyqtSignal
    error_occurred: pyqtSignal
    
    def __init__(self) -> None: ...
    def isRunning(self) -> bool: ...  # QThread의 메서드
    def run(self) -> None: ...
    def stop(self) -> None: ...

class NDIManager(QObject):
    sources_updated: pyqtSignal
    frame_received: pyqtSignal
    connection_status_changed: pyqtSignal
    
    worker_thread: Optional[NDIWorkerThread]
    
    def __init__(self) -> None: ...
    def initialize(self) -> None: ...
    def start_source_discovery(self) -> bool: ...
    def start_preview(self, source_name: str) -> bool: ...
    def stop_preview(self) -> None: ...

# vMix 관련 클래스들
class VMixTCPListener(QThread):
    tally_activity_detected: pyqtSignal
    connection_status_changed: pyqtSignal
    
    def __init__(self, vmix_ip: str = "127.0.0.1", vmix_tcp_port: int = 8099) -> None: ...
    def isRunning(self) -> bool: ...  # QThread의 메서드
    def run(self) -> None: ...
    def stop(self) -> None: ...

class VMixManager(QObject):
    tally_updated: pyqtSignal
    connection_status_changed: pyqtSignal
    input_list_updated: pyqtSignal
    websocket_status_changed: pyqtSignal
    
    tcp_listener: Optional[VMixTCPListener]
    
    def __init__(self) -> None: ...
    def connect_to_vmix(self, ip: str = "127.0.0.1", http_port: int = 8088, tcp_port: int = 8099) -> None: ...
    def disconnect_from_vmix(self) -> None: ...
    def get_current_tally(self) -> Dict[str, Any]: ...

# WebSocket 클라이언트
class WebSocketClient(QThread):
    connection_status_changed: pyqtSignal
    message_received: pyqtSignal
    
    def __init__(self, settings: Optional[Any] = None) -> None: ...
    def isRunning(self) -> bool: ...  # QThread의 메서드
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def send_message(self, message: Dict[str, Any]) -> None: ...

# 메인 윈도우
class MainWindow(QObject):
    window_closing: pyqtSignal
    
    ndi_manager: NDIManager
    vmix_manager: VMixManager
    ws_client: WebSocketClient
    
    def __init__(self) -> None: ...
    def show(self) -> None: ...
    def setAttribute(self, attribute: Any, on: bool = True) -> None: ...