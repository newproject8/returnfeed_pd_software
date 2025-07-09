# pd_app/ui/main_window.py
"""
통합 메인 윈도우 - NDI, vMix Tally, SRT 스트리밍 통합 UI
"""

import sys
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QStatusBar, QLabel, QMessageBox,
    QMenuBar, QMenu, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

# 로컬 임포트
from ..core import NDIManager, VMixManager, SRTManager, AuthManager
from ..network import WebSocketClient
from .ndi_widget import NDIWidget
from .tally_widget import TallyWidget
from .srt_widget import SRTWidget
from .login_widget import LoginWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """통합 메인 윈도우"""
    
    # 시그널 정의
    window_closing = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 관리자 초기화
        self.ndi_manager = NDIManager()
        self.vmix_manager = VMixManager()
        self.srt_manager = SRTManager()
        self.auth_manager = AuthManager()
        self.ws_client = WebSocketClient()
        
        # UI 초기화
        self.init_ui()
        self.init_managers()
        self.init_connections()
        
        # 타이머 설정
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # 1초마다 상태 업데이트
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("PD 통합 소프트웨어 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 상단 정보 바
        self.create_info_bar(main_layout)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 탭 추가
        self.create_tabs()
        
        # 상태 바
        self.create_status_bar()
        
        # 메뉴 바
        self.create_menu_bar()
        
        # 툴바
        self.create_toolbar()
        
    def create_info_bar(self, layout):
        """상단 정보 바 생성"""
        info_layout = QHBoxLayout()
        
        # 로그인 상태
        self.login_status_label = QLabel("로그인: 안됨")
        info_layout.addWidget(self.login_status_label)
        
        # 고유 주소
        self.unique_address_label = QLabel("고유 주소: -")
        info_layout.addWidget(self.unique_address_label)
        
        info_layout.addStretch()
        
        # 서버 연결 상태
        self.server_status_label = QLabel("서버: 연결 안됨")
        info_layout.addWidget(self.server_status_label)
        
        layout.addLayout(info_layout)
        
    def create_tabs(self):
        """탭 생성"""
        # 메인 탭
        self.main_tab = self.create_main_tab()
        self.tab_widget.addTab(self.main_tab, "메인")
        
        # NDI 프리뷰 탭
        self.ndi_widget = NDIWidget(self.ndi_manager)
        self.tab_widget.addTab(self.ndi_widget, "NDI 프리뷰")
        
        # Tally 탭
        self.tally_widget = TallyWidget(self.vmix_manager)
        self.tab_widget.addTab(self.tally_widget, "vMix Tally")
        
        # SRT 스트리밍 탭
        self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
        self.tab_widget.addTab(self.srt_widget, "SRT 스트리밍")
        
        # 설정 탭
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "설정")
        
    def create_main_tab(self):
        """메인 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 메인 대시보드를 4분할로 구성
        grid_layout = QHBoxLayout()
        
        # 왼쪽 열
        left_column = QVBoxLayout()
        
        # NDI 프리뷰 미니 뷰
        ndi_preview = QLabel("NDI 프리뷰")
        ndi_preview.setMinimumHeight(200)
        ndi_preview.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        ndi_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_column.addWidget(ndi_preview)
        
        # Tally 상태 미니 뷰
        tally_status = QLabel("Tally 상태")
        tally_status.setMinimumHeight(200)
        tally_status.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        tally_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_column.addWidget(tally_status)
        
        # 오른쪽 열
        right_column = QVBoxLayout()
        
        # SRT 스트리밍 상태
        srt_status = QLabel("SRT 스트리밍 상태")
        srt_status.setMinimumHeight(200)
        srt_status.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        srt_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(srt_status)
        
        # 시스템 상태
        system_status = QLabel("시스템 상태")
        system_status.setMinimumHeight(200)
        system_status.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        system_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_column.addWidget(system_status)
        
        grid_layout.addLayout(left_column)
        grid_layout.addLayout(right_column)
        
        layout.addLayout(grid_layout)
        
        # 실제 위젯으로 교체할 예정
        self.main_ndi_preview = ndi_preview
        self.main_tally_status = tally_status
        self.main_srt_status = srt_status
        self.main_system_status = system_status
        
        return widget
        
    def create_settings_tab(self):
        """설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 로그인 위젯
        self.login_widget = LoginWidget(self.auth_manager)
        layout.addWidget(self.login_widget)
        
        layout.addStretch()
        
        return widget
        
    def create_status_bar(self):
        """상태 바 생성"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 상태 라벨들
        self.ndi_status = QLabel("NDI: 준비")
        self.vmix_status = QLabel("vMix: 연결 안됨")
        self.srt_status = QLabel("SRT: 중지")
        self.ws_status = QLabel("서버: 연결 안됨")
        
        self.status_bar.addWidget(self.ndi_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.vmix_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.srt_status)
        self.status_bar.addWidget(QLabel(" | "))
        self.status_bar.addWidget(self.ws_status)
        
    def create_menu_bar(self):
        """메뉴 바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu("도구")
        
        # NDI 재검색
        refresh_ndi = QAction("NDI 소스 재검색", self)
        refresh_ndi.triggered.connect(self.refresh_ndi_sources)
        tools_menu.addAction(refresh_ndi)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """툴바 생성"""
        toolbar = QToolBar("메인 툴바")
        self.addToolBar(toolbar)
        
        # NDI 프리뷰 토글
        ndi_toggle = QAction("NDI 프리뷰", self)
        ndi_toggle.setCheckable(True)
        toolbar.addAction(ndi_toggle)
        
        # Tally 토글
        tally_toggle = QAction("Tally 활성화", self)
        tally_toggle.setCheckable(True)
        toolbar.addAction(tally_toggle)
        
        # SRT 스트리밍 토글
        srt_toggle = QAction("SRT 스트리밍", self)
        srt_toggle.setCheckable(True)
        toolbar.addAction(srt_toggle)
        
    def init_managers(self):
        """관리자 초기화"""
        try:
            # NDI 초기화
            self.ndi_manager.initialize()
            
            # WebSocket 시작
            self.ws_client.start()
            
            logger.info("모든 관리자 초기화 완료")
            
        except Exception as e:
            logger.error(f"관리자 초기화 실패: {e}")
            QMessageBox.critical(self, "초기화 오류", f"시스템 초기화 실패:\n{e}")
            
    def init_connections(self):
        """시그널 연결"""
        # 인증 관리자
        self.auth_manager.login_success.connect(self.on_login_success)
        self.auth_manager.logout_success.connect(self.on_logout_success)
        
        # WebSocket
        self.ws_client.connection_status_changed.connect(self.on_ws_status_changed)
        
        # NDI 관리자
        self.ndi_manager.connection_status_changed.connect(self.on_ndi_status_changed)
        
        # vMix 관리자
        self.vmix_manager.connection_status_changed.connect(self.on_vmix_status_changed)
        self.vmix_manager.tally_updated.connect(self.on_tally_updated)
        
        # SRT 관리자
        self.srt_manager.stream_status_changed.connect(self.on_srt_status_changed)
        
    def on_login_success(self, user_info):
        """로그인 성공 처리"""
        self.login_status_label.setText(f"로그인: {user_info['username']}")
        self.unique_address_label.setText(f"고유 주소: {user_info['unique_address']}")
        
        # WebSocket에 인증 정보 전송
        self.ws_client.send_auth_info(user_info)
        
    def on_logout_success(self):
        """로그아웃 처리"""
        self.login_status_label.setText("로그인: 안됨")
        self.unique_address_label.setText("고유 주소: -")
        
    def on_ws_status_changed(self, status, color):
        """WebSocket 상태 변경"""
        self.server_status_label.setText(f"서버: {status}")
        self.server_status_label.setStyleSheet(f"color: {color};")
        self.ws_status.setText(f"서버: {status}")
        
    def on_ndi_status_changed(self, status, color):
        """NDI 상태 변경"""
        self.ndi_status.setText(f"NDI: {status}")
        
    def on_vmix_status_changed(self, status, color):
        """vMix 상태 변경"""
        self.vmix_status.setText(f"vMix: {status}")
        
    def on_tally_updated(self, pgm, pvw, pgm_info, pvw_info):
        """Tally 업데이트 처리"""
        # WebSocket으로 전송
        self.ws_client.send_tally_update(pgm, pvw)
        
        # 입력 목록도 함께 전송 (카메라맨들이 입력 이름을 알 수 있도록)
        input_list = self.vmix_manager.get_input_list()
        if input_list:
            self.ws_client.send_input_list(input_list)
        
    def on_srt_status_changed(self, status):
        """SRT 상태 변경"""
        self.srt_status.setText(f"SRT: {status}")
        
    def update_status(self):
        """주기적 상태 업데이트"""
        # 메인 탭 상태 업데이트
        if self.auth_manager.is_logged_in():
            user_info = self.auth_manager.get_user_info()
            status_text = f"사용자: {user_info['username']}\n"
            status_text += f"고유 주소: {user_info['unique_address']}\n"
            
            if self.srt_manager.is_streaming:
                stream_info = self.srt_manager.get_stream_info()
                status_text += f"스트리밍 중: {stream_info['stream_name']}"
            else:
                status_text += "스트리밍: 중지"
                
            self.main_system_status.setText(status_text)
            
    def refresh_ndi_sources(self):
        """NDI 소스 재검색"""
        self.ndi_manager.start_source_discovery()
        
    def show_about(self):
        """정보 대화상자"""
        QMessageBox.about(
            self,
            "PD 통합 소프트웨어",
            "PD 통합 소프트웨어 v1.0\n\n"
            "NDI 프리뷰, vMix Tally, SRT 스트리밍 통합 시스템\n\n"
            "© 2024 PD Software Team"
        )
        
    def closeEvent(self, event):
        """종료 이벤트"""
        reply = QMessageBox.question(
            self,
            "종료 확인",
            "프로그램을 종료하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 리소스 정리
            self.cleanup()
            event.accept()
        else:
            event.ignore()
            
    def cleanup(self):
        """리소스 정리"""
        logger.info("리소스 정리 시작")
        
        # 스트리밍 중지
        if self.srt_manager.is_streaming:
            self.srt_manager.stop_streaming()
            
        # vMix 연결 해제
        self.vmix_manager.disconnect_from_vmix()
        
        # NDI 정리
        self.ndi_manager.cleanup()
        
        # WebSocket 중지
        self.ws_client.stop()
        
        logger.info("리소스 정리 완료")