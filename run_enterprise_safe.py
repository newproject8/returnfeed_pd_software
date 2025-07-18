#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Edition 안전 실행 스크립트
NDI 없이도 실행 가능한 버전
"""

import os
import sys
import subprocess
import platform

def check_requirements():
    """필수 요구사항 확인"""
    print("요구사항 확인 중...")
    
    # Python 버전 확인
    print(f"Python 버전: {sys.version}")
    
    # 모듈 확인
    required_modules = ['PyQt6', 'numpy', 'requests']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} 설치됨")
        except ImportError:
            print(f"✗ {module} 없음")
            missing.append(module)
    
    # NDI 확인 (옵션)
    try:
        import ndi
        print("✓ NDI 설치됨")
    except ImportError:
        print("! NDI 없음 (선택사항)")
    
    return missing

def find_python_executable():
    """가상환경의 Python 실행 파일 찾기"""
    system = platform.system()
    
    # 가능한 가상환경 경로들
    venv_paths = ['venv', 'venv_py312', '.venv']
    
    for venv_path in venv_paths:
        if system == 'Windows':
            # Windows
            python_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:
            # Linux/Mac
            python_exe = os.path.join(venv_path, 'bin', 'python')
            
        if os.path.exists(python_exe):
            return python_exe
    
    # 가상환경을 찾을 수 없으면 시스템 Python 사용
    return sys.executable

def main():
    """메인 실행 함수"""
    print("="*60)
    print("PD 통합 소프트웨어 - Enterprise Edition (Safe Mode)")
    print("="*60)
    
    # Python 실행 파일 찾기
    python_exe = find_python_executable()
    print(f"\nPython 경로: {python_exe}")
    
    # 요구사항 확인
    missing = check_requirements()
    if missing:
        print(f"\n경고: 다음 모듈이 없습니다: {', '.join(missing)}")
        print("설치 명령: pip install " + ' '.join(missing))
        response = input("\n계속하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\n실행 중...\n")
    
    # 실행할 스크립트 경로
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'enterprise',
        'main_enterprise_fixed.py'
    )
    
    # 환경 변수 설정
    env = os.environ.copy()
    
    # Windows에서 UTF-8 설정
    if platform.system() == 'Windows':
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUNBUFFERED'] = '1'
    
    # NDI 비활성화 옵션
    env['DISABLE_NDI'] = 'true'
    
    try:
        # 스크립트 실행
        subprocess.run([python_exe, script_path], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n오류 발생: {e}")
        print("\n로그 파일을 확인하세요:")
        print("- enterprise_fixed/pd_app_*.log")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n사용자가 프로그램을 종료했습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()