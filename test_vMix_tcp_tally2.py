# -*- coding: utf-8 -*-
"""
vMix Tally Broadcaster (v2.0.0 - Hybrid Method)

- TCP의 '즉각적인 감지 능력'과 HTTP API의 '정확성'을 결합한 하이브리드 방식 적용.
- (1) TCP Tally 신호로 변경 사항을 즉시 감지 (지연 시간 최소화).
- (2) 변경 감지 시에만 HTTP API를 1회 호출하여 정확한 PGM/PVW 정보를 가져옴 (오버레이 문제 해결).
- 이로써, 지연 시간을 최소화하면서 데이터의 정확성을 모두 확보합니다.
"""
import sys
import json
import requests
import socket
import asyncio
import websockets
from websockets.exceptions import ConnectionClosed
import threading
import time
import os
import xml.etree.ElementTree as ET
import logging

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QMessageBox, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, QObject, QThread, Qt

# --- 기본 설정 ---
RELAY_SERVER_IP = "returnfeed.net"
RELAY_SERVER_PORT = 443
USE_SSL = True

# --- 로깅 및 색상 설정 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s')
COLOR_OFF = "#333333"
COLOR_PVW_NORMAL = "#00aa00"
COLOR_PGM_NORMAL = "#aa0000"
COLOR_TEXT = "#ffffff"

def truncate_text(text, max_length=12):
    if not text: return "---"
    return text[:max_length] if len(text) <= max_length else text[:9] + '...'

class Signals(QObject):
    tally_activity_detected = pyqtSignal()
    connection_status_changed = pyqtSignal(str, str)
    vmix_connection_status_changed = pyqtSignal(str, str)
    server_connection_status_changed = pyqtSignal(str, str)

