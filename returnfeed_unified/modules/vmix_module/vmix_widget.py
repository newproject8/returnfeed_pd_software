# vmix_widget.py
from PyQt6.QtWidgets import (QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QGroupBox, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional


class TallyBox(QLabel):
    """Tally 상태 표시 박스"""
    
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(100)
        self.reset()
        
    def reset(self):
        """초기 상태로 리셋"""
        self.setText(f"{self.title}\n---\n")
        self.setStyleSheet(
            "background-color: #333333; color: #ffffff; "
            "border-radius: 5px; padding: 10px; font-weight: bold;"
        )
        
    def update_status(self, input_num: int, input_name: str, color: str):
        """상태 업데이트"""
        display_num = input_num if input_num > 0 else "..."
        display_name = self._truncate_text(input_name) if input_num > 0 else "---"
        
        self.setText(f"{self.title} ({display_num})\n{display_name}\n")
        self.setStyleSheet(
            f"background-color: {color}; color: #ffffff; "
            "border-radius: 5px; padding: 10px; font-weight: bold;"
        )
        
    @staticmethod
    def _truncate_text(text: str, max_length: int = 12) -> str:
        """텍스트 길이 제한"""
        if not text:
            return "---"
        return text[:max_length] if len(text) <= max_length else text[:9] + '...'


class vMixWidget(QWidget):
    """vMix 모듈 UI 위젯"""
    
    # 시그널
    connect_requested = pyqtSignal(str, int)  # ip, port
    disconnect_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self._is_connected = False
        
    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 연결 설정 그룹
        connection_group = QGroupBox("vMix 연결 설정")
        connection_layout = QHBoxLayout()
        
        self.ip_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("8088")
        self.connect_button = QPushButton("Connect")
        
        connection_layout.addWidget(QLabel("vMix IP:"))
        connection_layout.addWidget(self.ip_input)
        connection_layout.addWidget(QLabel("HTTP Port:"))
        connection_layout.addWidget(self.port_input)
        connection_layout.addStretch(1)
        connection_layout.addWidget(self.connect_button)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Tally 디스플레이
        tally_group = QGroupBox("Tally Status")
        tally_layout = QHBoxLayout()
        
        self.pvw_box = TallyBox("PREVIEW")
        self.pgm_box = TallyBox("PROGRAM")
        
        tally_layout.addWidget(self.pvw_box)
        tally_layout.addWidget(self.pgm_box)
        
        tally_group.setLayout(tally_layout)
        layout.addWidget(tally_group, stretch=1)
        
        # 상태 표시
        status_layout = QHBoxLayout()
        
        self.vmix_status = QLabel("vMix: Disconnected")
        self.relay_status = QLabel("Server: Disconnected")
        
        font = QFont()
        font.setPointSize(9)
        self.vmix_status.setFont(font)
        self.relay_status.setFont(font)
        
        status_layout.addWidget(self.vmix_status)
        status_layout.addStretch(1)
        status_layout.addWidget(self.relay_status)
        
        layout.addLayout(status_layout)
        
        # 시그널 연결
        self.connect_button.clicked.connect(self._on_connect_clicked)
        
    def _on_connect_clicked(self):
        """연결 버튼 클릭 처리"""
        if not self._is_connected:
            try:
                ip = self.ip_input.text().strip()
                port = int(self.port_input.text().strip())
                self.connect_requested.emit(ip, port)
            except ValueError:
                # 포트 번호 오류 처리는 상위 레벨에서
                pass
        else:
            self.disconnect_requested.emit()
            
    def set_connected(self, connected: bool):
        """연결 상태 설정"""
        self._is_connected = connected
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.ip_input.setEnabled(not connected)
        self.port_input.setEnabled(not connected)
        
        if not connected:
            self.reset_tally_display()
            
    def update_tally(self, pgm: int, pvw: int, pgm_name: str, pvw_name: str):
        """Tally 상태 업데이트"""
        pvw_color = "#00aa00" if pvw > 0 else "#333333"
        pgm_color = "#aa0000" if pgm > 0 else "#333333"
        
        self.pvw_box.update_status(pvw, pvw_name, pvw_color)
        self.pgm_box.update_status(pgm, pgm_name, pgm_color)
        
    def reset_tally_display(self):
        """Tally 디스플레이 리셋"""
        self.pvw_box.reset()
        self.pgm_box.reset()
        
    def update_vmix_status(self, message: str, color: str):
        """vMix 연결 상태 업데이트"""
        self.vmix_status.setText(f"vMix: {message}")
        self.vmix_status.setStyleSheet(f"color: {color};")
        
    def update_relay_status(self, message: str, color: str):
        """릴레이 서버 상태 업데이트"""
        self.relay_status.setText(f"Server: {message}")
        self.relay_status.setStyleSheet(f"color: {color};")