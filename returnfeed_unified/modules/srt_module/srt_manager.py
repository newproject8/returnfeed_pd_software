# srt_manager.py
"""
SRT Manager - MediaMTX 서버를 통한 SRT 스트리밍 관리
원본 NDI 소스에서 직접 MediaMTX로 전송
"""

import subprocess
import threading
import requests
import logging
import time
import json
import sys
import os

from PyQt6.QtCore import QObject, pyqtSignal

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
        # Windows에서 ffmpeg.exe도 확인
        commands = ['ffmpeg', 'ffmpeg.exe'] if sys.platform == "win32" else ['ffmpeg']
        
        for cmd in commands:
            try:
                result = subprocess.run(
                    [cmd, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        return False
    except Exception:
        return False


class MediaMTXClient:
    """MediaMTX 서버 클라이언트"""
    
    def __init__(self, server="returnfeed.net", srt_port=8890, api_port=9997):
        self.server = server
        self.srt_port = srt_port
        self.api_port = api_port
        self.api_url = f"http://{server}:{api_port}"
        
    def publish_stream(self, stream_name, username=None, password=None):
        """스트림 퍼블리시를 위한 SRT URL 생성"""
        streamid = f"publish:{stream_name}"
        if username and password:
            streamid += f":{username}:{password}"
        
        srt_url = f"srt://{self.server}:{self.srt_port}?streamid={streamid}&pkt_size=1316"
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


class SRTStreamMonitor(threading.Thread):
    """SRT 스트림 모니터링 스레드"""
    
    def __init__(self, ffmpeg_process, callback):
        super().__init__(daemon=True)
        self.ffmpeg_process = ffmpeg_process
        self.callback = callback
        self.monitoring = True
        
    def run(self):
        """FFmpeg 출력 모니터링"""
        while self.monitoring and self.ffmpeg_process:
            try:
                if self.ffmpeg_process.stderr:
                    line = self.ffmpeg_process.stderr.readline()
                    if line:
                        # FFmpeg 통계 파싱 (bitrate, fps 등)
                        if self.callback:
                            self.callback(line.decode('utf-8', errors='ignore'))
                    else:
                        # 프로세스 종료
                        break
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                break
                
    def stop(self):
        """모니터링 중지"""
        self.monitoring = False


class SRTManager(QObject):
    """SRT 스트리밍 관리자 - 원본 NDI에서 직접 전송"""
    
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
        self.media_mtx_server = self.media_mtx_client.server
        self.srt_port = self.media_mtx_client.srt_port
        self.api_port = self.media_mtx_client.api_port
        self.current_stats = {
            'bitrate': '0',
            'fps': '0',
            'time': '00:00:00'
        }
        
    def update_server_config(self, server: str, port: int):
        """MediaMTX 서버 설정 업데이트"""
        self.media_mtx_server = server
        self.srt_port = port
        self.media_mtx_client = MediaMTXClient(server, port, self.api_port)
        
    def start_ndi_streaming(self, ndi_source: str, stream_name: str, bitrate: str = "2M", fps: int = 30):
        """NDI 소스를 SRT로 스트리밍 (화면 캡처 방식)"""
        try:
            if self.is_streaming:
                self.stop_streaming()
                
            srt_url = self.media_mtx_client.publish_stream(stream_name)
            
            # Windows에서 화면 캡처 사용 (NDI 프리뷰가 표시되는 영역)
            # 임시로 전체 화면 캡처 사용
            logger.warning("NDI direct input not supported, using screen capture instead")
            
            # FFmpeg 명령어 구성 (화면 캡처)
            if sys.platform == "win32":
                cmd = [
                    'ffmpeg',
                    '-f', 'gdigrab',        # Windows 화면 캡처
                    '-framerate', str(fps), # 프레임 레이트
                    '-i', 'desktop',        # 전체 화면 캡처
                    '-c:v', 'libx264',      # H.264 비디오 코덱
                    '-preset', 'ultrafast', # 최소 지연 프리셋
                    '-tune', 'zerolatency', # 제로 레이턴시 튜닝
                    '-b:v', bitrate,        # 비디오 비트레이트
                    '-maxrate', bitrate,    # 최대 비트레이트
                    '-bufsize', f'{int(bitrate[:-1])*2}M',  # 버퍼 크기
                    '-g', str(fps * 2),     # GOP 크기 (2초)
                    '-f', 'mpegts',         # MPEG-TS 컨테이너
                    srt_url                 # SRT 출력 URL
                ]
            else:
                # Linux/Mac은 기존 screen_streaming 메서드 사용
                self.start_screen_streaming(stream_name, bitrate, fps)
                return
            
            # 로그 출력
            logger.info(f"Starting screen capture to SRT streaming: {stream_name}")
            logger.warning(f"Note: Capturing entire screen, not specific NDI source '{ndi_source}'")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # FFmpeg 프로세스 시작
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            self.current_stream_name = stream_name
            self.is_streaming = True
            self._streaming_confirmed = False  # 스트리밍 확인 플래그 초기화
            self.stream_status_changed.emit(f"화면 → 리턴피드 스트림 시작: {stream_name}")
            
            # 모니터링 시작
            self.start_monitoring()
            
            # 스트리밍 시작 확인 (1초 대기)
            time.sleep(1)
            if self.ffmpeg_process.poll() is not None:
                # 프로세스가 종료됨
                stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                stdout = self.ffmpeg_process.stdout.read().decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg stderr: {stderr}")
                logger.error(f"FFmpeg stdout: {stdout}")
                raise Exception(f"FFmpeg 프로세스가 시작되지 않았습니다: {stderr}")
            
            # MediaMTX API로 스트림 상태 확인
            if self._verify_stream_active(stream_name):
                logger.info(f"✅ Stream '{stream_name}' is active on MediaMTX")
            else:
                logger.warning(f"⚠️  Stream '{stream_name}' not detected on MediaMTX yet")
            
        except Exception as e:
            error_msg = f"NDI 스트리밍 실패: {str(e)}"
            logger.error(error_msg)
            self.stream_error.emit(error_msg)
            self.is_streaming = False
            
    def start_screen_streaming(self, stream_name: str, bitrate: str = "1M", fps: int = 30):
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
                
            cmd = [
                'ffmpeg',
                '-f', input_format,
                '-framerate', str(fps),
                '-i', input_source,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', f'{int(bitrate[:-1])*2}M',
                '-g', str(fps * 2),
                '-f', 'mpegts',
                srt_url
            ]
            
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            self.current_stream_name = stream_name
            self.is_streaming = True
            self._streaming_confirmed = False  # 스트리밍 확인 플래그 초기화
            self.stream_status_changed.emit(f"화면 → 리턴피드 스트림 시작: {stream_name}")
            
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
            if self.monitor:
                self.monitor.stop()
                self.monitor = None
                
            if self.ffmpeg_process:
                # 프로세스가 아직 실행 중인지 확인
                if self.ffmpeg_process.poll() is None:
                    # 정상 종료 시도
                    try:
                        if self.ffmpeg_process.stdin and not self.ffmpeg_process.stdin.closed:
                            self.ffmpeg_process.stdin.write(b'q')
                            self.ffmpeg_process.stdin.flush()
                    except (OSError, ValueError, BrokenPipeError) as e:
                        logger.debug(f"Could not send 'q' to ffmpeg: {e}")
                    
                    # 잠시 대기
                    try:
                        self.ffmpeg_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # 강제 종료
                        logger.info("FFmpeg did not stop gracefully, terminating...")
                        self.ffmpeg_process.terminate()
                        try:
                            self.ffmpeg_process.wait(timeout=1)
                        except subprocess.TimeoutExpired:
                            logger.warning("FFmpeg did not terminate, killing...")
                            self.ffmpeg_process.kill()
                            self.ffmpeg_process.wait()
                
                self.ffmpeg_process = None
                
            self.is_streaming = False
            self._streaming_confirmed = False  # 스트리밍 확인 플래그 초기화
            self.current_stream_name = None
            self.current_stats = {'bitrate': '0', 'fps': '0', 'time': '00:00:00'}
            self.stream_status_changed.emit("스트리밍 중지됨")
            
            logger.info("SRT 스트리밍 중지")
            
        except Exception as e:
            logger.error(f"스트리밍 중지 오류: {e}")
    
    def check_ffmpeg(self):
        """FFmpeg 사용 가능 여부 확인"""
        return check_ffmpeg_availability()
            
    def start_monitoring(self):
        """스트림 모니터링 시작"""
        if not self.monitor and self.ffmpeg_process:
            self.monitor = SRTStreamMonitor(
                self.ffmpeg_process,
                self._parse_ffmpeg_output
            )
            self.monitor.start()
            
    def _parse_ffmpeg_output(self, line: str):
        """FFmpeg 출력 파싱"""
        try:
            # 디버그 로깅 (주요 메시지만)
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'failed']):
                logger.warning(f"FFmpeg: {line.strip()}")
            elif 'output' in line.lower() and 'srt://' in line:
                logger.info(f"FFmpeg: {line.strip()}")
            
            # 통계 정보 추출
            if 'bitrate=' in line and 'fps=' in line:
                # FFmpeg 진행 상태 라인 파싱
                import re
                
                # bitrate 추출
                bitrate_match = re.search(r'bitrate=\s*(\S+)', line)
                if bitrate_match:
                    self.current_stats['bitrate'] = bitrate_match.group(1)
                
                # fps 추출
                fps_match = re.search(r'fps=\s*(\S+)', line)
                if fps_match:
                    self.current_stats['fps'] = fps_match.group(1)
                
                # time 추출
                time_match = re.search(r'time=\s*(\S+)', line)
                if time_match:
                    self.current_stats['time'] = time_match.group(1)
                
                # 상태 업데이트
                self.stream_stats_updated.emit(self.current_stats)
                
                # 스트리밍 활성 상태 표시
                if not hasattr(self, '_streaming_confirmed'):
                    self._streaming_confirmed = True
                    self.stream_status_changed.emit("✅ 스트리밍 활성")
                    logger.info(f"✅ Streaming confirmed - bitrate: {self.current_stats['bitrate']}, fps: {self.current_stats['fps']}")
                
        except Exception as e:
            logger.debug(f"Failed to parse FFmpeg output: {e}")
        
    def get_stream_info(self):
        """현재 스트림 정보 반환"""
        return {
            'is_streaming': self.is_streaming,
            'stream_name': self.current_stream_name,
            'server': self.media_mtx_server,
            'srt_port': self.srt_port,
            'stats': self.current_stats
        }
        
    def generate_stream_key(self, prefix: str = "stream"):
        """고유한 스트림 키 생성"""
        timestamp = int(time.time())
        return f"{prefix}_{timestamp}"
    
    def _verify_stream_active(self, stream_name: str) -> bool:
        """스트림이 MediaMTX에서 활성화되었는지 확인"""
        try:
            response = requests.get(
                f"http://{self.media_mtx_server}:{self.api_port}/v3/paths/list",
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get('items', []):
                    if item['name'] == stream_name:
                        return True
            return False
        except Exception as e:
            logger.debug(f"Could not verify stream status: {e}")
            return False