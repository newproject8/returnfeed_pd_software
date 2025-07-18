# ndi_receiver.py
import os
import sys
import time
from typing import Optional
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtMultimedia import QVideoSink, QVideoFrame
import logging
import numpy as np

# NDI SDK DLL 경로 설정
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

# Windows에서 DLL 경로 추가
if sys.platform == "win32" and hasattr(os, 'add_dll_directory'):
    try:
        if os.path.isdir(NDI_SDK_DLL_PATH):
            os.add_dll_directory(NDI_SDK_DLL_PATH)
    except Exception as e:
        pass

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    ndi = None


class NDIReceiver(QThread):
    """NDI 비디오 수신기 - QVideoSink 기반 스레드 안전 버전"""
    
    # 시그널
    frame_received = pyqtSignal(object)  # 수신된 프레임 - QImage 또는 dict{'image': QImage, 'resolution': str, 'fps': int, 'bitrate': str, 'audio_level': float}
    video_frame_ready = pyqtSignal(QVideoFrame)  # QVideoFrame 시그널 (신버전)
    error_occurred = pyqtSignal(str)  # 에러 메시지
    status_changed = pyqtSignal(str)  # 상태 변경
    debug_info = pyqtSignal(str)  # 🚀 ULTRATHINK 디버깅 정보
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = logging.getLogger("NDIReceiver")
        self.receiver = None
        self.source_name = ""
        self.running = False
        self.current_source = None  # 현재 연결된 소스 정보 저장
        self.bandwidth_mode = "highest"  # "highest" or "lowest" (proxy mode)
        
        # **핵심 수정**: QVideoSink 연결 지원
        self.video_sink = None
        self.frame_queue_size = 0
        self.max_queue_size = 3  # 메모리 절약을 위해 제한
        
        # 🚀 ULTRATHINK 디버깅: 상세 모니터링 변수들
        self.debug_enabled = False  # 성능 향상을 위해 기본값 False
        self.frame_count = 0
        self.last_debug_time = 0
        self.debug_interval = 5.0  # 5초마다 디버그 정보 출력
        self.memory_monitor_enabled = False  # 성능 향상을 위해 기본값 False
        
        # 프레임 레이트 제어 제거 - main_window의 QTimer가 정확한 60fps 제공
        self.target_fps = 60  # Target 60fps
        self.last_frame_time = 0
        self.frame_intervals = []  # 프레임 간격 추적
        
        # Technical info tracking
        self.current_resolution = ""
        self.current_fps = 0.0
        self.fps_calc_start_time = 0
        self.fps_frame_count = 0
        self.current_bitrate = "0 Mbps"
        self.current_audio_level = -60.0
        
        # 동적 비트레이트 계산을 위한 변수
        
        # 문서 기반 디버깅: 메모리 사용량 모니터링
        try:
            import psutil
            import gc
            self.psutil_available = True
            self.logger.info("🚀 ULTRATHINK: Memory monitoring enabled (psutil available)")
        except ImportError:
            self.psutil_available = False
            self.logger.warning("Memory monitoring disabled (psutil not available)")
        
    def connect_to_source(self, source_name: str, source_object=None) -> bool:
        """NDI 소스에 연결"""
        if not NDI_AVAILABLE:
            self.error_occurred.emit("NDI library not available")
            return False
            
        try:
            self.source_name = source_name
            self.current_source = (source_name, source_object)  # 현재 소스 저장
            
            # 직접 소스 객체가 제공된 경우 사용
            if source_object is not None:
                source = source_object
                self.logger.info(f"Using provided source object for: {source_name}")
            else:
                # 기존 방식: 소스 찾기 (호환성을 위해 유지)
                finder = None
                source = None
                
                # Finder 생성
                finder_functions = ['find_create_v2', 'find_create']
                for func_name in finder_functions:
                    if hasattr(ndi, func_name):
                        try:
                            func = getattr(ndi, func_name)
                            finder = func()
                            if finder:
                                break
                        except Exception:
                            continue
                            
                if not finder:
                    self.error_occurred.emit("Failed to create NDI finder")
                    return False
                    
                # 소스 검색
                sources = None
                source_functions = ['find_get_current_sources', 'get_current_sources']
                for func_name in source_functions:
                    if hasattr(ndi, func_name):
                        try:
                            func = getattr(ndi, func_name)
                            sources = func(finder)
                            if sources is not None:
                                break
                        except Exception:
                            continue
                            
                # 원하는 소스 찾기
                if sources:
                    for src in sources:
                        src_name = ""
                        if hasattr(src, 'name'):
                            src_name = src.name
                        elif hasattr(src, '__str__'):
                            src_name = str(src)
                            
                        if source_name in src_name:
                            source = src
                            break
                            
                # Finder 정리
                if finder:
                    try:
                        if hasattr(ndi, 'find_destroy'):
                            ndi.find_destroy(finder)
                    except Exception:
                        pass
                        
                if not source:
                    self.error_occurred.emit(f"Source '{source_name}' not found")
                    return False
                
            # Receiver 생성 - 올바른 RecvCreateV3 설정 방식 사용
            try:
                # RecvCreateV3 설정 객체 생성
                recv_create_v3 = ndi.RecvCreateV3()
                recv_create_v3.source_to_connect_to = source
                recv_create_v3.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA  # BGRA 포맷 강제
                
                # Bandwidth mode 설정
                if self.bandwidth_mode == "lowest":
                    recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_LOWEST  # Proxy mode (low bandwidth)
                    self.logger.info("Using PROXY mode (low bandwidth)")
                else:
                    recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST  # Normal mode (high quality)
                    self.logger.info("Using NORMAL mode (high quality)")
                    
                # 프록시 모드 최적화 설정
                if self.bandwidth_mode == "lowest":
                    recv_create_v3.allow_video_fields = False  # 프록시 모드: 필드 비활성화로 프레임레이트 안정화
                else:
                    recv_create_v3.allow_video_fields = True  # 일반 모드: 필드 허용
                # 추가 성능 최적화 설정
                if hasattr(recv_create_v3, 'p_ndi_recv_name'):
                    recv_create_v3.p_ndi_recv_name = "ReturnFeed High Performance Receiver"
                
                # Receiver 생성
                self.receiver = ndi.recv_create_v3(recv_create_v3)
                if self.receiver:
                    self.logger.info("NDI receiver created using recv_create_v3 with proper configuration")
                else:
                    raise Exception("recv_create_v3 returned None")
                    
            except Exception as e:
                self.logger.warning(f"Failed to create receiver with recv_create_v3: {e}")
                # 백업 방식 시도
                receiver_functions = ['recv_create_v3', 'RecvCreateV3']
                for func_name in receiver_functions:
                    if hasattr(ndi, func_name):
                        try:
                            func = getattr(ndi, func_name)
                            self.receiver = func()  # 빈 객체로 생성 후 연결
                            if self.receiver:
                                self.logger.info(f"NDI receiver created using fallback {func_name}")
                                break
                        except Exception as e2:
                            self.logger.warning(f"Failed to create receiver with fallback {func_name}: {e2}")
                            continue
                        
            if not self.receiver:
                self.error_occurred.emit("Failed to create NDI receiver")
                return False
            
            # 핵심: recv_connect 호출 추가!
            try:
                ndi.recv_connect(self.receiver, source)
                self.logger.info(f"Connected to NDI source: {source_name}")
                
                # NDI 소스 정보 확인
                if hasattr(self.receiver, 'get_performance'):
                    perf = self.receiver.get_performance()
                    self.logger.info(f"NDI 소스 성능 정보: {perf}")
                    
                self.status_changed.emit("connected")
                return True
            except Exception as e:
                self.logger.error(f"Failed to connect to source: {e}")
                self.error_occurred.emit(f"Connection failed: {e}")
                return False
            
        except Exception as e:
            self.error_occurred.emit(f"Connection error: {e}")
            return False
            
    def disconnect(self):
        """NDI 소스 연결 해제"""
        # 스레드에 정지 신호만 보내고, 실제 정리는 스레드가 종료될 때 수행
        self.running = False
        self.current_source = None
        self.status_changed.emit("disconnected")
    
    def disconnect_source(self):
        """NDI 소스 연결 해제 (프리뷰 일시정지용)"""
        self.running = False
        # current_source는 유지 (재연결용)
        self.status_changed.emit("paused")
        
    def pause_receiving(self):
        """NDI 수신 일시정지 (CPU 자원 절약)"""
        self.running = False
        self.logger.info("NDI receiving paused for resource saving")
        
    def resume_receiving(self):
        """NDI 수신 재개"""
        if self.receiver and self.current_source:
            self.running = True
            if not self.isRunning():
                self.start()
            self.logger.info("NDI receiving resumed")
    
    def is_connected(self) -> bool:
        """현재 연결 상태 확인"""
        return self.receiver is not None and self.running
    
    def set_bandwidth_mode(self, mode: str):
        """Set bandwidth mode (highest/lowest)"""
        if mode in ["highest", "lowest"]:
            self.bandwidth_mode = mode
            self.logger.info(f"Bandwidth mode set to: {mode}")
            
            # 프록시 모드일 때 프레임 처리 최적화
            if mode == "lowest":
                self.logger.info("프록시 모드 활성화 - 프레임 처리 최적화")
                # 프록시 모드에서는 디버그 비활성화로 성능 향상
                self.debug_enabled = False
                self.memory_monitor_enabled = False
            
            # If currently connected, reconnect with new bandwidth
            if self.is_connected() and self.current_source:
                self.logger.info("Reconnecting with new bandwidth mode...")
                source_name, source_object = self.current_source
                self.disconnect()
                self.wait(500)  # Wait for disconnect
                self.connect_to_source(source_name, source_object)
                self.start()
        else:
            self.logger.warning(f"Invalid bandwidth mode: {mode}")
    
    def _calculate_dynamic_bitrate(self, width, height, fps, actual_frame_size=None):
        """동적 비트레이트 계산 - 해상도와 압축률 고려"""
        # Raw 데이터 비트레이트 계산 (bits per second)
        # width * height * 4 bytes/pixel * 8 bits/byte * fps
        raw_bps = width * height * 4 * 8 * fps
        raw_mbps = raw_bps / 1_000_000
        
        # 실제 프레임 크기 기반 계산 (같은 PC 내부 NDI 검증용)
        if actual_frame_size and fps > 0:
            actual_bps = actual_frame_size * 8 * fps
            actual_mbps = actual_bps / 1_000_000
            
            # 실제 데이터와 이론 데이터 비교
            if not hasattr(self, '_frame_size_logged'):
                mode = "프록시" if self.bandwidth_mode == "lowest" else "일반"
                self.logger.info(f"[{mode} 모드] 실제 프레임 분석:")
                self.logger.info(f"  이론 크기: {raw_mbps:.1f} Mbps")
                self.logger.info(f"  실제 크기: {actual_mbps:.1f} Mbps")
                self.logger.info(f"  비율: {actual_mbps/raw_mbps:.2f}x")
                if actual_mbps > raw_mbps * 1.5:
                    self.logger.info(f"  🚨 같은 PC 내부 NDI는 압축을 건너뛸 수 있습니다!")
                self._frame_size_logged = True
            
            # 실제 데이터 크기가 이론값보다 훨씬 크면 압축 없음으로 판단
            if actual_mbps > raw_mbps * 0.8:
                return actual_mbps
        
        # 해상도와 모드에 따른 압축률 적용
        if self.bandwidth_mode == "lowest":
            # 프록시 모드: H.264/H.265 수준 압축률
            # 사용자 요청 기준: 640x360 60fps = 30 Mbps 최대
            if width == 640 and height == 360:
                if fps >= 60:
                    # 640x360 60fps: 30 Mbps 목표
                    compression_ratio = 30.0 / raw_mbps
                else:
                    # 30fps: 15 Mbps 목표
                    compression_ratio = 15.0 / raw_mbps
            elif width <= 640 and height <= 360:
                # 다른 소형 해상도
                compression_ratio = 0.068 if fps >= 60 else 0.034
            elif width <= 1280 and height <= 720:
                # HD: H.264 효율적 압축
                compression_ratio = 0.04 if fps >= 60 else 0.03
            elif width == 1920 and height == 1080:
                # Full HD: 사용자 요청 기준
                if fps >= 60:
                    # FHD 60fps 프록시: 120 Mbps 최대
                    compression_ratio = 120.0 / raw_mbps
                else:
                    # FHD 30fps 프록시: 100 Mbps
                    compression_ratio = 100.0 / raw_mbps
            elif width <= 1920 and height <= 1080:
                # 다른 Full HD 해상도
                compression_ratio = 0.06 if fps >= 60 else 0.05
            else:
                # 4K 이상: 최고 압축률
                compression_ratio = 0.015 if fps >= 60 else 0.01
        else:
            # 일반 모드: SpeedHQ 압축률 (NDI 문서 기반 정확한 값)
            # 문서에서 정확한 비트레이트를 역산하여 압축률 계산
            if width == 1280 and height == 720:
                # 720p 정확한 값
                if fps >= 60:
                    # 720p60: 105.83 Mbps / (1280*720*4*8*60/1e6) = 0.1196
                    compression_ratio = 105.83 / raw_mbps
                elif fps >= 50:
                    # 720p50: 96.94 Mbps
                    compression_ratio = 96.94 / raw_mbps
                else:
                    compression_ratio = 0.11
            elif width == 1920 and height == 1080:
                # 1080p 정확한 값 (사용자 요청 기준)
                if fps >= 60:
                    # 1080p60: 165.17 Mbps (사용자 지정 최대값)
                    compression_ratio = 165.17 / raw_mbps
                elif fps >= 50:
                    # 1080p50: 125.59 Mbps
                    compression_ratio = 125.59 / raw_mbps
                else:
                    compression_ratio = 0.051
            elif width == 3840 and height == 2160:
                # 4K 정확한 값
                if fps >= 60:
                    # 4K60: 249.99 Mbps
                    compression_ratio = 249.99 / raw_mbps
                elif fps >= 50:
                    # 4K50: 223.80 Mbps
                    compression_ratio = 223.80 / raw_mbps
                else:
                    compression_ratio = 0.028
            else:
                # 다른 해상도는 근사값 사용
                if width <= 1280 and height <= 720:
                    compression_ratio = 0.12 if fps >= 60 else 0.11
                elif width <= 1920 and height <= 1080:
                    compression_ratio = 0.066 if fps >= 60 else 0.051
                elif width <= 2560 and height <= 1440:
                    compression_ratio = 0.055 if fps >= 60 else 0.045
                elif width <= 3840 and height <= 2160:
                    compression_ratio = 0.031 if fps >= 60 else 0.028
                else:
                    compression_ratio = 0.025
        
        # 압축된 비트레이트 계산
        compressed_mbps = raw_mbps * compression_ratio
        
        # 최소값 보장
        compressed_mbps = max(compressed_mbps, 0.1)
        
        # 로그 (처음 한 번만)
        if not hasattr(self, '_bitrate_calc_logged'):
            mode = "프록시" if self.bandwidth_mode == "lowest" else "일반"
            self.logger.info(f"[{mode} 모드] {width}x{height}@{int(fps)}fps")
            self.logger.info(f"  Raw: {raw_mbps:.1f} Mbps → Compressed: {compressed_mbps:.1f} Mbps (압축률 {compression_ratio*100:.1f}%)")
            self.logger.info(f"  💡 같은 PC 내부 NDI는 압축을 건너뛸 수 있습니다!")
            self._bitrate_calc_logged = True
        
        return compressed_mbps
        
    def run(self):
        """비디오 수신 스레드"""
        if not self.receiver:
            return
            
        self.running = True
        self.logger.info("NDI receiver thread started")
        
        # 스레드 우선순위 높이기 (실시간 비디오 처리)
        try:
            import sys
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetCurrentThread()
                kernel32.SetThreadPriority(handle, 2)  # THREAD_PRIORITY_HIGHEST
                self.logger.info("Thread priority set to highest")
        except Exception as e:
            self.logger.warning(f"Failed to set thread priority: {e}")
        
        try:
            while self.running:
                try:
                    # 프레임 수신 타임아웃 최적화
                    # 프록시 모드는 비블로킹으로 최대 성능 확보
                    if self.bandwidth_mode == "lowest":
                        # 프록시 모드: 비블로킹으로 가능한 한 빨리 프레임 수신
                        timeout_ms = 0  # Non-blocking for maximum performance
                    else:
                        # 일반 모드: 60fps를 위한 적절한 타임아웃
                        timeout_ms = 16  # 16.67ms for 60fps
                    
                    frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2(self.receiver, timeout_ms)
                    
                    # 비디오 프레임 처리
                    if frame_type == ndi.FRAME_TYPE_VIDEO and v_frame is not None:
                        try:
                            if v_frame.data is not None and v_frame.data.size > 0:
                                # **🚀 ULTRATHINK 방탄화**: 문서 기반 완벽한 메모리 관리
                                try:
                                    # 🚀 ULTRATHINK 디버깅: NDI 프레임 수신 직후 상태 확인 (디버그 모드에서만)
                                    # if self.debug_enabled:
                                    #     self._detailed_frame_analysis(v_frame)
                                    
                                    # Extract frame info before copying
                                    width = getattr(v_frame, 'xres', 0)
                                    height = getattr(v_frame, 'yres', 0)
                                    
                                    # Update resolution if changed
                                    if width > 0 and height > 0:
                                        new_resolution = f"{width}x{height}"
                                        if new_resolution != self.current_resolution:
                                            self.current_resolution = new_resolution
                                            self.logger.info(f"Resolution changed to: {self.current_resolution}")
                                    
                                    # 프레임 카운터 및 성능 모니터링 (모든 모드에서 필요)
                                    self.frame_count += 1
                                    self.fps_frame_count += 1
                                    
                                    # FPS 및 비트레이트 계산
                                    current_time = time.perf_counter()  # 더 정확한 타이머
                                    
                                    # Calculate FPS every second
                                    if self.fps_calc_start_time == 0:
                                        self.fps_calc_start_time = current_time
                                    elif current_time - self.fps_calc_start_time >= 1.0:
                                        elapsed = current_time - self.fps_calc_start_time
                                        raw_fps = self.fps_frame_count / elapsed
                                        
                                        # FPS를 합리적인 범위로 제한 (일반적인 비디오 표준)
                                        # 60fps 소스는 실제로 59.94fps일 수 있음
                                        if raw_fps > 60.5:
                                            self.current_fps = 60.0
                                        elif raw_fps > 59.5 and raw_fps <= 60.5:
                                            self.current_fps = 60.0  # 59.94fps를 60fps로 표시
                                        elif raw_fps > 29.5 and raw_fps <= 30.5:
                                            self.current_fps = 30.0  # 29.97fps를 30fps로 표시
                                        else:
                                            self.current_fps = round(raw_fps, 1)
                                        
                                        # FPS 로그 (디버깅용)
                                        if self.bandwidth_mode == "lowest":
                                            # 프록시 모드 FPS 항상 로그
                                            if self.current_fps < 50:
                                                self.logger.warning(f"프록시 모드 FPS 저하: {self.current_fps:.1f} fps (목표: 60fps)")
                                            else:
                                                self.logger.info(f"프록시 모드 FPS: {self.current_fps:.1f} fps")
                                        elif self.current_fps < 55:  # 일반 모드에서 55fps 미만일 때만
                                            self.logger.info(f"일반 모드 FPS: {self.current_fps:.1f} fps")
                                        self.fps_frame_count = 0
                                        self.fps_calc_start_time = current_time
                                    
                                    # 동적 비트레이트 계산 (해상도, FPS, 압축률 기반)
                                    if hasattr(v_frame, 'xres') and hasattr(v_frame, 'yres') and self.current_fps > 0:
                                        # 실제 프레임 크기 계산 (line_stride_in_bytes * yres)
                                        actual_frame_size = None
                                        if hasattr(v_frame, 'line_stride_in_bytes') and hasattr(v_frame, 'yres'):
                                            actual_frame_size = v_frame.line_stride_in_bytes * v_frame.yres
                                        
                                        dynamic_bitrate = self._calculate_dynamic_bitrate(
                                            v_frame.xres, 
                                            v_frame.yres, 
                                            self.current_fps,
                                            actual_frame_size
                                        )
                                        
                                        # 포맷팅
                                        if dynamic_bitrate >= 1000:
                                            self.current_bitrate = f"{dynamic_bitrate/1000:.1f} Gbps"
                                        else:
                                            self.current_bitrate = f"{dynamic_bitrate:.1f} Mbps"
                                    else:
                                        self.current_bitrate = "계산 중..."
                                    
                                    # 프레임 데이터 복사 (프록시 모드 최적화)
                                    # 프록시 모드는 작은 프레임이므로 단순 복사가 더 빠름
                                    if self.bandwidth_mode == "lowest":
                                        # 프록시 모드: 즉시 복사 (작은 프레임이므로 오버헤드 적음)
                                        frame_data_copy = v_frame.data.copy()
                                    else:
                                        # 일반 모드: 안전한 깊은 복사
                                        frame_data_copy = v_frame.data.copy()
                                    
                                    # 2. 복사 직후 NDI 프레임 즉시 해제 (Use-After-Free 방지)
                                    ndi.recv_free_video_v2(self.receiver, v_frame)
                                    v_frame = None  # 명시적으로 None 설정하여 실수 방지
                                    
                                    # 🚀 ULTRATHINK 디버깅: 메모리 모니터링 (디버그 모드에서만)
                                    # if self.debug_enabled:
                                    #     self._monitor_performance()
                                    
                                    # 프레임 타이밍 기록 (항상 필요 - FPS 계산용)
                                    self.last_frame_time = current_time
                                    
                                    # 디버그 분석은 분리된 메서드에서만
                                    if self.debug_enabled:
                                        self._debug_frame_timing(current_time)
                                    
                                    # 복사된 데이터로 안전한 프레임 처리
                                    try:
                                        # 프록시 모드는 더 빠른 처리
                                        if self.bandwidth_mode == "lowest":
                                            image = self._create_qimage_fast(frame_data_copy)
                                        else:
                                            image = self._create_qimage_bulletproof(frame_data_copy)
                                        if image:
                                            # Emit frame data as dict with technical info
                                            frame_dict = {
                                                'image': image,
                                                'resolution': self.current_resolution,
                                                'fps': int(round(self.current_fps)),
                                                'bitrate': self.current_bitrate,
                                                'audio_level': self.current_audio_level
                                            }
                                            self.frame_received.emit(frame_dict)
                                            self.frame_queue_size = 1  # 간단한 카운터 유지
                                                    
                                    except Exception as qvf_error:
                                        if self.debug_enabled:
                                            self.logger.warning(f"Frame processing failed: {qvf_error}")
                                        
                                except Exception as copy_error:
                                    self.logger.error(f"Frame copy error: {copy_error}")
                                    # NDI 프레임이 아직 해제되지 않았다면 해제
                                    if v_frame is not None and self.receiver is not None:
                                        try:
                                            ndi.recv_free_video_v2(self.receiver, v_frame)
                                        except Exception as free_error:
                                            self.logger.warning(f"Emergency frame free failed: {free_error}")
                            
                        except Exception as e:
                            self.logger.error(f"Frame processing error: {e}")
                            # 에러 발생 시에도 NDI 프레임 해제 확인
                            if v_frame is not None and self.receiver is not None:
                                try:
                                    ndi.recv_free_video_v2(self.receiver, v_frame)
                                except Exception as free_error:
                                    self.logger.warning(f"Error cleanup frame free failed: {free_error}")
                    
                    elif frame_type == ndi.FRAME_TYPE_AUDIO and a_frame is not None:
                        try:
                            # 오디오 프레임은 별도 처리 (NDI 표준 비트레이트 사용)
                            
                            # Calculate audio level from audio frame
                            if hasattr(a_frame, 'data') and a_frame.data is not None:
                                try:
                                    audio_data = a_frame.data
                                    if audio_data.size > 0:
                                        # Calculate RMS (Root Mean Square) for audio level
                                        rms = np.sqrt(np.mean(audio_data**2))
                                        # Convert to dB (with protection against log(0))
                                        if rms > 0:
                                            db = 20 * np.log10(rms)
                                            # Clamp to reasonable range
                                            self.current_audio_level = max(-60.0, min(0.0, db))
                                        else:
                                            self.current_audio_level = -60.0
                                except Exception as audio_e:
                                    # Keep previous audio level on error
                                    pass
                        finally:
                            # 오디오 프레임 메모리 해제 - 안전한 해제
                            if a_frame is not None and self.receiver is not None:
                                try:
                                    ndi.recv_free_audio_v2(self.receiver, a_frame)
                                except Exception as free_error:
                                    self.logger.warning(f"Failed to free audio frame: {free_error}")
                    
                    elif frame_type == ndi.FRAME_TYPE_METADATA and m_frame is not None:
                        try:
                            # 메타데이터 프레임은 별도 처리 (NDI 표준 비트레이트 사용)
                            pass
                        finally:
                            # 메타데이터 프레임 메모리 해제 - 안전한 해제
                            if m_frame is not None and self.receiver is not None:
                                try:
                                    ndi.recv_free_metadata(self.receiver, m_frame)
                                except Exception as free_error:
                                    self.logger.warning(f"Failed to free metadata frame: {free_error}")
                    
                    elif frame_type == ndi.FRAME_TYPE_ERROR:
                        self.logger.error("NDI FRAME_TYPE_ERROR received. Attempting recovery...")
                        self.error_occurred.emit("NDI source reported an error")
                        # 즉시 재시도 (프록시 모드 성능 향상)
                        continue
                    
                    elif frame_type == ndi.FRAME_TYPE_NONE:
                        # 타임아웃 - 프록시 모드에서는 더 자주 발생
                        if self.bandwidth_mode == "lowest":
                            # 프록시 모드: 적절한 대기로 CPU 사용률 감소
                            self.msleep(8)  # 8ms 대기 (약 120fps 루프)
                        else:
                            # 일반 모드: 즉시 재시도
                            pass
                        continue
                            
                except Exception as e:
                    self.logger.error(f"Receive loop error: {e}")
                    # 연속된 에러로 인한 무한 루프 방지
                    if "recv_free" in str(e):
                        self.logger.warning("Memory free error detected - continuing without delay")
                        continue  # 지연 없이 계속
                    else:
                        # 심각한 에러만 짧은 대기
                        self.msleep(1)  # 최소한의 대기
                    
        finally:
            # 스레드 종료 시 receiver 정리
            self.logger.info("NDI receiver thread stopping...")
            if self.receiver:
                try:
                    ndi.recv_destroy(self.receiver)
                    self.receiver = None
                    self.logger.info("NDI receiver destroyed")
                except Exception as e:
                    self.logger.error(f"Error destroying receiver: {e}")
            
            self.running = False
            self.logger.info("NDI receiver thread stopped")
        
    def _convert_frame_to_qimage_safe(self, video_frame, frame_data_copy) -> Optional[QImage]:
        """안전한 프레임 변환 - 복사된 데이터 사용"""
        try:
            # 프레임 정보 추출
            width = getattr(video_frame, 'xres', 0)
            height = getattr(video_frame, 'yres', 0)
            
            if not width or not height or frame_data_copy is None:
                return None
            
            # 복사된 데이터 사용
            frame_data = frame_data_copy
            
            # 실제 데이터 크기로부터 픽셀당 바이트 계산
            total_pixels = width * height
            bytes_per_pixel = frame_data.size // total_pixels if total_pixels > 0 else 0
            
            # 첫 번째 프레임에서 포맷 정보 로깅
            if not hasattr(self, '_format_logged'):
                fourcc = getattr(video_frame, 'FourCC', None)
                frame_format = getattr(video_frame, 'frame_format_type', None)
                line_stride = getattr(video_frame, 'line_stride_in_bytes', None)
                self.logger.info(f"SAFE Frame format - Width: {width}, Height: {height}")
                self.logger.info(f"Data size: {frame_data.size}, Bytes/pixel: {bytes_per_pixel}")
                self.logger.info(f"FourCC: {fourcc}, Format: {frame_format}, Line stride: {line_stride}")
                self._format_logged = True
            
            # BGRA 포맷 처리 (4 bytes per pixel)
            if bytes_per_pixel == 4:
                expected_size = width * height * 4
                
                if frame_data.size >= expected_size:
                    try:
                        # 프레임 데이터를 (height, width, 4) 형태로 변환
                        image_data = frame_data[:expected_size].reshape((height, width, 4))
                        
                        # BGRA를 RGB로 변환 (Alpha 채널 제거)
                        rgb_data = image_data[:, :, [2, 1, 0]]  # B,G,R,A -> R,G,B
                        
                        # QImage 생성
                        qimage = QImage(
                            rgb_data.tobytes(),
                            width, height,
                            width * 3,
                            QImage.Format.Format_RGB888
                        )
                        
                        if not qimage.isNull():
                            return qimage
                    except Exception as e:
                        self.logger.warning(f"SAFE BGRA conversion failed: {e}")
            
            elif bytes_per_pixel == 2:
                # YUV 422 처리 (향상된 변환)
                if not hasattr(self, '_yuv_warning_shown'):
                    self.logger.warning(f"Still receiving YUV format despite BGRA forced!")
                    self._yuv_warning_shown = True
                
                try:
                    expected_size = width * height * 2
                    if frame_data.size >= expected_size:
                        # 간단한 그레이스케일 변환
                        gray_data = frame_data[::2][:total_pixels]  # Y 채널만 추출
                        if len(gray_data) >= total_pixels:
                            gray_image = gray_data[:total_pixels].reshape((height, width))
                            rgb_data = np.stack([gray_image, gray_image, gray_image], axis=-1)
                            
                            qimage = QImage(
                                rgb_data.tobytes(),
                                width, height,
                                width * 3,
                                QImage.Format.Format_RGB888
                            )
                            
                            if not qimage.isNull():
                                return qimage
                except Exception as yuv_e:
                    self.logger.error(f"YUV conversion failed: {yuv_e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Safe frame conversion error: {e}")
            return None
    
    def _convert_frame_to_qimage(self, video_frame) -> Optional[QImage]:
        """NDI 비디오 프레임을 QImage로 변환 - 강화된 포맷 지원"""
        try:
            # 프레임 정보 추출
            width = getattr(video_frame, 'xres', 0)
            height = getattr(video_frame, 'yres', 0)
            data = getattr(video_frame, 'data', None)
            
            if not width or not height or data is None:
                self.logger.warning(f"Invalid frame: width={width}, height={height}, data={data is not None}")
                return None
            
            # 프레임 포맷 정보 출력 (디버깅용)
            fourcc = getattr(video_frame, 'FourCC', None)
            frame_format = getattr(video_frame, 'frame_format_type', None)
            line_stride = getattr(video_frame, 'line_stride_in_bytes', None)
            
            # NumPy 배열로 변환 - 안전한 방식
            if hasattr(data, 'size') and data.size > 0:
                # 메모리 연속성 확보 - NumPy flags 안전 접근
                try:
                    # NumPy 버전별 flags 접근 방식 호환
                    if hasattr(data, 'flags'):
                        try:
                            is_contiguous = data.flags.get('C_CONTIGUOUS', True) if hasattr(data.flags, 'get') else data.flags['C_CONTIGUOUS']
                        except (KeyError, AttributeError):
                            is_contiguous = True  # 안전한 기본값
                        
                        if not is_contiguous:
                            frame_data = np.ascontiguousarray(data)
                        else:
                            frame_data = data
                    else:
                        frame_data = data
                except Exception as flag_e:
                    # flags 접근 실패 시 그냥 원본 사용
                    self.logger.debug(f"NumPy flags check failed: {flag_e}")
                    frame_data = data
                
                # 실제 데이터 크기로부터 픽셀당 바이트 계산
                total_pixels = width * height
                bytes_per_pixel = frame_data.size // total_pixels if total_pixels > 0 else 0
                
                # 첫 번째 프레임에서 포맷 정보 로깅
                if not hasattr(self, '_format_logged'):
                    self.logger.info(f"Frame format - Width: {width}, Height: {height}")
                    self.logger.info(f"Data size: {frame_data.size}, Bytes/pixel: {bytes_per_pixel}")
                    self.logger.info(f"FourCC: {fourcc}, Format: {frame_format}, Line stride: {line_stride}")
                    self._format_logged = True
                
                # 포맷에 따른 처리
                if bytes_per_pixel == 4:
                    # BGRA/BGRX 포맷 (4 bytes per pixel)
                    expected_size = width * height * 4
                    
                    if frame_data.size >= expected_size:
                        try:
                            # 프레임 데이터를 (height, width, 4) 형태로 변환
                            image_data = frame_data[:expected_size].reshape((height, width, 4))
                            
                            # BGRA를 RGB로 변환 (Alpha 채널 제거)
                            rgb_data = image_data[:, :, [2, 1, 0]]  # B,G,R,A -> R,G,B
                            
                            # QImage 생성
                            qimage = QImage(
                                rgb_data.tobytes(),
                                width, height,
                                width * 3,
                                QImage.Format.Format_RGB888
                            )
                            
                            if not qimage.isNull():
                                return qimage
                            else:
                                self.logger.warning("Created QImage is null")
                                
                        except Exception as e:
                            self.logger.warning(f"BGRA conversion failed: {e}")
                            
                elif bytes_per_pixel == 2:
                    # YUV 422 포맷 감지 - BGRA 강제했는데 YUV가 오면 설정 문제
                    if not hasattr(self, '_yuv_warning_shown'):
                        self.logger.warning(f"Still receiving YUV format despite BGRA forced! This indicates a configuration issue.")
                        self.logger.info(f"Will attempt YUV to RGB conversion as fallback...")
                        self._yuv_warning_shown = True
                    
                    # 개선된 YUV 422 색상 변환
                    try:
                        # YUV422 팩킹: UYVY 또는 YUYV 포맷
                        expected_size = width * height * 2
                        if frame_data.size >= expected_size:
                            yuv_data = frame_data[:expected_size].reshape((height, width * 2))
                            
                            # YUYV 포맷 가정 (Y0 U Y1 V 패턴)
                            y_data = yuv_data[:, ::2]  # Y 채널
                            u_data = yuv_data[:, 1::4]  # U 채널
                            v_data = yuv_data[:, 3::4]  # V 채널
                            
                            # U, V 채널을 Y 채널 크기로 업샘플링
                            u_upsampled = np.repeat(u_data, 2, axis=1)
                            v_upsampled = np.repeat(v_data, 2, axis=1)
                            
                            # YUV to RGB 변환 (간단한 변환)
                            y_norm = y_data.astype(np.float32)
                            u_norm = u_upsampled.astype(np.float32) - 128
                            v_norm = v_upsampled.astype(np.float32) - 128
                            
                            r = np.clip(y_norm + 1.402 * v_norm, 0, 255).astype(np.uint8)
                            g = np.clip(y_norm - 0.344 * u_norm - 0.714 * v_norm, 0, 255).astype(np.uint8)
                            b = np.clip(y_norm + 1.772 * u_norm, 0, 255).astype(np.uint8)
                            
                            # RGB 이미지 생성
                            rgb_data = np.stack([r, g, b], axis=-1)
                            
                            qimage = QImage(
                                rgb_data.tobytes(),
                                width, height,
                                width * 3,
                                QImage.Format.Format_RGB888
                            )
                            
                            if not qimage.isNull():
                                return qimage
                        else:
                            # 데이터 크기 부족 - 그레이스케일 폴백
                            gray_data = frame_data[::2][:total_pixels]  # Y 채널만 추출
                            if len(gray_data) >= total_pixels:
                                gray_image = gray_data[:total_pixels].reshape((height, width))
                                rgb_data = np.stack([gray_image, gray_image, gray_image], axis=-1)
                                
                                qimage = QImage(
                                    rgb_data.tobytes(),
                                    width, height,
                                    width * 3,
                                    QImage.Format.Format_RGB888
                                )
                                
                                if not qimage.isNull():
                                    return qimage
                                
                    except Exception as yuv_e:
                        self.logger.error(f"YUV conversion failed: {yuv_e}")
                        # 최종 폴백: 그레이스케일 이미지
                        try:
                            gray_data = frame_data[::2]  # Y 채널만
                            if len(gray_data) >= total_pixels:
                                gray_image = gray_data[:total_pixels].reshape((height, width))
                                rgb_data = np.stack([gray_image, gray_image, gray_image], axis=-1)
                                
                                qimage = QImage(
                                    rgb_data.tobytes(),
                                    width, height,
                                    width * 3,
                                    QImage.Format.Format_RGB888
                                )
                                
                                if not qimage.isNull():
                                    return qimage
                        except Exception:
                            pass
                    
                else:
                    # 지원되지 않는 포맷 경고 (한 번만 표시)
                    if not hasattr(self, '_unsupported_format_warned'):
                        self.logger.warning(f"Unsupported format: {bytes_per_pixel} bytes per pixel (total size: {frame_data.size})")
                        self.logger.info(f"Expected: 4 bytes/pixel (BGRA) or 2 bytes/pixel (YUV422)")
                        self._unsupported_format_warned = True
                    
            else:
                if not hasattr(self, '_empty_frame_warned'):
                    self.logger.warning("Frame data is empty or invalid")
                    self._empty_frame_warned = True
                    
        except Exception as e:
            self.logger.error(f"Frame conversion error: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
        return None
    
    def _convert_to_qvideo_frame_safe(self, video_frame, frame_data_copy) -> Optional[QVideoFrame]:
        """안전한 QVideoFrame 변환 - 스레드 안전 버전"""
        try:
            # 프레임 정보 추출
            width = getattr(video_frame, 'xres', 0)
            height = getattr(video_frame, 'yres', 0)
            
            if not width or not height or frame_data_copy is None:
                return None
            
            # 복사된 데이터 사용
            frame_data = frame_data_copy
            
            # 실제 데이터 크기로부터 픽셀당 바이트 계산
            total_pixels = width * height
            bytes_per_pixel = frame_data.size // total_pixels if total_pixels > 0 else 0
            
            # BGRA 포맷 처리 (4 bytes per pixel)
            if bytes_per_pixel == 4:
                expected_size = width * height * 4
                
                if frame_data.size >= expected_size:
                    try:
                        # 프레임 데이터를 (height, width, 4) 형태로 변환
                        image_data = frame_data[:expected_size].reshape((height, width, 4))
                        
                        # BGRA를 RGB로 변환 (Alpha 채널 제거)
                        rgb_data = image_data[:, :, [2, 1, 0]]  # B,G,R,A -> R,G,B
                        
                        # QImage 생성
                        qimage = QImage(
                            rgb_data.tobytes(),
                            width, height,
                            width * 3,
                            QImage.Format.Format_RGB888
                        )
                        
                        if not qimage.isNull():
                            # QVideoFrame 생성
                            video_frame_obj = QVideoFrame(qimage)
                            return video_frame_obj
                            
                    except Exception as e:
                        self.logger.warning(f"BGRA to QVideoFrame conversion failed: {e}")
            
            elif bytes_per_pixel == 2:
                # YUV 422 처리 - 그레이스케일 변환
                try:
                    expected_size = width * height * 2
                    if frame_data.size >= expected_size:
                        # 간단한 그레이스케일 변환
                        gray_data = frame_data[::2][:total_pixels]  # Y 채널만 추출
                        if len(gray_data) >= total_pixels:
                            gray_image = gray_data[:total_pixels].reshape((height, width))
                            rgb_data = np.stack([gray_image, gray_image, gray_image], axis=-1)
                            
                            qimage = QImage(
                                rgb_data.tobytes(),
                                width, height,
                                width * 3,
                                QImage.Format.Format_RGB888
                            )
                            
                            if not qimage.isNull():
                                return QVideoFrame(qimage)
                                
                except Exception as yuv_e:
                    self.logger.error(f"YUV to QVideoFrame conversion failed: {yuv_e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"QVideoFrame conversion error: {e}")
            return None
    
    def _reset_frame_queue_counter(self):
        """프레임 큐 카운터 리셋 - 메인 스레드에서 실행"""
        self.frame_queue_size = 0
    
    def _convert_to_qvideo_frame_bulletproof(self, frame_data_copy) -> Optional[QVideoFrame]:
        """🚀 ULTRATHINK 방탄화: 문서 기반 완벽한 QVideoFrame 변환"""
        try:
            # 복사된 데이터에서 차원 정보 추출
            if len(frame_data_copy.shape) != 3:
                self.logger.error(f"Invalid frame shape: {frame_data_copy.shape}")
                return None
                
            height, width, channels = frame_data_copy.shape
            
            # 문서 권장: 스트라이드를 명시적으로 전달
            stride = frame_data_copy.strides[0]  # 첫 번째 차원의 스트라이드
            
            # 포맷 검증 및 변환
            if channels == 4:
                # BGRA 포맷 처리
                try:
                    # BGRA를 RGB로 변환 (Alpha 채널 제거)
                    rgb_data = frame_data_copy[:, :, [2, 1, 0]]  # B,G,R,A -> R,G,B
                    
                    # 문서 권장: 명시적 스트라이드로 QImage 생성
                    qimage = QImage(
                        rgb_data.tobytes(),
                        width, height,
                        width * 3,  # RGB 스트라이드
                        QImage.Format.Format_RGB888
                    )
                    
                    if not qimage.isNull():
                        # 문서 권장: QImage가 기본 버퍼를 소유하도록 강제
                        qimage.bits().setsize(rgb_data.nbytes)
                        
                        # QVideoFrame 생성
                        video_frame = QVideoFrame(qimage)
                        return video_frame
                        
                except Exception as e:
                    self.logger.warning(f"BGRA to QVideoFrame conversion failed: {e}")
                    
            elif channels == 2:
                # YUV 422 처리 - 그레이스케일 변환
                try:
                    total_pixels = width * height
                    gray_data = frame_data_copy.flatten()[::2][:total_pixels]  # Y 채널만
                    
                    if len(gray_data) >= total_pixels:
                        gray_image = gray_data.reshape((height, width))
                        rgb_data = np.stack([gray_image, gray_image, gray_image], axis=-1)
                        
                        qimage = QImage(
                            rgb_data.tobytes(),
                            width, height,
                            width * 3,
                            QImage.Format.Format_RGB888
                        )
                        
                        if not qimage.isNull():
                            qimage.bits().setsize(rgb_data.nbytes)
                            return QVideoFrame(qimage)
                            
                except Exception as yuv_e:
                    self.logger.error(f"YUV to QVideoFrame conversion failed: {yuv_e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Bulletproof QVideoFrame conversion error: {e}")
            return None
    
    def _create_qimage_fast(self, frame_data_copy) -> Optional[QImage]:
        """프록시 모드 전용 빠른 QImage 생성"""
        try:
            if len(frame_data_copy.shape) != 3:
                return None
                
            height, width, channels = frame_data_copy.shape
            
            if channels == 4:
                # BGRA 형식 - 직접 사용
                bytes_per_line = width * 4
                # 복사 없이 바로 QImage 생성
                qimage = QImage(
                    frame_data_copy.data,
                    width, height,
                    bytes_per_line,
                    QImage.Format.Format_ARGB32
                )
                
                if not qimage.isNull():
                    # 프록시 모드: 이미 복사된 데이터이므로 추가 복사 불필요
                    return qimage
                    
            elif channels == 3:
                # RGB 형식
                bytes_per_line = width * 3
                qimage = QImage(
                    frame_data_copy.data,
                    width, height,
                    bytes_per_line,
                    QImage.Format.Format_RGB888
                )
                
                if not qimage.isNull():
                    return qimage
                    
            return None
            
        except Exception as e:
            self.logger.debug(f"Fast QImage creation failed: {e}")
            return None
    
    def _create_qimage_bulletproof(self, frame_data_copy) -> Optional[QImage]:
        """🚀 ULTRATHINK 방탄화: 문서 기반 완벽한 QImage 생성"""
        try:
            # 복사된 데이터에서 차원 정보 추출
            if len(frame_data_copy.shape) != 3:
                self.logger.error(f"Invalid frame shape for QImage: {frame_data_copy.shape}")
                return None
                
            height, width, channels = frame_data_copy.shape
            
            # 포맷별 처리
            if channels == 4:
                # BGRA 포맷 처리 - 직접 사용하여 변환 오버헤드 제거
                try:
                    # BGRA 데이터를 직접 사용 (변환 없음!)
                    bytes_per_line = width * 4
                    qimage = QImage(
                        frame_data_copy.data,  # NumPy 배열의 원시 데이터 포인터
                        width, height,
                        bytes_per_line,  # BGRA 스트라이드
                        QImage.Format.Format_ARGB32  # Qt의 BGRA 포맷
                    )
                    
                    if not qimage.isNull():
                        # 프레임 데이터가 이미 복사본이므로 추가 복사 최소화
                        # 성능 향상을 위해 copy() 제거
                        return qimage
                        
                except Exception as e:
                    self.logger.warning(f"BGRA to QImage conversion failed: {e}")
                    
            elif channels == 2:
                # YUV 422 처리 - 개선된 그레이스케일 변환
                try:
                    total_pixels = width * height
                    # Y 채널만 추출 (더 안전한 방식)
                    gray_data = frame_data_copy.flatten()[::2][:total_pixels]
                    
                    if len(gray_data) >= total_pixels:
                        gray_image = gray_data.reshape((height, width))
                        rgb_data = np.stack([gray_image, gray_image, gray_image], axis=-1)
                        
                        qimage = QImage(
                            rgb_data.tobytes(),
                            width, height,
                            width * 3,
                            QImage.Format.Format_RGB888
                        )
                        
                        if not qimage.isNull():
                            qimage.bits().setsize(rgb_data.nbytes)
                            return qimage
                            
                except Exception as yuv_e:
                    self.logger.error(f"YUV to QImage conversion failed: {yuv_e}")
            
            else:
                self.logger.warning(f"Unsupported channel count: {channels}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Bulletproof QImage creation error: {e}")
            return None
    
    def set_video_sink(self, video_sink: Optional[QVideoSink]):
        """🚀 ULTRATHINK: 레거시 호환성을 위한 더미 메서드 - QPainter 직접 렌더링에서는 사용하지 않음"""
        # QPainter 직접 렌더링 방식에서는 QVideoSink를 사용하지 않음
        # 기존 코드와의 호환성을 위해 메서드만 유지
        if video_sink:
            self.logger.info("⚠️ QVideoSink 설정 시도 - QPainter 직접 렌더링 모드에서는 무시됨")
        else:
            self.logger.info("✅ QPainter 직접 렌더링 모드 - QVideoSink 블랙박스 완전 우회")
    
    def _debug_frame_timing(self, current_time):
        """디버그 모드에서만 프레임 타이밍 분석"""
        if self.last_frame_time > 0:
            interval = current_time - self.last_frame_time
            self.frame_intervals.append(interval)
            
            # 프록시 모드에서 프레임 간격 분석 (1초마다)
            if self.bandwidth_mode == "lowest" and len(self.frame_intervals) > 50:
                avg_interval = sum(self.frame_intervals) / len(self.frame_intervals)
                expected_interval = 1.0 / 60.0  # 60fps = 16.67ms
                if avg_interval > expected_interval * 1.2:  # 20% 이상 차이
                    self.logger.warning(f"프록시 모드 프레임 간격 문제: 평균 {avg_interval*1000:.1f}ms (예상: {expected_interval*1000:.1f}ms)")
                self.frame_intervals = []  # 리셋
    
    def _detailed_frame_analysis(self, v_frame):
        """🚀 ULTRATHINK 디버깅: 문서 기반 NDI 프레임 상세 분석"""
        try:
            frame_info = []
            frame_info.append(f"Frame pointer: {hex(id(v_frame))}")
            
            if hasattr(v_frame, 'data') and v_frame.data is not None:
                data = v_frame.data
                frame_info.append(f"Data pointer: {hex(id(data))}")
                frame_info.append(f"Data dtype: {data.dtype}")
                frame_info.append(f"Data shape: {data.shape}")
                frame_info.append(f"Data size: {data.size}")
                
                # NumPy flags 상세 정보
                if hasattr(data, 'flags'):
                    try:
                        frame_info.append(f"C_CONTIGUOUS: {data.flags['C_CONTIGUOUS']}")
                        frame_info.append(f"ALIGNED: {data.flags['ALIGNED']}")
                        frame_info.append(f"WRITEABLE: {data.flags['WRITEABLE']}")
                    except Exception as flag_e:
                        frame_info.append(f"Flags access error: {flag_e}")
            
            # NDI 프레임 속성
            if hasattr(v_frame, 'xres'):
                frame_info.append(f"Width: {v_frame.xres}")
            if hasattr(v_frame, 'yres'):
                frame_info.append(f"Height: {v_frame.yres}")
            if hasattr(v_frame, 'FourCC'):
                frame_info.append(f"FourCC: {v_frame.FourCC}")
            if hasattr(v_frame, 'frame_format_type'):
                frame_info.append(f"Format: {v_frame.frame_format_type}")
            if hasattr(v_frame, 'line_stride_in_bytes'):
                frame_info.append(f"Line stride: {v_frame.line_stride_in_bytes}")
            
            # 처음 몇 프레임에 대해서만 상세 로깅
            if self.frame_count < 5:
                self.logger.info(f"🔍 Frame {self.frame_count} analysis: " + "; ".join(frame_info))
                
        except Exception as e:
            self.logger.error(f"Frame analysis error: {e}")
    
    def _monitor_performance(self):
        """🚀 ULTRATHINK 디버깅: 문서 기반 성능 및 메모리 모니터링"""
        try:
            import time
            current_time = time.time()
            
            # 일정 간격마다만 디버그 정보 출력
            if current_time - self.last_debug_time >= self.debug_interval:
                debug_info = []
                debug_info.append(f"Frames processed: {self.frame_count}")
                debug_info.append(f"Queue size: {self.frame_queue_size}/{self.max_queue_size}")
                
                # FPS 계산
                if self.last_debug_time > 0:
                    elapsed = current_time - self.last_debug_time
                    fps = self.frame_count / elapsed if elapsed > 0 else 0
                    debug_info.append(f"Avg FPS: {fps:.1f}")
                
                # 메모리 사용량 모니터링 (문서 권장)
                if self.psutil_available and self.memory_monitor_enabled:
                    try:
                        import psutil
                        import gc
                        
                        process = psutil.Process()
                        memory_info = process.memory_info()
                        debug_info.append(f"RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
                        debug_info.append(f"VMS: {memory_info.vms / 1024 / 1024:.1f} MB")
                        debug_info.append(f"Objects: {len(gc.get_objects())}")
                        
                    except Exception as mem_e:
                        debug_info.append(f"Memory monitor error: {mem_e}")
                
                # 디버그 정보 출력
                debug_message = "🚀 PERFORMANCE: " + "; ".join(debug_info)
                self.logger.info(debug_message)
                self.debug_info.emit(debug_message)
                
                # 카운터 리셋
                self.last_debug_time = current_time
                self.frame_count = 0
                
        except Exception as e:
            self.logger.error(f"Performance monitoring error: {e}")
    
    def _monitor_qimage_creation(self, frame_data_copy, success: bool, error_msg: str = ""):
        """🚀 ULTRATHINK 디버깅: QImage 생성 과정 모니터링 (문서 권장)"""
        try:
            if success:
                self.logger.debug(f"✅ QImage creation successful - Shape: {frame_data_copy.shape}")
            else:
                self.logger.warning(f"❌ QImage creation failed: {error_msg}")
                self.debug_info.emit(f"QImage creation failed: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"QImage monitoring error: {e}")