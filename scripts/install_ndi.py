#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NDI Python Wrapper 설치 스크립트
"""

import os
import sys
import subprocess
import platform

def install_ndi_python():
    """NDI Python wrapper 설치"""
    print("=" * 60)
    print("NDI Python Wrapper 설치 스크립트")
    print("=" * 60)
    print()
    
    # 시스템 정보
    print(f"운영체제: {platform.system()}")
    print(f"Python 버전: {sys.version}")
    print()
    
    # NDI SDK 확인
    if platform.system() == "Windows":
        ndi_path = r"C:\Program Files\NDI\NDI 6 SDK"
        if not os.path.exists(ndi_path):
            print("NDI SDK가 설치되지 않았습니다!")
            print("   https://ndi.tv/sdk/ 에서 NDI SDK를 먼저 설치하세요.")
            print()
            input("Enter 키를 눌러 종료...")
            return
        else:
            print("NDI SDK 설치 확인")
    
    print("\nNDI Python wrapper 옵션:")
    print("1. ndi-python (공식, 권장)")
    print("2. PyNDI (대안)")
    print("3. 수동 설치 안내")
    print()
    
    choice = "1"
    
    if choice == "1":
        print("\nndi-python 설치 중...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ndi-python"])
            print("\nndi-python 설치 완료!")
            
            # 테스트
            print("\n설치 테스트 중...")
            test_code = """
import ndi
print("NDI 버전:", ndi.version())
ndi.initialize()
print("NDI 초기화 성공!")
"""
            subprocess.run([sys.executable, "-c", test_code])
            
        except Exception as e:
            print(f"\n설치 실패: {e}")
            print("\n대안: PyNDI를 시도해보세요 (옵션 2)")
    
    elif choice == "2":
        print("\nPyNDI 설치 중...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyNDI"])
            print("\nPyNDI 설치 완료!")
            print("\n주의: PyNDI는 NDIlib와 다른 API를 사용합니다.")
            print("코드 수정이 필요할 수 있습니다.")
            
        except Exception as e:
            print(f"\n설치 실패: {e}")
    
    elif choice == "3":
        print("\n수동 설치 방법:")
        print("1. NDI SDK 설치 (https://ndi.tv/sdk/)")
        print("2. NDI Python binding 다운로드")
        print("   - https://github.com/buresu/ndi-python")
        print("   - 또는 https://github.com/nocarryr/cyndilib")
        print("3. 빌드 및 설치")
        print("   python setup.py install")
    
    print("\n" + "=" * 60)
    # input("Enter 키를 눌러 종료...")

if __name__ == "__main__":
    install_ndi_python()