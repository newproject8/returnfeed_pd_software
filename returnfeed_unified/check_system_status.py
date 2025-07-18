#!/usr/bin/env python3
"""
ReturnFeed 시스템 상태 종합 점검
"""
import subprocess
import requests
import json
import os
import socket
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_port(port, host='localhost'):
    """포트 열림 확인"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_mediamtx():
    """MediaMTX 상태 확인"""
    srt_ok = check_port(8890)
    api_ok = check_port(9997)
    
    status = "❌ Not Running"
    if srt_ok and api_ok:
        try:
            resp = requests.get("http://localhost:9997/v3/config/get", timeout=1)
            if resp.status_code == 200:
                status = "✅ Running"
        except:
            status = "⚠️  Partial"
    
    return f"MediaMTX: {status} (SRT: {srt_ok}, API: {api_ok})"

def check_vmix():
    """vMix 상태 확인"""
    tcp_ok = check_port(8099)
    http_ok = check_port(8088)
    
    if tcp_ok and http_ok:
        return "vMix: ✅ Running"
    elif tcp_ok or http_ok:
        return f"vMix: ⚠️  Partial (TCP: {tcp_ok}, HTTP: {http_ok})"
    else:
        return "vMix: ❌ Not Running"

def check_settings():
    """설정 파일 확인"""
    try:
        with open('config/settings.json', 'r') as f:
            settings = json.load(f)
        
        srt_server = settings.get('SRT', {}).get('media_mtx_server', 'unknown')
        vmix_ip = settings.get('vMixTally', {}).get('vmix_ip', 'unknown')
        
        if srt_server == 'localhost' and vmix_ip == '127.0.0.1':
            return "Settings: ✅ Local Mode"
        else:
            return f"Settings: ⚠️  Mixed (SRT: {srt_server}, vMix: {vmix_ip})"
    except Exception as e:
        return f"Settings: ❌ Error - {e}"

def check_ffmpeg():
    """FFmpeg 설치 확인"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode == 0:
            return "FFmpeg: ✅ Installed"
        else:
            return "FFmpeg: ❌ Not Found"
    except:
        return "FFmpeg: ❌ Not Found"

def check_ndi():
    """NDI SDK 확인"""
    ndi_path = r"C:\Program Files\NDI\NDI 6 SDK"
    if os.path.exists(ndi_path):
        return "NDI SDK: ✅ Installed"
    else:
        return "NDI SDK: ⚠️  Not Found (Optional)"

def main():
    """메인 상태 점검"""
    logger.info(check_mediamtx())
    logger.info(check_vmix())
    logger.info(check_settings())
    logger.info(check_ffmpeg())
    logger.info(check_ndi())
    
    logger.info("\n📌 Quick Actions:")
    
    if "❌" in check_mediamtx():
        logger.info("   - Run: START_MEDIAMTX.bat")
    
    if "❌" in check_vmix():
        logger.info("   - Start vMix application")
    
    if "Mixed" in check_settings():
        logger.info("   - Run: switch_server.bat → Choose Local")

if __name__ == "__main__":
    main()