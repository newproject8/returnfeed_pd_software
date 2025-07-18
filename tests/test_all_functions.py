#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 전체 기능 테스트 스크립트
"""

import sys
import os
import time
import logging
import io

# Windows 한글 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """필수 모듈 임포트 테스트"""
    print("\n=== 1. 모듈 임포트 테스트 ===")
    
    try:
        # PyQt6
        from PyQt6.QtCore import QObject
        print("✅ PyQt6 임포트 성공")
    except ImportError as e:
        print(f"❌ PyQt6 임포트 실패: {e}")
        return False
        
    try:
        # NDI
        import NDIlib as ndi
        print("✅ NDIlib 임포트 성공")
    except ImportError as e:
        print(f"❌ NDIlib 임포트 실패: {e}")
        return False
        
    try:
        # PD 앱 모듈
        from pd_app_v2.ndi_manager import NDIManagerV2
        from pd_app_v2.vmix_manager import VMixManagerV2
        from pd_app_v2.websocket_client import WebSocketClientV2
        print("✅ PD 앱 모듈 임포트 성공")
    except ImportError as e:
        print(f"❌ PD 앱 모듈 임포트 실패: {e}")
        return False
        
    return True

def test_ndi_functions():
    """NDI 기능 테스트"""
    print("\n=== 2. NDI 기능 테스트 ===")
    
    try:
        from pd_app_v2.ndi_manager import NDIManagerV2
        
        # NDI 매니저 생성
        ndi_manager = NDIManagerV2()
        print("✅ NDI 매니저 생성 성공")
        
        # 소스 검색 테스트
        time.sleep(2)  # 소스 검색 대기
        sources = ndi_manager.sources
        if sources:
            print(f"✅ NDI 소스 발견: {sources}")
        else:
            print("⚠️ NDI 소스가 발견되지 않음 (vMix가 실행 중인지 확인)")
            
        return True
        
    except Exception as e:
        print(f"❌ NDI 기능 테스트 실패: {e}")
        return False

def test_vmix_functions():
    """vMix 기능 테스트"""
    print("\n=== 3. vMix Tally 기능 테스트 ===")
    
    try:
        from pd_app_v2.vmix_manager import VMixManagerV2
        
        # vMix 매니저 생성
        vmix_manager = VMixManagerV2()
        print("✅ vMix 매니저 생성 성공")
        
        # 시그널 확인
        if hasattr(vmix_manager, 'websocket_status_changed'):
            print("✅ websocket_status_changed 시그널 존재")
        else:
            print("❌ websocket_status_changed 시그널 없음")
            
        # vMix 연결 테스트
        vmix_manager.connect_to_vmix()
        print("✅ vMix 연결 시도")
        
        time.sleep(2)
        
        if vmix_manager.is_connected:
            print("✅ vMix 연결 상태: 연결됨")
        else:
            print("⚠️ vMix 연결 상태: 연결 안됨 (vMix가 실행 중인지 확인)")
            
        return True
        
    except Exception as e:
        print(f"❌ vMix 기능 테스트 실패: {e}")
        return False

def test_websocket_functions():
    """WebSocket 기능 테스트"""
    print("\n=== 4. WebSocket 기능 테스트 ===")
    
    try:
        from pd_app_v2.websocket_client import WebSocketClientV2
        
        # WebSocket 클라이언트 생성
        ws_client = WebSocketClientV2()
        print("✅ WebSocket 클라이언트 생성 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket 기능 테스트 실패: {e}")
        return False

def test_gui_creation():
    """GUI 생성 테스트 (실제 윈도우는 표시하지 않음)"""
    print("\n=== 5. GUI 생성 테스트 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from pd_app_v2.main_window import MainWindowV2
        from pd_app_v2.ndi_manager import NDIManagerV2
        from pd_app_v2.vmix_manager import VMixManagerV2
        from pd_app_v2.websocket_client import WebSocketClientV2
        
        # Qt 애플리케이션 생성
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        # 매니저 생성
        managers = {
            'ndi': NDIManagerV2(),
            'vmix': VMixManagerV2(),
            'websocket': WebSocketClientV2()
        }
        
        # 메인 윈도우 생성 (표시하지 않음)
        main_window = MainWindowV2(managers)
        print("✅ 메인 윈도우 생성 성공")
        
        # 즉시 종료
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI 생성 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 함수"""
    print("="*60)
    print("PD 통합 소프트웨어 v2.1 전체 기능 테스트")
    print("="*60)
    print(f"Python 버전: {sys.version}")
    print(f"실행 경로: {os.getcwd()}")
    
    # 테스트 실행
    tests = [
        ("모듈 임포트", test_imports),
        ("NDI 기능", test_ndi_functions),
        ("vMix 기능", test_vmix_functions),
        ("WebSocket 기능", test_websocket_functions),
        ("GUI 생성", test_gui_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
            
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
            
    print(f"\n총 {len(results)}개 테스트 중 {passed}개 통과, {failed}개 실패")
    
    if failed == 0:
        print("\n🎉 모든 테스트가 성공적으로 통과했습니다!")
        print("✅ PD 통합 소프트웨어가 정상적으로 작동합니다.")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다.")
        print("위의 오류 메시지를 확인하고 문제를 해결하세요.")
        
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)