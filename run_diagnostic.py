#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Edition 진단 실행 스크립트
상세한 로그를 통해 성능 문제 파악
"""

import sys
import os
import subprocess
import datetime

def main():
    print("="*80)
    print("Enterprise Edition Diagnostic Runner")
    print("="*80)
    print(f"\n시작 시간: {datetime.datetime.now()}")
    print("\n진단 모드로 실행합니다...")
    print("다음 로그 파일들이 생성됩니다:")
    print("- diagnostic_enterprise_diagnostic_*.log (메인 로그)")
    print("- diagnostic_ndi_manager_fixed_*.log (NDI 로그)")
    print("- diagnostic_ndi_widget_fixed_*.log (위젯 로그)")
    print("- startup_profile.txt (시작 프로파일링)")
    print("\n실행 중...")
    print("-"*80)
    
    # Python 경로
    python = sys.executable
    
    # 진단 스크립트 경로
    diagnostic_script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "enterprise",
        "main_enterprise_diagnostic.py"
    )
    
    # 실행
    try:
        subprocess.run([python, diagnostic_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n오류 발생: {e}")
        print("\n생성된 로그 파일을 확인하세요.")
    except KeyboardInterrupt:
        print("\n사용자가 중단했습니다.")
    
    print("\n"+"="*80)
    print("진단 완료. 로그 파일을 분석하세요.")
    print("="*80)

if __name__ == '__main__':
    main()