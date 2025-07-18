"""
Control Panel Component
Bottom control panel with source selection and status
"""

from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QComboBox, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..styles.icons import get_icon, PREMIERE_COLORS
from .animated_button import AnimatedStreamingButton
from .animated_combo_box import AnimatedSourceComboBox
from .modern_toggle import ModernToggle


class TallyIndicator(QFrame):
    """탈리 상태 표시기"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TallyIndicator")
        self.setFixedSize(100, 36)  # 다른 요소와 동일한 높이
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(0)
        
        # Title - 숨김 (높이 제한으로 인해)
        # title = QLabel("탈리 상태")
        # title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # title.setStyleSheet(f"font-size: 11px; font-weight: 500; color: {PREMIERE_COLORS['text_secondary']};")
        # layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("대기")
        self.status_label.setObjectName("TallyLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Gmarket Sans", 16, QFont.Weight.Bold)  # 적절한 크기로 조정
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        self.set_tally_state("")
        
    def set_tally_state(self, state: str):
        """탈리 상태 설정: PGM, PVW, 또는 빈 문자열"""
        if state == "PGM":
            self.status_label.setText("● 방송중")
            self.setProperty("tally", "pgm")
            self.status_label.setProperty("tally", "pgm")
        elif state == "PVW":
            self.status_label.setText("● 미리보기")
            self.setProperty("tally", "pvw")
            self.status_label.setProperty("tally", "pvw")
        else:
            self.status_label.setText("대기")
            self.setProperty("tally", "")
            self.status_label.setProperty("tally", "")
            
        # Refresh styling
        self.style().unpolish(self)
        self.style().polish(self)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)


class ControlPanel(QFrame):
    """하단 제어 패널 - 소스 선택 및 스트리밍 제어"""
    
    # Signals
    source_selected = pyqtSignal(str)  # Source name
    connect_clicked = pyqtSignal()  # Now used for refresh
    disconnect_clicked = pyqtSignal()
    srt_start_clicked = pyqtSignal()
    srt_stop_clicked = pyqtSignal()
    bandwidth_mode_changed = pyqtSignal(str)  # "normal" or "proxy"
    refresh_clicked = pyqtSignal()  # NDI 재탐색
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ControlPanel")
        self.setFixedHeight(80)
        
        # 전체 컨트롤 패널 스타일
        self.setStyleSheet(f"""
            QFrame#ControlPanel {{
                background-color: {PREMIERE_COLORS['bg_dark']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 8px;
            }}
            
            QFrame#ControlCard {{
                background-color: {PREMIERE_COLORS['card_bg']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 6px;
                padding: 8px;
            }}
            
            QFrame#ControlCard:hover {{
                background-color: {PREMIERE_COLORS['bg_medium']};
                border: 1px solid {PREMIERE_COLORS['border_light']};
            }}
            
            QLabel {{
                color: {PREMIERE_COLORS['text_primary']};
                font-family: "Gmarket Sans";
            }}
            
            QPushButton#PrimaryButton {{
                background-color: {PREMIERE_COLORS['accent_blue']};
                color: white;
                border: 1px solid {PREMIERE_COLORS['accent_blue']};
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: 500;
            }}
            
            QPushButton#PrimaryButton:hover {{
                background-color: {PREMIERE_COLORS['accent_blue_hover']};
            }}
            
            QPushButton#PrimaryButton:pressed {{
                background-color: {PREMIERE_COLORS['accent_blue_pressed']};
            }}
            
            QPushButton#SecondaryButton {{
                background-color: {PREMIERE_COLORS['button_bg']};
                color: {PREMIERE_COLORS['text_primary']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: 500;
            }}
            
            QPushButton#SecondaryButton:hover {{
                background-color: {PREMIERE_COLORS['button_hover']};
            }}
            
            QPushButton#SecondaryButton:disabled {{
                background-color: {PREMIERE_COLORS['bg_medium']};
                color: {PREMIERE_COLORS['text_disabled']};
                border-color: {PREMIERE_COLORS['text_disabled']};
            }}
            
            QPushButton#SmallButton {{
                background-color: {PREMIERE_COLORS['button_bg']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 3px;
                color: {PREMIERE_COLORS['text_primary']};
                font-size: 10px;
                padding: 2px 6px;
            }}
            
            QPushButton#SmallButton:hover {{
                background-color: {PREMIERE_COLORS['button_hover']};
            }}
            
            /* Tally Indicator Styles */
            QFrame#TallyIndicator {{
                background-color: {PREMIERE_COLORS['bg_medium']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 6px;
            }}
            
            QFrame#TallyIndicator[tally="pgm"] {{
                background-color: {PREMIERE_COLORS['pgm_red']};
                border-color: {PREMIERE_COLORS['pgm_red']};
            }}
            
            QFrame#TallyIndicator[tally="pvw"] {{
                background-color: {PREMIERE_COLORS['pvw_green']};
                border-color: {PREMIERE_COLORS['pvw_green']};
            }}
            
            QLabel#TallyLabel {{
                color: {PREMIERE_COLORS['text_primary']};
                font-weight: bold;
            }}
            
            QLabel#TallyLabel[tally="pgm"] {{
                color: white;
            }}
            
            QLabel#TallyLabel[tally="pvw"] {{
                color: white;
            }}
        """)
        
        # 모든 UI 요소의 높이 통일
        self.element_height = 36  # 통일된 높이
        
        # State
        self.is_connected = False
        self.is_srt_streaming = False
        
        self._init_ui()
        
    def _init_ui(self):
        """UI 초기화 - 카드 기반 레이아웃"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(15)
        
        # NDI 소스 선택 카드
        source_card = self._create_source_card()
        main_layout.addWidget(source_card)
        
        # 연결 모드 토글 카드
        mode_card = self._create_mode_card()
        main_layout.addWidget(mode_card)
        
        # 탈리 상태 카드
        tally_card = self._create_tally_card()
        main_layout.addWidget(tally_card)
        
        # 스트리밍 제어 카드
        streaming_card = self._create_streaming_card()
        main_layout.addWidget(streaming_card)
        
        # Spacer
        main_layout.addStretch()
        
    def _create_source_card(self):
        """NDI 소스 선택 카드 생성"""
        card = QFrame()
        card.setObjectName("ControlCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # 제목
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        
        title = QLabel("NDI 소스")
        title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {PREMIERE_COLORS['text_primary']};")
        title_layout.addWidget(title)
        
        # 재탐색 버튼 (작은 크기)
        self.connect_button = QPushButton("재탐색")
        self.connect_button.setObjectName("SmallButton")
        self.connect_button.setFixedSize(50, 20)
        self.connect_button.setStyleSheet(f"""
            QPushButton#SmallButton {{
                background-color: {PREMIERE_COLORS['button_bg']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 3px;
                color: {PREMIERE_COLORS['text_primary']};
                font-size: 10px;
                padding: 2px 6px;
            }}
            QPushButton#SmallButton:hover {{
                background-color: {PREMIERE_COLORS['button_hover']};
            }}
        """)
        self.connect_button.clicked.connect(self._on_refresh_clicked)
        title_layout.addWidget(self.connect_button)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # 소스 선택 콤보박스
        self.source_combo = AnimatedSourceComboBox()
        self.source_combo.setMinimumWidth(200)
        self.source_combo.setFixedHeight(24)
        self.source_combo.addItem("소스를 선택하세요...")
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        layout.addWidget(self.source_combo)
        
        # 연결 해제 버튼
        self.disconnect_button = QPushButton("연결 해제")
        self.disconnect_button.setObjectName("SecondaryButton")
        self.disconnect_button.setFixedHeight(22)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)
        layout.addWidget(self.disconnect_button)
        
        return card
        
    def _create_mode_card(self):
        """연결 모드 토글 카드 생성"""
        card = QFrame()
        card.setObjectName("ControlCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # 제목
        title = QLabel("연결 모드")
        title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {PREMIERE_COLORS['text_primary']};")
        layout.addWidget(title)
        
        # 토글 스위치 (크기 최적화)
        self.bandwidth_toggle = ModernToggle()
        self.bandwidth_toggle.setFixedSize(120, 32)  # 크기 최적화
        self.bandwidth_toggle.setChecked(True)  # 기본값: 프록시
        self.bandwidth_toggle.setToolTip("프록시: 저대역폭\n일반: 고품질")
        self.bandwidth_toggle.toggled.connect(self._on_bandwidth_toggled)
        layout.addWidget(self.bandwidth_toggle)
        
        # 상태 표시
        self.mode_status = QLabel("프록시 모드")
        self.mode_status.setStyleSheet(f"font-size: 10px; color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.mode_status)
        
        return card
        
    def _create_tally_card(self):
        """탈리 상태 카드 생성"""
        card = QFrame()
        card.setObjectName("ControlCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # 제목
        title = QLabel("탈리 상태")
        title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {PREMIERE_COLORS['text_primary']};")
        layout.addWidget(title)
        
        # 탈리 표시기
        self.tally_indicator = TallyIndicator()
        self.tally_indicator.setFixedSize(80, 32)
        layout.addWidget(self.tally_indicator)
        
        return card
        
    def _create_streaming_card(self):
        """스트리밍 제어 카드 생성"""
        card = QFrame()
        card.setObjectName("ControlCard")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        # 제목
        title = QLabel("리턴피드 스트림")
        title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {PREMIERE_COLORS['text_primary']};")
        layout.addWidget(title)
        
        # 상태 표시
        self.srt_status = QLabel("준비")
        self.srt_status.setStyleSheet(f"font-size: 10px; color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.srt_status)
        
        # 스트리밍 버튼
        self.srt_button = AnimatedStreamingButton("스트리밍 시작")
        self.srt_button.setEnabled(False)
        self.srt_button.setFixedHeight(28)
        self.srt_button.clicked.connect(self._on_srt_clicked)
        layout.addWidget(self.srt_button)
        
        return card
        
    def _on_source_changed(self, text: str):
        """소스 선택 변경 처리 - 자동 연결"""
        if text and text != "NDI 소스를 선택하세요...":
            # 소스 선택 시 자동으로 연결
            self.source_selected.emit(text)
            # 항상 자동 연결 시도 (연결된 경우 자동 전환)
            self.connect_clicked.emit()
            
    def _on_refresh_clicked(self):
        """재탐색 버튼 클릭 처리"""
        self.refresh_clicked.emit()
        
    def _on_disconnect_clicked(self):
        """연결 해제 버튼 클릭 처리"""
        self.disconnect_clicked.emit()
            
    def _on_srt_clicked(self):
        """SRT 버튼 클릭 처리"""
        if self.is_srt_streaming:
            self.srt_stop_clicked.emit()
        else:
            self.srt_start_clicked.emit()
            
    def update_sources(self, sources: list):
        """사용 가능한 소스 업데이트"""
        current = self.source_combo.currentText()
        
        self.source_combo.clear()
        self.source_combo.addItem("NDI 소스를 선택하세요...")
        
        for source in sources:
            self.source_combo.addItem(source)
            
        # 이전 선택 복원
        if current in sources:
            index = self.source_combo.findText(current)
            if index >= 0:
                self.source_combo.setCurrentIndex(index)
                
    def set_connected(self, connected: bool, source_name: str = ""):
        """연결 상태 업데이트"""
        self.is_connected = connected
        
        if connected:
            self.source_combo.setEnabled(True)  # 연결된 상태에서도 다른 소스 선택 가능
            self.disconnect_button.setEnabled(True)
            self.srt_button.setEnabled(True)
        else:
            self.source_combo.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.srt_button.setEnabled(False)
            
            if self.is_srt_streaming:
                self.set_srt_streaming(False)
                
    def set_tally_state(self, state: str):
        """탈리 상태 업데이트"""
        self.tally_indicator.set_tally_state(state)
        
    def set_srt_streaming(self, streaming: bool, status: str = ""):
        """SRT 스트리밍 상태 업데이트"""
        self.is_srt_streaming = streaming
        
        # 애니메이션 버튼 상태 설정
        self.srt_button.set_streaming(streaming)
        
        if streaming:
            self.srt_button.setText("스트리밍 중지")
            self.srt_status.setText(status or "스트리밍 중")
            self.srt_status.setStyleSheet(f"color: {PREMIERE_COLORS['success']}; font-weight: bold;")
        else:
            self.srt_button.setText("스트리밍 시작")
            self.srt_status.setText(status or "준비")
            self.srt_status.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
            
    def update_srt_status(self, status: str):
        """SRT 상태 텍스트 업데이트"""
        if self.is_srt_streaming:
            self.srt_status.setText(status)
        else:
            self.srt_status.setText("준비")
            
    def _on_bandwidth_toggled(self, checked: bool):
        """대역폭 토글 스위치 처리"""
        if checked:
            self.mode_status.setText("프록시 모드")
            self.mode_status.setStyleSheet(f"font-size: 10px; color: {PREMIERE_COLORS['info']};")
            self.bandwidth_toggle.setToolTip("현재: 프록시 모드\n저대역폭 (~4 Mbps)\n클릭하여 일반 모드로 전환")
        else:
            self.mode_status.setText("일반 모드")
            self.mode_status.setStyleSheet(f"font-size: 10px; color: {PREMIERE_COLORS['success']};")
            self.bandwidth_toggle.setToolTip("현재: 일반 모드\n고품질 (~160 Mbps)\n클릭하여 프록시 모드로 전환")
        self.bandwidth_mode_changed.emit(self.get_bandwidth_mode())
    
    def get_bandwidth_mode(self) -> str:
        """현재 선택된 대역폭 모드 반환"""
        return "proxy" if self.bandwidth_toggle.isChecked() else "normal"
        
    def set_bandwidth_mode(self, mode: str):
        """대역폭 모드 설정"""
        self.bandwidth_toggle.setChecked(mode == "proxy")