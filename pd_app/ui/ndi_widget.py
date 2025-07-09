# pd_app/ui/ndi_widget.py
"""
NDI Widget - NDI 소스 선택 및 비디오 프리뷰 UI
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

class NDIWidget(QWidget):
    """NDI 프리뷰 위젯"""
    
    def __init__(self, ndi_manager):
        super().__init__()
        self.ndi_manager = ndi_manager
        self.init_ui()
        self.init_connections()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 컨트롤 패널
        control_layout = QHBoxLayout()
        
        # NDI 소스 검색 버튼
        self.search_button = QPushButton("NDI 소스 탐색")
        control_layout.addWidget(self.search_button)
        
        # NDI 소스 선택 드롭다운
        self.source_combo = QComboBox()
        self.source_combo.addItem("NDI 소스를 선택하세요")
        self.source_combo.setMinimumWidth(300)
        control_layout.addWidget(self.source_combo)
        
        # 재생 모드 선택
        self.original_radio = QRadioButton("원본 재생")
        self.proxy_radio = QRadioButton("프록시 재생")
        self.original_radio.setChecked(True)
        
        mode_group = QButtonGroup()
        mode_group.addButton(self.original_radio)
        mode_group.addButton(self.proxy_radio)
        
        control_layout.addWidget(self.original_radio)
        control_layout.addWidget(self.proxy_radio)
        
        control_layout.addStretch()
        
        # 프리뷰 시작/중지 버튼
        self.preview_button = QPushButton("프리뷰 시작")
        self.preview_button.setEnabled(False)
        control_layout.addWidget(self.preview_button)
        
        layout.addLayout(control_layout)
        
        # 비디오 프리뷰 영역
        self.video_widget = pg.RawImageWidget()
        self.video_widget.setMinimumHeight(400)
        layout.addWidget(self.video_widget)
        
        # 상태 표시
        self.status_label = QLabel("상태: NDI 준비")
        layout.addWidget(self.status_label)
        
    def init_connections(self):
        """시그널 연결"""
        # NDI 관리자 시그널
        self.ndi_manager.sources_updated.connect(self.on_sources_updated)
        self.ndi_manager.frame_received.connect(self.on_frame_received)
        self.ndi_manager.connection_status_changed.connect(self.on_status_changed)
        
        # UI 시그널
        self.search_button.clicked.connect(self.search_sources)
        self.source_combo.currentIndexChanged.connect(self.on_source_selected)
        self.preview_button.clicked.connect(self.toggle_preview)
        
    def search_sources(self):
        """NDI 소스 검색"""
        self.status_label.setText("상태: NDI 소스 검색 중...")
        self.search_button.setEnabled(False)
        
        # NDI 소스 검색 시작 (비동기)
        self.ndi_manager.start_source_discovery()
        
        # 3초 후 버튼 재활성화
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.search_button.setEnabled(True))
        
    def on_sources_updated(self, sources):
        """NDI 소스 목록 업데이트"""
        self.source_combo.clear()
        
        if sources:
            self.source_combo.addItems(sources)
            self.status_label.setText(f"상태: {len(sources)}개 소스 발견")
        else:
            self.source_combo.addItem("NDI 소스를 찾을 수 없습니다")
            self.status_label.setText("상태: NDI 소스 없음")
            
    def on_source_selected(self, index):
        """소스 선택 처리"""
        if index >= 0 and self.source_combo.currentText() != "NDI 소스를 선택하세요":
            self.preview_button.setEnabled(True)
        else:
            self.preview_button.setEnabled(False)
            
    def toggle_preview(self):
        """프리뷰 시작/중지"""
        if self.preview_button.text() == "프리뷰 시작":
            source_name = self.source_combo.currentText()
            if source_name:
                self.ndi_manager.start_preview(source_name)
                self.preview_button.setText("프리뷰 중지")
                self.source_combo.setEnabled(False)
                self.search_button.setEnabled(False)
        else:
            self.ndi_manager.stop_preview()
            self.preview_button.setText("프리뷰 시작")
            self.source_combo.setEnabled(True)
            self.search_button.setEnabled(True)
            
    def on_frame_received(self, frame):
        """프레임 수신 처리"""
        try:
            # PyQtGraph RawImageWidget에 직접 표시
            if frame.ndim == 3:
                # RGB/RGBA 형식 확인
                if frame.shape[2] == 4:
                    # RGBA -> RGB 변환
                    frame = frame[:, :, :3]
                    
                # BGR -> RGB 변환 (필요한 경우)
                # frame = frame[:, :, ::-1]
                
            self.video_widget.setImage(frame)
            
        except Exception as e:
            print(f"프레임 표시 오류: {e}")
            
    def on_status_changed(self, status, color):
        """상태 변경 처리"""
        self.status_label.setText(f"상태: {status}")
        self.status_label.setStyleSheet(f"color: {color};")