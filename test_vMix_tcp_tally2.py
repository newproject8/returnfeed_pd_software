# -*- coding: utf-8 -*-
"""
vMix Tally Broadcaster (v1.8.0 - Bi-directional Heartbeat)

- 서버와 클라이언트가 서로 생존 신호를 주고받는 양방향 하트비트 적용
- 서버로부터 신호가 장시간 없을 경우, 클라이언트가 먼저 재연결을 시도하여
  연결 안정성을 극대화합니다.
"""
import sys
import json
import requests
import socket
import asyncio
import websockets
import ssl
from websockets.exceptions import ConnectionClosed
import threading
import time
import os
import xml.etree.ElementTree as ET
import logging

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QStatusBar,
                             QSizePolicy)
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
    tally_updated = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(str, str)
    input_list_updated = pyqtSignal(list)

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
        self.thread_name = "vMixTCP"
        self.vmix_ip = "127.0.0.1"
        self.vmix_tcp_port = 8099
        self.sock = None

    def run(self):
        self.running = True
        self.log_info("스레드 시작.")
        while self.running:
            try:
                self.signals.connection_status_changed.emit(f"vMix TCP ({self.vmix_ip}:{self.vmix_tcp_port}) 연결 시도", "orange")
                self.sock = socket.create_connection((self.vmix_ip, self.vmix_tcp_port), timeout=5)
                self.signals.connection_status_changed.emit("vMix TCP 연결 성공", "green")
                self.sock.sendall(b"SUBSCRIBE TALLY\r\n")
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
                            if line.startswith('TALLY OK'):
                                self.signals.tally_updated.emit({"tally_str": line.split(' ')[2]})
                    except socket.timeout:
                        continue
                    except socket.error:
                        break
            except Exception as e:
                self.log_error(f"TCP 루프 오류: {e}")
            finally:
                if self.sock:
                    self.sock.close()
                self.sock = None
                self.signals.connection_status_changed.emit("vMix TCP 연결 끊김", "red")
                self.signals.tally_updated.emit({"tally_str": "0" * 200})

            if self.running:
                time.sleep(5)
        self.on_shutdown()

