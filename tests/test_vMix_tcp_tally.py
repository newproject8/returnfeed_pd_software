# -*- coding: utf-8 -*-
import sys
import os
import socket
import xml.etree.ElementTree as ET
import asyncio
import websockets
import threading
import json
import time
import logging
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QSizePolicy, QStatusBar, QMessageBox)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QPropertyAnimation, 
                          QAbstractAnimation, QRect, QSize, QVariantAnimation, QEventLoop, QEasingCurve)
from PyQt5.QtGui import QFont, QFontDatabase, QColor, QPalette
import qdarkstyle

# === Configuration ===
VMIX_DEFAULT_IP = "127.0.0.1"
VMIX_DEFAULT_PORT = "8088"  # HTTP API port
VMIX_TCP_PORT = "8099"  # TCP API port for subscription
WEBSOCKET_PORT = 8765
ANIMATION_DURATION = 500 # ms (0.5 seconds for quick glow effect)
FONT_DIR = "fonts"
REQUEST_TIMEOUT = 3 # seconds

# Colors - Basic Tally Colors
COLOR_OFF = "#333333"  # Basic gray for off state
COLOR_PVW_NORMAL = "#00aa00"  # Standard green for preview
COLOR_PVW_BRIGHT = "#00ff00"  # Bright green for animation
COLOR_PVW_GLOW = "#00ff00"    # Bright green glow
COLOR_PGM_NORMAL = "#aa0000"  # Standard red for program
COLOR_PGM_BRIGHT = "#ff0000"  # Bright red for animation
COLOR_PGM_GLOW = "#ff0000"    # Bright red glow
COLOR_TEXT = "#ffffff"  # White text for visibility
COLOR_TEXT_SHADOW = "rgba(0, 0, 0, 0.8)"  # Text shadow for depth

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Reduce requests/websockets noise
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


# === Helper ===
def truncate_text(text, max_length=12):
    """Truncate text to specified length with ellipsis (max 12 chars for input names)"""
    if not text:
        return "---"
    # For Korean text, we need to be more careful about character counting
    # Allow up to 12 characters to be displayed
    if len(text) <= max_length:
        return text
    # If longer than 12 chars, show first 9 chars + '...' (total 12 chars)
    return text[:9] + '...'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === WebSocket Server Manager ===
class WebsocketManager(threading.Thread):
    def __init__(self, port, status_callback=None):
        super().__init__(daemon=True)
        self.port = port
        self.clients = set()
        self.loop = asyncio.new_event_loop()
        self.server = None
        self._stop_event = threading.Event()
        self.latest_data = {"type": "status", "message": "Waiting for vMix data..."}
        self.status_callback = status_callback
        self._lock = threading.Lock()

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logging.info(f"WebSocket client connected: {client_addr}")
        if self.status_callback:
             self.status_callback(f"WS Client connected ({len(self.clients)})", append=True)
        try:
             # Send latest data immediately upon connection
            with self._lock:
                 await websocket.send(json.dumps(self.latest_data))
            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosedError:
             pass # Client disconnected expectedly
        finally:
            self.clients.remove(websocket)
            logging.info(f"WebSocket client disconnected: {client_addr}")
            if self.status_callback:
                 self.status_callback(f"WS Client disconnected ({len(self.clients)})", append=True)

    async def _serve(self):
         # Use 0.0.0.0 to allow connections from other machines
        async with websockets.serve(self.handler, "0.0.0.0", self.port) as server:
             self.server = server
             logging.info(f"WebSocket server started on ws://0.0.0.0:{self.port}")
             if self.status_callback:
                  self.status_callback(f"WebSocket server: ws://0.0.0.0:{self.port}", append=True)
             await self.server.wait_closed()
             logging.info("WebSocket server stopped.")

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
           # Start the server and keep the loop running
           serve_task = self.loop.create_task(self._serve())
           self.loop.run_until_complete(serve_task)
        except Exception as e:
            logging.error(f"WebSocket loop error: {e}")
        finally:
             self.loop.close()
             logging.info("WebSocket event loop closed.")


    def stop_server(self):
       logging.info("Stopping WebSocket server...")
       if self.loop and not self.loop.is_closed():
           if self.server:
               # Schedule server close from the loop's thread
               self.loop.call_soon_threadsafe(self.server.close)
               # Give it a moment to close connections before stopping the loop
               time.sleep(0.1) 
           # Only stop the loop if it's still running
           if self.loop.is_running():
               self.loop.call_soon_threadsafe(self.loop.stop)
       self._stop_event.set()
      

    async def _broadcast_message(self, message, clients_to_notify):
        if clients_to_notify:
             websockets.broadcast(clients_to_notify, message)

    def broadcast(self, data):
         with self._lock:
            self.latest_data = data # Store for new clients
         json_data = json.dumps(data, ensure_ascii=False)
         # Must call async function from the event loop's thread
         if self.loop.is_running() and self.clients:
            # Use copy of clients set to avoid issues during iteration if clients change
            asyncio.run_coroutine_threadsafe(
                 self._broadcast_message(json_data, self.clients.copy()), 
                 self.loop
            )

