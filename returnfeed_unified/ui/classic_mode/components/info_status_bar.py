"""
Info Status Bar Component
최하단행 - 소스, 해상도, 비트레이트 등 정보 표시 전용
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ..styles.icons import PREMIERE_COLORS


class InfoStatusBar(QFrame):
    """정보 표시 전용 상태바 - 최하단행"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("InfoStatusBar")
        self.setFixedHeight(32)
        
        self._init_ui()
        self._setup_styles()
        
    def _init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 4, 15, 4)
        layout.setSpacing(15)
        
        # 기술 데이터용 폰트
        tech_font = QFont("Consolas", 9)
        
        # 소스 정보
        self.source_label = QLabel("소스: 연결 안됨")
        self.source_label.setFont(tech_font)
        self.source_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.source_label)
        
        # 구분선
        sep1 = QLabel("|")
        sep1.setStyleSheet(f"color: {PREMIERE_COLORS['border']};")
        layout.addWidget(sep1)
        
        # 해상도 및 FPS
        self.resolution_label = QLabel("해상도: --")
        self.resolution_label.setFont(tech_font)
        self.resolution_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.resolution_label)
        
        # 구분선
        sep2 = QLabel("|")
        sep2.setStyleSheet(f"color: {PREMIERE_COLORS['border']};")
        layout.addWidget(sep2)
        
        # 비트레이트
        self.bitrate_label = QLabel("비트레이트: --")
        self.bitrate_label.setFont(tech_font)
        self.bitrate_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.bitrate_label)
        
        # 구분선
        sep3 = QLabel("|")
        sep3.setStyleSheet(f"color: {PREMIERE_COLORS['border']};")
        layout.addWidget(sep3)
        
        # 오디오 레벨
        self.audio_label = QLabel("오디오: --")
        self.audio_label.setFont(tech_font)
        self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.audio_label)
        
        # Spacer
        layout.addStretch()
        
        # 성능 통계 - 고정 너비로 위치 고정
        perf_font = QFont("Consolas", 9)
        
        self.fps_label = QLabel("monitor fps: 0")
        self.fps_label.setFont(perf_font)
        self.fps_label.setStyleSheet(f"color: {PREMIERE_COLORS['success']};")
        self.fps_label.setFixedWidth(100)
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.fps_label)
        
        # 구분선
        sep4 = QLabel("|")
        sep4.setStyleSheet(f"color: {PREMIERE_COLORS['border']};")
        layout.addWidget(sep4)
        
        # CPU 사용률
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setFont(perf_font)
        self.cpu_label.setFixedWidth(80)
        self.cpu_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.cpu_label)
        
        # 구분선
        sep5 = QLabel("|")
        sep5.setStyleSheet(f"color: {PREMIERE_COLORS['border']};")
        layout.addWidget(sep5)
        
        # 메모리 사용량
        self.memory_label = QLabel("메모리: 0 MB")
        self.memory_label.setFont(perf_font)
        self.memory_label.setFixedWidth(100)
        self.memory_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.memory_label)
        
    def _setup_styles(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QFrame#InfoStatusBar {{
                background-color: {PREMIERE_COLORS['bg_darkest']};
                border-top: 1px solid {PREMIERE_COLORS['border']};
                border-left: none;
                border-right: none;
                border-bottom: none;
            }}
            
            QLabel {{
                color: {PREMIERE_COLORS['text_primary']};
                font-family: "Consolas";
                background: none;
                border: none;
            }}
        """)
        
    def update_source_info(self, source_name: str, connected: bool):
        """소스 정보 업데이트"""
        if connected and source_name:
            self.source_label.setText(f"소스: {source_name}")
            self.source_label.setStyleSheet(f"color: {PREMIERE_COLORS['success']};")
        else:
            self.source_label.setText("소스: 연결 안됨")
            self.source_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
            self.clear_technical_info()
            
    def update_technical_info(self, info: dict):
        """기술 정보 업데이트"""
        # 해상도 및 FPS
        if 'resolution' in info and 'fps' in info:
            self.resolution_label.setText(f"{info['resolution']} @ {info['fps']}fps")
        else:
            self.resolution_label.setText("해상도: --")
            
        # 비트레이트
        if 'bitrate' in info:
            self.bitrate_label.setText(f"비트레이트: {info['bitrate']}")
        else:
            self.bitrate_label.setText("비트레이트: --")
            
        # 오디오 레벨
        if 'audio_level' in info:
            level = info['audio_level']
            self.audio_label.setText(f"오디오: {level:.1f}dB")
            
            # 오디오 레벨에 따른 색상 변경
            if level > -6:
                self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['pgm_red']};")  # 너무 큼
            elif level > -20:
                self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['success']};")  # 적정
            elif level > -40:
                self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['warning']};")  # 낮음
            else:
                self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_disabled']};")  # 매우 낮음
        else:
            self.audio_label.setText("오디오: --")
            self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
            
    def clear_technical_info(self):
        """기술 정보 지우기"""
        self.resolution_label.setText("해상도: --")
        self.bitrate_label.setText("비트레이트: --")
        self.audio_label.setText("오디오: --")
        self.audio_label.setStyleSheet(f"color: {PREMIERE_COLORS['text_secondary']};")
        
    def update_performance_stats(self, fps: int, cpu: float, memory: int):
        """성능 통계 업데이트"""
        # FPS
        self.fps_label.setText(f"monitor fps: {fps}")
        if fps >= 55:
            self.fps_label.setStyleSheet(f"color: {PREMIERE_COLORS['success']};")
        elif fps >= 45:
            self.fps_label.setStyleSheet(f"color: {PREMIERE_COLORS['warning']};")
        else:
            self.fps_label.setStyleSheet(f"color: {PREMIERE_COLORS['error']};")
            
        # CPU
        self.cpu_label.setText(f"CPU: {cpu:.1f}%")
        if cpu < 50:
            self.cpu_label.setStyleSheet(f"color: {PREMIERE_COLORS['success']};")
        elif cpu < 75:
            self.cpu_label.setStyleSheet(f"color: {PREMIERE_COLORS['warning']};")
        else:
            self.cpu_label.setStyleSheet(f"color: {PREMIERE_COLORS['error']};")
            
        # 메모리
        self.memory_label.setText(f"메모리: {memory} MB")
        if memory < 500:
            self.memory_label.setStyleSheet(f"color: {PREMIERE_COLORS['success']};")
        elif memory < 1000:
            self.memory_label.setStyleSheet(f"color: {PREMIERE_COLORS['warning']};")
        else:
            self.memory_label.setStyleSheet(f"color: {PREMIERE_COLORS['error']};")