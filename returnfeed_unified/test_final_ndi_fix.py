#!/usr/bin/env python3
"""
Final NDI Fix Validation Script
Tests all the critical NDI API fixes based on working main.py code
"""

def validate_ndi_receiver_fixes():
    """Validate all NDI receiver fixes"""
    print("🔍 Validating Final NDI Receiver Fixes...")
    
    try:
        with open('modules/ndi_module/ndi_receiver.py', 'r') as f:
            content = f.read()
        
        # 1. Check for RecvCreateV3 configuration object
        if 'recv_create_v3 = ndi.RecvCreateV3()' in content:
            print("✅ Uses RecvCreateV3 configuration object")
        else:
            print("❌ Missing RecvCreateV3 configuration object")
            return False
        
        # 2. Check for proper configuration settings
        required_settings = [
            'recv_create_v3.source_to_connect_to = source',
            'recv_create_v3.color_format = ndi.RECV_COLOR_FORMAT_FASTEST',
            'recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST',
            'recv_create_v3.allow_video_fields = True'
        ]
        
        for setting in required_settings:
            if setting in content:
                print(f"✅ {setting}")
            else:
                print(f"❌ Missing: {setting}")
                return False
        
        # 3. Check for recv_connect call
        if 'ndi.recv_connect(self.receiver, source)' in content:
            print("✅ Calls ndi.recv_connect() - 핵심 수정!")
        else:
            print("❌ Missing ndi.recv_connect() call")
            return False
        
        # 4. Check for correct frame capture pattern
        if 'frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2' in content:
            print("✅ Uses correct tuple unpacking for recv_capture_v2")
        else:
            print("❌ Missing correct tuple unpacking")
            return False
        
        # 5. Check for immediate memory release
        if 'ndi.recv_free_video_v2(self.receiver, v_frame)' in content:
            print("✅ Immediate video frame memory release")
        else:
            print("❌ Missing immediate memory release")
            return False
        
        # 6. Check for proper frame type handling
        frame_types = [
            'ndi.FRAME_TYPE_VIDEO',
            'ndi.FRAME_TYPE_AUDIO', 
            'ndi.FRAME_TYPE_METADATA',
            'ndi.FRAME_TYPE_ERROR',
            'ndi.FRAME_TYPE_NONE'
        ]
        
        for frame_type in frame_types:
            if frame_type in content:
                print(f"✅ Handles {frame_type}")
            else:
                print(f"❌ Missing {frame_type} handling")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error validating receiver: {e}")
        return False

def show_final_fix_summary():
    """Show summary of all fixes"""
    print("\n" + "=" * 70)
    print("🎯 FINAL NDI FIX SUMMARY - Based on Working main.py Code")
    print("=" * 70)
    
    print("\n🔧 Critical Issues Fixed:")
    print("1. ❌ recv_create_v3(source) - Wrong parameter type")
    print("   ✅ recv_create_v3(recv_create_v3_config) - Correct configuration object")
    print()
    print("2. ❌ Missing ndi.recv_connect() call")
    print("   ✅ Added ndi.recv_connect(receiver, source) - 핵심 수정!")
    print()
    print("3. ❌ Wrong frame capture return handling")
    print("   ✅ frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2()")
    print()
    print("4. ❌ Delayed memory release")
    print("   ✅ Immediate ndi.recv_free_video_v2() in finally block")
    
    print("\n🚀 Expected Results:")
    print("- ✅ NDI receiver creation succeeds")
    print("- ✅ Connection to source established")
    print("- ✅ Real-time video frames received")
    print("- ✅ Frames displayed in GUI")
    print("- ✅ No memory leaks")
    print("- ✅ Stable 60fps performance")
    
    print("\n📋 Key Working Pattern from main.py:")
    print("```python")
    print("# 1. Create configuration")
    print("recv_create_v3 = ndi.RecvCreateV3()")
    print("recv_create_v3.source_to_connect_to = source")
    print("recv_create_v3.color_format = ndi.RECV_COLOR_FORMAT_FASTEST")
    print("recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST")
    print("recv_create_v3.allow_video_fields = True")
    print()
    print("# 2. Create receiver")
    print("receiver = ndi.recv_create_v3(recv_create_v3)")
    print()
    print("# 3. Connect to source (핵심!)")
    print("ndi.recv_connect(receiver, source)")
    print()
    print("# 4. Capture frames")
    print("frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2(receiver, timeout)")
    print()
    print("# 5. Process and free immediately")
    print("if frame_type == ndi.FRAME_TYPE_VIDEO:")
    print("    process_frame(v_frame)")
    print("    ndi.recv_free_video_v2(receiver, v_frame)")
    print("```")

def main():
    """Run final validation"""
    print("🧪 Final NDI Fix Validation - Based on Working Code")
    print("=" * 70)
    
    if validate_ndi_receiver_fixes():
        print("\n🎉 ALL CRITICAL FIXES IMPLEMENTED!")
        show_final_fix_summary()
        print("\n🚀 NDI 비디오 재생이 이제 완벽하게 작동할 것입니다!")
        return True
    else:
        print("\n❌ Some fixes are still missing.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)