# === Main GUI Application ===
class VmixTallyApp(QWidget):
    
    # Signal: pvw_data(dict), pgm_data(dict), all_inputs(list), status_msg(str)
    tally_updated = pyqtSignal(dict, dict, list, str) 
    connection_error = pyqtSignal(str)
    status_message = pyqtSignal(str, bool) # message, append

    def __init__(self):
        super().__init__()
        self.setWindowTitle("vMix Tally Monitor & WebSocket Server")
        self.setGeometry(100, 100, 550, 300)

        self.fonts_loaded = False
        self.font_kor = QFont("Gmarket Sans", 16)
        self.font_eng = QFont("Metropolis", 16)
        self.font_small = QFont("Metropolis", 9)
        self.load_fonts()

        self.init_ui()
        self.init_animations()
       
        # TCP connection variables
        self.tcp_socket = None
        self.tcp_thread = None
        self.is_connected = False
        self.tcp_running = False
        
        # Input names storage
        self.input_names = {}  # {input_number: input_name}
        
        # Timer for fetching input names
        self.input_names_timer = QTimer()
        self.input_names_timer.timeout.connect(self.fetch_input_names)
        
        # State tracking for animation trigger
        self.last_pvw_key = None
        self.last_pgm_key = None
        self.last_pvw_active = False
        self.last_pgm_active = False
        self.last_all_inputs_hash = 0 # simple way to check if list changed

        self.tally_updated.connect(self.update_gui_and_ws)
        self.connection_error.connect(self.handle_connection_error)
        self.status_message.connect(self.update_status)

        # Start Websocket Server
        self.ws_manager = WebsocketManager(WEBSOCKET_PORT, self.update_status_threadsafe)
        self.ws_manager.start()
        self.update_status(f"Application Started. WebSocket on port {WEBSOCKET_PORT}.")


    def load_fonts(self):
         font_path = resource_path(FONT_DIR)
         if not os.path.exists(font_path):
             logging.warning(f"Font directory not found: {font_path}")
             self.fonts_loaded = False
             return
             
         try:
            families_before = set(QFontDatabase.applicationFontFamilies(QFontDatabase.Any))
            font_files = [f for f in os.listdir(font_path) if f.lower().endswith(('.ttf', '.otf'))]
            loaded_any = False
            for font_file in font_files:
                 font_id = QFontDatabase.addApplicationFont(os.path.join(font_path, font_file))
                 if font_id == -1:
                     logging.warning(f"Failed to load font: {font_file}")
                 else:
                    loaded_any = True
                    # logging.info(f"Loaded font: {font_file} - Families: {QFontDatabase.applicationFontFamilies(font_id)}")

            if loaded_any:
                 families_after = set(QFontDatabase.applicationFontFamilies(QFontDatabase.Any))
                 new_families = families_after - families_before
                 # Find best match if exact name isn't guaranteed
                 kor_family = next((f for f in new_families if "gmarket" in f.lower()), "Gmarket Sans")
                 eng_family = next((f for f in new_families if "metropolis" in f.lower()), "Metropolis")

                 self.font_kor = QFont(kor_family, 14, QFont.Bold)  # G마켓 산스
                 self.font_eng = QFont(eng_family, 14, QFont.Bold)  # Metropolis
                 self.font_small = QFont(eng_family, 9)
                 self.fonts_loaded = True
                 logging.info(f"Custom fonts loaded: {kor_family}, {eng_family}")
            else:
                 logging.warning("No custom fonts found or loaded.")
                 self.fonts_loaded = False

         except Exception as e:
             logging.error(f"Error loading fonts: {e}")
             self.fonts_loaded = False


    def set_widget_font(self, widget, text=""):
         if not self.fonts_loaded:
              return
         # Simple check for Korean characters
         if any('\uac00' <= char <= '\ud7a3' for char in text):
              widget.setFont(self.font_kor)
         else:
              widget.setFont(self.font_eng)

    def get_stylesheet(self, base_color, text_color, glow_color=None):
        """Generate stylesheet with basic box design and improved text visibility"""
        
        if glow_color:
            # Active state with thicker colored border for glow effect
            return f"""
            QLabel {{
                background-color: {base_color};
                border: 4px solid {glow_color};
                border-radius: 5px;
                color: {text_color};
                font-weight: bold;
                text-align: center;
                padding: 8px;
                margin: 5px;
                font-size: 16pt;
                letter-spacing: 1.5px;
            }}
            """
        else:
            # Inactive/normal state without glow - but keep bold font
            return f"""
            QLabel {{
                background-color: {base_color};
                border: 2px solid #555555;
                border-radius: 5px;
                color: {text_color};
                font-weight: bold;
                text-align: center;
                padding: 10px;
                margin: 5px;
                font-size: 16pt;
                letter-spacing: 1.5px;
            }}
            """

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # --- IP/Port Row ---
        ctrl_layout = QHBoxLayout()
        self.ip_label = QLabel("vMix IP:")
        self.ip_input = QLineEdit(VMIX_DEFAULT_IP)
        self.port_label = QLabel("Port:")
        self.port_input = QLineEdit(VMIX_DEFAULT_PORT)
        self.port_input.setMaximumWidth(60)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        self.ip_label.setFont(self.font_small)
        self.port_label.setFont(self.font_small)
        self.ip_input.setFont(self.font_small)
        self.port_input.setFont(self.font_small)
        self.connect_button.setFont(self.font_small)

        ctrl_layout.addWidget(self.ip_label)
        ctrl_layout.addWidget(self.ip_input)
        ctrl_layout.addWidget(self.port_label)
        ctrl_layout.addWidget(self.port_input)
        ctrl_layout.addStretch(1)
        ctrl_layout.addWidget(self.connect_button)
        main_layout.addLayout(ctrl_layout)

        # --- Tally Row ---
        tally_layout = QHBoxLayout()
        tally_layout.setSpacing(20)

        self.pvw_box = QLabel("PREVIEW\n---\n")
        self.pvw_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pvw_box.setFixedSize(250, 100)  # 크기 증가: 80->100 for third line
        self.pvw_box.setStyleSheet(self.get_stylesheet(COLOR_OFF, COLOR_TEXT))
        self.pvw_box.setFont(self.font_eng) # Default

        self.pgm_box = QLabel("PROGRAM\n---\n")
        self.pgm_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pgm_box.setFixedSize(250, 100)  # 크기 증가: 80->100 for third line
        self.pgm_box.setStyleSheet(self.get_stylesheet(COLOR_OFF, COLOR_TEXT))
        self.pgm_box.setFont(self.font_eng) # Default

        tally_layout.addWidget(self.pvw_box)
        tally_layout.addWidget(self.pgm_box)
        main_layout.addLayout(tally_layout, stretch=1) # stretch makes tally boxes grow

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setFont(self.font_small)
        main_layout.addWidget(self.status_bar)
         
        self.setLayout(main_layout)
        self.reset_tally_display()

    def init_animations(self):
        # Modern Preview Animation with smooth neon glow transitions
        self.pvw_anim = QVariantAnimation()
        self.pvw_anim.setDuration(ANIMATION_DURATION)
        self.pvw_anim.setEasingCurve(QEasingCurve.InOutSine)  # Added easing curve for smoother animation
        self.pvw_anim.setStartValue(QColor(COLOR_PVW_BRIGHT))
        self.pvw_anim.setEndValue(QColor(COLOR_PVW_NORMAL))
        # Simplified keyframes for more regular animation
        self.pvw_anim.setKeyValueAt(0.0, QColor(COLOR_PVW_BRIGHT))  # Start with bright
        self.pvw_anim.setKeyValueAt(0.5, QColor(COLOR_PVW_GLOW))    # Peak glow at middle
        self.pvw_anim.setKeyValueAt(1.0, QColor(COLOR_PVW_NORMAL))  # End with normal
        self.pvw_anim.valueChanged.connect(self._animate_pvw_color)
        
        # Modern Program Animation with smooth neon glow transitions
        self.pgm_anim = QVariantAnimation()
        self.pgm_anim.setDuration(ANIMATION_DURATION)
        self.pgm_anim.setEasingCurve(QEasingCurve.InOutSine)  # Added easing curve for smoother animation
        self.pgm_anim.setStartValue(QColor(COLOR_PGM_BRIGHT))
        self.pgm_anim.setEndValue(QColor(COLOR_PGM_NORMAL))
        # Simplified keyframes for more regular animation
        self.pgm_anim.setKeyValueAt(0.0, QColor(COLOR_PGM_BRIGHT))  # Start with bright
        self.pgm_anim.setKeyValueAt(0.5, QColor(COLOR_PGM_GLOW))    # Peak glow at middle
        self.pgm_anim.setKeyValueAt(1.0, QColor(COLOR_PGM_NORMAL))  # End with normal
        self.pgm_anim.valueChanged.connect(self._animate_pgm_color)

    def _animate_pvw_color(self, color):
        """Update preview box with simple glow animation"""
        # Determine if this is an active/bright state for glow effect
        is_bright = color.name().upper() in [COLOR_PVW_BRIGHT.upper(), COLOR_PVW_GLOW.upper()]
        glow_color = COLOR_PVW_GLOW if is_bright else None
        
        self.pvw_box.setStyleSheet(
            self.get_stylesheet(
                color.name(), 
                COLOR_TEXT, 
                glow_color=glow_color
            )
        )

    def _animate_pgm_color(self, color):
        """Update program box with simple glow animation"""
        # Determine if this is an active/bright state for glow effect
        is_bright = color.name().upper() in [COLOR_PGM_BRIGHT.upper(), COLOR_PGM_GLOW.upper()]
        glow_color = COLOR_PGM_GLOW if is_bright else None
        
        self.pgm_box.setStyleSheet(
            self.get_stylesheet(
                color.name(), 
                COLOR_TEXT, 
                glow_color=glow_color
            )
        )

    def start_animation(self, animation: QVariantAnimation, box: QLabel, normal_color:str ):
         if animation.state() == QAbstractAnimation.Running:
             animation.stop()
             # Wait a moment for the animation to fully stop
             QApplication.processEvents()
         # Set initial state with glow effect for active boxes
         glow_color = COLOR_PVW_GLOW if box == self.pvw_box else COLOR_PGM_GLOW
         # Apply glow effect immediately
         box.setStyleSheet(self.get_stylesheet(normal_color, COLOR_TEXT, glow_color=glow_color))
         # Force update to ensure glow is visible
         box.update()
         QApplication.processEvents()
         animation.start()

    def update_status_threadsafe(self, message, append=False):
         # Use signal to update GUI from websocket thread safely
         self.status_message.emit(message, append)

    def update_status(self, message, append=False):
        if append:
             current = self.status_bar.currentMessage()
             # Limit history
             parts = current.split(" | ")
             if len(parts) > 3:
                  parts = parts[-3:]
             new_msg = " | ".join(parts) + " | " + message
             self.status_bar.showMessage(new_msg)
        else:
            self.status_bar.showMessage(message)
        # logging.info(f"Status: {message}")

    def update_tally_status(self, pvw_status, pgm_status):
        """Update tally status with simple glow animations"""
        if pvw_status:
            self.start_animation(self.pvw_anim, self.pvw_box, COLOR_PVW_NORMAL)
        else:
            # Apply simple off state
            self.pvw_box.setStyleSheet(
                self.get_stylesheet(
                    COLOR_OFF, 
                    COLOR_TEXT, 
                    glow_color=None
                )
            )
            
        if pgm_status:
            self.start_animation(self.pgm_anim, self.pgm_box, COLOR_PGM_NORMAL)
        else:
            # Apply simple off state
            self.pgm_box.setStyleSheet(
                self.get_stylesheet(
                    COLOR_OFF, 
                    COLOR_TEXT, 
                    glow_color=None
                )
            )

    def toggle_connection(self):
        if self.is_connected:
            # Stop TCP connection
            self.tcp_running = False
            if self.tcp_thread and self.tcp_thread.is_alive():
                self.tcp_thread.join(timeout=2.0)
            self.is_connected = False
            self.connect_button.setText("Connect")
            self.ip_input.setEnabled(True)
            self.port_input.setEnabled(True)
            self.update_status("Disconnected from vMix.")
            self.reset_tally_display()
            # Stop input names timer
            self.input_names_timer.stop()
            # Broadcast disconnect status
            self.ws_manager.broadcast({
                 "type": "vmix_status", 
                 "connected": False, 
                 "message": "Disconnected",
                 "preview": {"number": 0, "name": "OFF", "key": None},
                 "program": {"number": 0, "name": "OFF", "key": None},
                 "all_inputs": [],
                 "timestamp": time.time()
                 })
        else:
            ip = self.ip_input.text()
            if not ip:
                 QMessageBox.warning(self, "Input Error", "IP cannot be empty.")
                 return
            self.update_status(f"Connecting to vMix TCP at {ip}:{VMIX_TCP_PORT}...")
            
            # Start TCP connection in separate thread
            self.tcp_running = True
            self.tcp_thread = threading.Thread(target=self.tcp_connect_and_listen, daemon=True)
            self.tcp_thread.start()
            
            # Fetch input names immediately, then start timer (fetch every 5 seconds)
            self.fetch_input_names()
            self.input_names_timer.start(5000)
            
            self.is_connected = True
            self.connect_button.setText("Disconnect")
            self.ip_input.setEnabled(False)
            self.port_input.setEnabled(False) 


    def reset_tally_display(self):
         """Reset tally display to off state"""
         self.pvw_box.setText("PREVIEW\n---\n")
         self.pvw_box.setStyleSheet(
             self.get_stylesheet(
                 COLOR_OFF, 
                 COLOR_TEXT, 
                 glow_color=None
             )
         )
         self.set_widget_font(self.pvw_box, "")
         
         self.pgm_box.setText("PROGRAM\n---\n")
         self.pgm_box.setStyleSheet(
             self.get_stylesheet(
                 COLOR_OFF, 
                 COLOR_TEXT, 
                 glow_color=None
             )
         )
         self.set_widget_font(self.pgm_box, "")
         
         self.last_pvw_key = None
         self.last_pgm_key = None
         self.last_pvw_active = False
         self.last_pgm_active = False
         self.last_all_inputs_hash = 0


    def tcp_connect_and_listen(self):
        """TCP connection thread function for vMix subscription"""
        ip = self.ip_input.text()
        tcp_port = int(VMIX_TCP_PORT)
        
        try:
            # Create TCP socket connection
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(5.0)  # 5 second timeout for connection
            self.tcp_socket.connect((ip, tcp_port))
            
            # Send SUBSCRIBE TALLY command
            subscribe_cmd = "SUBSCRIBE TALLY\r\n"
            self.tcp_socket.send(subscribe_cmd.encode('utf-8'))
            
            # Set socket to non-blocking for receiving data
            self.tcp_socket.settimeout(1.0)
            
            logging.info(f"TCP connected to vMix at {ip}:{tcp_port} and subscribed to TALLY")
            
            buffer = ""
            while self.tcp_running:
                try:
                    # Receive data from vMix
                    data = self.tcp_socket.recv(4096).decode('utf-8')
                    if not data:
                        break  # Connection closed by server
                    
                    buffer += data
                    
                    # Process complete lines
                    while '\r\n' in buffer:
                        line, buffer = buffer.split('\r\n', 1)
                        logging.info(f"TCP received: {line}")  # 디버깅용 로그 추가
                        
                        if line.startswith('TALLY OK'):
                            # Parse tally data: "TALLY OK 102" format (3-digit: PVW-PGM-Other)
                            parts = line.split()
                            if len(parts) >= 3:
                                try:
                                    tally_data = parts[2]  # 3자리 숫자 (예: "021")
                                    if len(tally_data) >= 3:
                                        # vMix TALLY 형식: 각 자리는 해당 Input의 상태를 나타냄
                                        # 예: "021" = Input 1이 Preview, Input 2가 Program
                                        pvw_input = 0
                                        pgm_input = 0
                                        
                                        # 각 자리를 확인하여 어떤 Input이 Preview/Program인지 찾기
                                        # vMix 공식 문서: 0 = off, 1 = program, 2 = preview
                                        for i, char in enumerate(tally_data):
                                            if char == '2':  # Preview
                                                pvw_input = i + 1  # 1-based Input 번호
                                            elif char == '1':  # Program
                                                pgm_input = i + 1  # 1-based Input 번호
                                        
                                        # Create data structure with actual input names
                                        pgm_name = self.input_names.get(pgm_input, f"Input {pgm_input}") if pgm_input > 0 else "NONE"
                                        pvw_name = self.input_names.get(pvw_input, f"Input {pvw_input}") if pvw_input > 0 else "NONE"
                                        
                                        pgm_data = {"number": pgm_input, "name": pgm_name, "key": f"input_{pgm_input}" if pgm_input > 0 else None}
                                        pvw_data = {"number": pvw_input, "name": pvw_name, "key": f"input_{pvw_input}" if pvw_input > 0 else None}
                                        
                                        status_msg = f"TCP Connected. PVW: Input {pvw_input}, PGM: Input {pgm_input}"
                                        logging.info(f"Parsed TALLY: {tally_data} -> PVW: Input {pvw_input}, PGM: Input {pgm_input}")
                                        self.tally_updated.emit(pvw_data, pgm_data, [], status_msg)
                                    else:
                                        logging.warning(f"Invalid TALLY data length: {tally_data}")
                                        
                                except (ValueError, IndexError) as e:
                                    logging.error(f"Error parsing TALLY data: {e}")
                                    continue
                        elif 'TALLY' in line:
                            # 다른 TALLY 형식도 로깅
                            logging.info(f"Unknown TALLY format: {line}")
                        
                except socket.timeout:
                    # Timeout is normal, continue listening
                    continue
                except socket.error as e:
                    logging.error(f"TCP socket error: {e}")
                    break
                    
        except socket.error as e:
            self.connection_error.emit(f"TCP Connection Failed: {e}")
        except Exception as e:
            logging.exception("Unexpected error during TCP connection")
            self.connection_error.emit(f"TCP Unexpected Error: {e}")
        finally:
            if self.tcp_socket:
                try:
                    self.tcp_socket.close()
                except:
                    pass
                self.tcp_socket = None
            logging.info("TCP connection closed")

    def handle_connection_error(self, message):
         logging.error(message)
         self.update_status(f"ERROR: {message}")
         # Optionally auto-disconnect on persistent errors
         # self.toggle_connection() 
         self.reset_tally_display()
         self.ws_manager.broadcast({
                 "type": "vmix_status", 
                 "connected": False, 
                 "message": message,
                  "preview": {"number": 0, "name": "OFF", "key": None},
                  "program": {"number": 0, "name": "OFF", "key": None},
                  "all_inputs": [],
                 "timestamp": time.time()
                 })

    def fetch_input_names(self):
        """Fetch input names from vMix HTTP API"""
        if not self.is_connected:
            return
            
        try:
            ip = self.ip_input.text()
            port = self.port_input.text()
            url = f"http://{ip}:{port}/api"
            
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                # Clear existing names
                self.input_names.clear()
                
                # Parse input names
                for input_elem in root.findall('.//input'):
                    try:
                        number = int(input_elem.get('number', 0))
                        title = input_elem.get('title', f'Input {number}')
                        self.input_names[number] = title
                    except (ValueError, TypeError):
                        continue
                        
                logging.info(f"Fetched {len(self.input_names)} input names")
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to fetch input names: {e}")
        except ET.ParseError as e:
            logging.warning(f"Failed to parse vMix XML: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching input names: {e}")


    def update_gui_and_ws(self, pvw_data, pgm_data, all_inputs, status_msg):
        self.update_status(status_msg)

        pvw_name = pvw_data.get("name", "NONE")
        pvw_key = pvw_data.get("key")
        pvw_num = pvw_data.get("number", 0)
        pvw_is_active = (pvw_num != 0 and pvw_name != "NONE")
        
        pgm_name = pgm_data.get("name", "NONE")
        pgm_key = pgm_data.get("key")
        pgm_num = pgm_data.get("number", 0)
        pgm_is_active = (pgm_num != 0 and pgm_name != "NONE")

        current_inputs_hash = hash(tuple(sorted(i['key'] for i in all_inputs if i['key'])))
        
        # --- Update Preview ---
        pvw_display_text = f"PREVIEW ({pvw_num})\n{truncate_text(pvw_name)}\n"
        self.pvw_box.setText(pvw_display_text)
        self.set_widget_font(self.pvw_box, pvw_name)
        
        # Simplified animation logic - always trigger animation when state changes
        if pvw_is_active != self.last_pvw_active or pvw_key != self.last_pvw_key:
            if pvw_is_active:
                # Start glow animation for active state
                self.start_animation(self.pvw_anim, self.pvw_box, COLOR_PVW_NORMAL)
            else:
                # Stop animation and set to off state
                if self.pvw_anim.state() == QAbstractAnimation.Running:
                    self.pvw_anim.stop()
                self.pvw_box.setStyleSheet(
                    self.get_stylesheet(
                        COLOR_OFF, 
                        COLOR_TEXT, 
                        glow_color=None
                    )
                )


        # --- Update Program ---
        pgm_display_text = f"PROGRAM ({pgm_num})\n{truncate_text(pgm_name)}\n"
        self.pgm_box.setText(pgm_display_text)
        self.set_widget_font(self.pgm_box, pgm_name)
        
        # Simplified animation logic - always trigger animation when state changes
        if pgm_is_active != self.last_pgm_active or pgm_key != self.last_pgm_key:
            if pgm_is_active:
                # Start glow animation for active state
                self.start_animation(self.pgm_anim, self.pgm_box, COLOR_PGM_NORMAL)
            else:
                # Stop animation and set to off state
                if self.pgm_anim.state() == QAbstractAnimation.Running:
                    self.pgm_anim.stop()
                self.pgm_box.setStyleSheet(
                    self.get_stylesheet(
                        COLOR_OFF, 
                        COLOR_TEXT, 
                        glow_color=None
                    )
                )
              
        # --- Broadcast via WebSocket if anything changed ---
        has_changed = (
             pvw_key != self.last_pvw_key or
             pgm_key != self.last_pgm_key or
             pvw_is_active != self.last_pvw_active or
             pgm_is_active != self.last_pgm_active or
             current_inputs_hash != self.last_all_inputs_hash
        )

        if has_changed:
             payload = {
                 "type": "tally_update",
                 "connected": True,
                 "timestamp": time.time(),
                 "preview": pvw_data,
                 "program": pgm_data,
                 "all_inputs": all_inputs
             }
             # logging.debug(f"Broadcasting: {payload}")
             self.ws_manager.broadcast(payload)

        # Update last state
        self.last_pvw_key = pvw_key
        self.last_pgm_key = pgm_key
        self.last_pvw_active = pvw_is_active
        self.last_pgm_active = pgm_is_active
        self.last_all_inputs_hash = current_inputs_hash


    def closeEvent(self, event):
        logging.info("Closing application...")
        # Stop TCP connection
        self.tcp_running = False
        if self.tcp_thread and self.tcp_thread.is_alive():
            self.tcp_thread.join(timeout=2.0)
        # Stop input names timer
        if hasattr(self, 'input_names_timer'):
            self.input_names_timer.stop()
        if self.ws_manager and self.ws_manager.is_alive():
            self.ws_manager.stop_server()
            # Give the thread a moment to shut down the loop
            self.ws_manager.join(timeout=2.0) 
        event.accept()


# === Main Execution ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply dark style
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    window = VmixTallyApp()
    window.show()
    sys.exit(app.exec_())