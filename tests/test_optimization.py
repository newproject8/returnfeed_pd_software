#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성능 최적화 테스트 스크립트
최적화 전후 성능 비교
"""

import sys
import os
import time
import logging
import psutil
import threading

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def measure_performance(func_name, func):
    """함수 실행 시간 및 메모리 사용량 측정"""
    process = psutil.Process()
    
    # 시작 전 메모리
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # 실행 시간 측정
    start_time = time.time()
    result = func()
    end_time = time.time()
    
    # 종료 후 메모리
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"\n[{func_name}]")
    print(f"실행 시간: {end_time - start_time:.3f}초")
    print(f"메모리 사용: {mem_before:.1f}MB -> {mem_after:.1f}MB (증가: {mem_after - mem_before:.1f}MB)")
    
    return result

def test_ndi_manager_import():
    """NDI Manager 임포트 테스트"""
    print("\n=== NDI Manager 임포트 테스트 ===")
    
    # 기본 버전
    def import_original():
        from pd_app.core.ndi_manager import NDIManager
        return NDIManager
    
    # 최적화 버전
    def import_optimized():
        from pd_app.core.ndi_manager_optimized import NDIManager
        return NDIManager
    
    try:
        measure_performance("기본 NDI Manager", import_original)
    except:
        print("기본 NDI Manager 임포트 실패")
    
    try:
        measure_performance("최적화 NDI Manager", import_optimized)
    except:
        print("최적화 NDI Manager 임포트 실패")

def test_frame_processing():
    """프레임 처리 성능 테스트"""
    print("\n=== 프레임 처리 성능 테스트 ===")
    
    try:
        import numpy as np
        
        # 테스트 프레임 생성 (1920x1080 RGB)
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        # 프레임 복사 테스트
        def copy_frame():
            for _ in range(100):
                frame_copy = np.copy(test_frame)
            return frame_copy
        
        # 프레임 참조 테스트
        def reference_frame():
            for _ in range(100):
                frame_ref = test_frame
            return frame_ref
        
        measure_performance("프레임 복사 (100회)", copy_frame)
        measure_performance("프레임 참조 (100회)", reference_frame)
        
    except ImportError:
        print("NumPy가 설치되지 않아 프레임 처리 테스트를 건너뜁니다.")

def test_gui_responsiveness():
    """GUI 응답성 테스트"""
    print("\n=== GUI 응답성 테스트 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer, QEventLoop
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 이벤트 루프 응답 시간 측정
        event_times = []
        
        def measure_event_response():
            start = time.time()
            loop = QEventLoop()
            QTimer.singleShot(1, loop.quit)
            loop.exec()
            event_times.append(time.time() - start)
        
        # 100회 측정
        for _ in range(100):
            measure_event_response()
        
        avg_response = sum(event_times) / len(event_times) * 1000  # ms
        max_response = max(event_times) * 1000  # ms
        
        print(f"평균 이벤트 응답 시간: {avg_response:.2f}ms")
        print(f"최대 이벤트 응답 시간: {max_response:.2f}ms")
        
        if avg_response < 10:
            print("✓ GUI 응답성 우수")
        elif avg_response < 50:
            print("✓ GUI 응답성 양호")
        else:
            print("✗ GUI 응답성 개선 필요")
            
    except ImportError:
        print("PyQt6가 설치되지 않아 GUI 응답성 테스트를 건너뜁니다.")

def test_thread_performance():
    """스레드 성능 테스트"""
    print("\n=== 스레드 성능 테스트 ===")
    
    class TestThread(threading.Thread):
        def __init__(self):
            super().__init__()
            self.counter = 0
            self.running = True
            
        def run(self):
            while self.running and self.counter < 1000000:
                self.counter += 1
    
    # 스레드 생성 및 실행
    threads = []
    start_time = time.time()
    
    for i in range(4):  # 4개 스레드
        thread = TestThread()
        thread.start()
        threads.append(thread)
    
    # 모든 스레드 완료 대기
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    print(f"4개 스레드 실행 시간: {end_time - start_time:.3f}초")
    print(f"총 카운트: {sum(t.counter for t in threads):,}")

def test_optimization_flags():
    """최적화 플래그 확인"""
    print("\n=== 최적화 설정 확인 ===")
    
    # 환경 변수 확인
    env_vars = [
        'QT_ENABLE_HIGHDPI_SCALING',
        'QT_AUTO_SCREEN_SCALE_FACTOR',
        'QT_SCALE_FACTOR'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, '설정되지 않음')
        print(f"{var}: {value}")
    
    # Python 최적화 플래그
    print(f"\nPython 최적화 레벨: {sys.flags.optimize}")
    print(f"Python 디버그 모드: {sys.flags.debug}")

def main():
    """메인 테스트 함수"""
    print("="*60)
    print("PD 통합 소프트웨어 성능 최적화 테스트")
    print("="*60)
    
    # 시스템 정보
    print(f"\n시스템 정보:")
    print(f"CPU 코어: {psutil.cpu_count()}")
    print(f"메모리: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB")
    print(f"Python 버전: {sys.version}")
    
    # 테스트 실행
    test_optimization_flags()
    test_ndi_manager_import()
    test_frame_processing()
    test_gui_responsiveness()
    test_thread_performance()
    
    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)

if __name__ == '__main__':
    main()