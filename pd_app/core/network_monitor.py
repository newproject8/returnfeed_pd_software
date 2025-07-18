# pd_app/core/network_monitor.py
"""
Network Monitor - Real-time ping measurement and adaptive latency calculation
Measures network latency to MediaMTX server and automatically adjusts SRT latency
"""

import time
import threading
import requests
import statistics
import logging
from collections import deque
from typing import Optional, Callable, Tuple
import socket
import struct

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer
except ImportError:
    class QObject:
        pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass

logger = logging.getLogger(__name__)

class NetworkMonitor(QObject):
    """Network monitoring for adaptive SRT latency"""
    
    # Signals
    ping_updated = pyqtSignal(float)  # Current ping in ms
    latency_updated = pyqtSignal(int)  # Calculated SRT latency in ms
    network_status_changed = pyqtSignal(str)  # Network quality status
    
    # Network quality thresholds
    QUALITY_EXCELLENT = "Excellent"  # < 10ms
    QUALITY_GOOD = "Good"           # 10-30ms
    QUALITY_FAIR = "Fair"           # 30-50ms
    QUALITY_POOR = "Poor"           # 50-100ms
    QUALITY_BAD = "Bad"             # > 100ms
    
    def __init__(self, server_host="returnfeed.net", api_port=9997):
        super().__init__()
        self.server_host = server_host
        self.api_port = api_port
        self.api_url = f"http://{server_host}:{api_port}/v3/config/global"
        
        # Ping history (keep last 10 measurements)
        self.ping_history = deque(maxlen=10)
        self.current_ping = 0.0
        self.current_latency = 120  # Default 120ms
        
        # Latency calculation settings
        self.latency_multiplier = 3.0  # Ping x 3
        self.min_latency = 20          # Minimum 20ms
        self.max_latency = 1000        # Maximum 1000ms
        self.auto_adjust = True        # Auto adjustment enabled
        
        # Monitoring thread
        self.monitoring = False
        self.monitor_thread = None
        self.check_interval = 5.0      # Check every 5 seconds
        
        # Callbacks
        self.latency_change_callback = None
        
    def start_monitoring(self):
        """Start network monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"Network monitoring started for {self.server_host}")
        
    def stop_monitoring(self):
        """Stop network monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Network monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Measure ping
                ping_ms = self._measure_ping()
                
                if ping_ms > 0:
                    # Update ping history
                    self.ping_history.append(ping_ms)
                    
                    # Calculate average ping (remove outliers)
                    avg_ping = self._calculate_average_ping()
                    self.current_ping = avg_ping
                    self.ping_updated.emit(avg_ping)
                    
                    # Calculate and update latency if auto-adjust is enabled
                    if self.auto_adjust:
                        new_latency = self._calculate_optimal_latency(avg_ping)
                        if abs(new_latency - self.current_latency) >= 10:  # Only update if change > 10ms
                            self.current_latency = new_latency
                            self.latency_updated.emit(new_latency)
                            
                            # Notify callback if set
                            if self.latency_change_callback:
                                self.latency_change_callback(new_latency)
                    
                    # Update network quality status
                    quality = self._assess_network_quality(avg_ping)
                    self.network_status_changed.emit(quality)
                    
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.check_interval * 2)  # Wait longer on error
                
    def _measure_ping(self) -> float:
        """Measure ping to MediaMTX server using multiple methods"""
        # Method 1: HTTP API ping (most reliable)
        http_ping = self._http_ping()
        if http_ping > 0:
            return http_ping
            
        # Method 2: TCP connect time (fallback)
        tcp_ping = self._tcp_ping()
        if tcp_ping > 0:
            return tcp_ping
            
        # Method 3: UDP echo (if available)
        # udp_ping = self._udp_ping()
        # if udp_ping > 0:
        #     return udp_ping
            
        return -1  # Failed to measure
        
    def _http_ping(self) -> float:
        """Measure HTTP response time to MediaMTX API"""
        try:
            start_time = time.time()
            response = requests.get(
                self.api_url,
                timeout=2,
                headers={'Connection': 'close'}
            )
            end_time = time.time()
            
            if response.status_code == 200:
                ping_ms = (end_time - start_time) * 1000
                logger.debug(f"HTTP ping: {ping_ms:.1f}ms")
                return ping_ms
                
        except Exception as e:
            logger.debug(f"HTTP ping failed: {e}")
            
        return -1
        
    def _tcp_ping(self) -> float:
        """Measure TCP connection time to SRT port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            start_time = time.time()
            # Try to connect to SRT control port (usually API port works)
            result = sock.connect_ex((self.server_host, self.api_port))
            end_time = time.time()
            sock.close()
            
            if result == 0:  # Success
                ping_ms = (end_time - start_time) * 1000
                logger.debug(f"TCP ping: {ping_ms:.1f}ms")
                return ping_ms
                
        except Exception as e:
            logger.debug(f"TCP ping failed: {e}")
            
        return -1
        
    def _calculate_average_ping(self) -> float:
        """Calculate average ping with outlier removal"""
        if not self.ping_history:
            return 0.0
            
        if len(self.ping_history) < 3:
            # Not enough samples, return simple average
            return sum(self.ping_history) / len(self.ping_history)
            
        # Remove outliers using IQR method
        sorted_pings = sorted(self.ping_history)
        q1 = sorted_pings[len(sorted_pings) // 4]
        q3 = sorted_pings[3 * len(sorted_pings) // 4]
        iqr = q3 - q1
        
        # Filter values within 1.5 * IQR
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        filtered_pings = [p for p in self.ping_history 
                         if lower_bound <= p <= upper_bound]
        
        if filtered_pings:
            return sum(filtered_pings) / len(filtered_pings)
        else:
            # All values were outliers, return median
            return statistics.median(self.ping_history)
            
    def _calculate_optimal_latency(self, ping_ms: float) -> int:
        """Calculate optimal SRT latency based on ping"""
        # Base calculation: ping * multiplier
        calculated_latency = ping_ms * self.latency_multiplier
        
        # Add jitter buffer (10% of ping)
        jitter_buffer = ping_ms * 0.1
        calculated_latency += jitter_buffer
        
        # Round to nearest 10ms
        calculated_latency = round(calculated_latency / 10) * 10
        
        # Apply min/max limits
        calculated_latency = max(self.min_latency, 
                                min(self.max_latency, int(calculated_latency)))
        
        logger.debug(f"Ping: {ping_ms:.1f}ms → SRT Latency: {calculated_latency}ms")
        
        return calculated_latency
        
    def _assess_network_quality(self, ping_ms: float) -> str:
        """Assess network quality based on ping"""
        if ping_ms < 10:
            return self.QUALITY_EXCELLENT
        elif ping_ms < 30:
            return self.QUALITY_GOOD
        elif ping_ms < 50:
            return self.QUALITY_FAIR
        elif ping_ms < 100:
            return self.QUALITY_POOR
        else:
            return self.QUALITY_BAD
            
    def set_auto_adjust(self, enabled: bool):
        """Enable/disable automatic latency adjustment"""
        self.auto_adjust = enabled
        logger.info(f"Auto latency adjustment: {'enabled' if enabled else 'disabled'}")
        
    def set_latency_multiplier(self, multiplier: float):
        """Set latency multiplier (default 3.0)"""
        self.latency_multiplier = max(1.0, min(5.0, multiplier))
        logger.info(f"Latency multiplier set to: {self.latency_multiplier}")
        
    def set_latency_limits(self, min_ms: int, max_ms: int):
        """Set min/max latency limits"""
        self.min_latency = max(20, min_ms)
        self.max_latency = min(2000, max_ms)
        logger.info(f"Latency limits: {self.min_latency}ms - {self.max_latency}ms")
        
    def get_current_stats(self) -> dict:
        """Get current network statistics"""
        return {
            'current_ping': self.current_ping,
            'average_ping': sum(self.ping_history) / len(self.ping_history) if self.ping_history else 0,
            'min_ping': min(self.ping_history) if self.ping_history else 0,
            'max_ping': max(self.ping_history) if self.ping_history else 0,
            'current_latency': self.current_latency,
            'auto_adjust': self.auto_adjust,
            'network_quality': self._assess_network_quality(self.current_ping),
            'sample_count': len(self.ping_history)
        }
        
    def force_ping_check(self) -> Tuple[float, int]:
        """Force immediate ping check and return (ping, latency)"""
        ping_ms = self._measure_ping()
        if ping_ms > 0:
            self.ping_history.append(ping_ms)
            avg_ping = self._calculate_average_ping()
            latency = self._calculate_optimal_latency(avg_ping)
            return avg_ping, latency
        return 0.0, self.current_latency


class NetworkQualityWidget(QObject):
    """Widget for displaying network quality in UI"""
    
    def __init__(self, network_monitor: NetworkMonitor):
        super().__init__()
        self.monitor = network_monitor
        
        # Connect signals
        self.monitor.ping_updated.connect(self.on_ping_updated)
        self.monitor.latency_updated.connect(self.on_latency_updated)
        self.monitor.network_status_changed.connect(self.on_quality_changed)
        
        # UI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
    def on_ping_updated(self, ping_ms: float):
        """Handle ping update"""
        # Update UI with new ping value
        pass
        
    def on_latency_updated(self, latency_ms: int):
        """Handle latency update"""
        # Update UI with new latency value
        pass
        
    def on_quality_changed(self, quality: str):
        """Handle network quality change"""
        # Update UI with quality indicator
        # Could change color based on quality
        pass
        
    def update_display(self):
        """Update display with current stats"""
        stats = self.monitor.get_current_stats()
        # Update UI elements with stats
        pass