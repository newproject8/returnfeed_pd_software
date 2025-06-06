# ndi_app/ui/widgets.py
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QImage
import time
import queue
import numpy as np
import cv2

# 최적화된 위젯 임포트
from .optimized_widgets import AspectRatioPreviewLabel, PreciseNDITimer, NDIFrameCapture

# Configure PyQtGraph for maximum performance
pg.setConfigOptions(
    imageAxisOrder='row-major', 
    useNumba=True, 
    antialias=False,  # Disable antialiasing for better performance
    useOpenGL=True,   # Enable OpenGL acceleration if available
    enableExperimental=True,
    crashWarning=False  # Disable crash warnings for performance
)

class VideoDisplayWidget(AspectRatioPreviewLabel):
    """최적화된 비디오 디스플레이 위젯 - 16:9 고정 비율과 59.94fps 지원"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 정밀 타이밍 시스템
        self.timer = PreciseNDITimer()
        
        # 프레임 버퍼링
        self.frame_mutex = QMutex()
        self.latest_frame = None
        self.frame_pending = False
        
        # 59.94fps 정밀 업데이트 타이머
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._process_pending_frame)
        
        # FPS 계산을 위한 변수들
        self.frame_count = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.fps_history = []
        
        # 오버레이 라벨 생성
        self.fps_overlay = QLabel(self)
        self.fps_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: #00ff00;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.fps_overlay.setText("FPS: 0.00")
        self.fps_overlay.setFixedSize(100, 30)
        self.fps_overlay.move(10, 10)  # 좌상단 위치
        self.fps_overlay.show()
        
        # 기본 이미지 설정
        self.set_default_image()
    
    def set_default_image(self):
        """기본 'No Signal' 이미지 설정"""
        self.setText("NDI 신호 없음\nNDI 소스에 연결하세요")
        self.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #cccccc;
                border: 2px dashed #666666;
                font-size: 14px;
                font-weight: bold;
            }
        """)

    @pyqtSlot(np.ndarray)
    def update_frame(self, frame_data):
        """NDI 소스 동기화된 정밀 타이밍으로 프레임 업데이트"""
        with QMutexLocker(self.frame_mutex):
            # 최신 프레임 저장
            self.latest_frame = frame_data
            
            # 프레임 처리가 대기 중이 아닐 때만 새로운 처리 시작
            if not self.frame_pending:
                self.frame_pending = True
                
                # 프레임레이트 감지 중이면 즉시 처리
                if not self.timer.fps_detected:
                    self.update_timer.start(1)  # 1ms 후 즉시 처리
                else:
                    # 감지된 프레임레이트에 따른 정밀 타이밍
                    delay = self.timer.get_next_frame_delay()
                    delay_ms = max(1, int(delay * 1000))
                    self.update_timer.start(delay_ms)
    
    def _process_pending_frame(self):
        """대기 중인 프레임을 59.94fps 타이밍으로 처리"""
        with QMutexLocker(self.frame_mutex):
            if self.latest_frame is None:
                self.frame_pending = False
                return
            
            frame_data = self.latest_frame
            self.latest_frame = None
            self.frame_pending = False
            
            # FPS 통계 업데이트 (실제 프레임 처리 시에만)
            self.timer.update_fps_statistics()
            self._update_fps_calculation()
        
        try:
            # 640x360 해상도 최적화된 고속 프레임 처리
            if frame_data.ndim == 3 and frame_data.shape[2] == 4:
                # NDI BGRX_BGRA 형식: RGB로 변환 (알파 채널 제거)
                bgr_frame = frame_data[:, :, :3]
                rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                
            elif frame_data.ndim == 3 and frame_data.shape[2] == 3:
                # BGR 형식으로 가정하고 RGB로 변환
                rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
                
            elif frame_data.ndim == 3 and frame_data.shape[2] == 2:
                # 2채널 데이터 처리 - 첫 번째 채널을 그레이스케일로 사용
                gray_data = frame_data[:, :, 0]
                rgb_frame = cv2.cvtColor(gray_data, cv2.COLOR_GRAY2RGB)
                
            else:
                print(f"[VideoDisplayWidget]: 지원되지 않는 프레임 형식: {frame_data.shape}")
                return
            
            # 640x360 해상도로 직접 리사이즈 (픽셀 처리 최적화)
            if rgb_frame.shape[:2] != (360, 640):
                rgb_frame = cv2.resize(rgb_frame, (640, 360), interpolation=cv2.INTER_LINEAR)
            
            # QImage로 효율적 변환 (640x360 고정)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            
            # 연속 메모리 보장
            if not rgb_frame.flags['C_CONTIGUOUS']:
                rgb_frame = np.ascontiguousarray(rgb_frame)
            
            q_image = QImage(
                rgb_frame.data, 
                width, 
                height, 
                bytes_per_line, 
                QImage.Format.Format_RGB888
            )
            
            # QPixmap으로 변환 (640x360 고정 해상도)
            pixmap = QPixmap.fromImage(q_image)
            
            if not pixmap.isNull():
                # 640x360 고정 해상도로 표시
                self.setPixmap(pixmap)
                
                # 활성 비디오 스타일 업데이트
                self.setStyleSheet("background-color: black; border: 2px solid #00aa00;")
            
            # FPS 통계 업데이트
            self.timer.update_fps_statistics()
                
        except Exception as e:
            print(f"[VideoDisplayWidget]: 프레임 처리 오류: {e}")

    def clear_display(self):
        """디스플레이 초기화 및 기본 이미지 표시"""
        with QMutexLocker(self.frame_mutex):
            self.latest_frame = None
            self.frame_pending = False
        
        self.update_timer.stop()
        
        # FPS 계산 초기화
        self.frame_count = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.fps_history = []
        
        # 오버레이 초기화
        self.fps_overlay.setText("FPS: 0.00")
        
        self.set_default_image()
        
    def _update_fps_calculation(self):
        """FPS 계산 및 오버레이 업데이트"""
        self.frame_count += 1
        current_time = time.time()
        
        # 1초마다 FPS 계산
        if current_time - self.fps_start_time >= 1.0:
            elapsed_time = current_time - self.fps_start_time
            fps = self.frame_count / elapsed_time
            
            # FPS 히스토리 관리 (최근 5개 값의 평균)
            self.fps_history.append(fps)
            if len(self.fps_history) > 5:
                self.fps_history.pop(0)
            
            # 평균 FPS 계산
            self.current_fps = sum(self.fps_history) / len(self.fps_history)
            
            # 오버레이 업데이트
            self.fps_overlay.setText(f"FPS: {self.current_fps:.1f}")
            
            # 리셋
            self.frame_count = 0
            self.fps_start_time = current_time
            
            print(f"[VideoDisplayWidget] FPS 업데이트: {self.current_fps:.1f}")
    
    def get_current_fps(self):
        """현재 평균 FPS 반환"""
        return self.current_fps
    
    @pyqtSlot(float)
    def update_fps(self, fps):
        """외부에서 FPS 정보를 업데이트 (NDI 수신기에서 직접 전달)"""
        self.current_fps = fps
        
        # FPS 히스토리 관리 (최근 5개 값의 평균)
        self.fps_history.append(fps)
        if len(self.fps_history) > 5:
            self.fps_history.pop(0)
        
        # 평균 FPS 계산
        avg_fps = sum(self.fps_history) / len(self.fps_history)
        
        # 오버레이 업데이트 (색상으로 성능 상태 표시)
        if avg_fps >= 58.0:  # 최적 (녹색)
            color = "#00ff00"
            status = "최적"
        elif avg_fps >= 50.0:  # 양호 (노란색)
            color = "#ffff00"
            status = "양호"
        elif avg_fps >= 30.0:  # 보통 (주황색)
            color = "#ff8800"
            status = "보통"
        else:  # 낮음 (빨간색)
            color = "#ff0000"
            status = "낮음"
        
        # 오버레이 스타일 업데이트
        self.fps_overlay.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(0, 0, 0, 180);
                color: {color};
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
        self.fps_overlay.setText(f"FPS: {avg_fps:.1f} ({status})")
        self.fps_overlay.setFixedSize(120, 30)  # 크기 조정
