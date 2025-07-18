"""
Fixed Main Window with stable NDI handling
NDI 연결 안정성 문제 해결
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QStatusBar, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# 수정된 NDI Manager 사용
from pd_app.core.ndi_manager_fixed import NDIManager
from pd_app.core import VMixManager, SRTManager, AuthManager
from pd_app.network import WebSocketClient
from pd_app.ui import LoginWidget, NDIWidget, TallyWidget, SRTWidget

logger = logging.getLogger(__name__)


class MainWindowFixed(QMainWindow):
    """메인 윈도우 - NDI 안정성 개선"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PD 통합 소프트웨어 v2.1 (Fixed)")
        self.setGeometry(100, 100, 1200, 800)
        
        # 관리자 초기화
        self._init_managers()
        
        # UI 초기화
        self._init_ui()
        
        # 신호 연결
        self._connect_signals()
        
        # 초기 상태 설정
        self._init_state()
        
        logger.info("메인 윈도우 초기화 완료")
        
    def _init_managers(self):
        """관리자 초기화"""
        try:
            # 인증 관리자
            self.auth_manager = AuthManager()
            self.auth_manager.load_credentials()
            logger.info("인증 정보 로드 완료")
            
            # NDI 관리자 - 수정된 버전 사용
            self.ndi_manager = NDIManager()
            self.ndi_manager.initialize()
            
            # vMix 관리자
            self.vmix_manager = VMixManager()
            
            # SRT 관리자
            self.srt_manager = SRTManager()
            
            # WebSocket 클라이언트
            self.ws_client = WebSocketClient()
            
            logger.info("모든 관리자 초기화 완료")
            
        except Exception as e:
            logger.error(f"관리자 초기화 오류: {e}", exc_info=True)
            raise
            
    def _init_ui(self):
        """UI 초기화"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 탭 생성 - 지연 로딩
        self._create_tabs()
        
        # 상태 바
        self._create_status_bar()
        
        # 자동 저장 타이머
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_settings)
        self.auto_save_timer.start(60000)  # 1분마다
        
    def _create_tabs(self):
        """탭 생성"""
        # 로그인 탭
        self.login_widget = LoginWidget(self.auth_manager)
        self.tab_widget.addTab(self.login_widget, "로그인")
        
        # 지연 로딩을 위한 플레이스홀더
        self.ndi_widget = None
        self.tally_widget = None
        self.srt_widget = None
        
        # 빈 위젯으로 탭 추가
        self.tab_widget.addTab(QWidget(), "NDI 프리뷰")
        self.tab_widget.addTab(QWidget(), "Tally")
        self.tab_widget.addTab(QWidget(), "SRT 스트리밍")
        
        # 탭 변경 시 위젯 생성
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
    def _create_status_bar(self):
        """상태 바 생성"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 연결 상태 라벨들
        self.ndi_status_label = QLabel("NDI: 준비")
        self.vmix_status_label = QLabel("vMix: 미연결")
        self.ws_status_label = QLabel("서버: 미연결")
        
        self.status_bar.addWidget(self.ndi_status_label)
        self.status_bar.addWidget(self.vmix_status_label)
        self.status_bar.addWidget(self.ws_status_label)
        
        # 메시지 라벨
        self.status_message = QLabel("")
        self.status_bar.addPermanentWidget(self.status_message)
        
    def _connect_signals(self):
        """신호 연결"""
        # NDI 관리자 신호
        self.ndi_manager.connection_status_changed.connect(self._on_ndi_status_changed)
        
        # vMix 관리자 신호
        self.vmix_manager.connection_status_changed.connect(self._on_vmix_status_changed)
        
        # WebSocket 신호
        self.ws_client.connection_state_changed.connect(self._on_ws_status_changed)
        
        # 인증 관리자 신호
        self.auth_manager.auth_state_changed.connect(self._on_auth_state_changed)
        
    def _init_state(self):
        """초기 상태 설정"""
        # WebSocket 시작
        try:
            unique_address = self.auth_manager.get_unique_address()
            if unique_address:
                self.ws_client.set_unique_address(unique_address)
                self.ws_client.start()
                logger.info("WebSocket 클라이언트 시작")
        except Exception as e:
            logger.error(f"WebSocket 시작 오류: {e}")
            
    def _on_tab_changed(self, index):
        """탭 변경 처리 - 지연 로딩"""
        try:
            # NDI 탭
            if index == 1 and self.ndi_widget is None:
                self.ndi_widget = NDIWidget(self.ndi_manager)
                self.tab_widget.setTabText(1, "NDI 프리뷰")
                # 기존 빈 위젯 교체
                self.tab_widget.removeTab(1)
                self.tab_widget.insertTab(1, self.ndi_widget, "NDI 프리뷰")
                self.tab_widget.setCurrentIndex(1)
                
            # Tally 탭
            elif index == 2 and self.tally_widget is None:
                self.tally_widget = TallyWidget(self.vmix_manager)
                self.tab_widget.setTabText(2, "Tally")
                self.tab_widget.removeTab(2)
                self.tab_widget.insertTab(2, self.tally_widget, "Tally")
                self.tab_widget.setCurrentIndex(2)
                
            # SRT 탭
            elif index == 3 and self.srt_widget is None:
                self.srt_widget = SRTWidget(self.srt_manager, self.auth_manager)
                self.tab_widget.setTabText(3, "SRT 스트리밍")
                self.tab_widget.removeTab(3)
                self.tab_widget.insertTab(3, self.srt_widget, "SRT 스트리밍")
                self.tab_widget.setCurrentIndex(3)
                
        except Exception as e:
            logger.error(f"탭 변경 중 오류 (탭 {index}): {e}")
            self.status_message.setText(f"탭 로딩 오류: {str(e)[:50]}...")
            
    def _on_ndi_status_changed(self, status: str, color: str):
        """NDI 상태 변경"""
        self.ndi_status_label.setText(f"NDI: {status}")
        self.ndi_status_label.setStyleSheet(f"color: {color};")
        
    def _on_vmix_status_changed(self, connected: bool):
        """vMix 상태 변경"""
        if connected:
            self.vmix_status_label.setText("vMix: 연결됨")
            self.vmix_status_label.setStyleSheet("color: green;")
        else:
            self.vmix_status_label.setText("vMix: 미연결")
            self.vmix_status_label.setStyleSheet("color: red;")
            
    def _on_ws_status_changed(self, connected: bool):
        """WebSocket 상태 변경"""
        if connected:
            self.ws_status_label.setText("서버: 연결됨")
            self.ws_status_label.setStyleSheet("color: green;")
        else:
            self.ws_status_label.setText("서버: 미연결")
            self.ws_status_label.setStyleSheet("color: red;")
            
    def _on_auth_state_changed(self, authenticated: bool):
        """인증 상태 변경"""
        if authenticated:
            self.status_message.setText("로그인됨")
            # 탭 활성화
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, True)
        else:
            self.status_message.setText("로그인 필요")
            # 탭 비활성화
            for i in range(1, self.tab_widget.count()):
                self.tab_widget.setTabEnabled(i, False)
                
    def _auto_save_settings(self):
        """설정 자동 저장"""
        try:
            # 필요시 설정 저장 로직 추가
            pass
        except Exception as e:
            logger.error(f"설정 자동 저장 오류: {e}")
            
    def closeEvent(self, event):
        """종료 이벤트"""
        try:
            # 관리자들 정리
            if hasattr(self, 'ndi_manager'):
                self.ndi_manager.cleanup()
                
            if hasattr(self, 'vmix_manager'):
                self.vmix_manager.disconnect()
                
            if hasattr(self, 'ws_client'):
                self.ws_client.stop()
                
            logger.info("메인 윈도우 종료")
            
        except Exception as e:
            logger.error(f"종료 중 오류: {e}")
            
        event.accept()