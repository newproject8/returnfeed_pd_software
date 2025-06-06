#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cyndilib 기반 고성능 NDI 수신기
프레임 동기화 및 성능 최적화를 위해 cyndilib의 FrameSync 기능 사용
"""

import time
import threading
import queue
import numpy as np
from typing import Optional, Callable, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

try:
    import cyndilib
    from cyndilib.receiver import Receiver
    from cyndilib.finder import Finder
    from cyndilib import RecvColorFormat, RecvBandwidth
    from cyndilib.framesync import FrameSyncThread, ReceiveFrameType
    CYNDILIB_AVAILABLE = True
except ImportError:
    CYNDILIB_AVAILABLE = False
    print("[CyndiReceiver] cyndilib를 사용할 수 없습니다. 기본 NDI 라이브러리를 사용합니다.")


class CyndiNDIReceiver(QObject):
    """
    cyndilib 기반 고성능 NDI 수신기
    
    주요 기능:
    - FrameSync를 통한 자동 프레임 동기화
    - 버퍼링 및 클럭 타이밍 기법으로 비디오/오디오 동기화
    - 타이밍 지터 보정으로 안정적인 프레임 수신
    - 고성능 Cython 기반 구현
    """
    
    # PyQt 시그널
    frame_received = pyqtSignal(np.ndarray, int, int, int)  # frame_data, width, height, fourcc
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    info_message = pyqtSignal(str)
    sources_changed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if not CYNDILIB_AVAILABLE:
            self.error_occurred.emit("cyndilib를 사용할 수 없습니다. pip install cyndilib로 설치해주세요.")
            return
            
        # cyndilib 객체들
        self.receiver: Optional[Receiver] = None
        self.finder: Optional[Finder] = None
        self.frame_sync_thread: Optional[FrameSyncThread] = None
        
        # 상태 관리
        self.is_connected = False
        self.is_running = False
        self.current_source = None
        
        # 프레임 처리를 위한 큐와 스레드 - 버퍼 크기 증가로 안정성 향상
        self.frame_queue = queue.Queue(maxsize=10)  # 최대 10프레임 버퍼로 증가
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # 성능 모니터링
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # FPS 모니터링 타이머
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._update_fps_info)
        self.fps_timer.start(1000)  # 1초마다 FPS 업데이트
        
    def start_finder(self):
        """NDI 소스 검색 시작"""
        if not CYNDILIB_AVAILABLE:
            return
            
        try:
            if self.finder is None:
                self.finder = Finder()
                
            # 소스 검색 스레드 시작
            finder_thread = threading.Thread(target=self._find_sources_loop, daemon=True)
            finder_thread.start()
            
            self.info_message.emit("NDI 소스 검색을 시작했습니다.")
            
        except Exception as e:
            self.error_occurred.emit(f"소스 검색 시작 실패: {str(e)}")
            
    def connect_to_source(self, source_info: Dict[str, Any], bandwidth_mode: str = "Original"):
        """NDI 소스에 연결"""
        if not CYNDILIB_AVAILABLE:
            return
            
        try:
            # 기존 연결 해제
            self.disconnect_source()
            
            source_name = source_info.get('name', '')
            self.info_message.emit(f"NDI 소스 연결 중: {source_name}")
            
            # 수신기 생성 - NDI SDK 성능 최적화 적용
            self.receiver = Receiver(
                color_format=RecvColorFormat.fastest,  # 최고 성능을 위해 fastest 사용
                bandwidth=self._get_bandwidth_mode(bandwidth_mode),
                allow_video_fields=False,  # 프로그레시브 스캔만 허용하여 성능 향상
                p_ndi_name="NDI Tally Receiver"  # 수신기 이름 설정
            )
            
            # 소스 연결
            source_obj = self._create_source_object(source_info)
            if source_obj:
                self.receiver.connect(source_obj)
                self.current_source = source_info
                
                # FrameSync 스레드 시작
                self._start_frame_sync()
                
                # 프레임 처리 스레드 시작
                self._start_processing_thread()
                
                self.is_connected = True
                self.connection_status_changed.emit(True)
                self.info_message.emit(f"NDI 소스에 연결되었습니다: {source_name}")
            else:
                self.error_occurred.emit("소스 객체 생성에 실패했습니다.")
                
        except Exception as e:
            self.error_occurred.emit(f"소스 연결 실패: {str(e)}")
            
    def disconnect_source(self):
        """현재 소스 연결 해제"""
        try:
            self.is_connected = False
            self.stop_event.set()
            
            # FrameSync 스레드 중지
            if self.frame_sync_thread:
                self.frame_sync_thread.stop()
                self.frame_sync_thread = None
                
            # 처리 스레드 중지
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=1.0)
                
            # 수신기 해제
            if self.receiver:
                self.receiver.disconnect()
                self.receiver = None
                
            self.current_source = None
            self.connection_status_changed.emit(False)
            self.info_message.emit("NDI 소스 연결이 해제되었습니다.")
            
            # 이벤트 리셋
            self.stop_event.clear()
            
        except Exception as e:
            self.error_occurred.emit(f"소스 연결 해제 실패: {str(e)}")
            
    def cleanup(self):
        """리소스 정리"""
        self.disconnect_source()
        
        if self.finder:
            self.finder = None
            
        self.fps_timer.stop()
        
    def _get_bandwidth_mode(self, bandwidth_mode: str):
        """대역폭 모드 변환"""
        if bandwidth_mode == "Original":
            return RecvBandwidth.highest
        elif bandwidth_mode == "Proxy":
            return RecvBandwidth.lowest
        else:
            return RecvBandwidth.highest
            
    def _create_source_object(self, source_info: Dict[str, Any]):
        """소스 객체 생성"""
        try:
            # cyndilib의 Source 객체 생성
            from cyndilib.finder import Source
            
            source = Source()
            source.name = source_info.get('name', '')
            source.url_address = source_info.get('url', '')
            
            return source
            
        except Exception as e:
            self.error_occurred.emit(f"소스 객체 생성 실패: {str(e)}")
            return None
            
    def _start_frame_sync(self):
        """FrameSync 스레드 시작"""
        try:
            if self.receiver and self.receiver.frame_sync:
                # 비디오 프레임 수신을 위한 FrameSyncThread 생성
                self.frame_sync_thread = FrameSyncThread(
                    self.receiver.frame_sync,
                    ReceiveFrameType.recv_video
                )
                
                # 프레임 수신 콜백 설정
                self.frame_sync_thread.set_callback(self._on_frame_received)
                
                # 스레드 시작
                self.frame_sync_thread.start()
                
                self.info_message.emit("FrameSync 스레드가 시작되었습니다.")
                
        except Exception as e:
            self.error_occurred.emit(f"FrameSync 시작 실패: {str(e)}")
            
    def _on_frame_received(self, frame_sync):
        """FrameSync에서 프레임 수신 시 호출되는 콜백"""
        try:
            if not self.is_connected:
                return
                
            # 비디오 프레임 캡처
            frame_sync.capture_video()
            video_frame = frame_sync.video_frame
            
            if video_frame and video_frame.get_data_size() > 0:
                # 프레임 데이터를 numpy 배열로 변환
                frame_data = self._convert_frame_to_numpy(video_frame)
                
                if frame_data is not None:
                    # 프레임 데이터와 메타데이터를 함께 저장
                    width, height = video_frame.get_resolution()
                    fourcc = video_frame.get_fourcc()
                    fourcc_int = int(fourcc) if hasattr(fourcc, '__int__') else 0
                    
                    frame_info = (frame_data, width, height, fourcc_int)
                    
                    # 프레임 큐에 추가 (논블로킹)
                    try:
                        self.frame_queue.put_nowait(frame_info)
                        self.frame_count += 1
                    except queue.Full:
                        # 큐가 가득 찬 경우 오래된 프레임 제거
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame_info)
                        except queue.Empty:
                            pass
                            
        except Exception as e:
            self.error_occurred.emit(f"프레임 수신 오류: {str(e)}")
            
    def _convert_frame_to_numpy(self, video_frame) -> Optional[np.ndarray]:
        """cyndilib VideoFrame을 numpy 배열로 변환 - 성능 최적화 및 호환성 개선"""
        try:
            # 프레임 해상도 및 포맷 정보 가져오기
            width, height = video_frame.get_resolution()
            fourcc = video_frame.get_fourcc()
            
            if width <= 0 or height <= 0:
                return None
                
            # 프레임 데이터를 numpy 배열로 변환
            # cyndilib의 VideoFrame은 buffer protocol을 지원
            frame_data = np.frombuffer(video_frame, dtype=np.uint8)
            
            # OpenCV import를 한 번만 수행
            import cv2
            
            # FourCC에 따른 형태 변환 - NDI SDK 모범 사례 적용
            fourcc_name = fourcc.name if hasattr(fourcc, 'name') else str(fourcc)
            
            if fourcc_name in ['UYVY', 'YUV2', 'UYVP']:
                # YUV 422 포맷 - NDI의 기본 고성능 포맷
                try:
                    # UYVY는 width가 2의 배수여야 함
                    if width % 2 != 0:
                        width = width - 1
                    
                    frame_data = frame_data[:height * width * 2]  # UYVY는 픽셀당 2바이트
                    uyvy_frame = frame_data.reshape((height, width, 2))
                    bgr_frame = cv2.cvtColor(uyvy_frame, cv2.COLOR_YUV2BGR_UYVY)
                    return bgr_frame
                except Exception as e:
                    print(f"[CyndiReceiver] UYVY 변환 오류: {e}")
                    return None
                
            elif fourcc_name in ['BGRA', 'BGRX']:
                # BGRA/BGRX 포맷 - 알파 채널 포함
                try:
                    channels = 4
                    expected_size = height * width * channels
                    if len(frame_data) >= expected_size:
                        bgra_frame = frame_data[:expected_size].reshape((height, width, channels))
                        # BGRA를 BGR로 변환 (알파 채널 제거)
                        bgr_frame = cv2.cvtColor(bgra_frame, cv2.COLOR_BGRA2BGR)
                        return bgr_frame
                except Exception as e:
                    print(f"[CyndiReceiver] BGRA 변환 오류: {e}")
                    return None
                    
            elif fourcc_name in ['RGBA', 'RGBX']:
                # RGBA/RGBX 포맷
                try:
                    channels = 4
                    expected_size = height * width * channels
                    if len(frame_data) >= expected_size:
                        rgba_frame = frame_data[:expected_size].reshape((height, width, channels))
                        # RGBA를 BGR로 변환
                        bgr_frame = cv2.cvtColor(rgba_frame, cv2.COLOR_RGBA2BGR)
                        return bgr_frame
                except Exception as e:
                    print(f"[CyndiReceiver] RGBA 변환 오류: {e}")
                    return None
                    
            elif fourcc_name in ['P216', 'PA16']:
                # 16비트 고정밀도 포맷 - NDI의 고품질 포맷
                try:
                    # 16비트 데이터를 8비트로 변환
                    frame_16bit = np.frombuffer(video_frame, dtype=np.uint16)
                    frame_8bit = (frame_16bit >> 8).astype(np.uint8)  # 상위 8비트 사용
                    
                    if fourcc_name == 'P216':
                        # Y + UV 플레인
                        y_size = width * height
                        uv_size = y_size // 2
                        
                        if len(frame_8bit) >= y_size + uv_size:
                            # NV12 형태로 재구성 후 BGR 변환
                            yuv_frame = np.zeros((height * 3 // 2, width), dtype=np.uint8)
                            yuv_frame[:height, :] = frame_8bit[:y_size].reshape((height, width))
                            uv_data = frame_8bit[y_size:y_size + uv_size].reshape((height // 2, width))
                            yuv_frame[height:, :] = uv_data
                            
                            bgr_frame = cv2.cvtColor(yuv_frame, cv2.COLOR_YUV2BGR_NV12)
                            return bgr_frame
                except Exception as e:
                    print(f"[CyndiReceiver] P216/PA16 변환 오류: {e}")
                    return None
                    
            elif fourcc_name == 'NV12':
                # NV12 포맷 (Y + UV) - 효율적인 4:2:0 포맷
                try:
                    y_size = width * height
                    uv_size = y_size // 2
                    
                    if len(frame_data) >= y_size + uv_size:
                        yuv_frame = frame_data[:y_size + uv_size]
                        yuv_reshaped = yuv_frame.reshape((height * 3 // 2, width))
                        bgr_frame = cv2.cvtColor(yuv_reshaped, cv2.COLOR_YUV2BGR_NV12)
                        return bgr_frame
                except Exception as e:
                    print(f"[CyndiReceiver] NV12 변환 오류: {e}")
                    return None
                    
            else:
                # 알려지지 않은 포맷 - 기본 RGB/BGR로 시도
                try:
                    total_pixels = width * height
                    channels = len(frame_data) // total_pixels
                    
                    if channels == 3:
                        # RGB 포맷으로 가정
                        rgb_frame = frame_data[:total_pixels * 3].reshape((height, width, 3))
                        bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
                        return bgr_frame
                    elif channels == 4:
                        # RGBA 포맷으로 가정
                        rgba_frame = frame_data[:total_pixels * 4].reshape((height, width, 4))
                        bgr_frame = cv2.cvtColor(rgba_frame, cv2.COLOR_RGBA2BGR)
                        return bgr_frame
                except Exception as e:
                    print(f"[CyndiReceiver] 기본 포맷 변환 오류: {e}")
                    
            print(f"[CyndiReceiver] 지원되지 않는 포맷: {fourcc_name}")
            return None
            
        except Exception as e:
            print(f"[CyndiReceiver] 프레임 변환 오류: {e}")
            return None
            
    def _start_processing_thread(self):
        """프레임 처리 스레드 시작"""
        self.processing_thread = threading.Thread(target=self._process_frames_loop, daemon=True)
        self.processing_thread.start()
        
    def _process_frames_loop(self):
        """프레임 처리 루프"""
        while not self.stop_event.is_set():
            try:
                # 프레임 큐에서 프레임 정보 가져오기 (타임아웃 설정)
                frame_info = self.frame_queue.get(timeout=0.1)
                
                if frame_info is not None:
                    # 프레임 정보 분해
                    frame_data, width, height, fourcc = frame_info
                    
                    # PyQt 시그널로 프레임 전송 (4개 매개변수)
                    self.frame_received.emit(frame_data, width, height, fourcc)
                    
            except queue.Empty:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    self.error_occurred.emit(f"프레임 처리 오류: {str(e)}")
                    
    def _find_sources_loop(self):
        """소스 검색 루프"""
        last_sources = []
        
        while True:
            try:
                if self.finder:
                    # 소스 검색 (1초 대기)
                    if self.finder.wait_for_sources(1000):
                        sources = self.finder.get_current_sources()
                        
                        # 소스 목록이 변경된 경우에만 시그널 발송
                        current_sources = []
                        for source in sources:
                            source_info = {
                                'name': source.name,
                                'url': source.url_address
                            }
                            current_sources.append(source_info)
                            
                        if current_sources != last_sources:
                            self.sources_changed.emit(current_sources)
                            last_sources = current_sources.copy()
                            
                time.sleep(2)  # 2초마다 검색
                
            except Exception as e:
                self.error_occurred.emit(f"소스 검색 오류: {str(e)}")
                time.sleep(5)  # 오류 시 5초 대기
                
    def _update_fps_info(self):
        """FPS 정보 업데이트"""
        current_time = time.time()
        time_diff = current_time - self.last_fps_time
        
        if time_diff > 0:
            self.current_fps = self.frame_count / time_diff
            
            if self.is_connected and self.current_fps > 0:
                self.info_message.emit(f"수신 FPS: {self.current_fps:.1f}")
                
        self.frame_count = 0
        self.last_fps_time = current_time
        
    def get_current_fps(self) -> float:
        """현재 FPS 반환"""
        return self.current_fps
        
    def is_receiver_connected(self) -> bool:
        """수신기 연결 상태 반환"""
        return self.is_connected