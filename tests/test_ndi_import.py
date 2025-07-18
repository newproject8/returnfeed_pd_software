#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NDI 임포트 테스트 스크립트
"""

import sys
import os
import io

# Windows 한글 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print(f"Python 버전: {sys.version}")
print(f"Python 경로: {sys.executable}")
print(f"시스템 경로:")
for path in sys.path:
    print(f"  - {path}")

# NDI DLL 경로 추가
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"
if sys.platform == "win32" and hasattr(os, 'add_dll_directory'):
    try:
        if os.path.isdir(NDI_SDK_DLL_PATH):
            os.add_dll_directory(NDI_SDK_DLL_PATH)
            print(f"\nDLL 경로 추가됨: {NDI_SDK_DLL_PATH}")
        else:
            print(f"\n경고: NDI SDK DLL 경로를 찾을 수 없음: {NDI_SDK_DLL_PATH}")
    except Exception as e:
        print(f"\n경고: NDI SDK DLL 경로 추가 실패: {e}")

# NDI 모듈 임포트 시도
print("\n=== NDI 모듈 임포트 시도 ===")

# 방법 1: NDIlib 직접 임포트
try:
    import NDIlib
    print("✅ NDIlib 임포트 성공!")
    print(f"   NDIlib 위치: {NDIlib.__file__ if hasattr(NDIlib, '__file__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ NDIlib 임포트 실패: {e}")

# 방법 2: ndi 임포트
try:
    import ndi
    print("✅ ndi 임포트 성공!")
    print(f"   ndi 위치: {ndi.__file__ if hasattr(ndi, '__file__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ ndi 임포트 실패: {e}")

# 방법 3: NDIlib as ndi
try:
    import NDIlib as ndi
    print("✅ NDIlib as ndi 임포트 성공!")
    
    # 초기화 테스트
    if hasattr(ndi, 'initialize'):
        result = ndi.initialize()
        print(f"   ndi.initialize() 결과: {result}")
    else:
        print("   경고: ndi.initialize() 메서드를 찾을 수 없음")
        
except Exception as e:
    print(f"❌ NDIlib 사용 실패: {e}")

# 설치된 패키지 확인
print("\n=== 설치된 NDI 관련 패키지 ===")
try:
    import pkg_resources
    installed_packages = [pkg.key for pkg in pkg_resources.working_set]
    ndi_packages = [pkg for pkg in installed_packages if 'ndi' in pkg.lower()]
    for pkg in ndi_packages:
        print(f"  - {pkg}")
except:
    print("  패키지 정보를 가져올 수 없음")

# site-packages 디렉토리 확인
print("\n=== site-packages 내 NDI 관련 파일 ===")
try:
    import site
    site_packages = site.getsitepackages()[0] if site.getsitepackages() else None
    if not site_packages:
        # 가상환경의 경우
        site_packages = os.path.join(sys.prefix, 'lib', 'site-packages')
    
    if os.path.exists(site_packages):
        for item in os.listdir(site_packages):
            if 'ndi' in item.lower():
                print(f"  - {item}")
                item_path = os.path.join(site_packages, item)
                if os.path.isdir(item_path):
                    for subitem in os.listdir(item_path)[:5]:  # 처음 5개만
                        print(f"    - {subitem}")
except Exception as e:
    print(f"  디렉토리 확인 실패: {e}")