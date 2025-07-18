#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
성능 로그 분석 도구
진단 로그에서 주요 문제점을 자동으로 찾아냅니다
"""

import os
import re
import glob
from datetime import datetime
from collections import defaultdict

def analyze_timing_logs(log_file):
    """타이밍 로그 분석"""
    print(f"\n분석 중: {log_file}")
    print("-" * 60)
    
    slow_operations = []
    import_times = defaultdict(float)
    function_times = defaultdict(list)
    errors = []
    freezes = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            # 느린 작업 찾기 (100ms 이상)
            timing_match = re.search(r'\[TIMING\] (\S+) completed in (\d+\.\d+)ms', line)
            if timing_match:
                func_name = timing_match.group(1)
                time_ms = float(timing_match.group(2))
                function_times[func_name].append(time_ms)
                if time_ms > 100:
                    slow_operations.append((func_name, time_ms))
            
            # Import 시간
            import_match = re.search(r'\[IMPORT\] (\S+) imported in (\d+\.\d+)ms', line)
            if import_match:
                module = import_match.group(1)
                time_ms = float(import_match.group(2))
                import_times[module] = time_ms
            
            # 에러 찾기
            if '[ERROR]' in line or '[CRITICAL]' in line:
                errors.append(line.strip())
            
            # GUI 프리징
            freeze_match = re.search(r'GUI freeze detected: (\d+\.\d+)ms', line)
            if freeze_match:
                freeze_time = float(freeze_match.group(1))
                freezes.append(freeze_time)
            
            # 성능 경고
            if 'freezes detected' in line:
                freezes.append(line.strip())
    
    # 결과 출력
    print("\n🔴 느린 작업 (>100ms):")
    if slow_operations:
        for func, time_ms in sorted(slow_operations, key=lambda x: x[1], reverse=True):
            print(f"  - {func}: {time_ms:.2f}ms")
    else:
        print("  없음")
    
    print("\n📦 Import 시간:")
    if import_times:
        total_import = sum(import_times.values())
        print(f"  총 Import 시간: {total_import:.2f}ms")
        for module, time_ms in sorted(import_times.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {module}: {time_ms:.2f}ms")
    
    print("\n⚠️ 에러:")
    if errors:
        for error in errors[:10]:  # 처음 10개만
            print(f"  - {error}")
    else:
        print("  없음")
    
    print("\n🧊 GUI 프리징:")
    if freezes:
        print(f"  프리징 횟수: {len([f for f in freezes if isinstance(f, float)])}")
        if any(isinstance(f, float) for f in freezes):
            freeze_times = [f for f in freezes if isinstance(f, float)]
            print(f"  최대 프리징: {max(freeze_times):.2f}ms")
            print(f"  평균 프리징: {sum(freeze_times)/len(freeze_times):.2f}ms")
    else:
        print("  없음")
    
    print("\n📊 함수별 평균 실행 시간:")
    for func, times in sorted(function_times.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:10]:
        avg_time = sum(times) / len(times)
        print(f"  - {func}: {avg_time:.2f}ms (호출 {len(times)}회)")

def analyze_startup_profile(profile_file):
    """시작 프로파일 분석"""
    if not os.path.exists(profile_file):
        return
        
    print(f"\n\n시작 프로파일 분석: {profile_file}")
    print("=" * 80)
    
    with open(profile_file, 'r') as f:
        lines = f.readlines()
        
    # 느린 함수 찾기
    print("\n🐌 가장 느린 함수들:")
    in_stats = False
    count = 0
    for line in lines:
        if 'cumulative' in line:
            in_stats = True
            continue
        if in_stats and count < 10:
            if line.strip() and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 6:
                    cumtime = parts[3]
                    func = ' '.join(parts[5:])
                    if float(cumtime) > 0.1:  # 100ms 이상
                        print(f"  - {func}: {cumtime}s")
                        count += 1

def find_bottlenecks():
    """주요 병목 현상 찾기"""
    print("\n\n🎯 주요 병목 현상 요약")
    print("=" * 80)
    
    # 최신 로그 파일 찾기
    log_files = glob.glob('diagnostic_*.log')
    if not log_files:
        print("진단 로그 파일을 찾을 수 없습니다.")
        print("먼저 run_diagnostic.py를 실행하세요.")
        return
    
    # 가장 최근 로그 분석
    latest_log = max(log_files, key=os.path.getctime)
    
    # 각 로그 파일 분석
    for log_file in log_files:
        analyze_timing_logs(log_file)
    
    # 시작 프로파일 분석
    analyze_startup_profile('startup_profile.txt')
    
    print("\n\n💡 권장 사항:")
    print("1. Import 시간이 길다면 → 지연 import 사용 고려")
    print("2. GUI 프리징이 많다면 → 메인 스레드에서 무거운 작업 확인")
    print("3. 특정 함수가 느리다면 → 해당 함수 최적화 필요")
    print("4. 에러가 많다면 → 에러 원인 먼저 해결")

if __name__ == '__main__':
    print("="*80)
    print("Enterprise Edition 성능 분석 도구")
    print("="*80)
    
    find_bottlenecks()