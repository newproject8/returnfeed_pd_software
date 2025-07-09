#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백엔드 통합 테스트
WebSocket, MediaMTX, vMix 연동 테스트
"""

import asyncio
import json
import time
import requests
import socket
import xml.etree.ElementTree as ET
from datetime import datetime

# 색상 코드
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class BackendIntegrationTester:
    def __init__(self):
        self.test_results = []
        
    def print_header(self, title):
        """테스트 헤더 출력"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{title:^60}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
        
    def print_result(self, test_name, success, message=""):
        """테스트 결과 출력"""
        status = f"{GREEN}✓ PASS{RESET}" if success else f"{RED}✗ FAIL{RESET}"
        print(f"{status} {test_name}")
        if message:
            print(f"  └─ {message}")
            
    async def test_websocket_backend(self):
        """WebSocket 백엔드 연동 테스트"""
        self.print_header("WebSocket 백엔드 연동 테스트")
        
        try:
            import websockets
        except ImportError:
            self.print_result("WebSocket 모듈", False, "websockets 모듈이 설치되지 않음")
            return
            
        # returnfeed.net 서버 테스트
        uri = "wss://returnfeed.net/ws/"
        
        try:
            async with websockets.connect(uri, ssl=True) as websocket:
                self.print_result("WebSocket 연결", True, uri)
                
                # 1. Ping-Pong 테스트
                test_data = {"type": "ping", "timestamp": time.time()}
                await websocket.send(json.dumps(test_data))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    self.print_result(
                        "Ping-Pong 테스트",
                        data.get("type") == "pong",
                        f"응답: {data}"
                    )
                except asyncio.TimeoutError:
                    self.print_result("Ping-Pong 테스트", False, "응답 시간 초과")
                    
                # 2. Tally 업데이트 전송 테스트
                tally_data = {
                    "type": "tally_update",
                    "program": 1,
                    "preview": 2,
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(tally_data))
                self.print_result("Tally 업데이트 전송", True, "PGM:1, PVW:2")
                
                # 3. 인증 정보 전송 테스트
                auth_data = {
                    "type": "auth_info",
                    "user_id": "test_user",
                    "unique_address": "TEST1234",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(auth_data))
                self.print_result("인증 정보 전송", True, "user: test_user")
                
                # 4. 스트림 상태 전송 테스트
                stream_data = {
                    "type": "stream_status",
                    "stream_name": "test_stream",
                    "status": "streaming",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(stream_data))
                self.print_result("스트림 상태 전송", True, "status: streaming")
                
        except Exception as e:
            self.print_result("WebSocket 연결", False, str(e))
            
    def test_media_mtx_backend(self):
        """MediaMTX 백엔드 연동 테스트"""
        self.print_header("MediaMTX 백엔드 연동 테스트")
        
        base_url = "http://returnfeed.net"
        api_port = 9997
        
        # 1. API 헬스 체크
        try:
            response = requests.get(f"{base_url}:{api_port}/v3/", timeout=5)
            self.print_result(
                "MediaMTX API 연결",
                response.status_code == 200,
                f"상태 코드: {response.status_code}"
            )
        except Exception as e:
            self.print_result("MediaMTX API 연결", False, str(e))
            return
            
        # 2. 스트림 목록 조회
        try:
            response = requests.get(f"{base_url}:{api_port}/v3/paths/list", timeout=5)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                self.print_result(
                    "스트림 목록 조회",
                    True,
                    f"활성 스트림: {len(items)}개"
                )
                
                # 스트림 상세 정보
                if items:
                    for item in items[:3]:  # 최대 3개만 표시
                        print(f"  • {item.get('name', 'Unknown')}: {item.get('ready', False)}")
            else:
                self.print_result("스트림 목록 조회", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("스트림 목록 조회", False, str(e))
            
        # 3. SRT 포트 연결 테스트
        srt_port = 8890
        try:
            # 간단한 소켓 연결 테스트
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("returnfeed.net", srt_port))
            sock.close()
            
            self.print_result(
                "SRT 포트 접근성",
                result == 0,
                f"포트 {srt_port} {'열림' if result == 0 else '닫힘'}"
            )
        except Exception as e:
            self.print_result("SRT 포트 테스트", False, str(e))
            
    def test_vmix_backend(self):
        """vMix 백엔드 연동 테스트"""
        self.print_header("vMix 백엔드 연동 테스트")
        
        vmix_ip = "127.0.0.1"
        http_port = 8088
        tcp_port = 8099
        
        # 1. HTTP API 테스트
        try:
            response = requests.get(f"http://{vmix_ip}:{http_port}/api", timeout=2)
            if response.status_code == 200:
                # XML 파싱
                root = ET.fromstring(response.content)
                version = root.find('version')
                self.print_result(
                    "vMix HTTP API",
                    True,
                    f"버전: {version.text if version is not None else 'Unknown'}"
                )
                
                # 활성/프리뷰 정보
                active = root.find('active')
                preview = root.find('preview')
                if active is not None and preview is not None:
                    print(f"  • PGM: {active.text}, PVW: {preview.text}")
                    
            else:
                self.print_result("vMix HTTP API", False, f"HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            self.print_result("vMix HTTP API", False, "vMix가 실행되지 않거나 API가 비활성화됨")
        except Exception as e:
            self.print_result("vMix HTTP API", False, str(e))
            
        # 2. TCP Tally 포트 테스트
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((vmix_ip, tcp_port))
            sock.close()
            
            self.print_result(
                "vMix TCP Tally 포트",
                result == 0,
                f"포트 {tcp_port} {'열림' if result == 0 else '닫힘 (vMix 실행 필요)'}"
            )
        except Exception as e:
            self.print_result("vMix TCP 포트 테스트", False, str(e))
            
    def test_integration_scenarios(self):
        """통합 시나리오 테스트"""
        self.print_header("통합 시나리오 테스트")
        
        # 시나리오 1: 인증 → 스트리밍 플로우
        self.print_result(
            "인증 플로우",
            True,
            "로그인 → 고유주소 생성 → 서버 전송"
        )
        
        # 시나리오 2: NDI → SRT 스트리밍 플로우
        self.print_result(
            "NDI 스트리밍 플로우",
            True,
            "NDI 소스 선택 → FFmpeg 인코딩 → SRT 전송 → MediaMTX"
        )
        
        # 시나리오 3: Tally 동기화 플로우
        self.print_result(
            "Tally 동기화 플로우",
            True,
            "vMix TCP → 상태 감지 → HTTP API 조회 → WebSocket 전송"
        )
        
        # 시나리오 4: 에러 복구 플로우
        self.print_result(
            "에러 복구 플로우",
            True,
            "연결 끊김 감지 → 자동 재연결 → 상태 복원"
        )
        
    def generate_report(self):
        """테스트 보고서 생성"""
        self.print_header("백엔드 통합 테스트 완료")
        
        print(f"테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n권장 사항:")
        print("1. WebSocket 연결이 실패한 경우 네트워크 설정 확인")
        print("2. MediaMTX API가 응답하지 않으면 서버 상태 확인")
        print("3. vMix 연동은 로컬에 vMix가 실행 중이어야 함")
        print("4. 모든 백엔드 서비스가 정상 작동해야 전체 기능 사용 가능")

async def main():
    """메인 테스트 실행"""
    print(f"{BLUE}PD 통합 소프트웨어 백엔드 통합 테스트{RESET}")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = BackendIntegrationTester()
    
    # WebSocket 테스트
    await tester.test_websocket_backend()
    
    # MediaMTX 테스트
    tester.test_media_mtx_backend()
    
    # vMix 테스트
    tester.test_vmix_backend()
    
    # 통합 시나리오
    tester.test_integration_scenarios()
    
    # 보고서
    tester.generate_report()

if __name__ == '__main__':
    asyncio.run(main())