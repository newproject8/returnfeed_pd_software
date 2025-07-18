#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReturnFeed Unified Application
NDI Discovery & vMix Tally Broadcaster

통합 애플리케이션 진입점
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# **핵심 수정**: NDI DLL 경로 추가 (원본 main.py 방식)
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

if sys.platform == "win32":
    if hasattr(os, 'add_dll_directory'):
        try:
            if os.path.isdir(NDI_SDK_DLL_PATH):
                os.add_dll_directory(NDI_SDK_DLL_PATH)
                print(f"Added to DLL search path: {NDI_SDK_DLL_PATH}")
            else:
                print(f"Warning: NDI SDK DLL path not found: {NDI_SDK_DLL_PATH}")
        except Exception as e:
            print(f"Warning: Failed to add NDI SDK DLL path: {e}")
    else:
        print("Warning: os.add_dll_directory not available")

# 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ui.main_window import MainWindow
from utils.logger import setup_logging

# **핵심 수정**: NDI 라이브러리 import (전역 초기화용)
try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    ndi = None


def main():
    """메인 함수 - 전역 NDI 초기화 포함"""
    
    # **🚀 ULTRATHINK 크래시 해결**: 문서 기반 환경 변수 설정
    # 1. OpenGL 백엔드 강제 - Direct3D와 OpenGL 충돌 방지
    os.environ['QSG_RHI_BACKEND'] = 'opengl'
    print("✅ Qt RHI backend forced to OpenGL (WSL2 호환성 향상)")
    
    # 2. FFmpeg 백엔드 명시 - 일관된 멀티미디어 플러그인 사용
    os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'ffmpeg'
    print("✅ Qt Multimedia backend set to FFmpeg")
    
    # 3. 최적화된 로깅 설정 - 성능 향상을 위해 RHI 디버그 로그 비활성화
    os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false'
    print("✅ Qt debug logging optimized for performance")
    
    # **핵심 수정**: 전역 NDI 초기화 (원본 main.py 방식)
    if NDI_AVAILABLE and ndi:
        if not ndi.initialize():
            print("CRITICAL: Failed to initialize NDIlib (ndi.initialize). The application cannot start.")
            # Qt 애플리케이션 생성 전에 에러 메시지 표시
            app_for_error_msg = QApplication.instance()
            if not app_for_error_msg:
                app_for_error_msg = QApplication(sys.argv)
            
            QMessageBox.critical(None, "NDI Initialization Error", 
                                 "Failed to initialize the NDI library (ndi.initialize). \n"
                                 "Please ensure the NDI SDK is correctly installed and accessible. \n"
                                 "The application will now close.")
            sys.exit(1)
        print("NDIlib (ndi.initialize) initialized successfully by main.py.")
    else:
        print("Warning: NDI library not available. NDI features will be disabled.")
    
    # 로깅 설정
    setup_logging()
    
    # High DPI 설정
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("ReturnFeed Unified")
    app.setOrganizationName("ReturnFeed")
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 애플리케이션 실행
    exit_code = app.exec()
    
    # **핵심 수정**: 애플리케이션 종료 시 NDI 정리 (원본 main.py 방식)
    if NDI_AVAILABLE and ndi:
        ndi.destroy()
        print("NDIlib (ndi.destroy) deinitialized by main.py.")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()