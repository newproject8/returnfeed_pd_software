# PD 통합 소프트웨어 즉시 적용 가능한 개선사항

## 🚀 바로 구현 가능한 기능들

### 1. **OBS Studio WebSocket 지원 추가**

#### 구현 파일: `pd_app/core/obs_manager.py`
```python
"""
OBS Studio WebSocket 통합 관리자
"""

import json
import asyncio
import logging
from typing import Optional, Dict, Any
import obsws_python as obs  # pip install obsws-python

from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)

class OBSManager(QObject):
    """OBS Studio 관리자"""
    
    # 시그널 정의
    scene_changed = pyqtSignal(str)
    streaming_started = pyqtSignal()
    streaming_stopped = pyqtSignal()
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    connection_status_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.host = "localhost"
        self.port = 4455
        self.password = ""
        self.connected = False
        
    def connect(self, host="localhost", port=4455, password=""):
        """OBS 연결"""
        try:
            self.client = obs.ReqClient(
                host=host, 
                port=port, 
                password=password
            )
            self.connected = True
            self.connection_status_changed.emit(True)
            logger.info(f"OBS Studio 연결 성공: {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"OBS 연결 실패: {e}")
            self.connected = False
            self.connection_status_changed.emit(False)
            return False
    
    def get_scenes(self):
        """씬 목록 가져오기"""
        if not self.connected:
            return []
        
        try:
            response = self.client.get_scene_list()
            return [scene['sceneName'] for scene in response.scenes]
        except Exception as e:
            logger.error(f"씬 목록 조회 실패: {e}")
            return []
    
    def switch_scene(self, scene_name):
        """씬 전환"""
        if not self.connected:
            return False
            
        try:
            self.client.set_current_program_scene(scene_name)
            self.scene_changed.emit(scene_name)
            return True
        except Exception as e:
            logger.error(f"씬 전환 실패: {e}")
            return False
    
    def start_streaming(self):
        """스트리밍 시작"""
        if not self.connected:
            return False
            
        try:
            self.client.start_stream()
            self.streaming_started.emit()
            return True
        except Exception as e:
            logger.error(f"스트리밍 시작 실패: {e}")
            return False
    
    def stop_streaming(self):
        """스트리밍 중지"""
        if not self.connected:
            return False
            
        try:
            self.client.stop_stream()
            self.streaming_stopped.emit()
            return True
        except Exception as e:
            logger.error(f"스트리밍 중지 실패: {e}")
            return False
```

### 2. **시스템 트레이 아이콘 추가**

#### 구현 코드
```python
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction

class SystemTrayManager:
    """시스템 트레이 관리자"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = None
        self.setup_tray()
        
    def setup_tray(self):
        """트레이 아이콘 설정"""
        # 아이콘 생성
        self.tray_icon = QSystemTrayIcon(self.main_window)
        self.tray_icon.setIcon(QIcon("assets/icon.png"))
        self.tray_icon.setToolTip("PD 통합 소프트웨어")
        
        # 메뉴 생성
        tray_menu = QMenu()
        
        # 메뉴 항목
        show_action = QAction("열기", self.main_window)
        show_action.triggered.connect(self.show_window)
        
        hide_action = QAction("숨기기", self.main_window)
        hide_action.triggered.connect(self.main_window.hide)
        
        separator = tray_menu.addSeparator()
        
        # Tally 상태 표시
        self.tally_status = QAction("Tally: 대기", self.main_window)
        self.tally_status.setEnabled(False)
        
        # NDI 소스 표시
        self.ndi_status = QAction("NDI: 연결 안됨", self.main_window)
        self.ndi_status.setEnabled(False)
        
        quit_action = QAction("종료", self.main_window)
        quit_action.triggered.connect(self.main_window.close)
        
        # 메뉴에 추가
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.tally_status)
        tray_menu.addAction(self.ndi_status)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # 더블클릭 이벤트
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # 트레이 표시
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """트레이 아이콘 활성화"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """윈도우 표시"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    def update_tally_status(self, camera, state):
        """Tally 상태 업데이트"""
        color = "🔴" if state == "PGM" else "🟢" if state == "PVW" else "⚫"
        self.tally_status.setText(f"Tally: {camera} {color}")
        
        # 알림 표시 (옵션)
        if state == "PGM":
            self.tray_icon.showMessage(
                "Tally 알림",
                f"{camera} - On Air",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
```

### 3. **키보드 단축키 시스템**

