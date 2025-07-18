#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PD 통합 소프트웨어 전체 기능 시뮬레이션 테스트
GUI 없이 모든 핵심 기능을 테스트
"""

import sys
import os
import time
import json
import logging
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로거 설정
from pd_app.utils import setup_logger
logger = setup_logger()

print("\n" + "=" * 80)
print("PD 통합 소프트웨어 - 전체 기능 시뮬레이션 테스트")
print("=" * 80)

# 1. 설정 시스템 테스트
print("\n[1] 설정 시스템 테스트")
print("-" * 40)
try:
    from pd_app.config.settings import Settings
    settings = Settings()
    logger.info("설정 시스템 초기화 성공")
    
    # 설정 값 테스트
    test_config = {
        'test.string': 'test_value',
        'test.number': 12345,
        'test.boolean': True,
        'test.list': [1, 2, 3],
        'test.dict': {'key': 'value'}
    }
    
    for key, value in test_config.items():
        settings.set(key, value)
        retrieved = settings.get(key)
        assert retrieved == value, f"설정 값 불일치: {key}"
    
    print("✓ 설정 저장/읽기 테스트 통과")
    logger.info("설정 시스템 테스트 완료")
except Exception as e:
    print(f"✗ 설정 시스템 오류: {e}")
    logger.error(f"설정 시스템 오류: {e}", exc_info=True)

# 2. 인증 관리자 테스트
print("\n[2] 인증 관리자 테스트")
print("-" * 40)
try:
    from pd_app.core.auth_manager import AuthManager
    auth = AuthManager()
    logger.info("인증 관리자 초기화 성공")
    
    # 테스트 자격 증명
    test_credentials = {
        'user_id': 'test_pd',
        'unique_address': 'test123.returnfeed.net',
        'access_token': 'test_token_12345'
    }
    
    # 자격 증명 저장
    auth.save_credentials(test_credentials)
    print("✓ 자격 증명 저장 성공")
    
    # 자격 증명 로드
    loaded = auth.load_credentials()
    if loaded:
        user_info = auth.get_user_info()
        if user_info:
            print(f"✓ 자격 증명 로드 성공: {user_info.get('user_id')}")
    
    logger.info("인증 관리자 테스트 완료")
except Exception as e:
    print(f"✗ 인증 관리자 오류: {e}")
    logger.error(f"인증 관리자 오류: {e}", exc_info=True)

# 3. NDI 관리자 테스트 (시뮬레이터 모드)
print("\n[3] NDI 관리자 테스트")
print("-" * 40)
try:
    from pd_app.core.ndi_manager import NDIManager
    ndi_manager = NDIManager()
    
    # 시뮬레이터 모드로 초기화
    ndi_manager.initialize()
    print("✓ NDI 관리자 초기화 성공 (시뮬레이터 모드)")
    
    # 소스 검색 시뮬레이션
    time.sleep(0.5)  # 소스 검색 대기
    
    logger.info("NDI 관리자 테스트 완료")
except Exception as e:
    print(f"✗ NDI 관리자 오류: {e}")
    logger.error(f"NDI 관리자 오류: {e}", exc_info=True)

# 4. vMix 관리자 테스트
print("\n[4] vMix 관리자 테스트")
print("-" * 40)
try:
    from pd_app.core.vmix_manager import VMixManager
    vmix = VMixManager()
    logger.info("vMix 관리자 초기화 성공")
    
    # 연결 테스트 (실제 연결 없이)
    print("✓ vMix 관리자 생성 성공")
    print(f"  - 기본 IP: {vmix.vmix_ip}")
    print(f"  - HTTP 포트: {vmix.http_port}")
    print(f"  - TCP 포트: {vmix.tcp_port}")
    
    logger.info("vMix 관리자 테스트 완료")
except Exception as e:
    print(f"✗ vMix 관리자 오류: {e}")
    logger.error(f"vMix 관리자 오류: {e}", exc_info=True)

# 5. SRT 관리자 테스트
print("\n[5] SRT 스트리밍 관리자 테스트")
print("-" * 40)
try:
    from pd_app.core.srt_manager import SRTManager
    srt = SRTManager()
    logger.info("SRT 관리자 초기화 성공")
    
    # FFmpeg 확인
    if srt.check_ffmpeg():
        print("✓ FFmpeg 사용 가능")
    else:
        print("! FFmpeg를 찾을 수 없음 (스트리밍 불가)")
    
    # MediaMTX 상태 확인 (실제 연결 없이)
    print(f"✓ MediaMTX 서버 설정: {srt.media_mtx_server}:{srt.srt_port}")
    
    logger.info("SRT 관리자 테스트 완료")
except Exception as e:
    print(f"✗ SRT 관리자 오류: {e}")
    logger.error(f"SRT 관리자 오류: {e}", exc_info=True)

# 6. 파일 시스템 테스트
print("\n[6] 파일 시스템 테스트")
print("-" * 40)
try:
    # 필요한 디렉토리 확인
    required_dirs = ['logs', 'config', 'temp']
    for dir_name in required_dirs:
        os.makedirs(dir_name, exist_ok=True)
        if os.path.exists(dir_name):
            print(f"✓ {dir_name}/ 디렉토리 확인")
    
    # 로그 파일 확인
    log_files = [f for f in os.listdir('logs') if f.endswith('.log')]
    print(f"✓ 로그 파일 개수: {len(log_files)}")
    
    logger.info("파일 시스템 테스트 완료")
except Exception as e:
    print(f"✗ 파일 시스템 오류: {e}")
    logger.error(f"파일 시스템 오류: {e}", exc_info=True)

# 7. 메모리 및 리소스 정리 테스트
print("\n[7] 리소스 정리 테스트")
print("-" * 40)
try:
    # NDI 정리
    if 'ndi_manager' in locals():
        del ndi_manager
        print("✓ NDI 관리자 정리")
    
    # 기타 리소스 정리
    import gc
    gc.collect()
    print("✓ 가비지 컬렉션 완료")
    
    logger.info("리소스 정리 완료")
except Exception as e:
    print(f"✗ 리소스 정리 오류: {e}")
    logger.error(f"리소스 정리 오류: {e}", exc_info=True)

# 테스트 결과 요약
print("\n" + "=" * 80)
print("테스트 완료!")
print("로그 파일을 확인하여 상세한 정보를 볼 수 있습니다.")
print("=" * 80)

# 최종 시스템 상태
print("\n최종 시스템 상태:")
print(f"- Python 버전: {sys.version.split()[0]}")
print(f"- 플랫폼: {sys.platform}")
print(f"- 작업 디렉토리: {os.getcwd()}")
print(f"- 테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

logger.info("전체 시뮬레이션 테스트 완료")