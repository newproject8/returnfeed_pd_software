# pd_app/core/vmix_manager.py
"""
vMix Manager - vMix TCP Tally 시스템 관리
WebSocket 기반 실시간 제로 레이턴시 구현
"""

import socket
import asyncio
import threading
import time
import json
import logging
import requests
import xml.etree.ElementTree as ET
import websockets
from websockets.exceptions import ConnectionClosed

try:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal
except ImportError:
    # Qt가 없는 환경에서도 기본 기능 사용 가능
    class QObject:
        pass
    class QThread:
        def __init__(self):
            pass
        def start(self):
            pass
        def wait(self):
            pass
        def run(self):
            pass
    class pyqtSignal:
        def __init__(self, *args):
            pass
        def emit(self, *args):
            pass
        def connect(self, *args):
            pass

logger = logging.getLogger(__name__)

class VMixTCPListener(QThread):
    """vMix TCP Tally 리스너 스레드 - 실시간 제로 레이턴시"""
    tally_activity_detected = pyqtSignal()
    connection_status_changed = pyqtSignal(str, str)
    
    def __init__(self, vmix_ip="127.0.0.1", vmix_tcp_port=8099):
        super().__init__()
        self.vmix_ip = vmix_ip
        self.vmix_tcp_port = vmix_tcp_port
        self.sock = None
        self.running = False
        self.last_tally_data = None
        
    def run(self):
        """TCP 리스너 실행 - 즉시 반응"""
        self.running = True
        logger.info("vMix TCP 리스너 시작 (제로 레이턴시 모드)")
        
        while self.running:
            try:
                # vMix 연결 시도
                self.connection_status_changed.emit(
                    f"vMix TCP ({self.vmix_ip}:{self.vmix_tcp_port}) 연결 시도", 
                    "orange"
                )
                
                self.sock = socket.create_connection(
                    (self.vmix_ip, self.vmix_tcp_port), 
                    timeout=2
                )
                
                self.connection_status_changed.emit(
                    "vMix TCP 연결 성공 (실시간 감지)", 
                    "green"
                )
                
                # TALLY 구독
                self.sock.sendall(b"SUBSCRIBE TALLY\r\n")
                
                # 초기 상태 가져오기
                self.tally_activity_detected.emit()
                
                # 데이터 수신 루프 - 즉시 반응
                buffer = ""
                self.sock.settimeout(0.1)  # 100ms 타임아웃으로 빠른 응답
                
                while self.running:
                    try:
                        data = self.sock.recv(1024)
                        if not data:
                            logger.info("vMix 연결 끊김")
                            break
                            
                        buffer += data.decode('utf-8', errors='ignore')
                        
                        # 라인별로 처리
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            
                            # TALLY OK 메시지 즉시 감지
                            if line.startswith('TALLY OK'):
                                # 실제 탈리 데이터 파싱
                                tally_data = line[9:]  # 'TALLY OK ' 이후 데이터
                                
                                # 변경사항이 있을 때만 이벤트 발생
                                if tally_data != self.last_tally_data:
                                    self.last_tally_data = tally_data
                                    logger.debug(f"TALLY 변경 감지: {tally_data}")
                                    self.tally_activity_detected.emit()
                                    
                    except socket.timeout:
                        # 타임아웃은 정상 - 계속 진행
                        continue
                    except socket.error as e:
                        if self.running:
                            logger.error(f"소켓 오류: {e}")
                        break
                    except Exception as e:
                        logger.error(f"예상치 못한 오류: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"TCP 루프 오류: {e}")
                
            finally:
                if self.sock:
                    self.sock.close()
                    self.sock = None
                self.connection_status_changed.emit("vMix TCP 연결 끊김", "red")
                
            if self.running:
                time.sleep(5)  # 재연결 대기
                
    def stop(self):
        """리스너 중지"""
        self.running = False
        if self.sock:
            self.sock.close()
        self.wait()

class VMixWebSocketRelay(QThread):
    """WebSocket 릴레이 스레드 - 실시간 전송"""
    websocket_status_changed = pyqtSignal(str, str)
    
    def __init__(self, relay_server_url="wss://returnfeed.net/ws/", enable_websocket=True):
        super().__init__()
        self.relay_server_url = relay_server_url
        self.message_queue = None
        self.running = False
        self.loop = None
        self.enable_websocket = enable_websocket
        
    def run(self):
        """WebSocket 릴레이 실행"""
        if not self.enable_websocket:
            logger.info("WebSocket 비활성화됨")
            return
            
        self.running = True
        logger.info("WebSocket 릴레이 시작")
        
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.message_queue = asyncio.Queue()
            self.loop.run_until_complete(self.websocket_loop())
        except Exception as e:
            logger.error(f"WebSocket 루프 오류: {e}")
        finally:
            if self.loop:
                self.loop.close()
                
    async def websocket_loop(self):
        """WebSocket 메인 루프"""
        while self.running:
            try:
                self.websocket_status_changed.emit("WebSocket 연결 시도", "orange")
                
                async with websockets.connect(
                    self.relay_server_url, 
                    ssl=True, 
                    ping_interval=20, 
                    ping_timeout=10
                ) as websocket:
                    self.websocket_status_changed.emit("WebSocket 연결 성공", "green")
                    
                    # 송신/수신 태스크 생성
                    sender_task = asyncio.create_task(self.sender(websocket))
                    receiver_task = asyncio.create_task(self.receiver(websocket))
                    
                    # 완료될 때까지 대기
                    done, pending = await asyncio.wait(
                        [sender_task, receiver_task], 
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    # 미완료 태스크 취소
                    for task in pending:
                        task.cancel()
                        
            except Exception as e:
                logger.error(f"WebSocket 연결 실패: {e}")
                
            if self.running:
                self.websocket_status_changed.emit("WebSocket 연결 끊김", "red")
                await asyncio.sleep(5)
                
    async def sender(self, websocket):
        """메시지 송신"""
        while self.running:
            try:
                message = await self.message_queue.get()
                if message is None:
                    break
                await websocket.send(json.dumps(message))
                self.message_queue.task_done()
            except Exception as e:
                logger.error(f"메시지 송신 오류: {e}")
                break
                
    async def receiver(self, websocket):
        """메시지 수신"""
        while self.running:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                # 핑 응답
                if data.get("type") == "ping":
                    await self.message_queue.put({
                        "type": "pong", 
                        "timestamp": time.time()
                    })
                    
            except ConnectionClosed:
                logger.info("WebSocket 연결 종료")
                break
            except Exception as e:
                logger.error(f"메시지 수신 오류: {e}")
                break
                
    def send_message(self, message):
        """메시지 전송"""
        if not self.enable_websocket:
            return
            
        if self.loop and self.loop.is_running() and self.message_queue:
            asyncio.run_coroutine_threadsafe(
                self.message_queue.put(message), 
                self.loop
            )
            
    def stop(self):
        """릴레이 중지"""
        self.running = False
        if self.loop and self.loop.is_running():
            self.send_message(None)
        self.wait()

class VMixManager(QObject):
    """vMix 관리자 - 실시간 제로 레이턴시 Tally 시스템"""
    
    # 시그널 정의
    tally_updated = pyqtSignal(int, int, dict, dict)  # pgm, pvw, pgm_info, pvw_info
    connection_status_changed = pyqtSignal(str, str)
    input_list_updated = pyqtSignal(dict)
    websocket_status_changed = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.tcp_listener = None
        self.websocket_relay = None
        self.vmix_ip = "127.0.0.1"
        self.http_port = 8088
        self.tcp_port = 8099
        self.input_names = {}
        self.last_pgm = 0
        self.last_pvw = 0
        self.last_input_hash = 0
        self.is_connected = False
        
    def connect_to_vmix(self, ip="127.0.0.1", http_port=8088, tcp_port=8099):
        """vMix 연결 - 실시간 제로 레이턴시 모드"""
        try:
            self.vmix_ip = ip
            self.http_port = http_port
            self.tcp_port = tcp_port
            
            # 기존 연결 정리
            if self.tcp_listener:
                self.tcp_listener.stop()
            if self.websocket_relay:
                self.websocket_relay.stop()
                
            # WebSocket 릴레이 시작 (실시간 브로드캐스트)
            self.websocket_relay = VMixWebSocketRelay(enable_websocket=True)
            self.websocket_relay.websocket_status_changed.connect(self.websocket_status_changed)
            self.websocket_relay.start()
            
            # TCP 리스너 시작
            self.tcp_listener = VMixTCPListener(ip, tcp_port)
            self.tcp_listener.tally_activity_detected.connect(self.fetch_and_broadcast_vmix_state)
            self.tcp_listener.connection_status_changed.connect(self._on_tcp_status_changed)
            self.tcp_listener.start()
            
            self.is_connected = True
            logger.info(f"vMix 실시간 연결 시작: {ip}:{http_port}/{tcp_port}")
            
        except Exception as e:
            logger.error(f"vMix 연결 실패: {e}")
            self.connection_status_changed.emit(f"연결 실패: {e}", "red")
            
    def disconnect_from_vmix(self):
        """vMix 연결 해제"""
        try:
            if self.tcp_listener:
                self.tcp_listener.stop()
                self.tcp_listener = None
                
            if self.websocket_relay:
                self.websocket_relay.stop()
                self.websocket_relay = None
                
            self.is_connected = False
            self.connection_status_changed.emit("연결 해제됨", "gray")
            logger.info("vMix 연결 해제")
            
        except Exception as e:
            logger.error(f"vMix 연결 해제 오류: {e}")
            
    def fetch_and_broadcast_vmix_state(self):
        """HTTP API로 vMix 상태 가져오기 및 실시간 브로드캐스트"""
        try:
            # TCP 이벤트가 발생했으므로 즉시 HTTP로 정확한 상태 조회
            url = f"http://{self.vmix_ip}:{self.http_port}/api"
            
            # 매우 짧은 타임아웃으로 빠른 응답
            response = requests.get(url, timeout=0.5)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            
            # PGM/PVW 정보
            pgm = int(root.find('active').text)
            pvw = int(root.find('preview').text)
            
            # 입력 목록
            inputs = {}
            for input_elem in root.findall('.//input'):
                input_num = int(input_elem.get('number'))
                input_info = {
                    'number': input_num,
                    'name': input_elem.get('title', f'Input {input_num}'),
                    'type': input_elem.get('type', 'Unknown')
                }
                inputs[input_num] = input_info
                
            # 입력 목록 변경 감지 및 브로드캐스트
            current_input_hash = hash(json.dumps(inputs, sort_keys=True))
            if current_input_hash != self.last_input_hash:
                self.last_input_hash = current_input_hash
                self.input_names = inputs
                self.input_list_updated.emit(self.input_names)
                
                # WebSocket으로 실시간 전송
                if self.websocket_relay:
                    self.websocket_relay.send_message({
                        "type": "input_list",
                        "inputs": {str(k): v for k, v in inputs.items()},
                        "timestamp": time.time()
                    })
                    
                logger.info(f"입력 목록 업데이트 및 브로드캐스트: {len(self.input_names)}개")
                
            # Tally 정보 변경 감지 및 실시간 브로드캐스트
            if pgm != self.last_pgm or pvw != self.last_pvw:
                self.last_pgm = pgm
                self.last_pvw = pvw
                
                pgm_info = self.input_names.get(pgm, {'name': f'Input {pgm}', 'type': 'Unknown'})
                pvw_info = self.input_names.get(pvw, {'name': f'Input {pvw}', 'type': 'Unknown'})
                
                # 로컬 UI 업데이트
                self.tally_updated.emit(pgm, pvw, pgm_info, pvw_info)
                
                # WebSocket으로 실시간 전송 (레이턴시 최소화)
                if self.websocket_relay:
                    self.websocket_relay.send_message({
                        "type": "tally_update",
                        "program": pgm,
                        "preview": pvw,
                        "program_info": pgm_info,
                        "preview_info": pvw_info,
                        "timestamp": time.time()
                    })
                    
                logger.debug(f"Tally 실시간 브로드캐스트 - PGM: {pgm}, PVW: {pvw}")
                
        except requests.RequestException as e:
            logger.error(f"vMix API 요청 실패: {e}")
            self.connection_status_changed.emit("API 요청 실패", "orange")
            
        except Exception as e:
            logger.error(f"vMix 상태 처리 오류: {e}")
            
    def get_input_list(self):
        """현재 입력 목록 반환"""
        return self.input_names
        
    def get_current_tally(self):
        """현재 Tally 상태 반환"""
        return {
            'pgm': self.last_pgm,
            'pvw': self.last_pvw,
            'pgm_info': self.input_names.get(self.last_pgm, {}),
            'pvw_info': self.input_names.get(self.last_pvw, {})
        }
        
    def _on_tcp_status_changed(self, status, color):
        """TCP 연결 상태 변경 처리"""
        self.connection_status_changed.emit(status, color)