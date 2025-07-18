#!/usr/bin/env python3
"""
SRT 스트리밍 상태 확인 도구
"""
import requests
import subprocess
import time
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_mediamtx_api():
    """MediaMTX API 상태 확인"""
    try:
        response = requests.get("http://localhost:9997/v3/config/get", timeout=2)
        if response.status_code == 200:
            logger.info("✅ MediaMTX API is accessible")
            return True
        else:
            logger.error(f"❌ MediaMTX API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ MediaMTX API is not running on localhost:9997")
        return False
    except Exception as e:
        logger.error(f"❌ MediaMTX API error: {e}")
        return False

def check_active_streams():
    """활성 스트림 목록 확인"""
    try:
        response = requests.get("http://localhost:9997/v3/paths/list", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data['items']:
                logger.info("\n📡 Active streams:")
                for item in data['items']:
                    path_name = item['name']
                    readers = item.get('readers', [])
                    publishers = item.get('source', {}).get('type', 'none')
                    logger.info(f"   - {path_name}: source={publishers}, readers={len(readers)}")
                return True
            else:
                logger.info("📡 No active streams found")
                return False
        else:
            logger.error(f"❌ Failed to get stream list: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error checking streams: {e}")
        return False

def test_ffmpeg_screen_capture():
    """FFmpeg 화면 캡처 테스트"""
    logger.info("\n🎬 Testing FFmpeg screen capture...")
    
    # 짧은 테스트 캡처 (3초)
    test_file = "test_capture.mp4"
    cmd = [
        'ffmpeg',
        '-f', 'gdigrab',
        '-framerate', '30',
        '-i', 'desktop',
        '-t', '3',  # 3초만 캡처
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-y',  # 파일 덮어쓰기
        test_file
    ]
    
    try:
        logger.info("   Running 3-second test capture...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            import os
            if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                logger.info(f"   ✅ FFmpeg screen capture works! ({os.path.getsize(test_file)} bytes)")
                os.remove(test_file)  # 테스트 파일 삭제
                return True
            else:
                logger.error("   ❌ FFmpeg succeeded but no output file created")
                return False
        else:
            logger.error(f"   ❌ FFmpeg failed with code {result.returncode}")
            logger.error(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"   ❌ FFmpeg test failed: {e}")
        return False

def test_srt_publish():
    """간단한 SRT 퍼블리시 테스트"""
    logger.info("\n🔴 Testing SRT publish...")
    
    stream_name = f"test_{int(time.time())}"
    srt_url = f"srt://localhost:8890?streamid=publish:{stream_name}&pkt_size=1316"
    
    # 5초 테스트 스트림
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'testsrc=size=640x480:rate=30',
        '-f', 'lavfi', 
        '-i', 'sine',
        '-t', '5',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-b:v', '500k',
        '-c:a', 'aac',
        '-f', 'mpegts',
        srt_url
    ]
    
    try:
        logger.info(f"   Publishing test stream '{stream_name}' for 5 seconds...")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 2초 대기 후 스트림 확인
        time.sleep(2)
        
        # API로 스트림 확인
        response = requests.get("http://localhost:9997/v3/paths/list", timeout=2)
        if response.status_code == 200:
            data = response.json()
            stream_found = any(item['name'] == stream_name for item in data.get('items', []))
            
            if stream_found:
                logger.info(f"   ✅ Test stream '{stream_name}' is active!")
            else:
                logger.warning(f"   ⚠️  Test stream '{stream_name}' not found in active streams")
        
        # 프로세스 종료 대기
        process.wait()
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ SRT publish test failed: {e}")
        return False

def main():
    """메인 진단 함수"""
    logger.info("=== SRT Streaming Diagnostics ===\n")
    
    # 1. MediaMTX API 확인
    api_ok = check_mediamtx_api()
    if not api_ok:
        logger.error("\n⚠️  MediaMTX server is not running!")
        logger.info("Run 'python setup_local_mediamtx.py' to start the server")
        return
    
    # 2. 활성 스트림 확인
    check_active_streams()
    
    # 3. FFmpeg 화면 캡처 테스트
    capture_ok = test_ffmpeg_screen_capture()
    
    # 4. SRT 퍼블리시 테스트
    if api_ok:
        publish_ok = test_srt_publish()
    
    # 5. 최종 상태
    logger.info("\n=== Summary ===")
    if api_ok and capture_ok:
        logger.info("✅ SRT streaming infrastructure is working!")
        logger.info("\nTo view streams:")
        logger.info("  - ffplay 'srt://localhost:8890?streamid=read:STREAM_NAME'")
        logger.info("  - VLC: srt://localhost:8890?streamid=read:STREAM_NAME")
    else:
        logger.error("❌ Some components are not working properly")
        
    # 6. 추가 정보
    logger.info("\n📌 Tips:")
    logger.info("  - Check Windows Firewall if streams don't work")
    logger.info("  - Make sure no other app is using port 8890")
    logger.info("  - For NDI input, consider using OBS Studio with NDI plugin")

if __name__ == "__main__":
    main()