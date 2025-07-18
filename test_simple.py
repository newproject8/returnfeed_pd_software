#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 - PyQt6 및 기본 모듈만 테스트
"""

import sys
import os

print("="*60)
print("간단한 테스트 시작")
print("="*60)

# 1. Python 정보
print(f"\nPython 버전: {sys.version}")
print(f"실행 경로: {sys.executable}")

# 2. 모듈 테스트
print("\n모듈 테스트:")

modules_to_test = [
    'PyQt6',
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'numpy',
    'requests',
    'websockets',
    'xml.etree.ElementTree'
]

for module in modules_to_test:
    try:
        __import__(module)
        print(f"✓ {module} - OK")
    except ImportError as e:
        print(f"✗ {module} - 실패: {e}")

# 3. 경로 테스트
print("\n경로 테스트:")
print(f"현재 디렉토리: {os.getcwd()}")
print(f"스크립트 디렉토리: {os.path.dirname(os.path.abspath(__file__))}")

# 4. 프로젝트 구조 확인
print("\n프로젝트 구조:")
for item in ['pd_app', 'enterprise', 'archive', 'config']:
    path = os.path.join(os.getcwd(), item)
    if os.path.exists(path):
        print(f"✓ {item}/ 존재")
    else:
        print(f"✗ {item}/ 없음")

# 5. 간단한 Qt 앱 테스트
print("\n간단한 Qt 앱 테스트:")
try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
    from PyQt6.QtCore import Qt
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("테스트")
    window.setGeometry(100, 100, 400, 300)
    
    label = QLabel("테스트 성공!", window)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.setCentralWidget(label)
    
    window.show()
    
    print("✓ Qt 앱 생성 성공")
    print("\n창이 표시되었나요? 종료하려면 창을 닫으세요.")
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"✗ Qt 앱 테스트 실패: {e}")
    import traceback
    traceback.print_exc()