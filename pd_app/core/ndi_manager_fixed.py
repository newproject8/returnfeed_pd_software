"""
NDI Manager with connection stability fixes
연결 안정성 문제 해결 버전
"""

import time
import threading
import logging
from typing import Optional, List
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal, QThread

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    ndi = None
    NDI_AVAILABLE = False
    
logger = logging.getLogger(__name__)


class NDIWorkerThread(QThread):
    """NDI 워커 스레드 - 안정성 개선"""
    
    # 시그널 정의
    frame_received = pyqtSignal(object)
    sources_updated = pyqtSignal(list)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.receiver = None
        self.running = False
        self.source_name = None
        self.last_frame_time = 0
        self.connection_timeout = 10.0  # 10초 타임아웃
        self.frame_timeout = 5.0  # 프레임 없음 타임아웃 5초로 증가
        
    def connect_to_source(self, source_name: str):
        """NDI 소스에 연결"""
        self.source_name = source_name
        self.last_frame_time = time.time()  # 연결 시작 시간 기록
        
    def run(self):
        """워커 스레드 메인 루프"""
        self.running = True
        logger.info("NDI 워커: NDI 워커 스레드 시작")
        
        while self.running:
            try:
                if self.source_name and not self.receiver:
                    # 소스 연결
                    if self._connect_to_source():
                        self.status_changed.emit("연결됨")
                        self.last_frame_time = time.time()
                    else:
                        time.sleep(1)
                        continue
                        
                elif self.receiver:
                    # 프레임 캡처
                    frame_received = self._capture_frame()
                    
                    # 프레임 타임아웃 체크
                    if not frame_received:
                        if time.time() - self.last_frame_time > self.frame_timeout:
                            logger.warning("프레임 수신 타임아웃 - 재연결 시도")
                            self._disconnect()
                            self.status_changed.emit("재연결 중...")
                            time.sleep(1)
                            continue
                    else:
                        self.last_frame_time = time.time()
                        
                else:
                    # 대기
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"NDI 워커 오류: {e}")
                self.error_occurred.emit(str(e))
                self._disconnect()
                time.sleep(1)
                
    def _connect_to_source(self) -> bool:
        """소스에 실제 연결"""
        try:
            if not self.finder:
                return False
                
            # 소스 찾기 (최대 5초 대기)
            sources = []
            start_time = time.time()
            
            while time.time() - start_time < 5.0:
                if ndi.find_wait_for_sources(self.finder, 100):
                    sources = ndi.find_get_current_sources(self.finder)
                    if sources:
                        break
                        
            if not sources:
                logger.warning("NDI 소스를 찾을 수 없음")
                return False
                
            # 요청된 소스 찾기
            target_source = None
            for source in sources:
                if source.ndi_name == self.source_name:
                    target_source = source
                    break
                    
            if not target_source:
                logger.warning(f"소스를 찾을 수 없음: {self.source_name}")
                return False
                
            # Receiver 생성
            recv_create = ndi.RecvCreateV3()
            recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
            recv_create.allow_video_fields = False
            
            self.receiver = ndi.recv_create_v3(recv_create)
            if not self.receiver:
                logger.error("NDI Receiver 생성 실패")
                return False
                
            # 연결
            ndi.recv_connect(self.receiver, target_source)
            logger.info(f"NDI 소스 연결 성공: {self.source_name}")
            
            # 연결 후 약간의 대기 시간
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"소스 연결 실패: {e}")
            return False
            
    def _capture_frame(self) -> bool:
        """프레임 캡처"""
        if not self.receiver:
            return False
            
        try:
            # 프레임 캡처 (100ms 타임아웃)
            frame_type = ndi.recv_capture_v2(self.receiver, 100)
            
            if frame_type == ndi.FRAME_TYPE_VIDEO:
                # 비디오 프레임
                v_frame = ndi.recv_get_video_data(self.receiver)
                if v_frame and v_frame.data is not None:
                    # 프레임 데이터 복사
                    frame_data = np.copy(v_frame.data)
                    
                    # 시그널 발생
                    self.frame_received.emit({
                        'data': frame_data,
                        'width': v_frame.xres,
                        'height': v_frame.yres,
                        'timestamp': time.time()
                    })
                    
                    # NDI 프레임 해제
                    ndi.recv_free_video_v2(self.receiver, v_frame)
                    
                    return True
                    
            elif frame_type == ndi.FRAME_TYPE_ERROR:
                logger.error("NDI 수신 오류")
                return False
                
            # FRAME_TYPE_NONE은 정상 - 프레임이 아직 없음
            return True
            
        except Exception as e:
            logger.error(f"프레임 캡처 오류: {e}")
            return False
            
    def _disconnect(self):
        """연결 해제"""
        if self.receiver:
            try:
                ndi.recv_destroy(self.receiver)
            except:
                pass
            self.receiver = None
            
    def stop(self):
        """스레드 중지"""
        self.running = False
        self._disconnect()
        self.quit()
        self.wait(2000)


