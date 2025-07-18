#!/usr/bin/env python3
"""
NDI API 테스트 및 함수명 확인
"""
import sys
import os

# NDI DLL 경로 설정
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

if sys.platform == "win32" and hasattr(os, 'add_dll_directory'):
    try:
        if os.path.isdir(NDI_SDK_DLL_PATH):
            os.add_dll_directory(NDI_SDK_DLL_PATH)
            print(f"✅ Added to DLL search path: {NDI_SDK_DLL_PATH}")
    except Exception as e:
        print(f"⚠️  Warning: Failed to add NDI SDK DLL path: {e}")

print("🔍 Testing NDI API functions...")
print("-" * 50)

try:
    import NDIlib as ndi
    print("✅ NDIlib imported successfully")
    
    # NDI 라이브러리의 사용 가능한 함수들 확인
    print("\n📋 Available NDI functions:")
    ndi_functions = [attr for attr in dir(ndi) if not attr.startswith('_')]
    for func in sorted(ndi_functions):
        print(f"   - {func}")
    
    # 특별히 찾는 함수들 확인
    print("\n🎯 Checking specific functions:")
    
    functions_to_check = [
        'initialize', 'destroy',
        'find_create', 'find_destroy', 'find_get_current_sources',
        'Find_create', 'Find_destroy', 'Find_get_current_sources',
        'create_find', 'create_finder', 'finder_create',
        'get_sources', 'discover_sources'
    ]
    
    for func_name in functions_to_check:
        if hasattr(ndi, func_name):
            print(f"   ✅ {func_name} - FOUND")
        else:
            print(f"   ❌ {func_name} - NOT FOUND")
    
    # NDI 초기화 테스트
    print("\n🚀 Testing NDI initialization...")
    if hasattr(ndi, 'initialize'):
        if ndi.initialize():
            print("   ✅ NDI initialized successfully")
            
            # Finder 생성 테스트
            print("\n🔍 Testing finder functions...")
            finder = None
            
            # 여러 가능한 함수명 시도
            finder_functions = ['find_create', 'Find_create', 'create_find', 'finder_create']
            for func_name in finder_functions:
                if hasattr(ndi, func_name):
                    try:
                        func = getattr(ndi, func_name)
                        finder = func()
                        if finder:
                            print(f"   ✅ {func_name}() worked! Finder created.")
                            break
                    except Exception as e:
                        print(f"   ❌ {func_name}() failed: {e}")
            
            if finder:
                print("   🎉 NDI finder successfully created!")
                
                # 소스 검색 테스트
                source_functions = ['find_get_current_sources', 'Find_get_current_sources', 'get_sources']
                for func_name in source_functions:
                    if hasattr(ndi, func_name):
                        try:
                            func = getattr(ndi, func_name)
                            sources = func(finder)
                            print(f"   ✅ {func_name}() worked! Found {len(sources) if sources else 0} sources.")
                            break
                        except Exception as e:
                            print(f"   ❌ {func_name}() failed: {e}")
                
                # Finder 정리
                destroy_functions = ['find_destroy', 'Find_destroy', 'destroy_find']
                for func_name in destroy_functions:
                    if hasattr(ndi, func_name):
                        try:
                            func = getattr(ndi, func_name)
                            func(finder)
                            print(f"   ✅ {func_name}() worked! Finder destroyed.")
                            break
                        except Exception as e:
                            print(f"   ❌ {func_name}() failed: {e}")
            else:
                print("   ❌ Could not create NDI finder with any function")
            
            # NDI 정리
            if hasattr(ndi, 'destroy'):
                ndi.destroy()
                print("   ✅ NDI deinitialized")
        else:
            print("   ❌ NDI initialization failed")
    else:
        print("   ❌ No 'initialize' function found")
    
except ImportError as e:
    print(f"❌ Failed to import NDIlib: {e}")
    print("\n💡 Solutions:")
    print("1. Install ndi-python: pip install ndi-python")
    print("2. Install NDI SDK from: https://www.ndi.tv/sdk/")
    print("3. Restart your system after NDI SDK installation")
except Exception as e:
    print(f"❌ Error during NDI testing: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-" * 50)
print("NDI API analysis complete!")