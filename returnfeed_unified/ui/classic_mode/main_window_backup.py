"""
Classic Mode Main Window
Professional single-channel monitoring interface
"""

from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QMessageBox,
                             QApplication, QHBoxLayout, QDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QEventLoop
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QImage
import logging
import psutil
import time
import re

from .components.command_bar import CommandBar
from .components.video_display import SingleChannelVideoDisplay
from .components.ndi_control_panel import NDIControlPanel
from .components.stream_control_panel import StreamControlPanel
from .components.info_status_bar import InfoStatusBar
from .components.custom_dialog import ConfirmDialog
from .styles.dark_theme import apply_theme


logger = logging.getLogger(__name__)


class PerformanceMonitor(QThread):
    """Background thread for monitoring performance"""
    stats_updated = pyqtSignal(int, float, int)  # fps, cpu, memory
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.frame_count = 0
        self.last_time = time.time()
        # CPU 측정을 위한 초기화
        self.process = psutil.Process()
        self.process.cpu_percent()  # 첫 번째 호출로 초기화
        
    def count_frame(self):
        """Count a rendered frame"""
        self.frame_count += 1
        
    def run(self):
        """Monitor performance metrics"""
        while self.running:
            try:
                # Calculate FPS
                current_time = time.time()
                elapsed = current_time - self.last_time
                if elapsed >= 1.0:
                    fps = int(self.frame_count / elapsed)
                    self.frame_count = 0
                    self.last_time = current_time
                    
                    # Get CPU and memory
                    # interval=0.1로 짧은 간격 측정하여 정확도 향상
                    cpu_percent = self.process.cpu_percent(interval=0.1)
                    
                    # CPU 사용률이 0%인 경우 최소값 설정
                    if cpu_percent == 0.0:
                        cpu_percent = 0.1
                    
                    # 이 프로세스만의 CPU 사용률 (전체 시스템 대비)
                    # psutil은 프로세스가 모든 코어를 100% 사용할 때 코어수*100%로 표시
                    # 예: 4코어에서 1코어 100% 사용 = 100%, 4코어 100% 사용 = 400%
                    # 전체 시스템 대비 비율로 표시하려면 코어 수로 나눔
                    num_cores = psutil.cpu_count()
                    cpu = min(cpu_percent / num_cores, 100.0)
                    
                    memory = int(self.process.memory_info().rss / 1024 / 1024)  # MB
                    
                    self.stats_updated.emit(fps, cpu, memory)
                    
                self.msleep(1000)  # Check every 1 second to reduce overhead
                
            except Exception as e:
                logger.error(f"Performance monitor error: {e}")
                
    def stop(self):
        """Stop monitoring"""
        self.running = False


