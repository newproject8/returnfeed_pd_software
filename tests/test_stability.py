#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 안정성 테스트
"""

import sys
import time
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_components():
    """모든 컴포넌트 테스트"""
    test_results = []
    
    # 1. PyQt6 임포트 테스트
    try:
        from PyQt6 import QtCore, QtWidgets, QtGui
        test_results.append(("PyQt6 임포트", True, "성공"))
    except Exception as e:
        test_results.append(("PyQt6 임포트", False, str(e)))
    
    # 2. NDI 모듈 테스트
    try:
        import NDIlib as ndi
        ndi.initialize()
        test_results.append(("NDI 초기화", True, "성공"))
    except Exception as e:
        test_results.append(("NDI 초기화", False, str(e)))
    
    # 3. 핵심 모듈 임포트 테스트
    try:
        from pd_app.core.ndi_manager import NDIManager
        from pd_app.core.vmix_manager import VMixManager
        from pd_app.core.srt_manager import SRTManager
        from pd_app.core.websocket_client import WebSocketClient
        test_results.append(("핵심 모듈 임포트", True, "성공"))
    except Exception as e:
        test_results.append(("핵심 모듈 임포트", False, str(e)))
    
    # 4. UI 모듈 임포트 테스트
    try:
        from pd_app.ui.main_window import MainWindow
        from pd_app.ui.ndi_widget import NDIWidget
        from pd_app.ui.tally_widget import TallyWidget
        test_results.append(("UI 모듈 임포트", True, "성공"))
    except Exception as e:
        test_results.append(("UI 모듈 임포트", False, str(e)))
    
    # 5. 유틸리티 모듈 테스트
    try:
        from pd_app.utils.logger import setup_logger
        from pd_app.utils.constants import *
        test_results.append(("유틸리티 모듈", True, "성공"))
    except Exception as e:
        test_results.append(("유틸리티 모듈", False, str(e)))
    
    # 6. WebSocket 라이브러리 테스트
    try:
        import websockets
        import asyncio
        test_results.append(("WebSocket 라이브러리", True, "성공"))
    except Exception as e:
        test_results.append(("WebSocket 라이브러리", False, str(e)))
    
    # 7. 기타 필수 라이브러리
    try:
        import numpy
        import cv2
        import requests
        test_results.append(("필수 라이브러리", True, "성공"))
    except Exception as e:
        test_results.append(("필수 라이브러리", False, str(e)))
    
    return test_results

def test_application_startup():
    """애플리케이션 시작 테스트"""
    try:
        from pd_app.utils.logger import setup_logger
        setup_logger()
        logger.info("로거 설정 완료")
        
        from pd_app.utils.settings import Settings
        settings = Settings()
        logger.info("설정 로드 완료")
        
        from pd_app.core.ndi_manager import NDIManager
        from pd_app.core.vmix_manager import VMixManager
        from pd_app.core.srt_manager import SRTManager
        from pd_app.core.websocket_client import WebSocketClient
        
        # 매니저 생성 테스트
        ndi_manager = NDIManager()
        logger.info("NDI 매니저 생성 완료")
        
        vmix_manager = VMixManager()
        logger.info("vMix 매니저 생성 완료")
        
        srt_manager = SRTManager()
        logger.info("SRT 매니저 생성 완료")
        
        ws_client = WebSocketClient(settings=settings)
        logger.info("WebSocket 클라이언트 생성 완료")
        
        return True, "모든 컴포넌트 생성 성공"
        
    except Exception as e:
        return False, f"컴포넌트 생성 실패: {str(e)}"

def main():
    print("=== PD 통합 소프트웨어 안정성 테스트 ===\n")
    
    # 1. 컴포넌트 테스트
    print("1. 컴포넌트 테스트 실행 중...")
    test_results = test_components()
    
    print("\n--- 컴포넌트 테스트 결과 ---")
    all_passed = True
    for test_name, passed, message in test_results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}: {message}")
        if not passed:
            all_passed = False
    
    if not all_passed:
        print("\n⚠️ 일부 컴포넌트 테스트 실패. 필요한 패키지를 설치하세요.")
        return
    
    # 2. 애플리케이션 시작 테스트
    print("\n2. 애플리케이션 시작 테스트 실행 중...")
    success, message = test_application_startup()
    
    if success:
        print(f"✅ 애플리케이션 시작 테스트: {message}")
    else:
        print(f"❌ 애플리케이션 시작 테스트: {message}")
        return
    
    # 3. GUI 테스트
    print("\n3. GUI 테스트 실행 중...")
    app = QApplication(sys.argv)
    
    try:
        from pd_app.ui.main_window import MainWindow
        from pd_app.core.ndi_manager import NDIManager
        from pd_app.core.vmix_manager import VMixManager
        from pd_app.core.srt_manager import SRTManager
        from pd_app.core.websocket_client import WebSocketClient
        from pd_app.utils.settings import Settings
        
        settings = Settings()
        managers = {
            'ndi': NDIManager(),
            'vmix': VMixManager(),
            'srt': SRTManager(),
            'websocket': WebSocketClient(settings=settings),
            'settings': settings
        }
        
        main_window = MainWindow(managers)
        main_window.show()
        
        print("✅ GUI 생성 성공")
        
        # 5초 후 자동 종료
        QTimer.singleShot(5000, app.quit)
        
        print("\n애플리케이션이 5초 동안 실행됩니다...")
        app.exec()
        
        print("✅ GUI 테스트 완료")
        
    except Exception as e:
        print(f"❌ GUI 테스트 실패: {str(e)}")
        return
    
    print("\n=== 모든 안정성 테스트 통과! ===")
    print("PD 통합 소프트웨어가 정상적으로 작동할 준비가 되었습니다.")

if __name__ == "__main__":
    main()