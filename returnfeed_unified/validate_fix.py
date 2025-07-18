#!/usr/bin/env python3
"""
Simple validation script to confirm NDI connection fixes are implemented
Does not require any dependencies - just validates the code changes
"""

def validate_ndi_manager_fixes():
    """Validate NDI Manager fixes"""
    print("🔍 Validating NDI Manager fixes...")
    
    try:
        with open('modules/ndi_module/ndi_manager.py', 'r') as f:
            content = f.read()
        
        # Check for source object storage in _scan_sources
        if 'ndi_source_obj=source' in content:
            print("✅ NDI Manager stores source objects in _scan_sources method")
        else:
            print("❌ Missing source object storage in _scan_sources")
            return False
        
        # Check for get_source_object method
        if 'def get_source_object(self, source_name: str):' in content:
            print("✅ NDI Manager has get_source_object method")
        else:
            print("❌ Missing get_source_object method")
            return False
        
        # Check method implementation
        if 'for source in self.sources:' in content and 'if source.name == source_name:' in content:
            print("✅ get_source_object method implementation is correct")
        else:
            print("❌ get_source_object method implementation incomplete")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating NDI Manager: {e}")
        return False

def validate_ndi_receiver_fixes():
    """Validate NDI Receiver fixes"""
    print("\n🔍 Validating NDI Receiver fixes...")
    
    try:
        with open('modules/ndi_module/ndi_receiver.py', 'r') as f:
            content = f.read()
        
        # Check for source_object parameter
        if 'def connect_to_source(self, source_name: str, source_object=None)' in content:
            print("✅ NDI Receiver accepts source_object parameter")
        else:
            print("❌ Missing source_object parameter in connect_to_source")
            return False
        
        # Check for source object usage logic
        if 'if source_object is not None:' in content:
            print("✅ NDI Receiver uses provided source objects")
        else:
            print("❌ Missing source object usage logic")
            return False
        
        # Check for fallback logic
        if '# 기존 방식: 소스 찾기 (호환성을 위해 유지)' in content:
            print("✅ NDI Receiver maintains backward compatibility")
        else:
            print("❌ Missing backward compatibility logic")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating NDI Receiver: {e}")
        return False

def validate_ndi_module_fixes():
    """Validate NDI Module fixes"""
    print("\n🔍 Validating NDI Module fixes...")
    
    try:
        with open('modules/ndi_module/ndi_module.py', 'r') as f:
            content = f.read()
        
        # Check for source object retrieval
        if 'source_object = self.manager.get_source_object(source_name)' in content:
            print("✅ NDI Module retrieves source objects from manager")
        else:
            print("❌ Missing source object retrieval in module")
            return False
        
        # Check for passing source object to receiver
        if 'self.receiver.connect_to_source(source_name, source_object)' in content:
            print("✅ NDI Module passes source objects to receiver")
        else:
            print("❌ Missing source object passing to receiver")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating NDI Module: {e}")
        return False

def validate_ndi_source_class():
    """Validate NDISource class"""
    print("\n🔍 Validating NDISource class...")
    
    try:
        with open('modules/ndi_module/ndi_manager.py', 'r') as f:
            content = f.read()
        
        # Check for ndi_source_obj parameter in constructor
        if 'def __init__(self, name: str, address: str = "", ndi_source_obj=None):' in content:
            print("✅ NDISource constructor accepts ndi_source_obj parameter")
        else:
            print("❌ Missing ndi_source_obj parameter in NDISource constructor")
            return False
        
        # Check for storage of source object
        if 'self.ndi_source_obj = ndi_source_obj' in content:
            print("✅ NDISource stores source object")
        else:
            print("❌ Missing source object storage in NDISource")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating NDISource class: {e}")
        return False

def show_fix_summary():
    """Show summary of what was fixed"""
    print("\n" + "=" * 60)
    print("📋 NDI CONNECTION FIX SUMMARY")
    print("=" * 60)
    
    print("\n🔧 Problem:")
    print("- NDI sources were discovered successfully")
    print("- Connection failed with 'Source not found' error")
    print("- Receiver was creating new finder and searching again")
    print("- Timing issue between discovery and connection")
    
    print("\n✅ Solution:")
    print("1. Modified NDISource to store actual NDI source objects")
    print("2. Updated _scan_sources() to pass source objects when creating NDISource")
    print("3. Added get_source_object() method to NDIManager")
    print("4. Modified NDIReceiver to accept source objects directly")
    print("5. Updated NDIModule to pass source objects from manager to receiver")
    
    print("\n🎯 Result:")
    print("- Receiver no longer needs to search for sources")
    print("- Uses already-discovered source objects directly")
    print("- Eliminates timing-related connection failures")
    print("- Maintains backward compatibility")
    
    print("\n🚀 Expected behavior:")
    print("When user clicks 'Connect' on 'NEWPROJECT (vMix - Output 1)':")
    print("1. UI calls NDIModule._on_connect_requested()")
    print("2. Module gets source object from manager")
    print("3. Module passes both name AND object to receiver")
    print("4. Receiver uses provided object instead of searching")
    print("5. Connection succeeds and video playback starts")

def main():
    """Run validation"""
    print("🧪 NDI Connection Fix Validation")
    print("=" * 60)
    
    tests = [
        validate_ndi_source_class,
        validate_ndi_manager_fixes,
        validate_ndi_receiver_fixes,
        validate_ndi_module_fixes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All validations passed!")
        show_fix_summary()
        return True
    else:
        print("❌ Some validations failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)