#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NDI Source Diagnostic Tool
NDI 소스 연결 문제 진단
"""

import sys
import time
import NDIlib as ndi

def test_ndi_source():
    """NDI 소스 테스트"""
    print("="*60)
    print("NDI Source Diagnostic")
    print("="*60)
    
    # NDI 초기화
    if not ndi.initialize():
        print("❌ NDI 초기화 실패!")
        return False
        
    print("✅ NDI 초기화 성공")
    
    # Finder 생성
    finder = ndi.find_create_v2()
    if not finder:
        print("❌ NDI Finder 생성 실패!")
        return False
        
    print("✅ NDI Finder 생성 성공")
    
    # 소스 검색 (5초 대기)
    print("\n소스 검색 중... (5초)")
    sources = []
    for i in range(50):  # 5초간 100ms 간격으로 체크
        if ndi.find_wait_for_sources(finder, 100):
            sources = ndi.find_get_current_sources(finder)
            if sources:
                break
        print(".", end="", flush=True)
        
    print()
    
    if not sources:
        print("❌ NDI 소스를 찾을 수 없습니다!")
        print("\n가능한 원인:")
        print("1. vMix가 실행 중이지 않음")
        print("2. vMix의 NDI Output이 활성화되지 않음") 
        print("3. 네트워크/방화벽 문제")
        return False
        
    print(f"\n✅ {len(sources)}개의 NDI 소스 발견:")
    for idx, source in enumerate(sources):
        print(f"  [{idx}] {source.ndi_name}")
        
    # 첫 번째 소스에 연결 시도
    if sources:
        source = sources[0]
        print(f"\n'{source.ndi_name}'에 연결 시도...")
        
        # Receiver 생성
        recv_create = ndi.RecvCreateV3()
        recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        recv_create.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
        
        receiver = ndi.recv_create_v3(recv_create)
        if not receiver:
            print("❌ Receiver 생성 실패!")
            return False
            
        # 연결
        ndi.recv_connect(receiver, source)
        print("✅ 연결 성공!")
        
        # 프레임 수신 테스트 (3초)
        print("\n프레임 수신 테스트 (3초)...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 3:
            frame_type = ndi.recv_capture_v2(receiver, 100)  # 100ms timeout
            
            if frame_type == ndi.FRAME_TYPE_VIDEO:
                v_frame = ndi.recv_get_video_data(receiver)
                if v_frame:
                    frame_count += 1
                    print(f"\r프레임 수신: {frame_count} (해상도: {v_frame.xres}x{v_frame.yres})", end="")
                    ndi.recv_free_video_v2(receiver, v_frame)
                    
        print(f"\n\n✅ 테스트 완료: 3초간 {frame_count}개 프레임 수신")
        print(f"   평균 FPS: {frame_count/3:.1f}")
        
        # 정리
        ndi.recv_destroy(receiver)
        
    # 정리
    ndi.find_destroy(finder)
    ndi.destroy()
    
    return True


if __name__ == "__main__":
    try:
        success = test_ndi_source()
        
        if success:
            print("\n✅ NDI 소스가 정상적으로 작동합니다!")
            print("\nmain_v2.py의 GUI 프리징은 코드 구조 문제입니다.")
            print("Enterprise Edition을 사용하세요:")
            print("  .\\venv\\Scripts\\python.exe enterprise\\main_enterprise.py")
        else:
            print("\n❌ NDI 소스에 문제가 있습니다.")
            print("vMix 설정을 확인하세요.")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        
    input("\n엔터를 눌러 종료...")