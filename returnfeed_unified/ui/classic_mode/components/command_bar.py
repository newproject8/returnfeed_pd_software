"""
Command Bar Component with Login Frame
Professional broadcast software top bar
"""

from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from datetime import datetime
from ..styles.icons import get_icon, PREMIERE_COLORS
import os
import sys
import logging


class LoginFrame(QFrame):
    """계정 로그인 프레임"""
    
    login_clicked = pyqtSignal(str, str)  # username, password
    signup_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LoginFrame")
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 통일된 요소 높이
        element_height = 36
        
        # 아이디 입력
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("아이디")
        self.id_input.setObjectName("LoginInput")
        self.id_input.setMaximumWidth(120)
        self.id_input.setFixedHeight(element_height)
        layout.addWidget(self.id_input)
        
        # 구분선
        sep1 = QLabel("|")
        sep1.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']};")
        layout.addWidget(sep1)
        
        # 비밀번호 입력
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("비밀번호")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setObjectName("LoginInput")
        self.pw_input.setMaximumWidth(120)
        self.pw_input.setFixedHeight(element_height)
        layout.addWidget(self.pw_input)
        
        # 구분선
        sep2 = QLabel("|")
        sep2.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']};")
        layout.addWidget(sep2)
        
        # 로그인 버튼
        self.login_btn = QPushButton("로그인")
        self.login_btn.setObjectName("LoginButton")
        self.login_btn.setFixedHeight(element_height)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn)
        
        # 구분선
        sep3 = QLabel("|")
        sep3.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']};")
        layout.addWidget(sep3)
        
        # 회원가입 버튼
        self.signup_btn = QPushButton("회원가입")
        self.signup_btn.setObjectName("SignupButton")
        self.signup_btn.setFixedHeight(element_height)
        self.signup_btn.clicked.connect(self.signup_clicked.emit)
        layout.addWidget(self.signup_btn)
        
    def _on_login(self):
        username = self.id_input.text()
        password = self.pw_input.text()
        if username and password:
            self.login_clicked.emit(username, password)


class StatusIndicator(QLabel):
    """연결 상태 표시기"""
    
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.setObjectName("StatusIndicator")
        self._status = "offline"
        self.set_status("offline")
        
    def set_status(self, status: str):
        """상태 설정: online, offline, error"""
        self._status = status
        if status == "online":
            icon = get_icon('check_circle')
            self.setText(f"{icon} {self.name}")
            self.setStyleSheet(f"color: {PREMIERE_COLORS['success']}; font-weight: bold;")
        elif status == "error":
            icon = get_icon('error')
            self.setText(f"{icon} {self.name}")
            self.setStyleSheet(f"color: {PREMIERE_COLORS['error']}; font-weight: bold;")
        else:  # offline
            icon = get_icon('standby')
            self.setText(f"{icon} {self.name}")
            self.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']}; font-weight: bold;")


