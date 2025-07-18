# vmix_manager.py
import socket
import asyncio
import json
import time
import requests
import xml.etree.ElementTree as ET
import websockets
from websockets.exceptions import ConnectionClosed
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import logging


class NetworkThread(QThread):
    """기본 네트워크 스레드 클래스"""
    def __init__(self, name: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.thread_name = name
        self.running = False
        self.logger = logging.getLogger(f"thread.{name}")
        
    def stop(self):
        self.running = False
        self.logger.info("Stop signal received")
        
    def log_info(self, msg):
        self.logger.info(msg)
        
    def log_error(self, msg):
        self.logger.error(msg)


class vMixTCPListener(NetworkThread):
    """vMix TCP Tally 리스너"""
    
    tally_changed = pyqtSignal()  # Tally 변경 감지 시그널
    connection_status_changed = pyqtSignal(str, str)  # status, color
    
    def __init__(self, vmix_ip: str = "127.0.0.1", vmix_tcp_port: int = 8099):
        super().__init__("vMixTCP")
        self.vmix_ip = vmix_ip
        self.vmix_tcp_port = vmix_tcp_port
        self.sock = None
        
    def run(self):
        self.running = True
        self.log_info("Thread started")
        
        while self.running:
            try:
                self.connection_status_changed.emit(
                    f"vMix TCP ({self.vmix_ip}:{self.vmix_tcp_port}) 연결 시도", "orange"
                )
                
                self.sock = socket.create_connection(
                    (self.vmix_ip, self.vmix_tcp_port), timeout=5
                )
                self.connection_status_changed.emit(
                    "vMix TCP 연결 성공 (감지 대기중)", "green"
                )
                
                self.sock.sendall(b"SUBSCRIBE TALLY\r\n")
                
                # 초기 상태 가져오기
                self.tally_changed.emit()
                
                buffer = ""
                while self.running:
                    try:
                        data = self.sock.recv(1024)
                        if not data:
                            self.log_info("vMix connection closed")
                            break
                            
                        buffer += data.decode('utf-8', errors='ignore')
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            if line.startswith('TALLY OK'):
                                self.log_info("TALLY OK received")
                                self.tally_changed.emit()
                                
                    except socket.timeout:
                        continue
                    except socket.error:
                        break
                        
            except Exception as e:
                self.log_error(f"TCP loop error: {e}")
                
            finally:
                if self.sock:
                    self.sock.close()
                    self.sock = None
                self.connection_status_changed.emit("vMix TCP 연결 끊김", "red")
                
            if self.running:
                time.sleep(5)  # 재연결 대기
                
        self.log_info("Thread stopped")


class WebSocketRelay(NetworkThread):
    """WebSocket 릴레이 클라이언트"""
    
    connection_status_changed = pyqtSignal(str, str)  # status, color
    
    def __init__(self, relay_server: str, port: int, use_ssl: bool = True):
        super().__init__("WebSocketRelay")
        self.relay_server = relay_server
        self.port = port
        self.use_ssl = use_ssl
        proto = "wss" if use_ssl else "ws"
        self.ws_uri = f"{proto}://{relay_server}/ws/"
        self.message_queue = asyncio.Queue()
        self.loop = None
        
    def run(self):
        self.running = True
        self.log_info("Thread started")
        
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.main_loop())
        except Exception as e:
            self.log_error(f"Asyncio loop fatal error: {e}")
        finally:
            self.log_info("Closing asyncio event loop")
            self.loop.close()
            
        self.log_info("Thread stopped")
        
    async def main_loop(self):
        while self.running:
            try:
                self.connection_status_changed.emit(
                    f"서버({self.ws_uri}) 연결 시도...", "orange"
                )
                
                async with websockets.connect(
                    self.ws_uri, ssl=self.use_ssl, ping_interval=20, ping_timeout=20
                ) as websocket:
                    self.connection_status_changed.emit("서버 연결 성공", "green")
                    await self.communication_loop(websocket)
                    
            except Exception as e:
                self.log_error(f"WebSocket connection failed: {e}")
                
            if self.running:
                self.connection_status_changed.emit("서버 연결 끊김", "red")
                await asyncio.sleep(5)
                
    async def sender(self, websocket):
        while self.running:
            message = await self.message_queue.get()
            if message is None:
                break
            await websocket.send(json.dumps(message))
            self.message_queue.task_done()
            
    async def receiver(self, websocket):
        last_signal_time = time.time()
        SERVER_TIMEOUT = 90
        
        while self.running:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                last_signal_time = time.time()
                data = json.loads(message)
                
                if data.get("type") == "ping":
                    await self.message_queue.put({"type": "pong", "timestamp": time.time()})
                    
            except asyncio.TimeoutError:
                if time.time() - last_signal_time > SERVER_TIMEOUT:
                    self.log_error(f"No signal from server for {SERVER_TIMEOUT}s")
                    break
                continue
            except (ConnectionClosed, Exception) as e:
                self.log_error(f"Receive error: {e}")
                break
                
    async def communication_loop(self, websocket):
        sender_task = asyncio.create_task(self.sender(websocket))
        receiver_task = asyncio.create_task(self.receiver(websocket))
        done, pending = await asyncio.wait(
            [sender_task, receiver_task], return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
            
    def send_message(self, message: Dict[str, Any]):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.message_queue.put(message), self.loop
            )
            
    def stop(self):
        super().stop()
        if self.loop and self.loop.is_running():
            self.send_message(None)


