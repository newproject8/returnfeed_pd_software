#!/usr/bin/env python3
"""
Integration Test Suite for PD Software
Tests all components working together
"""

import sys
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

# Import components to test
from pd_app.core.srt_manager_gpu import GPUAcceleratedSRTManager
from pd_app.core.network_monitor import NetworkMonitor
from pd_app.core.resource_monitor import SystemResourceMonitor, ResourceOptimizer
from pd_app.ui.video_display_resource_aware import ResourceAwareVideoDisplay
from pd_app.ui.streaming_status_enhanced import StreamingStatusEnhanced
from pd_app.ui.gpu_monitor_widget import GPUMonitorWidget, ResourceMonitorPanel


class TestGPUAcceleration(unittest.TestCase):
    """Test GPU acceleration features"""
    
    def setUp(self):
        self.manager = GPUAcceleratedSRTManager()
        
    def test_gpu_detection(self):
        """Test GPU encoder detection"""
        gpu_info = self.manager._detect_gpu_capabilities()
        self.assertIsInstance(gpu_info, dict)
        self.assertIn('encoders', gpu_info)
        
    def test_encoder_selection(self):
        """Test best encoder selection"""
        self.manager._select_best_encoder()
        self.assertIsNotNone(self.manager.selected_encoder)
        self.assertIn(self.manager.selected_encoder, [
            'h264_nvenc', 'h264_qsv', 'h264_amf', 
            'h264_videotoolbox', 'libx264'
        ])
        
    def test_encoder_params(self):
        """Test encoder parameter generation"""
        params = self.manager.get_encoder_params('5M', {
            'fps': 30,
            'h264_profile': 'main',
            'keyframe_interval': 2
        })
        self.assertIsInstance(params, list)
        self.assertIn('-c:v', params)
        self.assertIn('-b:v', params)
        
    def test_resource_optimization_callbacks(self):
        """Test preview pause/resume callbacks"""
        pause_called = False
        resume_called = False
        
        def pause_callback():
            nonlocal pause_called
            pause_called = True
            
        def resume_callback():
            nonlocal resume_called
            resume_called = True
            
        self.manager.set_preview_callbacks(pause_callback, resume_callback)
        self.manager.resource_optimization = True
        
        # Mock streaming start
        self.manager.preview_pause_callback()
        self.assertTrue(pause_called)
        
        # Mock streaming stop
        self.manager.preview_resume_callback()
        self.assertTrue(resume_called)


class TestNetworkAdaptiveLatency(unittest.TestCase):
    """Test network adaptive latency features"""
    
    def setUp(self):
        self.monitor = NetworkMonitor()
        
    def test_latency_calculation(self):
        """Test ping × 3 latency calculation"""
        # Test various ping values
        test_cases = [
            (10, 33),   # 10ms ping -> 33ms latency
            (50, 165),  # 50ms ping -> 165ms latency
            (100, 330), # 100ms ping -> 330ms latency
        ]
        
        for ping, expected_latency in test_cases:
            calculated = self.monitor._calculate_optimal_latency(ping)
            self.assertAlmostEqual(calculated, expected_latency, delta=5)
            
    def test_outlier_removal(self):
        """Test ping outlier removal"""
        measurements = [10, 12, 11, 150, 10, 11, 13, 200, 10]
        filtered = self.monitor._remove_outliers(measurements)
        
        # Should remove 150 and 200 as outliers
        self.assertNotIn(150, filtered)
        self.assertNotIn(200, filtered)
        self.assertLess(max(filtered), 20)


class TestResourceMonitoring(unittest.TestCase):
    """Test resource monitoring features"""
    
    def setUp(self):
        self.monitor = SystemResourceMonitor()
        
    def test_resource_stats(self):
        """Test getting resource statistics"""
        stats = self.monitor.get_current_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('cpu_percent', stats)
        self.assertIn('memory_percent', stats)
        
    def test_resource_savings_calculation(self):
        """Test resource savings calculation"""
        # When not streaming
        savings = self.monitor.calculate_resource_savings(True, False)
        self.assertEqual(savings['cpu_saved'], 0)
        
        # When streaming with preview paused
        savings = self.monitor.calculate_resource_savings(False, True)
        self.assertGreater(savings['cpu_saved'], 0)
        self.assertGreater(savings['memory_saved'], 0)
        
    def test_optimization_recommendations(self):
        """Test resource optimization recommendations"""
        optimizer = ResourceOptimizer()
        
        # Test high CPU recommendation
        tips = optimizer.get_optimization_tips({
            'cpu_percent': 85,
            'memory_percent': 50,
            'gpu_percent': 0,
            'gpu_temperature': 60
        })
        self.assertTrue(any('CPU usage' in tip for tip in tips))
        
        # Test GPU recommendation
        tips = optimizer.get_optimization_tips({
            'cpu_percent': 70,
            'memory_percent': 50,
            'gpu_percent': 0,
            'gpu_temperature': 60
        })
        self.assertTrue(any('GPU' in tip for tip in tips))