#### 구현 코드
```python
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

class ShortcutManager:
    """단축키 관리자"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.shortcuts = {}
        self.setup_default_shortcuts()
        
    def setup_default_shortcuts(self):
        """기본 단축키 설정"""
        # 전역 단축키
        self.add_shortcut("F1", self.show_help, "도움말")
        self.add_shortcut("F5", self.refresh_ndi_sources, "NDI 소스 새로고침")
        self.add_shortcut("F11", self.toggle_fullscreen, "전체화면")
        self.add_shortcut("Ctrl+Q", self.main_window.close, "종료")
        
        # 탭 이동
        self.add_shortcut("Alt+1", lambda: self.switch_tab(0), "로그인 탭")
        self.add_shortcut("Alt+2", lambda: self.switch_tab(1), "NDI 탭")
        self.add_shortcut("Alt+3", lambda: self.switch_tab(2), "Tally 탭")
        self.add_shortcut("Alt+4", lambda: self.switch_tab(3), "SRT 탭")
        
        # 프리뷰 제어
        self.add_shortcut("Space", self.toggle_preview, "프리뷰 시작/중지")
        self.add_shortcut("R", self.start_recording, "녹화 시작")
        self.add_shortcut("S", self.start_streaming, "스트리밍 시작")
        
        # Tally 제어 (숫자키)
        for i in range(1, 9):
            self.add_shortcut(
                str(i), 
                lambda x=i: self.select_tally_input(x),
                f"Tally 입력 {i}"
            )
    
    def add_shortcut(self, key_sequence, callback, description=""):
        """단축키 추가"""
        shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
        shortcut.activated.connect(callback)
        
        self.shortcuts[key_sequence] = {
            'shortcut': shortcut,
            'callback': callback,
            'description': description
        }
    
    def toggle_preview(self):
        """프리뷰 토글"""
        if hasattr(self.main_window, 'ndi_widget'):
            self.main_window.ndi_widget.toggle_preview()
    
    def select_tally_input(self, input_number):
        """Tally 입력 선택"""
        if hasattr(self.main_window, 'tally_widget'):
            self.main_window.tally_widget.select_input(input_number)
```

### 4. **설정 내보내기/가져오기**

#### 구현 코드
```python
import json
import zipfile
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog

class ConfigExporter:
    """설정 내보내기/가져오기"""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        
    def export_config(self):
        """설정 내보내기"""
        # 파일 대화상자
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "설정 내보내기",
            f"pd_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
        
        # ZIP 파일 생성
        with zipfile.ZipFile(file_path, 'w') as zipf:
            # 설정 파일
            config_data = {
                'version': '1.0',
                'exported_at': datetime.now().isoformat(),
                'settings': self.settings.config,
                'auth': self.get_exportable_auth(),
                'shortcuts': self.get_shortcuts_config()
            }
            
            zipf.writestr(
                'config.json',
                json.dumps(config_data, indent=2, ensure_ascii=False)
            )
            
            # 로그 파일 (옵션)
            if os.path.exists('logs/'):
                for log_file in os.listdir('logs/')[-5:]:  # 최근 5개
                    zipf.write(f'logs/{log_file}')
        
        logger.info(f"설정 내보내기 완료: {file_path}")
        return file_path
    
    def import_config(self):
        """설정 가져오기"""
        # 파일 대화상자
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "설정 가져오기",
            "",
            "ZIP Files (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # config.json 읽기
                config_data = json.loads(zipf.read('config.json'))
                
                # 버전 확인
                if config_data.get('version') != '1.0':
                    raise ValueError("호환되지 않는 설정 파일 버전")
                
                # 설정 적용
                self.settings.config = config_data['settings']
                self.settings.save_config()
                
                # 단축키 복원
                if 'shortcuts' in config_data:
                    self.restore_shortcuts(config_data['shortcuts'])
                
                logger.info(f"설정 가져오기 완료: {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"설정 가져오기 실패: {e}")
            return False
```

### 5. **실시간 성능 모니터링 위젯**

