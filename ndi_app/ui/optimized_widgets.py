# -*- coding: utf-8 -*-
"""
최적화된 NDI 프리뷰 위젯
16:9 고정 비율과 59.94fps 정밀 타이밍을 지원합니다.
"""

import time
import numpy as np
import cv2
from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

try:
    import NDIlib as ndi
except ImportError:
    print("NDI 라이브러리를 찾을 수 없습니다.")
    ndi = None


class AspectRatioPreviewLabel(QLabel):
    """
    16:9 종횡비를 자동으로 유지하는 프리뷰 라벨
    
    NDI 프리뷰를 위해 특별히 최적화된 QLabel 서브클래스입니다.
    어떤 크기의 윈도우에서도 항상 16:9 비율을 유지하며,
    프레임을 중앙에 배치하고 부드러운 스케일링을 제공합니다.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 16:9 비율 설정 및 640x360 고정 해상도
        self.aspect_ratio = 16.0 / 9.0
        self.fixed_width = 640
        self.fixed_height = 360
        
        # 위젯 크기 고정 (640x360)
        self.setFixedSize(self.fixed_width, self.fixed_height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 정렬 및 스케일링 설정
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(False)  # 수동 스케일링 사용
        
        # 스타일 설정
        self.setStyleSheet("""
            QLabel {
                background-color: black;
                border: 1px solid #333333;
            }
        """)
        
    def setPixmap(self, pixmap):
        """
        640x360 고정 해상도로 픽스맵 설정 (픽셀 처리 최적화)
        
        Args:
            pixmap (QPixmap): 표시할 픽스맵
        """
        if pixmap.isNull():
            super().setPixmap(pixmap)
            return
            
        # 640x360 고정 해상도로 최적화된 스케일링
        scaled_pixmap = self._scale_to_fixed_resolution(pixmap)
        
        super().setPixmap(scaled_pixmap)
        
    def _scale_to_fixed_resolution(self, pixmap):
        """
        640x360 고정 해상도로 픽스맵 스케일링 (픽셀 처리 최적화)
        
        Args:
            pixmap (QPixmap): 원본 픽스맵
            
        Returns:
            QPixmap: 640x360으로 스케일링된 픽스맵
        """
        if pixmap.isNull():
            return pixmap
            
        # 640x360 고정 해상도로 직접 스케일링
        # 빠른 스케일링을 위해 FastTransformation 사용
        return pixmap.scaled(
            self.fixed_width, 
            self.fixed_height, 
            Qt.AspectRatioMode.IgnoreAspectRatio,  # 정확한 640x360 크기 유지
            Qt.TransformationMode.FastTransformation  # 성능 최적화
        )
        
    def resizeEvent(self, event):
        """
        크기 변경 이벤트 (640x360 고정이므로 크기 변경 없음)
        
        Args:
            event: 크기 변경 이벤트
        """
        super().resizeEvent(event)
        # 640x360 고정 크기이므로 추가 처리 불필요


class PreciseNDITimer:
    """
    NDI 소스 프레임레이트 동기화 타이밍 클래스
    
    NDI 소스의 실제 프레임레이트를 감지하고 정확히 동기화
    """
    
    def __init__(self):
        # 동적 프레임레이트 감지
        self.detected_fps = None
        self.target_frame_time = None
        
        # 프레임 타이밍 추적
        self.frame_timestamps = []
        self.last_frame_time = 0.0
        self.frame_count = 0
        
        # FPS 통계
        self.fps_calculation_start = 0.0
        self.actual_fps_history = []
        
        # 프레임레이트 감지를 위한 설정
        self.detection_frames = 30  # 30프레임으로 프레임레이트 감지
        self.fps_detected = False
        
    def detect_source_framerate(self):
        """
        NDI 소스의 실제 프레임레이트 감지
        
        Returns:
            bool: 프레임레이트 감지 완료 여부
        """
        current_time = time.time()
        self.frame_timestamps.append(current_time)
        
        # 충분한 프레임이 수집되면 프레임레이트 계산
        if len(self.frame_timestamps) >= self.detection_frames:
            # 최근 프레임들의 평균 간격 계산
            time_diffs = []
            for i in range(1, len(self.frame_timestamps)):
                time_diffs.append(self.frame_timestamps[i] - self.frame_timestamps[i-1])
            
            if time_diffs:
                avg_frame_time = sum(time_diffs) / len(time_diffs)
                self.detected_fps = 1.0 / avg_frame_time
                self.target_frame_time = avg_frame_time
                self.fps_detected = True
                
                print(f"[NDI Timer] 소스 프레임레이트 감지: {self.detected_fps:.2f} fps")
                
                # 오래된 타임스탬프 제거 (최근 30개만 유지)
                self.frame_timestamps = self.frame_timestamps[-self.detection_frames:]
                
                return True
        
        return False
    
    def get_next_frame_delay(self):
        """
        NDI 소스와 동기화된 정확한 대기 시간 계산
        
        Returns:
            float: 대기 시간 (초)
        """
        current_time = time.time()
        
        # 프레임레이트가 아직 감지되지 않았으면 감지 시도
        if not self.fps_detected:
            self.detect_source_framerate()
            self.last_frame_time = current_time
            return 0.0  # 감지 중에는 대기 없음
        
        if self.last_frame_time == 0.0:
            self.last_frame_time = current_time
            return 0.0
            
        # 감지된 프레임레이트에 따른 이상적인 다음 프레임 시간
        ideal_next_time = self.last_frame_time + self.target_frame_time
        
        # 실제 대기 시간 계산
        delay = max(0.0, ideal_next_time - current_time)
        
        # 다음 프레임을 위해 시간 업데이트
        self.last_frame_time = max(current_time, ideal_next_time)
        
        return delay
        
    def update_fps_statistics(self):
        """
        FPS 통계 업데이트 (감지된 프레임레이트 기준)
        """
        current_time = time.time()
        self.frame_count += 1
        
        # 프레임레이트가 감지된 후에만 통계 계산
        if not self.fps_detected:
            return
        
        # 30프레임마다 FPS 계산 (더 빠른 피드백)
        if self.frame_count % 30 == 0:
            if self.fps_calculation_start > 0:
                elapsed = current_time - self.fps_calculation_start
                actual_fps = 30.0 / elapsed
                self.actual_fps_history.append(actual_fps)
                
                # 최근 10개 측정값만 유지
                if len(self.actual_fps_history) > 10:
                    self.actual_fps_history.pop(0)
                    
                # 감지된 프레임레이트와 비교
                target_fps = self.detected_fps if self.detected_fps else 59.94
                print(f"실제 FPS: {actual_fps:.2f}, 목표 FPS: {target_fps:.2f}")
                
            self.fps_calculation_start = current_time
            
    def get_average_fps(self):
        """
        평균 FPS 계산
        
        Returns:
            float: 평균 FPS
        """
        if not self.actual_fps_history:
            return 0.0
        return sum(self.actual_fps_history) / len(self.actual_fps_history)


class NDIFrameCapture(QThread):
    """
    59.94fps NDI 프레임 캡처 스레드
    """
    
    # 시그널 정의
    frame_ready = pyqtSignal(QPixmap)
    fps_updated = pyqtSignal(float)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ndi_source):
        super().__init__()
        
        self.ndi_source = ndi_source
        self.ndi_recv = None
        self.running = False
        
        # 정밀 타이밍 시스템
        self.timer = PreciseNDITimer()
        
        # 프레임 처리 최적화
        self.frame_mutex = QMutex()
        
    def setup_receiver(self):
        """
        NDI 수신기 설정
        
        Returns:
            bool: 설정 성공 여부
        """
        try:
            if not ndi:
                raise Exception("NDI 라이브러리가 로드되지 않았습니다.")
                
            # NDI 수신기 설정
            recv_settings = ndi.RecvCreateV3()
            recv_settings.source_to_connect_to = self.ndi_source
            recv_settings.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_settings.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
            recv_settings.allow_video_fields = False
            
            # 수신기 생성
            self.ndi_recv = ndi.recv_create_v3(recv_settings)
            
            if not self.ndi_recv:
                raise Exception("NDI 수신기 생성 실패")
                
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"NDI 수신기 설정 실패: {str(e)}")
            return False
            
    def run(self):
        """
        메인 캡처 루프 (NDI 소스 동기화)
        """
        if not self.setup_receiver():
            return
            
        self.running = True
        
        try:
            while self.running:
                # NDI 프레임 캡처 (논블로킹)
                frame_captured = self._capture_and_process_frame()
                
                if frame_captured:
                    # 프레임이 캡처되었을 때만 타이밍 계산
                    self.timer.update_fps_statistics()
                    
                    # FPS 정보 전송 (30프레임마다)
                    if self.timer.frame_count % 30 == 0:
                        avg_fps = self.timer.get_average_fps()
                        self.fps_updated.emit(avg_fps)
                    
                    # 다음 프레임까지 정확한 대기
                    delay = self.timer.get_next_frame_delay()
                    if delay > 0:
                        time.sleep(delay)
                else:
                    # 프레임이 없으면 짧은 대기 (CPU 사용률 최적화)
                    time.sleep(0.001)  # 1ms 대기
                    
        except Exception as e:
            self.error_occurred.emit(f"캡처 루프 오류: {str(e)}")
        finally:
            self._cleanup()
            
    def _capture_and_process_frame(self):
        """
        프레임 캡처 및 처리
        
        Returns:
            bool: 처리 성공 여부
        """
        try:
            # NDI 프레임 캡처 (논블로킹)
            result = ndi.recv_capture_v2(self.ndi_recv, 0)
            frame_type, v_frame, a_frame, m_frame = result
            
            if frame_type == ndi.FRAME_TYPE_VIDEO and v_frame is not None:
                if v_frame.data is not None and v_frame.data.size > 0:
                    # 프레임을 QPixmap으로 변환
                    pixmap = self._convert_frame_to_pixmap(v_frame)
                    if not pixmap.isNull():
                        self.frame_ready.emit(pixmap)
                        
                # 프레임 해제
                ndi.recv_free_video_v2(self.ndi_recv, v_frame)
                return True
                
            elif frame_type == ndi.FRAME_TYPE_AUDIO and a_frame is not None:
                ndi.recv_free_audio_v2(self.ndi_recv, a_frame)
                
            elif frame_type == ndi.FRAME_TYPE_METADATA and m_frame is not None:
                ndi.recv_free_metadata(self.ndi_recv, m_frame)
                
            return False
            
        except Exception as e:
            self.error_occurred.emit(f"프레임 처리 오류: {str(e)}")
            return False
            
    def _convert_frame_to_pixmap(self, v_frame):
        """
        NDI 프레임을 QPixmap으로 변환
        
        Args:
            v_frame: NDI 비디오 프레임
            
        Returns:
            QPixmap: 변환된 픽스맵
        """
        try:
            with QMutexLocker(self.frame_mutex):
                # 프레임 데이터 복사
                if not v_frame.data.flags['C_CONTIGUOUS']:
                    frame_data = np.ascontiguousarray(v_frame.data.copy())
                else:
                    frame_data = v_frame.data.copy()
                    
                # BGRX 형식에서 RGB로 변환
                if frame_data.ndim == 3 and frame_data.shape[2] == 4:
                    # 알파 채널 제거 후 BGR -> RGB 변환
                    bgr_frame = frame_data[:, :, :3]
                    rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                else:
                    # 다른 형식 처리
                    rgb_frame = frame_data
                    
                # QImage로 변환
                height, width, channel = rgb_frame.shape
                bytes_per_line = 3 * width
                
                q_image = QImage(
                    rgb_frame.data,
                    width,
                    height,
                    bytes_per_line,
                    QImage.Format.Format_RGB888
                )
                
                # QPixmap으로 변환
                return QPixmap.fromImage(q_image)
                
        except Exception as e:
            print(f"프레임 변환 오류: {str(e)}")
            return QPixmap()
            
    def _cleanup(self):
        """
        리소스 정리
        """
        if self.ndi_recv:
            ndi.recv_destroy(self.ndi_recv)
            self.ndi_recv = None
            
    def stop(self):
        """
        캡처 중지
        """
        self.running = False
        self.wait()  # 스레드 종료 대기