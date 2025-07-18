# pd_app/core/ndi_manager_optimized.py
"""
NDI Manager - 성능 최적화 버전
GUI 응답성 개선을 위한 프레임 처리 최적화
"""

import sys
import time
import logging
import threading
from collections import deque
from dataclasses import dataclass

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    
try:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, QMutex, QMutexLocker
except ImportError:
    # Qt가 없는 환경에서도 기본 기능 사용 가능
    class QObject: pass
    class QThread: pass
    class pyqtSignal:
        def __init__(self, *args): pass
        def emit(self, *args): pass
        def connect(self, *args): pass
    class QTimer: pass
    class QMutex: pass
    class QMutexLocker: pass

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    logging.warning("NDIlib not available - using simulator")
    try:
        from . import ndi_simulator as ndi
        NDI_AVAILABLE = True
        logging.info("NDI 시뮬레이터 모드 활성화")
    except ImportError:
        logging.error("NDI 시뮬레이터도 로드 실패")

logger = logging.getLogger(__name__)

# 성능 설정
FRAME_BUFFER_SIZE = 3  # 프레임 버퍼 크기
GUI_UPDATE_FPS = 15    # GUI 업데이트 프레임레이트 (15fps)
FRAME_SKIP_INTERVAL = 4  # 4프레임당 1개만 처리

@dataclass
class FrameData:
    """프레임 데이터 컨테이너"""
    data: np.ndarray
    timestamp: float
    width: int
    height: int
    
def safe_decode(value):
    """안전한 문자열 디코딩"""
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except:
            return value.decode('utf-8', errors='ignore')
    return str(value)

