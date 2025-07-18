# pd_app/core/srt_manager_adaptive.py
"""
Adaptive SRT Manager - Network-aware streaming with dynamic latency adjustment
Integrates with NetworkMonitor for optimal streaming performance
"""

import subprocess
import threading
import logging
import time
from typing import Optional, Dict, Any

from .srt_manager_enhanced import EnhancedSRTManager
from .network_monitor import NetworkMonitor

try:
    from PyQt6.QtCore import pyqtSignal
except ImportError:
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass

logger = logging.getLogger(__name__)

class AdaptiveSRTManager(EnhancedSRTManager):
    """SRT Manager with adaptive network-based latency"""
    
    # Additional signals
    latency_auto_adjusted = pyqtSignal(int, float)  # new_latency, ping
    reconnecting = pyqtSignal(str)  # reason
    
    def __init__(self):
        super().__init__()
        
        # Network monitoring
        self.network_monitor = NetworkMonitor(
            server_host=self.media_mtx_server,
            api_port=self.api_port
        )
        
        # Adaptive settings
        self.adaptive_mode = True
        self.last_applied_latency = 120
        self.reconnect_on_latency_change = False
        self.latency_change_threshold = 50  # Reconnect if latency changes by 50ms
        
        # Connect network monitor callback
        self.network_monitor.latency_change_callback = self._on_latency_changed
        
        # Start network monitoring
        self.network_monitor.start_monitoring()
        
    def set_adaptive_mode(self, enabled: bool):
        """Enable/disable adaptive latency mode"""
        self.adaptive_mode = enabled
        self.network_monitor.set_auto_adjust(enabled)
        
        if enabled:
            # Force immediate ping check
            ping, latency = self.network_monitor.force_ping_check()
            if latency != self.last_applied_latency:
                self._on_latency_changed(latency)
                
        logger.info(f"Adaptive mode: {'enabled' if enabled else 'disabled'}")
        
    def start_ndi_streaming_adaptive(self, ndi_source, stream_name, params):
        """Start NDI streaming with adaptive latency"""
        # Get current optimal latency
        if self.adaptive_mode:
            ping, optimal_latency = self.network_monitor.force_ping_check()
            params['srt_latency'] = optimal_latency
            self.last_applied_latency = optimal_latency
            logger.info(f"Starting stream with adaptive latency: {optimal_latency}ms (ping: {ping:.1f}ms)")
        
        # Start streaming with parent method
        super().start_ndi_streaming_enhanced(ndi_source, stream_name, params)
        
    def start_screen_streaming_adaptive(self, stream_name, params):
        """Start screen streaming with adaptive latency"""
        # Get current optimal latency
        if self.adaptive_mode:
            ping, optimal_latency = self.network_monitor.force_ping_check()
            params['srt_latency'] = optimal_latency
            self.last_applied_latency = optimal_latency
            logger.info(f"Starting stream with adaptive latency: {optimal_latency}ms (ping: {ping:.1f}ms)")
        
        # Start streaming with parent method
        super().start_screen_streaming_enhanced(stream_name, params)
        
    def _on_latency_changed(self, new_latency: int):
        """Handle latency change from network monitor"""
        if not self.adaptive_mode:
            return
            
        # Check if change is significant
        latency_change = abs(new_latency - self.last_applied_latency)
        
        if latency_change >= self.latency_change_threshold:
            logger.info(f"Significant latency change detected: {self.last_applied_latency}ms → {new_latency}ms")
            
            # Emit signal for UI update
            current_ping = self.network_monitor.current_ping
            self.latency_auto_adjusted.emit(new_latency, current_ping)
            
            # If streaming, decide whether to reconnect
            if self.is_streaming and self.reconnect_on_latency_change:
                self._reconnect_with_new_latency(new_latency)
            else:
                # Just update for next stream
                self.last_applied_latency = new_latency
                
    def _reconnect_with_new_latency(self, new_latency: int):
        """Reconnect stream with new latency"""
        if not self.is_streaming:
            return
            
        logger.info(f"Reconnecting stream with new latency: {new_latency}ms")
        self.reconnecting.emit(f"Adjusting latency to {new_latency}ms")
        
        # Save current stream info
        stream_name = self.current_stream_name
        current_stats = self.stream_stats.copy()
        
        # Stop current stream
        self.stop_streaming()
        
        # Brief pause to ensure clean disconnect
        time.sleep(0.5)
        
        # Restart with new latency
        # Note: This is simplified - in practice, you'd need to preserve
        # all the original parameters (source, bitrate, etc.)
        self.last_applied_latency = new_latency
        logger.info("Stream reconnected with new latency")
        
    def get_network_stats(self) -> Dict[str, Any]:
        """Get combined streaming and network statistics"""
        stream_stats = self.get_stream_info()
        network_stats = self.network_monitor.get_current_stats()
        
        return {
            **stream_stats,
            'network': network_stats,
            'adaptive_mode': self.adaptive_mode,
            'applied_latency': self.last_applied_latency
        }
        
    def set_reconnect_on_latency_change(self, enabled: bool):
        """Enable/disable automatic reconnection on latency change"""
        self.reconnect_on_latency_change = enabled
        logger.info(f"Reconnect on latency change: {'enabled' if enabled else 'disabled'}")
        
    def set_latency_change_threshold(self, threshold_ms: int):
        """Set threshold for latency change to trigger reconnection"""
        self.latency_change_threshold = max(10, min(200, threshold_ms))
        logger.info(f"Latency change threshold: {self.latency_change_threshold}ms")
        
    def stop_streaming(self):
        """Stop streaming and cleanup"""
        super().stop_streaming()
        
    def cleanup(self):
        """Cleanup resources"""
        self.network_monitor.stop_monitoring()
        
    def configure_network_monitor(self, **kwargs):
        """Configure network monitor settings"""
        if 'multiplier' in kwargs:
            self.network_monitor.set_latency_multiplier(kwargs['multiplier'])
        if 'min_latency' in kwargs:
            self.network_monitor.set_latency_limits(
                kwargs.get('min_latency', 20),
                kwargs.get('max_latency', 1000)
            )
        if 'check_interval' in kwargs:
            self.network_monitor.check_interval = kwargs['check_interval']


