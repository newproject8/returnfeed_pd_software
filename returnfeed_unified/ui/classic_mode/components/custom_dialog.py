"""
Custom Dialog Components
Professional styled dialogs for the application
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPixmap, QIcon
from ..styles.icons import PREMIERE_COLORS
import os
import sys


class ConfirmDialog(QDialog):
    """일체감 있는 확인 다이얼로그"""
    
    confirmed = pyqtSignal()
    cancelled = pyqtSignal()
    
    def __init__(self, title="확인", message="계속하시겠습니까?", parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        # 다이얼로그에 로고 설정
        logo_filename = "returnfeed_리턴피드_로고.png"
        self.paths_to_try = [
            # 1. WSL 절대 경로 (가장 확실한 경로)
            "/mnt/c/coding/returnfeed_tally_fresh/returnfeed_unified/resource/returnfeed_리턴피드_로고.png",
            # 2. Windows 절대 경로
            r"C:\coding\returnfeed_tally_fresh\returnfeed_unified\resource\returnfeed_리턴피드_로고.png",
            # 3. 현재 파일 기준 상대 경로
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resource", logo_filename),
            # 4. 프로젝트 루트 기준
            os.path.join("returnfeed_unified", "resource", logo_filename),
            # 5. sys.path[0] 기준
            os.path.join(sys.path[0], "returnfeed_unified", "resource", logo_filename) if sys.path else None,
        ]
        
        for path in self.paths_to_try:
            if path and os.path.exists(path):
                icon = QIcon(path)
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    break
        
        # 윈도우 플래그 설정 - 프레임리스 + 그림자
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 애니메이션
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self._init_ui(message)
        self._apply_shadow()
        
        # 페이드 인 애니메이션
        self.setWindowOpacity(0)
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
    def _init_ui(self, message):
        """UI 초기화"""
        # 메인 위젯 (실제 컨텐츠)
        self.main_widget = QWidget()
        self.main_widget.setObjectName("DialogContent")
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.main_widget)
        
        # 컨텐츠 레이아웃
        content_layout = QVBoxLayout(self.main_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 아이콘 및 메시지
        message_layout = QHBoxLayout()
        message_layout.setSpacing(15)
        
        # 리턴피드 로고
        logo_label = QLabel()
        
        logo_loaded = False
        for path in self.paths_to_try:  # 위에서 설정한 paths_to_try 사용
            if path and os.path.exists(path):
                logo_pixmap = QPixmap(path)
                if not logo_pixmap.isNull():
                    # 로고 크기를 적절히 조절 (높이 48px 기준으로 비율 유지)
                    scaled_pixmap = logo_pixmap.scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(scaled_pixmap)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    logo_loaded = True
                    break
        
        if not logo_loaded:
            # Fallback: 아이콘 텍스트
            logo_label.setText("Ⓡ")  # Info icon
            logo_label.setStyleSheet("font-size: 48px; color: #4A90E2;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        message_layout.addWidget(logo_label)
        
        # 메시지
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet(f"""
            font-family: 'Gmarket Sans', sans-serif;
            font-size: 16px;
            font-weight: 500;
            color: {PREMIERE_COLORS['text_primary']};
            line-height: 1.5;
        """)
        message_layout.addWidget(self.message_label, 1)
        
        content_layout.addLayout(message_layout)
        content_layout.addStretch()
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()
        
        # 취소 버튼
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setObjectName("DialogSecondaryButton")
        self.cancel_button.setFixedSize(100, 36)
        self.cancel_button.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_button)
        
        # 확인 버튼
        self.confirm_button = QPushButton("종료")
        self.confirm_button.setObjectName("DialogPrimaryButton")
        self.confirm_button.setFixedSize(100, 36)
        self.confirm_button.clicked.connect(self._on_confirm)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        
        content_layout.addLayout(button_layout)
        
        # 스타일 적용
        self._apply_styles()
        
    def _apply_styles(self):
        """스타일 적용"""
        self.main_widget.setStyleSheet(f"""
            QWidget#DialogContent {{
                background-color: {PREMIERE_COLORS['bg_medium']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 8px;
            }}
            
            QPushButton#DialogPrimaryButton {{
                background-color: {PREMIERE_COLORS['error']};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-family: 'Gmarket Sans', sans-serif;
                font-size: 14px;
                font-weight: 500;
            }}
            
            QPushButton#DialogPrimaryButton:hover {{
                background-color: #e54345;  /* Darker red */
            }}
            
            QPushButton#DialogPrimaryButton:pressed {{
                background-color: #d63638;  /* Even darker red */
            }}
            
            QPushButton#DialogSecondaryButton {{
                background-color: {PREMIERE_COLORS['bg_light']};
                color: {PREMIERE_COLORS['text_primary']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 4px;
                font-family: 'Gmarket Sans', sans-serif;
                font-size: 14px;
                font-weight: 500;
            }}
            
            QPushButton#DialogSecondaryButton:hover {{
                background-color: {PREMIERE_COLORS['bg_lighter']};
                border-color: {PREMIERE_COLORS['border_light']};
            }}
            
            QPushButton#DialogSecondaryButton:pressed {{
                background-color: {PREMIERE_COLORS['bg_medium']};
            }}
        """)
        
    def _apply_shadow(self):
        """그림자 효과 적용"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.main_widget.setGraphicsEffect(shadow)
        
    def _on_confirm(self):
        """확인 버튼 클릭"""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(lambda: self.accept())
        self.fade_animation.start()
        self.confirmed.emit()
        
    def _on_cancel(self):
        """취소 버튼 클릭"""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(lambda: self.reject())
        self.fade_animation.start()
        self.cancelled.emit()
        
    def paintEvent(self, event):
        """배경 페인트 (반투명 효과)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 반투명 배경
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        
        painter.end()