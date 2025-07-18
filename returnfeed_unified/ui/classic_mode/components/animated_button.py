"""
Animated Streaming Button with Flowing Light Effect
Professional broadcast-style visual feedback
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QLinearGradient, QPen, QColor, QPainterPath, QBrush
import math


class AnimatedStreamingButton(QPushButton):
    """스트리밍 버튼 - 조명이 흐르는 효과"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        
        # 애니메이션 상태
        self.is_streaming = False
        self.animation_position = 0.0  # 0.0 ~ 1.0
        self.glow_intensity = 0.0  # 글로우 강도
        
        # 애니메이션 타이머
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.setInterval(20)  # 50fps 애니메이션
        
        # 스타일 설정
        self.setMinimumHeight(36)
        
    def set_streaming(self, streaming: bool):
        """스트리밍 상태 설정"""
        self.is_streaming = streaming
        
        if streaming:
            self.animation_timer.start()
        else:
            self.animation_timer.stop()
            self.animation_position = 0.0
            self.glow_intensity = 0.0
            self.update()
            
    def _update_animation(self):
        """애니메이션 업데이트"""
        # 위치 업데이트 (0 ~ 2 순환, 2배 느리게)
        self.animation_position += 0.0025  # 기존 0.005에서 절반으로 감소
        if self.animation_position > 2.0:
            self.animation_position = 0.0
            
        # 글로우 강도 계산 (사인파로 부드러운 변화)
        self.glow_intensity = (math.sin(self.animation_position * math.pi) + 1) / 2
        
        self.update()
        
    def paintEvent(self, event):
        """커스텀 페인트 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 버튼 영역
        rect = self.rect()
        
        # 기본 버튼 그리기
        if self.is_streaming:
            # 스트리밍 중: 빨간색 계열
            base_color = QColor(180, 40, 40)
            glow_color = QColor(255, 100, 100)
            border_base = QColor(200, 50, 50)
        else:
            # 일반 상태
            base_color = QColor(60, 60, 60)
            glow_color = QColor(100, 100, 100)
            border_base = QColor(80, 80, 80)
            
        # 배경 채우기
        painter.fillRect(rect, base_color)
        
        if self.is_streaming:
            # 조명 효과를 위한 그라데이션 생성
            gradient_rect = rect.adjusted(2, 2, -2, -2)
            
            # 이동하는 조명 효과 (좌우 왕복)
            light_width = gradient_rect.width() * 0.4  # 조명 폭
            
            # 0~1: 왼쪽에서 오른쪽, 1~2: 오른쪽에서 왼쪽
            if self.animation_position <= 1.0:
                normalized_pos = self.animation_position
            else:
                normalized_pos = 2.0 - self.animation_position
                
            light_center = gradient_rect.left() + gradient_rect.width() * normalized_pos
            
            # 외곽선 그라데이션
            path = QPainterPath()
            path.addRoundedRect(gradient_rect.x(), gradient_rect.y(), 
                              gradient_rect.width(), gradient_rect.height(), 3, 3)
            
            # 펜 설정
            pen = QPen()
            pen.setWidth(3)
            
            # 조명 위치에 따른 그라데이션
            gradient = QLinearGradient(gradient_rect.left(), 0, gradient_rect.right(), 0)
            
            # 조명 전후로 색상 설정
            for i in range(5):
                pos = i / 4.0
                actual_pos = gradient_rect.left() + gradient_rect.width() * pos
                
                # 조명과의 거리 계산
                distance = abs(actual_pos - light_center)
                intensity = max(0, 1 - (distance / light_width))
                
                # 색상 보간
                if intensity > 0:
                    color = QColor(
                        int(border_base.red() + (glow_color.red() - border_base.red()) * intensity),
                        int(border_base.green() + (glow_color.green() - border_base.green()) * intensity),
                        int(border_base.blue() + (glow_color.blue() - border_base.blue()) * intensity),
                        255
                    )
                else:
                    color = border_base
                    
                gradient.setColorAt(pos, color)
            
            pen.setBrush(gradient)
            painter.setPen(pen)
            painter.drawPath(path)
            
            # 내부 글로우 효과
            glow_rect = rect.adjusted(4, 4, -4, -4)
            glow_gradient = QLinearGradient(glow_rect.left(), glow_rect.top(), 
                                          glow_rect.left(), glow_rect.bottom())
            glow_gradient.setColorAt(0, QColor(255, 100, 100, int(50 * self.glow_intensity)))
            glow_gradient.setColorAt(1, QColor(255, 50, 50, int(20 * self.glow_intensity)))
            
            painter.fillRect(glow_rect, glow_gradient)
            
        else:
            # 일반 외곽선
            painter.setPen(QPen(border_base, 1))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        # 텍스트 그리기
        painter.setPen(QColor(255, 255, 255) if self.is_streaming else QColor(200, 200, 200))
        font = self.font()
        font.setBold(self.is_streaming)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())
        
        painter.end()