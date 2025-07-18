#!/usr/bin/env python3
"""
MediaMTX 상태 확인 도구
"""
import requests
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_port(port):
    """포트 사용 확인"""
    try:
        result = subprocess.run(
            ['netstat', '-an'], 
            capture_output=True, 
            text=True,
            shell=True
        )
        return f":{port}" in result.stdout
    except:
        return False

def check_mediamtx_status():
    """MediaMTX 상태 확인"""
    logger.info("=== MediaMTX Status Check ===\n")
    
    # 1. 포트 확인
    srt_port_open = check_port(8890)
    api_port_open = check_port(9997)
    
    logger.info(f"📡 Port Status:")
    logger.info(f"   SRT (8890): {'✅ Open' if srt_port_open else '❌ Closed'}")
    logger.info(f"   API (9997): {'✅ Open' if api_port_open else '❌ Closed'}")
    logger.info("")
    
    # 2. API 확인
    try:
        response = requests.get("http://localhost:9997/v3/config/get", timeout=2)
        if response.status_code == 200:
            logger.info("✅ MediaMTX API is responding")
            
            # 활성 스트림 확인
            paths_response = requests.get("http://localhost:9997/v3/paths/list", timeout=2)
            if paths_response.status_code == 200:
                data = paths_response.json()
                if data.get('items'):
                    logger.info(f"\n📺 Active streams: {len(data['items'])}")
                    for item in data['items']:
                        logger.info(f"   - {item['name']}")
                else:
                    logger.info("\n📺 No active streams")
        else:
            logger.error(f"❌ API returned status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to MediaMTX API")
        logger.info("   Make sure MediaMTX is running")
    except Exception as e:
        logger.error(f"❌ API error: {e}")
    
    # 3. 프로세스 확인
    logger.info("\n🔍 Checking MediaMTX process...")
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq mediamtx.exe'],
            capture_output=True,
            text=True,
            shell=True
        )
        if "mediamtx.exe" in result.stdout:
            logger.info("✅ MediaMTX process is running")
        else:
            logger.error("❌ MediaMTX process not found")
    except:
        logger.warning("⚠️  Could not check process status")
    
    logger.info("\n" + "="*30)

if __name__ == "__main__":
    check_mediamtx_status()