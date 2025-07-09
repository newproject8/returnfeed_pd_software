#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 - 메인 실행 파일
NDI 프리뷰, vMix Tally, SRT 스트리밍 통합 시스템
"""

import sys
import os

# NDI DLL 경로 추가 (Windows)
if sys.platform == "win32":
    NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"
    if hasattr(os, 'add_dll_directory') and os.path.isdir(NDI_SDK_DLL_PATH):
        try:
            os.add_dll_directory(NDI_SDK_DLL_PATH)
            print(f"NDI SDK DLL 경로 추가: {NDI_SDK_DLL_PATH}")
        except Exception as e:
            print(f"NDI SDK DLL 경로 추가 실패: {e}")

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# 로거 설정
from pd_app.utils import setup_logger
logger = setup_logger()

# NDI 라이브러리 초기화 테스트
try:
    import NDIlib as ndi
    if not ndi.initialize():
        raise RuntimeError("NDIlib 초기화 실패")
    logger.info("NDIlib 초기화 성공")
except Exception as e:
    logger.error(f"NDIlib 초기화 오류: {e}")
    # 계속 진행 (NDI 없이도 다른 기능 사용 가능)

# 메인 윈도우 임포트
from pd_app.ui import MainWindow
from pd_app.config import Settings
from pd_app.utils.helpers import get_platform_info

def show_error_dialog(title, message):
    """오류 대화상자 표시"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    QMessageBox.critical(None, title, message)

def main():
    """메인 함수"""
    try:
        # 플랫폼 정보 로깅
        platform_info = get_platform_info()
        logger.info(f"플랫폼 정보: {platform_info}")
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        app.setApplicationName("PD 통합 소프트웨어")
        app.setOrganizationName("PD Software Team")
        
        # 고DPI 스케일링 설정
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        # 설정 로드
        settings = Settings()
        
        # 메인 윈도우 생성
        main_window = MainWindow()
        
        # 저장된 윈도우 위치/크기 복원
        geometry = settings.get('ui.window_geometry')
        if geometry:
            main_window.restoreGeometry(geometry)
        
        # 마지막 탭 복원
        last_tab = settings.get('ui.last_tab', 0)
        main_window.tab_widget.setCurrentIndex(last_tab)
        
        # 윈도우 표시
        main_window.show()
        
        logger.info("애플리케이션 시작 완료")
        
        # 이벤트 루프 실행
        exit_code = app.exec()
        
        # 종료 시 설정 저장
        settings.update_window_geometry(main_window.saveGeometry())
        settings.update_last_tab(main_window.tab_widget.currentIndex())
        
        # NDI 정리
        try:
            ndi.destroy()
            logger.info("NDIlib 정리 완료")
        except:
            pass
            
        logger.info("애플리케이션 정상 종료")
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"치명적 오류: {e}", exc_info=True)
        show_error_dialog("치명적 오류", f"애플리케이션 실행 중 오류가 발생했습니다:\n{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()