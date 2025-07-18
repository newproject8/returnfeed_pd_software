# pd_app/core/ndi_simulator.py
"""
NDI 시뮬레이터 - NDI SDK가 없을 때 사용
"""

import logging
import time
import random
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class SimulatedNDISource:
    """시뮬레이션된 NDI 소스"""
    ndi_name: bytes
    ip_address: str = "127.0.0.1"
    
    def __init__(self, name: str, ip_address: str = "127.0.0.1"):
        self.ndi_name = name.encode('utf-8') if isinstance(name, str) else name
        self.ip_address = ip_address
    
    def __str__(self):
        return self.ndi_name.decode('utf-8') if isinstance(self.ndi_name, bytes) else str(self.ndi_name)

class NDISimulator:
    """NDI 기능 시뮬레이터"""
    
    def __init__(self):
        self.initialized = False
        self.sources = []
        self.finder = None
        self.receiver = None
        logger.info("NDI 시뮬레이터 모드 활성화")
        
    def initialize(self):
        """NDI 초기화 시뮬레이션"""
        self.initialized = True
        logger.info("NDI 시뮬레이터 초기화 완료")
        return True
        
    def destroy(self):
        """NDI 종료 시뮬레이션"""
        self.initialized = False
        logger.info("NDI 시뮬레이터 종료")
        
    def find_create_v2(self):
        """Finder 생성 시뮬레이션"""
        self.finder = "SimulatedFinder"
        # 테스트용 가상 소스 추가
        self.sources = [
            SimulatedNDISource("테스트 카메라 1 (시뮬레이션)"),
            SimulatedNDISource("테스트 카메라 2 (시뮬레이션)"),
            SimulatedNDISource("화면 캡처 (시뮬레이션)")
        ]
        return self.finder
        
    def find_wait_for_sources(self, finder, timeout):
        """소스 대기 시뮬레이션"""
        time.sleep(min(timeout / 1000, 0.1))  # 짧은 대기
        return True
        
    def find_get_current_sources(self, finder):
        """현재 소스 목록 반환"""
        # 가끔 소스 목록 변경 시뮬레이션
        if random.random() > 0.9:
            new_source = SimulatedNDISource(f"새 소스 {random.randint(1, 100)} (시뮬레이션)")
            self.sources.append(new_source)
            logger.info(f"시뮬레이션: 새 NDI 소스 발견 - {new_source.ndi_name}")
        
        # list 형태로 반환 (ndi_manager.py와 호환성을 위해)
        return self.sources if self.sources else []
        
    def find_destroy(self, finder):
        """Finder 제거 시뮬레이션"""
        self.finder = None
        logger.info("NDI Finder 시뮬레이션 종료")
        
    def recv_create_v3(self, recv_create):
        """Receiver 생성 시뮬레이션"""
        self.receiver = "SimulatedReceiver"
        return self.receiver
        
    def recv_connect(self, receiver, source):
        """소스 연결 시뮬레이션"""
        logger.info(f"시뮬레이션: {source.ndi_name}에 연결")
        return True
        
    def recv_capture_v2(self, receiver, timeout):
        """프레임 캡처 시뮬레이션"""
        # 가상 프레임 데이터
        class VideoFrame:
            def __init__(self):
                self.type = 1  # FRAME_TYPE_VIDEO
                self.width = 1920
                self.height = 1080
                self.data = self._generate_test_pattern()
                
            def _generate_test_pattern(self):
                """테스트 패턴 생성"""
                import numpy as np
                # 간단한 그라데이션 패턴
                pattern = np.zeros((1080, 1920, 4), dtype=np.uint8)
                for y in range(1080):
                    pattern[y, :, 0] = int(255 * y / 1080)  # R
                    pattern[y, :, 1] = 128  # G
                    pattern[y, :, 2] = int(255 * (1 - y / 1080))  # B
                    pattern[y, :, 3] = 255  # A
                return pattern
                
        time.sleep(0.033)  # 30fps 시뮬레이션
        return VideoFrame()
        
    def recv_free_video_v2(self, receiver, video_frame):
        """비디오 프레임 해제 시뮬레이션"""
        pass
        
    def recv_destroy(self, receiver):
        """Receiver 제거 시뮬레이션"""
        self.receiver = None
        logger.info("NDI Receiver 시뮬레이션 종료")

# 상수 정의
FRAME_TYPE_VIDEO = 1
RECV_COLOR_FORMAT_RGBX_RGBA = 3

class RecvCreateV3:
    """Receiver 생성 설정"""
    def __init__(self):
        self.color_format = RECV_COLOR_FORMAT_RGBX_RGBA

# 글로벌 시뮬레이터 인스턴스
_simulator = NDISimulator()

# NDIlib 호환 API
initialize = _simulator.initialize
destroy = _simulator.destroy
find_create_v2 = _simulator.find_create_v2
find_wait_for_sources = _simulator.find_wait_for_sources
find_get_current_sources = _simulator.find_get_current_sources
find_destroy = _simulator.find_destroy
recv_create_v3 = _simulator.recv_create_v3
recv_connect = _simulator.recv_connect
recv_capture_v2 = _simulator.recv_capture_v2
recv_free_video_v2 = _simulator.recv_free_video_v2
recv_destroy = _simulator.recv_destroy