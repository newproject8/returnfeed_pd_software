#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 디버그 실행기
에러 상세 정보 표시
"""

import sys
import os
import traceback

print("=" * 60)
print("PD 통합 소프트웨어 디버그 모드")
print("=" * 60)

# 환경 정보 출력
print(f"\nPython 버전: {sys.version}")
print(f"실행 경로: {os.getcwd()}")
print(f"플랫폼: {sys.platform}")

# PyQt6 버전 확인
try:
    from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
    print(f"Qt 버전: {QT_VERSION_STR}")
    print(f"PyQt6 버전: {PYQT_VERSION_STR}")
except ImportError as e:
    print(f"PyQt6 임포트 실패: {e}")
    print("PyQt6를 설치해주세요: pip install PyQt6")
    input("\n종료하려면 Enter 키를 누르세요...")
    sys.exit(1)

# High DPI 관련 환경 설정
print("\nHigh DPI 설정 적용 중...")
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

# Windows DPI 설정
if sys.platform == "win32":
    try:
        import ctypes
        awareness = ctypes.c_int()
        error = ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        print(f"현재 DPI Awareness: {awareness.value}")
        
        # DPI Aware 설정
        ctypes.windll.user32.SetProcessDPIAware()
        print("DPI Aware 설정 완료")
    except Exception as e:
        print(f"Windows DPI 설정 실패 (무시 가능): {e}")

# 메인 애플리케이션 실행
print("\n애플리케이션 시작 중...\n")
print("-" * 60)

try:
    # main_integrated 직접 임포트 전에 경로 확인
    main_file = os.path.join(os.path.dirname(__file__), 'main_integrated.py')
    if not os.path.exists(main_file):
        raise FileNotFoundError(f"main_integrated.py 파일을 찾을 수 없습니다: {main_file}")
    
    # 메인 함수 실행
    from main_integrated import main
    main()
    
except ImportError as e:
    print(f"\n임포트 오류: {e}")
    print("\n필요한 모듈이 설치되지 않았을 수 있습니다.")
    print("다음 명령으로 설치해주세요:")
    print("pip install -r requirements.txt")
    
except Exception as e:
    print(f"\n오류 발생: {type(e).__name__}: {e}")
    print("\n상세 오류 정보:")
    print("-" * 60)
    traceback.print_exc()
    print("-" * 60)
    
    # High DPI 관련 오류인 경우 추가 안내
    if "AA_EnableHighDpiScaling" in str(e):
        print("\n[High DPI 오류 해결 방법]")
        print("1. 이 디버그 스크립트를 사용하세요 (현재 사용 중)")
        print("2. 또는 run_pd_software.bat 파일을 실행하세요")
        print("3. 프로그램 속성에서 'DPI 설정 재정의' 옵션 활성화")
        
finally:
    print("\n프로그램이 종료되었습니다.")
    input("종료하려면 Enter 키를 누르세요...")