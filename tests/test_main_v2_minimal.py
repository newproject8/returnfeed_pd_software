#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_v2.py 기본 기능 테스트
"""

import sys
import os
import logging

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """필수 임포트 테스트"""
    print("=== 임포트 테스트 시작 ===")
    
    # PyQt6 테스트
    try:
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6 임포트 성공")
    except ImportError as e:
        print(f"✗ PyQt6 임포트 실패: {e}")
        return False
    
    # pd_app 모듈 테스트
    try:
        from pd_app.utils import setup_logger
        print("✓ pd_app.utils.setup_logger 임포트 성공")
    except ImportError as e:
        print(f"✗ pd_app.utils.setup_logger 임포트 실패: {e}")
        return False
    
    try:
        from pd_app.ui import MainWindow
        print("✓ pd_app.ui.MainWindow 임포트 성공")
    except ImportError as e:
        print(f"✗ pd_app.ui.MainWindow 임포트 실패: {e}")
        return False
    
    try:
        from pd_app.config import Settings
        print("✓ pd_app.config.Settings 임포트 성공")
    except ImportError as e:
        print(f"✗ pd_app.config.Settings 임포트 실패: {e}")
        return False
    
    # NDI 테스트 (선택적)
    try:
        import NDIlib as ndi
        print("✓ NDIlib 임포트 성공")
    except ImportError:
        print("! NDIlib 사용 불가 - 시뮬레이션 모드로 실행 가능")
    
    print("=== 임포트 테스트 완료 ===\n")
    return True

def test_logger():
    """로거 초기화 테스트"""
    print("=== 로거 테스트 시작 ===")
    try:
        from pd_app.utils import setup_logger
        logger = setup_logger()
        logger.info("로거 테스트 메시지")
        print("✓ 로거 초기화 성공")
    except Exception as e:
        print(f"✗ 로거 초기화 실패: {e}")
        return False
    print("=== 로거 테스트 완료 ===\n")
    return True

def test_settings():
    """설정 관리자 테스트"""
    print("=== 설정 테스트 시작 ===")
    try:
        from pd_app.config import Settings
        settings = Settings()
        print(f"✓ 설정 로드 성공")
        print(f"  - 앱 버전: {settings.get('app.version')}")
        print(f"  - WebSocket URL: {settings.get('server.websocket_url')}")
    except Exception as e:
        print(f"✗ 설정 로드 실패: {e}")
        return False
    print("=== 설정 테스트 완료 ===\n")
    return True

def test_ui_creation():
    """UI 생성 테스트 (윈도우 표시 없이)"""
    print("=== UI 생성 테스트 시작 ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from pd_app.ui import MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow()
        print("✓ 메인 윈도우 생성 성공")
        
        # 탭 위젯 확인
        if hasattr(window, 'tab_widget'):
            print(f"✓ 탭 위젯 존재: {window.tab_widget.count()} 개의 탭")
        
        # 매니저 확인
        if hasattr(window, 'ndi_manager'):
            print("✓ NDI 매니저 초기화됨")
        if hasattr(window, 'vmix_manager'):
            print("✓ vMix 매니저 초기화됨")
        if hasattr(window, 'srt_manager'):
            print("✓ SRT 매니저 초기화됨")
        
        app.quit()
        
    except Exception as e:
        print(f"✗ UI 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    print("=== UI 생성 테스트 완료 ===\n")
    return True

def main():
    """메인 테스트 함수"""
    print("\n" + "="*50)
    print("main_v2.py 기능 테스트")
    print("="*50 + "\n")
    
    # 테스트 실행
    tests = [
        ("임포트", test_imports),
        ("로거", test_logger),
        ("설정", test_settings),
        ("UI 생성", test_ui_creation)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 테스트 중 예외 발생: {e}")
            results.append((name, False))
    
    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        status = "✓ 성공" if result else "✗ 실패"
        print(f"{name}: {status}")
    
    print(f"\n전체: {success_count}/{total_count} 테스트 통과")
    
    if success_count == total_count:
        print("\n✅ 모든 테스트 통과! main_v2.py가 정상 작동할 준비가 되었습니다.")
    else:
        print("\n❌ 일부 테스트 실패. 위의 오류를 확인하세요.")
    
    return success_count == total_count

if __name__ == '__main__':
    sys.exit(0 if main() else 1)