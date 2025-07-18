# main.py
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
import os # os 모듈 import 추가
from ndi_app.updater import check_for_updates

# --- NDI DLL 경로 추가 시작 ---
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64" # 실제 DLL 파일이 있는 경로

if sys.platform == "win32": # Windows인지 확인
    if hasattr(os, 'add_dll_directory'): # Python 3.8+ 기능 확인
        try:
            if os.path.isdir(NDI_SDK_DLL_PATH):
                os.add_dll_directory(NDI_SDK_DLL_PATH)
                print(f"Added to DLL search path: {NDI_SDK_DLL_PATH}")
            else:
                print(f"Warning: NDI SDK DLL path not found: {NDI_SDK_DLL_PATH}. NDI might not work.")
        except Exception as e:
            print(f"Warning: Failed to add NDI SDK DLL path: {e}")
    else:
        print("Warning: os.add_dll_directory not available (requires Python 3.8+ on Windows). Consider upgrading Python or setting system PATH correctly.")
# --- NDI DLL 경로 추가 끝 ---

from ndi_app.ui.main_window import MainWindow
import d as ndi

def main():
    # Initialize NDI library globally at the start of the application
    # This is crucial and should only be done once.
    if not ndi.initialize():
        print("CRITICAL: Failed to initialize NDIlib (ndi.initialize). The application cannot start.")
        # Try to show a message box if possible
        app_for_error_msg = QApplication.instance() # Check if an instance already exists
        if not app_for_error_msg:
            app_for_error_msg = QApplication(sys.argv) # Create one for the message box
        
        QMessageBox.critical(None, "NDI Initialization Error", 
                             "Failed to initialize the NDI library (ndi.initialize). \n"
                             "Please ensure the NDI SDK is correctly installed and accessible. \n"
                             "The application will now close.")
        sys.exit(1)
    print("NDIlib (ndi.initialize) initialized successfully by main.py.")

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
# Check for updates in the background
    update_info = check_for_updates()
    if update_info:
        main_win.show_update_dialog(update_info)

    exit_code = app.exec()

    # Deinitialize NDI library when the application is about to exit
    ndi.destroy()
    print("NDIlib (ndi.destroy) deinitialized by main.py.")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
