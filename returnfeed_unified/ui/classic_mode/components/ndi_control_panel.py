"""
NDI Control Panel Component
차차하단행 - NDI 소스 선택, 연결 모드, 탈리 상태 전용
"""

from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QComboBox, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..styles.icons import get_icon, PREMIERE_COLORS
from .animated_combo_box import AnimatedSourceComboBox



class NDIControlPanel(QFrame):
    """NDI 전용 컨트롤 패널 - 차차하단행"""
    
    # Signals
    source_selected = pyqtSignal(str)
    connect_clicked = pyqtSignal()
    disconnect_clicked = pyqtSignal()
    bandwidth_mode_changed = pyqtSignal(str)
    refresh_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NDIControlPanel")
        self.setFixedHeight(50)  # 상단행과 동일한 높이
        
        # State
        self.is_connected = False
        
        self._init_ui()
        self._setup_styles()
        
    def _init_ui(self):
        """UI 초기화 - 극단적으로 간소화된 레이아웃"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)  # 상단행과 동일한 패딩
        layout.setSpacing(25)  # 상단행과 동일한 간격
        
        # NDI 레이블 (고정 너비로 정렬)
        ndi_label = QLabel("NDI")
        ndi_label.setFixedWidth(80)  # 고정 너비
        ndi_label.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {PREMIERE_COLORS['text_primary']};
        """)
        layout.addWidget(ndi_label)
        
        # 구분선
        separator1 = QLabel("|")
        separator1.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator1)
        
        # 소스 콤보박스
        self.source_combo = AnimatedSourceComboBox()
        self.source_combo.setFixedWidth(400)  # 고정 너비 400px
        self.source_combo.setFixedHeight(30)  # 고정 높이
        self.source_combo.addItem("소스를 선택하세요...")
        self.source_combo.currentTextChanged.connect(self._on_source_changed)
        self.source_combo.setStyleSheet(f"""
            QComboBox {{
                font-size: 12px;
                font-family: "Gmarket Sans";
                padding-left: 10px;
                padding-right: 25px;
            }}
        """)
        layout.addWidget(self.source_combo)
        
        # 구분선
        separator2 = QLabel("|")
        separator2.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator2)
        
        # 프록시/일반 토글 버튼 (단일 버튼으로 변경)
        self.bandwidth_button = QPushButton("프록시 모드")
        self.bandwidth_button.setObjectName("BandwidthToggleButton")
        self.bandwidth_button.setCheckable(True)
        self.bandwidth_button.setChecked(True)  # 기본값: 프록시
        self.bandwidth_button.setFixedSize(100, 28)
        self.bandwidth_button.clicked.connect(self._on_bandwidth_toggled)
        self._update_bandwidth_button_style(True)
        layout.addWidget(self.bandwidth_button)
        
        # 구분선
        separator3 = QLabel("|")
        separator3.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator3)
        
        # 연결해제 버튼
        self.disconnect_button = QPushButton("연결해제")
        self.disconnect_button.setObjectName("ControlButton")
        self.disconnect_button.setFixedSize(80, 28)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_button.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self.disconnect_button)
        
        # 구분선
        separator4 = QLabel("|")
        separator4.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator4)
        
        # 재탐색 버튼
        self.refresh_button = QPushButton("재탐색")
        self.refresh_button.setObjectName("ControlButton")
        self.refresh_button.setFixedSize(70, 28)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.refresh_button.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self.refresh_button)
        
        # 탈리 상태는 내부적으로만 유지 (UI에 표시하지 않음)
        self.tally_state = ""
        
        # Spacer
        layout.addStretch()
        
    def _create_compact_group(self, label_text: str):
        """컴팩트 레이블|요소 그룹 생성"""
        group_layout = QHBoxLayout()
        group_layout.setSpacing(8)
        
        # 레이블
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            font-size: 10px; 
            font-weight: 600; 
            color: {PREMIERE_COLORS['text_primary']};
            min-width: 50px;
        """)
        group_layout.addWidget(label)
        
        return group_layout
        
    def _setup_styles(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QFrame#NDIControlPanel {{
                background-color: {PREMIERE_COLORS['bg_dark']};
                border: none;
            }}
            
            QLabel {{
                color: {PREMIERE_COLORS['text_primary']};
                font-family: "Gmarket Sans";
            }}
            
            QPushButton#ControlButton {{
                background-color: {PREMIERE_COLORS['bg_medium']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 3px;
                color: {PREMIERE_COLORS['text_primary']};
                font-size: 12px;
                font-weight: 500;
                padding: 5px 10px;
            }}
            
            QPushButton#ControlButton:hover {{
                background-color: {PREMIERE_COLORS['bg_light']};
                border-color: {PREMIERE_COLORS['border_light']};
            }}
            
            QPushButton#ControlButton:pressed {{
                background-color: {PREMIERE_COLORS['bg_lighter']};
            }}
            
            QPushButton#ControlButton:disabled {{
                background-color: {PREMIERE_COLORS['bg_dark']};
                color: {PREMIERE_COLORS['text_disabled']};
                border-color: {PREMIERE_COLORS['bg_medium']};
            }}
        """)
        
    def _on_source_changed(self, text: str):
        """소스 선택 변경 처리"""
        if text and text != "소스를 선택하세요...":
            self.source_selected.emit(text)
            self.connect_clicked.emit()
            
    def _update_bandwidth_button_style(self, is_proxy: bool):
        """대역폭 버튼 스타일 업데이트"""
        if is_proxy:
            self.bandwidth_button.setText("프록시 모드")
            self.bandwidth_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PREMIERE_COLORS['info']};
                    color: white;
                    border: 1px solid {PREMIERE_COLORS['info']};
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {PREMIERE_COLORS['info_hover']};
                    border-color: {PREMIERE_COLORS['info_hover']};
                }}
            """)
        else:
            self.bandwidth_button.setText("일반 모드")
            self.bandwidth_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PREMIERE_COLORS['success']};
                    color: white;
                    border: 1px solid {PREMIERE_COLORS['success']};
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {PREMIERE_COLORS['success_hover']};
                    border-color: {PREMIERE_COLORS['success_hover']};
                }}
            """)
    
    def _on_bandwidth_toggled(self, checked: bool):
        """대역폭 토글 스위치 처리"""
        # 프록시(True) 또는 일반(False) 모드
        self._update_bandwidth_button_style(checked)
        self.bandwidth_mode_changed.emit(self.get_bandwidth_mode())
        
    def _on_refresh_clicked(self):
        """재탐색 버튼 클릭 처리"""
        self.refresh_clicked.emit()
        
    def _on_disconnect_clicked(self):
        """연결 해제 버튼 클릭 처리"""
        self.disconnect_clicked.emit()
        
    def update_sources(self, sources: list):
        """사용 가능한 소스 업데이트"""
        current = self.source_combo.currentText()
        
        self.source_combo.clear()
        self.source_combo.addItem("소스를 선택하세요...")
        
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
        self.disconnect_button.setEnabled(connected)
        
    def set_tally_state(self, state: str):
        """탈리 상태 업데이트 - 내부적으로만 유지"""
        self.tally_state = state
        
    def get_bandwidth_mode(self) -> str:
        """현재 선택된 대역폭 모드 반환"""
        return "proxy" if self.bandwidth_button.isChecked() else "normal"
        
    def set_bandwidth_mode(self, mode: str):
        """대역폭 모드 설정"""
        self.bandwidth_button.setChecked(mode == "proxy")
        self._update_bandwidth_button_style(mode == "proxy")
        
    def focus_source_combo(self):
        """NDI 소스 선택 드롭다운에 포커스하고 애니메이션 트리거"""
        # 포커스 설정
        self.source_combo.setFocus()
        
        # 아무것도 선택되지 않은 상태라면 애니메이션 트리거
        if (self.source_combo.currentText() == "소스를 선택하세요..." or 
            self.source_combo.currentIndex() == 0):
            # 애니메이션 트리거
            self.source_combo.trigger_animation()
            
        # 드롭다운 열기
        self.source_combo.showPopup()