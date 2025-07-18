# srt_module.py
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QTimer
import logging

from modules import BaseModule, ModuleStatus
from .srt_manager import SRTManager
from .srt_widget import SRTWidget


class SRTModule(BaseModule):
    """SRT 스트리밍 모듈 - MediaMTX 서버로 직접 전송"""
    
    # 추가 시그널
    streaming_started = pyqtSignal(str, str)  # ndi_source, stream_name
    streaming_stopped = pyqtSignal()
    request_ndi_sources = pyqtSignal()  # NDI 소스 목록 요청
    request_preview_control = pyqtSignal(bool)  # True=pause, False=resume
    
    def __init__(self, parent=None):
        super().__init__("SRT", parent)
        self.srt_manager = None
        self.widget = None
        self.ndi_sources = []
        self.current_ndi_source = None
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats)
        self._initialized = False  # Track initialization state
        
    def initialize(self) -> bool:
        """모듈 초기화"""
        try:
            self.set_status(ModuleStatus.INITIALIZING, "SRT 모듈 초기화 중...")
            
            # Manager가 없으면 생성 (fallback)
            if self.srt_manager is None:
                self.srt_manager = SRTManager()
                self.logger.info("SRT manager created in initialize (fallback)")
            
            # 시그널 연결
            self.srt_manager.stream_status_changed.connect(self._on_stream_status_changed)
            self.srt_manager.stream_error.connect(self._on_stream_error)
            self.srt_manager.stream_stats_updated.connect(self._on_stream_stats)
            
            # FFmpeg 확인
            if not self.srt_manager.check_ffmpeg():
                self.logger.warning("FFmpeg not found in PATH. SRT streaming will not work.")
                # FFmpeg가 없어도 모듈은 초기화되도록 함 (UI는 표시)
            
            # Widget이 없으면 생성 (fallback)
            if self.widget is None:
                self.widget = SRTWidget(self)
                self.logger.info("SRT widget created in initialize (fallback)")
            
            self.set_status(ModuleStatus.IDLE, "SRT 모듈 준비 완료")
            self.logger.info("SRT module initialization completed")
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"SRT module initialization failed: {e}", exc_info=True)
            self.emit_error("Initialization Error", str(e))
            return False
    
    def start(self) -> bool:
        """모듈 시작"""
        try:
            self.set_status(ModuleStatus.RUNNING, "SRT 모듈 활성화")
            return True
        except Exception as e:
            self.emit_error("Start Error", str(e))
            return False
    
    def stop(self) -> bool:
        """모듈 정지"""
        try:
            self.set_status(ModuleStatus.STOPPING, "SRT 모듈 정지 중...")
            
            # 스트리밍 중이면 중지
            if self.srt_manager and self.srt_manager.is_streaming:
                self.stop_streaming()
            
            # 타이머 중지
            self.stats_timer.stop()
            
            self.set_status(ModuleStatus.STOPPED, "SRT 모듈 정지됨")
            return True
            
        except Exception as e:
            self.emit_error("Stop Error", str(e))
            return False
    
    def cleanup(self) -> None:
        """리소스 정리"""
        if self.srt_manager:
            self.srt_manager.stop_streaming()
            self.srt_manager = None
        
        if self.widget:
            self.widget = None
    
    def get_widget(self) -> QWidget:
        """UI 위젯 반환"""
        # If not initialized yet, try to initialize first
        if not self._initialized and self.widget is None:
            self.logger.warning("get_widget called before initialization, attempting to initialize...")
            if not self.initialize():
                self.logger.error("Failed to initialize SRT module in get_widget")
        
        if self.widget is None:
            # Try to create widget if it doesn't exist (lazy initialization)
            try:
                # Ensure manager exists first
                if self.srt_manager is None:
                    self.srt_manager = SRTManager()
                    self.logger.info("SRT manager created in get_widget (emergency)")
                
                # Create widget
                self.widget = SRTWidget(self)
                self.logger.info("SRT widget created in get_widget (emergency)")
            except Exception as e:
                self.logger.error(f"Failed to create SRT widget: {e}", exc_info=True)
                # Return emergency widget with error details
                from PyQt6.QtWidgets import QLabel
                error_msg = f"SRT 모듈 초기화 실패\n\n오류: {str(e)}"
                emergency_widget = QLabel(error_msg)
                emergency_widget.setStyleSheet("color: red; padding: 20px;")
                emergency_widget.setWordWrap(True)
                return emergency_widget
        return self.widget
    
    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        return {
            'media_mtx_server': self.srt_manager.media_mtx_server if self.srt_manager else 'returnfeed.net',
            'srt_port': self.srt_manager.srt_port if self.srt_manager else 8890,
            'last_bitrate': self.widget.get_bitrate() if self.widget else '2M',
            'last_fps': self.widget.get_fps() if self.widget else 30,
            'auto_resume_preview': self.widget.auto_resume_preview if self.widget else True
        }
    
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 적용"""
        try:
            if self.srt_manager:
                # MediaMTX 서버 설정 업데이트
                server = settings.get('media_mtx_server', 'returnfeed.net')
                port = settings.get('srt_port', 8890)
                self.srt_manager.update_server_config(server, port)
            
            if self.widget:
                # UI 설정 적용
                self.widget.set_bitrate(settings.get('last_bitrate', '2M'))
                self.widget.set_fps(settings.get('last_fps', 30))
                self.widget.auto_resume_preview = settings.get('auto_resume_preview', True)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to apply settings: {e}")
            return False
    
    def update_ndi_sources(self, sources: list):
        """NDI 소스 목록 업데이트 (NDI 모듈에서 호출)"""
        self.ndi_sources = sources
        if self.widget:
            self.widget.update_ndi_sources(sources)
    
    def start_streaming(self, ndi_source: str, stream_name: str, bitrate: str, fps: int):
        """SRT 스트리밍 시작"""
        try:
            if not ndi_source or not stream_name:
                raise ValueError("NDI 소스와 스트림 이름이 필요합니다")
            
            # NDI 프리뷰 일시정지 요청
            self.request_preview_control.emit(True)
            
            # SRT 스트리밍 시작
            self.srt_manager.start_ndi_streaming(ndi_source, stream_name, bitrate, fps)
            
            self.current_ndi_source = ndi_source
            self.streaming_started.emit(ndi_source, stream_name)
            
            # 통계 업데이트 시작
            self.stats_timer.start(2000)  # 2초마다
            
            self.logger.info(f"SRT streaming started: {ndi_source} -> {stream_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            # 실패 시 프리뷰 재개
            self.request_preview_control.emit(False)
            raise
    
    def stop_streaming(self):
        """SRT 스트리밍 중지"""
        try:
            # 통계 타이머 중지
            self.stats_timer.stop()
            
            # SRT 스트리밍 중지
            if self.srt_manager:
                self.srt_manager.stop_streaming()
            
            # 프리뷰 재개 여부 확인
            if self.widget and self.widget.auto_resume_preview:
                self.request_preview_control.emit(False)
            
            self.current_ndi_source = None
            self.streaming_stopped.emit()
            
            self.logger.info("SRT streaming stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
    
    def _on_stream_status_changed(self, status: str):
        """스트림 상태 변경 처리"""
        if self.widget:
            self.widget.update_status(status)
    
    def _on_stream_error(self, error: str):
        """스트림 오류 처리"""
        self.emit_error("Stream Error", error)
        # 오류 시 스트리밍 중지 및 프리뷰 재개
        self.stop_streaming()
    
    def _on_stream_stats(self, stats: dict):
        """스트림 통계 업데이트"""
        if self.widget:
            self.widget.update_stats(stats)
    
    def _update_stats(self):
        """통계 업데이트 타이머 콜백"""
        if self.srt_manager and self.srt_manager.is_streaming:
            info = self.srt_manager.get_stream_info()
            if self.widget:
                self.widget.update_stream_info(info)