#!/usr/bin/env python3
"""
FFmpeg NDI 지원 확인 스크립트
"""
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ffmpeg_ndi_support():
    """FFmpeg의 NDI 지원 확인"""
    print("=== FFmpeg NDI Support Check ===\n")
    
    # 1. FFmpeg 버전 확인
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        print("FFmpeg Version:")
        print(result.stdout.split('\n')[0])
        print()
    except Exception as e:
        print(f"FFmpeg not found: {e}")
        return
    
    # 2. 입력 포맷 확인
    print("Checking input formats for NDI support...")
    try:
        result = subprocess.run(['ffmpeg', '-formats'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        ndi_formats = [line for line in lines if 'ndi' in line.lower()]
        
        if ndi_formats:
            print("✅ NDI formats found:")
            for fmt in ndi_formats:
                print(f"  {fmt}")
        else:
            print("❌ No NDI formats found in standard FFmpeg")
            print("\nChecking protocols instead...")
            
            # 3. 프로토콜 확인
            result = subprocess.run(['ffmpeg', '-protocols'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            ndi_protocols = [line for line in lines if 'ndi' in line.lower()]
            
            if ndi_protocols:
                print("✅ NDI protocols found:")
                for proto in ndi_protocols:
                    print(f"  {proto}")
            else:
                print("❌ No NDI protocols found")
        
        print()
    except Exception as e:
        print(f"Error checking formats: {e}")
    
    # 4. 디바이스 확인
    print("Checking available devices...")
    try:
        # Windows: dshow devices
        if subprocess.run(['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'], 
                         capture_output=True).returncode == 1:
            result = subprocess.run(['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy'], 
                                  capture_output=True, text=True, stderr=subprocess.STDOUT)
            print("\nDirectShow devices:")
            print(result.stdout)
    except:
        pass
    
    print("\n=== Recommendations ===")
    print("Since standard FFmpeg doesn't support NDI input directly, consider:")
    print("1. Use NDI Virtual Input to create a virtual webcam from NDI source")
    print("2. Use OBS Studio with NDI plugin to capture and stream")
    print("3. Use screen capture of NDI Monitor application")
    print("4. Build FFmpeg with NDI SDK support (advanced)")

if __name__ == "__main__":
    check_ffmpeg_ndi_support()