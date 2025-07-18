# main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget,
                            QMenuBar, QMenu, QMessageBox, QStatusBar, QLabel)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from typing import Optional
import logging
import json
import os
from modules import ModuleManager, ModuleStatus, ModuleProtocol
from modules.ndi_module import NDIModule
from modules.vmix_module import vMixModule
from modules.srt_module import SRTModule
from ui.unified_streaming_widget import UnifiedStreamingWidget
from ui.classic_mode import ClassicMainWindow


class StatusIndicator(QLabel):
    """모듈 상태 표시기"""
    def __init__(self, module_name: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.module_name = module_name
        self.setText(f"{module_name}: Unknown")
        self.setStyleSheet("padding: 2px 5px;")
        
    def update_status(self, status: str, message: str = ""):
        """상태 업데이트"""
        color_map = {
            ModuleStatus.IDLE: "#666666",
            ModuleStatus.INITIALIZING: "#ff9900",
            ModuleStatus.RUNNING: "#00aa00",
            ModuleStatus.ERROR: "#aa0000",
            ModuleStatus.STOPPING: "#ff9900",
            ModuleStatus.STOPPED: "#666666"
        }
        
        color = color_map.get(status, "#000000")
        display_text = f"{self.module_name}: {message or status}"
        
        self.setText(display_text)
        self.setStyleSheet(f"color: {color}; padding: 2px 5px;")


class MainWindow(QMainWindow):
    """통합 애플리케이션 메인 윈도우"""
    
    # 시그널
    closing = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("MainWindow")
        self.module_manager = ModuleManager()
        self.settings_file = "config/settings.json"
        
        # UI 초기화
        self._init_ui()
        
        # 모듈 초기화
        self._init_modules()
        
        # 설정 로드
        self.load_settings()
        
        # 자동 시작
        QTimer.singleShot(100, self._auto_start)
        
    def _init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("ReturnFeed Unified - NDI & vMix Tally")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 - UnifiedStreamingWidget으로 변경
        self.unified_widget = None  # 모듈 초기화 후 설정
        
        # 메뉴바
        self._create_menu_bar()
        
        # 상태바
        self._create_status_bar()
        
    def _create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # File 메뉴
        file_menu = menubar.addMenu("File")
        
        save_settings_action = QAction("Save Settings", self)
        save_settings_action.triggered.connect(self.save_settings)
        file_menu.addAction(save_settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Modules 메뉴
        modules_menu = menubar.addMenu("Modules")
        
        start_all_action = QAction("Start All", self)
        start_all_action.triggered.connect(self._start_all_modules)
        modules_menu.addAction(start_all_action)
        
        stop_all_action = QAction("Stop All", self)
        stop_all_action.triggered.connect(self._stop_all_modules)
        modules_menu.addAction(stop_all_action)
        
        # Help 메뉴
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _create_status_bar(self):
        """상태바 생성"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 일반 메시지 영역
        self.status_bar.showMessage("Ready")
        
        # 모듈별 상태 표시기는 모듈 초기화 후 추가됨
        
    def _init_modules(self):
        """모듈 초기화 및 등록"""
        try:
            # NDI 모듈
            self.ndi_module = NDIModule(self)
            self.module_manager.register_module(self.ndi_module)
            
            # vMix 모듈
            self.vmix_module = vMixModule(self)
            self.module_manager.register_module(self.vmix_module)
            
            # SRT 모듈
            self.srt_module = SRTModule(self)
            self.module_manager.register_module(self.srt_module)
            
            # 통합 위젯 생성 및 설정
            self.unified_widget = UnifiedStreamingWidget(
                ndi_module=self.ndi_module,
                srt_module=self.srt_module,
                vmix_module=self.vmix_module
            )
            self.setCentralWidget(self.unified_widget)
            
            # 상태바에 모듈 상태 표시기 추가
            self.ndi_status = StatusIndicator("NDI")
            self.vmix_status = StatusIndicator("vMix")
            self.srt_status = StatusIndicator("SRT")
            
            self.status_bar.addPermanentWidget(self.ndi_status)
            self.status_bar.addPermanentWidget(self.vmix_status)
            self.status_bar.addPermanentWidget(self.srt_status)
            
            # 모듈 시그널 연결
            self.ndi_module.status_changed.connect(
                lambda status, msg: self.ndi_status.update_status(status, msg)
            )
            self.vmix_module.status_changed.connect(
                lambda status, msg: self.vmix_status.update_status(status, msg)
            )
            self.srt_module.status_changed.connect(
                lambda status, msg: self.srt_status.update_status(status, msg)
            )
            
            # 에러 시그널 연결
            self.ndi_module.error_occurred.connect(self._on_module_error)
            self.vmix_module.error_occurred.connect(self._on_module_error)
            self.srt_module.error_occurred.connect(self._on_module_error)
            
            # vMix tally를 NDI 디스플레이에 연결
            self.vmix_module.manager.tally_updated.connect(self._on_tally_updated)
            
        except Exception as e:
            self.logger.error(f"Module initialization failed: {e}")
            QMessageBox.critical(self, "Error", f"모듈 초기화 실패:\n{e}")
            
    def _auto_start(self):
        """자동 시작"""
        self.logger.info("Auto-starting modules...")
        
        # 모든 모듈 초기화
        if self.module_manager.initialize_all():
            # 초기화 후 모듈 간 통신 설정
            self._setup_module_communication()
            # 모든 모듈 시작
            self.module_manager.start_all()
        else:
            QMessageBox.warning(self, "Warning", "일부 모듈 초기화에 실패했습니다.")
            
    def _start_all_modules(self):
        """모든 모듈 시작"""
        if not self.module_manager.start_all():
            QMessageBox.warning(self, "Warning", "일부 모듈 시작에 실패했습니다.")
            
    def _stop_all_modules(self):
        """모든 모듈 정지"""
        self.module_manager.stop_all()
        
    def _on_module_error(self, error_type: str, error_msg: str):
        """모듈 에러 처리"""
        self.logger.error(f"{error_type}: {error_msg}")
        self.status_bar.showMessage(f"Error: {error_msg}", 5000)
    
    def _setup_module_communication(self):
        """모듈 간 통신 설정"""
        try:
            # SRT 모듈이 NDI 소스 목록 요청
            self.srt_module.request_ndi_sources.connect(
                lambda: self.srt_module.update_ndi_sources(self.ndi_module.get_ndi_sources())
            )
            
            # SRT 모듈이 NDI 프리뷰 제어 요청
            self.srt_module.request_preview_control.connect(self._handle_preview_control)
            
            # SRT 스트리밍 시작/종료 알림
            self.srt_module.streaming_started.connect(self._on_srt_streaming_started)
            self.srt_module.streaming_stopped.connect(self._on_srt_streaming_stopped)
            
            # SRT 통계 업데이트 - srt_manager가 있는 경우에만
            if hasattr(self.srt_module, 'srt_manager') and self.srt_module.srt_manager:
                self.srt_module.srt_manager.stream_stats_updated.connect(
                    lambda stats: self.ndi_module.update_srt_stats(stats)
                )
            else:
                self.logger.warning("SRT manager not available for stats connection")
                
            self.logger.info("Module communication setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup module communication: {e}", exc_info=True)
    
    def _handle_preview_control(self, pause: bool):
        """NDI 프리뷰 일시정지/재개 처리"""
        if pause:
            # SRT 스트리밍 정보 전달
            stream_info = self.srt_module.srt_manager.get_stream_info()
            self.ndi_module.pause_preview(stream_info)
        else:
            self.ndi_module.resume_preview()
    
    def _on_srt_streaming_started(self, ndi_source: str, stream_name: str):
        """SRT 스트리밍 시작 처리"""
        self.logger.info(f"SRT streaming started: {ndi_source} -> {stream_name}")
        self.status_bar.showMessage(f"리턴피드 스트림 중: {stream_name}", 0)
    
    def _on_srt_streaming_stopped(self):
        """SRT 스트리밍 종료 처리"""
        self.logger.info("SRT streaming stopped")
        self.status_bar.showMessage("리턴피드 스트림 종료", 3000)
        
    def load_settings(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 각 모듈에 설정 적용
                for module_name, module_settings in settings.items():
                    module = self.module_manager.get_module(module_name)
                    if module:
                        module.apply_settings(module_settings)
                        
                self.logger.info("Settings loaded successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            
    def save_settings(self):
        """설정 파일 저장"""
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            # 모든 모듈의 설정 수집
            settings = {}
            for name, module in self.module_manager.modules.items():
                settings[name] = module.get_settings()
                
            # 파일에 저장
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                
            self.logger.info("Settings saved successfully")
            self.status_bar.showMessage("Settings saved", 2000)
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            QMessageBox.warning(self, "Error", f"설정 저장 실패:\n{e}")
            
    def _show_about(self):
        """About 다이얼로그 표시"""
        QMessageBox.about(
            self,
            "About ReturnFeed Unified",
            "ReturnFeed Unified Application\n\n"
            "NDI Discovery & vMix Tally Broadcaster\n"
            "Version 1.0.0\n\n"
            "This application combines NDI source discovery\n"
            "and vMix tally broadcasting in a unified interface."
        )
    
    def _on_tally_updated(self, pgm: int, pvw: int, pgm_name: str, pvw_name: str):
        """Handle vMix tally updates"""
        # Convert vMix input numbers and names to tally states
        tally_data = {}
        
        # Get all NDI sources
        if hasattr(self, 'ndi_module'):
            ndi_sources = self.ndi_module.get_ndi_sources()
            
            # Check each NDI source against vMix inputs
            for source in ndi_sources:
                # Reset state
                tally_data[source] = ""
                
                # Check if this NDI source matches PGM or PVW
                # Match by partial name (e.g., "NDI Source 1" matches "Input 1")
                if pgm_name and source.lower() in pgm_name.lower():
                    tally_data[source] = "PGM"
                elif pvw_name and source.lower() in pvw_name.lower():
                    tally_data[source] = "PVW"
                # Also check by number pattern
                elif f"Input {pgm}" in source or f"NDI {pgm}" in source:
                    tally_data[source] = "PGM"
                elif f"Input {pvw}" in source or f"NDI {pvw}" in source:
                    tally_data[source] = "PVW"
            
            # Update NDI module with tally states
            self.ndi_module.update_tally_states(tally_data)
            self.logger.debug(f"Tally updated - PGM: {pgm_name}, PVW: {pvw_name}")
        
    def closeEvent(self, event):
        """창 닫기 이벤트 처리"""
        reply = QMessageBox.question(
            self,
            "Exit",
            "정말로 종료하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Application closing...")
            
            # 모든 모듈 정지 및 정리
            self.module_manager.stop_all()
            self.module_manager.cleanup_all()
            
            # 설정 저장
            self.save_settings()
            
            # 시그널 발송
            self.closing.emit()
            
            event.accept()
        else:
            event.ignore()