# pd_app/utils/helpers.py
"""
Helper utilities
"""

import os
import sys
import platform

def get_platform_info():
    """플랫폼 정보 반환"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': sys.version
    }

def ensure_directory(path):
    """디렉토리 생성 확인"""
    os.makedirs(path, exist_ok=True)
    return path

def format_bytes(bytes_value):
    """바이트를 읽기 쉬운 형식으로 변환"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_duration(seconds):
    """초를 읽기 쉬운 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def truncate_text(text, max_length=20):
    """텍스트 자르기"""
    if not text:
        return ""
    return text[:max_length] if len(text) <= max_length else text[:max_length-3] + "..."