# pd_app/core/resource_monitor.py
"""
Real-time System Resource Monitor
Tracks CPU, Memory, and GPU usage for resource optimization
"""

import psutil
import subprocess
import platform
import threading
import time
from typing import Dict, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class SystemResourceMonitor(QObject):
    """Monitor system resources in real-time"""
    
    # Signals
    resources_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Current stats
        self.current_stats = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'gpu_percent': 0,
            'gpu_memory_percent': 0,
            'gpu_temperature': 0,
            'gpu_power': 0,
            'process_cpu': 0,
            'process_memory': 0
        }
        
        # Monitoring settings
        self.monitor_interval = 1000  # ms
        self.is_monitoring = False
        
        # Process handle
        self.process = psutil.Process()
        
        # GPU detection
        self.gpu_type = self._detect_gpu_type()
        
        # Timer for monitoring
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_stats)
        
    def _detect_gpu_type(self) -> str:
        """Detect GPU type (nvidia, intel, amd, none)"""
        try:
            # Check for NVIDIA
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return 'nvidia'
        except:
            pass
            
        # Check system info for other GPUs
        system = platform.system()
        if system == 'Darwin':
            return 'apple'
        elif system == 'Windows':
            # Could check for Intel/AMD on Windows
            return 'unknown'
        else:
            # Linux - check for Intel/AMD
            return 'unknown'
            
        return 'none'
        
    def start_monitoring(self):
        """Start resource monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_timer.start(self.monitor_interval)
            
    def stop_monitoring(self):
        """Stop resource monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.monitor_timer.stop()
            
    def _update_stats(self):
        """Update all resource statistics"""
        try:
            # System-wide CPU and memory
            self.current_stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            self.current_stats['memory_percent'] = psutil.virtual_memory().percent
            
            # Process-specific stats
            self.current_stats['process_cpu'] = self.process.cpu_percent()
            self.current_stats['process_memory'] = self.process.memory_percent()
            
            # GPU stats
            if self.gpu_type == 'nvidia':
                gpu_stats = self._get_nvidia_stats()
                if gpu_stats:
                    self.current_stats.update(gpu_stats)
                    
            # Emit update signal
            self.resources_updated.emit(self.current_stats.copy())
            
        except Exception as e:
            print(f"Resource monitoring error: {e}")
            
    def _get_nvidia_stats(self) -> Optional[Dict]:
        """Get NVIDIA GPU statistics"""
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
                    'gpu_percent': int(values[0]),
                    'gpu_memory_percent': int(values[1]),
                    'gpu_temperature': int(values[2]),
                    'gpu_power': float(values[3])
                }
        except:
            pass
        return None
        
    def get_current_stats(self) -> Dict:
        """Get current resource statistics"""
        return self.current_stats.copy()
        
    def calculate_resource_savings(self, preview_active: bool, streaming: bool) -> Dict:
        """Calculate estimated resource savings"""
        savings = {
            'cpu_saved': 0,
            'memory_saved': 0,
            'gpu_saved': 0
        }
        
        if streaming and not preview_active:
            # Estimate savings when preview is paused
            base_cpu = self.current_stats['process_cpu']
            base_memory = self.current_stats['process_memory']
            
            # Typical savings from pausing preview
            savings['cpu_saved'] = max(10, int(base_cpu * 0.3))  # ~30% CPU savings
            savings['memory_saved'] = max(5, int(base_memory * 0.2))  # ~20% memory savings
            savings['gpu_saved'] = 15  # ~15% GPU savings from not rendering preview
            
        return savings


class ResourceOptimizer:
    """Helper class for resource optimization decisions"""
    
    @staticmethod
    def should_pause_preview(cpu_percent: float, memory_percent: float, 
                           is_streaming: bool) -> bool:
        """Determine if preview should be paused for resources"""
        # Auto-pause if resources are high during streaming
        if is_streaming:
            if cpu_percent > 80 or memory_percent > 85:
                return True
        return False
        
    @staticmethod
    def get_recommended_bitrate(cpu_percent: float, gpu_available: bool) -> str:
        """Get recommended bitrate based on available resources"""
        if gpu_available:
            # With GPU, we can handle higher bitrates
            if cpu_percent < 50:
                return "10M"  # 10 Mbps
            elif cpu_percent < 70:
                return "5M"   # 5 Mbps
            else:
                return "3M"   # 3 Mbps
        else:
            # CPU only - be more conservative
            if cpu_percent < 40:
                return "3M"   # 3 Mbps
            elif cpu_percent < 60:
                return "2M"   # 2 Mbps
            else:
                return "1M"   # 1 Mbps
                
    @staticmethod
    def get_optimization_tips(stats: Dict) -> list:
        """Get optimization tips based on current stats"""
        tips = []
        
        if stats['cpu_percent'] > 80:
            tips.append("High CPU usage detected. Consider lowering bitrate or FPS.")
            
        if stats['memory_percent'] > 85:
            tips.append("High memory usage. Close unnecessary applications.")
            
        if stats['gpu_percent'] == 0 and stats['cpu_percent'] > 60:
            tips.append("GPU encoding not active. Enable GPU acceleration for better performance.")
            
        if stats['gpu_temperature'] > 80:
            tips.append("GPU running hot. Ensure proper ventilation.")
            
        return tips