class vMixManager(QObject):
    """vMix 통신 관리자"""
    
    # 시그널
    tally_updated = pyqtSignal(int, int, str, str)  # pgm, pvw, pgm_name, pvw_name
    input_list_updated = pyqtSignal(dict)  # {number: name}
    vmix_status_changed = pyqtSignal(str, str)  # status, color
    relay_status_changed = pyqtSignal(str, str)  # status, color
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.vmix_ip = "127.0.0.1"
        self.vmix_http_port = 8088
        self.relay_server = "returnfeed.net"
        self.relay_port = 443
        
        self.tcp_listener = None
        self.ws_relay = None
        
        self.input_names = {}
        self.last_pgm = 0
        self.last_pvw = 0
        self.last_input_hash = 0
        
        self.logger = logging.getLogger("vMixManager")
        
    def initialize(self, vmix_ip: str, vmix_http_port: int, 
                   relay_server: str, relay_port: int) -> bool:
        """매니저 초기화"""
        try:
            self.vmix_ip = vmix_ip
            self.vmix_http_port = vmix_http_port
            self.relay_server = relay_server
            self.relay_port = relay_port
            
            # TCP 리스너 생성
            self.tcp_listener = vMixTCPListener(vmix_ip)
            self.tcp_listener.tally_changed.connect(self._on_tally_changed)
            self.tcp_listener.connection_status_changed.connect(self.vmix_status_changed)
            
            # WebSocket 릴레이 생성
            self.ws_relay = WebSocketRelay(relay_server, relay_port, use_ssl=True)
            self.ws_relay.connection_status_changed.connect(self.relay_status_changed)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            return False
            
    def start(self) -> bool:
        """통신 시작"""
        try:
            # vMix TCP 리스너 자동 시작
            if self.tcp_listener and not self.tcp_listener.isRunning():
                self.tcp_listener.start()
                self.logger.info("vMix TCP listener started automatically")
            
            # WebSocket relay는 선택적으로 시작 (relay 서버가 localhost이면 비활성화)
            if self.ws_relay and self.relay_server != "localhost" and self.relay_server != "127.0.0.1":
                try:
                    self.ws_relay.start()
                    self.logger.info("WebSocket relay started")
                except Exception as e:
                    self.logger.warning(f"WebSocket relay start failed (non-critical): {e}")
                    # WebSocket relay 실패는 치명적이지 않음
            else:
                self.logger.info("WebSocket relay disabled (localhost or not configured)")
                
            return True
        except Exception as e:
            self.logger.error(f"Start failed: {e}")
            return False
            
    def connect_vmix(self) -> bool:
        """vMix 연결"""
        try:
            if self.tcp_listener and not self.tcp_listener.isRunning():
                self.tcp_listener.start()
                return True
            return False
        except Exception as e:
            self.logger.error(f"vMix connection failed: {e}")
            return False
            
    def disconnect_vmix(self) -> bool:
        """vMix 연결 해제"""
        try:
            if self.tcp_listener and self.tcp_listener.isRunning():
                self.tcp_listener.stop()
                self.tcp_listener.wait(1000)
                return True
            return False
        except Exception as e:
            self.logger.error(f"vMix disconnection failed: {e}")
            return False
            
    def stop(self) -> None:
        """통신 정지"""
        if self.tcp_listener:
            self.tcp_listener.stop()
            self.tcp_listener.wait(1000)
            
        if self.ws_relay:
            self.ws_relay.stop()
            self.ws_relay.wait(1000)
            
    def _on_tally_changed(self):
        """Tally 변경 감지 시 호출"""
        try:
            url = f"http://{self.vmix_ip}:{self.vmix_http_port}/api"
            response = requests.get(url, timeout=0.5)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            pgm = int(root.find('active').text)
            pvw = int(root.find('preview').text)
            inputs = [
                {"number": int(e.get('number')), "name": e.get('title')} 
                for e in root.findall('.//input')
            ]
            
            # 입력 목록 업데이트
            current_hash = hash(json.dumps(inputs, sort_keys=True))
            if current_hash != self.last_input_hash:
                self.last_input_hash = current_hash
                self.input_names = {item["number"]: item["name"] for item in inputs}
                self.input_list_updated.emit(self.input_names)
                
                # 릴레이 서버에 전송
                if self.ws_relay:
                    self.ws_relay.send_message({
                        "type": "input_list",
                        "inputs": self.input_names
                    })
                    
            # Tally 정보 업데이트
            if pgm != self.last_pgm or pvw != self.last_pvw:
                self.last_pgm, self.last_pvw = pgm, pvw
                
                pgm_name = self.input_names.get(pgm, f"Input {pgm}")
                pvw_name = self.input_names.get(pvw, f"Input {pvw}")
                
                self.logger.info(f"Tally changed - PGM: {pgm_name} ({pgm}), PVW: {pvw_name} ({pvw})")
                self.tally_updated.emit(pgm, pvw, pgm_name, pvw_name)
                
                # 릴레이 서버에 전송
                if self.ws_relay:
                    self.ws_relay.send_message({
                        "type": "tally_update",
                        "program": pgm,
                        "preview": pvw
                    })
                    
        except requests.RequestException as e:
            self.logger.error(f"HTTP API request failed: {e}")
            self.vmix_status_changed.emit("API 요청 실패", "orange")
        except Exception as e:
            self.logger.error(f"Tally processing error: {e}")