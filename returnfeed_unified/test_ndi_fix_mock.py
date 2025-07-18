#!/usr/bin/env python3
"""
Test script to validate NDI connection fixes with PyQt6 mocking
Tests the source object passing mechanism without requiring PyQt6
"""

import sys
import os
from unittest.mock import MagicMock, patch

# Mock PyQt6 modules before importing our code
sys.modules['PyQt6'] = MagicMock()
sys.modules['PyQt6.QtCore'] = MagicMock()
sys.modules['PyQt6.QtWidgets'] = MagicMock()
sys.modules['PyQt6.QtGui'] = MagicMock()

# Mock QObject and related classes
mock_qobject = MagicMock()
mock_qthread = MagicMock()
mock_pyqt_signal = MagicMock()

sys.modules['PyQt6.QtCore'].QObject = mock_qobject
sys.modules['PyQt6.QtCore'].QThread = mock_qthread
sys.modules['PyQt6.QtCore'].pyqtSignal = mock_pyqt_signal
sys.modules['PyQt6.QtCore'].QTimer = MagicMock()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ndi_source_creation():
    """Test NDISource object creation with source object storage"""
    print("🔍 Testing NDISource creation with source object...")
    
    try:
        # Import after mocking
        from modules.ndi_module.ndi_manager import NDISource
        
        # Mock NDI source object
        class MockNDISource:
            def __init__(self, name):
                self.name = name
                self.address = "192.168.1.100"
                
        mock_source = MockNDISource("NEWPROJECT (vMix - Output 1)")
        
        # Test NDISource creation with source object
        ndi_source = NDISource("NEWPROJECT (vMix - Output 1)", "192.168.1.100", ndi_source_obj=mock_source)
        
        assert ndi_source.name == "NEWPROJECT (vMix - Output 1)"
        assert ndi_source.address == "192.168.1.100"
        assert ndi_source.ndi_source_obj == mock_source
        
        print("✅ NDISource stores source object correctly")
        return True
        
    except Exception as e:
        print(f"❌ NDISource test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manager_source_object_retrieval():
    """Test NDIManager get_source_object method"""
    print("\n🔍 Testing NDIManager.get_source_object...")
    
    try:
        from modules.ndi_module.ndi_manager import NDIManager, NDISource
        
        # Create manager instance
        manager = NDIManager()
        
        # Mock source objects
        class MockNDISource:
            def __init__(self, name):
                self.name = name
                
        mock_source1 = MockNDISource("NEWPROJECT (vMix - Output 1)")
        mock_source2 = MockNDISource("Test Source 2")
        
        # Create NDISource instances with mock objects
        source1 = NDISource("NEWPROJECT (vMix - Output 1)", "", ndi_source_obj=mock_source1)
        source2 = NDISource("Test Source 2", "", ndi_source_obj=mock_source2)
        
        # Manually set sources list (simulating discovered sources)
        manager.sources = [source1, source2]
        
        # Test retrieval
        retrieved1 = manager.get_source_object("NEWPROJECT (vMix - Output 1)")
        retrieved2 = manager.get_source_object("Test Source 2")
        retrieved_none = manager.get_source_object("Non-existent Source")
        
        assert retrieved1 == mock_source1
        assert retrieved2 == mock_source2
        assert retrieved_none is None
        
        print("✅ NDIManager.get_source_object works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_receiver_signature():
    """Test NDIReceiver connect_to_source method signature"""
    print("\n🔍 Testing NDIReceiver method signature...")
    
    try:
        from modules.ndi_module.ndi_receiver import NDIReceiver
        
        # Check method signature
        import inspect
        sig = inspect.signature(NDIReceiver.connect_to_source)
        params = list(sig.parameters.keys())
        
        # Should have self, source_name, and source_object parameters
        expected_params = ['self', 'source_name', 'source_object']
        for param in expected_params:
            assert param in params, f"Missing parameter: {param}"
        
        # Check that source_object has default value of None
        source_object_param = sig.parameters['source_object']
        assert source_object_param.default is None, "source_object should default to None"
        
        print("✅ NDIReceiver.connect_to_source signature is correct")
        return True
        
    except Exception as e:
        print(f"❌ Receiver signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_integration():
    """Test that NDIModule can retrieve and pass source objects"""
    print("\n🔍 Testing NDIModule integration...")
    
    try:
        from modules.ndi_module.ndi_module import NDIModule
        from modules.ndi_module.ndi_manager import NDISource
        
        # Create module instance
        module = NDIModule()
        
        # Mock source object
        class MockNDISource:
            def __init__(self, name):
                self.name = name
                
        mock_source = MockNDISource("NEWPROJECT (vMix - Output 1)")
        
        # Set up manager with source
        source = NDISource("NEWPROJECT (vMix - Output 1)", "", ndi_source_obj=mock_source)
        module.manager.sources = [source]
        
        # Test that manager can retrieve the source object
        retrieved = module.manager.get_source_object("NEWPROJECT (vMix - Output 1)")
        assert retrieved == mock_source
        
        print("✅ NDIModule integration works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Module integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_code_changes():
    """Validate that the specific code changes were made correctly"""
    print("\n🔍 Validating specific code changes...")
    
    try:
        # Check ndi_manager.py for the source object storage fix
        with open('modules/ndi_module/ndi_manager.py', 'r') as f:
            manager_code = f.read()
            
        # Should contain the fixed line for storing source objects
        assert 'ndi_source_obj=source' in manager_code, "Missing source object storage in _scan_sources"
        print("✅ NDI Manager stores source objects correctly")
        
        # Should contain the get_source_object method
        assert 'def get_source_object(self, source_name: str):' in manager_code, "Missing get_source_object method"
        print("✅ NDI Manager has get_source_object method")
        
        # Check ndi_receiver.py for the source_object parameter
        with open('modules/ndi_module/ndi_receiver.py', 'r') as f:
            receiver_code = f.read()
            
        assert 'source_object=None' in receiver_code, "Missing source_object parameter"
        assert 'if source_object is not None:' in receiver_code, "Missing source object usage logic"
        print("✅ NDI Receiver accepts source objects")
        
        # Check ndi_module.py for passing source object
        with open('modules/ndi_module/ndi_module.py', 'r') as f:
            module_code = f.read()
            
        assert 'source_object = self.manager.get_source_object(source_name)' in module_code, "Missing source object retrieval"
        assert 'self.receiver.connect_to_source(source_name, source_object)' in module_code, "Missing source object passing"
        print("✅ NDI Module passes source objects to receiver")
        
        return True
        
    except Exception as e:
        print(f"❌ Code validation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing NDI Connection Fix (Mock Version)")
    print("=" * 60)
    
    tests = [
        test_ndi_source_creation,
        test_manager_source_object_retrieval,
        test_receiver_signature,
        test_module_integration,
        validate_code_changes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! NDI connection fix is working correctly.")
        print("\n📋 Summary of fixes implemented:")
        print("✅ NDISource now stores actual NDI source objects (ndi_source_obj parameter)")
        print("✅ NDIManager._scan_sources() updated to pass source objects")
        print("✅ NDIManager.get_source_object() method added for retrieval")
        print("✅ NDIReceiver.connect_to_source() accepts optional source_object parameter")
        print("✅ NDIModule._on_connect_requested() passes source objects to receiver")
        print("\n🔧 What this fixes:")
        print("❌ Before: Receiver created new finder and searched for sources again")
        print("✅ After: Receiver uses already-discovered source objects directly")
        print("\n🚀 The 'Source not found' error should now be resolved!")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)