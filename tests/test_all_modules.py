#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 모듈 임포트 테스트 및 초기화 검증
"""

import sys
import os
import importlib
import traceback
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("PD 통합 소프트웨어 - 모듈 테스트")
print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 테스트할 모듈 목록
modules_to_test = [
    # 기본 유틸리티
    ("pd_app.utils.logger", "로거 설정"),
    ("pd_app.utils.helpers", "헬퍼 함수"),
    
    # 설정 관련
    ("pd_app.config.constants", "상수 정의"),
    ("pd_app.config.settings", "설정 관리"),
    
    # 핵심 관리자
    ("pd_app.core.auth_manager", "인증 관리자"),
    ("pd_app.core.ndi_manager", "NDI 관리자"),
    ("pd_app.core.vmix_manager", "vMix 관리자"),
    ("pd_app.core.srt_manager", "SRT 관리자"),
    
    # 네트워크
    ("pd_app.network.websocket_client", "WebSocket 클라이언트"),
    ("pd_app.network.tcp_client", "TCP 클라이언트"),
    
    # UI (PyQt6 필요)
    ("pd_app.ui.main_window", "메인 윈도우"),
    ("pd_app.ui.ndi_widget", "NDI 위젯"),
    ("pd_app.ui.tally_widget", "Tally 위젯"),
    ("pd_app.ui.srt_widget", "SRT 위젯"),
]

# 임포트 테스트
print("\n1. 모듈 임포트 테스트")
print("-" * 40)

successful_imports = []
failed_imports = []

for module_name, description in modules_to_test:
    try:
        module = importlib.import_module(module_name)
        successful_imports.append((module_name, description))
        print(f"✓ {description:20} [{module_name}]")
    except Exception as e:
        failed_imports.append((module_name, description, str(e)))
        print(f"✗ {description:20} [{module_name}]")
        print(f"  오류: {type(e).__name__}: {e}")

# 요약
print(f"\n임포트 성공: {len(successful_imports)}/{len(modules_to_test)}")

# 클래스 초기화 테스트
print("\n2. 주요 클래스 초기화 테스트")
print("-" * 40)

# 기본 의존성 없이 생성 가능한 클래스들
classes_to_test = [
    ("pd_app.config.settings", "Settings", "설정 관리자"),
    ("pd_app.core.auth_manager", "AuthManager", "인증 관리자"),
]

for module_name, class_name, description in classes_to_test:
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        instance = cls()
        print(f"✓ {description:20} 초기화 성공")
    except Exception as e:
        print(f"✗ {description:20} 초기화 실패")
        print(f"  오류: {type(e).__name__}: {e}")

# NDI 시뮬레이터 테스트
print("\n3. NDI 시뮬레이터 테스트")
print("-" * 40)

try:
    from pd_app.core import ndi_simulator
    sim = ndi_simulator.NDISimulator()
    sim.initialize()
    print("✓ NDI 시뮬레이터 초기화 성공")
    
    # 소스 검색 테스트
    finder = sim.find_create_v2()
    sources = sim.find_get_current_sources(finder)
    print(f"✓ 시뮬레이션 소스 개수: {len(sources) if sources else 0}")
except Exception as e:
    print(f"✗ NDI 시뮬레이터 오류: {e}")
    traceback.print_exc()

# 설정 파일 테스트
print("\n4. 설정 파일 시스템 테스트")
print("-" * 40)

try:
    from pd_app.config.settings import Settings
    settings = Settings()
    
    # 테스트 값 저장
    test_key = "test.module_check"
    test_value = datetime.now().isoformat()
    settings.set(test_key, test_value)
    
    # 값 읽기
    read_value = settings.get(test_key)
    if read_value == test_value:
        print("✓ 설정 저장/읽기 성공")
    else:
        print("✗ 설정 저장/읽기 실패")
except Exception as e:
    print(f"✗ 설정 시스템 오류: {e}")
    traceback.print_exc()

# 오류 파일 생성
if failed_imports:
    print("\n5. 오류 보고서 생성")
    print("-" * 40)
    
    error_file = f"module_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write("PD 통합 소프트웨어 - 모듈 오류 보고서\n")
        f.write(f"생성 시간: {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        for module_name, description, error in failed_imports:
            f.write(f"모듈: {module_name}\n")
            f.write(f"설명: {description}\n")
            f.write(f"오류: {error}\n")
            f.write("-" * 40 + "\n")
    
    print(f"오류 보고서 생성: {error_file}")

print("\n" + "=" * 80)