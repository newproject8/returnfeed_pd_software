# pd_app/ui/ndi_widget_optimized.py
"""
NDI Widget - 성능 최적화 버전
GUI 응답성 개선을 위한 렌더링 최적화
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QRadioButton, QButtonGroup,
    QGraphicsView, QGraphicsScene
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
import logging

logger = logging.getLogger(__name__)

class OptimizedVideoWidget(QGraphicsView):
    """최적화된 비디오 표시 위젯"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 렌더링 최적화 설정
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        
        # 안티앨리어싱 비활성화 (성능 향상)
        from PyQt6.QtGui import QPainter
        self.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        # 배경색 설정
        self.setBackgroundBrush(Qt.GlobalColor.black)
        
        self.pixmap_item = None
        self.last_size = None
        
    def update_frame(self, frame):
        """프레임 업데이트 - 최적화된 렌더링"""
        try:
            if frame is None or not isinstance(frame, np.ndarray):
                return
            
            height, width = frame.shape[:2]
            
            # 크기가 변경된 경우에만 씬 재구성
            if self.last_size != (width, height):
                self.scene.clear()
                self.pixmap_item = None
                self.last_size = (width, height)
            
            # NumPy 배열을 QImage로 변환 (최적화)
            if frame.ndim == 3:
                if frame.shape[2] == 4:
                    # RGBA
                    format = QImage.Format.Format_RGBA8888
                elif frame.shape[2] == 3:
                    # RGB - BGR로 변환 필요
                    frame = frame[:, :, ::-1].copy()  # RGB to BGR
                    format = QImage.Format.Format_RGB888
                else:
                    return
            else:
                # Grayscale
                format = QImage.Format.Format_Grayscale8
            
            # QImage 생성 (복사 없이 직접 참조)
            bytes_per_line = frame.strides[0]
            qimage = QImage(frame.data, width, height, bytes_per_line, format)
            
            # QPixmap으로 변환
            pixmap = QPixmap.fromImage(qimage)
            
            # Scene에 추가 또는 업데이트
            if self.pixmap_item is None:
                self.pixmap_item = self.scene.addPixmap(pixmap)
                self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            else:
                self.pixmap_item.setPixmap(pixmap)
            
        except Exception as e:
            logger.error(f"프레임 렌더링 오류: {e}")