class vMixHTTPFetcher(NetworkThread):
    def __init__(self, signals, parent=None):
        super().__init__(signals, parent)
        self.thread_name = "vMixHTTP"
        self.vmix_ip = "127.0.0.1"
        self.vmix_http_port = 8088

    def run(self):
        self.running = True
        self.log_info("스레드 시작.")
        while self.running:
            try:
                url = f"http://{self.vmix_ip}:{self.vmix_http_port}/api"
                response = requests.get(url, timeout=2)
                response.raise_for_status()
                root = ET.fromstring(response.content)
                inputs = [{"number": int(e.get('number')), "name": e.get('title')} for e in root.findall('.//input')]
                if inputs:
                    self.signals.input_list_updated.emit(inputs)
            except requests.RequestException:
                pass
            except Exception as e:
                self.log_error(f"HTTP 파싱 오류: {e}")

            for _ in range(50):
                if not self.running: break
                time.sleep(0.1)
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
                self.signals.connection_status_changed.emit(f"서버({self.ws_uri}) 연결 시도...", "orange")
                # ping/pong은 서버-클라이언트 양단에서 설정하여 안정성 확보
                async with websockets.connect(self.ws_uri, ssl=USE_SSL, ping_interval=20, ping_timeout=20) as websocket:
                    self.signals.connection_status_changed.emit("서버 연결 성공", "green")
                    await self.communication_loop(websocket)
            except Exception as e:
                self.log_error(f"웹소켓 연결 또는 통신 실패: {e}")

            if self.running:
                self.signals.connection_status_changed.emit("서버 연결 끊김", "red")
                delay = 5
                self.log_info(f"{delay}초 후 재연결합니다.")
                await asyncio.sleep(delay)

    async def sender(self, websocket):
        """메시지 큐에서 메시지를 꺼내 서버로 전송"""
        while self.running:
            message = await self.message_queue.get()
            if message is None:
                break
            await websocket.send(json.dumps(message))
            self.message_queue.task_done()

    async def receiver(self, websocket):
        """서버로부터 메시지를 수신하고 PONG 응답"""
        last_server_signal_time = time.time()
        SERVER_TIMEOUT = 90  # 90초간 서버 신호 없으면 연결 종료

        while self.running:
            try:
                # 1초 타임아웃으로 메시지 수신 대기
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                last_server_signal_time = time.time()  # 서버 신호 수신 시간 갱신
                
                data = json.loads(message)
                if data.get("type") == "ping":
                    # 서버의 ping에 pong으로 응답
                    pong_msg = {"type": "pong", "timestamp": time.time()}
                    await self.message_queue.put(pong_msg)

            except asyncio.TimeoutError:
                # 타임아웃은 정상, 서버 생존 시간 체크
                if time.time() - last_server_signal_time > SERVER_TIMEOUT:
                    self.log_error(f"서버로부터 {SERVER_TIMEOUT}초 이상 신호 없음. 재연결합니다.")
                    break # 루프를 중단시켜 재연결 유도
                continue
            except ConnectionClosed:
                self.log_error("수신 중 연결이 끊겼습니다.")
                break
            except Exception as e:
                self.log_error(f"수신 중 오류 발생: {e}")
                break
    
    async def communication_loop(self, websocket):
        """sender와 receiver를 동시에 실행"""
        self.log_info("통신 루프 시작.")
        
        sender_task = asyncio.create_task(self.sender(websocket))
        receiver_task = asyncio.create_task(self.receiver(websocket))

        done, pending = await asyncio.wait(
            [sender_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
        
        self.log_info("통신 루프 종료.")

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
        self.input_names = {}
        self.last_pgm = 0
        self.last_pvw = 0
        self.last_input_hash = 0
        self.init_ui()
        self.init_threads()
        self.init_signals()
        self.start_threads()

    def init_ui(self):
        self.setWindowTitle("vMix Tally Broadcaster v1.8.0")
        self.setGeometry(100, 100, 550, 300)
        main_layout = QVBoxLayout(self)
        ctrl_layout = QHBoxLayout()
        self.ip_input = QLineEdit("127.0.0.1")
        self.port_input = QLineEdit("8088")
        self.connect_button = QPushButton("Connect")
        ctrl_layout.addWidget(QLabel("vMix IP:"))
        ctrl_layout.addWidget(self.ip_input)
        ctrl_layout.addWidget(QLabel("Port:"))
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
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        self.reset_tally_display()

    def init_threads(self):
        self.signals = Signals()
        self.tcp_listener = vMixTCPListener(self.signals)
        self.http_fetcher = vMixHTTPFetcher(self.signals)
        self.ws_client = WebSocketClient(self.signals)

    def init_signals(self):
        self.connect_button.clicked.connect(self.toggle_connection)
        self.signals.tally_updated.connect(self.process_tally_update)
        self.signals.input_list_updated.connect(self.process_input_list_update)
        self.ws_client.signals.connection_status_changed.connect(lambda m, c: self.update_status(f"Server: {m}", c))
        self.tcp_listener.signals.connection_status_changed.connect(lambda m, c: self.update_status(f"vMix: {m}", c))
    
    def update_status(self, text, color="white"):
        self.status_bar.showMessage(text)
        self.status_bar.setStyleSheet(f"color: {color};")

    def start_threads(self):
        self.ws_client.start()

    def toggle_connection(self):
        if self.tcp_listener.isRunning():
            self.connect_button.setText("Connect")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.tcp_listener.stop()
            self.http_fetcher.stop()
        else:
            self.connect_button.setText("Disconnect")
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False)
            self.tcp_listener.vmix_ip = self.ip_input.text().strip()
            self.http_fetcher.vmix_ip = self.ip_input.text().strip()
            self.http_fetcher.vmix_http_port = int(self.port_input.text().strip())
            self.tcp_listener.start()
            self.http_fetcher.start()

    def reset_tally_display(self):
        self.pvw_box.setText("PREVIEW\n---\n")
        self.pgm_box.setText("PROGRAM\n---\n")
        self.pvw_box.setStyleSheet(f"background-color: {COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")
        self.pgm_box.setStyleSheet(f"background-color: {COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")

    def process_input_list_update(self, inputs):
        current_hash = hash(json.dumps(inputs, sort_keys=True))
        if current_hash == self.last_input_hash: return
        self.last_input_hash = current_hash
        self.input_names = {item["number"]: item["name"] for item in inputs}
        self.ws_client.send_message({"type": "input_list", "inputs": self.input_names})
        logging.info(f"Input 목록 업데이트 ({len(self.input_names)}개) 및 서버 전송.")

    def process_tally_update(self, tally_info):
        tally_str = tally_info.get("tally_str", "")
        pgm, pvw = 0, 0
        for i, state in enumerate(tally_str, 1):
            if state == '1': pgm = i
            elif state == '2': pvw = i
        if pgm == self.last_pgm and pvw == self.last_pvw: return
        self.last_pgm, self.last_pvw = pgm, pvw

        pgm_name = self.input_names.get(pgm, f"Input {pgm}")
        pvw_name = self.input_names.get(pvw, f"Input {pvw}")

        self.pvw_box.setText(f"PREVIEW ({pvw if pvw > 0 else '...'})\n{truncate_text(pvw_name if pvw > 0 else '---')}\n")
        self.pgm_box.setText(f"PROGRAM ({pgm if pgm > 0 else '...'})\n{truncate_text(pgm_name if pgm > 0 else '---')}\n")

        self.pvw_box.setStyleSheet(f"background-color: {COLOR_PVW_NORMAL if pvw > 0 else COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")
        self.pgm_box.setStyleSheet(f"background-color: {COLOR_PGM_NORMAL if pgm > 0 else COLOR_OFF}; color: {COLOR_TEXT}; border-radius: 5px; padding: 10px;")

        self.ws_client.send_message({
            "type": "tally_update",
            "program": pgm,
            "preview": pvw
        })

    def closeEvent(self, event):
        logging.info("애플리케이션 종료 중...")
        self.tcp_listener.stop()
        self.http_fetcher.stop()
        self.ws_client.stop()
        
        self.tcp_listener.wait(500)
        self.http_fetcher.wait(500)
        self.ws_client.wait(500)
        
        logging.info("모든 스레드 종료 완료.")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainApp()
    win.show()
    sys.exit(app.exec_())