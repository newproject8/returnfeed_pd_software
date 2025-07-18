# pd_app/core/srt_manager.py
"""
SRT Manager - MediaMTX 서버를 통한 SRT 스트리밍 관리
NDI, 화면 캡처, 웹캠 소스 지원
"""

import subprocess
import threading
import requests
import logging
import time
import json
import sys

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    # Qt가 없는 환경에서도 기본 기능 사용 가능
    class QObject:
        pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass

try:
    import ffmpeg
    FFMPEG_PYTHON_AVAILABLE = True
except ImportError:
    FFMPEG_PYTHON_AVAILABLE = False
    logging.warning("ffmpeg-python not installed. Using subprocess fallback.")

logger = logging.getLogger(__name__)

def check_ffmpeg_availability():
    """시스템에 FFmpeg가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

class MediaMTXClient:
    """MediaMTX 서버 클라이언트"""
    
    def __init__(self, server="returnfeed.net", srt_port=8890, api_port=9997):
        self.server = server
        self.srt_port = srt_port
        self.api_port = api_port
        self.api_url = f"http://{server}:{api_port}"
        self.active_streams = {}
        
    def publish_stream(self, stream_name, username=None, password=None):
        """스트림 퍼블리시를 위한 SRT URL 생성"""
        streamid = f"publish:{stream_name}"
        if username and password:
            streamid += f":{username}:{password}"
        
        srt_url = f"srt://{self.server}:{self.srt_port}?streamid={streamid}&pkt_size=1316"
        return srt_url
        
    def consume_stream(self, stream_name):
        """스트림 소비를 위한 SRT URL 생성"""
        srt_url = f"srt://{self.server}:{self.srt_port}?streamid=read:{stream_name}"
        return srt_url
        
    def get_stream_stats(self):
        """MediaMTX API를 통한 스트림 통계"""
        try:
            response = requests.get(f"{self.api_url}/v3/paths/list", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            logger.error(f"MediaMTX API 요청 실패: {e}")
        return None
        
    def kick_publisher(self, stream_name):
        """특정 스트림의 퍼블리셔 강제 종료"""
        try:
            response = requests.post(f"{self.api_url}/v3/paths/kick/{stream_name}")
            return response.status_code == 200
        except requests.RequestException:
            return False

class SRTStreamMonitor(threading.Thread):
    """SRT 스트림 모니터링 스레드"""
    
    def __init__(self, media_mtx_client, callback):
        super().__init__(daemon=True)
        self.client = media_mtx_client
        self.callback = callback
        self.monitoring = True
        
    def run(self):
        """모니터링 루프"""
        while self.monitoring:
            try:
                stats = self.client.get_stream_stats()
                if stats and self.callback:
                    self.callback(stats)
                time.sleep(5)  # 5초마다 체크
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                time.sleep(10)
                
    def stop(self):
        """모니터링 중지"""
        self.monitoring = False

class SRTManager(QObject):
    """SRT 스트리밍 관리자"""
    
    # 시그널 정의
    stream_status_changed = pyqtSignal(str)
    stream_stats_updated = pyqtSignal(dict)
    stream_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.media_mtx_client = MediaMTXClient()
        self.ffmpeg_process = None
        self.monitor = None
        self.current_stream_name = None
        self.is_streaming = False
        # MediaMTX 서버 설정 속성 추가
        self.media_mtx_server = self.media_mtx_client.server
        self.srt_port = self.media_mtx_client.srt_port
        self.api_port = self.media_mtx_client.api_port
        
    def start_ndi_streaming(self, ndi_source, stream_name, bitrate="2M"):
        """NDI 소스를 SRT로 스트리밍"""
        try:
            if self.is_streaming:
                self.stop_streaming()
                
            srt_url = self.media_mtx_client.publish_stream(stream_name)
            
            if FFMPEG_PYTHON_AVAILABLE:
                # ffmpeg-python 사용
                stream = ffmpeg.input(ndi_source, f='libndi_newtek')
                stream = ffmpeg.output(
                    stream,
                    srt_url,
                    vcodec='libx264',
                    preset='ultrafast',
                    tune='zerolatency',
                    **{
                        'b:v': bitrate,
                        'maxrate': bitrate,
                        'bufsize': f'{int(bitrate[:-1])*2}M',
                        'g': '50'
                    },
                    acodec='aac',
                    **{'b:a': '128k'},
                    f='mpegts'
                )
                
                self.ffmpeg_process = ffmpeg.run_async(
                    stream, 
                    pipe_stdout=True, 
                    pipe_stderr=True
                )
            else:
                # subprocess 사용
                cmd = [
                    'ffmpeg',
                    '-f', 'libndi_newtek',
                    '-i', ndi_source,
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-tune', 'zerolatency',
                    '-b:v', bitrate,
                    '-maxrate', bitrate,
                    '-bufsize', f'{int(bitrate[:-1])*2}M',
                    '-g', '50',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-f', 'mpegts',
                    srt_url
                ]
                
                self.ffmpeg_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
            self.current_stream_name = stream_name
            self.is_streaming = True
            self.stream_status_changed.emit(f"NDI → SRT 스트리밍 시작: {stream_name}")
            
            # 모니터링 시작
            self.start_monitoring()
            
            logger.info(f"NDI 스트리밍 시작: {ndi_source} → {stream_name}")
            
        except Exception as e:
            error_msg = f"NDI 스트리밍 실패: {str(e)}"
            logger.error(error_msg)
            self.stream_error.emit(error_msg)
            
    def start_screen_streaming(self, stream_name, bitrate="1M", fps=30):
        """화면 캡처를 SRT로 스트리밍"""
        try:
            if self.is_streaming:
                self.stop_streaming()
                
            srt_url = self.media_mtx_client.publish_stream(stream_name)
            
            # OS별 화면 캡처 설정
            if sys.platform == "win32":
                input_format = 'gdigrab'
                input_source = 'desktop'
            elif sys.platform == "darwin":
                input_format = 'avfoundation'
                input_source = '1:0'  # 화면:오디오
            else:
                input_format = 'x11grab'
                input_source = ':0.0'
                
            if FFMPEG_PYTHON_AVAILABLE:
                stream = ffmpeg.input(input_source, f=input_format, framerate=fps)
                stream = ffmpeg.output(
                    stream,
                    srt_url,
                    vcodec='libx264',
                    preset='ultrafast',
                    tune='zerolatency',
                    **{'b:v': bitrate},
                    f='mpegts'
                )
                
                self.ffmpeg_process = ffmpeg.run_async(
                    stream,
                    pipe_stdout=True,
                    pipe_stderr=True
                )
            else:
                cmd = [
                    'ffmpeg',
                    '-f', input_format,
                    '-framerate', str(fps),
                    '-i', input_source,
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-tune', 'zerolatency',
                    '-b:v', bitrate,
                    '-f', 'mpegts',
                    srt_url
                ]
                
                self.ffmpeg_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
            self.current_stream_name = stream_name
            self.is_streaming = True
            self.stream_status_changed.emit(f"화면 → SRT 스트리밍 시작: {stream_name}")
            
            # 모니터링 시작
            self.start_monitoring()
            
            logger.info(f"화면 스트리밍 시작: {stream_name}")
            
        except Exception as e:
            error_msg = f"화면 스트리밍 실패: {str(e)}"
            logger.error(error_msg)
            self.stream_error.emit(error_msg)
            
    def stop_streaming(self):
        """스트리밍 중지"""
        try:
            if self.ffmpeg_process:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=5)
                self.ffmpeg_process = None
                
            if self.monitor:
                self.monitor.stop()
                self.monitor = None
                
            self.is_streaming = False
            self.current_stream_name = None
            self.stream_status_changed.emit("스트리밍 중지됨")
            
            logger.info("SRT 스트리밍 중지")
            
        except Exception as e:
            logger.error(f"스트리밍 중지 오류: {e}")
    
    def check_ffmpeg(self):
        """FFmpeg 사용 가능 여부 확인"""
        return check_ffmpeg_availability()
            
    def start_monitoring(self):
        """스트림 모니터링 시작"""
        if not self.monitor:
            self.monitor = SRTStreamMonitor(
                self.media_mtx_client,
                self._on_stream_stats
            )
            self.monitor.start()
            
    def _on_stream_stats(self, stats):
        """스트림 통계 콜백"""
        self.stream_stats_updated.emit(stats)
        
        # 현재 스트림 상태 확인
        if self.current_stream_name:
            active_streams = stats.get('items', [])
            stream_found = any(
                stream.get('name') == self.current_stream_name 
                for stream in active_streams
            )
            
            if not stream_found and self.is_streaming:
                logger.warning(f"스트림 '{self.current_stream_name}'이 서버에서 감지되지 않음")
                
    def get_stream_info(self):
        """현재 스트림 정보 반환"""
        return {
            'is_streaming': self.is_streaming,
            'stream_name': self.current_stream_name,
            'server': self.media_mtx_client.server,
            'srt_port': self.media_mtx_client.srt_port
        }
        
    def generate_stream_key(self, user_id, unique_address):
        """고유한 스트림 키 생성"""
        timestamp = int(time.time())
        return f"{user_id}_{unique_address}_{timestamp}"