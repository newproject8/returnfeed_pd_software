# -*- coding: utf-8 -*-
"""
vMix Tally Broadcaster (v1.2 - GUI 완벽 복제 버전)

안정적인 v1.1의 코드 구조는 유지하면서, 사용자의 요청에 따라
GUI의 모든 시각적 요소(디자인, 애니메이션, 폰트, 텍스트 스타일)를
'test_vMix_tcp_tally.py' 원본과 완전히 동일하게 변경한 최종 버전입니다.
"""
import sys
import json
import requests
import socket
import asyncio
import websockets
import threading
import time
import os
import xml.etree.ElementTree as ET
import logging
import random

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QStatusBar,
                             QSizePolicy)
from PyQt5.QtGui import QFont, QColor, QFontDatabase, QPalette
from PyQt5.QtCore import (pyqtSignal, QObject, QThread, Qt, QPropertyAnimation, 
                          QEasingCurve, QVariantAnimation, QAbstractAnimation)

# qdarkstyle이 설치되어 있지 않아도 프로그램이 실행되도록 예외 처리
try:
    import qdarkstyle
except ImportError:
    qdarkstyle = None
    print("Warning: qdarkstyle is not installed. The application will use the default system theme.")
    print("To install, run: pip install qdarkstyle")

# --- 기본 설정 (test_vMix...py 원본과 동일하게 맞춤) ---
RELAY_SERVER_IP = "www.returnfeed.net"
RELAY_SERVER_PORT = 8765
FONT_DIR = "fonts" 

# 색상 설정
COLOR_OFF = "#333333"
COLOR_PVW_NORMAL = "#00aa00"
COLOR_PVW_BRIGHT = "#00ff00"
COLOR_PGM_NORMAL = "#aa0000"
COLOR_PGM_BRIGHT = "#ff0000"
COLOR_TEXT = "#ffffff"

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s')

