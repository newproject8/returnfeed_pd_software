#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_integrated.py 테스트 실행 스크립트
오류를 안전하게 캐치하고 로그 파일 경로를 출력
"""

import subprocess
import sys
import os
from datetime import datetime

print("=" * 80)
print("PD 통합 소프트웨어 테스트 실행")
print("=" * 80)

# 로그 디렉토리 생성
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# 현재 시간
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

print(f"\n작업 디렉토리: {os.getcwd()}")
print(f"Python 버전: {sys.version}")
print(f"로그 디렉토리: {os.path.abspath(log_dir)}")
print(f"\n실행 중... (Ctrl+C로 중단 가능)\n")

# main_integrated.py 실행
try:
    result = subprocess.run(
        [sys.executable, "main_integrated.py"],
        capture_output=True,
        text=True,
        timeout=30  # 30초 타임아웃
    )
    
    print("\n=== 표준 출력 ===")
    print(result.stdout)
    
    print("\n=== 표준 에러 ===")
    print(result.stderr)
    
    print(f"\n종료 코드: {result.returncode}")
    
except subprocess.TimeoutExpired:
    print("\n실행 시간 초과 (30초)")
except KeyboardInterrupt:
    print("\n사용자에 의해 중단됨")
except Exception as e:
    print(f"\n실행 오류: {type(e).__name__}: {e}")

# 최신 로그 파일 찾기
try:
    log_files = [f for f in os.listdir(log_dir) if f.startswith("pd_app_") and f.endswith(".log")]
    if log_files:
        latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
        log_path = os.path.join(log_dir, latest_log)
        print(f"\n최신 로그 파일: {os.path.abspath(log_path)}")
        
        # 로그 파일의 마지막 50줄 출력
        print("\n=== 로그 파일 내용 (마지막 50줄) ===")
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                print(line.rstrip())
    else:
        print("\n로그 파일을 찾을 수 없습니다.")
except Exception as e:
    print(f"\n로그 파일 읽기 오류: {e}")

print("\n" + "=" * 80)