class TallyDisplay(QFrame):
    """탈리 상태 표시"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TallyDisplay")
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 10, 3)  # Reduced vertical padding
        layout.setSpacing(15)
        
        # PVW 표시 (왼쪽)
        self.pvw_label = QLabel("PVW: -")
        self.pvw_label.setObjectName("TallyPVW")
        self.pvw_label.setMinimumWidth(250)  # 2.5배 확대 (100 -> 250)
        self.pvw_label.setMaximumWidth(400)  # 최대 너비 제한
        layout.addWidget(self.pvw_label)
        
        # PGM 표시 (오른쪽)
        self.pgm_label = QLabel("PGM: -")
        self.pgm_label.setObjectName("TallyPGM")
        self.pgm_label.setMinimumWidth(250)  # 2.5배 확대 (100 -> 250)
        self.pgm_label.setMaximumWidth(400)  # 최대 너비 제한
        layout.addWidget(self.pgm_label)
        
    def update_tally(self, pgm_inputs: list, pvw_inputs: list):
        """탈리 상태 업데이트"""
        # 현재 너비 확인
        max_width = min(self.pgm_label.width(), 350) if self.pgm_label.width() > 0 else 350
        
        # PGM
        if pgm_inputs:
            pgm_text = ', '.join(pgm_inputs)
            # 글자 수 제한 (너비에 따라)
            if len(pgm_text) > max_width // 10:  # 대략 1글자당 10px
                pgm_text = pgm_text[:max_width // 10 - 3] + '...'
            self.pgm_label.setText(f"● PGM: {pgm_text}")
            self.pgm_label.setStyleSheet(f"color: {PREMIERE_COLORS['pgm_red']}; font-weight: bold;")
            self.pgm_label.setToolTip(', '.join(pgm_inputs))  # 전체 텍스트는 툴팁으로
        else:
            self.pgm_label.setText("○ PGM: -")
            self.pgm_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']};")
            self.pgm_label.setToolTip("")
            
        # PVW
        if pvw_inputs:
            pvw_text = ', '.join(pvw_inputs)
            # 글자 수 제한 (너비에 따라)
            if len(pvw_text) > max_width // 10:  # 대략 1글자당 10px
                pvw_text = pvw_text[:max_width // 10 - 3] + '...'
            self.pvw_label.setText(f"● PVW: {pvw_text}")
            self.pvw_label.setStyleSheet(f"color: {PREMIERE_COLORS['pvw_green']}; font-weight: bold;")
            self.pvw_label.setToolTip(', '.join(pvw_inputs))  # 전체 텍스트는 툴팁으로
        else:
            self.pvw_label.setText("○ PVW: -")
            self.pvw_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']};")
            self.pvw_label.setToolTip("")


class CommandBar(QFrame):
    """상단 명령 바 - 로그인, 연결 상태, 탈리"""
    
    # Signals
    login_requested = pyqtSignal(str, str)  # username, password
    signup_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CommandBar")
        self.setFixedHeight(100)  # Increased to prevent clipping
        
        self._init_ui()
        self._start_clock()
        
    def _init_ui(self):
        """UI 초기화"""
        # Main vertical layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top row - Login frame
        top_frame = QFrame()
        top_frame.setObjectName("TopFrame")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(20, 5, 20, 5)
        
        # Login frame on the left
        self.login_frame = LoginFrame()
        self.login_frame.login_clicked.connect(self.login_requested)
        self.login_frame.signup_clicked.connect(self.signup_requested)
        top_layout.addWidget(self.login_frame)
        
        # Spacer
        top_layout.addStretch()
        
        # 리턴피드 로고 (우측 끝)
        logo_label = QLabel()
        logger = logging.getLogger(__name__)
        
        # 여러 경로 시도
        logo_loaded = False
        logo_filename = "returnfeed_리턴피드_공식로고_타이포포함_흰색타이포.png"
        
        # 경로 시도 순서 (더 포괄적으로)
        paths_to_try = [
            # 1. WSL 절대 경로 (가장 확실한 경로)
            "/mnt/c/coding/returnfeed_tally_fresh/returnfeed_unified/resource/returnfeed_리턴피드_공식로고_타이포포함_흰색타이포.png",
            # 2. 현재 파일 기준 상대 경로
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resource", logo_filename),
            # 3. 프로젝트 루트 기준 (main_v2.py 위치)
            os.path.join("returnfeed_unified", "resource", logo_filename),
            # 4. sys.path[0] 기준 (스크립트 실행 위치)
            os.path.join(sys.path[0], "returnfeed_unified", "resource", logo_filename) if sys.path else None,
            # 5. Windows 절대 경로
            r"C:\coding\returnfeed_tally_fresh\returnfeed_unified\resource\returnfeed_리턴피드_공식로고_타이포포함_흰색타이포.png",
        ]
        
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Script location: {sys.path[0] if sys.path else 'Unknown'}")
        
        for i, path in enumerate(paths_to_try):
            if path:
                logger.info(f"Trying path {i+1}: {path}")
                logger.info(f"Path exists: {os.path.exists(path)}")
                
                if os.path.exists(path):
                    try:
                        logo_pixmap = QPixmap(path)
                        logger.info(f"QPixmap created. IsNull: {logo_pixmap.isNull()}")
                        logger.info(f"QPixmap size: {logo_pixmap.size().width()}x{logo_pixmap.size().height()}")
                        
                        if not logo_pixmap.isNull():
                            # 로고 크기를 적절히 조절 (높이 32px로 80% 축소)
                            scaled_pixmap = logo_pixmap.scaledToHeight(32, Qt.TransformationMode.SmoothTransformation)
                            logo_label.setPixmap(scaled_pixmap)
                            logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            logger.info(f"✅ Logo loaded successfully from: {path}")
                            logo_loaded = True
                            break
                        else:
                            logger.error(f"❌ QPixmap is null for path: {path}")
                    except Exception as e:
                        logger.error(f"❌ Error loading QPixmap from {path}: {e}")
                else:
                    logger.warning(f"❌ Path does not exist: {path}")
        
        if not logo_loaded:
            # 로고를 찾을 수 없을 때 텍스트 표시
            logger.error(f"❌ Logo file not found in any of the paths!")
            logo_label.setText("RETURNFEED")  # Fallback text
            logo_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_primary']}; font-size: 18px; font-weight: bold;")
            
        top_layout.addWidget(logo_label)
        
        main_layout.addWidget(top_frame)
        
        # Separator line
        separator_line = QFrame()
        separator_line.setObjectName("HorizontalSeparator")
        separator_line.setFixedHeight(1)
        main_layout.addWidget(separator_line)
        
        # Bottom row - Status and controls
        bottom_frame = QFrame()
        bottom_frame.setObjectName("BottomFrame")
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(20, 8, 20, 8)  # Reduced vertical margins
        bottom_layout.setSpacing(0)  # No spacing, manual control
        
        # 상태 표시기들을 중앙에 배치하기 위한 레이아웃
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(25)
        
        # 연결 상태 표시기들
        self.ndi_status = StatusIndicator("NDI")
        self.vmix_status = StatusIndicator("vMix")
        self.srt_status = StatusIndicator("리턴피드 스트림")
        
        center_layout.addWidget(self.ndi_status)
        center_layout.addWidget(self.vmix_status)
        center_layout.addWidget(self.srt_status)
        
        # 구분선
        separator = QLabel("|")
        separator.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        center_layout.addWidget(separator)
        
        # 탈리 표시
        self.tally_display = TallyDisplay()
        center_layout.addWidget(self.tally_display)
        
        # 좌측 spacer
        bottom_layout.addStretch(1)
        
        # 중앙 컨텐츠
        bottom_layout.addWidget(center_widget)
        
        # 우측 spacer
        bottom_layout.addStretch(1)
        
        # 시계 (우측 끝)
        self.clock_label = QLabel("00:00:00")
        clock_font = QFont("Consolas", 13)  # Monospace font
        clock_font.setStyleHint(QFont.StyleHint.Monospace)  # 강제로 monospace 적용
        self.clock_label.setFont(clock_font)
        self.clock_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']}; padding: 0px;")
        self.clock_label.setFixedWidth(85)  # 고정 너비로 위치 고정
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.clock_label)
        
        main_layout.addWidget(bottom_frame)
        
    def _start_clock(self):
        """시계 타이머 시작"""
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()
        
    def _update_clock(self):
        """시계 업데이트"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.setText(current_time)
        
    def update_status(self, module: str, status: str):
        """모듈 상태 업데이트"""
        if module == "NDI":
            self.ndi_status.set_status(status)
        elif module == "vMix":
            self.vmix_status.set_status(status)
        elif module == "리턴피드 스트림":
            self.srt_status.set_status(status)
            
    def update_tally(self, tally_data: dict):
        """탈리 상태 업데이트"""
        pgm_inputs = []
        pvw_inputs = []
        
        for input_name, state in tally_data.items():
            if state == "PGM":
                pgm_inputs.append(input_name)
            elif state == "PVW":
                pvw_inputs.append(input_name)
                
        self.tally_display.update_tally(pgm_inputs, pvw_inputs)