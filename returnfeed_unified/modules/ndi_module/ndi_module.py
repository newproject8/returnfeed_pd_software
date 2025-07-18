# ndi_module.py
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import QObject
from modules import BaseModule, ModuleStatus
from .ndi_manager import NDIManager
from .ndi_widget import NDIWidget
from .ndi_receiver import NDIReceiver


class NDIModule(BaseModule):
    """NDI Discovery and Display Module"""
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__("NDIDiscovery", parent)
        self.manager = NDIManager(self)
        self.widget = NDIWidget()
        self.receiver = NDIReceiver(self)
        
        # 시그널 연결
        self._setup_connections()
        
        # 기본 설정
        self.settings = {
            "auto_refresh": True,
            "refresh_interval": 2000,  # milliseconds
            "show_addresses": True,
            "bandwidth_mode": "highest"  # highest (normal) or lowest (proxy)
        }
        
        # 프리뷰 상태
        self.preview_paused = False
        self.current_ndi_source = None
        
        # Tally 상태 추적
        self.tally_states = {}  # {source_name: "PGM"|"PVW"|""}
        
    def _setup_connections(self):
        """시그널/슬롯 연결 설정 - QVideoSink 기반 스레드 안전 버전"""
        # Widget → Module
        self.widget.refresh_requested.connect(self._on_refresh_requested)
        self.widget.source_selected.connect(self._on_source_selected)
        self.widget.source_connect_requested.connect(self._on_connect_requested)
        self.widget.source_disconnect_requested.connect(self._on_disconnect_requested)
        self.widget.bandwidth_mode_changed.connect(self._on_bandwidth_mode_changed)
        
        # Manager → Widget
        self.manager.sources_updated.connect(self.widget.update_sources)
        self.manager.status_changed.connect(self.widget.update_status)
        
        # Receiver → Widget
        self.receiver.frame_received.connect(self.widget.display_frame)  # 레거시 호환
        self.receiver.status_changed.connect(self._on_receiver_status_changed)
        self.receiver.error_occurred.connect(self._on_receiver_error)
        
        # **🚀 ULTRATHINK 수정**: QPainter 직접 렌더링 연결
        # QVideoSink 대신 QImage 시그널을 직접 연결
        video_display = getattr(self.widget, 'video_display', None)
        if video_display and hasattr(video_display, 'updateFrame'):
            # NDI receiver의 frame_received 시그널을 VideoDisplayWidget의 updateFrame에 직접 연결
            self.receiver.frame_received.connect(video_display.updateFrame)
            self.logger.info("🚀 QPainter direct rendering connected - QVideoSink 블랙박스 우회 완료")
        
        # Manager → Module
        self.manager.error_occurred.connect(self._on_manager_error)
        self.manager.status_changed.connect(self._on_status_changed)
        
    def initialize(self) -> bool:
        """모듈 초기화"""
        try:
            self.set_status(ModuleStatus.INITIALIZING, "NDI 초기화 중...")
            
            # NDI Manager 초기화
            if self.manager.initialize():
                self.widget.set_enabled(True)
                
                # Apply saved bandwidth mode
                saved_mode = self.settings.get("bandwidth_mode", "highest")
                self.receiver.set_bandwidth_mode(saved_mode)
                # Update UI to reflect saved mode
                if saved_mode == "lowest":
                    self.widget.bandwidth_combo.setCurrentIndex(1)
                else:
                    self.widget.bandwidth_combo.setCurrentIndex(0)
                
                self.set_status(ModuleStatus.IDLE, "NDI 초기화 완료")
                return True
            else:
                self.widget.set_enabled(False)
                self.emit_error("InitError", "NDI 라이브러리 초기화 실패")
                return False
                
        except Exception as e:
            self.emit_error("InitError", str(e))
            self.widget.set_enabled(False)
            return False
            
    def start(self) -> bool:
        """모듈 시작"""
        try:
            self.set_status(ModuleStatus.RUNNING, "NDI 검색 시작...")
            
            # NDI 소스 검색 시작
            if self.manager.start_discovery():
                self.set_status(ModuleStatus.RUNNING, "NDI 소스 검색 중")
                return True
            else:
                self.emit_error("StartError", "NDI 검색 시작 실패")
                return False
                
        except Exception as e:
            self.emit_error("StartError", str(e))
            return False
            
    def stop(self) -> bool:
        """모듈 정지"""
        try:
            self.set_status(ModuleStatus.STOPPING, "NDI 검색 중지 중...")
            
            # NDI 수신기 정지
            if self.receiver.isRunning():
                self.receiver.disconnect()
                self.receiver.quit()
                self.receiver.wait(1000)
            
            # NDI 검색 중지
            self.manager.stop_discovery()
            
            # UI 클리어
            self.widget.clear_sources()
            self.widget.update_connection_status(False)
            
            self.set_status(ModuleStatus.STOPPED, "NDI 검색 중지됨")
            return True
            
        except Exception as e:
            self.emit_error("StopError", str(e))
            return False
            
    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            # 수신기 정리
            if self.receiver.isRunning():
                self.receiver.disconnect()
                self.receiver.quit()
                self.receiver.wait(1000)
            
            # 매니저 정리
            self.manager.cleanup()
            self.logger.info("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            
    def get_widget(self) -> QWidget:
        """모듈 UI 위젯 반환"""
        return self.widget
        
    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return self.settings.copy()
        
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 적용"""
        try:
            # 설정 업데이트
            self.settings.update(settings)
            
            # 리프레시 간격 변경 적용
            if "refresh_interval" in settings and self.status == ModuleStatus.RUNNING:
                # Manager의 타이머 간격 변경 (현재는 고정값 사용)
                self.logger.info(f"Refresh interval updated to {settings['refresh_interval']}ms")
            
            # Bandwidth mode 변경 적용
            if "bandwidth_mode" in settings:
                mode = settings["bandwidth_mode"]
                self.receiver.set_bandwidth_mode(mode)
                # Update UI
                if mode == "lowest":
                    self.widget.bandwidth_combo.setCurrentIndex(1)
                else:
                    self.widget.bandwidth_combo.setCurrentIndex(0)
                
            return True
            
        except Exception as e:
            self.emit_error("SettingsError", str(e))
            return False
            
    def _on_refresh_requested(self):
        """새로고침 요청 처리"""
        if self.status == ModuleStatus.RUNNING:
            self.logger.info("Manual refresh requested")
            # Manager의 _scan_sources 메서드를 직접 호출
            self.manager._scan_sources()
            
    def _on_source_selected(self, source_name: str):
        """NDI 소스 선택 처리"""
        self.logger.info(f"NDI source selected: {source_name}")
        
    def _on_connect_requested(self, source_name: str):
        """NDI 소스 연결 요청 처리"""
        try:
            self.logger.info(f"Connecting to NDI source: {source_name}")
            
            # Manager에서 소스 객체 가져오기
            source_object = self.manager.get_source_object(source_name)
            
            if self.receiver.connect_to_source(source_name, source_object):
                self.receiver.start()
                self.widget.update_connection_status(True, source_name)
                self.logger.info(f"Successfully connected to: {source_name}")
            else:
                self.logger.error(f"Failed to connect to: {source_name}")
                
        except Exception as e:
            self.emit_error("ConnectionError", f"Failed to connect to source: {e}")
            
    def _on_disconnect_requested(self):
        """NDI 소스 연결 해제 요청 처리 - 스레드 안전 버전"""
        try:
            self.logger.info("Disconnecting from NDI source")
            
            if self.receiver.isRunning():
                # QVideoSink 연결 해제
                self.receiver.disconnect()
                self.receiver.quit()
                self.receiver.wait(1000)
            
            # 비디오 디스플레이 클리어
            if hasattr(self.widget, 'video_display'):
                self.widget.video_display.clear_display()
                
            self.widget.update_connection_status(False)
            self.logger.info("Disconnected from NDI source")
            
        except Exception as e:
            self.emit_error("DisconnectionError", f"Failed to disconnect: {e}")
            
    def _on_receiver_status_changed(self, status: str):
        """NDI 수신기 상태 변경 처리"""
        if status == "connected":
            self.logger.info("NDI receiver connected")
        elif status == "disconnected":
            self.widget.update_connection_status(False)
            self.logger.info("NDI receiver disconnected")
            
    def _on_receiver_error(self, error_msg: str):
        """NDI 수신기 에러 처리"""
        self.emit_error("ReceiverError", error_msg)
        self.widget.update_connection_status(False)
        
    def _on_manager_error(self, error_msg: str):
        """Manager 에러 처리"""
        self.emit_error("NDIError", error_msg)
        
        # 심각한 에러인 경우 사용자에게 알림
        if "initialize" in error_msg.lower():
            QMessageBox.critical(
                self.widget,
                "NDI Error",
                f"NDI 초기화 실패:\n{error_msg}\n\nNDI SDK가 올바르게 설치되었는지 확인하세요."
            )
            
    def _on_status_changed(self, status: str, message: str):
        """Manager 상태 변경 처리"""
        # 특정 상태에 대한 추가 처리가 필요한 경우
        if status == "error":
            self.set_status(ModuleStatus.ERROR, message)
    
    def pause_preview(self, srt_stream_info: dict = None):
        """NDI 프리뷰 일시정지 (SRT 스트리밍 시작 시)"""
        if self.receiver.is_connected():
            self.logger.info("Pausing NDI preview for SRT streaming")
            # 현재 소스 저장
            self.current_ndi_source = self.receiver.current_source
            # 수신 중지
            self.receiver.disconnect_source()
            # 프리뷰 상태 설정
            self.preview_paused = True
            
            # 비디오 디스플레이에 SRT 스트리밍 오버레이 표시
            if hasattr(self.widget, 'video_display'):
                stream_name = srt_stream_info.get('stream_name', '') if srt_stream_info else ''
                self.widget.video_display.set_srt_streaming(True, stream_name)
    
    def resume_preview(self):
        """NDI 프리뷰 재개 (SRT 스트리밍 종료 시)"""
        if self.preview_paused and self.current_ndi_source:
            self.logger.info("Resuming NDI preview after SRT streaming")
            # SRT 오버레이 제거
            if hasattr(self.widget, 'video_display'):
                self.widget.video_display.set_srt_streaming(False)
            # 이전 소스로 재연결
            source_name, source_object = self.current_ndi_source
            self._on_connect_requested(source_name)
            self.preview_paused = False
        elif hasattr(self.widget, 'video_display'):
            # 재연결할 소스가 없어도 오버레이는 제거
            self.widget.video_display.set_srt_streaming(False)
    
    def update_srt_stats(self, stats: dict):
        """SRT 스트리밍 통계 업데이트"""
        if self.preview_paused and hasattr(self.widget, 'video_display'):
            self.widget.video_display.srt_stats = stats
            self.widget.video_display.update()
    
    def get_ndi_sources(self) -> list:
        """현재 NDI 소스 목록 반환"""
        return self.manager.get_source_names()
    
    def _on_bandwidth_mode_changed(self, mode: str):
        """Bandwidth mode change handler"""
        self.logger.info(f"Bandwidth mode changed to: {mode}")
        self.settings["bandwidth_mode"] = mode
        self.receiver.set_bandwidth_mode(mode)
    
    def update_tally_states(self, tally_data: dict):
        """Update tally states for all NDI sources
        
        Args:
            tally_data: {source_name: "PGM"|"PVW"|""}
        """
        self.tally_states = tally_data.copy()
        
        # Update current source tally display if connected
        if self.current_ndi_source:
            source_name = self.current_ndi_source[0] if isinstance(self.current_ndi_source, tuple) else self.current_ndi_source
            current_tally = self.tally_states.get(source_name, "")
            
            # Update video display widget
            if hasattr(self.widget, 'video_display'):
                self.widget.video_display.set_tally_state(current_tally)
                self.logger.debug(f"Updated tally state for {source_name}: {current_tally}")