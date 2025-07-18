#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""통합 테스트 - main_integrated.py의 모든 기능 테스트"""

import sys
import time
import subprocess
import threading
import psutil
import os
from pathlib import Path

# 테스트 결과 저장
test_results = {
    "startup": False,
    "ndi_preview": False,
    "vmix_connection": False,
    "websocket": False,
    "memory_usage": 0,
    "cpu_usage": 0,
    "errors": []
}

def monitor_process(proc, duration=30):
    """프로세스 모니터링"""
    start_time = time.time()
    log_file = Path("logs/test_integrated.log")
    
    print(f"[*] 프로세스 모니터링 시작 ({duration}초)...")
    
    while time.time() - start_time < duration:
        try:
            # 프로세스 상태 확인
            if proc.poll() is not None:
                test_results["errors"].append(f"프로세스가 예기치 않게 종료됨 (코드: {proc.returncode})")
                return False
            
            # 로그 파일에서 주요 이벤트 확인
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    log_content = f.read()
                    
                    # 시작 확인
                    if "애플리케이션 시작 완료" in log_content:
                        test_results["startup"] = True
                        print("[O] 애플리케이션 시작 확인")
                    
                    # NDI 프리뷰 확인
                    if "NDI 프리뷰 시작 성공" in log_content:
                        test_results["ndi_preview"] = True
                        print("[O] NDI 프리뷰 시작 확인")
                    
                    # vMix 연결 확인
                    if "vMix 연결 성공" in log_content or "vMix TCP 리스너 시작" in log_content:
                        test_results["vmix_connection"] = True
                        print("[O] vMix 연결 확인")
                    
                    # WebSocket 연결 확인
                    if "WebSocket 연결 시도" in log_content:
                        test_results["websocket"] = True
                        print("[O] WebSocket 연결 확인")
                    
                    # 오류 확인
                    for line in log_content.split('\n'):
                        if "ERROR" in line and line not in test_results["errors"]:
                            test_results["errors"].append(line.strip())
            
            # CPU/메모리 사용률 확인
            try:
                process = psutil.Process(proc.pid)
                test_results["cpu_usage"] = process.cpu_percent(interval=1)
                test_results["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
            except:
                pass
            
            time.sleep(1)
            
        except Exception as e:
            test_results["errors"].append(f"모니터링 오류: {str(e)}")
    
    return True

def run_integrated_test():
    """통합 테스트 실행"""
    print("=== PD 소프트웨어 통합 테스트 시작 ===\n")
    
    # 로그 디렉토리 확인
    os.makedirs("logs", exist_ok=True)
    
    # 테스트용 로그 파일 설정
    env = os.environ.copy()
    env['PD_LOG_FILE'] = 'logs/test_integrated.log'
    
    try:
        # main_integrated.py 실행
        print("[*] main_integrated.py 실행 중...")
        proc = subprocess.Popen(
            ["venv/Scripts/python.exe", "main_integrated.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 프로세스 모니터링 (30초)
        monitor_success = monitor_process(proc, duration=30)
        
        # 프로세스 종료
        print("\n[*] 테스트 완료, 프로세스 종료 중...")
        proc.terminate()
        time.sleep(2)
        
        if proc.poll() is None:
            proc.kill()
        
    except Exception as e:
        test_results["errors"].append(f"테스트 실행 오류: {str(e)}")
        return False
    
    # 결과 분석
    print("\n=== 테스트 결과 ===")
    print(f"애플리케이션 시작: {'[O] 성공' if test_results['startup'] else '[X] 실패'}")
    print(f"NDI 프리뷰: {'[O] 성공' if test_results['ndi_preview'] else '[X] 실패'}")
    print(f"vMix 연결: {'[O] 성공' if test_results['vmix_connection'] else '[X] 실패'}")
    print(f"WebSocket: {'[O] 성공' if test_results['websocket'] else '[X] 실패'}")
    print(f"\n리소스 사용:")
    print(f"  CPU: {test_results['cpu_usage']:.1f}%")
    print(f"  메모리: {test_results['memory_usage']:.1f} MB")
    
    if test_results["errors"]:
        print(f"\n오류 발견 ({len(test_results['errors'])}개):")
        for error in test_results["errors"][:5]:  # 처음 5개만
            print(f"  - {error}")
    
    # 전체 성공 여부
    all_passed = all([
        test_results["startup"],
        test_results["ndi_preview"],
        test_results["vmix_connection"],
        test_results["websocket"],
        len(test_results["errors"]) == 0
    ])
    
    if all_passed:
        print("\n[O] 모든 통합 테스트 통과!")
        return True
    else:
        print("\n[X] 일부 테스트 실패")
        return False

if __name__ == "__main__":
    success = run_integrated_test()
    sys.exit(0 if success else 1)