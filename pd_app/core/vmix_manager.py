# pd_app/core/vmix_manager.py
"""
vMix Manager - vMix TCP Tally 시스템 관리
하이브리드 방식 (TCP + HTTP API) 구현
"""

import socket
import asyncio
import threading
import time
import json
import logging
import requests
import xml.etree.ElementTree as ET

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
    """vMix TCP Tally 리스너 스레드"""
    tally_activity_detected = pyqtSignal()
    connection_status_changed = pyqtSignal(str, str)
    
    def __init__(self, vmix_ip="127.0.0.1", vmix_tcp_port=8099):
        super().__init__()
        self.vmix_ip = vmix_ip
        self.vmix_tcp_port = vmix_tcp_port
        self.sock = None
        self.running = False
        
    def run(self):
        """TCP 리스너 실행"""
        self.running = True
        logger.info("vMix TCP 리스너 시작")
        
        while self.running:
            try:
                # vMix 연결 시도
                self.connection_status_changed.emit(
                    f"vMix TCP ({self.vmix_ip}:{self.vmix_tcp_port}) 연결 시도", 
                    "orange"
                )
                
                self.sock = socket.create_connection(
                    (self.vmix_ip, self.vmix_tcp_port), 
                    timeout=5
                )
                
                self.connection_status_changed.emit(
                    "vMix TCP 연결 성공 (감지 대기중)", 
                    "green"
                )
                
                # TALLY 구독
                self.sock.sendall(b"SUBSCRIBE TALLY\r\n")
                
                # 초기 상태 가져오기
                self.tally_activity_detected.emit()
                
                # 데이터 수신 루프
                buffer = ""
                while self.running:
                    try:
                        data = self.sock.recv(1024)
                        if not data:
                            logger.info("vMix 연결 끊김")
                            break
                            
                        buffer += data.decode('utf-8', errors='ignore')
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            # TALLY OK 메시지 감지
                            if line.startswith('TALLY OK'):
                                self.tally_activity_detected.emit()
                                
                    except socket.timeout:
                        continue
                    except socket.error:
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

class VMixManager(QObject):
    """vMix 관리자 - Tally 시스템 통합"""
    
    # 시그널 정의
    tally_updated = pyqtSignal(int, int, dict, dict)  # pgm, pvw, pgm_info, pvw_info
    connection_status_changed = pyqtSignal(str, str)
    input_list_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.tcp_listener = None
        self.vmix_ip = "127.0.0.1"
        self.vmix_http_port = 8088
        self.input_names = {}
        self.last_pgm = 0
        self.last_pvw = 0
        self.is_connected = False
        
    def connect_to_vmix(self, ip="127.0.0.1", http_port=8088, tcp_port=8099):
        """vMix 연결"""
        try:
            self.vmix_ip = ip
            self.vmix_http_port = http_port
            
            # TCP 리스너 시작
            if self.tcp_listener:
                self.tcp_listener.stop()
                
            self.tcp_listener = VMixTCPListener(ip, tcp_port)
            self.tcp_listener.tally_activity_detected.connect(self.fetch_vmix_state)
            self.tcp_listener.connection_status_changed.connect(self._on_tcp_status_changed)
            self.tcp_listener.start()
            
            self.is_connected = True
            logger.info(f"vMix 연결 시작: {ip}:{http_port}/{tcp_port}")
            
        except Exception as e:
            logger.error(f"vMix 연결 실패: {e}")
            self.connection_status_changed.emit(f"연결 실패: {e}", "red")
            
    def disconnect_from_vmix(self):
        """vMix 연결 해제"""
        try:
            if self.tcp_listener:
                self.tcp_listener.stop()
                self.tcp_listener = None
                
            self.is_connected = False
            self.connection_status_changed.emit("연결 해제됨", "gray")
            logger.info("vMix 연결 해제")
            
        except Exception as e:
            logger.error(f"vMix 연결 해제 오류: {e}")
            
    def fetch_vmix_state(self):
        """HTTP API로 vMix 상태 가져오기"""
        try:
            url = f"http://{self.vmix_ip}:{self.vmix_http_port}/api"
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
                
            # 입력 목록 업데이트
            if inputs != self.input_names:
                self.input_names = inputs
                self.input_list_updated.emit(self.input_names)
                logger.info(f"입력 목록 업데이트: {len(self.input_names)}개")
                
            # Tally 정보 업데이트
            if pgm != self.last_pgm or pvw != self.last_pvw:
                self.last_pgm = pgm
                self.last_pvw = pvw
                
                pgm_info = self.input_names.get(pgm, {'name': f'Input {pgm}', 'type': 'Unknown'})
                pvw_info = self.input_names.get(pvw, {'name': f'Input {pvw}', 'type': 'Unknown'})
                
                self.tally_updated.emit(pgm, pvw, pgm_info, pvw_info)
                logger.debug(f"Tally 업데이트 - PGM: {pgm}, PVW: {pvw}")
                
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