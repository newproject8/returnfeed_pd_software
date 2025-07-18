# srt_widget.py
"""
SRT Widget - SRT 스트리밍 제어 UI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QLineEdit, QGroupBox,
    QTextEdit, QSpinBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
import logging


class SRTWidget(QWidget):
    """SRT 스트리밍 위젯"""
    
    # 시그널
    start_streaming_requested = pyqtSignal(str, str, str, int)  # ndi_source, stream_name, bitrate, fps
    stop_streaming_requested = pyqtSignal()
    
    def __init__(self, srt_module):
        super().__init__()
        self.srt_module = srt_module
        self.logger = logging.getLogger("SRTWidget")
        self.auto_resume_preview = True
        self.init_ui()
        self.init_connections()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 타이틀
        title_label = QLabel("리턴피드 스트림 (MediaMTX)")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 소스 선택 그룹
        source_group = QGroupBox("스트리밍 소스")
        source_layout = QVBoxLayout()
        
        # 소스 타입 선택
        source_type_layout = QHBoxLayout()
        source_type_layout.addWidget(QLabel("소스 타입:"))
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["NDI", "화면 캡처"])
        self.source_type_combo.setCurrentText("NDI")
        source_type_layout.addWidget(self.source_type_combo)
        
        source_type_layout.addStretch()
        source_layout.addLayout(source_type_layout)
        
        # NDI 소스 선택
        self.ndi_source_layout = QHBoxLayout()
        self.ndi_source_layout.addWidget(QLabel("NDI 소스:"))
        
        self.ndi_source_combo = QComboBox()
        self.ndi_source_combo.setMinimumWidth(300)
        self.ndi_source_combo.addItem("NDI 소스를 선택하세요")
        self.ndi_source_layout.addWidget(self.ndi_source_combo)
        
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.setMaximumWidth(80)
        self.ndi_source_layout.addWidget(self.refresh_button)
        
        source_layout.addLayout(self.ndi_source_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # 스트리밍 설정 그룹
        settings_group = QGroupBox("스트리밍 설정")
        settings_layout = QVBoxLayout()
        
        # 스트림 이름
        stream_name_layout = QHBoxLayout()
        stream_name_layout.addWidget(QLabel("스트림 이름:"))
        
        self.stream_name_input = QLineEdit()
        self.stream_name_input.setPlaceholderText("자동 생성됨")
        stream_name_layout.addWidget(self.stream_name_input)
        
        self.generate_name_button = QPushButton("자동 생성")
        self.generate_name_button.setMaximumWidth(80)
        stream_name_layout.addWidget(self.generate_name_button)
        
        settings_layout.addLayout(stream_name_layout)
        
        # 비트레이트 및 FPS 설정
        quality_layout = QHBoxLayout()
        
        quality_layout.addWidget(QLabel("비트레이트:"))
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["500K", "1M", "2M", "3M", "5M", "8M"])
        self.bitrate_combo.setCurrentText("2M")
        self.bitrate_combo.setMinimumWidth(80)
        quality_layout.addWidget(self.bitrate_combo)
        
        quality_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(30)
        self.fps_spin.setSingleStep(5)
        quality_layout.addWidget(self.fps_spin)
        
        quality_layout.addStretch()
        settings_layout.addLayout(quality_layout)
        
        # 프리뷰 재개 옵션
        self.auto_resume_checkbox = QCheckBox("스트리밍 종료 시 NDI 프리뷰 자동 재개")
        self.auto_resume_checkbox.setChecked(True)
        settings_layout.addWidget(self.auto_resume_checkbox)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 스트리밍 제어
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🔴 스트리밍 시작")
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⬛ 스트리밍 중지")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
        
        # 상태 표시
        status_group = QGroupBox("스트리밍 상태")
        status_layout = QVBoxLayout()
        
        # 현재 상태
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        status_layout.addWidget(self.status_label)
        
        # 통계 정보
        stats_layout = QHBoxLayout()
        
        self.bitrate_label = QLabel("비트레이트: 0 kb/s")
        stats_layout.addWidget(self.bitrate_label)
        
        self.fps_label = QLabel("FPS: 0")
        stats_layout.addWidget(self.fps_label)
        
        self.time_label = QLabel("시간: 00:00:00")
        stats_layout.addWidget(self.time_label)
        
        stats_layout.addStretch()
        status_layout.addLayout(stats_layout)
        
        # 로그 표시
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("background-color: #2c3e50; color: #ecf0f1; font-family: monospace;")
        status_layout.addWidget(self.log_text)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def init_connections(self):
        """시그널 연결"""
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.refresh_button.clicked.connect(self.refresh_ndi_sources)
        self.generate_name_button.clicked.connect(self.generate_stream_name)
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)
        self.auto_resume_checkbox.toggled.connect(self.on_auto_resume_changed)
        
    def on_source_type_changed(self, source_type):
        """소스 타입 변경"""
        is_ndi = source_type == "NDI"
        self.ndi_source_combo.setVisible(is_ndi)
        self.refresh_button.setVisible(is_ndi)
        
        # 화면 캡처일 때는 FPS 조정 가능
        self.fps_spin.setEnabled(not is_ndi)
        if is_ndi:
            self.fps_spin.setValue(30)  # NDI는 기본 30fps
            
    def refresh_ndi_sources(self):
        """NDI 소스 목록 새로고침 요청"""
        self.log_message("NDI 소스 목록 새로고침 중...")
        self.srt_module.request_ndi_sources.emit()
        
    def update_ndi_sources(self, sources: list):
        """NDI 소스 목록 업데이트"""
        current_text = self.ndi_source_combo.currentText()
        self.ndi_source_combo.clear()
        
        if sources:
            self.ndi_source_combo.addItems(sources)
            # 이전 선택 유지
            if current_text in sources:
                self.ndi_source_combo.setCurrentText(current_text)
            self.log_message(f"{len(sources)}개의 NDI 소스를 찾았습니다")
        else:
            self.ndi_source_combo.addItem("NDI 소스를 찾을 수 없습니다")
            self.log_message("NDI 소스를 찾을 수 없습니다")
            
    def generate_stream_name(self):
        """스트림 이름 자동 생성"""
        stream_name = self.srt_module.srt_manager.generate_stream_key("ndi_stream")
        self.stream_name_input.setText(stream_name)
        self.log_message(f"스트림 이름 생성: {stream_name}")
        
    def start_streaming(self):
        """스트리밍 시작"""
        try:
            source_type = self.source_type_combo.currentText()
            
            if source_type == "NDI":
                ndi_source = self.ndi_source_combo.currentText()
                if not ndi_source or ndi_source.startswith("NDI 소스"):
                    QMessageBox.warning(self, "경고", "NDI 소스를 선택하세요")
                    return
            else:
                ndi_source = "SCREEN_CAPTURE"
            
            stream_name = self.stream_name_input.text().strip()
            if not stream_name:
                self.generate_stream_name()
                stream_name = self.stream_name_input.text().strip()
                
            bitrate = self.bitrate_combo.currentText()
            fps = self.fps_spin.value()
            
            # UI 상태 변경
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.source_type_combo.setEnabled(False)
            self.ndi_source_combo.setEnabled(False)
            self.bitrate_combo.setEnabled(False)
            self.fps_spin.setEnabled(False)
            
            # 스트리밍 시작
            if source_type == "NDI":
                self.srt_module.start_streaming(ndi_source, stream_name, bitrate, fps)
            else:
                self.srt_module.srt_manager.start_screen_streaming(stream_name, bitrate, fps)
                
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            QMessageBox.critical(self, "오류", f"스트리밍 시작 실패: {str(e)}")
            self.reset_ui_state()
            
    def stop_streaming(self):
        """스트리밍 중지"""
        self.srt_module.stop_streaming()
        self.reset_ui_state()
        
    def reset_ui_state(self):
        """UI 상태 초기화"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_type_combo.setEnabled(True)
        self.ndi_source_combo.setEnabled(True)
        self.bitrate_combo.setEnabled(True)
        self.on_source_type_changed(self.source_type_combo.currentText())
        
    def update_status(self, status: str):
        """상태 업데이트"""
        self.status_label.setText(status)
        self.log_message(status)
        
        # 상태에 따른 색상 변경
        if "시작" in status:
            self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        elif "중지" in status:
            self.status_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        elif "오류" in status:
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            
    def update_stats(self, stats: dict):
        """통계 업데이트"""
        if 'bitrate' in stats:
            self.bitrate_label.setText(f"비트레이트: {stats['bitrate']}")
        if 'fps' in stats:
            self.fps_label.setText(f"FPS: {stats['fps']}")
        if 'time' in stats:
            self.time_label.setText(f"시간: {stats['time']}")
            
    def update_stream_info(self, info: dict):
        """스트림 정보 업데이트"""
        if info.get('is_streaming'):
            stats = info.get('stats', {})
            self.update_stats(stats)
            
    def on_auto_resume_changed(self, checked: bool):
        """프리뷰 자동 재개 설정 변경"""
        self.auto_resume_preview = checked
        
    def log_message(self, message: str):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 스크롤을 맨 아래로
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def get_bitrate(self) -> str:
        """현재 비트레이트 설정 반환"""
        return self.bitrate_combo.currentText()
        
    def set_bitrate(self, bitrate: str):
        """비트레이트 설정"""
        if bitrate in [self.bitrate_combo.itemText(i) for i in range(self.bitrate_combo.count())]:
            self.bitrate_combo.setCurrentText(bitrate)
            
    def get_fps(self) -> int:
        """현재 FPS 설정 반환"""
        return self.fps_spin.value()
        
    def set_fps(self, fps: int):
        """FPS 설정"""
        self.fps_spin.setValue(fps)