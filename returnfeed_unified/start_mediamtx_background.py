#!/usr/bin/env python3
"""
MediaMTX 백그라운드 실행 스크립트
"""
import subprocess
import sys
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_mediamtx_background():
    """MediaMTX를 백그라운드에서 실행"""
    mediamtx_dir = "mediamtx_local"
    
    # 디렉토리 확인
    if not os.path.exists(mediamtx_dir):
        logger.error(f"MediaMTX directory not found: {mediamtx_dir}")
        logger.info("Run 'python setup_local_mediamtx.py' first")
        return False
    
    # 설정 파일 확인
    config_path = os.path.join(mediamtx_dir, "mediamtx.yml")
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        return False
    
    # WSL 환경 확인
    is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
    
    try:
        if is_wsl:
            # WSL에서는 cmd.exe 사용
            cmd = ['cmd.exe', '/c', 'start', '/B', 'mediamtx.exe', 'mediamtx.yml']
            logger.info("Starting MediaMTX in WSL environment...")
        else:
            # Native Windows
            if sys.platform == "win32":
                cmd = ['start', '/B', 'mediamtx.exe', 'mediamtx.yml']
            else:
                cmd = ['./mediamtx', 'mediamtx.yml']
        
        # 백그라운드로 실행
        if is_wsl:
            # WSL에서는 단순히 백그라운드로 실행
            subprocess.Popen(
                cmd,
                cwd=mediamtx_dir,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif sys.platform == "win32":
            # Native Windows에서 백그라운드 실행
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(
                cmd,
                cwd=mediamtx_dir,
                startupinfo=startupinfo,
                shell=True
            )
        else:
            # Linux/Mac
            subprocess.Popen(
                cmd,
                cwd=mediamtx_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        # 시작 확인
        logger.info("MediaMTX starting...")
        time.sleep(3)
        
        # API 확인
        import requests
        try:
            response = requests.get("http://localhost:9997/v3/paths/list", timeout=2)
            if response.status_code == 200:
                logger.info("✅ MediaMTX is running successfully!")
                logger.info("   SRT: localhost:8890")
                logger.info("   API: localhost:9997")
                return True
        except:
            pass
        
        logger.warning("MediaMTX started but API not responding")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start MediaMTX: {e}")
        return False

if __name__ == "__main__":
    if start_mediamtx_background():
        print("\nMediaMTX is running in the background.")
        print("To stop it, use Task Manager or 'taskkill /F /IM mediamtx.exe'")
    else:
        print("\nFailed to start MediaMTX")
        sys.exit(1)