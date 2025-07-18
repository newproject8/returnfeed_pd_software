# ndi_widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QGroupBox, QPushButton, QLabel, QListWidgetItem, QSplitter,
                            QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QRect
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QColor
from PyQt6.QtMultimedia import QVideoSink, QVideoFrame
from typing import Optional, List, Dict
import numpy as np


class VideoDisplayWidget(QWidget):
    """🚀 ULTRATHINK: QPainter 직접 렌더링 기반 비디오 위젯 - 문서 기반 완전 안정화"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        # 위젯 크기는 자유롭게, 이미지만 16:9 비율 유지
        self.setMinimumSize(320, 180)  # 최소 크기만 설정
        self.base_width = 640
        self.base_height = 360
        
        # 배경 스타일 설정
        self.setStyleSheet(
            "VideoDisplayWidget { "
            "background-color: #2a2a2a; "
            "border: 2px solid #555; "
            "border-radius: 5px; "
            "}"
        )
        
        # **🚀 ULTRATHINK 핵심**: QPainter 직접 렌더링 구조
        # QVideoSink 완전 배제 - 블랙박스 우회
        self.current_qimage = None  # 현재 표시할 QImage
        self.no_source_text = "No NDI Source\nSelect a source from the list"
        self.technical_info = None  # Technical info dict from NDI receiver
        
        # SRT 스트리밍 상태 관리
        self.is_srt_streaming = False
        self.srt_stream_name = ""
        self.srt_stats = {}
        
        # Tally 상태 관리
        self.tally_state = ""  # "PGM", "PVW", or ""
        
        # 렌더링 최적화를 위한 속성 설정
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # 불투명 페인트 이벤트
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)  # 시스템 배경 비활성화
        
        # 레거시 호환성을 위한 더미 video_sink (기존 코드와의 호환성)
        self.video_sink = None
        
    def resizeEvent(self, event):
        """크기 변경 시 위젯은 자유롭게 변경, 이미지만 16:9 유지"""
        super().resizeEvent(event)
        # 단순히 다시 그리기만 요청
        self.update()
    
    def sizeHint(self):
        """기본 크기 힌트 - 16:9 비율"""
        return QSize(self.base_width, self.base_height)
    
    def paintEvent(self, event):
        """🚀 ULTRATHINK 핵심: QPainter 직접 렌더링 - 메인 GUI 스레드에서만 실행"""
        painter = QPainter(self)
        try:
            # 안티에일리어싱 활성화
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # 배경 그리기
            painter.fillRect(self.rect(), Qt.GlobalColor.black)
            
            if self.current_qimage and not self.current_qimage.isNull():
                # 비디오 프레임이 있을 때 - QImage를 직접 그리기
                widget_rect = self.rect()
                widget_width = widget_rect.width()
                widget_height = widget_rect.height()
                
                # 🚀 ULTRATHINK: 16:9 비율을 완벽하게 유지하는 로직
                # 1단계: 위젯 내에서 16:9 비율의 최대 크기 계산
                target_width = widget_width
                target_height = int(target_width * 9 / 16)
                
                if target_height > widget_height:
                    # 높이가 초과하면 높이 기준으로 재계산
                    target_height = widget_height
                    target_width = int(target_height * 16 / 9)
                
                # 2단계: 16:9 영역을 위젯 중앙에 배치
                target_x = (widget_width - target_width) // 2
                target_y = (widget_height - target_height) // 2
                
                # 3단계: 16:9 비율의 검은색 배경 그리기
                black_rect = QRect(target_x, target_y, target_width, target_height)
                painter.fillRect(black_rect, Qt.GlobalColor.black)
                
                # 4단계: 원본 이미지를 16:9 영역에 맞춰 그리기
                # 원본 이미지가 16:9가 아닐 경우 레터박스/필라박스 적용
                image_size = self.current_qimage.size()
                image_width = image_size.width()
                image_height = image_size.height()
                
                # 이미지를 16:9 영역에 맞춰 스케일링 (원본 비율 유지)
                scale_x = target_width / image_width
                scale_y = target_height / image_height
                scale = min(scale_x, scale_y)  # 작은 쪽에 맞춰서 전체가 보이도록
                
                scaled_width = int(image_width * scale)
                scaled_height = int(image_height * scale)
                
                # 스케일된 이미지를 16:9 영역 중앙에 배치
                image_x = target_x + (target_width - scaled_width) // 2
                image_y = target_y + (target_height - scaled_height) // 2
                
                image_rect = QRect(image_x, image_y, scaled_width, scaled_height)
                
                # QImage를 위젯에 직접 그리기
                painter.drawImage(image_rect, self.current_qimage)
                
                # Display technical info overlay if available
                if hasattr(self, 'technical_info') and self.technical_info:
                    self._draw_technical_info(painter, black_rect)
                
            else:
                # 비디오 프레임이 없을 때 - 텍스트 표시
                painter.setPen(Qt.GlobalColor.gray)
                font = painter.font()
                font.setPointSize(12)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.no_source_text)
            
            # SRT 스트리밍 중 오버레이 표시
            if self.is_srt_streaming:
                self._draw_srt_overlay(painter)
            
            # Tally 상태 표시
            if self.tally_state and self.current_qimage:
                self._draw_tally_border(painter)
                
        except Exception as e:
            print(f"Paint event error: {e}")
        finally:
            painter.end()
    
    def updateFrame(self, frame_data):
        """🚀 ULTRATHINK: 작업자 스레드로부터 프레임 수신 - 스레드 안전"""
        # NDI 스레드로부터 QImage 또는 dict를 받아 저장하고, 다시 그리도록 요청
        if isinstance(frame_data, QImage):
            # Legacy support - just QImage
            if frame_data and not frame_data.isNull():
                self.current_qimage = frame_data
                self.technical_info = None
                # 메인 GUI 스레드에서 paintEvent 실행 요청
                self.update()
        elif isinstance(frame_data, dict) and 'image' in frame_data:
            # New format - dict with image and technical info
            qimage = frame_data['image']
            if qimage and not qimage.isNull():
                self.current_qimage = qimage
                self.technical_info = frame_data
                # 메인 GUI 스레드에서 paintEvent 실행 요청
                self.update()
    
    def display_frame(self, frame_data):
        """레거시 호환성을 위한 프레임 표시"""
        self.updateFrame(frame_data)
    
    def get_video_sink(self) -> Optional[QVideoSink]:
        """레거시 호환성을 위한 더미 메서드 - 실제로는 None 반환"""
        return None
        
    def clear_display(self):
        """화면 지우기"""
        self.current_qimage = None
        self.update()  # paintEvent를 통해 "No NDI Source" 텍스트 표시
    
    def _draw_srt_overlay(self, painter):
        """SRT 스트리밍 중 오버레이 그리기"""
        # 반투명 검은 배경
        overlay_rect = self.rect()
        painter.fillRect(overlay_rect, QColor(0, 0, 0, 180))  # 70% 불투명도
        
        # 빨간 원과 REC 텍스트
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(220, 20, 60))  # Crimson red
        
        # 원 위치 계산
        circle_radius = 8
        circle_x = overlay_rect.width() - 100
        circle_y = 30
        painter.drawEllipse(circle_x, circle_y, circle_radius * 2, circle_radius * 2)
        
        # REC 텍스트
        painter.setPen(QColor(255, 255, 255))  # White color
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(circle_x + 25, circle_y + 12, "REC")
        
        # 메인 텍스트
        font.setPointSize(24)
        painter.setFont(font)
        painter.drawText(overlay_rect, Qt.AlignCenter, f"리턴피드 스트림 중\n{self.srt_stream_name}")
        
        # 통계 정보
        if self.srt_stats:
            font.setPointSize(12)
            font.setBold(False)
            painter.setFont(font)
            
            stats_text = []
            if 'bitrate' in self.srt_stats:
                stats_text.append(f"비트레이트: {self.srt_stats['bitrate']}")
            if 'fps' in self.srt_stats:
                stats_text.append(f"FPS: {self.srt_stats['fps']}")
            if 'time' in self.srt_stats:
                stats_text.append(f"시간: {self.srt_stats['time']}")
            
            if stats_text:
                stats_y = overlay_rect.height() - 50
                painter.drawText(overlay_rect.adjusted(0, 0, 0, -30), 
                               Qt.AlignBottom | Qt.AlignHCenter, 
                               " | ".join(stats_text))
    
    def set_srt_streaming(self, is_streaming: bool, stream_name: str = "", stats: dict = None):
        """SRT 스트리밍 상태 설정"""
        self.is_srt_streaming = is_streaming
        self.srt_stream_name = stream_name
        if stats:
            self.srt_stats = stats
        self.update()
    
    def _draw_technical_info(self, painter, video_rect):
        """Draw technical information overlay"""
        if not self.technical_info:
            return
            
        # Semi-transparent background for info
        info_height = 30
        info_rect = QRect(video_rect.x(), video_rect.bottom() - info_height, 
                         video_rect.width(), info_height)
        painter.fillRect(info_rect, QColor(0, 0, 0, 180))
        
        # Prepare info text
        info_parts = []
        if 'resolution' in self.technical_info:
            info_parts.append(self.technical_info['resolution'])
        if 'fps' in self.technical_info:
            info_parts.append(f"{self.technical_info['fps']} fps")
        if 'bitrate' in self.technical_info:
            info_parts.append(self.technical_info['bitrate'])
        
        # Add bandwidth mode indicator
        mode = self.parent().parent().get_bandwidth_mode() if hasattr(self.parent().parent(), 'get_bandwidth_mode') else None
        if mode:
            mode_text = "Normal" if mode == "highest" else "Proxy"
            info_parts.append(f"[{mode_text}]")
        
        # Draw text
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        
        info_text = " | ".join(info_parts)
        painter.drawText(info_rect, Qt.AlignCenter, info_text)
    
    def _draw_tally_border(self, painter):
        """Draw tally state border"""
        if self.tally_state == "PGM":
            color = QColor(255, 55, 55)  # Red
            label = "PGM"
        elif self.tally_state == "PVW":
            color = QColor(0, 255, 55)   # Green
            label = "PVW"
        else:
            return
        
        # Draw thick border around the entire widget
        pen = QPen(color, 8)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(4, 4, -4, -4))
        
        # Draw tally label in top-left corner
        label_rect = QRect(20, 20, 80, 30)
        painter.fillRect(label_rect, color)
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)
    
    def set_tally_state(self, state: str):
        """Set tally state: PGM, PVW, or empty string"""
        self.tally_state = state
        self.update()


class NDIWidget(QWidget):
    """NDI 모듈 UI 위젯"""
    
    # 시그널
    refresh_requested = pyqtSignal()
    source_selected = pyqtSignal(str)  # source name
    source_connect_requested = pyqtSignal(str)  # source name for connection
    source_disconnect_requested = pyqtSignal()
    bandwidth_mode_changed = pyqtSignal(str)  # bandwidth mode (highest/lowest)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self.current_source = ""
        self.is_connected = False
        
    def _init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 타이틀 및 컨트롤
        header_layout = QHBoxLayout()
        
        title_label = QLabel("NDI Sources")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_requested)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        self.connect_button.setEnabled(False)
        
        # Bandwidth mode selector
        bandwidth_label = QLabel("Mode:")
        self.bandwidth_combo = QComboBox()
        self.bandwidth_combo.addItem("Normal (High Quality)", "highest")
        self.bandwidth_combo.addItem("Proxy (Low Bandwidth)", "lowest")
        self.bandwidth_combo.setCurrentIndex(0)
        self.bandwidth_combo.currentIndexChanged.connect(self._on_bandwidth_changed)
        self.bandwidth_combo.setToolTip("Normal: Full quality, higher bandwidth\nProxy: Reduced quality, lower bandwidth")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(bandwidth_label)
        header_layout.addWidget(self.bandwidth_combo)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.connect_button)
        
        layout.addLayout(header_layout)
        
        # 메인 스플리터 (소스 리스트 + 비디오)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 왼쪽: NDI 소스 리스트
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        sources_group = QGroupBox("Available NDI Sources")
        sources_layout = QVBoxLayout()
        
        self.sources_list = QListWidget()
        self.sources_list.itemClicked.connect(self._on_source_clicked)
        self.sources_list.itemDoubleClicked.connect(self._on_source_double_clicked)
        
        sources_layout.addWidget(self.sources_list)
        sources_group.setLayout(sources_layout)
        left_layout.addWidget(sources_group)
        
        # 소스 카운트
        self.count_label = QLabel("Sources found: 0")
        count_font = QFont()
        count_font.setPointSize(9)
        self.count_label.setFont(count_font)
        left_layout.addWidget(self.count_label)
        
        left_widget.setMaximumWidth(350)
        main_splitter.addWidget(left_widget)
        
        # 오른쪽: 비디오 디스플레이
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        video_group = QGroupBox("NDI Video Preview")
        video_layout = QVBoxLayout()
        
        self.video_display = VideoDisplayWidget()
        video_layout.addWidget(self.video_display)
        
        # 비디오 정보
        self.video_info = QLabel("No source connected")
        self.video_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_info.setStyleSheet("color: #666; padding: 5px;")
        video_layout.addWidget(self.video_info)
        
        video_group.setLayout(video_layout)
        right_layout.addWidget(video_group)
        
        main_splitter.addWidget(right_widget)
        
        # 스플리터 비율 설정 (1:2)
        main_splitter.setSizes([250, 500])
        layout.addWidget(main_splitter)
        
        # 상태 표시
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: Not initialized")
        status_font = QFont()
        status_font.setPointSize(9)
        self.status_label.setFont(status_font)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
    def _on_source_clicked(self, item: QListWidgetItem):
        """소스 클릭 처리"""
        if item:
            self.current_source = item.text()
            self.connect_button.setEnabled(True)
            self.source_selected.emit(item.text())
            
    def _on_source_double_clicked(self, item: QListWidgetItem):
        """소스 더블클릭 처리 - 자동 연결"""
        if item and not self.is_connected:
            self.current_source = item.text()
            self._connect_to_source()
            
    def _on_connect_clicked(self):
        """연결 버튼 클릭 처리"""
        if not self.is_connected:
            self._connect_to_source()
        else:
            self._disconnect_from_source()
            
    def _connect_to_source(self):
        """소스에 연결"""
        if self.current_source:
            self.source_connect_requested.emit(self.current_source)
            
    def _disconnect_from_source(self):
        """소스 연결 해제"""
        self.source_disconnect_requested.emit()
        
    def update_sources(self, sources: List[Dict[str, str]]):
        """NDI 소스 목록 업데이트"""
        self.sources_list.clear()
        
        for source in sources:
            name = source.get("name", "Unknown")
            address = source.get("address", "")
            
            # 리스트 아이템 생성
            item = QListWidgetItem(name)
            if address:
                item.setToolTip(f"Address: {address}")
                
            self.sources_list.addItem(item)
            
        # 카운트 업데이트
        self.count_label.setText(f"Sources found: {len(sources)}")
        
        # 현재 선택된 소스가 없어진 경우 처리
        if self.current_source and not any(s.get("name") == self.current_source for s in sources):
            self.current_source = ""
            self.connect_button.setEnabled(False)
        
    def update_status(self, status: str, message: str):
        """상태 표시 업데이트"""
        self.status_label.setText(f"Status: {message}")
        
        # 상태에 따른 색상 설정
        color_map = {
            "initialized": "green",
            "discovering": "orange",
            "error": "red",
            "stopped": "gray"
        }
        color = color_map.get(status, "black")
        self.status_label.setStyleSheet(f"color: {color};")
        
    def update_connection_status(self, connected: bool, source_name: str = ""):
        """연결 상태 업데이트"""
        self.is_connected = connected
        
        if connected:
            self.connect_button.setText("Disconnect")
            mode_text = "Normal" if self.get_bandwidth_mode() == "highest" else "Proxy"
            self.video_info.setText(f"Connected to: {source_name} ({mode_text} mode)")
            self.video_info.setStyleSheet("color: green; padding: 5px;")
        else:
            self.connect_button.setText("Connect")
            self.video_info.setText("No source connected")
            self.video_info.setStyleSheet("color: #666; padding: 5px;")
            self.video_display.clear_display()
            
        # 소스 리스트 활성화/비활성화
        self.sources_list.setEnabled(not connected)
        self.refresh_button.setEnabled(not connected)
        
    def display_frame(self, frame_data):
        """비디오 프레임 표시 - QImage 또는 dict 지원"""
        if isinstance(frame_data, QImage):
            # Legacy support - just QImage
            self.video_display.display_frame(frame_data)
        elif isinstance(frame_data, dict) and 'image' in frame_data:
            # New format - dict with image and technical info
            self.video_display.display_frame(frame_data['image'])
        
    def clear_sources(self):
        """소스 목록 클리어"""
        self.sources_list.clear()
        self.count_label.setText("Sources found: 0")
        self.current_source = ""
        self.connect_button.setEnabled(False)
        
    def set_enabled(self, enabled: bool):
        """위젯 활성화/비활성화"""
        if not self.is_connected:  # 연결 중이 아닐 때만 적용
            self.refresh_button.setEnabled(enabled)
            self.sources_list.setEnabled(enabled)
    
    def _on_bandwidth_changed(self, index: int):
        """Bandwidth mode changed handler"""
        mode = self.bandwidth_combo.currentData()
        if mode:
            self.bandwidth_mode_changed.emit(mode)
    
    def get_bandwidth_mode(self) -> str:
        """Get current bandwidth mode"""
        return self.bandwidth_combo.currentData()