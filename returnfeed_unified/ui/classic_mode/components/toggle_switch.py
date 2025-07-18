"""
Modern Toggle Switch Widget
iOS-style toggle switch for bandwidth mode selection
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont


class ToggleSwitch(QWidget):
    """현대적인 토글 스위치 위젯"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 상태
        self._checked = True  # 기본값: True (프록시)
        
        # 크기 설정
        self.setFixedSize(60, 30)
        
        # 애니메이션
        self._handle_position = 0.0
        self.animation = QPropertyAnimation(self, b"handle_position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
        
        # 색상
        self.bg_color_on = QColor("#0084FF")  # 파란색 (프록시 ON)
        self.bg_color_off = QColor("#52c41a")  # 녹색 (일반 OFF)
        self.handle_color = QColor("#FFFFFF")
        
        # 초기 위치 설정
        self._update_handle_position()
        
    def isChecked(self):
        """현재 체크 상태 반환"""
        return self._checked
        
    def setChecked(self, checked):
        """체크 상태 설정"""
        if self._checked != checked:
            self._checked = checked
            self._update_handle_position()
            self.toggled.emit(checked)
            
    def toggle(self):
        """상태 토글"""
        self.setChecked(not self._checked)
        
    def _update_handle_position(self):
        """핸들 위치 업데이트"""
        if self._checked:
            end_pos = self.width() - self.height() + 4
        else:
            end_pos = 4
            
        self.animation.setStartValue(self._handle_position)
        self.animation.setEndValue(float(end_pos))
        self.animation.start()
        
    def mousePressEvent(self, event):
        """마우스 클릭 처리"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            
    @property
    def handle_position(self):
        return self._handle_position
        
    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update()
        
    def paintEvent(self, event):
        """페인트 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 배경 그리기
        bg_rect = self.rect()
        bg_radius = bg_rect.height() // 2
        
        # 현재 상태에 따른 색상 보간
        if self.animation.state() == QPropertyAnimation.State.Running:
            # 애니메이션 중일 때 색상 보간
            progress = (self._handle_position - 4) / (self.width() - self.height())
            r = int(self.bg_color_off.red() + (self.bg_color_on.red() - self.bg_color_off.red()) * progress)
            g = int(self.bg_color_off.green() + (self.bg_color_on.green() - self.bg_color_off.green()) * progress)
            b = int(self.bg_color_off.blue() + (self.bg_color_on.blue() - self.bg_color_off.blue()) * progress)
            current_bg_color = QColor(r, g, b)
        else:
            current_bg_color = self.bg_color_on if self._checked else self.bg_color_off
            
        # 배경 그리기
        painter.setBrush(QBrush(current_bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bg_rect, bg_radius, bg_radius)
        
        # 핸들 그리기
        handle_radius = (self.height() - 8) // 2
        handle_rect = QRect(
            int(self._handle_position),
            4,
            self.height() - 8,
            self.height() - 8
        )
        
        # 핸들 그림자
        shadow_rect = handle_rect.adjusted(1, 1, 1, 1)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
        painter.drawEllipse(shadow_rect)
        
        # 핸들
        painter.setBrush(QBrush(self.handle_color))
        painter.drawEllipse(handle_rect)
        
        painter.end()