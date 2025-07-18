# pd_app/network/tcp_client.py
"""
TCP Client - TCP 통신 관리 (향후 확장용)
"""

import socket
import threading
import logging
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class TCPClient(QObject):
    """TCP 클라이언트"""
    
    # 시그널 정의
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, host=None, port=None):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = None
        self.receive_thread = None
        self.running = False
        
    def connect(self, host=None, port=None):
        """서버 연결"""
        if host:
            self.host = host
        if port:
            self.port = port
            
        if not self.host or not self.port:
            self.error_occurred.emit("호스트와 포트를 지정하세요")
            return False
            
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5초 타임아웃
            self.socket.connect((self.host, self.port))
            
            self.running = True
            self.connected.emit()
            
            # 수신 스레드 시작
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"TCP 연결 성공: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            error_msg = f"TCP 연결 실패: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
    def disconnect(self):
        """연결 해제"""
        self.running = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
            
        self.disconnected.emit()
        logger.info("TCP 연결 해제")
        
    def send(self, data):
        """데이터 전송"""
        if not self.socket:
            self.error_occurred.emit("연결되지 않음")
            return False
            
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            self.socket.sendall(data)
            return True
            
        except Exception as e:
            error_msg = f"전송 실패: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
    def _receive_loop(self):
        """수신 루프"""
        buffer = b""
        
        while self.running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    logger.info("서버가 연결을 종료했습니다")
                    break
                    
                buffer += data
                
                # 데이터 처리 (필요에 따라 프로토콜 구현)
                self.data_received.emit(buffer)
                buffer = b""
                
            except socket.timeout:
                continue
                
            except Exception as e:
                if self.running:
                    logger.error(f"수신 오류: {e}")
                break
                
        self.running = False
        self.disconnected.emit()
        
    def is_connected(self):
        """연결 상태 확인"""
        return self.socket is not None and self.running