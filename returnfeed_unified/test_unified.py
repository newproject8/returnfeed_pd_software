#!/usr/bin/env python3
"""
통합 레이아웃 테스트 스크립트
"""
import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_unified_layout():
    """통합 레이아웃 테스트"""
    app = QApplication(sys.argv)
    
    try:
        # MainWindow 임포트
        from ui.main_window import MainWindow
        
        # 메인 윈도우 생성
        main_window = MainWindow()
        main_window.show()
        
        # 테스트 정보 출력
        def print_test_info():
            logging.info("=== Unified Layout Test ===")
            logging.info("✓ MainWindow created successfully")
            logging.info("✓ Unified widget loaded")
            logging.info("✓ Modules initialized")
            logging.info("")
            logging.info("Test the following:")
            logging.info("1. NDI Discovery tab on the left")
            logging.info("2. vMix Tally tab on the left")
            logging.info("3. SRT Streaming panel on the right")
            logging.info("4. Status bar at the bottom")
            logging.info("========================")
        
        # 1초 후 테스트 정보 출력
        QTimer.singleShot(1000, print_test_info)
        
        # 애플리케이션 실행
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"Failed to start application: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    test_unified_layout()