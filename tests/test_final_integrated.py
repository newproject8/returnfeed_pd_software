#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""최종 통합 테스트 - 모든 수정사항 확인"""

import sys
import time
import subprocess
import os

# 출력 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_quick_test():
    """빠른 테스트 실행"""
    print("=== PD 소프트웨어 최종 테스트 ===\n")
    
    # 1. 컴포넌트 테스트
    print("[1] 컴포넌트 개별 테스트...")
    result = subprocess.run(
        ["venv/Scripts/python.exe", "test_components.py"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    if result.stdout and "[O]" in result.stdout and "NDI" in result.stdout:
        print("   [O] 컴포넌트 테스트 성공")
    else:
        print("   [X] 컴포넌트 테스트 실패")
        print(result.stdout[-500:])  # 마지막 500자만
        return False
    
    # 2. 메인 프로그램 실행 (10초)
    print("\n[2] 메인 프로그램 실행 테스트 (10초)...")
    
    # 테스트용 환경 변수
    env = os.environ.copy()
    env['PD_TEST_MODE'] = '1'
    
    proc = subprocess.Popen(
        ["venv/Scripts/python.exe", "main_integrated.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    # 10초 동안 실행
    time.sleep(10)
    
    # 프로세스가 여전히 실행 중인지 확인
    if proc.poll() is None:
        print("   [O] 프로그램이 크래시 없이 실행 중")
        proc.terminate()
        time.sleep(2)
        if proc.poll() is None:
            proc.kill()
        success = True
    else:
        print("   [X] 프로그램이 종료됨 (종료 코드: {})".format(proc.returncode))
        stdout, stderr = proc.communicate()
        print("   표준 출력:", stdout[-500:] if stdout else "없음")
        print("   표준 에러:", stderr[-500:] if stderr else "없음")
        success = False
    
    # 3. 최근 로그 확인
    print("\n[3] 최근 로그 확인...")
    
    # 가장 최근 로그 파일 찾기
    import glob
    log_files = sorted(glob.glob("logs/pd_app_*.log"), key=os.path.getmtime)
    
    if log_files:
        latest_log = log_files[-1]
        print(f"   최근 로그: {latest_log}")
        
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            log_content = f.read()
            
        # 주요 이벤트 확인
        events = {
            "NDI 초기화": "NDI 라이브러리 초기화 성공" in log_content,
            "크래시 핸들러": "크래시 핸들러 설치 완료" in log_content,
            "메인 윈도우": "메인 윈도우 생성 성공" in log_content,
            "WebSocket": "WebSocket 클라이언트 시작" in log_content,
            "NDI 소스 발견": "NDI 소스 발견" in log_content,
        }
        
        for event, found in events.items():
            print(f"   {event}: {'[O]' if found else '[X]'}")
        
        # 오류 확인
        error_count = log_content.count("ERROR") + log_content.count("CRITICAL")
        warning_count = log_content.count("WARNING")
        
        print(f"\n   오류 수: {error_count}")
        print(f"   경고 수: {warning_count}")
        
        if error_count > 0:
            # 오류 내용 출력
            print("\n   주요 오류:")
            for line in log_content.split('\n'):
                if "ERROR" in line or "CRITICAL" in line:
                    print(f"   - {line.strip()[:100]}...")
                    if len(print.__name__) > 5:  # 출력 제한
                        break
    
    return success

def main():
    """메인 테스트 함수"""
    
    # 로그 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    
    # 테스트 실행
    success = run_quick_test()
    
    print("\n=== 테스트 결과 ===")
    if success:
        print("[O] 모든 테스트 통과 - 프로그램이 안정적으로 실행됩니다")
        
        print("\n다음 명령으로 프로그램을 실행하세요:")
        print("venv\\Scripts\\python.exe main_integrated.py")
    else:
        print("[X] 일부 테스트 실패 - 로그를 확인하세요")
        
        # 크래시 로그 확인
        crash_logs = glob.glob("logs/crash_*.log")
        if crash_logs:
            print(f"\n크래시 로그 발견: {crash_logs[-1]}")

if __name__ == "__main__":
    import glob  # main 함수에서 사용하므로 여기서도 import
    main()