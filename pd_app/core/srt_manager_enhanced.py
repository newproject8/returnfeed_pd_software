# pd_app/core/srt_manager_enhanced.py
"""
Enhanced SRT Manager - Professional Broadcasting Support (0.1-10 Mbps)
H.264 codec with flexible bitrate and advanced settings
"""

import subprocess
import threading
import requests
import logging
import time
import json
import sys
import os

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    class QObject:
        pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass

logger = logging.getLogger(__name__)

class EnhancedSRTManager(QObject):
    """Enhanced SRT Streaming Manager for Professional Broadcasting"""
    
    # Signals
    stream_status_changed = pyqtSignal(str)
    stream_stats_updated = pyqtSignal(dict)
    stream_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ffmpeg_process = None
        self.monitor_thread = None
        self.current_stream_name = None
        self.is_streaming = False
        self.stream_stats = {}
        
        # MediaMTX settings
        self.media_mtx_server = "returnfeed.net"
        self.srt_port = 8890
        self.api_port = 9997
        
    def start_ndi_streaming_enhanced(self, ndi_source, stream_name, params):
        """Start NDI streaming with professional parameters"""
        try:
            if self.is_streaming:
                self.stop_streaming()
                
            # Build SRT URL with authentication
            srt_url = f"srt://{self.media_mtx_server}:{self.srt_port}?streamid={stream_name}"
            
            # Build FFmpeg command with professional settings
            cmd = [
                'ffmpeg',
                '-f', 'libndi_newtek',
                '-i', ndi_source,
                
                # Video encoding - H.264
                '-c:v', 'libx264',
                '-preset', params.get('h264_preset', 'ultrafast'),
                '-profile:v', params.get('h264_profile', 'main'),
                '-tune', 'zerolatency',  # Critical for low latency
                
                # Bitrate settings
                '-b:v', params.get('bitrate', '2M'),
                '-maxrate', params.get('bitrate', '2M'),
                '-bufsize', self._calculate_buffer_size(params.get('bitrate', '2M')),
                
                # Keyframe interval (GOP size)
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                
                # Frame rate (if needed to override)
                '-r', str(params.get('fps', 30)),
                
                # Audio encoding - AAC
                '-c:a', 'aac',
                '-b:a', params.get('audio_bitrate', '128k'),
                '-ar', '48000',  # 48kHz sample rate
                '-ac', '2',      # Stereo
                
                # SRT specific settings
                '-f', 'mpegts',
                
                # Output with latency parameter
                f"{srt_url}&latency={params.get('srt_latency', 120)}"
            ]
            
            # Add advanced x264 parameters for quality/performance balance
            x264_params = []
            
            # Rate control for consistent quality
            x264_params.append('nal-hrd=cbr')  # CBR for consistent bitrate
            x264_params.append('no-mbtree')    # Disable for lower latency
            
            # Performance optimizations
            if params.get('h264_preset') == 'ultrafast':
                x264_params.append('threads=auto')
                x264_params.append('sliced-threads')
                
            if x264_params:
                cmd.extend(['-x264-params', ':'.join(x264_params)])
            
            logger.info(f"Starting NDI stream with command: {' '.join(cmd)}")
            
            # Start FFmpeg process
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.current_stream_name = stream_name
            self.is_streaming = True
            self.stream_status_changed.emit(f"NDI → SRT Streaming: {stream_name}")
            
            # Start monitoring thread
            self._start_monitoring()
            
            # Start stats collection thread
            self._start_stats_thread()
            
        except Exception as e:
            error_msg = f"NDI streaming failed: {str(e)}"
            logger.error(error_msg)
            self.stream_error.emit(error_msg)
            
    def start_screen_streaming_enhanced(self, stream_name, params):
        """Start screen capture streaming with professional parameters"""
        try:
            if self.is_streaming:
                self.stop_streaming()
                
            # Build SRT URL
            srt_url = f"srt://{self.media_mtx_server}:{self.srt_port}?streamid={stream_name}"
            
            # OS-specific screen capture
            if sys.platform == "win32":
                input_format = 'gdigrab'
                input_source = 'desktop'
                # Windows specific optimizations
                input_params = [
                    '-framerate', str(params.get('fps', 30)),
                    '-offset_x', '0',
                    '-offset_y', '0'
                ]
            elif sys.platform == "darwin":
                input_format = 'avfoundation'
                input_source = '1:0'  # Screen:Audio
                input_params = [
                    '-framerate', str(params.get('fps', 30)),
                    '-capture_cursor', '1',
                    '-capture_mouse_clicks', '1'
                ]
            else:  # Linux
                input_format = 'x11grab'
                input_source = ':0.0'
                input_params = [
                    '-framerate', str(params.get('fps', 30)),
                    '-draw_mouse', '1'
                ]
                
            # Build FFmpeg command
            cmd = ['ffmpeg']
            cmd.extend(input_params)
            cmd.extend([
                '-f', input_format,
                '-i', input_source,
                
                # Video encoding - H.264
                '-c:v', 'libx264',
                '-preset', params.get('h264_preset', 'ultrafast'),
                '-profile:v', params.get('h264_profile', 'main'),
                '-tune', 'zerolatency',
                
                # Bitrate settings
                '-b:v', params.get('bitrate', '2M'),
                '-maxrate', params.get('bitrate', '2M'),
                '-bufsize', self._calculate_buffer_size(params.get('bitrate', '2M')),
                
                # Keyframe interval
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                
                # Pixel format for compatibility
                '-pix_fmt', 'yuv420p',
                
                # Audio (if available)
                '-c:a', 'aac',
                '-b:a', params.get('audio_bitrate', '128k'),
                
                # Output format
                '-f', 'mpegts',
                
                # SRT output with latency
                f"{srt_url}&latency={params.get('srt_latency', 120)}"
            ])
            
            logger.info(f"Starting screen capture with: {' '.join(cmd)}")
            
            # Start FFmpeg process
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.current_stream_name = stream_name
            self.is_streaming = True
            self.stream_status_changed.emit(f"Screen → SRT Streaming: {stream_name}")
            
            # Start monitoring
            self._start_monitoring()
            self._start_stats_thread()
            
        except Exception as e:
            error_msg = f"Screen streaming failed: {str(e)}"
            logger.error(error_msg)
            self.stream_error.emit(error_msg)
            
    def _calculate_buffer_size(self, bitrate):
        """Calculate appropriate buffer size based on bitrate"""
        # Extract numeric value from bitrate string
        if bitrate.endswith('k'):
            value = float(bitrate[:-1]) / 1000  # Convert to Mbps
        elif bitrate.endswith('M'):
            value = float(bitrate[:-1])
        else:
            value = 2.0  # Default 2 Mbps
            
        # Buffer = 2x bitrate for stability
        buffer_mbps = value * 2
        
        # Minimum 1M buffer, maximum 20M
        buffer_mbps = max(1, min(buffer_mbps, 20))
        
        return f"{buffer_mbps:.1f}M"
        
    def _start_monitoring(self):
        """Start FFmpeg output monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
            
        self.monitor_thread = threading.Thread(target=self._monitor_ffmpeg_output)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def _monitor_ffmpeg_output(self):
        """Monitor FFmpeg stderr for status and errors"""
        if not self.ffmpeg_process:
            return
            
        try:
            for line in self.ffmpeg_process.stderr:
                if not self.is_streaming:
                    break
                    
                # Parse FFmpeg output for stats
                if "frame=" in line:
                    self._parse_ffmpeg_stats(line)
                elif "error" in line.lower():
                    logger.error(f"FFmpeg error: {line.strip()}")
                    self.stream_error.emit(line.strip())
                    
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            
    def _parse_ffmpeg_stats(self, line):
        """Parse FFmpeg statistics from output line"""
        try:
            # Extract stats from FFmpeg output
            # Format: frame= 1234 fps=30.0 q=23.0 size= 12345kB time=00:00:41.23 bitrate=2456.7kbits/s
            
            stats = {}
            
            # Extract frame count
            if "frame=" in line:
                frame_match = line.split("frame=")[1].split()[0]
                stats['frames'] = int(frame_match)
                
            # Extract FPS
            if "fps=" in line:
                fps_match = line.split("fps=")[1].split()[0]
                stats['fps'] = float(fps_match)
                
            # Extract bitrate
            if "bitrate=" in line:
                bitrate_match = line.split("bitrate=")[1].split()[0]
                stats['bitrate'] = bitrate_match
                
            # Extract dropped frames
            if "dup=" in line:
                dup_match = line.split("dup=")[1].split()[0]
                stats['dropped'] = int(dup_match)
            else:
                stats['dropped'] = 0
                
            self.stream_stats.update(stats)
            
        except Exception as e:
            logger.debug(f"Stats parsing error: {e}")
            
    def _start_stats_thread(self):
        """Start thread to collect MediaMTX statistics"""
        stats_thread = threading.Thread(target=self._collect_mediamtx_stats)
        stats_thread.daemon = True
        stats_thread.start()
        
    def _collect_mediamtx_stats(self):
        """Collect statistics from MediaMTX API"""
        while self.is_streaming:
            try:
                # Get stats from MediaMTX API
                response = requests.get(
                    f"http://{self.media_mtx_server}:{self.api_port}/v3/paths/list",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    paths = data.get('items', [])
                    
                    # Find our stream
                    for path in paths:
                        if path.get('name') == self.current_stream_name:
                            # Extract relevant stats
                            stats = {
                                'readers': len(path.get('readers', [])),
                                'bytesIn': path.get('bytesIn', 0),
                                'bytesOut': path.get('bytesOut', 0)
                            }
                            
                            # Calculate bitrate from bytes
                            if 'bytesIn' in stats and stats['bytesIn'] > 0:
                                # Rough bitrate calculation
                                mbps = (stats['bytesIn'] * 8) / (1000000 * 5)  # 5 second interval
                                stats['bitrate_mbps'] = f"{mbps:.2f} Mbps"
                                
                            # Merge with FFmpeg stats
                            self.stream_stats.update(stats)
                            self.stream_stats_updated.emit(self.stream_stats)
                            break
                            
            except Exception as e:
                logger.debug(f"MediaMTX stats error: {e}")
                
            time.sleep(5)  # Update every 5 seconds
            
    def stop_streaming(self):
        """Stop streaming gracefully"""
        try:
            self.is_streaming = False
            
            if self.ffmpeg_process:
                # Send graceful termination
                self.ffmpeg_process.terminate()
                
                # Wait for process to end
                try:
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.ffmpeg_process.kill()
                    
                self.ffmpeg_process = None
                
            self.current_stream_name = None
            self.stream_stats = {}
            self.stream_status_changed.emit("Streaming stopped")
            
            logger.info("SRT streaming stopped")
            
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            
    def request_stream_stats(self):
        """Request current stream statistics"""
        if self.stream_stats:
            self.stream_stats_updated.emit(self.stream_stats)
            
    def get_stream_info(self):
        """Get current stream information"""
        return {
            'is_streaming': self.is_streaming,
            'stream_name': self.current_stream_name,
            'server': self.media_mtx_server,
            'srt_port': self.srt_port,
            'stats': self.stream_stats
        }
        
    def generate_stream_key(self, user_id, unique_address):
        """Generate unique stream key"""
        timestamp = int(time.time())
        return f"{user_id}_{unique_address}_{timestamp}"
        
    def validate_ffmpeg(self):
        """Validate FFmpeg installation and codecs"""
        try:
            # Check FFmpeg version
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, "FFmpeg not found"
                
            # Check for required codecs
            codecs_result = subprocess.run(
                ['ffmpeg', '-codecs'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            required = {
                'libx264': False,    # H.264 encoder
                'aac': False,        # AAC audio encoder
                'libndi_newtek': False  # NDI support
            }
            
            for line in codecs_result.stdout.split('\n'):
                for codec in required:
                    if codec in line:
                        required[codec] = True
                        
            missing = [k for k, v in required.items() if not v]
            
            if missing:
                return False, f"Missing codecs: {', '.join(missing)}"
                
            return True, "FFmpeg ready"
            
        except Exception as e:
            return False, str(e)