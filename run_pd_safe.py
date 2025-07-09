#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 안전 실행 스크립트
모든 환경 설정과 오류 처리 포함
"""

import sys
import os
import locale

# Python 인코딩 설정
if sys.platform == "win32":
    # Windows 콘솔 UTF-8 설정
    os.system("chcp 65001 > nul")
    
    # Python 기본 인코딩 설정
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # 로케일 설정
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Korean_Korea.949')
        except:
            pass

# 환경 변수로 Qt High DPI 설정
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'

# Windows에서 DPI 인식 설정
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

print("=" * 60)
print("PD 통합 소프트웨어 v1.0.0")
print("=" * 60)
print()

# ffmpeg-python 설치 확인
try:
    import ffmpeg
    print("✓ ffmpeg-python 설치됨")
except ImportError:
    print("! ffmpeg-python이 설치되지 않음 (SRT 스트리밍 제한)")
    print("  설치: pip install ffmpeg-python")
    print()

# websockets 설치 확인
try:
    import websockets
    print("✓ websockets 설치됨")
except ImportError:
    print("✗ websockets가 설치되지 않음!")
    print("  설치: pip install websockets")
    print()
    response = input("websockets를 지금 설치하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        os.system("pip install websockets")
        print("설치 완료. 프로그램을 다시 시작하세요.")
        input("Enter 키를 눌러 종료...")
        sys.exit(0)

# 메인 애플리케이션 실행
try:
    from main_integrated import main
    main()
except ImportError as e:
    print(f"\n임포트 오류: {e}")
    print("\n필요한 모듈이 설치되지 않았습니다.")
    print("다음 명령으로 모든 의존성을 설치하세요:")
    print("pip install -r requirements.txt")
    input("\nEnter 키를 눌러 종료...")
    sys.exit(1)
except Exception as e:
    print(f"\n오류 발생: {e}")
    import traceback
    traceback.print_exc()
    input("\nEnter 키를 눌러 종료...")
    sys.exit(1)