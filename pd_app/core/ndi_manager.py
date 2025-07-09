# pd_app/core/ndi_manager.py
"""
NDI Manager - NDI 소스 검색 및 비디오 수신 관리
기존 최적화된 NDIlib 구현 유지
"""

import sys
import time
import logging
import threading

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    
try:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal
except ImportError:
    # Qt가 없는 환경에서도 기본 기능 사용 가능
    class QObject:
        pass
    class QThread:
        def __init__(self):
            pass
        def start(self):
            pass
        def wait(self):
            pass
        def run(self):
            pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    logging.warning("NDIlib not available - using simulator")
    try:
        from . import ndi_simulator as ndi
        NDI_AVAILABLE = True  # 시뮬레이터 사용 가능
        logging.info("NDI 시뮬레이터 모드 활성화")
    except ImportError:
        logging.error("NDI 시뮬레이터도 로드 실패")

logger = logging.getLogger(__name__)

class NDIWorkerThread(QThread):
    """NDI 작업을 처리하는 워커 스레드"""
    # numpy가 없어도 작동하도록 object 타입 사용
    frame_received = pyqtSignal(object)
    sources_updated = pyqtSignal(list)
    status_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.running = False
        self.current_source = None
        
    def run(self):
        """스레드 실행"""
        self.running = True
        self.status_changed.emit("NDI 워커 스레드 시작")
        
        while self.running:
            if self.receiver and self.current_source:
                self.receive_frames()
            else:
                time.sleep(0.1)
                
    def receive_frames(self):
        """NDI 프레임 수신"""
        if not NDI_AVAILABLE:
            return
            
        try:
            video_frame = ndi.recv_capture_v2(self.receiver, 16)
            if video_frame.type == ndi.FRAME_TYPE_VIDEO:
                # NumPy 배열로 변환
                if NUMPY_AVAILABLE:
                    frame_data = np.copy(video_frame.data)
                else:
                    frame_data = video_frame.data
                self.frame_received.emit(frame_data)
                ndi.recv_free_video_v2(self.receiver, video_frame)
        except Exception as e:
            logger.error(f"프레임 수신 오류: {e}")
            
    def stop(self):
        """스레드 중지"""
        self.running = False
        if self.receiver:
            ndi.recv_destroy(self.receiver)
            self.receiver = None
        self.wait()

