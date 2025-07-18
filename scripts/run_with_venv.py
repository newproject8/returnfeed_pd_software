#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가상환경을 사용하여 main_integrated.py 실행
"""

import subprocess
import sys
import os
import platform

print("=" * 80)
print("PD 통합 소프트웨어 실행 (가상환경 사용)")
print("=" * 80)

# 시스템 정보
print(f"\n시스템 정보:")
print(f"  - 플랫폼: {platform.system()}")
print(f"  - Python: {sys.version}")
print(f"  - 작업 디렉토리: {os.getcwd()}")

# Windows에서 실행 중인지 확인
is_wsl = 'microsoft' in platform.uname().release.lower()
print(f"  - WSL 환경: {is_wsl}")

if is_wsl:
    print("\nWSL 환경에서는 GUI 애플리케이션을 직접 실행할 수 없습니다.")
    print("Windows에서 다음 명령을 실행하세요:")
    print("\n1. 가상환경 활성화:")
    print("   venv\\Scripts\\activate")
    print("\n2. 프로그램 실행:")
    print("   python main_integrated.py")
    print("\n또는 한 줄로:")
    print("   venv\\Scripts\\python.exe main_integrated.py")
else:
    # Windows나 다른 환경에서 실행
    venv_python = None
    
    # 가상환경 Python 찾기
    if os.path.exists("venv/Scripts/python.exe"):
        venv_python = "venv/Scripts/python.exe"
    elif os.path.exists("venv_py312/Scripts/python.exe"):
        venv_python = "venv_py312/Scripts/python.exe"
    elif os.path.exists("venv/bin/python"):
        venv_python = "venv/bin/python"
    
    if venv_python:
        print(f"\n가상환경 Python 발견: {venv_python}")
        print("\nmain_integrated.py 실행 중...")
        
        try:
            subprocess.run([venv_python, "main_integrated.py"])
        except Exception as e:
            print(f"\n실행 오류: {e}")
    else:
        print("\n가상환경을 찾을 수 없습니다.")
        print("다음 명령으로 가상환경을 생성하세요:")
        print("  python -m venv venv")

print("\n" + "=" * 80)