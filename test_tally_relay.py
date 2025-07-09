#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tally 릴레이 시스템 테스트
PD 앱과 카메라맨 클라이언트 시뮬레이션
"""

import asyncio
import websockets
import json
import time
import sys

# 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class PD_Client:
    """PD 앱 시뮬레이션"""
    
    def __init__(self, server_url="ws://returnfeed.net:8765"):
        self.server_url = server_url
        
    async def run(self):
        """PD 클라이언트 실행"""
        print(f"{BLUE}[PD] 릴레이 서버 연결 시도: {self.server_url}{RESET}")
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"{GREEN}[PD] 릴레이 서버 연결 성공!{RESET}")
                
                # 1. 입력 목록 전송
                input_list = {
                    "type": "input_list",
                    "inputs": {
                        "1": {"number": 1, "name": "CAM 1 - 메인", "type": "Camera"},
                        "2": {"number": 2, "name": "CAM 2 - 서브", "type": "Camera"},
                        "3": {"number": 3, "name": "PPT 화면", "type": "Desktop"},
                        "4": {"number": 4, "name": "동영상", "type": "Video"}
                    },
                    "timestamp": time.time()
                }
                
                await websocket.send(json.dumps(input_list))
                print(f"{YELLOW}[PD] 입력 목록 전송 완료{RESET}")
                
                # 2. Tally 상태 주기적 전송
                tally_sequence = [
                    {"program": 1, "preview": 2},
                    {"program": 2, "preview": 3},
                    {"program": 3, "preview": 4},
                    {"program": 4, "preview": 1}
                ]
                
                for i, tally in enumerate(tally_sequence):
                    tally_msg = {
                        "type": "tally_update",
                        "program": tally["program"],
                        "preview": tally["preview"],
                        "timestamp": time.time()
                    }
                    
                    await websocket.send(json.dumps(tally_msg))
                    print(f"{YELLOW}[PD] Tally 전송: PGM={tally['program']}, PVW={tally['preview']}{RESET}")
                    
                    await asyncio.sleep(3)  # 3초마다 변경
                    
        except Exception as e:
            print(f"{RED}[PD] 오류 발생: {e}{RESET}")

class Cameraman_Client:
    """카메라맨 클라이언트 시뮬레이션"""
    
    def __init__(self, camera_id, server_url="ws://returnfeed.net:8765"):
        self.camera_id = camera_id
        self.server_url = server_url
        self.input_list = {}
        
    async def run(self):
        """카메라맨 클라이언트 실행"""
        print(f"{BLUE}[CAM{self.camera_id}] 릴레이 서버 연결 시도{RESET}")
        
        try:
            async with websockets.connect(self.server_url) as websocket:
                print(f"{GREEN}[CAM{self.camera_id}] 릴레이 서버 연결 성공!{RESET}")
                
                # 메시지 수신 루프
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if data.get("type") == "input_list":
                            # 입력 목록 저장
                            self.input_list = data.get("inputs", {})
                            print(f"{BLUE}[CAM{self.camera_id}] 입력 목록 수신: {len(self.input_list)}개{RESET}")
                            
                        elif data.get("type") == "tally_update":
                            # Tally 상태 처리
                            pgm = data.get("program", 0)
                            pvw = data.get("preview", 0)
                            
                            # 내 카메라 상태 확인
                            if pgm == self.camera_id:
                                pgm_info = self.input_list.get(str(pgm), {})
                                print(f"{RED}[CAM{self.camera_id}] ★ ON AIR ★ - {pgm_info.get('name', f'Input {pgm}')}{RESET}")
                            elif pvw == self.camera_id:
                                pvw_info = self.input_list.get(str(pvw), {})
                                print(f"{GREEN}[CAM{self.camera_id}] ◆ PREVIEW ◆ - {pvw_info.get('name', f'Input {pvw}')}{RESET}")
                            else:
                                print(f"{YELLOW}[CAM{self.camera_id}] 대기 중... (PGM={pgm}, PVW={pvw}){RESET}")
                                
                    except json.JSONDecodeError:
                        print(f"{RED}[CAM{self.camera_id}] JSON 파싱 오류{RESET}")
                        
        except Exception as e:
            print(f"{RED}[CAM{self.camera_id}] 오류 발생: {e}{RESET}")

async def test_local():
    """로컬 테스트 (localhost)"""
    print(f"\n{BLUE}=== 로컬 릴레이 서버 테스트 ==={RESET}\n")
    
    # 로컬 서버 URL
    local_url = "ws://localhost:8765"
    
    # PD 클라이언트
    pd_client = PD_Client(local_url)
    
    # 카메라맨 클라이언트 3개
    cam_clients = [
        Cameraman_Client(1, local_url),
        Cameraman_Client(2, local_url),
        Cameraman_Client(3, local_url)
    ]
    
    # 모든 클라이언트 동시 실행
    tasks = [pd_client.run()]
    tasks.extend([cam.run() for cam in cam_clients])
    
    await asyncio.gather(*tasks)

async def test_remote():
    """원격 테스트 (returnfeed.net)"""
    print(f"\n{BLUE}=== 원격 릴레이 서버 테스트 ==={RESET}\n")
    
    # 원격 서버 URL
    remote_url = "ws://returnfeed.net:8765"
    
    # 테스트 클라이언트
    print("1. 연결 테스트...")
    try:
        async with websockets.connect(remote_url) as ws:
            print(f"{GREEN}원격 서버 연결 성공!{RESET}")
            
            # 간단한 메시지 전송
            test_msg = {"type": "test", "message": "Hello from PD app"}
            await ws.send(json.dumps(test_msg))
            print(f"{YELLOW}테스트 메시지 전송 완료{RESET}")
            
    except Exception as e:
        print(f"{RED}원격 서버 연결 실패: {e}{RESET}")

def print_usage():
    """사용법 출력"""
    print(f"""
{BLUE}Tally 릴레이 시스템 테스트{RESET}

사용법:
  python test_tally_relay.py [옵션]

옵션:
  local   - 로컬 릴레이 서버 테스트 (localhost:8765)
  remote  - 원격 릴레이 서버 테스트 (returnfeed.net:8765)
  
없으면 로컬 테스트 실행
""")

async def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "remote":
            await test_remote()
        elif sys.argv[1] == "local":
            await test_local()
        else:
            print_usage()
    else:
        # 기본: 로컬 테스트
        await test_local()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}테스트 중단됨{RESET}")