# ndi_app/ui/main_window.py
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QTextEdit, QSplitter, QApplication, QMessageBox, 
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

from ndi_app.ndi_core.ndi_process_manager import NDIProcessManager
from ndi_app.ui.widgets import VideoDisplayWidget
from ndi_app.config import NDI_APP_NAME, NDI_APP_VERSION

class MainWindow(QMainWindow):
    print("[DEBUG] MainWindow class defined")
    def __init__(self, parent=None):
        print("[DEBUG][MainWindow.__init__] Start")
        super().__init__(parent)
        print("[DEBUG][MainWindow.__init__] super().__init__ done")
        self.setWindowTitle(f"{NDI_APP_NAME} - {NDI_APP_VERSION}")
        self.setGeometry(100, 100, 1280, 720)

        self.ndi_sources_cache = {} # Store name -> url mapping
        print("[DEBUG][MainWindow.__init__] ndi_sources_cache initialized")

        self.ndi_manager = NDIProcessManager()
        print("[DEBUG][MainWindow.__init__] NDIProcessManager instantiated")

        print("[DEBUG][MainWindow.__init__] Calling create_widgets...")
        self.create_widgets()
        print("[DEBUG][MainWindow.__init__] create_widgets done")
        print("[DEBUG][MainWindow.__init__] Calling create_layout...")
        self.create_layout()
        print("[DEBUG][MainWindow.__init__] create_layout done")
        print("[DEBUG][MainWindow.__init__] Calling create_connections...")
        self.create_connections()
        print("[DEBUG][MainWindow.__init__] create_connections done")
        print("[DEBUG][MainWindow.__init__] Calling create_menus...")
        self.create_menus()
        print("[DEBUG][MainWindow.__init__] create_menus done")

        # 상태 변수 초기화
        self.connection_status = "연결 안됨"
        self.current_fps = 0.0
        
        self.log_message_gui("Application started. Initializing NDI process manager...")
        print("[DEBUG][MainWindow.__init__] log_message_gui for app start done")
        # Delay starting NDI process slightly to ensure GUI is up
        QTimer.singleShot(100, self.ndi_manager.start_ndi_process)
        QTimer.singleShot(200, self.ndi_manager.start_finder)
        print("[DEBUG][MainWindow.__init__] NDI process manager start scheduled")
        print("[DEBUG][MainWindow.__init__] End")

    def create_widgets(self):
        self.source_label = QLabel("NDI 소스:")
        self.ndi_source_dropdown = QComboBox()
        self.ndi_source_dropdown.setToolTip("미리보기할 NDI 소스를 선택하세요")
        self.ndi_source_dropdown.addItem("소스 검색 중...")
        self.ndi_source_dropdown.setEnabled(False)
        self.ndi_source_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.setToolTip("NDI 소스 목록을 수동으로 새로고침합니다")
        
        self.connect_button = QPushButton("연결")
        self.connect_button.setToolTip("선택한 NDI 소스에 연결합니다")
        self.connect_button.setEnabled(False)

        self.disconnect_button = QPushButton("연결 해제")
        self.disconnect_button.setToolTip("현재 NDI 소스 연결을 해제합니다")
        self.disconnect_button.setEnabled(False)

        self.video_display = VideoDisplayWidget()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(120)
        self.log_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def create_layout(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(self.source_label)
        controls_layout.addWidget(self.ndi_source_dropdown, 1) # Stretch combo box
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.connect_button)
        controls_layout.addWidget(self.disconnect_button)

        # FPS 표시는 이제 프리뷰창 오버레이로 처리됨
        # 별도의 상태 라벨은 제거
        
        # Main content area (video + logs) using QSplitter
        self.video_log_splitter = QSplitter(Qt.Orientation.Vertical)
        self.video_log_splitter.addWidget(self.video_display)
        self.video_log_splitter.addWidget(self.log_area)
        self.video_log_splitter.setStretchFactor(0, 1) # Video display takes more space
        self.video_log_splitter.setStretchFactor(1, 0) # Log area fixed height initially
        self.video_log_splitter.setSizes([600, 120]) # Initial preferred sizes

        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.video_log_splitter, 1) # Splitter takes remaining space
        self.setCentralWidget(central_widget)

    def create_connections(self):
        # NDI Process Manager 시그널 연결
        self.ndi_manager.sources_changed.connect(self.update_ndi_sources_gui)
        self.ndi_manager.error_occurred.connect(self.log_error_message_gui)
        self.ndi_manager.info_message.connect(self.log_message_gui)
        self.ndi_manager.frame_received.connect(self.video_display.update_frame)
        self.ndi_manager.connection_status_changed.connect(self.on_receiver_connection_status_changed_gui)
        
        # FPS 업데이트 시그널 연결 (최적화된 성능 모니터링)
        self.ndi_manager.fps_updated.connect(self.video_display.update_fps)
        self.ndi_manager.fps_updated.connect(self.on_fps_updated)

        # UI 컨트롤 시그널 연결
        self.refresh_button.clicked.connect(self.manual_refresh_sources)
        self.connect_button.clicked.connect(self.connect_selected_source)
        self.disconnect_button.clicked.connect(self.disconnect_current_source)
        self.ndi_source_dropdown.currentIndexChanged.connect(self.on_source_selection_changed_gui)

    def create_menus(self):
        file_menu = self.menuBar().addMenu("파일(&F)")
        exit_action = QAction("종료(&X)", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = self.menuBar().addMenu("도움말(&H)")
        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self.show_about_dialog_gui)
        help_menu.addAction(about_action)

    def manual_refresh_sources(self):
        self.log_message_gui("수동 소스 새로고침을 시작합니다.")
        print("[DEBUG][MainWindow.manual_refresh_sources] Method called.")

        # Clear UI elements related to NDI sources
        self.ndi_source_dropdown.clear()
        self.ndi_source_dropdown.addItem("소스 새로고침 중...") # Placeholder
        self.ndi_source_dropdown.setEnabled(False)
        self.connect_button.setEnabled(False)
        self.ndi_sources_cache.clear()
        print("[DEBUG][MainWindow.manual_refresh_sources] Cache and UI cleared for refresh.")

        # NDI Process Manager를 통해 소스 검색 재시작
        if self.ndi_manager.is_running:
            print("[DEBUG][MainWindow.manual_refresh_sources] NDI Process Manager is running. Restarting finder...")
            self.ndi_manager.start_finder()
        else:
            print("[DEBUG][MainWindow.manual_refresh_sources] NDI Process Manager not running. Starting process and finder...")
            self.ndi_manager.start_ndi_process()
            QTimer.singleShot(100, self.ndi_manager.start_finder)
        
        self.log_message_gui("NDI 소스 검색을 다시 시작했습니다. 소스를 검색 중입니다...")

    @pyqtSlot(list) # Argument is now a list of source dictionaries
    def update_ndi_sources_gui(self, ndi_source_list: list):
        self.log_message_gui(f"GUI: NDI 소스 업데이트됨 - {len(ndi_source_list)}개 발견.")
        print(f"[DEBUG][MainWindow.update_ndi_sources_gui] Slot called with {len(ndi_source_list)} NDI Source dictionaries.")
        if ndi_source_list:
            for i, src_dict in enumerate(ndi_source_list):
                print(f"  [DEBUG] Source {i}: Name='{src_dict.get('name', 'N/A')}', URL='{src_dict.get('url', 'N/A')}'")

        current_selection_name = self.ndi_source_dropdown.currentText()
        self.ndi_source_dropdown.clear()
        self.ndi_sources_cache.clear() # Clear cache before repopulating

        if not ndi_source_list:
            self.ndi_source_dropdown.addItem("NDI 소스를 찾을 수 없습니다.")
            self.ndi_source_dropdown.setEnabled(False)
            self.connect_button.setEnabled(False)
        else:
            for source_dict in ndi_source_list: # Iterate over source dictionaries
                source_name = source_dict.get('name')
                source_url = source_dict.get('url')
                if source_name:
                    self.ndi_source_dropdown.addItem(source_name)
                    self.ndi_sources_cache[source_name] = {
                        'name': source_name,
                        'url': source_url
                    }
                else:
                    print(f"[WARNING][MainWindow.update_ndi_sources_gui] Found an NDI source without a valid 'name'. Skipping.")
            
            if current_selection_name and current_selection_name in self.ndi_sources_cache:
                self.ndi_source_dropdown.setCurrentText(current_selection_name)
            elif self.ndi_source_dropdown.count() > 0:
                self.ndi_source_dropdown.setCurrentIndex(0)

            self.ndi_source_dropdown.setEnabled(True)
            self.connect_button.setEnabled(True)
            
            # 자동 연결: 첫 번째 소스가 발견되고 현재 연결되지 않은 상태라면 자동으로 연결
            if not self.ndi_manager.is_receiver_connected() and self.ndi_source_dropdown.count() > 0:
                print("[DEBUG][MainWindow.update_ndi_sources_gui] Auto-connecting to first source...")
                QTimer.singleShot(500, self.connect_selected_source)  # 약간의 지연 후 연결
        
        print(f"[DEBUG][MainWindow.update_ndi_sources_gui] ndi_sources_cache updated. Keys: {list(self.ndi_sources_cache.keys())}")
        self.on_source_selection_changed_gui(self.ndi_source_dropdown.currentIndex()) # Update button states


    @pyqtSlot(int)
    def on_source_selection_changed_gui(self, index):
        is_placeholder = self.ndi_source_dropdown.itemText(index) in ["소스 검색 중...", "소스 새로고침 중...", "NDI 소스를 찾을 수 없습니다."]
        can_connect = index >= 0 and not is_placeholder and self.ndi_source_dropdown.itemText(index) in self.ndi_sources_cache
        self.connect_button.setEnabled(can_connect and not self.ndi_manager.is_receiver_connected())

    def connect_selected_source(self):
        print("[DEBUG][MainWindow.connect_selected_source] Method called.")
        if self.ndi_manager.is_receiver_connected():
            self.log_message_gui("이미 연결되어 있습니다. 먼저 연결을 해제하세요.")
            print("[DEBUG][MainWindow.connect_selected_source] Receiver already connected. Returning.")
            return

        selected_name = self.ndi_source_dropdown.currentText()
        print(f"[DEBUG][MainWindow.connect_selected_source] Selected source name: '{selected_name}'")
        if not selected_name or selected_name not in self.ndi_sources_cache:
            self.log_error_message_gui("연결할 유효한 NDI 소스가 선택되지 않았습니다.")
            print(f"[DEBUG][MainWindow.connect_selected_source] No valid source selected ('{selected_name}') or not in cache. Returning.")
            return

        source_info = self.ndi_sources_cache.get(selected_name)
        print(f"[DEBUG][MainWindow.connect_selected_source] Retrieved source info from cache: {source_info}")
        
        if not source_info:
            self.log_error_message_gui(f"캐시에서 '{selected_name}'의 소스 정보를 가져올 수 없습니다.")
            print(f"[ERROR][MainWindow.connect_selected_source] Source info is None for '{selected_name}'.")
            return

        source_url = source_info.get('url')
        self.log_message_gui(f"연결 시도 중: {selected_name} ({source_url})")
        
        # 항상 Proxy 모드 사용
        bandwidth_mode = "Proxy"
        print(f"[DEBUG][MainWindow.connect_selected_source] Setting bandwidth mode: {bandwidth_mode}")
        
        try:
            print(f"[DEBUG][MainWindow.connect_selected_source] Calling ndi_manager.connect_to_source...")
            self.ndi_manager.connect_to_source(source_info, bandwidth_mode)
            print("[DEBUG][MainWindow.connect_selected_source] ndi_manager.connect_to_source called successfully.")
        except Exception as e:
            self.log_error_message_gui(f"NDI 소스 {selected_name} 연결 실패: {e}")
            print(f"[ERROR][MainWindow.connect_selected_source] Exception during connection: {e}")
            QMessageBox.critical(self, "연결 오류", f"NDI 소스에 연결할 수 없습니다: {e}")

    def disconnect_current_source(self):
        self.log_message_gui("NDI 소스 연결을 해제하는 중...")
        try:
            self.ndi_manager.disconnect_source()
        except Exception as e:
            self.log_error_message_gui(f"연결 해제 중 오류: {e}")
            print(f"[ERROR][MainWindow.disconnect_current_source] Exception: {e}")
        # UI state will be updated by on_receiver_connection_status_changed_gui

    @pyqtSlot(bool)
    def on_receiver_connection_status_changed_gui(self, is_connected: bool):
        """NDI 수신기 연결 상태 변경 시 GUI 업데이트"""
        print(f"[DEBUG][MainWindow.on_receiver_connection_status_changed_gui] Connection status changed: {is_connected}")
        
        if is_connected:
            self.connection_status = "연결됨"
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            selected_source = self.ndi_source_dropdown.currentText()
            self.log_message_gui(f"NDI 소스 '{selected_source}'에 성공적으로 연결되었습니다. (최적화된 성능 모드)")
        else:
            self.connection_status = "연결 안됨"
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.log_message_gui("NDI 소스 연결이 해제되었습니다.")
            
            # 연결 해제 시 비디오 디스플레이 초기화
            self.video_display.clear_display()
        
        # FPS 표시는 이제 VideoDisplayWidget의 오버레이로 처리됨
    
    @pyqtSlot(float)
    def on_fps_updated(self, fps: float):
        """FPS 업데이트 핸들러 - 성능 모니터링"""
        self.current_fps = fps
        # 로그에 FPS 정보 기록 (너무 자주 로그하지 않도록 조건부)
        if fps > 0:
            # 1초마다 한 번씩만 로그 (이미 receiver에서 1초 간격으로 emit하므로 안전)
            if fps >= 58.0:  # 59.94fps에 가까운 경우
                status = "최적"
            elif fps >= 50.0:
                status = "양호"
            elif fps >= 30.0:
                status = "보통"
            else:
                status = "낮음"
            
            # 상태바나 로그에 간헐적으로 성능 정보 표시
            if hasattr(self, '_last_fps_log_time'):
                import time
                if time.time() - self._last_fps_log_time > 5.0:  # 5초마다 한 번
                    self.log_message_gui(f"성능 상태: {fps:.1f} FPS ({status})")
                    self._last_fps_log_time = time.time()
            else:
                import time
                self._last_fps_log_time = time.time()
                self.log_message_gui(f"성능 모니터링 시작: {fps:.1f} FPS ({status})")



    @pyqtSlot(str)
    def log_message_gui(self, message):
        self.log_area.append(message) # No [INFO] prefix, as it's from various sources

    @pyqtSlot(str)
    def log_error_message_gui(self, message):
        self.log_area.append(f"[ERROR] {message}")
        # Optionally show a QMessageBox for critical errors
        # QMessageBox.critical(self, "Error", message)

    def show_about_dialog_gui(self):
        QMessageBox.about(self, f"정보 {NDI_APP_NAME}",
                          f"{NDI_APP_NAME} 버전 {NDI_APP_VERSION}\n\n"
                          "PyQtGraph와 NDI-Python을 사용한 간단한 NDI 비디오 미리보기 도구입니다.")

    def show_update_dialog(self, update_info):
        version = update_info.get("version")
        notes = update_info.get("notes")
        url = update_info.get("url")

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle("Update Available")
        dialog.setText(f"A new version ({version}) is available!")
        dialog.setInformativeText(f"<b>Release Notes:</b><br><pre>{notes}</pre><br>Would you like to go to the download page?")
        
        update_button = dialog.addButton("Update Now", QMessageBox.ButtonRole.YesRole)
        later_button = dialog.addButton("Later", QMessageBox.ButtonRole.NoRole)
        
        dialog.exec()

        if dialog.clickedButton() == update_button:
            QDesktopServices.openUrl(QUrl(url))

    # FPS 표시는 이제 VideoDisplayWidget의 오버레이로 처리됨
    # 별도의 FPS 업데이트 메서드는 제거됨
    
    def closeEvent(self, event):
        """애플리케이션 종료 이벤트 처리"""
        print("[DEBUG][MainWindow.closeEvent] Application closing...")
        try:
            # 연결된 NDI 소스 연결 해제
            if self.ndi_manager.is_receiver_connected():
                print("[DEBUG][MainWindow.closeEvent] Disconnecting NDI source...")
                self.ndi_manager.disconnect_source()
                print("[DEBUG][MainWindow.closeEvent] NDI source disconnected.")
            
            # NDI 매니저 정리
            print("[DEBUG][MainWindow.closeEvent] Cleaning up NDI manager...")
            self.ndi_manager.cleanup()
            print("[DEBUG][MainWindow.closeEvent] NDI manager cleaned up.")
            
        except Exception as e:
            print(f"[ERROR][MainWindow.closeEvent] Exception during cleanup: {e}")
        
        print("[DEBUG][MainWindow.closeEvent] Accepting close event.")
        event.accept()