class NDIWorkerThread(QThread):
    """NDI 작업을 처리하는 최적화된 워커 스레드"""
    
    # 시그널 - 프레임 레이트 제한을 위해 별도 처리
    frame_available = pyqtSignal()  # 프레임이 준비됨을 알림
    sources_updated = pyqtSignal(list)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.running = False
        self.current_source = None
        
        # 프레임 버퍼 (링 버퍼)
        self.frame_buffer = deque(maxlen=FRAME_BUFFER_SIZE)
        self.buffer_mutex = QMutex()
        
        # 프레임 스킵 카운터
        self.frame_counter = 0
        self.last_gui_update = 0
        
        # 성능 통계
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.actual_fps = 0
        
    def get_latest_frame(self):
        """가장 최신 프레임 반환 (thread-safe)"""
        with QMutexLocker(self.buffer_mutex):
            if self.frame_buffer:
                return self.frame_buffer[-1]  # 가장 최신 프레임
            return None
    
    def run(self):
        """스레드 실행 - 최적화된 버전"""
        self.running = True
        self.status_changed.emit("NDI 워커 스레드 시작")
        logger.info("NDI 워커: 최적화된 워커 스레드 시작")
        
        # Windows 스레드 우선순위 설정
        if sys.platform == "win32":
            try:
                import ctypes
                handle = ctypes.windll.kernel32.GetCurrentThread()
                ctypes.windll.kernel32.SetThreadPriority(handle, 1)  # THREAD_PRIORITY_ABOVE_NORMAL
                logger.info("NDI 워커 스레드 우선순위 설정 완료")
            except Exception as e:
                logger.warning(f"스레드 우선순위 설정 실패: {e}")
        
        last_frame_time = time.time()
        
        while self.running:
            try:
                if self.receiver and self.current_source:
                    # NDI 프레임 수신 (non-blocking)
                    try:
                        result = ndi.recv_capture_v2(self.receiver, 0)  # 0ms timeout for non-blocking
                        
                        if isinstance(result, tuple) and len(result) == 4:
                            frame_type, v_frame, a_frame, m_frame = result
                        else:
                            continue
                    except Exception as recv_error:
                        logger.error(f"recv_capture_v2 호출 오류: {recv_error}")
                        time.sleep(0.001)
                        continue
                    
                    # 비디오 프레임 처리
                    if frame_type == ndi.FRAME_TYPE_VIDEO and v_frame and v_frame.data is not None:
                        self.frame_counter += 1
                        
                        # FPS 계산
                        current_time = time.time()
                        self.fps_counter += 1
                        if current_time - self.fps_timer >= 1.0:
                            self.actual_fps = self.fps_counter
                            self.fps_counter = 0
                            self.fps_timer = current_time
                            logger.debug(f"NDI 실제 FPS: {self.actual_fps}")
                        
                        # 프레임 스킵 로직
                        if self.frame_counter % FRAME_SKIP_INTERVAL == 0:
                            # GUI 업데이트 레이트 제한
                            time_since_last_update = current_time - self.last_gui_update
                            min_update_interval = 1.0 / GUI_UPDATE_FPS
                            
                            if time_since_last_update >= min_update_interval:
                                try:
                                    # 프레임 데이터 처리 (복사 최소화)
                                    if NUMPY_AVAILABLE and hasattr(v_frame.data, 'shape'):
                                        # 버퍼에 프레임 추가 (복사 없이 참조만)
                                        frame_data = FrameData(
                                            data=v_frame.data,  # 복사하지 않음
                                            timestamp=current_time,
                                            width=v_frame.xres,
                                            height=v_frame.yres
                                        )
                                        
                                        with QMutexLocker(self.buffer_mutex):
                                            self.frame_buffer.append(frame_data)
                                        
                                        # GUI 업데이트 시그널 (데이터는 전달하지 않음)
                                        self.frame_available.emit()
                                        self.last_gui_update = current_time
                                        
                                except Exception as e:
                                    logger.error(f"프레임 처리 오류: {e}")
                        
                        # 비디오 프레임 메모리 해제
                        try:
                            ndi.recv_free_video_v2(self.receiver, v_frame)
                        except:
                            pass
                    
                    # 오디오/메타데이터 프레임 해제
                    if frame_type == ndi.FRAME_TYPE_AUDIO and a_frame:
                        try:
                            ndi.recv_free_audio_v2(self.receiver, a_frame)
                        except:
                            pass
                    
                    if frame_type == ndi.FRAME_TYPE_METADATA and m_frame:
                        try:
                            ndi.recv_free_metadata(self.receiver, m_frame)
                        except:
                            pass
                    
                    # CPU 사용률 제어
                    if frame_type == ndi.FRAME_TYPE_NONE:
                        time.sleep(0.005)  # 5ms 대기
                else:
                    time.sleep(0.1)  # 연결 대기 중
                    
            except Exception as e:
                logger.error(f"NDI 워커 스레드 오류: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(1)
                
    def stop(self):
        """스레드 중지"""
        self.running = False
        if self.receiver:
            try:
                ndi.recv_destroy(self.receiver)
            except:
                pass
            self.receiver = None
        self.quit()
        self.wait(5000)

class NDIManager(QObject):
    """NDI 관리자 - 성능 최적화 버전"""
    
    # 시그널 정의
    frame_ready = pyqtSignal(object)  # 프레임 데이터 전달
    sources_updated = pyqtSignal(list)
    connection_status_changed = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.worker_thread = None
        self.sources = []
        self.is_initialized = False
        
        # GUI 업데이트 타이머
        self.gui_update_timer = QTimer()
        self.gui_update_timer.timeout.connect(self._process_frame_buffer)
        self.gui_update_timer.setInterval(int(1000 / GUI_UPDATE_FPS))  # 15fps
        
        # 소스 검색 타이머
        self.source_search_timer = QTimer()
        self.source_search_timer.timeout.connect(self._update_sources)
        self.source_search_timer.setInterval(5000)  # 5초마다
        
        # NDI 초기화 (시뮬레이터 모드 포함)
        self._initialize_ndi()
        
    def _initialize_ndi(self):
        """NDI 라이브러리 초기화"""
        if not NDI_AVAILABLE:
            logger.error("NDI 라이브러리를 사용할 수 없습니다")
            self.connection_status_changed.emit("NDI 사용 불가", "red")
            return False
            
        try:
            # 이미 초기화되어 있는지 확인
            if hasattr(ndi, '_initialized') and ndi._initialized:
                self.is_initialized = True
                return True
                
            # NDI 초기화 (시뮬레이터는 초기화 불필요)
            if hasattr(ndi, 'initialize'):
                if not ndi.initialize():
                    raise RuntimeError("NDI 초기화 실패")
                ndi._initialized = True
            
            self.is_initialized = True
            logger.info("NDI 라이브러리 초기화 성공")
            return True
            
        except Exception as e:
            logger.error(f"NDI 초기화 오류: {e}")
            self.is_initialized = False
            return False
    
    def start_source_discovery(self):
        """NDI 소스 검색 시작"""
        if not self.is_initialized:
            if not self._initialize_ndi():
                return False
        
        try:
            # Finder 생성
            if not self.finder:
                self.finder = ndi.find_create_v2()
                if not self.finder:
                    raise RuntimeError("NDI Finder 생성 실패")
            
            # 워커 스레드 시작
            if not self.worker_thread:
                self.worker_thread = NDIWorkerThread()
                self.worker_thread.finder = self.finder
                self.worker_thread.frame_available.connect(self._on_frame_available)
                self.worker_thread.sources_updated.connect(self.sources_updated.emit)
                self.worker_thread.status_changed.connect(self._on_status_changed)
                self.worker_thread.error_occurred.connect(self._on_error)
                self.worker_thread.start()
            
            # 타이머 시작
            self.source_search_timer.start()
            self._update_sources()  # 즉시 검색
            
            return True
            
        except Exception as e:
            logger.error(f"소스 검색 시작 오류: {e}")
            return False
    
    def _update_sources(self):
        """NDI 소스 목록 업데이트"""
        if not self.finder:
            return
            
        try:
            # 소스 검색
            if not ndi.find_wait_for_sources(self.finder, 100):  # 100ms timeout
                return
                
            sources = ndi.find_get_current_sources(self.finder)
            
            # 소스 이름 추출
            source_names = []
            for source in sources:
                name = safe_decode(source.ndi_name)
                if name:
                    source_names.append(name)
            
            # 변경사항이 있을 때만 업데이트
            if source_names != self.sources:
                self.sources = source_names
                self.sources_updated.emit(source_names)
                logger.info(f"NDI 소스 업데이트: {len(source_names)}개")
                
        except Exception as e:
            logger.error(f"소스 업데이트 오류: {e}")
    
    def start_preview(self, source_name):
        """프리뷰 시작 - 최적화된 버전"""
        if not self.worker_thread:
            return False
            
        try:
            # 기존 receiver 정리
            if self.worker_thread.receiver:
                ndi.recv_destroy(self.worker_thread.receiver)
                self.worker_thread.receiver = None
            
            # 소스 찾기
            sources = ndi.find_get_current_sources(self.finder)
            selected_source = None
            
            for source in sources:
                if safe_decode(source.ndi_name) == source_name:
                    selected_source = source
                    break
            
            if not selected_source:
                logger.error(f"소스를 찾을 수 없음: {source_name}")
                return False
            
            # Receiver 생성 - 최적화된 설정
            recv_create = ndi.RecvCreateV3_t()
            recv_create.source_to_connect_to = selected_source
            recv_create.color_format = ndi.RECV_COLOR_FORMAT_UYVY_RGBA  # 최적 포맷
            recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
            recv_create.allow_video_fields = False  # 필드 비활성화로 성능 향상
            
            receiver = ndi.recv_create_v3(recv_create)
            if not receiver:
                logger.error("NDI Receiver 생성 실패")
                return False
            
            # 워커 스레드에 receiver 설정
            self.worker_thread.receiver = receiver
            self.worker_thread.current_source = source_name
            
            # GUI 업데이트 타이머 시작
            self.gui_update_timer.start()
            
            self.connection_status_changed.emit(f"{source_name} 연결됨", "green")
            logger.info(f"프리뷰 시작: {source_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"프리뷰 시작 오류: {e}")
            return False
    
    def stop_preview(self):
        """프리뷰 중지"""
        # GUI 업데이트 타이머 중지
        self.gui_update_timer.stop()
        
        if self.worker_thread:
            self.worker_thread.current_source = None
            if self.worker_thread.receiver:
                try:
                    ndi.recv_destroy(self.worker_thread.receiver)
                except:
                    pass
                self.worker_thread.receiver = None
        
        self.connection_status_changed.emit("연결 해제됨", "gray")
        logger.info("프리뷰 중지")
    
    def _on_frame_available(self):
        """프레임 사용 가능 알림 처리"""
        # 타이머가 이미 처리하므로 여기서는 아무것도 하지 않음
        pass
    
    def _process_frame_buffer(self):
        """프레임 버퍼 처리 - GUI 업데이트"""
        if not self.worker_thread:
            return
            
        frame_data = self.worker_thread.get_latest_frame()
        if frame_data:
            # 프레임 데이터를 복사하여 전달 (thread-safe)
            try:
                if NUMPY_AVAILABLE:
                    # 최소한의 복사만 수행
                    frame_copy = np.copy(frame_data.data)
                    self.frame_ready.emit(frame_copy)
                else:
                    self.frame_ready.emit(frame_data.data)
            except Exception as e:
                logger.error(f"프레임 전달 오류: {e}")
    
    def _on_status_changed(self, status):
        """상태 변경 처리"""
        logger.info(f"NDI 상태: {status}")
    
    def _on_error(self, error):
        """오류 처리"""
        logger.error(f"NDI 오류: {error}")
        self.connection_status_changed.emit(f"오류: {error}", "red")
    
    def cleanup(self):
        """정리 작업"""
        self.stop_preview()
        
        # 타이머 중지
        self.source_search_timer.stop()
        self.gui_update_timer.stop()
        
        # 워커 스레드 중지
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread = None
        
        # Finder 정리
        if self.finder:
            try:
                ndi.find_destroy(self.finder)
            except:
                pass
            self.finder = None
        
        logger.info("NDI 관리자 정리 완료")