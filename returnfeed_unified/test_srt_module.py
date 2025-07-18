#!/usr/bin/env python3
"""Test SRT module initialization"""

import sys
import os

# Add module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.srt_module import SRTModule

def test_srt_module():
    print("Testing SRT module initialization...")
    
    try:
        # Create module
        srt_module = SRTModule()
        print("✓ SRT module created")
        
        # Initialize
        if srt_module.initialize():
            print("✓ SRT module initialized")
        else:
            print("✗ SRT module initialization failed")
            return False
            
        # Check widget
        widget = srt_module.get_widget()
        if widget:
            print("✓ SRT widget created")
        else:
            print("✗ SRT widget is None")
            return False
            
        # Check manager
        if srt_module.srt_manager:
            print("✓ SRT manager created")
            
            # Check FFmpeg
            if srt_module.srt_manager.check_ffmpeg():
                print("✓ FFmpeg is available")
            else:
                print("⚠ FFmpeg not found - streaming won't work")
        else:
            print("✗ SRT manager is None")
            return False
            
        print("\nSRT module test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Setup logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run test
    success = test_srt_module()
    sys.exit(0 if success else 1)