class NetworkThread(QThread):
    def __init__(self, signals, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.running = False
        self.thread_name = "NetworkThread"

    def stop(self):
        self.running = False
        self.log_info("종료 신호 수신...")

    def log_info(self, msg): logging.info(f"[{self.thread_name}] {msg}")
    def log_error(self, msg): logging.error(f"[{self.thread_name}] {msg}")
    def on_shutdown(self): self.log_info("스레드 종료.")

class vMixTCPListener(NetworkThread):
    def __init__(self, signals, parent=None):
        super().__init__(signals, parent)
        self.thread_name = "vMixTCP_Trigger"
        self.vmix_ip = "127.0.0.1"
        self.vmix_tcp_port = 8099
        self.sock = None

    def run(self):
        self.running = True
        self.log_info("스레드 시작.")
        while self.running:
            try:
                self.signals.vmix_connection_status_changed.emit(f"vMix TCP ({self.vmix_ip}:{self.vmix_tcp_port}) 연결 시도", "orange")
                self.sock = socket.create_connection((self.vmix_ip, self.vmix_tcp_port), timeout=5)
                self.signals.vmix_connection_status_changed.emit("vMix TCP 연결 성공 (감지 대기중)", "green")
                self.sock.sendall(b"SUBSCRIBE TALLY\r\n")
                
                # 최초 연결 시, 초기 상태를 가져오기 위해 신호 한번 보냄
                self.signals.tally_activity_detected.emit()
                
                buffer = ""
                while self.running:
                    try:
                        data = self.sock.recv(1024)
                        if not data:
                            self.log_info("vMix 연결 끊김.")
                            break
                        buffer += data.decode('utf-8', errors='ignore')
                        while '\r\n' in buffer:
                            line, buffer = buffer.split('\r\n', 1)
                            # TALLY OK 메시지를 받으면, 내용과 상관없이 '변경'이 일어났다는 신호만 보냄
                            if line.startswith('TALLY OK'):
                                self.signals.tally_activity_detected.emit()
                    except socket.timeout:
                        continue
                    except socket.error:
                        break
            except Exception as e:
                self.log_error(f"TCP 루프 오류: {e}")
            finally:
                if self.sock: self.sock.close()
                self.sock = None
                self.signals.vmix_connection_status_changed.emit("vMix TCP 연결 끊김", "red")
            
            if self.running:
                time.sleep(5) # 재연결 시도 간격
        self.on_shutdown()


class WebSocketClient(NetworkThread):
    def __init__(self, signals, parent=None):
        super().__init__(signals, parent)
        self.thread_name = "WebSocket"
        proto = "wss" if USE_SSL else "ws"
        self.ws_uri = f"{proto}://{RELAY_SERVER_IP}/ws/"
        self.message_queue = asyncio.Queue()
        self.loop = None

    def run(self):
        self.running = True
        self.log_info("스레드 시작.")
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.main_loop())
        except Exception as e:
            self.log_error(f"Asyncio 루프가 치명적 오류로 종료되었습니다: {e}")
        finally:
            self.log_info("Asyncio 이벤트 루프를 닫습니다.")
            self.loop.close()
        self.on_shutdown()

    async def main_loop(self):
        while self.running:
            try:
                self.signals.server_connection_status_changed.emit(f"서버({self.ws_uri}) 연결 시도...", "orange")
                async with websockets.connect(self.ws_uri, ssl=USE_SSL, ping_interval=20, ping_timeout=20) as websocket:
                    self.signals.server_connection_status_changed.emit("서버 연결 성공", "green")
                    await self.communication_loop(websocket)
            except Exception as e:
                self.log_error(f"웹소켓 연결 또는 통신 실패: {e}")

            if self.running:
                self.signals.server_connection_status_changed.emit("서버 연결 끊김", "red")
                await asyncio.sleep(5)

    async def sender(self, websocket):
        while self.running:
            message = await self.message_queue.get()
            if message is None: break
            await websocket.send(json.dumps(message))
            self.message_queue.task_done()

    async def receiver(self, websocket):
        last_server_signal_time = time.time()
        SERVER_TIMEOUT = 90
        while self.running:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                last_server_signal_time = time.time()
                data = json.loads(message)
                if data.get("type") == "ping":
                    await self.message_queue.put({"type": "pong", "timestamp": time.time()})
            except asyncio.TimeoutError:
                if time.time() - last_server_signal_time > SERVER_TIMEOUT:
                    self.log_error(f"서버로부터 {SERVER_TIMEOUT}초 이상 신호 없음. 재연결합니다.")
                    break
                continue
            except (ConnectionClosed, Exception) as e:
                self.log_error(f"수신 중 오류: {e}")
                break
    
    async def communication_loop(self, websocket):
        sender_task = asyncio.create_task(self.sender(websocket))
        receiver_task = asyncio.create_task(self.receiver(websocket))
        done, pending = await asyncio.wait([sender_task, receiver_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending: task.cancel()

    def send_message(self, message):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.message_queue.put(message), self.loop)

    def stop(self):
        super().stop()
        if self.loop and self.loop.is_running():
            self.send_message(None)

class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.vmix_ip = "127.0.0.1"
        self.vmix_http_port = 8088
        self.input_names = {}
        self.last_pgm = 0
        self.last_pvw = 0
        self.last_input_hash = 0
        self.init_ui()
        self.init_threads()
        self.init_signals()
        self.start_threads()

    def init_ui(self):
        self.setWindowTitle("vMix Tally Broadcaster v2.0.0 (Hybrid)")
        self.setGeometry(100, 100, 550, 300)
        main_layout = QVBoxLayout(self)
        ctrl_layout = QHBoxLayout()
        self.ip_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("8088")
        self.connect_button = QPushButton("Connect")
        ctrl_layout.addWidget(QLabel("vMix IP:"))
        ctrl_layout.addWidget(self.ip_input)
        ctrl_layout.addWidget(QLabel("HTTP Port:"))
        ctrl_layout.addWidget(self.port_input)
        ctrl_layout.addStretch(1)
        ctrl_layout.addWidget(self.connect_button)
        main_layout.addLayout(ctrl_layout)
        tally_layout = QHBoxLayout()
        self.pvw_box = QLabel("PREVIEW\n---\n")
        self.pgm_box = QLabel("PROGRAM\n---\n")
        for box in [self.pvw_box, self.pgm_box]:
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            box.setAlignment(Qt.AlignCenter)
            box.setWordWrap(True)
            tally_layout.addWidget(box)
        main_layout.addLayout(tally_layout, stretch=1)
        
        status_layout = QHBoxLayout()
        self.vmix_status_label = QLabel("vMix: Disconnected")
        self.server_status_label = QLabel("Server: Disconnected")
        status_layout.addWidget(self.vmix_status_label)
        status_layout.addStretch(1)
        status_layout.addWidget(self.server_status_label)
        main_layout.addLayout(status_layout)
        
        self.reset_tally_display()

    def init_threads(self):
        self.signals = Signals()
        self.tcp_listener = vMixTCPListener(self.signals)
        self.ws_client = WebSocketClient(self.signals)

    def init_signals(self):
        self.connect_button.clicked.connect(self.toggle_connection)
        self.signals.tally_activity_detected.connect(self.fetch_and_process_vmix_state)
        self.signals.vmix_connection_status_changed.connect(lambda msg, color: self.update_status_label(self.vmix_status_label, "vMix", msg, color))
        self.signals.server_connection_status_changed.connect(lambda msg, color: self.update_status_label(self.server_status_label, "Server", msg, color))

    def update_status_label(self, label, prefix, msg, color):
        label.setText(f"{prefix}: {msg}")
        label.setStyleSheet(f"color: {color};")

    def start_threads(self):
        self.ws_client.start()

    def toggle_connection(self):
        if self.tcp_listener.isRunning():
            self.connect_button.setText("Connect")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.tcp_listener.stop()
            self.reset_tally_display()
            self.update_status_label(self.vmix_status_label, "vMix", "Disconnected", "gray")
        else:
            try:
                self.vmix_ip = self.ip_input.text().strip()
                self.vmix_http_port = int(self.port_input.text().strip())
                
                self.connect_button.setText("Disconnect")
                self.ip_input.setEnabled(False)
                self.port_input.setEnabled(False)
                
                self.tcp_listener.vmix_ip = self.vmix_ip
                self.tcp_listener.start()
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "Port는 숫자여야 합니다.")

    def fetch_and_process_vmix_state(self):
        """TCP 신호를 받으면 호출되는 핵심 함수. HTTP로 정확한 상태를 가져와 처리."""
        try:
            url = f"http://{self.vmix_ip}:{self.vmix_http_port}/api"
            response = requests.get(url, timeout=0.5) # 타임아웃을 짧게 설정
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            pgm = int(root.find('active').text)
            pvw = int(root.find('preview').text)
            inputs = [{"number": int(e.get('number')), "name": e.get('title')} for e in root.findall('.//input')]

            # 입력 목록 처리
            current_hash = hash(json.dumps(inputs, sort_keys=True))
            if current_hash != self.last_input_hash:
                self.last_input_hash = current_hash
                self.input_names = {item["number"]: item["name"] for item in inputs}
                self.ws_client.send_message({"type": "input_list", "inputs": self.input_names})
                logging.info(f"Input 목록 업데이트 ({len(self.input_names)}개) 및 서버 전송.")
            
            # Tally 정보 처리
            if pgm != self.last_pgm or pvw != self.last_pvw:
                self.last_pgm, self.last_pvw = pgm, pvw

                pgm_name = self.input_names.get(pgm, f"Input {pgm}")
                pvw_name = self.input_names.get(pvw, f"Input {pvw}")

                self.pvw_box.setText(f"PREVIEW ({pvw if pvw > 0 else '...'})\n{truncate_text(pvw_name if pvw > 0 else '---')}\n")
                self.pgm_box.setText(f"PROGRAM ({pgm if pgm > 0 else '...'})\n{truncate_text(pgm_name if pgm > 0 else '---')}\n")

                self.pvw_box.setStyleSheet(f"background-color: {COLOR_PVW_NORMAL if pvw > 0 else COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")
                self.pgm_box.setStyleSheet(f"background-color: {COLOR_PGM_NORMAL if pgm > 0 else COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")

                self.ws_client.send_message({"type": "tally_update", "program": pgm, "preview": pvw})

        except requests.RequestException:
            # HTTP 요청 실패 시, TCP 연결 상태는 유지하되 에러 로그만 남김
            logging.error("HTTP API 요청 실패. vMix가 실행 중인지, IP/Port가 맞는지 확인하세요.")
            # UI에 에러 상태를 잠시 표시할 수도 있음
            self.update_status_label(self.vmix_status_label, "vMix", "API 요청 실패", "orange")


    def reset_tally_display(self):
        self.pvw_box.setText("PREVIEW\n---\n")
        self.pgm_box.setText("PROGRAM\n---\n")
        self.pvw_box.setStyleSheet(f"background-color: {COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")
        self.pgm_box.setStyleSheet(f"background-color: {COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")
        self.last_pgm, self.last_pvw, self.last_input_hash = 0, 0, 0

    def closeEvent(self, event):
        logging.info("애플리케이션 종료 중...")
        self.tcp_listener.stop()
        self.ws_client.stop()
        self.tcp_listener.wait(500)
        self.ws_client.wait(500)
        logging.info("모든 스레드 종료 완료.")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainApp()
    win.show()
    sys.exit(app.exec_())
