import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger():
    """애플리케이션 로거 설정"""
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 루트 로거 설정
    logger = logging.getLogger('NDIApp')
    logger.setLevel(logging.DEBUG)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (로그 파일 로테이션)
    file_handler = RotatingFileHandler('ndi_app.log', maxBytes=5*1024*1024, backupCount=2)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    return logger

# 전역 로거 인스턴스
log = setup_logger()