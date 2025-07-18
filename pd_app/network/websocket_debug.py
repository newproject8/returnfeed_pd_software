#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 디버그 도구 - 연결 상태 확인
"""

import asyncio
import websockets
import json
import time

async def test_connection():
    """WebSocket 연결 테스트"""
    url = "ws://returnfeed.net:8765"
    
    try:
        print(f"연결 시도: {url}")
        async with websockets.connect(url) as websocket:
            print("✓ 연결 성공!")
            
            # 초기 메시지 수신
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"✓ 초기 메시지 수신: {data.get('type', 'unknown')}")
                if data.get('type') == 'input_list':
                    print(f"  입력 목록: {data.get('inputs', {})}")
            except asyncio.TimeoutError:
                print("! 초기 메시지 없음")
            
            # 핑 테스트
            print("\n핑 테스트 시작...")
            for i in range(3):
                ping_msg = {"type": "ping", "timestamp": time.time()}
                await websocket.send(json.dumps(ping_msg))
                print(f"→ 핑 #{i+1} 전송")
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    if data.get('type') == 'pong':
                        print(f"← 퐁 #{i+1} 수신!")
                    else:
                        print(f"← 다른 메시지: {data.get('type')}")
                except asyncio.TimeoutError:
                    print(f"✗ 퐁 #{i+1} 타임아웃")
                
                await asyncio.sleep(2)
            
            # Tally 업데이트 테스트
            print("\nTally 업데이트 전송 테스트...")
            tally_msg = {
                "type": "tally_update",
                "program": 1,
                "preview": 2,
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(tally_msg))
            print("→ Tally 업데이트 전송 (PGM: 1, PVW: 2)")
            
            print("\n연결 유지 중... (10초)")
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"✗ 연결 오류: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("="*60)
    print("WebSocket 디버그 도구")
    print("="*60)
    asyncio.run(test_connection())
    print("\n테스트 완료")