#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""컴포넌트 개별 테스트 스크립트"""

import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import time
import NDIlib as ndi

def test_ndi_basic():
    """NDI 기본 기능 테스트"""
    print("=== NDI 기본 테스트 시작 ===")
    
    # NDI 초기화
    if not ndi.initialize():
        print("[X] NDI 초기화 실패")
        return False
    print("[O] NDI 초기화 성공")
    
    # Finder 생성
    finder = ndi.find_create_v2()
    if not finder:
        print("[X] NDI Finder 생성 실패")
        return False
    print("[O] NDI Finder 생성 성공")
    
    # 소스 검색 (5초 대기)
    print("[...] NDI 소스 검색 중... (5초)")
    ndi.find_wait_for_sources(finder, 5000)
    
    sources = ndi.find_get_current_sources(finder)
    if not sources:
        print("[X] NDI 소스를 찾을 수 없음")
        ndi.find_destroy(finder)
        return False
    
    # 소스 목록 출력
    print(f"[O] {len(sources) if hasattr(sources, '__len__') else sources.no_sources}개의 NDI 소스 발견:")
    
    if hasattr(sources, 'no_sources'):
        for i in range(sources.no_sources):
            source_name = sources.sources[i].ndi_name
            if isinstance(source_name, bytes):
                source_name = source_name.decode('utf-8')
            print(f"   - {source_name}")
    else:
        for source in sources:
            print(f"   - {source}")
    
    # 첫 번째 소스에 연결 테스트
    print("\n[>] 첫 번째 소스에 연결 시도...")
    
    recv_create = ndi.RecvCreateV3()
    recv_create.color_format = ndi.RECV_COLOR_FORMAT_RGBX_RGBA
    
    receiver = ndi.recv_create_v3(recv_create)
    if not receiver:
        print("[X] 리시버 생성 실패")
        ndi.find_destroy(finder)
        return False
    print("[O] 리시버 생성 성공")
    
    # 소스 연결
    if hasattr(sources, 'sources'):
        target_source = sources.sources[0]
    else:
        target_source = sources[0]
    
    ndi.recv_connect(receiver, target_source)
    print("[O] 소스 연결 성공")
    
    # 프레임 수신 테스트 (10프레임)
    print("\n[V] 프레임 수신 테스트 (10프레임)...")
    frame_count = 0
    start_time = time.time()
    
    while frame_count < 10 and time.time() - start_time < 10:
        frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2(receiver, 100)
        
        if frame_type == ndi.FRAME_TYPE_VIDEO and v_frame:
            frame_count += 1
            print(f"   [F] 비디오 프레임 #{frame_count} 수신 (크기: {v_frame.xres}x{v_frame.yres})")
            ndi.recv_free_video_v2(receiver, v_frame)
        elif frame_type == ndi.FRAME_TYPE_AUDIO and a_frame:
            ndi.recv_free_audio_v2(receiver, a_frame)
        elif frame_type == ndi.FRAME_TYPE_METADATA and m_frame:
            ndi.recv_free_metadata(receiver, m_frame)
    
    if frame_count > 0:
        print(f"[O] {frame_count}개의 프레임 수신 성공")
    else:
        print("[X] 프레임을 수신하지 못함")
    
    # 정리
    ndi.recv_destroy(receiver)
    ndi.find_destroy(finder)
    ndi.destroy()
    
    return frame_count > 0


def test_vmix_connection():
    """vMix 연결 테스트"""
    print("\n=== vMix 연결 테스트 시작 ===")
    
    import socket
    import xml.etree.ElementTree as ET
    from urllib.request import urlopen
    
    vmix_ip = "127.0.0.1"
    http_port = 8088
    tcp_port = 8099
    
    # HTTP API 테스트
    try:
        print(f"[HTTP] vMix HTTP API 테스트 ({vmix_ip}:{http_port})...")
        response = urlopen(f"http://{vmix_ip}:{http_port}/api", timeout=5)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        version = root.find('version')
        if version is not None:
            print(f"[O] vMix 버전: {version.text}")
        
        # 입력 목록 확인
        inputs = root.findall('.//input')
        print(f"[O] {len(inputs)}개의 입력 발견")
        for inp in inputs[:3]:  # 처음 3개만
            print(f"   - {inp.get('title', 'Unknown')}")
            
    except Exception as e:
        print(f"[X] vMix HTTP API 연결 실패: {e}")
        return False
    
    # TCP Tally 테스트
    try:
        print(f"\n[TCP] vMix TCP Tally 테스트 ({vmix_ip}:{tcp_port})...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((vmix_ip, tcp_port))
        
        # SUBSCRIBE 명령 전송
        sock.send(b"SUBSCRIBE TALLY\r\n")
        
        # 응답 대기
        data = sock.recv(1024)
        if data:
            print(f"[O] Tally 데이터 수신: {data[:50]}...")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"[X] vMix TCP Tally 연결 실패: {e}")
        return False


def test_websocket_connection():
    """WebSocket 서버 연결 테스트"""
    print("\n=== WebSocket 서버 연결 테스트 시작 ===")
    
    try:
        import asyncio
        import websockets
        import json
        
        async def test_ws():
            uri = "ws://returnfeed.net:8765"
            print(f"[WS] WebSocket 서버 연결 시도: {uri}")
            
            try:
                async with websockets.connect(uri) as websocket:
                    print("[O] WebSocket 연결 성공")
                    
                    # 메시지 수신 대기 (5초)
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(message)
                        print(f"[O] 메시지 수신: {data.get('type', 'unknown')}")
                        return True
                    except asyncio.TimeoutError:
                        print("[!] 메시지 수신 타임아웃 (정상일 수 있음)")
                        return True
                        
            except Exception as e:
                print(f"[X] WebSocket 연결 실패: {e}")
                return False
        
        return asyncio.run(test_ws())
        
    except ImportError:
        print("[X] websockets 모듈이 설치되지 않음")
        return False


if __name__ == "__main__":
    print("PD 소프트웨어 컴포넌트 테스트\n")
    
    # 각 컴포넌트 테스트
    ndi_ok = test_ndi_basic()
    vmix_ok = test_vmix_connection()
    ws_ok = test_websocket_connection()
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    print(f"NDI 기본 기능: {'[O] 정상' if ndi_ok else '[X] 실패'}")
    print(f"vMix 연결: {'[O] 정상' if vmix_ok else '[X] 실패'}")
    print(f"WebSocket 서버: {'[O] 정상' if ws_ok else '[X] 실패'}")
    
    if not all([ndi_ok, vmix_ok, ws_ok]):
        print("\n[!] 일부 테스트가 실패했습니다. 위의 오류 메시지를 확인하세요.")
        sys.exit(1)
    else:
        print("\n[O] 모든 테스트 통과!")
        sys.exit(0)