class NDIManager(QObject):
    """NDI 관리자 - 연결 안정성 개선"""
    
    # 시그널
    frame_received = pyqtSignal(object)
    sources_updated = pyqtSignal(list)
    connection_status_changed = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.finder = None
        self.worker_thread = None
        self.sources = []
        self.is_initialized = False
        self.current_source_name = None
        self.discovery_thread = None
        self.discovery_running = False
        
    def initialize(self):
        """NDI 초기화"""
        if not NDI_AVAILABLE:
            logger.warning("NDI 사용 불가 - 시뮬레이션 모드")
            self.connection_status_changed.emit("NDI 없음", "orange")
            return
            
        try:
            if not ndi.initialize():
                raise RuntimeError("NDI 초기화 실패")
                
            # Finder 생성
            self.finder = ndi.find_create_v2()
            if not self.finder:
                raise RuntimeError("NDI Finder 생성 실패")
                
            self.is_initialized = True
            self.connection_status_changed.emit("NDI 준비됨", "green")
            logger.info("NDI 초기화 성공")
            
            # 워커 스레드 시작
            self._start_worker_thread()
            
            # 소스 검색 시작
            self._start_source_discovery()
            
        except Exception as e:
            logger.error(f"NDI 초기화 실패: {e}")
            self.connection_status_changed.emit(f"초기화 실패", "red")
            
    def _start_worker_thread(self):
        """워커 스레드 시작"""
        if not self.worker_thread:
            self.worker_thread = NDIWorkerThread()
            self.worker_thread.frame_received.connect(self._on_frame_received)
            self.worker_thread.status_changed.connect(self._on_status_changed)
            self.worker_thread.error_occurred.connect(self._on_error)
            self.worker_thread.finder = self.finder
            self.worker_thread.start()
            
    def _start_source_discovery(self):
        """소스 검색 시작"""
        if not self.discovery_running:
            self.discovery_running = True
            self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
            self.discovery_thread.start()
            
    def _discovery_loop(self):
        """소스 검색 루프"""
        while self.discovery_running and self.is_initialized:
            try:
                if ndi.find_wait_for_sources(self.finder, 1000):
                    sources = ndi.find_get_current_sources(self.finder)
                    if sources:
                        source_names = [s.ndi_name for s in sources]
                        if source_names != self.sources:
                            self.sources = source_names
                            self.sources_updated.emit(self.sources)
                            logger.info(f"NDI 소스 발견: {self.sources}")
            except Exception as e:
                logger.error(f"소스 검색 오류: {e}")
                
            time.sleep(2)  # 2초마다 검색
            
    def connect_to_source(self, source_name: str):
        """소스에 연결"""
        if not self.worker_thread:
            logger.error("워커 스레드가 없음")
            return
            
        self.current_source_name = source_name
        self.worker_thread.connect_to_source(source_name)
        self.connection_status_changed.emit("연결 중...", "orange")
        logger.info(f"NDI 소스 연결 시도: {source_name}")
        
    def disconnect_source(self):
        """소스 연결 해제"""
        if self.worker_thread:
            self.worker_thread.source_name = None
            self.worker_thread._disconnect()
        self.current_source_name = None
        self.connection_status_changed.emit("연결 해제됨", "gray")
        
    def _on_frame_received(self, frame_data):
        """프레임 수신 처리"""
        self.frame_received.emit(frame_data)
        
    def _on_status_changed(self, status):
        """상태 변경 처리"""
        if status == "연결됨":
            self.connection_status_changed.emit(f"연결됨: {self.current_source_name}", "green")
        else:
            self.connection_status_changed.emit(status, "orange")
            
    def _on_error(self, error_msg):
        """에러 처리"""
        logger.error(f"NDI 에러: {error_msg}")
        # 에러 메시지 박스를 띄우지 않고 상태만 업데이트
        self.connection_status_changed.emit(f"오류: {error_msg[:30]}...", "red")
        
    def cleanup(self):
        """정리"""
        self.discovery_running = False
        
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread = None
            
        if self.finder:
            try:
                ndi.find_destroy(self.finder)
            except:
                pass
            self.finder = None
            
        if NDI_AVAILABLE and ndi:
            try:
                ndi.destroy()
            except:
                pass
                
        self.is_initialized = False