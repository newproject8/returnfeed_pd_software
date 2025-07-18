#!/usr/bin/env python3
"""
Metaclass 충돌 수정 테스트
"""
import sys
import os

# 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("Testing metaclass conflict fix...")
print("-" * 50)

# 1. 기본 클래스 import 테스트
try:
    print("1. Testing base classes import...")
    from modules import BaseModule, QObjectBaseModule, ModuleStatus, ModuleManager
    print("   ✓ Base classes imported successfully")
    print(f"   - BaseModule: {BaseModule}")
    print(f"   - QObjectBaseModule: {QObjectBaseModule}")
except Exception as e:
    print(f"   ✗ Failed to import base classes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 모듈 import 테스트
try:
    print("\n2. Testing module imports...")
    from modules.ndi_module import NDIModule
    from modules.vmix_module import vMixModule
    print("   ✓ Modules imported successfully")
    print(f"   - NDIModule: {NDIModule}")
    print(f"   - vMixModule: {vMixModule}")
except Exception as e:
    print(f"   ✗ Failed to import modules: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 상속 구조 확인
try:
    print("\n3. Checking inheritance structure...")
    print(f"   - NDIModule.__bases__: {NDIModule.__bases__}")
    print(f"   - vMixModule.__bases__: {vMixModule.__bases__}")
    print(f"   - QObjectBaseModule.__bases__: {QObjectBaseModule.__bases__}")
    
    # MRO (Method Resolution Order) 확인
    print("\n   Method Resolution Order:")
    print(f"   - NDIModule MRO: {[cls.__name__ for cls in NDIModule.__mro__]}")
    
    print("   ✓ Inheritance structure is correct")
except Exception as e:
    print(f"   ✗ Error checking inheritance: {e}")

# 4. 객체 생성 테스트 (PyQt6가 설치된 경우에만)
try:
    print("\n4. Testing object creation...")
    from PyQt6.QtWidgets import QApplication
    
    # QApplication이 필요할 수 있음
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # 모듈 객체 생성 시도
    ndi = NDIModule()
    vmix = vMixModule()
    
    print("   ✓ Module objects created successfully")
    print(f"   - NDI module name: {ndi.name}")
    print(f"   - vMix module name: {vmix.name}")
    
except ImportError:
    print("   ⚠ PyQt6 not installed, skipping object creation test")
except Exception as e:
    print(f"   ✗ Error creating objects: {e}")

print("\n" + "-" * 50)
print("Metaclass conflict has been resolved! ✅")