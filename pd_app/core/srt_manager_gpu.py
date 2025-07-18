# pd_app/core/srt_manager_gpu.py
"""
GPU-Accelerated SRT Manager with Resource Optimization
Supports NVENC, QuickSync, and AMF for H.264 encoding
"""

import subprocess
import platform
import logging
import os
from typing import Optional, Dict, List, Tuple

from .srt_manager_adaptive import AdaptiveSRTManager

logger = logging.getLogger(__name__)

class GPUAcceleratedSRTManager(AdaptiveSRTManager):
    """SRT Manager with GPU acceleration and resource optimization"""
    
    def __init__(self):
        super().__init__()
        
        # GPU capabilities
        self.gpu_info = self._detect_gpu_capabilities()
        self.selected_encoder = None
        self.gpu_available = False
        
        # Resource optimization settings
        self.resource_optimization = True
        self.preview_pause_callback = None
        self.preview_resume_callback = None
        
        # Encoder preferences (in order of preference)
        self.encoder_priority = [
            'h264_nvenc',      # NVIDIA NVENC
            'h264_qsv',        # Intel QuickSync
            'h264_amf',        # AMD AMF
            'h264_videotoolbox', # macOS Hardware
            'libx264'          # CPU fallback
        ]
        
        # Detect best available encoder
        self._select_best_encoder()
        
    def _detect_gpu_capabilities(self) -> Dict:
        """Detect available GPU and capabilities"""
        gpu_info = {
            'nvidia': False,
            'intel': False,
            'amd': False,
            'apple': False,
            'encoders': []
        }
        
        try:
            # Get available encoders from FFmpeg
            result = subprocess.run(
                ['ffmpeg', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check for GPU encoders
                if 'h264_nvenc' in output:
                    gpu_info['nvidia'] = True
                    gpu_info['encoders'].append('h264_nvenc')
                    logger.info("NVIDIA NVENC detected")
                    
                if 'h264_qsv' in output:
                    gpu_info['intel'] = True
                    gpu_info['encoders'].append('h264_qsv')
                    logger.info("Intel QuickSync detected")
                    
                if 'h264_amf' in output:
                    gpu_info['amd'] = True
                    gpu_info['encoders'].append('h264_amf')
                    logger.info("AMD AMF detected")
                    
                if 'h264_videotoolbox' in output and platform.system() == 'Darwin':
                    gpu_info['apple'] = True
                    gpu_info['encoders'].append('h264_videotoolbox')
                    logger.info("Apple VideoToolbox detected")
                    
        except Exception as e:
            logger.error(f"GPU detection failed: {e}")
            
        return gpu_info
        
    def _select_best_encoder(self):
        """Select the best available encoder"""
        for encoder in self.encoder_priority:
            if encoder in self.gpu_info['encoders'] or encoder == 'libx264':
                self.selected_encoder = encoder
                self.gpu_available = encoder != 'libx264'
                logger.info(f"Selected encoder: {encoder} (GPU: {self.gpu_available})")
                break
                
    def get_encoder_params(self, bitrate: str, params: Dict) -> List[str]:
        """Get encoder-specific parameters"""
        encoder_params = []
        
        if self.selected_encoder == 'h264_nvenc':
            # NVIDIA NVENC parameters
            encoder_params.extend([
                '-c:v', 'h264_nvenc',
                '-preset', 'p4',  # P4 preset for low latency
                '-tune', 'll',    # Low latency tuning
                '-zerolatency', '1',
                '-rc', 'cbr',     # Constant bitrate for streaming
                '-rc-lookahead', '0',  # Disable lookahead for low latency
                '-no-scenecut', '1',   # Disable scene cut detection
                '-forced-idr', '1',    # Force IDR frames
                '-profile:v', params.get('h264_profile', 'main'),
                '-level', '4.1',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', self._calculate_buffer_size(bitrate),
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                '-bf', '0',  # No B-frames for low latency
            ])
            
            # GPU selection if multiple GPUs
            if 'gpu_index' in params:
                encoder_params.extend(['-gpu', str(params['gpu_index'])])
                
        elif self.selected_encoder == 'h264_qsv':
            # Intel QuickSync parameters
            encoder_params.extend([
                '-c:v', 'h264_qsv',
                '-preset', 'veryfast',
                '-look_ahead', '0',
                '-look_ahead_depth', '0',
                '-profile:v', params.get('h264_profile', 'main'),
                '-level', '4.1',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', self._calculate_buffer_size(bitrate),
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                '-bf', '0',
                '-refs', '1',
            ])
            
        elif self.selected_encoder == 'h264_amf':
            # AMD AMF parameters
            encoder_params.extend([
                '-c:v', 'h264_amf',
                '-usage', 'ultralowlatency',
                '-profile:v', params.get('h264_profile', 'main'),
                '-level', '4.1',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', self._calculate_buffer_size(bitrate),
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                '-bf', '0',
            ])
            
        elif self.selected_encoder == 'h264_videotoolbox':
            # macOS VideoToolbox parameters
            encoder_params.extend([
                '-c:v', 'h264_videotoolbox',
                '-profile:v', params.get('h264_profile', 'main'),
                '-level', '4.1',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', self._calculate_buffer_size(bitrate),
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                '-bf', '0',
                '-realtime', '1',
            ])
            
        else:
            # CPU fallback with libx264
            encoder_params.extend([
                '-c:v', 'libx264',
                '-preset', params.get('h264_preset', 'ultrafast'),
                '-profile:v', params.get('h264_profile', 'main'),
                '-tune', 'zerolatency',
                '-b:v', bitrate,
                '-maxrate', bitrate,
                '-bufsize', self._calculate_buffer_size(bitrate),
                '-g', str(params.get('fps', 30) * params.get('keyframe_interval', 2)),
                '-x264-params', 'nal-hrd=cbr:no-mbtree:bframes=0:threads=auto:sliced-threads'
            ])
            
        return encoder_params
        
    def start_ndi_streaming_gpu(self, ndi_source, stream_name, params):
        """Start NDI streaming with GPU acceleration"""
        try:
            if self.is_streaming:
                self.stop_streaming()
                
            # Pause NDI preview if resource optimization is enabled
            if self.resource_optimization and self.preview_pause_callback:
                logger.info("Pausing NDI preview for resource optimization")
                self.preview_pause_callback()
                
            # Get optimal latency
            if self.adaptive_mode:
                ping, optimal_latency = self.network_monitor.force_ping_check()
                params['srt_latency'] = optimal_latency
                self.last_applied_latency = optimal_latency
                
            # Build SRT URL
            srt_url = f"srt://{self.media_mtx_server}:{self.srt_port}?streamid={stream_name}&latency={params.get('srt_latency', 120)}"
            
            # Build FFmpeg command
            cmd = ['ffmpeg']
            
            # Hardware acceleration flags
            if self.gpu_available:
                if self.selected_encoder == 'h264_nvenc':
                    # NVIDIA hardware acceleration
                    cmd.extend(['-hwaccel', 'cuda'])
                    if 'gpu_index' in params:
                        cmd.extend(['-hwaccel_device', str(params['gpu_index'])])
                elif self.selected_encoder == 'h264_qsv':
                    # Intel QuickSync acceleration
                    cmd.extend(['-hwaccel', 'qsv'])
                elif self.selected_encoder == 'h264_videotoolbox':
                    # macOS hardware acceleration
                    cmd.extend(['-hwaccel', 'videotoolbox'])
                    
            # Input
            cmd.extend([
                '-f', 'libndi_newtek',
                '-i', ndi_source,
            ])
            
            # Add encoder parameters
            encoder_params = self.get_encoder_params(
                params.get('bitrate', '2M'),
                params
            )
            cmd.extend(encoder_params)
            
            # Audio encoding
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', params.get('audio_bitrate', '128k'),
                '-ar', '48000',
                '-ac', '2',
            ])
            
            # Output format
            cmd.extend([
                '-f', 'mpegts',
                '-fflags', '+genpts',
                srt_url
            ])
            
            logger.info(f"Starting GPU-accelerated stream: {' '.join(cmd)}")
            
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
            
            # Emit status with GPU info
            gpu_status = f"GPU Accelerated ({self.selected_encoder})" if self.gpu_available else "CPU Encoding"
            self.stream_status_changed.emit(f"NDI → SRT Streaming ({gpu_status}): {stream_name}")
            
            # Start monitoring
            self._start_monitoring()
            self._start_stats_thread()
            
        except Exception as e:
            error_msg = f"GPU streaming failed: {str(e)}"
            logger.error(error_msg)
            self.stream_error.emit(error_msg)
            
            # Resume NDI preview on error
            if self.resource_optimization and self.preview_resume_callback:
                self.preview_resume_callback()
                
    def stop_streaming(self):
        """Stop streaming and resume NDI preview"""
        super().stop_streaming()
        
        # Resume NDI preview
        if self.resource_optimization and self.preview_resume_callback:
            logger.info("Resuming NDI preview")
            self.preview_resume_callback()
            
    def set_preview_callbacks(self, pause_callback, resume_callback):
        """Set callbacks for NDI preview control"""
        self.preview_pause_callback = pause_callback
        self.preview_resume_callback = resume_callback
        
    def set_resource_optimization(self, enabled: bool):
        """Enable/disable resource optimization"""
        self.resource_optimization = enabled
        logger.info(f"Resource optimization: {'enabled' if enabled else 'disabled'}")
        
    def get_gpu_status(self) -> Dict:
        """Get GPU encoder status"""
        return {
            'gpu_available': self.gpu_available,
            'selected_encoder': self.selected_encoder,
            'gpu_info': self.gpu_info,
            'resource_optimization': self.resource_optimization
        }
        
    def benchmark_encoders(self) -> Dict[str, float]:
        """Benchmark available encoders (for testing)"""
        benchmarks = {}
        test_duration = 5  # seconds
        
        for encoder in self.gpu_info['encoders'] + ['libx264']:
            try:
                # Test encode command
                cmd = [
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', 'testsrc=size=1920x1080:rate=30',
                    '-t', str(test_duration),
                    '-c:v', encoder,
                    '-b:v', '5M',
                    '-f', 'null',
                    '-'
                ]
                
                import time
                start_time = time.time()
                result = subprocess.run(cmd, capture_output=True, text=True)
                encode_time = time.time() - start_time
                
                if result.returncode == 0:
                    # Calculate encoding speed ratio
                    speed_ratio = test_duration / encode_time
                    benchmarks[encoder] = speed_ratio
                    logger.info(f"{encoder} benchmark: {speed_ratio:.2f}x realtime")
                    
            except Exception as e:
                logger.error(f"Benchmark failed for {encoder}: {e}")
                
        return benchmarks


class GPUMonitor:
    """Monitor GPU usage and temperature"""
    
    @staticmethod
    def get_nvidia_stats() -> Optional[Dict]:
        """Get NVIDIA GPU statistics using nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                values = result.stdout.strip().split(', ')
                return {
                    'gpu_usage': int(values[0]),
                    'memory_usage': int(values[1]),
                    'temperature': int(values[2]),
                    'power_draw': float(values[3])
                }
        except:
            pass
        return None
        
    @staticmethod
    def get_intel_stats() -> Optional[Dict]:
        """Get Intel GPU statistics (platform specific)"""
        # Intel GPU monitoring is platform-specific
        # This is a placeholder for actual implementation
        return None
        
    @staticmethod
    def get_amd_stats() -> Optional[Dict]:
        """Get AMD GPU statistics (platform specific)"""
        # AMD GPU monitoring is platform-specific
        # This is a placeholder for actual implementation
        return None