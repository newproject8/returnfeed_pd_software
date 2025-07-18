#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fixed NDI Manager Enterprise - Based on stable implementation patterns
Removes blocking operations, complex buffering, and forbidden patterns
"""

import sys
import os
import logging
from typing import Optional, List, Dict, Any
import numpy as np
from collections import deque
import time

# Qt imports
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer

# NDI handling
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pd_app.utils import setup_logger

logger = setup_logger("ndi_manager_fixed")

# Platform-specific NDI setup
if sys.platform == "win32":
    ndi_sdk_path = "C:\\Program Files\\NDI\\NDI 5 SDK\\Bin\\x64"
    if os.path.exists(ndi_sdk_path):
        try:
            os.add_dll_directory(ndi_sdk_path)
            logger.info(f"Added NDI SDK DLL directory: {ndi_sdk_path}")
        except Exception as e:
            logger.error(f"Failed to add DLL directory: {e}")

try:
    import ndi
except ImportError as e:
    logger.critical(f"Failed to import NDI: {e}")
    ndi = None


class NDIReceiveWorker(QThread):
    """
    Simplified NDI receiver worker based on stable implementation
    No blocking waits, direct frame emission, simple frame skipping
    """
    
    # Signals
    frame_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    statistics_updated = pyqtSignal(dict)
    
    def __init__(self, source_name: str):
        super().__init__()
        self.source_name = source_name
        self.receiver = None
        self.running = False
        
        # Frame rate control - simple and effective
        self.target_fps = 30  # Display at 30fps max
        self.frame_interval = 1.0 / self.target_fps
        self.last_frame_time = 0
        
        # Statistics
        self.frames_received = 0
        self.frames_displayed = 0
        self.frames_dropped = 0
        self.start_time = time.time()
        
    def run(self):
        """Main receive loop - based on stable pattern"""
        self.running = True
        self.start_time = time.time()
        
        try:
            # Create receiver
            if not self._create_receiver():
                return
                
            self.connection_status_changed.emit(True)
            logger.info(f"Connected to NDI source: {self.source_name}")
            
            # Main receive loop - simple and non-blocking
            while self.running:
                try:
                    # Receive frame with minimal timeout (16ms = ~60fps)
                    frame_type = ndi.recv_capture_v2(self.receiver, 16)
                    
                    if frame_type == ndi.FRAME_TYPE_VIDEO:
                        self._handle_video_frame()
                    elif frame_type == ndi.FRAME_TYPE_NONE:
                        # No frame available - this is normal, continue
                        continue
                        
                except Exception as e:
                    logger.error(f"Frame receive error: {e}")
                    # Continue receiving despite errors
                    continue
                    
            # Update statistics periodically
            if self.frames_received % 30 == 0:
                self._emit_statistics()
                    
        except Exception as e:
            logger.error(f"Receiver error: {e}")
            self.error_occurred.emit(str(e))
            
        finally:
            self._cleanup()
            self.connection_status_changed.emit(False)
            
    def _create_receiver(self) -> bool:
        """Create NDI receiver"""
        try:
            # Parse source name
            source_dict = {
                'name': self.source_name,
                'url_address': None
            }
            
            # Create receiver
            self.receiver = ndi.recv_create_v3(source_dict)
            if not self.receiver:
                self.error_occurred.emit("Failed to create NDI receiver")
                return False
                
            # Set format to highest quality
            ndi.recv_color_format(self.receiver, ndi.COLOR_FORMAT_RGBX_RGBA)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create receiver: {e}")
            self.error_occurred.emit(str(e))
            return False
            
    def _handle_video_frame(self):
        """Handle received video frame - simple frame skipping"""
        try:
            # Get frame
            video_frame = ndi.recv_get_video_data(self.receiver)
            if not video_frame or not video_frame.data:
                return
                
            self.frames_received += 1
            current_time = time.time()
            
            # Simple frame rate limiting
            time_since_last = current_time - self.last_frame_time
            if time_since_last < self.frame_interval:
                # Skip this frame to maintain target FPS
                self.frames_dropped += 1
                ndi.recv_free_video_v2(self.receiver, video_frame)
                return
                
            # Convert and emit frame
            try:
                # Direct numpy array creation - no copy
                height = video_frame.yres
                width = video_frame.xres
                
                # Create numpy array view of the data
                frame_data = np.frombuffer(
                    video_frame.data,
                    dtype=np.uint8
                ).reshape((height, width, 4))
                
                # Convert RGBA to RGB (in-place operation)
                rgb_frame = frame_data[:, :, :3]
                
                # Emit frame
                self.frame_received.emit(rgb_frame)
                self.frames_displayed += 1
                self.last_frame_time = current_time
                
            finally:
                # Always free the frame
                ndi.recv_free_video_v2(self.receiver, video_frame)
                
        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            
    def _emit_statistics(self):
        """Emit performance statistics"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            actual_fps = self.frames_displayed / elapsed
            receive_fps = self.frames_received / elapsed
            drop_rate = (self.frames_dropped / self.frames_received * 100) if self.frames_received > 0 else 0
            
            stats = {
                'actual_fps': actual_fps,
                'receive_fps': receive_fps,
                'frames_displayed': self.frames_displayed,
                'frames_dropped': self.frames_dropped,
                'drop_rate': drop_rate
            }
            
            self.statistics_updated.emit(stats)
            
    def stop(self):
        """Stop the receiver"""
        self.running = False
        
    def _cleanup(self):
        """Clean up resources"""
        if self.receiver:
            try:
                ndi.recv_destroy(self.receiver)
            except:
                pass
            self.receiver = None