class NDIWidgetOptimized(QWidget):
    """최적화된 NDI 프리뷰 위젯"""
    
    def __init__(self, ndi_manager):
        super().__init__()
        self.ndi_manager = ndi_manager
        self.init_ui()
        self.init_connections()
        
        # 성능 모니터링
        self.fps_counter = 0
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps)
        self.fps_timer.start(1000)  # 1초마다 FPS 업데이트
        self.last_frame_time = 0
        
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
        
        # 품질 설정
        self.quality_label = QLabel("품질:")
        control_layout.addWidget(self.quality_label)
        
        self.high_quality_radio = QRadioButton("고품질")
        self.low_quality_radio = QRadioButton("저품질 (빠름)")
        self.low_quality_radio.setChecked(True)  # 기본값은 저품질
        
        quality_group = QButtonGroup()
        quality_group.addButton(self.high_quality_radio)
        quality_group.addButton(self.low_quality_radio)
        
        control_layout.addWidget(self.high_quality_radio)
        control_layout.addWidget(self.low_quality_radio)
        
        control_layout.addStretch()
        
        # 프리뷰 시작/중지 버튼
        self.preview_button = QPushButton("프리뷰 시작")
        self.preview_button.setEnabled(False)
        control_layout.addWidget(self.preview_button)
        
        layout.addLayout(control_layout)
        
        # 비디오 프리뷰 영역 (최적화된 위젯 사용)
        self.video_widget = OptimizedVideoWidget()
        self.video_widget.setMinimumHeight(400)
        layout.addWidget(self.video_widget)
        
        # 상태 표시 패널
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("상태: NDI 준비")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.fps_label = QLabel("FPS: 0")
        status_layout.addWidget(self.fps_label)
        
        self.latency_label = QLabel("지연: 0ms")
        status_layout.addWidget(self.latency_label)
        
        layout.addLayout(status_layout)
        
    def init_connections(self):
        """시그널 연결"""
        # NDI 관리자 시그널 (최적화된 버전)
        self.ndi_manager.sources_updated.connect(self.on_sources_updated)
        self.ndi_manager.frame_ready.connect(self.on_frame_received)
        self.ndi_manager.connection_status_changed.connect(self.on_status_changed)
        
        # UI 시그널
        self.search_button.clicked.connect(self.search_sources)
        self.source_combo.currentIndexChanged.connect(self.on_source_selected)
        self.preview_button.clicked.connect(self.toggle_preview)
        
    def search_sources(self):
        """NDI 소스 검색"""
        try:
            self.status_label.setText("상태: NDI 소스 검색 중...")
            self.status_label.setStyleSheet("color: blue;")
            self.search_button.setEnabled(False)
            
            # 기존 소스 목록 초기화
            self.source_combo.clear()
            self.source_combo.addItem("검색 중...")
            
            # NDI 소스 검색 시작
            success = self.ndi_manager.start_source_discovery()
            
            if not success:
                self.status_label.setText("상태: NDI 초기화 실패")
                self.status_label.setStyleSheet("color: red;")
                self.source_combo.clear()
                self.source_combo.addItem("NDI 초기화 실패")
            
            # 버튼 재활성화 타이머
            QTimer.singleShot(3000, lambda: self.search_button.setEnabled(True))
            
        except Exception as e:
            logger.error(f"NDI 소스 검색 오류: {e}")
            self.status_label.setText(f"상태: 검색 오류")
            self.status_label.setStyleSheet("color: red;")
            self.search_button.setEnabled(True)
        
    def on_sources_updated(self, sources):
        """NDI 소스 목록 업데이트"""
        self.source_combo.clear()
        
        if sources:
            self.source_combo.addItem("NDI 소스를 선택하세요")
            self.source_combo.addItems(sources)
            self.status_label.setText(f"상태: {len(sources)}개 소스 발견")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.source_combo.addItem("NDI 소스를 찾을 수 없습니다")
            self.status_label.setText("상태: NDI 소스 없음")
            self.status_label.setStyleSheet("color: orange;")
            
    def on_source_selected(self, index):
        """소스 선택 처리"""
        if index > 0:  # 첫 번째 항목은 "선택하세요" 메시지
            self.preview_button.setEnabled(True)
        else:
            self.preview_button.setEnabled(False)
            
    def toggle_preview(self):
        """프리뷰 시작/중지"""
        if self.preview_button.text() == "프리뷰 시작":
            source_name = self.source_combo.currentText()
            if source_name and source_name not in ["NDI 소스를 선택하세요", "NDI 소스를 찾을 수 없습니다"]:
                # 품질 설정 적용
                if self.high_quality_radio.isChecked():
                    # 고품질 설정 (필요시 NDI 매니저에 전달)
                    pass
                
                # 프리뷰 시작
                success = self.ndi_manager.start_preview(source_name)
                if success:
                    self.preview_button.setText("프리뷰 중지")
                    self.source_combo.setEnabled(False)
                    self.search_button.setEnabled(False)
                    self.high_quality_radio.setEnabled(False)
                    self.low_quality_radio.setEnabled(False)
                    
                    # FPS 카운터 리셋
                    self.fps_counter = 0
                else:
                    self.status_label.setText("상태: 프리뷰 시작 실패")
                    self.status_label.setStyleSheet("color: red;")
        else:
            # 프리뷰 중지
            self.ndi_manager.stop_preview()
            self.preview_button.setText("프리뷰 시작")
            self.source_combo.setEnabled(True)
            self.search_button.setEnabled(True)
            self.high_quality_radio.setEnabled(True)
            self.low_quality_radio.setEnabled(True)
            
            # 비디오 위젯 초기화
            self.video_widget.scene.clear()
            self.video_widget.pixmap_item = None
            
    def on_frame_received(self, frame):
        """프레임 수신 처리 - 최적화된 버전"""
        try:
            # FPS 카운터 증가
            self.fps_counter += 1
            
            # 지연시간 계산
            import time
            current_time = time.time()
            if self.last_frame_time > 0:
                latency = int((current_time - self.last_frame_time) * 1000)
                self.latency_label.setText(f"지연: {latency}ms")
            self.last_frame_time = current_time
            
            # 프레임 표시
            self.video_widget.update_frame(frame)
            
        except Exception as e:
            logger.error(f"프레임 처리 오류: {e}")
    
    def on_status_changed(self, status, color):
        """상태 변경 처리"""
        self.status_label.setText(f"상태: {status}")
        self.status_label.setStyleSheet(f"color: {color};")
    
    def _update_fps(self):
        """FPS 표시 업데이트"""
        self.fps_label.setText(f"FPS: {self.fps_counter}")
        self.fps_counter = 0
    
    def resizeEvent(self, event):
        """윈도우 크기 변경 시 비디오 스케일 조정"""
        super().resizeEvent(event)
        if self.video_widget.pixmap_item:
            self.video_widget.fitInView(
                self.video_widget.pixmap_item, 
                Qt.AspectRatioMode.KeepAspectRatio
            )