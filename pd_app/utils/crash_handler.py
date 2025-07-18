#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""글로벌 예외 처리기"""

import sys
import traceback
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def handle_exception(exc_type, exc_value, exc_traceback):
    """처리되지 않은 예외 처리"""
    
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 크래시 로그 생성
    crash_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_log = f"logs/crash_{crash_time}.log"
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # 로그 파일에 기록
    with open(crash_log, 'w', encoding='utf-8') as f:
        f.write(f"크래시 시간: {datetime.now()}\n")
        f.write(f"Python 버전: {sys.version}\n")
        f.write(f"\n{error_msg}")
    
    logger.critical(f"처리되지 않은 예외 발생:\n{error_msg}")
    
    # 사용자에게 알림
    try:
        from PyQt6.QtWidgets import QMessageBox, QApplication
        
        if QApplication.instance():
            QMessageBox.critical(
                None,
                "오류 발생",
                f"예기치 않은 오류가 발생했습니다.\n\n"
                f"오류 로그: {crash_log}\n\n"
                f"프로그램을 재시작해 주세요."
            )
    except:
        pass

def install_handler():
    """예외 처리기 설치"""
    sys.excepthook = handle_exception