class NDISourceDiscovery(QThread):
    """
    Simple NDI source discovery based on stable pattern
    No blocking waits, periodic updates
    """
    
    sources_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.finder = None
        
    def run(self):
        """Discovery loop"""
        self.running = True
        
        try:
            # Create finder
            self.finder = ndi.find_create_v2()
            if not self.finder:
                logger.error("Failed to create NDI finder")
                return
                
            # Discovery loop with periodic updates
            while self.running:
                # Get current sources - non-blocking
                sources = ndi.find_get_current_sources(self.finder)
                
                if sources:
                    # Convert to list of source names
                    source_list = []
                    for source in sources:
                        if hasattr(source, 'name') and source.name:
                            source_list.append(source.name)
                            
                    self.sources_updated.emit(source_list)
                    
                # Wait before next update - using QThread.msleep instead of blocking wait
                self.msleep(1000)  # Update every second
                
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            
        finally:
            if self.finder:
                try:
                    ndi.find_destroy(self.finder)
                except:
                    pass
                    
    def stop(self):
        """Stop discovery"""
        self.running = False


class NDIManagerEnterprise(QObject):
    """
    Fixed NDI Manager - Simple, stable, high-performance
    Based on proven patterns from stable implementation
    """
    
    # Signals
    frame_ready = pyqtSignal(np.ndarray)
    connection_changed = pyqtSignal(bool)
    sources_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    statistics_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Check NDI availability
        if not ndi:
            logger.critical("NDI library not available")
            return
            
        # Initialize NDI
        if not ndi.initialize():
            logger.critical("Failed to initialize NDI")
            return
            
        self.connected = False
        self.receiver_thread = None
        self.discovery_thread = None
        
        # Start discovery
        self._start_discovery()
        
        logger.info("NDI Manager initialized (fixed version)")
        
    def _start_discovery(self):
        """Start source discovery"""
        self.discovery_thread = NDISourceDiscovery()
        self.discovery_thread.sources_updated.connect(self.sources_updated.emit)
        self.discovery_thread.start()
        
    def connect_to_source(self, source_name: str):
        """Connect to NDI source"""
        # Disconnect if already connected
        if self.connected:
            self.disconnect()
            
        # Create and start receiver
        self.receiver_thread = NDIReceiveWorker(source_name)
        
        # Connect signals
        self.receiver_thread.frame_received.connect(self.frame_ready.emit)
        self.receiver_thread.connection_status_changed.connect(self._on_connection_changed)
        self.receiver_thread.error_occurred.connect(self.error_occurred.emit)
        self.receiver_thread.statistics_updated.connect(self.statistics_updated.emit)
        
        # Start receiving
        self.receiver_thread.start()
        
    def disconnect(self):
        """Disconnect from current source"""
        if self.receiver_thread:
            self.receiver_thread.stop()
            self.receiver_thread.wait(2000)  # Wait max 2 seconds
            self.receiver_thread = None
            
        self.connected = False
        self.connection_changed.emit(False)
        
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool):
        """Handle connection state change"""
        self.connected = connected
        self.connection_changed.emit(connected)
        
    def stop(self):
        """Stop all operations"""
        # Stop discovery
        if self.discovery_thread:
            self.discovery_thread.stop()
            self.discovery_thread.wait(2000)
            
        # Disconnect
        self.disconnect()
        
        # Destroy NDI
        try:
            ndi.destroy()
        except:
            pass
            
    def refresh_sources(self):
        """Refresh source list - discovery runs continuously"""
        # Discovery is automatic, just log the request
        logger.info("Source refresh requested")