class NDIManager(QObject):
    """NDI 관리자 - 기존 최적화된 구현 통합"""
    
    # 시그널 정의
    frame_received = pyqtSignal(object)  # numpy 없어도 작동
    sources_updated = pyqtSignal(list)
    connection_status_changed = pyqtSignal(str, str)  # status, color
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.worker_thread = None
        self.sources = []
        self.is_initialized = False
        
    def initialize(self):
        """NDI 라이브러리 초기화 (기존 최적화 유지)"""
        if not NDI_AVAILABLE:
            logger.warning("NDIlib not available - running in simulation mode")
            self.connection_status_changed.emit("NDI 없음 (시뮬레이션 모드)", "orange")
            self.is_initialized = False
            return
            
        try:
            if not ndi.initialize():
                raise RuntimeError("Failed to initialize NDIlib")
                
            # NDI Finder 생성
            self.finder = ndi.find_create_v2()
            if not self.finder:
                raise RuntimeError("Failed to create NDI finder")
                
            self.is_initialized = True
            self.connection_status_changed.emit("NDI 초기화 성공", "green")
            logger.info("NDI 라이브러리 초기화 성공")
            
            # 워커 스레드 시작
            self.start_worker_thread()
            
            # 소스 검색 시작
            self.start_source_discovery()
            
        except Exception as e:
            logger.error(f"NDI 초기화 실패: {e}")
            self.connection_status_changed.emit(f"NDI 초기화 실패: {e}", "red")
            raise
            
    def start_worker_thread(self):
        """워커 스레드 시작"""
        if not self.worker_thread:
            self.worker_thread = NDIWorkerThread()
            self.worker_thread.frame_received.connect(self.frame_received.emit)
            self.worker_thread.sources_updated.connect(self.sources_updated.emit)
            self.worker_thread.status_changed.connect(self._on_worker_status)
            self.worker_thread.finder = self.finder
            self.worker_thread.start()
            
    def start_source_discovery(self):
        """NDI 소스 검색 시작"""
        def discover_sources():
            while self.is_initialized:
                try:
                    # NDI 소스 검색
                    if not ndi.find_wait_for_sources(self.finder, 1000):
                        continue
                        
                    sources = ndi.find_get_current_sources(self.finder)
                    if sources:
                        source_list = []
                        # NDIlib C-struct 반환값과 list 반환값 모두 처리
                        try:
                            if hasattr(sources, 'no_sources'):
                                # C-struct 형태의 반환값
                                for i in range(sources.no_sources):
                                    source_name = sources.sources[i].ndi_name.decode('utf-8')
                                    source_list.append(source_name)
                            elif isinstance(sources, list):
                                # Python list 형태의 반환값
                                for source in sources:
                                    if hasattr(source, 'ndi_name'):
                                        source_name = source.ndi_name.decode('utf-8')
                                    else:
                                        source_name = str(source)
                                    source_list.append(source_name)
                            else:
                                logger.warning(f"알 수 없는 sources 타입: {type(sources)}")
                        except AttributeError as ae:
                            logger.error(f"NDI sources 속성 오류: {ae}")
                        except Exception as e:
                            logger.error(f"NDI sources 처리 오류: {e}")
                        
                        if source_list != self.sources:
                            self.sources = source_list
                            self.sources_updated.emit(self.sources)
                            logger.info(f"NDI 소스 발견: {self.sources}")
                            
                except Exception as e:
                    logger.error(f"소스 검색 오류: {e}")
                    
                time.sleep(5)  # 5초마다 재검색
                
        # 검색 스레드 시작
        discovery_thread = threading.Thread(target=discover_sources, daemon=True)
        discovery_thread.start()
        
    def start_preview(self, source_name):
        """NDI 소스 프리뷰 시작"""
        try:
            if not self.is_initialized:
                raise RuntimeError("NDI가 초기화되지 않았습니다")
                
            # 기존 리시버 정리
            if self.worker_thread and self.worker_thread.receiver:
                ndi.recv_destroy(self.worker_thread.receiver)
                self.worker_thread.receiver = None
                
            # 소스 찾기
            sources = ndi.find_get_current_sources(self.finder)
            target_source = None
            
            for i in range(sources.no_sources):
                if sources.sources[i].ndi_name.decode('utf-8') == source_name:
                    target_source = sources.sources[i]
                    break
                    
            if not target_source:
                raise ValueError(f"NDI 소스를 찾을 수 없습니다: {source_name}")
                
            # 리시버 생성
            recv_create = ndi.RecvCreateV3()
            recv_create.color_format = ndi.RECV_COLOR_FORMAT_RGBX_RGBA
            
            receiver = ndi.recv_create_v3(recv_create)
            if not receiver:
                raise RuntimeError("NDI 리시버 생성 실패")
                
            # 소스 연결
            ndi.recv_connect(receiver, target_source)
            
            # 워커 스레드에 리시버 설정
            self.worker_thread.receiver = receiver
            self.worker_thread.current_source = source_name
            
            self.connection_status_changed.emit(f"연결됨: {source_name}", "green")
            logger.info(f"NDI 소스 연결 성공: {source_name}")
            
        except Exception as e:
            logger.error(f"NDI 프리뷰 시작 실패: {e}")
            self.connection_status_changed.emit(f"연결 실패: {e}", "red")
            
    def stop_preview(self):
        """NDI 소스 프리뷰 중지"""
        try:
            if self.worker_thread:
                self.worker_thread.current_source = None
                if self.worker_thread.receiver:
                    ndi.recv_destroy(self.worker_thread.receiver)
                    self.worker_thread.receiver = None
                    
            self.connection_status_changed.emit("연결 해제됨", "orange")
            logger.info("NDI 프리뷰 중지")
            
        except Exception as e:
            logger.error(f"NDI 프리뷰 중지 오류: {e}")
            
    def cleanup(self):
        """리소스 정리"""
        try:
            self.is_initialized = False
            
            # 워커 스레드 중지
            if self.worker_thread:
                self.worker_thread.stop()
                self.worker_thread = None
                
            # Finder 정리
            if self.finder:
                ndi.find_destroy(self.finder)
                self.finder = None
                
            # NDI 라이브러리 종료
            ndi.destroy()
            
            logger.info("NDI 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"NDI 정리 오류: {e}")
            
    def _on_worker_status(self, status):
        """워커 스레드 상태 변경 처리"""
        logger.info(f"NDI 워커: {status}")