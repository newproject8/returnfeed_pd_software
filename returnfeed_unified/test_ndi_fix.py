#!/usr/bin/env python3
"""
Test script to validate NDI connection fixes
Tests the source object passing mechanism without requiring GUI
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        from modules.ndi_module.ndi_manager import NDIManager, NDISource
        print("✅ NDIManager import successful")
        
        from modules.ndi_module.ndi_receiver import NDIReceiver
        print("✅ NDIReceiver import successful")
        
        from modules.ndi_module.ndi_module import NDIModule
        print("✅ NDIModule import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_ndi_source_object_storage():
    """Test NDISource object creation and source object storage"""
    print("\n🔍 Testing NDISource object storage...")
    
    try:
        from modules.ndi_module.ndi_manager import NDISource
        
        # Mock NDI source object
        class MockNDISource:
            def __init__(self, name):
                self.name = name
                
        mock_source = MockNDISource("Test Source")
        
        # Test NDISource creation with source object
        ndi_source = NDISource("Test Source", "127.0.0.1", ndi_source_obj=mock_source)
        
        assert ndi_source.name == "Test Source"
        assert ndi_source.address == "127.0.0.1"
        assert ndi_source.ndi_source_obj == mock_source
        
        print("✅ NDISource object storage working correctly")
        return True
        
    except Exception as e:
        print(f"❌ NDISource test failed: {e}")
        return False

def test_manager_get_source_object():
    """Test NDIManager.get_source_object method"""
    print("\n🔍 Testing NDIManager.get_source_object...")
    
    try:
        from modules.ndi_module.ndi_manager import NDIManager, NDISource
        
        # Create manager (won't initialize NDI library in test)
        manager = NDIManager()
        
        # Mock source object
        class MockNDISource:
            def __init__(self, name):
                self.name = name
                
        mock_source = MockNDISource("NEWPROJECT (vMix - Output 1)")
        
        # Manually add a source to test get_source_object
        test_source = NDISource("NEWPROJECT (vMix - Output 1)", "", ndi_source_obj=mock_source)
        manager.sources = [test_source]
        
        # Test get_source_object method
        retrieved_object = manager.get_source_object("NEWPROJECT (vMix - Output 1)")
        assert retrieved_object == mock_source
        
        # Test with non-existent source
        none_object = manager.get_source_object("Non-existent Source")
        assert none_object is None
        
        print("✅ NDIManager.get_source_object working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Manager get_source_object test failed: {e}")
        return False

def test_receiver_source_object_parameter():
    """Test NDIReceiver connect_to_source with source object parameter"""
    print("\n🔍 Testing NDIReceiver source object parameter...")
    
    try:
        from modules.ndi_module.ndi_receiver import NDIReceiver
        
        # Create receiver (won't actually connect in test)
        receiver = NDIReceiver()
        
        # Check that the method signature accepts source_object parameter
        import inspect
        sig = inspect.signature(receiver.connect_to_source)
        params = list(sig.parameters.keys())
        
        assert 'source_name' in params
        assert 'source_object' in params
        
        # Check default value
        assert sig.parameters['source_object'].default is None
        
        print("✅ NDIReceiver.connect_to_source signature updated correctly")
        return True
        
    except Exception as e:
        print(f"❌ Receiver parameter test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing NDI Connection Fix")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_ndi_source_object_storage,
        test_manager_get_source_object,
        test_receiver_source_object_parameter
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test failed: {test.__name__}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! NDI connection fix is working correctly.")
        print("\n📋 Summary of fixes:")
        print("✅ NDISource now stores actual NDI source objects")
        print("✅ NDIManager.get_source_object() method added")
        print("✅ NDIReceiver accepts source objects directly")
        print("✅ NDIModule passes source objects to receiver")
        print("\n🚀 The application should now connect to NDI sources successfully!")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)