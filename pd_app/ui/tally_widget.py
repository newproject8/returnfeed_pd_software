# pd_app/ui/tally_widget.py
"""
Tally Widget - vMix TCP Tally 시스템 UI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# 색상 정의
COLOR_OFF = "#333333"
COLOR_PVW_NORMAL = "#00aa00"
COLOR_PGM_NORMAL = "#aa0000"
COLOR_TEXT = "#ffffff"

def truncate_text(text, max_length=12):
    """텍스트 자르기"""
    if not text:
        return "---"
    return text[:max_length] if len(text) <= max_length else text[:9] + '...'

class TallyWidget(QWidget):
    """Tally 표시 위젯"""
    
    def __init__(self, vmix_manager):
        super().__init__()
        self.vmix_manager = vmix_manager
        self.init_ui()
        self.init_connections()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 연결 컨트롤
        control_layout = QHBoxLayout()
        
        # vMix IP
        control_layout.addWidget(QLabel("vMix IP:"))
        self.ip_input = QLineEdit("127.0.0.1")
        self.ip_input.setMaximumWidth(150)
        control_layout.addWidget(self.ip_input)
        
        # HTTP Port
        control_layout.addWidget(QLabel("HTTP Port:"))
        self.port_input = QLineEdit("8088")
        self.port_input.setMaximumWidth(80)
        control_layout.addWidget(self.port_input)
        
        control_layout.addStretch()
        
        # 연결 버튼
        self.connect_button = QPushButton("Connect")
        control_layout.addWidget(self.connect_button)
        
        layout.addLayout(control_layout)
        
        # Tally 표시 영역
        tally_layout = QHBoxLayout()
        
        # Preview 박스
        self.pvw_box = QLabel("PREVIEW\n---\n")
        self.pvw_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pvw_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pvw_box.setWordWrap(True)
        self.pvw_box.setMinimumHeight(200)
        
        # Program 박스
        self.pgm_box = QLabel("PROGRAM\n---\n")
        self.pgm_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.pgm_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pgm_box.setWordWrap(True)
        self.pgm_box.setMinimumHeight(200)
        
        # 폰트 설정
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.pvw_box.setFont(font)
        self.pgm_box.setFont(font)
        
        tally_layout.addWidget(self.pvw_box)
        tally_layout.addWidget(self.pgm_box)
        
        layout.addLayout(tally_layout)
        
        # 상태 표시
        status_layout = QHBoxLayout()
        
        self.vmix_status_label = QLabel("vMix: Disconnected")
        status_layout.addWidget(self.vmix_status_label)
        
        status_layout.addStretch()
        
        self.websocket_status_label = QLabel("WebSocket: Disconnected")
        status_layout.addWidget(self.websocket_status_label)
        
        status_layout.addStretch()
        
        self.input_count_label = QLabel("입력: 0개")
        status_layout.addWidget(self.input_count_label)
        
        layout.addLayout(status_layout)
        
        # 초기 스타일 설정
        self.reset_tally_display()
        
    def init_connections(self):
        """시그널 연결"""
        # vMix 관리자 시그널
        self.vmix_manager.connection_status_changed.connect(self.on_connection_status_changed)
        self.vmix_manager.tally_updated.connect(self.on_tally_updated)
        self.vmix_manager.input_list_updated.connect(self.on_input_list_updated)
        self.vmix_manager.websocket_status_changed.connect(self.on_websocket_status_changed)
        
        # UI 시그널
        self.connect_button.clicked.connect(self.toggle_connection)
        
    def toggle_connection(self):
        """연결 토글"""
        if self.connect_button.text() == "Connect":
            # 연결 시도
            try:
                ip = self.ip_input.text().strip()
                port = int(self.port_input.text().strip())
                
                self.vmix_manager.connect_to_vmix(ip, port, 8099)  # TCP 포트 추가
                
                self.connect_button.setText("Disconnect")
                self.ip_input.setEnabled(False)
                self.port_input.setEnabled(False)
                
            except ValueError:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "입력 오류", "Port는 숫자여야 합니다.")
                
        else:
            # 연결 해제
            self.vmix_manager.disconnect_from_vmix()
            
            self.connect_button.setText("Connect")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            
            self.reset_tally_display()
            
    def on_connection_status_changed(self, status, color):
        """연결 상태 변경"""
        self.vmix_status_label.setText(f"vMix: {status}")
        self.vmix_status_label.setStyleSheet(f"color: {color};")
        
    def on_websocket_status_changed(self, status, color):
        """WebSocket 상태 변경"""
        self.websocket_status_label.setText(f"WebSocket: {status}")
        self.websocket_status_label.setStyleSheet(f"color: {color};")
        
    def on_tally_updated(self, pgm, pvw, pgm_info, pvw_info):
        """Tally 업데이트"""
        # Preview 업데이트
        pvw_name = pvw_info.get('name', f'Input {pvw}') if pvw > 0 else '---'
        self.pvw_box.setText(f"PREVIEW ({pvw if pvw > 0 else '...'})\n{truncate_text(pvw_name)}\n")
        
        # Program 업데이트
        pgm_name = pgm_info.get('name', f'Input {pgm}') if pgm > 0 else '---'
        self.pgm_box.setText(f"PROGRAM ({pgm if pgm > 0 else '...'})\n{truncate_text(pgm_name)}\n")
        
        # 스타일 업데이트
        pvw_style = f"""
            background-color: {COLOR_PVW_NORMAL if pvw > 0 else COLOR_OFF};
            color: {COLOR_TEXT};
            border-radius: 5px;
            padding: 10px;
        """
        self.pvw_box.setStyleSheet(pvw_style)
        
        pgm_style = f"""
            background-color: {COLOR_PGM_NORMAL if pgm > 0 else COLOR_OFF};
            color: {COLOR_TEXT};
            border-radius: 5px;
            padding: 10px;
        """
        self.pgm_box.setStyleSheet(pgm_style)
        
    def on_input_list_updated(self, inputs):
        """입력 목록 업데이트"""
        self.input_count_label.setText(f"입력: {len(inputs)}개")
        
    def reset_tally_display(self):
        """Tally 표시 초기화"""
        self.pvw_box.setText("PREVIEW\n---\n")
        self.pgm_box.setText("PROGRAM\n---\n")
        
        default_style = f"""
            background-color: {COLOR_OFF};
            color: {COLOR_TEXT};
            border-radius: 5px;
            padding: 10px;
            border: 2px solid transparent;
        """
        self.pvw_box.setStyleSheet(default_style)
        self.pgm_box.setStyleSheet(default_style)
        
        # 상태 초기화
        self.websocket_status_label.setText("WebSocket: Disconnected")
        self.websocket_status_label.setStyleSheet("color: gray;")
        self.input_count_label.setText("입력: 0개")