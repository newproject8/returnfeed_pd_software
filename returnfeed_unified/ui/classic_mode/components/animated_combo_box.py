"""
Animated ComboBox with Rotating Light Effect
Professional broadcast-style visual feedback for required selection
"""

from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QLinearGradient, QPen, QColor, QPainterPath, QBrush
import math


class AnimatedSourceComboBox(QComboBox):
    """소스 선택 콤보박스 - 선택 필요 시 회전하는 빛 효과"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 애니메이션 상태
        self.needs_selection = True  # 선택이 필요한 상태
        self.animation_angle = 0.0  # 0 ~ 360도
        self.glow_intensity = 0.8  # 글로우 강도
        
        # 애니메이션 타이머
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.setInterval(20)  # 50fps 애니메이션
        
        # 선택 변경 시 애니메이션 상태 업데이트
        self.currentTextChanged.connect(self._on_selection_changed)
        
        # 애니메이션 시작
        self.animation_timer.start()
        
    def _on_selection_changed(self, text):
        """선택 변경 시 처리"""
        # 실제 소스가 선택되었는지 확인
        if text and text != "소스를 선택하세요...":
            self.needs_selection = False
        else:
            self.needs_selection = True
            
    def _update_animation(self):
        """애니메이션 업데이트"""
        if self.needs_selection:
            # 각도 업데이트 (360도 회전)
            self.animation_angle += 2.0  # 회전 속도
            if self.animation_angle >= 360.0:
                self.animation_angle = 0.0
                
            # 글로우 강도 펄싱 효과
            self.glow_intensity = 0.5 + 0.3 * math.sin(self.animation_angle * math.pi / 180.0)
            self.update()
            
    def paintEvent(self, event):
        """커스텀 페인트 이벤트"""
        # 기본 콤보박스 그리기
        super().paintEvent(event)
        
        if self.needs_selection:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # 콤보박스 영역
            rect = self.rect()
            
            # 회전하는 빛 효과를 위한 경로
            path = QPainterPath()
            path.addRoundedRect(rect.x() + 1, rect.y() + 1, 
                              rect.width() - 2, rect.height() - 2, 3, 3)
            
            # 펜 설정
            pen = QPen()
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            
            # 회전하는 그라데이션 생성
            center_x = rect.center().x()
            center_y = rect.center().y()
            
            # 각도를 라디안으로 변환
            angle_rad = self.animation_angle * math.pi / 180.0
            
            # 그라데이션 시작점과 끝점 계산
            gradient_length = max(rect.width(), rect.height()) * 0.7
            start_x = center_x + gradient_length * math.cos(angle_rad)
            start_y = center_y + gradient_length * math.sin(angle_rad)
            end_x = center_x - gradient_length * math.cos(angle_rad)
            end_y = center_y - gradient_length * math.sin(angle_rad)
            
            gradient = QLinearGradient(start_x, start_y, end_x, end_y)
            
            # 색상 설정 - 파란색 계열로 주의를 끄는 효과
            base_color = QColor(100, 150, 255)
            glow_color = QColor(150, 200, 255)
            
            # 그라데이션 색상 설정
            gradient.setColorAt(0, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))
            gradient.setColorAt(0.3, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 
                                           int(200 * self.glow_intensity)))
            gradient.setColorAt(0.5, QColor(base_color.red(), base_color.green(), base_color.blue(), 
                                           int(255 * self.glow_intensity)))
            gradient.setColorAt(0.7, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 
                                           int(200 * self.glow_intensity)))
            gradient.setColorAt(1, QColor(base_color.red(), base_color.green(), base_color.blue(), 0))
            
            pen.setBrush(gradient)
            painter.setPen(pen)
            painter.drawPath(path)
            
            # 추가 글로우 효과
            if self.glow_intensity > 0.7:
                glow_pen = QPen()
                glow_pen.setWidth(4)
                glow_pen.setColor(QColor(150, 200, 255, int(50 * self.glow_intensity)))
                painter.setPen(glow_pen)
                painter.drawPath(path)
            
            painter.end()
            
    def trigger_animation(self):
        """애니메이션 트리거 - 강제로 애니메이션 시작"""
        self.needs_selection = True
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        # 애니메이션 강화를 위해 글로우 강도 증가
        self.glow_intensity = 1.0
        self.update()