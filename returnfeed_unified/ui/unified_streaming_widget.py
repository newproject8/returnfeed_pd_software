from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QGroupBox, QLabel, QPushButton, QListWidget,
                             QComboBox, QSpinBox, QTextEdit, QFrame,
                             QFormLayout, QTabWidget, QLineEdit, QCheckBox,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import logging

logger = logging.getLogger(__name__)


class UnifiedStreamingWidget(QWidget):
    """통합 스트리밍 위젯 - NDI와 SRT 기능을 하나의 페이지에 통합"""
    
    # 시그널 정의
    ndi_source_selected = pyqtSignal(str)  # NDI 소스 선택 시그널
    srt_stream_started = pyqtSignal()      # SRT 스트리밍 시작 시그널
    srt_stream_stopped = pyqtSignal()      # SRT 스트리밍 중지 시그널
    
    def __init__(self, ndi_module=None, srt_module=None, vmix_module=None):
        super().__init__()
        self.ndi_module = ndi_module
        self.srt_module = srt_module
        self.vmix_module = vmix_module
        
        self._init_ui()
        self._connect_modules()
        
    def _init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        # 제목
        title = QLabel("ReturnFeed Unified Streaming")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 메인 스플리터 (3열 레이아웃)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 왼쪽 패널: NDI 소스 및 vMix 연결
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # 중앙 패널: 비디오 프리뷰
        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # 오른쪽 패널: SRT 스트리밍 컨트롤
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # 스플리터 비율 설정 (25:50:25)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setStretchFactor(2, 1)
        
        main_layout.addWidget(main_splitter)
        
        # 하단 상태 표시줄
        self.status_bar = self._create_status_bar()
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        
    def _create_left_panel(self):
        """왼쪽 패널 생성: NDI 소스 및 vMix 연결"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # NDI Discovery 탭
        ndi_tab = QTabWidget()
        
        # NDI 소스 탭
        if self.ndi_module:
            ndi_widget = self.ndi_module.get_widget()
            if ndi_widget:
                ndi_tab.addTab(ndi_widget, "NDI Discovery")
        
        # vMix Tally 탭
        if self.vmix_module:
            vmix_widget = self.vmix_module.get_widget()
            if vmix_widget:
                ndi_tab.addTab(vmix_widget, "vMix Tally")
        
        layout.addWidget(ndi_tab)
        panel.setLayout(layout)
        return panel
        
    def _create_center_panel(self):
        """중앙 패널: 빈 공간 또는 추가 정보 표시용"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 정보 표시 영역
        info_group = QGroupBox("Stream Information")
        info_layout = QVBoxLayout()
        
        # 상태 정보 표시
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlainText("Welcome to ReturnFeed Unified Streaming\n\n"
                                   "• Left: NDI Discovery and vMix Tally control\n"
                                   "• Right: SRT Streaming control\n\n"
                                   "Select an NDI source from the left panel to begin.")
        info_layout.addWidget(self.info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        panel.setLayout(layout)
        return panel
        
    def _create_right_panel(self):
        """오른쪽 패널 생성: SRT 스트리밍 컨트롤"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # SRT 위젯 전체를 임베드
        if self.srt_module:
            srt_widget = self.srt_module.get_widget()
            if srt_widget:
                layout.addWidget(srt_widget)
        else:
            # 폴백: SRT 모듈이 없을 경우
            placeholder = QLabel("SRT Module Not Available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)
        
        panel.setLayout(layout)
        return panel
        
    def _create_status_bar(self):
        """하단 상태 표시줄 생성"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.Box)
        status_layout = QHBoxLayout()
        
        # NDI 상태
        self.ndi_status_label = QLabel("NDI: 대기 중")
        status_layout.addWidget(self.ndi_status_label)
        
        status_layout.addWidget(QLabel("|"))
        
        # SRT 상태
        self.srt_status_label = QLabel("SRT: 대기 중")
        status_layout.addWidget(self.srt_status_label)
        
        status_layout.addWidget(QLabel("|"))
        
        # vMix 상태
        self.vmix_status_label = QLabel("vMix: 연결 안 됨")
        status_layout.addWidget(self.vmix_status_label)
        
        status_layout.addStretch()
        
        # 시간 표시
        self.time_label = QLabel("00:00:00")
        status_layout.addWidget(self.time_label)
        
        status_frame.setLayout(status_layout)
        return status_frame
        
    def _connect_modules(self):
        """모듈 간 연결 설정"""
        # 타이머 설정 (상태 업데이트용)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # 1초마다 업데이트
        
            
    def _update_status(self):
        """상태 표시 업데이트"""
        # NDI 상태
        if self.ndi_module:
            if hasattr(self.ndi_module, 'is_connected') and self.ndi_module.is_connected():
                self.ndi_status_label.setText("NDI: 연결됨")
                self.ndi_status_label.setStyleSheet("color: green;")
            else:
                self.ndi_status_label.setText("NDI: 대기 중")
                self.ndi_status_label.setStyleSheet("color: orange;")
                
        # SRT 상태
        if self.srt_module:
            if hasattr(self.srt_module, 'is_streaming') and self.srt_module.is_streaming():
                self.srt_status_label.setText("리턴피드: 스트리밍 중")
                self.srt_status_label.setStyleSheet("color: green;")
            else:
                self.srt_status_label.setText("리턴피드: 대기 중")
                self.srt_status_label.setStyleSheet("color: orange;")
                
        # vMix 상태
        if self.vmix_module:
            if hasattr(self.vmix_module, 'is_connected') and self.vmix_module.is_connected():
                self.vmix_status_label.setText("vMix: 연결됨")
                self.vmix_status_label.setStyleSheet("color: green;")
            else:
                self.vmix_status_label.setText("vMix: 연결 안 됨")
                self.vmix_status_label.setStyleSheet("color: red;")
                
        # 시간 업데이트
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(current_time)