# pd_app/ui/main_window_optimized.py
"""
통합 메인 윈도우 - 성능 최적화 버전
GUI 응답성 개선을 위한 이벤트 처리 최적화
"""

import sys
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QStatusBar, QLabel, QMessageBox,
    QMenuBar, QMenu, QToolBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon

# 로컬 임포트 - 최적화된 버전 사용
try:
    from ..core.ndi_manager_optimized import NDIManager
except ImportError:
    from ..core import NDIManager
    
from ..core import VMixManager, SRTManager, AuthManager
from ..network import WebSocketClient

try:
    from .ndi_widget_optimized import NDIWidgetOptimized as NDIWidget
except ImportError:
    from .ndi_widget import NDIWidget
    
from .tally_widget import TallyWidget
from .srt_widget import SRTWidget
from .login_widget import LoginWidget

logger = logging.getLogger(__name__)

class MainWindowOptimized(QMainWindow):
    """성능 최적화된 통합 메인 윈도우"""
    
    # 시그널 정의
    window_closing = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 최적화 플래그 설정
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        
        # 관리자 초기화
        logger.info("관리자 초기화 시작")
        self.ndi_manager = NDIManager()
        self.vmix_manager = VMixManager()
        self.srt_manager = SRTManager()
        self.auth_manager = AuthManager()
        self.ws_client = WebSocketClient()
        
        # UI 초기화
        self.init_ui()
        self.init_managers()
        self.init_connections()
        
        # 타이머 설정 - 최적화된 주기
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # 5초마다 상태 업데이트 (기존 1초에서 변경)
        
        # 지연된 초기화를 위한 타이머
        QTimer.singleShot(100, self.delayed_initialization)
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("PD 통합 소프트웨어 v1.0 (최적화)")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 여백 최소화
        
        # 상단 정보 바
        self.create_info_bar(main_layout)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        # 탭 변경 시 불필요한 업데이트 방지
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_widget)
        
        # 탭 추가 (지연 로딩)
        self.create_tabs()
        
        # 상태 바
        self.create_status_bar()
        
        # 메뉴 바 (간소화)
        self.create_menu_bar()
        
    def create_info_bar(self, layout):
        """상단 정보 바 생성"""
        info_widget = QWidget()
        info_widget.setMaximumHeight(30)
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(5, 0, 5, 0)
        
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
        
        layout.addWidget(info_widget)
        
    def create_tabs(self):
        """탭 생성 - 지연 로딩 적용"""
        # 로그인 탭 (항상 첫 번째)
        self.login_widget = LoginWidget(self.auth_manager)
        self.tab_widget.addTab(self.login_widget, "로그인")
        
        # 나머지 탭은 초기화만 하고 실제 위젯은 나중에 생성
        self.tab_widget.addTab(QWidget(), "NDI 프리뷰")
        self.tab_widget.addTab(QWidget(), "vMix Tally")
        self.tab_widget.addTab(QWidget(), "SRT 스트리밍")
        self.tab_widget.addTab(QWidget(), "설정")
        
        # 실제 위젯 참조 저장
        self.ndi_widget = None
        self.tally_widget = None
        self.srt_widget = None
        self.settings_widget = None
        
    def on_tab_changed(self, index):
        """탭 변경 시 지연 로딩"""
        # NDI 탭
        if index == 1 and self.ndi_widget is None:
            self.ndi_widget = NDIWidget(self.ndi_manager)
            self.tab_widget.setTabText(1, "NDI 프리뷰")
            old_widget = self.tab_widget.widget(1)
            self.tab_widget.removeTab(1)
            self.tab_widget.insertTab(1, self.ndi_widget, "NDI 프리뷰")
            self.tab_widget.setCurrentIndex(1)
            if old_widget:
                old_widget.deleteLater()
                
        # vMix Tally 탭
        elif index == 2 and self.tally_widget is None:
            self.tally_widget = TallyWidget(self.vmix_manager)
            self.tab_widget.setTabText(2, "vMix Tally")
            old_widget = self.tab_widget.widget(2)
            self.tab_widget.removeTab(2)
            self.tab_widget.insertTab(2, self.tally_widget, "vMix Tally")
            self.tab_widget.setCurrentIndex(2)
            if old_widget:
                old_widget.deleteLater()
                
        # SRT 스트리밍 탭
        elif index == 3 and self.srt_widget is None:
            self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
            self.tab_widget.setTabText(3, "SRT 스트리밍")
            old_widget = self.tab_widget.widget(3)
            self.tab_widget.removeTab(3)
            self.tab_widget.insertTab(3, self.srt_widget, "SRT 스트리밍")
            self.tab_widget.setCurrentIndex(3)
            if old_widget:
                old_widget.deleteLater()
        
    def create_status_bar(self):
        """상태 바 생성"""
        self.status_bar = self.statusBar()
        
        # 왼쪽: 일반 메시지
        self.status_message = QLabel("준비")
        self.status_bar.addWidget(self.status_message)
        
        # 오른쪽: 성능 정보
        self.performance_label = QLabel("CPU: 0% | 메모리: 0MB")
        self.status_bar.addPermanentWidget(self.performance_label)
        
    def create_menu_bar(self):
        """메뉴 바 생성 (간소화)"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일")
        
        exit_action = QAction("종료", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말")
        
        about_action = QAction("정보", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def init_managers(self):
        """관리자 초기화"""
        try:
            # 인증 정보 로드
            self.auth_manager.load_auth_info()
            
            # 로그인 상태 확인
            if self.auth_manager.is_authenticated():
                username = self.auth_manager.get_username()
                unique_address = self.auth_manager.get_unique_address()
                
                self.login_status_label.setText(f"로그인: {username}")
                self.unique_address_label.setText(f"고유 주소: {unique_address}")
                
                # WebSocket 연결은 지연 실행
                QTimer.singleShot(1000, self.connect_websocket)
            
            logger.info("모든 관리자 초기화 완료")
            
        except Exception as e:
            logger.error(f"관리자 초기화 오류: {e}")
            
    def connect_websocket(self):
        """WebSocket 연결 (별도 스레드에서 실행)"""
        if self.auth_manager.is_authenticated():
            unique_address = self.auth_manager.get_unique_address()
            if unique_address:
                self.ws_client.set_unique_address(unique_address)
                self.ws_client.start()
                
    def init_connections(self):
        """시그널 연결"""
        # 인증 관련
        self.auth_manager.auth_state_changed.connect(self.on_auth_state_changed)
        
        # WebSocket 관련
        self.ws_client.connection_state_changed.connect(self.on_ws_connection_changed)
        
        # 로그인 위젯
        self.login_widget.login_success.connect(self.on_login_success)
        self.login_widget.logout_success.connect(self.on_logout_success)
        
    def delayed_initialization(self):
        """지연된 초기화 작업"""
        # 무거운 초기화 작업을 여기서 수행
        logger.info("지연된 초기화 시작")
        
    def update_status(self):
        """상태 업데이트 - 최적화된 버전"""
        try:
            # 성능 정보 업데이트 (간단한 정보만)
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0)  # Non-blocking
            memory_info = psutil.Process().memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            self.performance_label.setText(f"CPU: {cpu_percent:.1f}% | 메모리: {memory_mb:.0f}MB")
            
        except Exception as e:
            logger.debug(f"상태 업데이트 오류: {e}")
            
    def on_auth_state_changed(self, is_authenticated):
        """인증 상태 변경 처리"""
        if is_authenticated:
            username = self.auth_manager.get_username()
            unique_address = self.auth_manager.get_unique_address()
            
            self.login_status_label.setText(f"로그인: {username}")
            self.unique_address_label.setText(f"고유 주소: {unique_address}")
            
            # WebSocket 연결
            self.connect_websocket()
        else:
            self.login_status_label.setText("로그인: 안됨")
            self.unique_address_label.setText("고유 주소: -")
            
            # WebSocket 연결 해제
            self.ws_client.stop()
            
    def on_ws_connection_changed(self, is_connected):
        """WebSocket 연결 상태 변경 처리"""
        if is_connected:
            self.server_status_label.setText("서버: 연결됨")
            self.server_status_label.setStyleSheet("color: green;")
        else:
            self.server_status_label.setText("서버: 연결 안됨")
            self.server_status_label.setStyleSheet("color: red;")
            
    def on_login_success(self):
        """로그인 성공 처리"""
        self.status_message.setText("로그인 성공")
        
        # 다른 탭 활성화
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, True)
            
    def on_logout_success(self):
        """로그아웃 성공 처리"""
        self.status_message.setText("로그아웃됨")
        
        # 다른 탭 비활성화
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, False)
            
        # 로그인 탭으로 이동
        self.tab_widget.setCurrentIndex(0)
        
    def show_about(self):
        """정보 대화상자 표시"""
        QMessageBox.about(
            self,
            "PD 통합 소프트웨어",
            "PD 통합 소프트웨어 v1.0 (최적화)\n\n"
            "NDI 프리뷰, vMix Tally, SRT 스트리밍 통합 시스템\n\n"
            "© 2024 PD Software Team"
        )
        
    def closeEvent(self, event):
        """윈도우 닫기 이벤트 처리"""
        # 정리 작업
        self.window_closing.emit()
        
        # 타이머 중지
        self.status_timer.stop()
        
        # 관리자 정리
        if self.ndi_widget:
            self.ndi_manager.cleanup()
        
        if self.ws_client:
            self.ws_client.stop()
            
        event.accept()
        
    def saveGeometry(self):
        """윈도우 geometry 저장을 위한 메서드"""
        return super().saveGeometry()
        
    def restoreGeometry(self, geometry):
        """윈도우 geometry 복원을 위한 메서드"""
        return super().restoreGeometry(geometry)