def resource_path(relative_path):
    """ PyInstaller와 일반 실행 환경 모두에서 리소스 경로를 올바르게 찾습니다. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def truncate_text(text, max_length=12):
    """ 원본과 동일한 텍스트 축약 함수 """
    if not text: return "---"
    if len(text) <= max_length: return text
    return text[:9] + '...'

class Signals(QObject):
    """GUI 업데이트를 위한 커스텀 시그널"""
    tally_updated = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(str, str)
    input_list_updated = pyqtSignal(list)

# --- 네트워크 스레드는 v1.1의 안정적인 구조를 그대로 사용 ---
class NetworkThread(QThread):
    def __init__(self, signals, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.running = False
        self.thread_name = "NetworkThread"

    def run(self):
        self.running = True
        self.log_info("스레드 시작.")
        retry_delay = 1; max_retry_delay = 30
        while self.running:
            try:
                self.connect_and_loop()
            except Exception as e:
                self.log_error(f"연결 루프 오류: {e}. {retry_delay:.1f}초 후 재시도.")
                self.on_disconnect()
                time.sleep(retry_delay)
                retry_delay = min(max_retry_delay, retry_delay * 1.5 + random.uniform(0, 1))
        self.on_shutdown()
        self.log_info("스레드 종료.")
        
    def stop(self):
        self.running = False
        self.log_info("종료 신호 수신...")

    def log_info(self, msg): logging.info(f"[{self.thread_name}] {msg}")
    def log_error(self, msg): logging.error(f"[{self.thread_name}] {msg}")
    def connect_and_loop(self): raise NotImplementedError
    def on_disconnect(self): pass
    def on_shutdown(self): pass

class vMixTCPListener(NetworkThread):
    def __init__(self, signals, parent=None):
        super().__init__(signals, parent)
        self.thread_name = "vMixTCP"
        self.vmix_ip = "127.0.0.1"
        self.vmix_tcp_port = 8099
        self.sock = None

    def connect_and_loop(self):
        self.signals.connection_status_changed.emit(f"vMix TCP 연결 시도 ({self.vmix_ip}:{self.vmix_tcp_port})", "orange")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((self.vmix_ip, self.vmix_tcp_port))
        self.signals.connection_status_changed.emit(f"vMix TCP 연결 성공", "green")
        self.sock.sendall(b"SUBSCRIBE TALLY\r\n")
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data: self.log_info("vMix 연결 끊김."); break
                buffer += data.decode('utf-8', errors='ignore')
                while '\r\n' in buffer:
                    line, buffer = buffer.split('\r\n', 1)
                    if line.startswith('TALLY OK'):
                        self.signals.tally_updated.emit({"tally_str": line.split(' ')[2]})
            except socket.timeout: continue
            except socket.error as e: self.log_error(f"소켓 오류: {e}"); break

    def on_disconnect(self):
        if self.sock: self.sock.close()
        self.signals.connection_status_changed.emit(f"vMix TCP 연결 끊김", "red")
        self.signals.tally_updated.emit({"tally_str": "0"*200})

    def on_shutdown(self):
        if self.sock: self.sock.close()

class vMixHTTPFetcher(NetworkThread):
    def __init__(self, signals, parent=None):
        super().__init__(signals, parent)
        self.thread_name = "vMixHTTP"
        self.vmix_ip = "127.0.0.1"
        self.vmix_http_port = 8088

    def connect_and_loop(self):
        while self.running:
            try:
                url = f"http://{self.vmix_ip}:{self.vmix_http_port}/api"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    inputs = [{"number": int(e.get('number')), "name": e.get('title')} for e in root.findall('.//input')]
                    if inputs: self.signals.input_list_updated.emit(inputs)
                else: self.log_error(f"API 요청 실패 (코드: {response.status_code})")
            except requests.RequestException as e: self.log_error(f"HTTP 요청 오류: {e}")
            except Exception as e: self.log_error(f"Input 파싱 오류: {e}")
            for _ in range(50):
                if not self.running: break
                time.sleep(0.1)
                
class WebSocketClient(NetworkThread):
    def __init__(self, signals, parent=None):
        super().__init__(signals, parent)
        self.thread_name = "WebSocket"
        self.ws_uri = f"ws://{RELAY_SERVER_IP}:{RELAY_SERVER_PORT}"
        self.message_queue = asyncio.Queue()
        self.loop = None

    def connect_and_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.async_connect_and_loop())

    async def async_connect_and_loop(self):
        self.signals.connection_status_changed.emit(f"중계 서버 연결 시도...", "orange")
        try:
            async with websockets.connect(self.ws_uri) as websocket:
                self.signals.connection_status_changed.emit(f"중계 서버 연결 성공", "green")
                while self.running:
                    try:
                        message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                        await websocket.send(json.dumps(message))
                    except asyncio.TimeoutError:
                        try: await websocket.ping()
                        except websockets.ConnectionClosed: self.log_error("핑 전송 중 연결 끊김."); break
                        continue
        except Exception as e: self.log_error(f"웹소켓 연결 실패: {e}"); raise

    def send_message(self, message):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.message_queue.put_nowait, message)

    def on_disconnect(self):
        self.signals.connection_status_changed.emit(f"중계 서버 연결 끊김", "red")

    def stop(self):
        self.running = False
        if self.loop and self.loop.is_running(): self.loop.call_soon_threadsafe(self.loop.stop)
        super().stop()


class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_names = {}
        self.last_pgm = 0
        self.last_pvw = 0
        self.last_pgm_active = False
        self.last_pvw_active = False
        self.last_input_hash = 0
        
        self.init_ui()
        self.init_animations()
        self.init_threads()
        self.init_signals()
        self.start_threads()

    def init_ui(self):
        """test_vmix...py 원본과 동일하게 GUI 위젯과 레이아웃을 구성합니다."""
        self.setWindowTitle("vMix Tally Broadcaster v1.2")
        self.setGeometry(100, 100, 550, 300)
        self.load_and_set_fonts()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # --- IP/Port 입력부 (원본과 동일하게 복원) ---
        ctrl_layout = QHBoxLayout()
        self.ip_label = QLabel("vMix IP:")
        self.ip_input = QLineEdit("127.0.0.1")
        self.port_label = QLabel("Port:") # TCP Port가 아닌 HTTP Port용
        self.port_input = QLineEdit("8088")
        self.port_input.setMaximumWidth(60)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        # 원본과 동일한 작은 폰트 적용
        small_font = QFont("Metropolis", 9)
        self.ip_label.setFont(small_font)
        self.port_label.setFont(small_font)
        self.ip_input.setFont(small_font)
        self.port_input.setFont(small_font)
        self.connect_button.setFont(small_font)

        ctrl_layout.addWidget(self.ip_label)
        ctrl_layout.addWidget(self.ip_input)
        ctrl_layout.addWidget(self.port_label)
        ctrl_layout.addWidget(self.port_input)
        ctrl_layout.addStretch(1)
        ctrl_layout.addWidget(self.connect_button)
        main_layout.addLayout(ctrl_layout)

        # --- 탈리 박스 (원본과 동일하게 QLabel로 변경) ---
        tally_layout = QHBoxLayout()
        tally_layout.setSpacing(20)

        self.pvw_box = QLabel()
        self.pgm_box = QLabel()
        
        for box in [self.pvw_box, self.pgm_box]:
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            box.setAlignment(Qt.AlignCenter)
            box.setWordWrap(True)
            tally_layout.addWidget(box)
        
        main_layout.addLayout(tally_layout, stretch=1)

        # --- 상태 바 ---
        self.status_bar = QStatusBar()
        self.status_bar.setFont(small_font)
        main_layout.addWidget(self.status_bar)
        
        self.reset_tally_display() # 초기 상태 설정

    def load_and_set_fonts(self):
        font_path = resource_path(FONT_DIR)
        if not os.path.exists(font_path):
            logging.warning(f"폰트 디렉토리({FONT_DIR})를 찾을 수 없습니다.")
            return

        db = QFontDatabase()
        for font_file in [f for f in os.listdir(font_path) if f.lower().endswith(('.ttf', '.otf'))]:
            db.addApplicationFont(os.path.join(font_path, font_file))
        
        # 원본과 동일한 폰트 및 크기 설정
        self.tally_font = QFont("Gmarket Sans", 16, QFont.Bold)
        self.pvw_box.setFont(self.tally_font)
        self.pgm_box.setFont(self.tally_font)

    def get_stylesheet(self, base_color, text_color, glow_color=None):
        """ 원본과 동일한 스타일시트 생성 함수 """
        border_width = "4px" if glow_color else "2px"
        border_color = glow_color if glow_color else "#555555"
        return f"""
            QLabel {{
                background-color: {base_color};
                border: {border_width} solid {border_color};
                border-radius: 5px;
                color: {text_color};
                font-weight: bold;
                padding: 10px;
            }}
        """

    def init_animations(self):
        """ 원본과 동일한 애니메이션 초기화 """
        self.pvw_anim = QVariantAnimation(self)
        self.pvw_anim.setDuration(500)
        self.pvw_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pvw_anim.setStartValue(QColor(COLOR_PVW_BRIGHT))
        self.pvw_anim.setEndValue(QColor(COLOR_PVW_NORMAL))
        self.pvw_anim.valueChanged.connect(lambda c: self._animate_color(self.pvw_box, c, COLOR_PVW_BRIGHT))

        self.pgm_anim = QVariantAnimation(self)
        self.pgm_anim.setDuration(500)
        self.pgm_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.pgm_anim.setStartValue(QColor(COLOR_PGM_BRIGHT))
        self.pgm_anim.setEndValue(QColor(COLOR_PGM_NORMAL))
        self.pgm_anim.valueChanged.connect(lambda c: self._animate_color(self.pgm_box, c, COLOR_PGM_BRIGHT))

    def _animate_color(self, box, color, bright_color):
        """ 애니메이션 색상 적용 헬퍼 함수 """
        box.setStyleSheet(self.get_stylesheet(color.name(), COLOR_TEXT, glow_color=bright_color))

    def init_threads(self):
        self.signals = Signals()
        self.tcp_listener = vMixTCPListener(self.signals)
        self.http_fetcher = vMixHTTPFetcher(self.signals)
        self.ws_client = WebSocketClient(self.signals)

    def init_signals(self):
        self.signals.tally_updated.connect(self.process_tally_update)
        self.signals.input_list_updated.connect(self.process_input_list_update)
        self.ws_client.signals.connection_status_changed.connect(lambda m, c: self.update_status(f"Server: {m}", c))
        self.tcp_listener.signals.connection_status_changed.connect(lambda m, c: self.update_status(f"vMix: {m}", c))

    def start_threads(self):
        self.ws_client.start() # 중계 서버 연결은 항상 시도

    def update_status(self, text, color="white"):
        self.status_bar.showMessage(text)
        self.status_bar.setStyleSheet(f"color: {color};")
        
    def toggle_connection(self):
        if self.tcp_listener.isRunning():
            self.connect_button.setText("Connect")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.tcp_listener.stop()
            self.http_fetcher.stop()
            self.reset_tally_display()
        else:
            ip = self.ip_input.text().strip()
            port_str = self.port_input.text().strip()
            if not ip or not port_str.isdigit():
                QMessageBox.warning(self, "입력 오류", "올바른 IP와 Port를 입력하세요.")
                return

            self.connect_button.setText("Disconnect")
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False)
            
            self.tcp_listener.vmix_ip = ip
            self.http_fetcher.vmix_ip = ip
            self.http_fetcher.vmix_http_port = int(port_str)
            
            self.tcp_listener.start()
            self.http_fetcher.start()

    def reset_tally_display(self):
        self.pvw_box.setText("PREVIEW\n---\n")
        self.pgm_box.setText("PROGRAM\n---\n")
        self.pvw_box.setStyleSheet(self.get_stylesheet(COLOR_OFF, COLOR_TEXT))
        self.pgm_box.setStyleSheet(self.get_stylesheet(COLOR_OFF, COLOR_TEXT))

    def process_input_list_update(self, inputs):
        current_hash = hash(json.dumps(inputs, sort_keys=True))
        if current_hash == self.last_input_hash: return
        self.last_input_hash = current_hash
        self.input_names = {item["number"]: item["name"] for item in inputs}
        self.ws_client.send_message({"type": "input_list", "inputs": inputs})
        logging.info(f"Input 목록 업데이트 ({len(inputs)}개) 및 서버 전송.")

    def process_tally_update(self, tally_info):
        tally_str = tally_info.get("tally_str", "")
        pgm, pvw = 0, 0
        for i, state in enumerate(tally_str, 1):
            if state == '1': pgm = i
            elif state == '2': pvw = i
        
        if pgm == self.last_pgm and pvw == self.last_pvw: return

        pgm_name = self.input_names.get(pgm, f"Input {pgm}")
        pvw_name = self.input_names.get(pvw, f"Input {pvw}")
        
        pgm_is_active = pgm > 0
        pvw_is_active = pvw > 0
        
        # 상태가 변경되었을 때만 GUI 및 애니메이션 업데이트
        if pgm_is_active != self.last_pgm_active or self.last_pgm != pgm:
            self.pgm_box.setText(f"PROGRAM ({pgm})\n{truncate_text(pgm_name)}\n")
            if pgm_is_active: self.pgm_anim.start()
            else: self.pgm_box.setStyleSheet(self.get_stylesheet(COLOR_OFF, COLOR_TEXT))

        if pvw_is_active != self.last_pvw_active or self.last_pvw != pvw:
            self.pvw_box.setText(f"PREVIEW ({pvw})\n{truncate_text(pvw_name)}\n")
            if pvw_is_active: self.pvw_anim.start()
            else: self.pvw_box.setStyleSheet(self.get_stylesheet(COLOR_OFF, COLOR_TEXT))

        self.last_pgm, self.last_pvw = pgm, pvw
        self.last_pgm_active, self.last_pvw_active = pgm_is_active, pvw_is_active
        
        self.ws_client.send_message({
            "type": "tally_update",
            "program": {"number": pgm, "name": pgm_name},
            "preview": {"number": pvw, "name": pvw_name}
        })

    def closeEvent(self, event):
        logging.info("애플리케이션 종료 중...")
        self.tcp_listener.stop()
        self.http_fetcher.stop()
        self.ws_client.stop()
        self.tcp_listener.wait()
        self.http_fetcher.wait()
        self.ws_client.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if qdarkstyle:
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    win = MainApp()
    win.show()
    sys.exit(app.exec_())
