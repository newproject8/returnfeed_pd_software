# pd_app/ui/ndi_widget.py
"""
NDI Widget - NDI 소스 선택 및 비디오 프리뷰 UI
"""

import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

class NDIWidget(QWidget):
    """NDI 프리뷰 위젯"""
    
    def __init__(self, ndi_manager):
        super().__init__()
        self.ndi_manager = ndi_manager
        self.frame_skip_counter = 0
        self.init_ui()
        self.init_connections()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 컨트롤 패널
        control_layout = QHBoxLayout()
        
        # NDI 소스 검색 버튼
        self.search_button = QPushButton("NDI 소스 탐색")
        control_layout.addWidget(self.search_button)
        
        # NDI 소스 선택 드롭다운
        self.source_combo = QComboBox()
        self.source_combo.addItem("NDI 소스를 선택하세요")
        self.source_combo.setMinimumWidth(300)
        control_layout.addWidget(self.source_combo)
        
        # 재생 모드 선택
        self.original_radio = QRadioButton("원본 재생")
        self.proxy_radio = QRadioButton("프록시 재생")
        self.original_radio.setChecked(True)
        
        mode_group = QButtonGroup()
        mode_group.addButton(self.original_radio)
        mode_group.addButton(self.proxy_radio)
        
        control_layout.addWidget(self.original_radio)
        control_layout.addWidget(self.proxy_radio)
        
        control_layout.addStretch()
        
        # 프리뷰 시작/중지 버튼
        self.preview_button = QPushButton("프리뷰 시작")
        self.preview_button.setEnabled(False)
        control_layout.addWidget(self.preview_button)
        
        layout.addLayout(control_layout)
        
        # 비디오 프리뷰 영역
        self.video_widget = pg.RawImageWidget()
        self.video_widget.setMinimumHeight(400)
        layout.addWidget(self.video_widget)
        
        # 상태 표시
        self.status_label = QLabel("상태: NDI 준비")
        layout.addWidget(self.status_label)
        
    def init_connections(self):
        """시그널 연결"""
        # NDI 관리자 시그널
        self.ndi_manager.sources_updated.connect(self.on_sources_updated)
        self.ndi_manager.frame_received.connect(self.on_frame_received)
        self.ndi_manager.connection_status_changed.connect(self.on_status_changed)
        
        # UI 시그널
        self.search_button.clicked.connect(self.search_sources)
        self.source_combo.currentIndexChanged.connect(self.on_source_selected)
        self.preview_button.clicked.connect(self.toggle_preview)
        
    def search_sources(self):
        """NDI 소스 검색"""
        try:
            self.status_label.setText("상태: NDI 소스 검색 중...")
            self.status_label.setStyleSheet("color: blue;")
            self.search_button.setEnabled(False)
            
            # 기존 소스 목록 초기화
            self.source_combo.clear()
            self.source_combo.addItem("검색 중...")
            
            # NDI 소스 검색 시작 (비동기)
            success = self.ndi_manager.start_source_discovery()
            
            if not success:
                self.status_label.setText("상태: NDI 초기화 실패")
                self.status_label.setStyleSheet("color: red;")
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "NDI 오류",
                    "NDI 라이브러리를 초기화할 수 없습니다.\n\n"
                    "가능한 원인:\n"
                    "- NDI 런타임이 설치되지 않았습니다\n"
                    "- 네트워크 권한이 없습니다\n"
                    "- 방화벽이 NDI를 차단하고 있습니다"
                )
                
                self.source_combo.clear()
                self.source_combo.addItem("NDI 초기화 실패")
            
            # 3초 후 버튼 재활성화
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.search_button.setEnabled(True))
            
        except Exception as e:
            self.status_label.setText(f"상태: 검색 오류 - {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            self.search_button.setEnabled(True)
            
            self.source_combo.clear()
            self.source_combo.addItem("검색 오류 발생")
            
            print(f"NDI 소스 검색 오류: {e}")
            import traceback
            traceback.print_exc()
        
    def on_sources_updated(self, sources):
        """NDI 소스 목록 업데이트"""
        self.source_combo.clear()
        
        if sources:
            self.source_combo.addItems(sources)
            self.status_label.setText(f"상태: {len(sources)}개 소스 발견")
        else:
            self.source_combo.addItem("NDI 소스를 찾을 수 없습니다")
            self.status_label.setText("상태: NDI 소스 없음")
            
    def on_source_selected(self, index):
        """소스 선택 처리"""
        if index >= 0 and self.source_combo.currentText() != "NDI 소스를 선택하세요":
            self.preview_button.setEnabled(True)
        else:
            self.preview_button.setEnabled(False)
            
    def toggle_preview(self):
        """프리뷰 시작/중지"""
        if self.preview_button.text() == "프리뷰 시작":
            source_name = self.source_combo.currentText()
            if source_name and source_name != "NDI 소스를 선택하세요" and source_name != "NDI 소스를 찾을 수 없습니다":
                try:
                    # 프리뷰 시작 시도
                    success = self.ndi_manager.start_preview(source_name)
                    if success:
                        self.preview_button.setText("프리뷰 중지")
                        self.source_combo.setEnabled(False)
                        self.search_button.setEnabled(False)
                        self.status_label.setText(f"상태: {source_name} 프리뷰 중")
                        self.status_label.setStyleSheet("color: green;")
                    else:
                        # 프리뷰 시작 실패
                        self.status_label.setText("상태: 프리뷰 시작 실패 - NDI 소스에 연결할 수 없습니다")
                        self.status_label.setStyleSheet("color: red;")
                        
                        # 에러 메시지 표시
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            self, 
                            "프리뷰 오류", 
                            f"'{source_name}' NDI 소스에 연결할 수 없습니다.\n\n"
                            "가능한 원인:\n"
                            "- NDI 소스가 오프라인 상태입니다\n"
                            "- 네트워크 연결 문제가 있습니다\n"
                            "- NDI 소스가 다른 애플리케이션에서 사용 중입니다\n\n"
                            "NDI 소스를 다시 검색하거나 다른 소스를 선택해주세요."
                        )
                except Exception as e:
                    # 예외 처리
                    self.status_label.setText(f"상태: 프리뷰 오류 - {str(e)}")
                    self.status_label.setStyleSheet("color: red;")
                    
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(
                        self, 
                        "프리뷰 오류", 
                        f"NDI 프리뷰를 시작하는 중 오류가 발생했습니다:\n\n{str(e)}"
                    )
            else:
                # 유효하지 않은 소스 선택
                self.status_label.setText("상태: 유효한 NDI 소스를 선택해주세요")
                self.status_label.setStyleSheet("color: orange;")
        else:
            try:
                # 프리뷰 중지
                self.ndi_manager.stop_preview()
                self.preview_button.setText("프리뷰 시작")
                self.source_combo.setEnabled(True)
                self.search_button.setEnabled(True)
                self.status_label.setText("상태: 프리뷰 중지됨")
                self.status_label.setStyleSheet("color: black;")
                
                # 비디오 위젯 초기화
                self.video_widget.setImage(np.zeros((480, 640, 3), dtype=np.uint8))
            except Exception as e:
                # 중지 중 오류 처리
                self.status_label.setText(f"상태: 프리뷰 중지 오류 - {str(e)}")
                self.status_label.setStyleSheet("color: red;")
                
                # UI는 원래 상태로 복구
                self.preview_button.setText("프리뷰 시작")
                self.source_combo.setEnabled(True)
                self.search_button.setEnabled(True)
            
    def on_frame_received(self, frame):
        """프레임 수신 처리"""
        # 프레임 스킵으로 GUI 부하 감소 (3프레임당 1개만 표시)
        self.frame_skip_counter += 1
        if self.frame_skip_counter % 3 != 0:
            return
            
        try:
            # 프레임 유효성 검사
            if frame is None:
                return
                
            if not isinstance(frame, np.ndarray):
                # numpy 배열로 변환 시도
                try:
                    frame = np.asarray(frame)
                except Exception:
                    return
                
            # 프레임 차원 검사
            if frame.ndim < 2 or frame.ndim > 3:
                return
                
            # PyQtGraph RawImageWidget에 직접 표시
            if frame.ndim == 3:
                # RGB/RGBA 형식 확인
                if frame.shape[2] == 4:
                    # RGBA -> RGB 변환
                    frame = frame[:, :, :3]
                elif frame.shape[2] != 3:
                    print(f"경고: 지원하지 않는 채널 수: {frame.shape[2]}")
                    return
                    
                # BGR -> RGB 변환 (필요한 경우)
                # frame = frame[:, :, ::-1]
                
            # 90도 회전 문제 해결 - vMix NDI는 항상 회전되어 있음
            # 안전한 회전 처리
            try:
                # vMix NDI Output은 항상 90도 회전되어 있으므로 무조건 회전
                frame = np.rot90(frame, k=-1)  # k=-1은 시계방향 90도 회전
            except Exception as rot_error:
                # 회전 실패해도 원본 프레임 사용
                pass
                
            # 프레임 크기 확인 (너무 크거나 작은 경우 경고)
            height, width = frame.shape[:2]
            if width < 100 or height < 100:
                print(f"경고: 프레임 크기가 너무 작습니다: {width}x{height}")
            elif width > 4096 or height > 4096:
                print(f"경고: 프레임 크기가 너무 큽니다: {width}x{height}")
                
            # 프레임 리사이즈로 성능 향상
            try:
                # 프레임이 너무 크면 리사이즈
                if frame.shape[0] > 1080 or frame.shape[1] > 1920:
                    import cv2
                    frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
                
                self.video_widget.setImage(frame)
            except Exception as display_error:
                # 디스플레이 오류 무시 (크래시 방지)
                pass
            
        except AttributeError as e:
            print(f"프레임 표시 오류 (속성 오류): {e}")
            self.status_label.setText("상태: 프레임 표시 오류")
            self.status_label.setStyleSheet("color: red;")
        except ValueError as e:
            print(f"프레임 표시 오류 (값 오류): {e}")
            self.status_label.setText("상태: 잘못된 프레임 형식")
            self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            print(f"프레임 표시 오류 (일반): {type(e).__name__}: {e}")
            # 연속적인 오류를 방지하기 위해 상태만 업데이트하고 UI는 유지
            import traceback
            traceback.print_exc()
            
    def on_status_changed(self, status, color):
        """상태 변경 처리"""
        self.status_label.setText(f"상태: {status}")
        self.status_label.setStyleSheet(f"color: {color};")