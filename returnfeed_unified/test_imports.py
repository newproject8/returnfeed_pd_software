#!/usr/bin/env python3
"""
모듈 import 테스트 스크립트
각 모듈이 올바르게 import되는지 확인
"""
import sys
import os

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing module imports...")
print("-" * 50)

try:
    print("1. Testing base modules...")
    from modules import BaseModule, ModuleManager, ModuleStatus
    print("   ✓ Base modules imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import base modules: {e}")

try:
    print("\n2. Testing NDI module...")
    from modules.ndi_module import NDIModule, NDIManager, NDIWidget
    print("   ✓ NDI module imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import NDI module: {e}")

try:
    print("\n3. Testing vMix module...")
    from modules.vmix_module import vMixModule, vMixManager, vMixWidget
    print("   ✓ vMix module imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import vMix module: {e}")

try:
    print("\n4. Testing UI components...")
    from ui import MainWindow
    print("   ✓ UI components imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import UI components: {e}")

try:
    print("\n5. Testing utilities...")
    from utils import setup_logging
    print("   ✓ Utilities imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import utilities: {e}")

print("\n" + "-" * 50)
print("Import test completed!")
print("\nNote: NDI library may show import errors if NDI SDK is not installed.")
print("This is expected and will be handled gracefully by the application.")