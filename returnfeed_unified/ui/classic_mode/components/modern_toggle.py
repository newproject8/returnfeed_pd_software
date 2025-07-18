"""
Modern Toggle Switch with Visual States
Professional broadcast style toggle with clear visual feedback
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect, QSize, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient, QPainterPath


class ModernToggle(QWidget):
    """현대적인 시각적 토글 스위치"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 상태
        self._checked = True  # 기본값: True (프록시)
        
        # 크기 설정 - 컴팩트한 크기로 최적화
        self.setFixedSize(120, 32)
        
        # 애니메이션
        self._handle_position = 0.0
        self.animation = QPropertyAnimation(self, b"handle_position")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(300)
        
        # 글로우 애니메이션
        self._glow_opacity = 0.0
        self.glow_animation = QPropertyAnimation(self, b"glow_opacity")
        self.glow_animation.setDuration(200)
        
        # 폰트 설정
        self.font = QFont("Gmarket Sans", 10, QFont.Weight.Medium)
        
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
        # 스위치 영역 (중앙 50%)
        switch_width = self.width() * 0.5
        switch_start = self.width() * 0.25
        
        if self._checked:
            # 프록시 모드 - 왼쪽
            end_pos = switch_start + 2
        else:
            # 일반 모드 - 오른쪽
            end_pos = switch_start + switch_width - 20
            
        self.animation.setStartValue(self._handle_position)
        self.animation.setEndValue(float(end_pos))
        self.animation.start()
        
    def mousePressEvent(self, event):
        """마우스 클릭 처리"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 글로우 효과
            self.glow_animation.setStartValue(0.0)
            self.glow_animation.setEndValue(1.0)
            self.glow_animation.finished.connect(self._fade_glow)
            self.glow_animation.start()
            
            self.toggle()
            
    def _fade_glow(self):
        """글로우 페이드 아웃"""
        self.glow_animation.setStartValue(1.0)
        self.glow_animation.setEndValue(0.0)
        self.glow_animation.start()
        
    def enterEvent(self, event):
        """마우스 진입"""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def leaveEvent(self, event):
        """마우스 이탈"""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
    @property
    def handle_position(self):
        return self._handle_position
        
    @handle_position.setter
    def handle_position(self, pos):
        self._handle_position = pos
        self.update()
        
    @property
    def glow_opacity(self):
        return self._glow_opacity
        
    @glow_opacity.setter
    def glow_opacity(self, opacity):
        self._glow_opacity = opacity
        self.update()
        
    def paintEvent(self, event):
        """페인트 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font)
        
        # 전체 배경 (어두운 배경)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter.fillPath(bg_path, QColor("#1a1a1a"))
        
        # 텍스트 영역 너비 (조정)
        text_width = self.width() * 0.25
        
        # 프록시 텍스트 (왼쪽)
        proxy_rect = QRect(0, 0, int(text_width), self.height())
        if self._checked:
            painter.setPen(QColor("#0084FF"))
        else:
            painter.setPen(QColor("#666666"))
        painter.drawText(proxy_rect, Qt.AlignmentFlag.AlignCenter, "프록시")
        
        # 일반 텍스트 (오른쪽)
        normal_rect = QRect(int(self.width() - text_width), 0, int(text_width), self.height())
        if not self._checked:
            painter.setPen(QColor("#52c41a"))
        else:
            painter.setPen(QColor("#666666"))
        painter.drawText(normal_rect, Qt.AlignmentFlag.AlignCenter, "일반")
        
        # 스위치 트랙 영역 (조정)
        switch_width = self.width() * 0.5
        switch_x = self.width() * 0.25
        switch_rect = QRect(int(switch_x), 5, int(switch_width), self.height() - 10)
        
        # 스위치 트랙 배경
        track_path = QPainterPath()
        track_path.addRoundedRect(switch_rect.x(), switch_rect.y(), 
                                switch_rect.width(), switch_rect.height(), 12, 12)
        
        # 그라데이션 배경
        gradient = QLinearGradient(switch_rect.x(), 0, switch_rect.x() + switch_rect.width(), 0)
        if self._checked:
            # 프록시 모드 - 파란색 그라데이션
            gradient.setColorAt(0, QColor("#0084FF"))
            gradient.setColorAt(1, QColor("#0066CC"))
        else:
            # 일반 모드 - 녹색 그라데이션
            gradient.setColorAt(0, QColor("#52c41a"))
            gradient.setColorAt(1, QColor("#3f9c0a"))
            
        painter.fillPath(track_path, QBrush(gradient))
        
        # 트랙 테두리
        painter.setPen(QPen(QColor("#333333"), 1))
        painter.drawPath(track_path)
        
        # 글로우 효과
        if self._glow_opacity > 0:
            glow_color = QColor("#0084FF" if self._checked else "#52c41a")
            glow_color.setAlpha(int(100 * self._glow_opacity))
            painter.setPen(QPen(glow_color, 3))
            painter.drawPath(track_path)
        
        # 핸들
        handle_rect = QRect(int(self._handle_position), switch_rect.y() + 1, 
                          18, switch_rect.height() - 2)
        
        # 핸들 그림자
        shadow_gradient = QLinearGradient(handle_rect.x(), handle_rect.y(), 
                                        handle_rect.x(), handle_rect.y() + handle_rect.height())
        shadow_gradient.setColorAt(0, QColor(0, 0, 0, 80))
        shadow_gradient.setColorAt(1, QColor(0, 0, 0, 40))
        
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(handle_rect.x() + 1, handle_rect.y() + 1,
                                 handle_rect.width(), handle_rect.height(), 10, 10)
        painter.fillPath(shadow_path, QBrush(shadow_gradient))
        
        # 핸들 본체
        handle_path = QPainterPath()
        handle_path.addRoundedRect(handle_rect.x(), handle_rect.y(),
                                 handle_rect.width(), handle_rect.height(), 10, 10)
        
        # 핸들 그라데이션
        handle_gradient = QLinearGradient(handle_rect.x(), handle_rect.y(),
                                        handle_rect.x(), handle_rect.y() + handle_rect.height())
        handle_gradient.setColorAt(0, QColor("#ffffff"))
        handle_gradient.setColorAt(1, QColor("#f0f0f0"))
        
        painter.fillPath(handle_path, QBrush(handle_gradient))
        
        # 핸들 테두리
        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawPath(handle_path)
        
        # 핸들 내부 표시
        indicator_rect = QRect(handle_rect.x() + 6, handle_rect.y() + 5,
                             6, handle_rect.height() - 10)
        if self._checked:
            painter.fillRect(indicator_rect, QColor("#0084FF"))
        else:
            painter.fillRect(indicator_rect, QColor("#52c41a"))
        
        painter.end()