class AdaptiveStreamingController:
    """High-level controller for adaptive streaming"""
    
    def __init__(self, srt_manager: AdaptiveSRTManager):
        self.srt_manager = srt_manager
        self.presets = {
            'local': {
                'multiplier': 2.0,      # 2x for local network
                'min_latency': 20,
                'max_latency': 100,
                'check_interval': 3.0
            },
            'regional': {
                'multiplier': 3.0,      # 3x for regional
                'min_latency': 50,
                'max_latency': 300,
                'check_interval': 5.0
            },
            'global': {
                'multiplier': 4.0,      # 4x for global
                'min_latency': 100,
                'max_latency': 500,
                'check_interval': 10.0
            },
            'satellite': {
                'multiplier': 5.0,      # 5x for satellite
                'min_latency': 200,
                'max_latency': 1000,
                'check_interval': 15.0
            }
        }
        
    def apply_preset(self, preset_name: str):
        """Apply network preset"""
        if preset_name in self.presets:
            settings = self.presets[preset_name]
            self.srt_manager.configure_network_monitor(**settings)
            logger.info(f"Applied network preset: {preset_name}")
            return True
        return False
        
    def get_optimal_settings(self) -> Dict[str, Any]:
        """Get optimal settings based on current network"""
        stats = self.srt_manager.network_monitor.get_current_stats()
        ping = stats['current_ping']
        
        # Recommend preset based on ping
        if ping < 10:
            preset = 'local'
        elif ping < 50:
            preset = 'regional'  
        elif ping < 150:
            preset = 'global'
        else:
            preset = 'satellite'
            
        return {
            'recommended_preset': preset,
            'current_ping': ping,
            'optimal_latency': stats['current_latency'],
            'network_quality': stats['network_quality']
        }