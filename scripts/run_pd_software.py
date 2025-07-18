#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 실행 스크립트
High DPI 및 환경 설정을 처리하는 안전한 실행 파일
"""

import sys
import os

# 환경 변수로 Qt High DPI 설정
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

# Windows에서 DPI 인식 설정
if sys.platform == "win32":
    try:
        import ctypes
        # Windows DPI 인식 설정
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 메인 애플리케이션 실행
try:
    from main_integrated import main
    main()
except Exception as e:
    print(f"애플리케이션 실행 오류: {e}")
    input("종료하려면 Enter 키를 누르세요...")
    sys.exit(1)