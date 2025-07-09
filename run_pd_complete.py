#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 완전 실행 스크립트
모든 문제 해결 및 자동 설정
"""

import sys
import os
import subprocess
import locale

print("=" * 60)
print("PD 통합 소프트웨어 v1.0.0 - 완전 실행 스크립트")
print("=" * 60)
print()

# 1. Python 인코딩 설정
if sys.platform == "win32":
    # Windows 콘솔 UTF-8 설정
    os.system("chcp 65001 > nul 2>&1")
    
    # Python 기본 인코딩 설정
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # 로케일 설정
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Korean_Korea.949')
        except:
            pass

# 2. 환경 변수 설정
os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
os.environ['QT_SCALE_FACTOR_ROUNDING_POLICY'] = 'PassThrough'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 3. Windows DPI 설정
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

# 4. 의존성 확인
print("의존성 확인 중...")
missing_packages = []

# 필수 패키지 목록
required_packages = {
    'PyQt6': 'PyQt6',
    'numpy': 'numpy',
    'websockets': 'websockets',
    'requests': 'requests',
    'pyqtgraph': 'pyqtgraph'
}

for module_name, package_name in required_packages.items():
    try:
        __import__(module_name)
        print(f"✓ {module_name} 설치됨")
    except ImportError:
        print(f"✗ {module_name} 미설치")
        missing_packages.append(package_name)

# 선택적 패키지
optional_packages = {
    'cv2': 'opencv-python',
    'ffmpeg': 'ffmpeg-python',
    'NDIlib': 'NDI SDK (별도 설치 필요)'
}

print("\n선택적 패키지:")
for module_name, package_name in optional_packages.items():
    try:
        __import__(module_name)
        print(f"✓ {module_name} 설치됨")
    except ImportError:
        print(f"! {module_name} 미설치 ({package_name})")

# 5. 필수 패키지 설치 제안
if missing_packages:
    print(f"\n필수 패키지가 {len(missing_packages)}개 누락되었습니다.")
    response = input("지금 설치하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        for package in missing_packages:
            print(f"\n{package} 설치 중...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} 설치 완료")
            except:
                print(f"✗ {package} 설치 실패")
        print("\n모든 패키지 설치 완료. 프로그램을 다시 시작하세요.")
        input("Enter 키를 눌러 종료...")
        sys.exit(0)

# 6. NDI 확인
print("\nNDI 상태 확인...")
try:
    import NDIlib
    print("✓ NDI SDK 사용 가능")
except ImportError:
    print("! NDI SDK를 찾을 수 없습니다 (시뮬레이터 모드로 실행됩니다)")
    print("  실제 NDI 기능을 사용하려면:")
    print("  1. https://ndi.tv/sdk/ 에서 NDI SDK 설치")
    print("  2. python install_ndi.py 실행")

# 7. 설정 파일 확인
print("\n설정 파일 확인...")
settings_path = "config/settings.json"
if os.path.exists(settings_path):
    print("✓ 설정 파일 존재")
    # 파일 무결성 확인
    try:
        import json
        with open(settings_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print("✓ 설정 파일 정상")
    except:
        print("✗ 설정 파일 손상 - 복구 중...")
        # 백업에서 복구 시도
        backup_path = settings_path + ".backup"
        if os.path.exists(backup_path):
            import shutil
            shutil.copy2(backup_path, settings_path)
            print("✓ 백업에서 복구 완료")
else:
    print("! 설정 파일 없음 (기본값 사용)")

print("\n" + "=" * 60)
print("애플리케이션 시작 중...")
print("=" * 60 + "\n")

# 8. 메인 애플리케이션 실행
try:
    from main_integrated import main
    main()
except ImportError as e:
    print(f"\n임포트 오류: {e}")
    print("\n해결 방법:")
    print("1. pip install -r requirements.txt")
    print("2. 프로젝트 경로가 올바른지 확인")
except Exception as e:
    print(f"\n예상치 못한 오류: {e}")
    import traceback
    traceback.print_exc()
finally:
    input("\n프로그램이 종료되었습니다. Enter 키를 눌러 창을 닫으세요...")