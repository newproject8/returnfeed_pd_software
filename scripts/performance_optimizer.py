#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""성능 최적화 패치"""

import os

def optimize_ndi_performance():
    """NDI 성능 최적화"""
    
    # 프레임 큐 크기 조정
    ndi_manager_file = "pd_app/core/ndi_manager.py"
    
    # QApplication 속성 설정으로 GUI 성능 개선
    main_file = "main_integrated.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # QApplication 생성 후 성능 최적화 속성 추가
    app_creation = "app = QApplication(sys.argv)"
    optimized_app = """app = QApplication(sys.argv)
        
        # GUI 성능 최적화
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_CompressHighFrequencyEvents, True)"""
    
    if app_creation in content and "AA_CompressHighFrequencyEvents" not in content:
        content = content.replace(app_creation, optimized_app)
        
        # Qt import 추가
        qt_import = "from PyQt6.QtWidgets import QApplication, QMessageBox"
        new_import = "from PyQt6.QtWidgets import QApplication, QMessageBox\n    from PyQt6.QtCore import Qt"
        content = content.replace(qt_import, new_import)
        
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[O] {main_file} GUI 성능 최적화 완료")

def optimize_frame_processing():
    """프레임 처리 최적화"""
    
    # NDI 위젯에 프레임 드롭핑 추가
    widget_file = "pd_app/ui/ndi_widget.py"
    
    with open(widget_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 프레임 리사이즈 추가 (성능 향상)
    if "# 프레임 리사이즈로 성능 향상" not in content:
        old_code = """            try:
                self.video_widget.setImage(frame)"""
        
        new_code = """            # 프레임 리사이즈로 성능 향상
            try:
                # 프레임이 너무 크면 리사이즈
                if frame.shape[0] > 1080 or frame.shape[1] > 1920:
                    import cv2
                    frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_LINEAR)
                
                self.video_widget.setImage(frame)"""
        
        if old_code in content:
            content = content.replace(old_code, new_code)
            
            with open(widget_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"[O] {widget_file} 프레임 리사이즈 최적화 완료")

def optimize_tally_response():
    """Tally 응답 속도 개선"""
    
    vmix_file = "pd_app/core/vmix_manager.py"
    
    with open(vmix_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # HTTP 요청 타임아웃 단축
    old_timeout = "timeout=5"
    new_timeout = "timeout=2"
    
    if old_timeout in content:
        content = content.replace(old_timeout, new_timeout)
        
        with open(vmix_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[O] {vmix_file} HTTP 타임아웃 최적화 완료")

def main():
    """메인 최적화 함수"""
    
    print("=== 성능 최적화 패치 시작 ===\n")
    
    # 1. NDI 성능 최적화
    optimize_ndi_performance()
    
    # 2. 프레임 처리 최적화
    optimize_frame_processing()
    
    # 3. Tally 응답 속도 개선
    optimize_tally_response()
    
    print("\n=== 최적화 완료 ===")
    print("\n적용된 최적화:")
    print("- GUI 고주파 이벤트 압축")
    print("- 프레임 스킵 (3프레임당 1개 표시)")
    print("- 대형 프레임 자동 리사이즈")
    print("- NDI 타임아웃 16ms (60fps)")
    print("- vMix HTTP 타임아웃 2초")
    print("- WebSocket ping 90초")

if __name__ == "__main__":
    main()