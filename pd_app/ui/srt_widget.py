# pd_app/ui/srt_widget.py
"""
SRT Widget - SRT 스트리밍 제어 UI
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QLineEdit, QGroupBox,
    QTextEdit, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer

class SRTWidget(QWidget):
    """SRT 스트리밍 위젯"""
    
    def __init__(self, srt_manager, auth_manager):
        super().__init__()
        self.srt_manager = srt_manager
        self.auth_manager = auth_manager
        self.init_ui()
        self.init_connections()
        
        # 타이머 설정
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(5000)  # 5초마다 통계 업데이트
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 소스 선택 그룹
        source_group = QGroupBox("스트리밍 소스")
        source_layout = QVBoxLayout()
        
        # 소스 타입 선택
        source_type_layout = QHBoxLayout()
        source_type_layout.addWidget(QLabel("소스 타입:"))
        
        self.source_type_combo = QComboBox()
        self.source_type_combo.addItems(["NDI", "화면 캡처", "웹캠"])
        source_type_layout.addWidget(self.source_type_combo)
        
        source_type_layout.addStretch()
        source_layout.addLayout(source_type_layout)
        
        # NDI 소스 선택 (NDI 타입 선택 시에만 표시)
        self.ndi_source_layout = QHBoxLayout()
        self.ndi_source_layout.addWidget(QLabel("NDI 소스:"))
        
        self.ndi_source_combo = QComboBox()
        self.ndi_source_combo.addItem("NDI 소스를 선택하세요")
        self.ndi_source_layout.addWidget(self.ndi_source_combo)
        
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
        stream_name_layout.addWidget(self.generate_name_button)
        
        settings_layout.addLayout(stream_name_layout)
        
        # 비트레이트 설정
        bitrate_layout = QHBoxLayout()
        bitrate_layout.addWidget(QLabel("비트레이트:"))
        
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["500K", "1M", "2M", "3M", "5M"])
        self.bitrate_combo.setCurrentText("2M")
        bitrate_layout.addWidget(self.bitrate_combo)
        
        # FPS 설정 (화면 캡처용)
        bitrate_layout.addWidget(QLabel("FPS:"))
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(30)
        self.fps_spin.setEnabled(False)  # 화면 캡처 시에만 활성화
        bitrate_layout.addWidget(self.fps_spin)
        
        bitrate_layout.addStretch()
        settings_layout.addLayout(bitrate_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 스트리밍 제어
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("스트리밍 시작")
        self.start_button.setMinimumHeight(40)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("스트리밍 중지")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        layout.addLayout(control_layout)
        
        # 상태 표시
        status_group = QGroupBox("스트리밍 상태")
        status_layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        status_layout.addWidget(self.status_text)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        
    def init_connections(self):
        """시그널 연결"""
        # SRT 관리자 시그널
        self.srt_manager.stream_status_changed.connect(self.on_stream_status_changed)
        self.srt_manager.stream_error.connect(self.on_stream_error)
        self.srt_manager.stream_stats_updated.connect(self.on_stream_stats_updated)
        
        # UI 시그널
        self.source_type_combo.currentTextChanged.connect(self.on_source_type_changed)
        self.generate_name_button.clicked.connect(self.generate_stream_name)
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)
        
    def on_source_type_changed(self, source_type):
        """소스 타입 변경"""
        if source_type == "NDI":
            self.ndi_source_combo.setVisible(True)
            self.fps_spin.setEnabled(False)
            # NDI 소스 목록 업데이트 필요
            self.update_ndi_sources()
        else:
            self.ndi_source_combo.setVisible(False)
            self.fps_spin.setEnabled(source_type == "화면 캡처")
            
    def update_ndi_sources(self):
        """NDI 소스 목록 업데이트"""
        # TODO: NDI 관리자에서 소스 목록 가져오기
        pass
        
    def generate_stream_name(self):
        """스트림 이름 자동 생성"""
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            stream_name = self.srt_manager.generate_stream_key(
                user_info['user_id'],
                user_info['unique_address']
            )
            self.stream_name_input.setText(stream_name)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "로그인 필요", "스트림 이름 생성을 위해 로그인이 필요합니다.")
            
    def start_streaming(self):
        """스트리밍 시작"""
        # 스트림 이름 확인
        stream_name = self.stream_name_input.text().strip()
        if not stream_name:
            self.generate_stream_name()
            stream_name = self.stream_name_input.text().strip()
            
        if not stream_name:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "입력 오류", "스트림 이름을 입력하세요.")
            return
            
        # 소스 타입에 따른 스트리밍 시작
        source_type = self.source_type_combo.currentText()
        bitrate = self.bitrate_combo.currentText()
        
        try:
            if source_type == "NDI":
                ndi_source = self.ndi_source_combo.currentText()
                if ndi_source and ndi_source != "NDI 소스를 선택하세요":
                    self.srt_manager.start_ndi_streaming(ndi_source, stream_name, bitrate)
                else:
                    raise ValueError("NDI 소스를 선택하세요")
                    
            elif source_type == "화면 캡처":
                fps = self.fps_spin.value()
                self.srt_manager.start_screen_streaming(stream_name, bitrate, fps)
                
            elif source_type == "웹캠":
                # TODO: 웹캠 스트리밍 구현
                raise NotImplementedError("웹캠 스트리밍은 아직 구현되지 않았습니다")
                
            # UI 상태 업데이트
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.source_type_combo.setEnabled(False)
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "스트리밍 실패", str(e))
            
    def stop_streaming(self):
        """스트리밍 중지"""
        self.srt_manager.stop_streaming()
        
        # UI 상태 업데이트
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.source_type_combo.setEnabled(True)
        
    def on_stream_status_changed(self, status):
        """스트림 상태 변경"""
        self.append_status(f"상태: {status}")
        
    def on_stream_error(self, error):
        """스트림 오류"""
        self.append_status(f"오류: {error}")
        
    def on_stream_stats_updated(self, stats):
        """스트림 통계 업데이트"""
        active_streams = stats.get('items', [])
        if active_streams:
            self.append_status(f"활성 스트림: {len(active_streams)}개")
            
    def append_status(self, message):
        """상태 메시지 추가"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
    def update_stats(self):
        """통계 업데이트"""
        if self.srt_manager.is_streaming:
            stream_info = self.srt_manager.get_stream_info()
            self.append_status(f"스트리밍 중: {stream_info['stream_name']}")