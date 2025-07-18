#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""크래시 디버깅 및 문제 진단 스크립트"""

import sys
import os
import logging
import traceback
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_crash.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_isolated_components():
    """각 컴포넌트를 격리하여 테스트"""
    
    logger.info("=== 격리된 컴포넌트 테스트 시작 ===")
    
    # 1. NDI만 테스트
    try:
        logger.info("1. NDI Manager 단독 테스트")
        from pd_app.core.ndi_manager import NDIManager
        ndi_manager = NDIManager()
        ndi_manager.initialize()
        logger.info("NDI Manager 초기화 성공")
        
        # 소스 검색 대기
        import time
        time.sleep(3)
        
        # 정리
        ndi_manager.cleanup()
        logger.info("NDI Manager 정리 완료")
        
    except Exception as e:
        logger.error(f"NDI Manager 테스트 실패: {e}")
        logger.error(traceback.format_exc())
    
    # 2. vMix만 테스트
    try:
        logger.info("\n2. vMix Manager 단독 테스트")
        from pd_app.core.vmix_manager import VMixManager
        vmix_manager = VMixManager()
        # vMix 연결은 실제 vMix가 실행 중일 때만 가능
        logger.info("vMix Manager 생성 성공")
        
    except Exception as e:
        logger.error(f"vMix Manager 테스트 실패: {e}")
        logger.error(traceback.format_exc())
    
    # 3. WebSocket만 테스트
    try:
        logger.info("\n3. WebSocket Client 단독 테스트")
        from pd_app.network.websocket_client import WebSocketClient
        ws_client = WebSocketClient()
        logger.info("WebSocket Client 생성 성공")
        
    except Exception as e:
        logger.error(f"WebSocket Client 테스트 실패: {e}")
        logger.error(traceback.format_exc())

def test_thread_conflicts():
    """스레드 충돌 테스트"""
    
    logger.info("\n=== 스레드 충돌 테스트 ===")
    
    app = QApplication(sys.argv)
    
    from pd_app.ui.main_window import MainWindow
    
    # 메인 윈도우 생성 (모든 매니저 초기화)
    try:
        main_window = MainWindow()
        logger.info("메인 윈도우 생성 성공")
        
        # 각 매니저의 스레드 상태 확인
        logger.info("\n스레드 상태 확인:")
        
        # NDI 워커 스레드
        if hasattr(main_window.ndi_manager, 'worker_thread'):
            worker_thread = main_window.ndi_manager.worker_thread
            if worker_thread and hasattr(worker_thread, 'isRunning'):
                logger.info(f"NDI 워커 스레드: {worker_thread.isRunning()}")
        
        # WebSocket 스레드
        if hasattr(main_window, 'ws_client') and main_window.ws_client:
            ws_client = main_window.ws_client
            if hasattr(ws_client, 'isRunning'):
                logger.info(f"WebSocket 스레드: {ws_client.isRunning()}")
        
        # vMix TCP 리스너 스레드
        if hasattr(main_window.vmix_manager, 'tcp_listener'):
            tcp_listener = main_window.vmix_manager.tcp_listener
            if tcp_listener and hasattr(tcp_listener, 'isRunning'):
                logger.info(f"vMix TCP 스레드: {tcp_listener.isRunning()}")
        
        # 5초 후 종료
        QTimer.singleShot(5000, app.quit)
        
        logger.info("\n애플리케이션 실행 (5초)...")
        app.exec()
        
        logger.info("정상 종료")
        
    except Exception as e:
        logger.error(f"스레드 테스트 실패: {e}")
        logger.error(traceback.format_exc())

def check_resource_usage():
    """리소스 사용량 확인"""
    
    logger.info("\n=== 리소스 사용량 확인 ===")
    
    try:
        import psutil
        process = psutil.Process()
        
        logger.info(f"CPU 사용률: {process.cpu_percent(interval=1)}%")
        logger.info(f"메모리 사용량: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        logger.info(f"스레드 수: {process.num_threads()}")
        
        # 열린 파일/핸들 수
        try:
            logger.info(f"열린 핸들 수: {len(process.open_files())}")
        except:
            pass
            
    except ImportError:
        logger.warning("psutil이 설치되지 않음")

def main():
    """메인 디버깅 함수"""
    
    logger.info("크래시 디버깅 시작\n")
    
    # 1. 격리된 컴포넌트 테스트
    test_isolated_components()
    
    # 2. 리소스 사용량 확인
    check_resource_usage()
    
    # 3. 스레드 충돌 테스트
    test_thread_conflicts()
    
    logger.info("\n디버깅 완료")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"디버깅 중 오류 발생: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)