class ClassicMainWindow(QMainWindow):
    """Main window for Classic Mode - Single channel monitoring"""
    
    # Signals
    closing = pyqtSignal()
    
    def __init__(self, ndi_module=None, vmix_module=None, srt_module=None):
        super().__init__()
        
        # Module references
        self.ndi_module = ndi_module
        self.vmix_module = vmix_module
        self.srt_module = srt_module
        
        # State
        self.current_source = ""
        self.is_fullscreen = False
        self.is_srt_streaming = False  # SRT 스트리밍 상태
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Frame processing queue and timer for stable 60fps
        self.frame_queue = []
        self.frame_queue_lock = QThread.currentThread()  # For thread safety
        self.max_frame_buffer = 2  # 적절한 버퍼링
        self.frame_skip_count = 0
        self.current_bandwidth_mode = "normal"  # Track current mode
        
        # 60fps precise timing (16.67ms)
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self._process_frame_queue)
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)  # High precision timer
        self.frame_timer.setInterval(16)  # 60fps = 16.67ms
        
        # 프레임 타이밍 추적
        self.last_process_time = 0
        self.frame_process_count = 0
        self.last_displayed_frame = None  # 프레임 보간용
        
        # Initialize UI
        self._init_ui()
        self._setup_shortcuts()
        self._connect_modules()
        
        # Apply theme
        apply_theme(QApplication.instance())
        
        # Start performance monitoring
        self.performance_monitor.stats_updated.connect(self._update_performance_stats)
        self.performance_monitor.start()
        
        # 초기 서버 상태 설정\n        self.stream_control_panel.update_server_status(True, \"00:00:00\", 0)\n        \n        # Start frame processing timer
        self.frame_timer.start()
        logger.info("Frame processing timer started at 60fps")
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_settings)
        self.auto_save_timer.start(300000)  # Save every 5 minutes
        
    def _init_ui(self):
        """사용자 인터페이스 초기화"""
        self.setWindowTitle("리턴피드 클래식 - 전문 NDI 모니터")
        self.setGeometry(100, 100, 1280, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 커맨드 바 (상단)
        self.command_bar = CommandBar()
        self.command_bar.login_requested.connect(self._on_login_requested)
        self.command_bar.signup_requested.connect(self._on_signup_requested)
        main_layout.addWidget(self.command_bar)
        
        # Video display (center)
        self.video_display = SingleChannelVideoDisplay()
        self.video_display.double_clicked.connect(self._toggle_fullscreen)
        main_layout.addWidget(self.video_display, 1)  # Stretch factor 1
        
        # NDI Control Panel (차차하단행)
        self.ndi_control_panel = NDIControlPanel()
        self.ndi_control_panel.source_selected.connect(self._on_source_selected)
        self.ndi_control_panel.connect_clicked.connect(self._on_connect_clicked)
        self.ndi_control_panel.refresh_clicked.connect(self._refresh_sources)
        self.ndi_control_panel.disconnect_clicked.connect(self._on_disconnect_clicked)
        self.ndi_control_panel.bandwidth_mode_changed.connect(self._on_bandwidth_mode_changed)
        main_layout.addWidget(self.ndi_control_panel)
        
        # Stream Control Panel (차하단행)
        self.stream_control_panel = StreamControlPanel()
        self.stream_control_panel.srt_start_clicked.connect(self._on_srt_start_clicked)
        self.stream_control_panel.srt_stop_clicked.connect(self._on_srt_stop_clicked)
        main_layout.addWidget(self.stream_control_panel)
        
        # Info Status Bar (최하단행)
        self.info_status_bar = InfoStatusBar()
        main_layout.addWidget(self.info_status_bar)
        
        # Set minimum size
        self.setMinimumSize(1024, 600)
        
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Space - Toggle connection
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._toggle_connection)
        
        # R - Toggle recording
        QShortcut(QKeySequence(Qt.Key.Key_R), self, self._toggle_recording)
        
        # S - Toggle streaming
        QShortcut(QKeySequence(Qt.Key.Key_S), self, self._toggle_streaming)
        
        # F - Toggle fullscreen
        QShortcut(QKeySequence(Qt.Key.Key_F), self, self._toggle_fullscreen)
        
        # G - Toggle safe areas
        QShortcut(QKeySequence(Qt.Key.Key_G), self, self.video_display.toggle_safe_areas)
        
        # I - Toggle info overlay
        QShortcut(QKeySequence(Qt.Key.Key_I), self, self.video_display.toggle_info_overlay)
        
        # A - Toggle audio meter
        QShortcut(QKeySequence(Qt.Key.Key_A), self, self.video_display.toggle_audio_meter)
        
        # Escape - Exit fullscreen
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._exit_fullscreen)
        
    def _connect_modules(self):
        """Connect to backend modules"""
        if not self.ndi_module:
            logger.warning("No NDI module provided")
            return
            
        # Connect NDI manager signals (sources list)
        if hasattr(self.ndi_module, 'manager') and self.ndi_module.manager:
            self.ndi_module.manager.sources_updated.connect(self._on_sources_updated)
            
        # Connect NDI receiver signals (frames)
        if hasattr(self.ndi_module, 'receiver') and self.ndi_module.receiver:
            self.ndi_module.receiver.frame_received.connect(self._on_frame_received)
            self.ndi_module.receiver.status_changed.connect(self._on_ndi_receiver_status_changed)
            
        # Connect NDI widget for connection status
        if hasattr(self.ndi_module, 'widget') and self.ndi_module.widget:
            # The widget tracks connection status
            pass
            
        # Connect vMix module signals
        if self.vmix_module:
            # Tally updates from vMix manager
            if hasattr(self.vmix_module, 'manager') and self.vmix_module.manager:
                if hasattr(self.vmix_module.manager, 'tally_updated'):
                    # vMixManager emits (pgm, pvw, pgm_name, pvw_name)
                    self.vmix_module.manager.tally_updated.connect(self._on_vmix_tally_updated)
                    
                # Connect vMix status changes
                if hasattr(self.vmix_module.manager, 'vmix_status_changed'):
                    self.vmix_module.manager.vmix_status_changed.connect(
                        lambda status, color: self.command_bar.update_status("vMix", "online" if "연결" in status else "offline")
                    )
            elif hasattr(self.vmix_module, 'tally_updated'):
                self.vmix_module.tally_updated.connect(self._on_tally_updated)
                
            if hasattr(self.vmix_module, 'connection_status_changed'):
                self.vmix_module.connection_status_changed.connect(
                    lambda connected: self.command_bar.update_status("vMix", "online" if connected else "offline")
                )
                
        # Module status updates
        if hasattr(self.ndi_module, 'status_changed'):
            self.ndi_module.status_changed.connect(
                lambda status, msg: self.command_bar.update_status("NDI", "online" if status == "running" else "offline")
            )
            
        # Request initial source list
        QTimer.singleShot(100, self._refresh_sources)
        
    def _refresh_sources(self):
        """Refresh NDI source list"""
        if self.ndi_module:
            # Call the widget's refresh which triggers the manager
            if hasattr(self.ndi_module, 'widget') and self.ndi_module.widget:
                self.ndi_module.widget.refresh_requested.emit()
            elif hasattr(self.ndi_module, 'manager') and self.ndi_module.manager:
                # Direct manager call if available
                self.ndi_module.manager._scan_sources()
            
    def _on_sources_updated(self, sources: list):
        """Handle NDI sources update"""
        source_names = []
        for s in sources:
            if isinstance(s, dict):
                name = s.get('name', '')
            elif hasattr(s, 'name'):
                name = s.name
            elif hasattr(s, 'to_dict'):
                name = s.to_dict().get('name', '')
            else:
                name = str(s)
            if name:
                source_names.append(name)
                
        self.ndi_control_panel.update_sources(source_names)
        self.command_bar.update_status("NDI", "online" if sources else "offline")
        
    def _on_frame_received(self, frame_data):
        """Handle received NDI frame - add to queue for stable timing"""
        # SRT 스트리밍 중이고 페이드가 완료된 경우 프레임 처리 생략 (자원 절약)
        if self.is_srt_streaming and hasattr(self.video_display, '_fade_opacity') and self.video_display._fade_opacity >= 1.0:
            return
            
        # 프레임 큐에 추가
        if len(self.frame_queue) < self.max_frame_buffer:
            self.frame_queue.append(frame_data)
        else:
            # 버퍼가 가득 찬 경우 가장 오래된 프레임 교체
            self.frame_skip_count += 1
            self.frame_queue[0] = frame_data
            
    def _process_frame_queue(self):
        """Process frames from queue at precise intervals"""
        if not self.frame_queue:
            # 프록시 모드에서 프레임이 없으면 이전 프레임 재사용
            if self.current_bandwidth_mode == "proxy" and self.last_displayed_frame:
                # 이전 프레임을 다시 표시하여 60fps 유지
                self._display_frame(self.last_displayed_frame, is_interpolated=True)
            return
            
        # 큐에서 프레임 처리
        frame_data = self.frame_queue.pop(0)
        self.last_displayed_frame = frame_data  # 나중에 재사용하기 위해 저장
        self._display_frame(frame_data)
        
    def _display_frame(self, frame_data, is_interpolated=False):
        """Display a frame immediately"""
        # Handle both QImage directly or dict with image
        if isinstance(frame_data, QImage):
            self.video_display.update_frame(frame_data)
            # 보간된 프레임도 카운트하여 60fps 유지
            self.performance_monitor.count_frame()
        elif isinstance(frame_data, dict) and 'image' in frame_data:
            image = frame_data['image']
            if isinstance(image, QImage):
                self.video_display.update_frame(image)
                self.performance_monitor.count_frame()
                
            # Update technical info from dict
            info = {
                'resolution': frame_data.get('resolution', ''),
                'fps': frame_data.get('fps', 0),
                'bitrate': frame_data.get('bitrate', ''),
                'audio_level': frame_data.get('audio_level', -60)
            }
            self.video_display.update_frame_info(info)
            self.info_status_bar.update_technical_info(info)
        
    def _on_ndi_receiver_status_changed(self, status: str, message: str = ""):
        """Handle NDI receiver status change"""
        connected = status == "connected"
        source_name = self.current_source if connected else ""
        self._on_connection_changed(connected, source_name)
        
    def _on_connection_changed(self, connected: bool, source_name: str = ""):
        """Handle NDI connection status change"""
        self.video_display.set_connected(connected)
        self.ndi_control_panel.set_connected(connected, source_name)
        self.info_status_bar.update_source_info(source_name, connected)
        
        # SRT 스트리밍 버튼 활성화 상태 설정\n        self.stream_control_panel.set_streaming_enabled(connected)\n        \n        if not connected:
            self.video_display.clear_display()
            
    def _on_vmix_tally_updated(self, pgm: int, pvw: int, pgm_name: str, pvw_name: str):
        """vMixManager 탈리 업데이트 처리 (int, int, str, str 형식)"""
        logger.info(f"Tally update received - PGM: {pgm_name} ({pgm}), PVW: {pvw_name} ({pvw})")
        
        # Convert to dict format
        tally_data = {}
        
        # Mark PGM source
        if pgm_name:
            tally_data[pgm_name] = "PGM"
            
        # Mark PVW source (only if different from PGM)
        if pvw_name and pvw_name != pgm_name:
            tally_data[pvw_name] = "PVW"
            
        # Call the main tally update handler
        self._on_tally_updated(tally_data)
    
    def _on_tally_updated(self, tally_data: dict):
        """vMix 탈리 업데이트 처리"""
        logger.info(f"Processing tally data: {tally_data}")
        
        # Update command bar with all tally data
        self.command_bar.update_tally(tally_data)
        
        # Update video display and control panel for current source
        # 유연한 이름 매칭 - 대소문자 무시, 공백 처리
        if self.current_source:
            # 직접 매칭
            if self.current_source in tally_data:
                state = tally_data[self.current_source]
                self.video_display.set_tally_state(state)
                self.ndi_control_panel.set_tally_state(state)
            else:
                # 유연한 매칭 시도
                current_lower = self.current_source.lower().strip()
                for input_name, state in tally_data.items():
                    if input_name.lower().strip() == current_lower:
                        self.video_display.set_tally_state(state)
                        self.ndi_control_panel.set_tally_state(state)
                        break
                    # 부분 매칭도 시도
                    elif current_lower in input_name.lower() or input_name.lower() in current_lower:
                        self.video_display.set_tally_state(state)
                        self.ndi_control_panel.set_tally_state(state)
                        break
            
    def _on_source_selected(self, source_name: str):
        """Handle source selection - auto connect"""
        self.current_source = source_name
        self.video_display.set_source(source_name)
        
    def _on_connect_clicked(self):
        """Handle connect button click - now auto-connect from source selection"""
        if self.current_source and self.ndi_module:
            # 이미 연결된 경우 먼저 연결 해제
            if self.ndi_control_panel.is_connected:
                if hasattr(self.ndi_module, 'widget') and self.ndi_module.widget:
                    self.ndi_module.widget.source_disconnect_requested.emit()
                # 잠시 대기 후 새 연결
                QTimer.singleShot(200, lambda: self._connect_to_source())
            else:
                self._connect_to_source()
                
    def _connect_to_source(self):
        """Actually connect to the NDI source"""
        if self.current_source and self.ndi_module:
            # Show connecting state immediately
            self.video_display.set_source(self.current_source)
            self.video_display.set_connected(False)  # Show connecting message
            
            # Apply bandwidth mode
            bandwidth_mode = self.ndi_control_panel.get_bandwidth_mode()
            self.current_bandwidth_mode = bandwidth_mode  # 현재 모드 업데이트
            
            if hasattr(self.ndi_module, 'receiver') and self.ndi_module.receiver:
                bandwidth = "highest" if bandwidth_mode == "normal" else "lowest"
                self.ndi_module.receiver.set_bandwidth_mode(bandwidth)
                
            # 프레임 큐 초기화 및 버퍼 크기 조정
            self.frame_queue.clear()
            if bandwidth_mode == "proxy":
                self.max_frame_buffer = 1  # 프록시 모드: 최소 버퍼로 지연 방지
            else:
                self.max_frame_buffer = 2  # 일반 모드: 안정적인 버퍼링
                
            logger.info(f"{bandwidth_mode} 모드로 NDI 연결 시도 (버퍼: {self.max_frame_buffer})")
            
            # Use the widget's connect signal
            if hasattr(self.ndi_module, 'widget') and self.ndi_module.widget:
                self.ndi_module.widget.source_connect_requested.emit(self.current_source)
                
    def _on_disconnect_clicked(self):
        """Handle disconnect button click"""
        if self.ndi_module:
            # Use the widget's disconnect signal
            if hasattr(self.ndi_module, 'widget') and self.ndi_module.widget:
                self.ndi_module.widget.source_disconnect_requested.emit()
            
    def _on_srt_start_clicked(self):
        """Handle SRT start click"""
        if self.srt_module and self.current_source:
            if hasattr(self.srt_module, 'start_streaming'):
                # Generate stream name from source name
                stream_name = re.sub(r'[^\w\s-]', '', self.current_source)
                stream_name = re.sub(r'[-\s]+', '-', stream_name).lower()
                
                # Use default values for bitrate and fps
                bitrate = "2M"  # Default bitrate
                fps = 30       # Default fps
                
                # Call with all required parameters
                self.srt_module.start_streaming(self.current_source, stream_name, bitrate, fps)
                self.stream_control_panel.set_srt_streaming(True, "Starting...")
                self.command_bar.update_status("리턴피드 스트림", "online")
                
                # 스트리밍 시작 시 프리뷰 중지 및 NDI 수신 일시정지
                self.is_srt_streaming = True
                self.video_display.set_streaming_mode(True)
                
                # NDI receiver 일시정지로 CPU 자원 절약
                if self.ndi_module and hasattr(self.ndi_module, 'receiver') and self.ndi_module.receiver:
                    self.ndi_module.receiver.pause_receiving()
                    
                logger.info("리턴피드 스트리밍 시작 - 프리뷰 중지 및 NDI 수신 일시정지")
                
    def _on_srt_stop_clicked(self):
        """Handle SRT stop click"""
        if self.srt_module:
            if hasattr(self.srt_module, 'stop_streaming'):
                self.srt_module.stop_streaming()
                self.stream_control_panel.set_srt_streaming(False)
                self.command_bar.update_status("리턴피드 스트림", "offline")
                
                # 스트리밍 종료 시 프리뷰 재개 및 NDI 수신 재개
                self.is_srt_streaming = False
                self.video_display.set_streaming_mode(False)
                
                # NDI receiver 재개
                if self.ndi_module and hasattr(self.ndi_module, 'receiver') and self.ndi_module.receiver:
                    # 프레임 큐 초기화하여 새로운 프레임을 즉시 받을 준비
                    self.frame_queue.clear()
                    self.last_displayed_frame = None
                    
                    # NDI 수신 재개
                    self.ndi_module.receiver.resume_receiving()
                    
                    # 연결 상태 확인 및 UI 업데이트
                    if self.current_source:
                        self.video_display.set_source(self.current_source)
                        self.video_display.set_connected(True)
                    
                logger.info("리턴피드 스트리밍 종료 - 프리뷰 재개 및 NDI 수신 재개")
                
    def _on_login_requested(self, username: str, password: str):
        """로그인 요청 처리"""
        # TODO: 실제 로그인 구현
        logger.info(f"로그인 시도: {username}")
        QMessageBox.information(self, "로그인", f"환영합니다, {username}님!")
        
    def _on_signup_requested(self):
        """회원가입 요청 처리"""
        # TODO: 실제 회원가입 구현
        logger.info("회원가입 요청")
        QMessageBox.information(self, "회원가입", "회원가입 페이지로 이동합니다.")
        
    def _on_bandwidth_mode_changed(self, mode: str):
        """NDI 대역폭 모드 변경 처리"""
        logger.info(f"NDI 대역폭 모드 변경: {mode}")
        if self.ndi_module and hasattr(self.ndi_module, 'receiver') and self.ndi_module.receiver:
            bandwidth = "highest" if mode == "normal" else "lowest"
            self.ndi_module.receiver.set_bandwidth_mode(bandwidth)
            
        # 현재 모드 저장
        self.current_bandwidth_mode = mode
        
        # 프록시/일반 모드 모두 동일한 60fps 유지
        logger.info(f"대역폭 모드 변경: {mode}")
        
        # 모드 변경 시 프레임 큐 초기화 및 버퍼 크기 조정
        self.frame_queue.clear()
        if mode == "proxy":
            self.max_frame_buffer = 1
        else:
            self.max_frame_buffer = 2
            
    def _toggle_connection(self):
        """NDI 연결 토글"""
        if self.ndi_control_panel.is_connected:
            self._on_disconnect_clicked()
        else:
            self._on_connect_clicked()
            
    def _toggle_recording(self):
        """녹화 토글"""
        # 녹화 기능은 추후 구현
        logger.info("녹화 기능은 준비 중입니다")
        
    def _toggle_streaming(self):
        """스트리밍 토글"""
        # SRT 스트리밍 토글
        if self.stream_control_panel.is_srt_streaming:
            self._on_srt_stop_clicked()
        else:
            self._on_srt_start_clicked()
        
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.is_fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()
            
    def _enter_fullscreen(self):
        """Enter fullscreen mode"""
        self.is_fullscreen = True
        self.command_bar.hide()
        self.ndi_control_panel.hide()
        self.stream_control_panel.hide()
        self.info_status_bar.hide()
        self.showFullScreen()
        
    def _exit_fullscreen(self):
        """Exit fullscreen mode"""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.command_bar.show()
            self.ndi_control_panel.show()
            self.stream_control_panel.show()
            self.info_status_bar.show()
            self.showNormal()
            
    def _update_performance_stats(self, fps: int, cpu: float, memory: int):
        """Update performance statistics"""
        self.info_status_bar.update_performance_stats(fps, cpu, memory)
        
    def _auto_save_settings(self):
        """Auto-save settings"""
        # TODO: Implement settings save
        logger.debug("Auto-saving settings...")
        
    def closeEvent(self, event):
        """창 닫기 처리"""
        # 커스텀 다이얼로그 사용
        dialog = ConfirmDialog(
            title="종료 확인",
            message="정말로 종료하시겠습니까?",
            parent=self
        )
        
        # 다이얼로그를 중앙에 배치
        dialog.move(
            self.x() + (self.width() - dialog.width()) // 2,
            self.y() + (self.height() - dialog.height()) // 2
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 프레임 타이머 중지
            self.frame_timer.stop()
            
            # 성능 모니터 중지
            self.performance_monitor.stop()
            self.performance_monitor.wait()
            
            # 종료 시그널 발송
            self.closing.emit()
            
            event.accept()
        else:
            event.ignore()