class TestUIComponents(unittest.TestCase):
    """Test UI components integration"""
    
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        self.video_display = ResourceAwareVideoDisplay()
        self.status_display = StreamingStatusEnhanced()
        self.gpu_monitor = GPUMonitorWidget()
        
    def test_video_display_fade(self):
        """Test video display fade to black"""
        # Start streaming
        self.video_display.start_streaming("test_stream")
        
        # Check fade started
        self.assertTrue(self.video_display.fade_timer.isActive())
        self.assertEqual(self.video_display.fade_direction, -1)  # Fade out
        
        # Wait for fade to complete
        QTest.qWait(1100)  # Wait for animation
        
        # Check preview is paused
        self.assertFalse(self.video_display.is_preview_active)
        
    def test_streaming_status_display(self):
        """Test streaming status updates"""
        # Start streaming
        self.status_display.start_streaming("test_stream")
        
        # Check status updated
        self.assertEqual(self.status_display.status_label.text(), "LIVE")
        self.assertTrue(self.status_display.is_streaming)
        
        # Update stats
        self.status_display.update_stats({
            'bitrate': '3.5 Mbps',
            'fps': 30,
            'latency': 120,
            'viewers': 25
        })
        
        # Check stats displayed
        self.assertEqual(self.status_display.bitrate_value.text(), '3.5 Mbps')
        self.assertEqual(self.status_display.fps_value.text(), '30')
        
    def test_gpu_monitor_updates(self):
        """Test GPU monitor display"""
        # Update GPU info
        self.gpu_monitor.update_gpu_info({
            'gpu_available': True,
            'selected_encoder': 'h264_nvenc'
        })
        
        # Check display updated
        self.assertIn('NVENC', self.gpu_monitor.encoder_type_label.text())
        self.assertEqual(self.gpu_monitor.encoder_label.text(), "GPU Ready")
        
        # Set streaming state
        self.gpu_monitor.set_streaming_state(True)
        self.assertTrue(self.gpu_monitor.is_streaming)


class TestIntegration(unittest.TestCase):
    """Test complete integration scenarios"""
    
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
    def test_streaming_workflow(self):
        """Test complete streaming workflow"""
        # Create components
        srt_manager = GPUAcceleratedSRTManager()
        video_display = ResourceAwareVideoDisplay()
        status_display = StreamingStatusEnhanced()
        
        # Setup preview callbacks
        preview_paused = False
        preview_resumed = False
        
        def pause_preview():
            nonlocal preview_paused
            preview_paused = True
            
        def resume_preview():
            nonlocal preview_resumed
            preview_resumed = True
            
        srt_manager.set_preview_callbacks(pause_preview, resume_preview)
        
        # Mock streaming start
        with patch.object(srt_manager, 'ffmpeg_process', MagicMock()):
            # Start streaming
            video_display.start_streaming("test_stream")
            status_display.start_streaming("test_stream")
            
            # Simulate SRT manager pause
            if srt_manager.resource_optimization:
                srt_manager.preview_pause_callback()
            
            # Check preview paused
            self.assertTrue(preview_paused)
            
            # Wait for fade animation
            QTest.qWait(1100)
            
            # Check video display state
            self.assertFalse(video_display.is_preview_active)
            self.assertTrue(video_display.is_streaming)
            
            # Stop streaming
            video_display.stop_streaming()
            status_display.stop_streaming()
            
            # Simulate SRT manager resume
            srt_manager.preview_resume_callback()
            
            # Check preview resumed
            self.assertTrue(preview_resumed)
            self.assertTrue(video_display.is_preview_active)
            self.assertFalse(video_display.is_streaming)


def run_tests():
    """Run all integration tests"""
    print("🧪 Running PD Software Integration Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestGPUAcceleration))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkAdaptiveLatency))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestUIComponents))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Run tests
    success = run_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)