"""
Stream Control Panel Component
차하단행 - 리턴피드 스트리밍 컨트롤 전용
"""

from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QWidget, QLineEdit, QApplication, QToolTip)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QClipboard, QCursor
from ..styles.icons import get_icon, PREMIERE_COLORS
from .animated_button import AnimatedStreamingButton
import uuid
import random
import string


class ClickableUrlLabel(QLabel):
    """클릭 가능한 URL 라벨"""
    
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.is_streaming = False
        self._update_style()
        
    def _update_style(self):
        """스트리밍 상태에 따른 스타일 업데이트"""
        if self.is_streaming:
            # 스트리밍 중: 붉은 계통 컬러
            self.setStyleSheet("""
                QLabel {
                    color: #EF4444;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 4px;
                    border-radius: 3px;
                }
                QLabel:hover {
                    background-color: rgba(239, 68, 68, 0.1);
                    text-decoration: underline;
                }
            """)
        else:
            # 기본 상태: 옅은 회색
            self.setStyleSheet("""
                QLabel {
                    color: #9CA3AF;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 4px;
                    border-radius: 3px;
                }
                QLabel:hover {
                    background-color: rgba(156, 163, 175, 0.1);
                    text-decoration: underline;
                }
            """)
        
    def set_streaming(self, streaming: bool):
        """스트리밍 상태 설정"""
        self.is_streaming = streaming
        self._update_style()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StreamControlPanel(QFrame):
    """스트리밍 전용 컨트롤 패널 - 차하단행"""
    
    # Signals
    srt_start_clicked = pyqtSignal()
    srt_stop_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StreamControlPanel")
        self.setFixedHeight(50)  # 상단행과 동일한 높이
        
        # State
        self.is_srt_streaming = False
        
        # 고유 스트림 ID 생성 (더미 구현)
        self.stream_id = self._generate_stream_id()
        self.stream_url = f"https://returnfeed.stream/live/{self.stream_id}"
        
        self._init_ui()
        self._setup_styles()
        
    def _init_ui(self):
        """UI 초기화 - 극단적으로 간소화된 레이아웃"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)  # 상단행과 동일한 패딩
        layout.setSpacing(25)  # 상단행과 동일한 간격
        
        # 리턴피드 레이블 (고정 너비로 정렬)
        returnfeed_label = QLabel("리턴피드")
        returnfeed_label.setFixedWidth(80)  # NDI와 동일한 고정 너비
        returnfeed_label.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {PREMIERE_COLORS['text_primary']};
        """)
        layout.addWidget(returnfeed_label)
        
        # 구분선
        separator1 = QLabel("|")
        separator1.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator1)
        
        # 서버상태
        self.server_status = QLabel("● 연결됨")
        self.server_status.setStyleSheet(f"font-size: 13px; color: {PREMIERE_COLORS['success']}; font-weight: bold;")
        layout.addWidget(self.server_status)
        
        # 업타임과 클라이언트 수 (간소화된 표시)
        self.server_detail = QLabel("00:00:00 · 0명")
        self.server_detail.setStyleSheet(f"font-size: 11px; color: {PREMIERE_COLORS['text_secondary']};")
        layout.addWidget(self.server_detail)
        
        # 구분선
        separator2 = QLabel("|")
        separator2.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator2)
        
        # 스트리밍 버튼
        self.srt_button = AnimatedStreamingButton("스트리밍 시작")
        self.srt_button.setEnabled(False)
        self.srt_button.setFixedSize(100, 28)
        self.srt_button.clicked.connect(self._on_srt_clicked)
        self.srt_button.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
        """)
        layout.addWidget(self.srt_button)
        
        # 구분선
        separator3 = QLabel("|")
        separator3.setStyleSheet(f"color: {PREMIERE_COLORS['border']}; padding: 0px; margin: 0px;")
        layout.addWidget(separator3)
        
        # 고유 스트림 URL 표시 라벨 (클릭 가능)
        self.stream_url_label = ClickableUrlLabel(self.stream_url)
        self.stream_url_label.clicked.connect(self._on_url_clicked)
        self.stream_url_label.setMinimumWidth(520)  # URL 전체 표시를 위한 충분한 너비
        self.stream_url_label.setMaximumWidth(600)  # 최대 너비 증가
        self.stream_url_label.setFixedHeight(28)
        layout.addWidget(self.stream_url_label)
        
        # 복사 버튼
        self.copy_button = QPushButton("고유주소복사")
        self.copy_button.setFixedSize(100, 28)
        self.copy_button.clicked.connect(self._on_copy_url)
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PREMIERE_COLORS['bg_light']};
                color: {PREMIERE_COLORS['text_primary']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 3px;
                font-size: 11px;
                font-weight: 500;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {PREMIERE_COLORS['bg_lighter']};
                border-color: {PREMIERE_COLORS['border_light']};
            }}
            QPushButton:pressed {{
                background-color: {PREMIERE_COLORS['bg_medium']};
            }}
        """)
        layout.addWidget(self.copy_button)
        
        # 내부 상태 변수
        self.uptime = "00:00:00"
        self.client_count = 0
        
        # Spacer
        layout.addStretch()
        
    def _create_compact_group(self, label_text: str):
        """컴팩트 레이블|요소 그룹 생성"""
        group_layout = QHBoxLayout()
        group_layout.setSpacing(8)
        
        # 레이블
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            font-size: 10px; 
            font-weight: 600; 
            color: {PREMIERE_COLORS['text_primary']};
            min-width: 60px;
        """)
        group_layout.addWidget(label)
        
        return group_layout
        
    def _setup_styles(self):
        """스타일 설정"""
        self.setStyleSheet(f"""
            QFrame#StreamControlPanel {{
                background-color: {PREMIERE_COLORS['bg_dark']};
                border: none;
            }}
            
            QLabel {{
                color: {PREMIERE_COLORS['text_primary']};
                font-family: "Gmarket Sans";
            }}
        """)
        
    def _on_srt_clicked(self):
        """SRT 버튼 클릭 처리"""
        if self.is_srt_streaming:
            self.srt_stop_clicked.emit()
        else:
            self.srt_start_clicked.emit()
            
    def set_srt_streaming(self, streaming: bool, status: str = ""):
        """SRT 스트리밍 상태 업데이트"""
        self.is_srt_streaming = streaming
        
        # 애니메이션 버튼 상태 설정
        self.srt_button.set_streaming(streaming)
        
        # URL 라벨 색상 상태 설정
        self.stream_url_label.set_streaming(streaming)
        
        if streaming:
            self.srt_button.setText("스트리밍 중지")
        else:
            self.srt_button.setText("스트리밍 시작")
            
    def update_srt_status(self, status: str):
        """SRT 상태 텍스트 업데이트"""
        # 간소화된 UI에서는 별도 상태 표시 없음
        pass
            
    def set_streaming_enabled(self, enabled: bool):
        """스트리밍 버튼 활성화 상태 설정"""
        self.srt_button.setEnabled(enabled)
        
    def update_server_status(self, connected: bool, uptime: str = "", client_count: int = 0):
        """서버 상태 업데이트"""
        self.uptime = uptime or "00:00:00"
        self.client_count = client_count
        
        if connected:
            self.server_status.setText("● 연결됨")
            self.server_status.setStyleSheet(f"font-size: 13px; color: {PREMIERE_COLORS['success']}; font-weight: bold;")
        else:
            self.server_status.setText("● 연결 안됨")
            self.server_status.setStyleSheet(f"font-size: 13px; color: {PREMIERE_COLORS['error']}; font-weight: bold;")
            
        # 업타임과 클라이언트 수를 하나의 라벨로 표시
        self.server_detail.setText(f"{self.uptime} · {self.client_count}명")
        
    def update_uptime(self, uptime: str):
        """업타임 업데이트"""
        self.uptime = uptime
        self.server_detail.setText(f"{self.uptime} · {self.client_count}명")
        
    def update_client_count(self, count: int):
        """클라이언트 수 업데이트"""
        self.client_count = count
        self.server_detail.setText(f"{self.uptime} · {self.client_count}명")
        
    def _generate_stream_id(self) -> str:
        """고유 스트림 ID 생성 (더미 구현)"""
        # 사용자 친화적인 ID 생성: 6자리 대문자 + 3자리 숫자
        letters = ''.join(random.choices(string.ascii_uppercase, k=6))
        numbers = ''.join(random.choices(string.digits, k=3))
        return f"{letters}{numbers}"
        
    def _on_url_clicked(self):
        """URL 라벨 클릭 시 복사 처리"""
        self._copy_url_to_clipboard()
        
    def _on_copy_url(self):
        """URL 복사 버튼 클릭 처리"""
        self._copy_url_to_clipboard()
        
    def _copy_url_to_clipboard(self):
        """URL을 클립보드에 복사하는 공통 메서드"""
        try:
            # 클립보드에 URL 복사
            clipboard = QApplication.clipboard()
            clipboard.setText(self.stream_url)
            
            # URL 라벨 시각적 피드백 (복사 완료 시 녹색)
            self.stream_url_label.setStyleSheet("""
                QLabel {
                    color: #10B981;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 4px;
                    border-radius: 3px;
                    background-color: rgba(16, 185, 129, 0.1);
                }
            """)
            
            # 복사 완료 시각적 피드백
            self.copy_button.setText("복사됨!")
            self.copy_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PREMIERE_COLORS['success']};
                    color: white;
                    border: 1px solid {PREMIERE_COLORS['success']};
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 0px;
                }}
            """)
            
            # 툴팁 표시
            QToolTip.showText(self.copy_button.mapToGlobal(self.copy_button.rect().center()), 
                             "스트림 URL이 클립보드에 복사되었습니다!")
            
            # 2초 후 원래 상태로 복원
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, self._restore_copy_state)
            
        except Exception as e:
            print(f"URL 복사 중 오류 발생: {e}")
            
    def _restore_copy_state(self):
        """복사 상태를 원래대로 복원"""
        # URL 라벨을 스트리밍 상태에 맞는 원래 스타일로 복원
        self.stream_url_label._update_style()
        
        # 복사 버튼 원래 상태로 복원
        self.copy_button.setText("고유주소복사")
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {PREMIERE_COLORS['bg_light']};
                color: {PREMIERE_COLORS['text_primary']};
                border: 1px solid {PREMIERE_COLORS['border']};
                border-radius: 3px;
                font-size: 11px;
                font-weight: 500;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {PREMIERE_COLORS['bg_lighter']};
                border-color: {PREMIERE_COLORS['border_light']};
            }}
            QPushButton:pressed {{
                background-color: {PREMIERE_COLORS['bg_medium']};
            }}
        """)
        
    def regenerate_stream_id(self):
        """새로운 스트림 ID 생성 (필요시 사용)"""
        self.stream_id = self._generate_stream_id()
        self.stream_url = f"https://returnfeed.stream/live/{self.stream_id}"
        self.stream_url_label.setText(self.stream_url)