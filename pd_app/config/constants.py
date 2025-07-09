# pd_app/config/constants.py
"""
Application constants
"""

# 애플리케이션 정보
APP_NAME = "PD 통합 소프트웨어"
APP_VERSION = "1.0.0"
APP_AUTHOR = "PD Software Team"

# 서버 설정
DEFAULT_WEBSOCKET_URL = "ws://returnfeed.net:8765"  # 릴레이 서버 주소
DEFAULT_MEDIA_MTX_SERVER = "returnfeed.net"
DEFAULT_MEDIA_MTX_SRT_PORT = 8890
DEFAULT_MEDIA_MTX_API_PORT = 9997

# vMix 기본 설정
DEFAULT_VMIX_IP = "127.0.0.1"
DEFAULT_VMIX_HTTP_PORT = 8088
DEFAULT_VMIX_TCP_PORT = 8099

# Tally 색상
COLOR_OFF = "#333333"
COLOR_PVW_NORMAL = "#00aa00"
COLOR_PGM_NORMAL = "#aa0000"
COLOR_TEXT = "#ffffff"

# 타임아웃 설정
WEBSOCKET_PING_INTERVAL = 20
WEBSOCKET_PING_TIMEOUT = 20
SERVER_TIMEOUT = 90
VMIX_TIMEOUT = 5

# 스트리밍 기본 설정
DEFAULT_BITRATE = "2M"
DEFAULT_FPS = 30
DEFAULT_PRESET = "ultrafast"
DEFAULT_TUNE = "zerolatency"

# 파일 경로
CONFIG_DIR = "config"
LOG_DIR = "logs"
AUTH_FILE = "config/auth.json"
SETTINGS_FILE = "config/settings.json"