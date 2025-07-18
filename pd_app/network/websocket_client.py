# pd_app/network/websocket_client.py
"""
WebSocket Client - 서버와의 실시간 통신 관리
"""

import json
import time
import asyncio
import logging
import websockets
from websockets.exceptions import ConnectionClosed
from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)

class WebSocketClient(QThread):
    """WebSocket 클라이언트 스레드"""
    
    # 시그널 정의
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    message_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    connection_status_changed = pyqtSignal(str, str)
    connection_state_changed = pyqtSignal(bool)  # 연결 상태 변경 (bool)
    
    def __init__(self, server_url=None):
        super().__init__()
        # 기본값을 constants에서 가져오기
        from ..config.constants import DEFAULT_WEBSOCKET_URL
        self.server_url = server_url if server_url else DEFAULT_WEBSOCKET_URL
        self.websocket = None
        self.running = False
        self.message_queue = None
        self.loop = None
        self.unique_address = None  # 고유 주소 저장
        
    def run(self):
        """WebSocket 스레드 실행"""
        self.running = True
        logger.info("WebSocket 클라이언트 시작")
        
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.message_queue = asyncio.Queue()
            self.loop.run_until_complete(self.main_loop())
            
        except Exception as e:
            logger.error(f"WebSocket 루프 오류: {e}")
            self.error_occurred.emit(str(e))
            
        finally:
            if self.loop:
                self.loop.close()
            logger.info("WebSocket 클라이언트 종료")
            
    async def main_loop(self):
        """메인 연결 루프"""
        while self.running:
            try:
                logger.info(f"WebSocket 연결 시도: {self.server_url}")
                self.connection_status_changed.emit("서버 연결 시도...", "orange")
                
                # 연결 옵션 설정
                connect_kwargs = {
                    'ping_interval': 20,
                    'ping_timeout': 20,
                }
                
                # SSL 관련 설정 (ws://는 SSL 불필요)
                if self.server_url.startswith('wss://'):
                    import ssl
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    connect_kwargs['ssl'] = ssl_context
                
                async with websockets.connect(
                    self.server_url,
                    **connect_kwargs
                ) as websocket:
                    self.websocket = websocket
                    self.connected.emit()
                    self.connection_state_changed.emit(True)  # 연결 상태 변경
                    self.connection_status_changed.emit("서버 연결됨", "green")
                    
                    # 통신 루프 실행
                    await self.communication_loop(websocket)
                    
            except Exception as e:
                logger.error(f"WebSocket 연결 실패: {e}")
                self.error_occurred.emit(str(e))
                
            if self.running:
                self.disconnected.emit()
                self.connection_state_changed.emit(False)  # 연결 상태 변경
                self.connection_status_changed.emit("서버 연결 끊김", "red")
                await asyncio.sleep(5)  # 5초 후 재연결
                
    async def communication_loop(self, websocket):
        """송수신 통신 루프"""
        sender_task = asyncio.create_task(self.sender(websocket))
        receiver_task = asyncio.create_task(self.receiver(websocket))
        
        done, pending = await asyncio.wait(
            [sender_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in pending:
            task.cancel()
            
    async def sender(self, websocket):
        """메시지 송신"""
        while self.running:
            try:
                message = await self.message_queue.get()
                if message is None:
                    break
                    
                await websocket.send(json.dumps(message))
                logger.debug(f"메시지 전송: {message}")
                
            except Exception as e:
                logger.error(f"메시지 전송 오류: {e}")
                break
                
    async def receiver(self, websocket):
        """메시지 수신"""
        last_server_signal = time.time()
        server_timeout = 180  # 180초 타임아웃으로 증가
        ping_interval = 90  # 90초마다 클라이언트에서 핑 전송 (성능 최적화)
        last_ping_sent = time.time()
        
        while self.running:
            try:
                # 메시지 수신 (1초 타임아웃)
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                last_server_signal = time.time()
                
                # JSON 파싱
                data = json.loads(message)
                self.message_received.emit(data)
                logger.debug(f"메시지 수신: {data}")
                
                # 핑 메시지 처리
                if data.get("type") == "ping":
                    await websocket.send(json.dumps({"type": "pong", "timestamp": time.time()}))
                    logger.debug("Pong 전송")
                    
            except asyncio.TimeoutError:
                # 주기적으로 핑 전송
                if time.time() - last_ping_sent > ping_interval:
                    try:
                        await websocket.send(json.dumps({"type": "ping", "timestamp": time.time()}))
                        logger.debug("Ping 전송")
                        last_ping_sent = time.time()
                    except:
                        pass
                
                # 서버 타임아웃 체크 (input_list 같은 메시지도 신호로 간주)
                if time.time() - last_server_signal > server_timeout:
                    logger.error(f"{server_timeout}초 이상 서버 응답 없음")
                    break
                continue
                
            except (ConnectionClosed, json.JSONDecodeError) as e:
                logger.error(f"수신 오류: {e}")
                break
                
            except Exception as e:
                logger.error(f"예상치 못한 수신 오류: {e}")
                break
                
    def send_message(self, message):
        """메시지 전송 (외부 호출용)"""
        if self.loop and self.loop.is_running() and self.message_queue:
            asyncio.run_coroutine_threadsafe(
                self.message_queue.put(message),
                self.loop
            )
            
    def send_tally_update(self, pgm, pvw):
        """Tally 업데이트 전송"""
        message = {
            "type": "tally_update",
            "program": pgm,
            "preview": pvw,
            "timestamp": time.time()
        }
        self.send_message(message)
        
    def send_input_list(self, inputs):
        """입력 목록 전송"""
        message = {
            "type": "input_list",
            "inputs": inputs,
            "timestamp": time.time()
        }
        self.send_message(message)
        
    def send_stream_status(self, stream_name, status):
        """스트림 상태 전송"""
        message = {
            "type": "stream_status",
            "stream_name": stream_name,
            "status": status,
            "timestamp": time.time()
        }
        self.send_message(message)
        
    def send_auth_info(self, user_info):
        """인증 정보 전송"""
        message = {
            "type": "auth_info",
            "user_id": user_info.get('user_id'),
            "unique_address": user_info.get('unique_address'),
            "timestamp": time.time()
        }
        self.send_message(message)
        
    def set_unique_address(self, unique_address):
        """고유 주소 설정"""
        self.unique_address = unique_address
        logger.info(f"WebSocket 클라이언트 고유 주소 설정: {unique_address}")
        
    def stop(self):
        """클라이언트 중지"""
        self.running = False
        
        if self.message_queue and self.loop:
            # None을 보내서 sender 종료
            asyncio.run_coroutine_threadsafe(
                self.message_queue.put(None),
                self.loop
            )
            
        self.wait()  # 스레드 종료 대기
        logger.info("WebSocket 클라이언트 중지 완료")
        
    def is_connected(self):
        """연결 상태 확인"""
        return self.websocket is not None and not self.websocket.closed