# logger.py
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """애플리케이션 로깅 설정"""
    
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 경로
    log_file = os.path.join(log_dir, f"returnfeed_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 로그 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    
    # 파일 핸들러 (로테이션)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # 라이브러리 로거 레벨 조정
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # 초기 로그
    logging.info("=" * 60)
    logging.info("ReturnFeed Unified Application Started")
    logging.info(f"Log Level: {log_level}")
    logging.info(f"Log File: {log_file}")
    logging.info("=" * 60)