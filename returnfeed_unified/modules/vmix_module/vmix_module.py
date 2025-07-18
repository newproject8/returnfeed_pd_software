# vmix_module.py
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import QObject
from modules import BaseModule, ModuleStatus
from .vmix_manager import vMixManager
from .vmix_widget import vMixWidget


class vMixModule(BaseModule):
    """vMix Tally Broadcaster 모듈"""
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__("vMixTally", parent)
        self.manager = vMixManager(self)
        self.widget = vMixWidget()
        
        # 시그널 연결
        self._setup_connections()
        
        # 기본 설정
        self.settings = {
            "vmix_ip": "127.0.0.1",
            "vmix_http_port": 8088,
            "vmix_tcp_port": 8099,
            "relay_server": "localhost",  # localhost로 설정하여 WebSocket relay 비활성화
            "relay_port": 443,
            "use_ssl": True
        }
        
    def _setup_connections(self):
        """시그널/슬롯 연결 설정"""
        # Widget → Module
        self.widget.connect_requested.connect(self._on_connect_requested)
        self.widget.disconnect_requested.connect(self._on_disconnect_requested)
        
        # Manager → Widget
        self.manager.tally_updated.connect(self.widget.update_tally)
        self.manager.vmix_status_changed.connect(self.widget.update_vmix_status)
        self.manager.relay_status_changed.connect(self.widget.update_relay_status)
        
        # Manager → Module
        self.manager.vmix_status_changed.connect(self._on_vmix_status_changed)
        
    def initialize(self) -> bool:
        """모듈 초기화"""
        try:
            self.set_status(ModuleStatus.INITIALIZING, "초기화 중...")
            
            # Manager 초기화
            success = self.manager.initialize(
                self.settings["vmix_ip"],
                self.settings["vmix_http_port"],
                self.settings["relay_server"],
                self.settings["relay_port"]
            )
            
            if success:
                self.set_status(ModuleStatus.IDLE, "초기화 완료")
                return True
            else:
                self.emit_error("InitError", "Manager 초기화 실패")
                return False
                
        except Exception as e:
            self.emit_error("InitError", str(e))
            return False
            
    def start(self) -> bool:
        """모듈 시작"""
        try:
            self.set_status(ModuleStatus.RUNNING, "시작 중...")
            
            # WebSocket 릴레이 시작
            if self.manager.start():
                self.set_status(ModuleStatus.RUNNING, "실행 중")
                return True
            else:
                self.emit_error("StartError", "시작 실패")
                return False
                
        except Exception as e:
            self.emit_error("StartError", str(e))
            return False
            
    def stop(self) -> bool:
        """모듈 정지"""
        try:
            self.set_status(ModuleStatus.STOPPING, "정지 중...")
            
            # Manager 정지
            self.manager.stop()
            
            # UI 리셋
            self.widget.set_connected(False)
            self.widget.reset_tally_display()
            
            self.set_status(ModuleStatus.STOPPED, "정지됨")
            return True
            
        except Exception as e:
            self.emit_error("StopError", str(e))
            return False
            
    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            self.manager.stop()
            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            
    def get_widget(self) -> QWidget:
        """모듈 UI 위젯 반환"""
        return self.widget
        
    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return self.settings.copy()
        
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 적용"""
        try:
            # 설정 유효성 검사
            required_keys = ["vmix_ip", "vmix_http_port", "relay_server", "relay_port"]
            for key in required_keys:
                if key not in settings:
                    self.emit_error("SettingsError", f"Missing required setting: {key}")
                    return False
                    
            # 설정 업데이트
            self.settings.update(settings)
            
            # Manager에 적용
            if self.status == ModuleStatus.RUNNING:
                # 실행 중이면 재시작 필요
                self.logger.info("Settings will be applied on next connection")
                
            return True
            
        except Exception as e:
            self.emit_error("SettingsError", str(e))
            return False
            
    def _on_connect_requested(self, ip: str, port: int):
        """vMix 연결 요청 처리"""
        try:
            # 설정 업데이트
            self.settings["vmix_ip"] = ip
            self.settings["vmix_http_port"] = port
            
            # Manager 재초기화
            self.manager.initialize(ip, port,
                                  self.settings["relay_server"],
                                  self.settings["relay_port"])
            
            # vMix 연결
            if self.manager.connect_vmix():
                self.widget.set_connected(True)
                self.logger.info(f"Connected to vMix at {ip}:{port}")
            else:
                self.emit_error("ConnectionError", "vMix 연결 실패")
                
        except ValueError:
            QMessageBox.warning(self.widget, "입력 오류", "Port는 숫자여야 합니다.")
        except Exception as e:
            self.emit_error("ConnectionError", str(e))
            
    def _on_disconnect_requested(self):
        """vMix 연결 해제 요청 처리"""
        try:
            if self.manager.disconnect_vmix():
                self.widget.set_connected(False)
                self.logger.info("Disconnected from vMix")
                
        except Exception as e:
            self.emit_error("DisconnectionError", str(e))
            
    def _on_vmix_status_changed(self, message: str, color: str):
        """vMix 상태 변경 처리"""
        if "연결 끊김" in message:
            self.widget.set_connected(False)