#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Edition (Fixed) 실행 스크립트
가상환경을 자동으로 활성화하고 수정된 버전을 실행합니다
"""

import os
import sys
import subprocess
import platform

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
    print("PD 통합 소프트웨어 - Enterprise Edition (Fixed)")
    print("="*60)
    print("\n수정된 버전을 실행합니다...")
    print("- GUI 프리징 문제 해결")
    print("- NDI 표시 안정화")
    print("- 성능 최적화 적용")
    print("\n시작 중...\n")
    
    # Python 실행 파일 찾기
    python_exe = find_python_executable()
    print(f"Python 경로: {python_exe}")
    
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
    
    try:
        # 스크립트 실행
        subprocess.run([python_exe, script_path], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n사용자가 프로그램을 종료했습니다.")
    except Exception as e:
        print(f"\n예상치 못한 오류: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()