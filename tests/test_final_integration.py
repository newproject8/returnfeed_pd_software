#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 통합 테스트 스크립트
모든 오류 수정 후 전체 기능 검증
"""

import sys
import os
import time
import logging

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """모든 필수 모듈 임포트 테스트"""
    print("\n=== 모듈 임포트 테스트 ===")
    
    results = []
    
    # 기본 모듈
    modules = [
        ("PyQt6", "from PyQt6.QtWidgets import QApplication"),
        ("NDIlib", "import NDIlib as ndi"),
        ("numpy", "import numpy as np"),
        ("websockets", "import websockets"),
        ("psutil", "import psutil"),
    ]
    
    for name, import_str in modules:
        try:
            exec(import_str)
            print(f"✓ {name} 임포트 성공")
            results.append((name, True))
        except ImportError as e:
            print(f"✗ {name} 임포트 실패: {e}")
            results.append((name, False))
    
    # PD 앱 모듈
    pd_modules = [
        ("pd_app.utils", "from pd_app.utils import setup_logger"),
        ("pd_app.core", "from pd_app.core import NDIManager, VMixManager, SRTManager, AuthManager"),
        ("pd_app.ui", "from pd_app.ui import MainWindow"),
        ("pd_app.network", "from pd_app.network import WebSocketClient"),
    ]
    
    for name, import_str in pd_modules:
        try:
            exec(import_str)
            print(f"✓ {name} 임포트 성공")
            results.append((name, True))
        except ImportError as e:
            print(f"✗ {name} 임포트 실패: {e}")
            results.append((name, False))
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n결과: {success_count}/{len(results)} 모듈 임포트 성공")
    
    return success_count == len(results)

def test_widget_creation():
    """위젯 생성 테스트"""
    print("\n=== 위젯 생성 테스트 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 각 위젯 테스트
        widgets_to_test = [
            ("LoginWidget", "from pd_app.ui import LoginWidget; from pd_app.core import AuthManager; w = LoginWidget(AuthManager())"),
            ("NDIWidget", "from pd_app.ui import NDIWidget; from pd_app.core import NDIManager; w = NDIWidget(NDIManager())"),
            ("TallyWidget", "from pd_app.ui import TallyWidget; from pd_app.core import VMixManager; w = TallyWidget(VMixManager())"),
            ("SRTWidget", "from pd_app.ui import SRTWidget; from pd_app.core import SRTManager, AuthManager; w = SRTWidget(SRTManager(), AuthManager())"),
        ]
        
        results = []
        for widget_name, test_code in widgets_to_test:
            try:
                exec(test_code)
                print(f"✓ {widget_name} 생성 성공")
                results.append((widget_name, True))
            except Exception as e:
                print(f"✗ {widget_name} 생성 실패: {e}")
                results.append((widget_name, False))
        
        app.quit()
        
        success_count = sum(1 for _, success in results if success)
        print(f"\n결과: {success_count}/{len(results)} 위젯 생성 성공")
        
        return success_count == len(results)
        
    except Exception as e:
        print(f"✗ 위젯 테스트 실패: {e}")
        return False

def test_main_window():
    """메인 윈도우 테스트"""
    print("\n=== 메인 윈도우 테스트 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from pd_app.ui import MainWindow
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 메인 윈도우 생성
        main_window = MainWindow()
        print("✓ 메인 윈도우 생성 성공")
        
        # 탭 위젯 확인
        if hasattr(main_window, 'tab_widget'):
            tab_count = main_window.tab_widget.count()
            print(f"✓ 탭 위젯 존재: {tab_count} 개의 탭")
        else:
            print("✗ 탭 위젯이 없습니다")
            return False
        
        # 관리자 확인
        managers = ['ndi_manager', 'vmix_manager', 'srt_manager', 'auth_manager', 'ws_client']
        for manager in managers:
            if hasattr(main_window, manager):
                print(f"✓ {manager} 초기화됨")
            else:
                print(f"✗ {manager} 없음")
        
        # 탭 변경 테스트 (오류 발생 여부 확인)
        print("\n탭 변경 테스트:")
        for i in range(min(tab_count, 4)):
            try:
                main_window.tab_widget.setCurrentIndex(i)
                tab_name = main_window.tab_widget.tabText(i)
                print(f"✓ 탭 {i} ({tab_name}) 변경 성공")
                time.sleep(0.1)  # 짧은 대기
            except Exception as e:
                print(f"✗ 탭 {i} 변경 실패: {e}")
        
        app.quit()
        
        print("\n✓ 메인 윈도우 테스트 완료")
        return True
        
    except Exception as e:
        print(f"✗ 메인 윈도우 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """오류 처리 테스트"""
    print("\n=== 오류 처리 테스트 ===")
    
    try:
        from pd_app.utils import setup_logger
        logger = setup_logger()
        
        # 로거 테스트
        logger.info("정보 메시지 테스트")
        logger.warning("경고 메시지 테스트")
        logger.error("오류 메시지 테스트")
        print("✓ 로거 정상 작동")
        
        # 크래시 핸들러 테스트
        try:
            from pd_app.utils.crash_handler import install_handler
            install_handler()
            print("✓ 크래시 핸들러 설치 성공")
        except:
            print("! 크래시 핸들러 사용 불가")
        
        return True
        
    except Exception as e:
        print(f"✗ 오류 처리 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("="*60)
    print("PD 통합 소프트웨어 최종 통합 테스트")
    print("="*60)
    
    # 시스템 정보
    try:
        import platform
        print(f"\n시스템 정보:")
        print(f"Python: {sys.version}")
        print(f"Platform: {platform.platform()}")
    except:
        pass
    
    # 테스트 실행
    tests = [
        ("모듈 임포트", test_imports),
        ("오류 처리", test_error_handling),
        ("위젯 생성", test_widget_creation),
        ("메인 윈도우", test_main_window),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 최종 결과
    print("\n" + "="*60)
    print("최종 테스트 결과")
    print("="*60)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for test_name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{test_name}: {status}")
    
    print(f"\n전체: {success_count}/{total_count} 테스트 통과")
    
    if success_count == total_count:
        print("\n✅ 모든 테스트 통과! 프로그램이 정상적으로 작동할 준비가 되었습니다.")
        print("\n실행 명령:")
        print("venv\\Scripts\\python.exe main_v2_optimized.py")
    else:
        print("\n❌ 일부 테스트 실패. 위의 오류를 확인하세요.")
    
    return success_count == total_count

if __name__ == '__main__':
    sys.exit(0 if main() else 1)