"""
Single Channel Video Display Component
Optimized for monitoring one NDI source with professional features
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QImage, QColor, QFont, QPen
import logging

logger = logging.getLogger(__name__)


class SingleChannelVideoDisplay(QFrame):
    """Professional single-channel video display with 16:9 aspect ratio"""
    
    # Signals
    double_clicked = pyqtSignal()  # For fullscreen toggle
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VideoDisplay")
        self.setMinimumSize(640, 360)  # Minimum 16:9 size
        
        # Video state
        self.current_frame = None
        self.source_name = ""
        self.is_connected = False
        self.is_streaming = False  # SRT 스트리밍 상태
        self.frame_info = {
            'resolution': '',
            'fps': 0,
            'bitrate': '',
            'audio_level': -60
        }
        
        # Tally state
        self.tally_state = ""  # "PGM", "PVW", or ""
        
        # Display options
        self.show_safe_areas = False
        self.show_info_overlay = True
        self.show_audio_meter = True
        
        # Audio meter animation
        self.audio_peak = -60.0  # Peak hold value
        self.audio_history = [-60.0] * 20  # Smooth audio values
        
        # Fade to black animation
        self._fade_opacity = 0.0  # 0.0 = 투명 (비디오 보임), 1.0 = 불투명 (검은색)
        self.fade_animation = QPropertyAnimation(self, b"fadeOpacity")
        self.fade_animation.setDuration(800)  # 0.8초 동안 페이드
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Style and performance optimization
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)  # Prevent unnecessary background fills
        
        # Optimization: Disable complex composition for better performance
        self.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, False)
        self.setUpdatesEnabled(True)
        
    def mouseDoubleClickEvent(self, event):
        """Handle double-click for fullscreen"""
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
        
    def paintEvent(self, event):
        """Paint the video frame with overlays"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        try:
            # Fill background
            painter.fillRect(self.rect(), QColor(0, 0, 0))
            
            # Calculate 16:9 display area
            display_rect = self._calculate_display_rect()
            
            if self.current_frame and not self.current_frame.isNull():
                # Draw video frame
                painter.drawImage(display_rect, self.current_frame)
                
                # Draw overlays
                if self.show_safe_areas:
                    self._draw_safe_areas(painter, display_rect)
                    
                if self.show_info_overlay:
                    self._draw_info_overlay(painter, display_rect)
                    
                if self.show_audio_meter:
                    self._draw_audio_meter(painter, display_rect)
                    
            else:
                # Draw placeholder
                self._draw_placeholder(painter, display_rect)
                
            # Draw tally border
            if self.tally_state:
                self._draw_tally_border(painter, display_rect)
                
            # 페이드 투 블랙 효과 적용
            if self._fade_opacity > 0:
                painter.fillRect(self.rect(), QColor(0, 0, 0, int(255 * self._fade_opacity)))
                
            # 스트리밍 중 오버레이 텍스트 (페이드 효과 위에 그리기)
            if self.is_streaming and self._fade_opacity > 0.7:
                # 텍스트 영역
                text_rect = QRect(0, display_rect.center().y() - 30, self.width(), 60)
                
                # 회색 텍스트
                painter.setPen(QColor(180, 180, 180))  # 회색
                font = QFont("Gmarket Sans", 28, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "리턴피드로 스트리밍 중")
                
        except Exception as e:
            logger.error(f"Paint error: {e}")
        finally:
            painter.end()
            
    def _calculate_display_rect(self) -> QRect:
        """Calculate 16:9 display area centered in widget"""
        widget_width = self.width()
        widget_height = self.height()
        
        # Calculate 16:9 dimensions that fit in widget
        target_width = widget_width
        target_height = int(target_width * 9 / 16)
        
        if target_height > widget_height:
            target_height = widget_height
            target_width = int(target_height * 16 / 9)
            
        # Center the display area
        x = (widget_width - target_width) // 2
        y = (widget_height - target_height) // 2
        
        return QRect(x, y, target_width, target_height)
        
    def _draw_placeholder(self, painter: QPainter, rect: QRect):
        """비디오가 없을 때 플레이스홀더 그리기"""
        # 어두운 회색 배경
        painter.fillRect(rect, QColor(40, 40, 40))
        
        # 중앙 텍스트
        painter.setPen(QColor(150, 150, 150))
        font = QFont("Gmarket Sans", 16)
        painter.setFont(font)
        
        # SRT 스트리밍 중인 경우는 paintEvent에서 처리하므로 여기서는 스킵
        if self.is_streaming:
            return
        elif self.source_name and not self.is_connected:
            # 연결 중 메시지 - 더 눈에 띄게
            painter.setPen(QColor(255, 200, 100))  # 노란색
            font = QFont("Gmarket Sans", 18, QFont.Weight.Bold)
            painter.setFont(font)
            text = f"🔄 {self.source_name}에 연결 중..."
            
            # 부가 정보
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
            
            # 작은 폰트로 추가 정보
            font = QFont("Gmarket Sans", 12)
            painter.setFont(font)
            painter.setPen(QColor(150, 150, 150))
            sub_text = "\n\n\n잠시만 기다려 주세요..."
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, sub_text)
            return
        else:
            text = "NDI 소스가 선택되지 않았습니다\n\n제어 패널에서 NDI 소스를 선택하세요"
            
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        
    def _draw_tally_border(self, painter: QPainter, rect: QRect):
        """Draw tally state border"""
        if self.tally_state == "PGM":
            color = QColor(255, 55, 55)  # Red
        elif self.tally_state == "PVW":
            color = QColor(0, 255, 55)   # Green
        else:
            return
            
        # Draw thick border
        pen = QPen(color, 8)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect.adjusted(4, 4, -4, -4))
        
        # Draw tally label
        label_rect = QRect(rect.x() + 20, rect.y() + 20, 80, 30)
        painter.fillRect(label_rect, color)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self.tally_state)
        
    def _draw_safe_areas(self, painter: QPainter, rect: QRect):
        """Draw broadcast safe areas (90% and 80%)"""
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # 90% safe area (action safe)
        safe_90 = rect.adjusted(
            int(rect.width() * 0.05),
            int(rect.height() * 0.05),
            -int(rect.width() * 0.05),
            -int(rect.height() * 0.05)
        )
        painter.drawRect(safe_90)
        
        # 80% safe area (title safe)
        safe_80 = rect.adjusted(
            int(rect.width() * 0.1),
            int(rect.height() * 0.1),
            -int(rect.width() * 0.1),
            -int(rect.height() * 0.1)
        )
        painter.drawRect(safe_80)
        
    def _draw_info_overlay(self, painter: QPainter, rect: QRect):
        """Draw information overlay"""
        if not self.is_connected:
            return
            
        # Semi-transparent background
        info_rect = QRect(rect.x(), rect.bottom() - 40, rect.width(), 40)
        painter.fillRect(info_rect, QColor(0, 0, 0, 180))
        
        # Info text
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Consolas", 11)
        painter.setFont(font)
        
        info_text = f"{self.source_name} | {self.frame_info['resolution']} @ {self.frame_info['fps']}fps | {self.frame_info['bitrate']}"
        painter.drawText(info_rect.adjusted(10, 0, -10, 0), 
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                        info_text)
        
        # Audio level on right
        audio_text = f"Audio: {self.frame_info['audio_level']:.1f}dB"
        painter.drawText(info_rect.adjusted(10, 0, -10, 0),
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                        audio_text)
    
    def _draw_audio_meter(self, painter: QPainter, rect: QRect):
        """반투명 오디오 레벨 미터 그리기"""
        if not self.is_connected:
            return
            
        # 미터 크기와 위치 (우측, 세로)
        meter_width = 25  # 40 → 25로 줄임
        meter_margin = 20
        meter_x = rect.right() - meter_width - meter_margin
        meter_y = rect.y() + meter_margin
        meter_height = rect.height() - (meter_margin * 2) - 50  # 하단 정보 오버레이 공간 확보
        
        # 반투명 배경
        bg_rect = QRect(meter_x - 5, meter_y - 5, meter_width + 10, meter_height + 10)
        painter.fillRect(bg_rect, QColor(0, 0, 0, 120))
        
        # 미터 배경
        meter_rect = QRect(meter_x, meter_y, meter_width, meter_height)
        painter.fillRect(meter_rect, QColor(30, 30, 30, 200))
        
        # 데시벨 스케일 (-60 to 0 dB)
        painter.setPen(QColor(200, 200, 200, 200))
        font = QFont("Consolas", 8)
        painter.setFont(font)
        
        # 스케일 마크와 라벨
        db_marks = [0, -6, -12, -18, -24, -36, -48, -60]
        for db in db_marks:
            y_pos = meter_y + int(((-db) / 60.0) * meter_height)
            
            # 마크 라인
            if db == 0:
                painter.setPen(QPen(QColor(255, 100, 100, 200), 2))
            elif db == -6:
                painter.setPen(QPen(QColor(255, 200, 100, 200), 1))
            else:
                painter.setPen(QPen(QColor(150, 150, 150, 150), 1))
                
            painter.drawLine(meter_x - 3, y_pos, meter_x + meter_width + 3, y_pos)
            
            # 라벨
            painter.setPen(QColor(200, 200, 200, 200))
            label_rect = QRect(meter_x - 35, y_pos - 8, 30, 16)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{db}")
        
        # 현재 오디오 레벨 (평균값 계산)
        avg_level = sum(self.audio_history[-5:]) / 5  # 최근 5개 샘플 평균
        level_height = int(((avg_level + 60) / 60.0) * meter_height)
        level_height = max(0, min(level_height, meter_height))
        
        # 레벨 바 그리기 (그라디언트)
        if level_height > 0:
            level_rect = QRect(meter_x + 3, meter_y + meter_height - level_height, 
                             meter_width - 6, level_height)  # 좌우 여백도 조정
            
            # 색상 결정 (레벨에 따라)
            if avg_level > -6:
                # 빨간색 (클리핑 경고)
                color_bottom = QColor(255, 50, 50, 200)
                color_top = QColor(255, 100, 100, 200)
            elif avg_level > -12:
                # 노란색 (높은 레벨)
                color_bottom = QColor(200, 180, 0, 200)
                color_top = QColor(255, 230, 0, 200)
            else:
                # 초록색 (정상 레벨)
                color_bottom = QColor(0, 150, 0, 200)
                color_top = QColor(0, 255, 100, 200)
                
            # 채우기
            painter.fillRect(level_rect, color_bottom)
            
        # 피크 홀드 라인
        if self.audio_peak > -60:
            peak_y = meter_y + meter_height - int(((self.audio_peak + 60) / 60.0) * meter_height)
            painter.setPen(QPen(QColor(255, 255, 255, 250), 2))
            painter.drawLine(meter_x + 3, peak_y, meter_x + meter_width - 3, peak_y)
            
        # 미터 테두리
        painter.setPen(QPen(QColor(100, 100, 100, 200), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(meter_rect)
        
    def update_frame(self, frame: QImage):
        """Update video frame"""
        if frame and not frame.isNull():
            self.current_frame = frame
            self.update()
            
    def set_source(self, source_name: str):
        """Set current source name"""
        self.source_name = source_name
        self.update()
        
    def set_connected(self, connected: bool):
        """Set connection status"""
        self.is_connected = connected
        if not connected:
            self.current_frame = None
        self.update()
        
    def set_tally_state(self, state: str):
        """Set tally state: PGM, PVW, or empty string"""
        self.tally_state = state
        self.update()
        
    def update_frame_info(self, info: dict):
        """Update frame information"""
        self.frame_info.update(info)
        
        # Update audio history for smooth meter
        if 'audio_level' in info:
            level = info['audio_level']
            self.audio_history.pop(0)
            self.audio_history.append(level)
            
            # Update peak hold
            if level > self.audio_peak:
                self.audio_peak = level
            else:
                # Peak decay
                self.audio_peak = max(self.audio_peak - 0.5, level)
        
        self.update()
        
    def toggle_safe_areas(self):
        """Toggle safe area display"""
        self.show_safe_areas = not self.show_safe_areas
        self.update()
        
    def toggle_info_overlay(self):
        """Toggle info overlay display"""
        self.show_info_overlay = not self.show_info_overlay
        self.update()
        
    def toggle_audio_meter(self):
        """Toggle audio meter display"""
        self.show_audio_meter = not self.show_audio_meter
        self.update()
        
    def clear_display(self):
        """Clear the display"""
        self.current_frame = None
        self.is_connected = False
        self.audio_history = [-60.0] * 20
        self.audio_peak = -60.0
        self.update()
        
    @pyqtProperty(float)
    def fadeOpacity(self):
        """페이드 투 블랙 불투명도 속성"""
        return self._fade_opacity
        
    @fadeOpacity.setter
    def fadeOpacity(self, value):
        """페이드 투 블랙 불투명도 설정"""
        self._fade_opacity = value
        self.update()
        
    def set_streaming_mode(self, is_streaming: bool):
        """SRT 스트리밍 모드 설정 - 스트리밍 중일 때 프리뷰 중지"""
        self.is_streaming = is_streaming
        
        # 페이드 애니메이션 실행
        if is_streaming:
            # 페이드 투 블랙
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.finished.connect(self._on_fade_to_black_complete)
            self.fade_animation.start()
        else:
            # 페이드 인 (블랙에서 비디오로)
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.start()
            
    def _on_fade_to_black_complete(self):
        """페이드 투 블랙 완료 시 프레임 업데이트 중지"""
        if self.is_streaming:
            self.current_frame = None
            self.update()