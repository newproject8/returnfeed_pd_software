# pd_app/utils/logger.py
"""
Logger setup utility
"""

import logging
import os
from datetime import datetime

def setup_logger(log_dir="logs", log_level=logging.INFO):
    """로거 설정"""
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일명 (날짜별)
    log_file = os.path.join(log_dir, f"pd_app_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 핸들러 생성
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # 콘솔 핸들러 (Windows 인코딩 문제 해결)
    import sys
    console_handler = logging.StreamHandler(sys.stdout)
    if sys.platform == "win32":
        # Windows에서 UTF-8 출력 강제
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # 로거 설정
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s',
        handlers=[file_handler, console_handler]
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"로거 초기화 완료 - 로그 파일: {log_file}")
    
    return logger