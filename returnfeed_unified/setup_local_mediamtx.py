#!/usr/bin/env python3
"""
로컬 MediaMTX 서버 설정 및 테스트 스크립트
"""
import os
import sys
import subprocess
import time
import requests
import platform
import zipfile
import tarfile
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEDIAMTX_VERSION = "v1.4.0"
MEDIAMTX_DIR = "mediamtx_local"

def download_mediamtx():
    """MediaMTX 바이너리 다운로드"""
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # 플랫폼별 파일명 설정
    if system == "windows":
        if "64" in arch:
            filename = "mediamtx_v1.4.0_windows_amd64.zip"
        else:
            filename = "mediamtx_v1.4.0_windows_386.zip"
        ext = "zip"
    elif system == "darwin":  # macOS
        filename = "mediamtx_v1.4.0_darwin_amd64.tar.gz"
        ext = "tar.gz"
    else:  # Linux
        if "arm" in arch:
            filename = "mediamtx_v1.4.0_linux_arm64v8.tar.gz"
        else:
            filename = "mediamtx_v1.4.0_linux_amd64.tar.gz"
        ext = "tar.gz"
    
    download_url = f"https://github.com/bluenviron/mediamtx/releases/download/{MEDIAMTX_VERSION}/{filename}"
    
    logger.info(f"Downloading MediaMTX from {download_url}")
    
    # 디렉토리 생성
    os.makedirs(MEDIAMTX_DIR, exist_ok=True)
    
    # 다운로드
    local_file = os.path.join(MEDIAMTX_DIR, filename)
    if not os.path.exists(local_file):
        try:
            urllib.request.urlretrieve(download_url, local_file)
            logger.info(f"Downloaded to {local_file}")
        except Exception as e:
            logger.error(f"Download failed: {e}")
            logger.error("Please download manually from https://github.com/bluenviron/mediamtx/releases")
            return False
    
    # 압축 해제
    try:
        if ext == "zip":
            with zipfile.ZipFile(local_file, 'r') as zip_ref:
                zip_ref.extractall(MEDIAMTX_DIR)
        else:
            with tarfile.open(local_file, 'r:gz') as tar_ref:
                tar_ref.extractall(MEDIAMTX_DIR)
        logger.info("Extracted successfully")
        
        # 실행 권한 부여 (Linux/macOS)
        if system != "windows":
            binary_path = os.path.join(MEDIAMTX_DIR, "mediamtx")
            os.chmod(binary_path, 0o755)
            
        return True
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False

def create_config():
    """MediaMTX 설정 파일 생성"""
    config_content = """# MediaMTX 로컬 테스트 설정

# 로그 레벨
logLevel: info

# SRT 서버 활성화
srt: yes

# SRT 서버 설정
srtAddress: :8890

# API 설정
api: yes
apiAddress: :9997

# 경로 설정
paths:
  all:
    # 모든 스트림 허용
    source: publisher
    # SRT 암호화 패스프레이즈 (빈 값 = 암호화 없음)
    srtReadPassphrase:
    srtPublishPassphrase:
"""
    
    config_path = os.path.join(MEDIAMTX_DIR, "mediamtx.yml")
    with open(config_path, 'w') as f:
        f.write(config_content)
    logger.info(f"Created config file: {config_path}")
    return config_path

def start_mediamtx():
    """MediaMTX 서버 시작"""
    system = platform.system().lower()
    
    if system == "windows":
        binary_name = "mediamtx.exe"
    else:
        binary_name = "mediamtx"
    
    binary_path = os.path.join(MEDIAMTX_DIR, binary_name)
    config_path = os.path.join(MEDIAMTX_DIR, "mediamtx.yml")
    
    if not os.path.exists(binary_path):
        logger.error(f"MediaMTX binary not found at {binary_path}")
        logger.info("Attempting to download...")
        if not download_mediamtx():
            return None
    
    # 설정 파일 생성
    if not os.path.exists(config_path):
        create_config()
    
    # 서버 시작
    logger.info(f"Starting MediaMTX server...")
    try:
        # WSL에서 Windows 실행 파일을 실행하는 경우 cmd.exe 사용
        if os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
            # WSL 환경
            logger.info("Detected WSL environment, using cmd.exe to run MediaMTX")
            # Windows 실행 파일 경로 확인
            windows_binary_path = os.path.join(MEDIAMTX_DIR, "mediamtx.exe")
            if os.path.exists(windows_binary_path):
                process = subprocess.Popen(
                    ['cmd.exe', '/c', 'mediamtx.exe', 'mediamtx.yml'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=MEDIAMTX_DIR
                )
            else:
                logger.error(f"Windows binary not found at {windows_binary_path}")
                return None
        else:
            # Native Windows 또는 다른 환경
            process = subprocess.Popen(
                [binary_path, config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=MEDIAMTX_DIR
            )
        
        # 시작 대기
        time.sleep(2)
        
        # 프로세스 확인
        if process.poll() is not None:
            stderr = process.stderr.read().decode('utf-8', errors='ignore')
            logger.error(f"MediaMTX failed to start: {stderr}")
            return None
        
        # API 확인
        try:
            response = requests.get("http://localhost:9997/v3/config/get", timeout=2)
            if response.status_code == 200:
                logger.info("✅ MediaMTX server is running!")
                logger.info("   SRT port: 8890")
                logger.info("   API port: 9997")
                return process
        except:
            pass
        
        logger.warning("Server started but API not responding yet")
        return process
        
    except Exception as e:
        logger.error(f"Failed to start MediaMTX: {e}")
        return None

def test_srt_stream():
    """간단한 SRT 스트림 테스트"""
    logger.info("\n=== SRT Stream Test ===")
    logger.info("You can test SRT streaming with:")
    logger.info("ffmpeg -re -f lavfi -i testsrc=size=1920x1080:rate=30 -f lavfi -i sine -c:v libx264 -preset ultrafast -b:v 2M -c:a aac -f mpegts 'srt://localhost:8890?streamid=publish:test'")
    logger.info("\nView stream at:")
    logger.info("ffplay 'srt://localhost:8890?streamid=read:test'")
    logger.info("VLC: srt://localhost:8890?streamid=read:test")

def main():
    """메인 함수"""
    print("=== MediaMTX Local Server Setup ===\n")
    
    # 이미 실행 중인지 확인
    try:
        response = requests.get("http://localhost:9997/v3/config/get", timeout=1)
        if response.status_code == 200:
            logger.info("✅ MediaMTX is already running on localhost:8890")
            test_srt_stream()
            return
    except:
        pass
    
    # 서버 시작
    process = start_mediamtx()
    if process:
        logger.info("\n✅ MediaMTX server is ready for local testing!")
        test_srt_stream()
        
        logger.info("\nPress Ctrl+C to stop the server...")
        try:
            process.wait()
        except KeyboardInterrupt:
            logger.info("\nStopping MediaMTX server...")
            process.terminate()
            process.wait()
            logger.info("Server stopped.")
    else:
        logger.error("Failed to start MediaMTX server")
        logger.info("\nAlternative: Use Docker")
        logger.info("docker run --rm -it -p 8890:8890/udp -p 9997:9997 bluenviron/mediamtx:latest")

if __name__ == "__main__":
    main()