# For testing MainWindow independently (usually run via main.py)
if __name__ == '__main__':
    import NDIlib as ndi
    import os
    # Attempt to add NDI SDK path for standalone testing, mirroring main.py logic
    sdk_path_found = False
    possible_sdk_paths = [
        os.getenv("NDI_SDK_DIR", ""), # Check environment variable first
        "C:\\Program Files\\NDI\\NDI 6 SDK\\Bin\\x64",
        "C:\\Program Files\\NDI\\NDI SDK\\Bin\\x64" # Older SDK path
    ]
    for path in possible_sdk_paths:
        if path and os.path.isdir(path):
            try:
                os.add_dll_directory(path)
                print(f"Added NDI SDK DLL directory: {path} (MainWindow test block)")
                sdk_path_found = True
                break # Found and added a valid path
            except OSError as e:
                print(f"Warning: Could not add NDI SDK DLL directory {path}: {e} (MainWindow test block)")
        
    if not sdk_path_found:
        print("CRITICAL: NDI SDK DLL directory not found or could not be added. NDI will likely fail to initialize. (MainWindow test block)")

    # NDIlib_initialize() should be called by main.py in production
    if not ndi.initialize():
        print("CRITICAL: Failed to initialize NDIlib (MainWindow test block).")
        # For a GUI app, a message box is better if QApplication is available
        app_temp = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "NDI Error", "Failed to initialize NDI. The application will close.")
        sys.exit(1)
    print("NDIlib initialized (MainWindow test block).")
    
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    exit_code = app.exec()
    
    ndi.destroy()
    print("NDIlib destroyed (MainWindow test block).")
    sys.exit(exit_code)
