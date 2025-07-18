# pd_app/utils/logger.py
"""
Logger setup utility
"""

import logging
import os
import sys
import traceback
from datetime import datetime

def setup_logger(log_dir="logs", log_level=logging.DEBUG):
    """향상된 로거 설정 - 더 자세한 오류 추적"""
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일명 (날짜와 시간별)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"pd_app_{timestamp}.log")
    
    # 파일 핸들러 생성 - 더 자세한 포맷
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - '
        '%(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # 콘솔 핸들러 - 간단한 포맷
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Windows 인코딩 문제 해결
    if sys.platform == "win32":
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except:
            pass
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # 기존 핸들러 제거
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # 전역 예외 핸들러 설정
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = logging.getLogger('CRITICAL')
        logger.critical(
            "처리되지 않은 예외 발생!",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
    
    logger = logging.getLogger(__name__)
    logger.info(f"향상된 로거 초기화 완료 - 로그 파일: {log_file}")
    logger.info(f"Python 버전: {sys.version}")
    logger.info(f"플랫폼: {sys.platform}")
    
    return logger