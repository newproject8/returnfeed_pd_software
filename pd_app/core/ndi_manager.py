# pd_app/core/ndi_manager.py
"""
NDI Manager - NDI 소스 검색 및 비디오 수신 관리
모든 decode 오류 수정 및 안정성 개선 버전
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
    from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
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
        def quit(self):
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
    """NDI 작업을 처리하는 워커 스레드"""
    # numpy가 없어도 작동하도록 object 타입 사용
    frame_received = pyqtSignal(object)
    sources_updated = pyqtSignal(list)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.running = False
        self.current_source = None
        self._frame_timeout_timer = None
        
    def run(self):
        """스레드 실행"""
        self.running = True
        self.status_changed.emit("NDI 워커 스레드 시작")
        logger.info("NDI 워커: NDI 워커 스레드 시작")
        
        # 스레드 우선순위 설정 (Windows)
        try:
            import ctypes
            import ctypes.wintypes
            
            # 높은 우선순위 설정
            handle = ctypes.windll.kernel32.GetCurrentThread()
            ctypes.windll.kernel32.SetThreadPriority(handle, 1)  # THREAD_PRIORITY_ABOVE_NORMAL
            logger.info("NDI 워커 스레드 우선순위 설정 완료")
        except Exception as e:
            logger.warning(f"스레드 우선순위 설정 실패: {e}")
        
        frame_timeout_count = 0
        last_frame_time = time.time()
        
        while self.running:
            try:
                if self.receiver and self.current_source:
                    # 타임아웃 방지를 위한 non-blocking 수신
                    # recv_capture_v2는 4개의 값을 반환: (frame_type, video_frame, audio_frame, metadata_frame)
                    # 적절한 타임아웃으로 안정성 확보 (100ms)
                    try:
                        result = ndi.recv_capture_v2(self.receiver, 16)  # 16ms timeout (60fps)
                        
                        # 반환값 타입 확인
                        if isinstance(result, tuple) and len(result) == 4:
                            frame_type, v_frame, a_frame, m_frame = result
                        else:
                            # 단일 객체가 반환된 경우 (구버전 NDI SDK?)
                            logger.warning(f"예상치 못한 recv_capture_v2 반환 타입: {type(result)}")
                            if hasattr(result, 'type'):
                                # 구버전 스타일 처리
                                frame_type = result.type
                                v_frame = result if frame_type == ndi.FRAME_TYPE_VIDEO else None
                                a_frame = result if frame_type == ndi.FRAME_TYPE_AUDIO else None
                                m_frame = result if frame_type == ndi.FRAME_TYPE_METADATA else None
                            else:
                                continue
                    except Exception as recv_error:
                        logger.error(f"recv_capture_v2 호출 오류: {recv_error}")
                        continue
                    
                    if frame_type == ndi.FRAME_TYPE_VIDEO and v_frame:
                        last_frame_time = time.time()
                        frame_timeout_count = 0
                        
                        # 프레임 데이터가 유효한지 확인
                        if v_frame.data is not None:
                            try:
                                # 프레임 크기 확인
                                if hasattr(v_frame, 'data') and hasattr(v_frame.data, 'size'):
                                    if v_frame.data.size == 0:
                                        logger.warning("빈 프레임 데이터")
                                        continue
                                
                                if NUMPY_AVAILABLE:
                                    # 안전한 복사본 생성
                                    try:
                                        frame_data = np.copy(v_frame.data)
                                        self.frame_received.emit(frame_data)
                                    except Exception as copy_error:
                                        logger.error(f"프레임 복사 오류: {copy_error}")
                                else:
                                    # NumPy 없이도 작동
                                    self.frame_received.emit(v_frame.data)
                                    
                            except Exception as e:
                                logger.error(f"프레임 데이터 처리 오류: {e}")
                                # 오류가 발생해도 계속 진행
                        
                        # 비디오 프레임 메모리 해제
                        try:
                            ndi.recv_free_video_v2(self.receiver, v_frame)
                        except:
                            pass
                    
                    # 오디오 프레임이 있으면 해제
                    if frame_type == ndi.FRAME_TYPE_AUDIO and a_frame:
                        try:
                            ndi.recv_free_audio_v2(self.receiver, a_frame)
                        except Exception as e:
                            logger.debug(f"오디오 프레임 해제 오류: {e}")
                    
                    # 메타데이터가 있으면 해제
                    if frame_type == ndi.FRAME_TYPE_METADATA and m_frame:
                        try:
                            ndi.recv_free_metadata(self.receiver, m_frame)
                        except Exception as e:
                            logger.debug(f"메타데이터 프레임 해제 오류: {e}")
                    
                    # 에러 프레임 처리
                    if frame_type == ndi.FRAME_TYPE_ERROR:
                        logger.error("NDI 수신 에러 프레임")
                        self.error_occurred.emit("NDI 수신 에러")
                    
                    # 프레임 타임아웃 체크 - 수신기가 연결된 경우에만
                    if self.receiver and self.current_source:
                        current_time = time.time()
                        if current_time - last_frame_time > 15.0:  # 15초로 증가
                            frame_timeout_count += 1
                            logger.warning(f"NDI 프레임 타임아웃 카운트: {frame_timeout_count}")
                            if frame_timeout_count > 3:  # 3번까지 허용
                                logger.error(f"NDI 프레임 수신 타임아웃 초과: {self.current_source}")
                                self.error_occurred.emit("프레임 수신 타임아웃")
                                # 재연결 시도는 하지 않음 (안정성)
                                frame_timeout_count = 0
                                last_frame_time = current_time
                    
                    # CPU 사용률 감소를 위한 짧은 대기
                    # 프레임이 없을 때만 sleep - 성능 최적화
                    if frame_type == ndi.FRAME_TYPE_NONE:
                        time.sleep(0.001)  # 1ms - 더 빠른 응답
                else:
                    time.sleep(0.05)  # 50ms 대기로 단축
                    
            except Exception as e:
                logger.error(f"NDI 워커 스레드 오류: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(1)  # 오류 후 1초 대기
                
    def reconnect_source(self):
        """소스 재연결"""
        if self.receiver:
            try:
                ndi.recv_destroy(self.receiver)
            except:
                pass
            self.receiver = None
        
        # 재연결은 메인 스레드에서 처리하도록 시그널 발생
        self.status_changed.emit("재연결 필요")
            
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
        self.wait(5000)  # 최대 5초 대기

class NDIManager(QObject):
    """NDI 관리자 - 안정성 개선 버전"""
    
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
        self.current_source_name = None
        
    def initialize(self):
        """NDI 라이브러리 초기화"""
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
            self.worker_thread.error_occurred.connect(self._on_worker_error)
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
                            # 먼저 list 타입인지 확인
                            if isinstance(sources, list):
                                # Python list 형태의 반환값
                                for source in sources:
                                    if hasattr(source, 'ndi_name'):
                                        source_name = safe_decode(source.ndi_name)
                                    else:
                                        source_name = str(source)
                                    source_list.append(source_name)
                            elif hasattr(sources, 'no_sources'):
                                # C-struct 형태의 반환값
                                for i in range(sources.no_sources):
                                    ndi_name = sources.sources[i].ndi_name
                                    source_name = safe_decode(ndi_name)
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
                
            logger.info(f"NDI 프리뷰 시작 시도: {source_name}")
            
            # 기존 리시버 정리
            if self.worker_thread and self.worker_thread.receiver:
                try:
                    ndi.recv_destroy(self.worker_thread.receiver)
                except:
                    pass
                self.worker_thread.receiver = None
                
            # 소스 찾기
            sources = ndi.find_get_current_sources(self.finder)
            target_source = None
            
            # list와 C-struct 형태 모두 처리
            if hasattr(sources, 'no_sources'):
                # C-struct 형태
                for i in range(sources.no_sources):
                    ndi_name = sources.sources[i].ndi_name
                    name_str = safe_decode(ndi_name)
                    
                    if name_str == source_name:
                        target_source = sources.sources[i]
                        break
            elif isinstance(sources, list):
                # Python list 형태
                for source in sources:
                    if hasattr(source, 'ndi_name'):
                        ndi_name = source.ndi_name
                        name_str = safe_decode(ndi_name)
                        
                        if name_str == source_name:
                            target_source = source
                            break
                    elif str(source) == source_name:
                        target_source = source
                        break
                    
            if not target_source:
                raise ValueError(f"NDI 소스를 찾을 수 없습니다: {source_name}")
                
            # 리시버 생성 - 안정성 우선 설정
            recv_create = ndi.RecvCreateV3()
            recv_create.color_format = ndi.RECV_COLOR_FORMAT_RGBX_RGBA  # 호환성이 좋은 포맷
            recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST  # 최고 대역폭
            recv_create.allow_video_fields = True  # 모든 필드 허용
            
            receiver = ndi.recv_create_v3(recv_create)
            if not receiver:
                raise RuntimeError("NDI 리시버 생성 실패")
                
            # 소스 연결
            ndi.recv_connect(receiver, target_source)
            
            # 워커 스레드에 리시버 설정
            self.worker_thread.receiver = receiver
            self.worker_thread.current_source = source_name
            self.current_source_name = source_name
            
            self.connection_status_changed.emit(f"연결됨: {source_name}", "green")
            logger.info(f"NDI 프리뷰 시작 성공: {source_name}")
            
        except Exception as e:
            error_msg = f"NDI 프리뷰 시작 실패: {e}"
            logger.error(error_msg, exc_info=True)
            self.connection_status_changed.emit(error_msg, "red")
            raise
            
    def stop_preview(self):
        """프리뷰 중지"""
        try:
            if self.worker_thread:
                self.worker_thread.current_source = None
                if self.worker_thread.receiver:
                    try:
                        ndi.recv_destroy(self.worker_thread.receiver)
                    except:
                        pass
                    self.worker_thread.receiver = None
                    
            self.current_source_name = None
            self.connection_status_changed.emit("연결 해제됨", "gray")
            logger.info("NDI 프리뷰 중지")
            
        except Exception as e:
            logger.error(f"프리뷰 중지 오류: {e}")
            
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
                try:
                    ndi.find_destroy(self.finder)
                except:
                    pass
                self.finder = None
                
            # NDI 라이브러리 정리
            if NDI_AVAILABLE:
                try:
                    ndi.destroy()
                except:
                    pass
                    
            logger.info("NDI 리소스 정리 완료")
            
        except Exception as e:
            logger.error(f"NDI 정리 오류: {e}")
            
    def _on_worker_status(self, status):
        """워커 상태 변경 처리"""
        logger.info(f"NDI 워커 상태: {status}")
        if status == "재연결 필요" and self.current_source_name:
            # 자동 재연결 시도
            try:
                self.start_preview(self.current_source_name)
            except Exception as e:
                logger.error(f"자동 재연결 실패: {e}")
                
    def _on_worker_error(self, error):
        """워커 오류 처리"""
        logger.error(f"NDI 워커 오류: {error}")
        self.connection_status_changed.emit(f"오류: {error}", "red")