#### 구현 코드
```python
import psutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

class PerformanceMonitor(QWidget):
    """실시간 성능 모니터링"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_data()
        self.start_monitoring()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # CPU 그래프
        self.cpu_plot = pg.PlotWidget(title="CPU 사용률 (%)")
        self.cpu_plot.setYRange(0, 100)
        self.cpu_curve = self.cpu_plot.plot(pen='y')
        layout.addWidget(self.cpu_plot)
        
        # 메모리 그래프
        self.mem_plot = pg.PlotWidget(title="메모리 사용량 (MB)")
        self.mem_curve = self.mem_plot.plot(pen='g')
        layout.addWidget(self.mem_plot)
        
        # 네트워크 그래프
        self.net_plot = pg.PlotWidget(title="네트워크 (Mbps)")
        self.net_send_curve = self.net_plot.plot(pen='r', name='송신')
        self.net_recv_curve = self.net_plot.plot(pen='b', name='수신')
        self.net_plot.addLegend()
        layout.addWidget(self.net_plot)
        
        # 통계 라벨
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)
        
    def init_data(self):
        """데이터 초기화"""
        self.max_points = 100
        self.cpu_data = []
        self.mem_data = []
        self.net_send_data = []
        self.net_recv_data = []
        self.last_net_io = psutil.net_io_counters()
        
    def start_monitoring(self):
        """모니터링 시작"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # 1초마다 업데이트
        
    def update_data(self):
        """데이터 업데이트"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0)
        self.cpu_data.append(cpu_percent)
        if len(self.cpu_data) > self.max_points:
            self.cpu_data.pop(0)
        self.cpu_curve.setData(self.cpu_data)
        
        # 메모리
        mem = psutil.virtual_memory()
        mem_mb = mem.used / 1024 / 1024
        self.mem_data.append(mem_mb)
        if len(self.mem_data) > self.max_points:
            self.mem_data.pop(0)
        self.mem_curve.setData(self.mem_data)
        
        # 네트워크
        net_io = psutil.net_io_counters()
        send_mbps = (net_io.bytes_sent - self.last_net_io.bytes_sent) * 8 / 1024 / 1024
        recv_mbps = (net_io.bytes_recv - self.last_net_io.bytes_recv) * 8 / 1024 / 1024
        
        self.net_send_data.append(send_mbps)
        self.net_recv_data.append(recv_mbps)
        
        if len(self.net_send_data) > self.max_points:
            self.net_send_data.pop(0)
            self.net_recv_data.pop(0)
            
        self.net_send_curve.setData(self.net_send_data)
        self.net_recv_curve.setData(self.net_recv_data)
        
        self.last_net_io = net_io
        
        # 통계 업데이트
        self.update_stats(cpu_percent, mem)
        
    def update_stats(self, cpu_percent, mem):
        """통계 라벨 업데이트"""
        stats_text = f"""
        시스템 상태:
        CPU: {cpu_percent:.1f}% | 코어: {psutil.cpu_count()}
        메모리: {mem.percent:.1f}% 사용 ({mem.used/1024/1024/1024:.1f}GB / {mem.total/1024/1024/1024:.1f}GB)
        프로세스: {len(psutil.pids())} 개
        """
        self.stats_label.setText(stats_text)
```

### 6. **다크 모드 지원**

#### 구현 코드
```python
class ThemeManager:
    """테마 관리자"""
    
    def __init__(self, app):
        self.app = app
        self.current_theme = 'light'
        
    def apply_dark_theme(self):
        """다크 테마 적용"""
        dark_style = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: #484848;
        }
        
        QPushButton:pressed {
            background-color: #222;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3c3c;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
        }
        
        QTabWidget::pane {
            border: 1px solid #555;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #3c3c3c;
            padding: 8px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #484848;
        }
        
        QMenuBar {
            background-color: #2b2b2b;
        }
        
        QMenuBar::item:selected {
            background-color: #3c3c3c;
        }
        
        QMenu {
            background-color: #2b2b2b;
            border: 1px solid #555;
        }
        
        QMenu::item:selected {
            background-color: #3c3c3c;
        }
        """
        
        self.app.setStyleSheet(dark_style)
        self.current_theme = 'dark'
    
    def apply_light_theme(self):
        """라이트 테마 적용"""
        self.app.setStyleSheet("")  # 기본 스타일
        self.current_theme = 'light'
    
    def toggle_theme(self):
        """테마 토글"""
        if self.current_theme == 'light':
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
```

## 📝 구현 우선순위

1. **즉시 구현 가능 (1주일)**
   - ✅ 시스템 트레이 아이콘
   - ✅ 키보드 단축키
   - ✅ 다크 모드
   - ✅ 설정 내보내기/가져오기

2. **단기 구현 (2주일)**
   - ✅ OBS Studio 연동
   - ✅ 성능 모니터링 위젯
   - ✅ 자동 업데이트 체크

3. **중기 구현 (1개월)**
   - Stream Deck 기본 지원
   - 웹 제어 인터페이스
   - 플러그인 시스템 기초

## 🎯 결론

이러한 즉시 적용 가능한 개선사항들은 기존 코드베이스에 큰 변경 없이 추가할 수 있으며, 사용자 경험을 크게 향상시킬 수 있습니다. 특히 OBS Studio 연동과 시스템 트레이 기능은 실제 방송 현장에서 매우 유용할 것입니다.