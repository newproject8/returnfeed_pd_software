#!/usr/bin/env python3
"""
스타트업 테스트 스크립트
애플리케이션이 정상적으로 시작되는지 확인
"""
import sys
import os

# 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("Testing application startup...")
print("-" * 50)

# 1. Import 테스트
try:
    print("1. Testing imports...")
    from ui.main_window import MainWindow
    from utils.logger import setup_logging
    print("   ✓ Main imports successful")
except Exception as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# 2. 로깅 설정 테스트
try:
    print("\n2. Testing logging setup...")
    setup_logging(log_dir="test_logs", log_level="DEBUG")
    print("   ✓ Logging setup successful")
except Exception as e:
    print(f"   ✗ Logging setup error: {e}")

# 3. Qt 애플리케이션 생성 테스트
try:
    print("\n3. Testing Qt application creation...")
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    
    # High DPI 설정
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    print("   ✓ Qt application created successfully")
    
    # 4. 메인 윈도우 생성 테스트
    print("\n4. Testing main window creation...")
    window = MainWindow()
    print("   ✓ Main window created successfully")
    
    print("\n" + "-" * 50)
    print("All startup tests passed! Application is ready to run.")
    
    # 정리
    app.quit()
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)