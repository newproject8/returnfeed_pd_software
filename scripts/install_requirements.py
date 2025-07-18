#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
의존성 설치 스크립트
"""

import subprocess
import sys
import os

print("=" * 80)
print("PD 통합 소프트웨어 의존성 설치")
print("=" * 80)

# pip 업그레이드
print("\n1. pip 업그레이드...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    print("   ✓ pip 업그레이드 완료")
except Exception as e:
    print(f"   ✗ pip 업그레이드 실패: {e}")

# requirements.txt 읽기
requirements_file = "requirements.txt"
if not os.path.exists(requirements_file):
    print(f"\n오류: {requirements_file} 파일을 찾을 수 없습니다.")
    sys.exit(1)

print(f"\n2. {requirements_file} 파일 읽기...")
with open(requirements_file, 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"   설치할 패키지 수: {len(requirements)}")
for req in requirements:
    print(f"   - {req}")

# 패키지 설치
print("\n3. 패키지 설치 시작...")
failed_packages = []

for i, package in enumerate(requirements, 1):
    print(f"\n   [{i}/{len(requirements)}] {package} 설치 중...")
    try:
        # asyncio는 Python 내장 모듈이므로 설치 불필요
        if package.lower() == "asyncio":
            print(f"      ✓ {package}는 Python 내장 모듈입니다.")
            continue
            
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"      ✓ {package} 설치 완료")
    except subprocess.CalledProcessError as e:
        print(f"      ✗ {package} 설치 실패: {e}")
        failed_packages.append(package)

# 결과 요약
print("\n" + "=" * 80)
print("설치 완료!")
print(f"성공: {len(requirements) - len(failed_packages)}/{len(requirements)}")

if failed_packages:
    print(f"\n설치 실패한 패키지:")
    for pkg in failed_packages:
        print(f"   - {pkg}")
    print("\n다음 명령으로 개별 설치를 시도해보세요:")
    for pkg in failed_packages:
        print(f"   python -m pip install {pkg}")

# 설치된 패키지 확인
print("\n4. 주요 패키지 버전 확인...")
important_packages = ["PyQt6", "numpy", "websockets", "opencv-python"]
for pkg in important_packages:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(': ')[1]
                    print(f"   ✓ {pkg}: {version}")
                    break
        else:
            print(f"   ✗ {pkg}: 설치되지 않음")
    except:
        print(f"   ? {pkg}: 확인 실패")

print("\n" + "=" * 80)