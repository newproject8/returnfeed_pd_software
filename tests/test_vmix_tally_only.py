#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vMix Tally 전용 테스트 - 실시간 반응 확인
"""

import sys
import time
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 시스템 경로 추가
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pd_app.core.vmix_manager import VMixManager
from pd_app.ui.tally_widget import TallyWidget

class VMixTallyTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("vMix Tally 실시간 테스트")
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 상태 표시
        self.status_label = QLabel("vMix Tally 테스트 준비")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # vMix 매니저 생성
        self.vmix_manager = VMixManager()
        
        # Tally 위젯 추가
        self.tally_widget = TallyWidget(self.vmix_manager)
        layout.addWidget(self.tally_widget)
        
        # 로그 표시
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 테스트 버튼
        self.test_button = QPushButton("TCP 리스너 테스트")
        self.test_button.clicked.connect(self.test_tcp_listener)
        layout.addWidget(self.test_button)
        
        # 통계
        self.tally_count = 0
        self.last_tally_time = 0
        self.latencies = []
        
        # 시그널 연결
        self.vmix_manager.tally_updated.connect(self.on_tally_update)
        self.vmix_manager.connection_status_changed.connect(self.on_connection_status)
        
        # 상태 업데이트 타이머
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)
        
        self.log("vMix Tally 테스트 시작")
        self.log("1. vMix를 실행하고 있는지 확인하세요")
        self.log("2. vMix TCP API가 활성화되어 있는지 확인하세요 (포트 8099)")
        self.log("3. Connect 버튼을 클릭하여 연결하세요")
        
    def log(self, message):
        """로그 메시지 추가"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        logger.info(message)
        
    def on_tally_update(self, pgm, pvw, pgm_info, pvw_info):
        """Tally 업데이트 시 호출"""
        current_time = time.time()
        
        if self.last_tally_time > 0:
            latency = (current_time - self.last_tally_time) * 1000  # ms
            self.latencies.append(latency)
            
            # 최근 10개만 유지
            if len(self.latencies) > 10:
                self.latencies.pop(0)
                
            avg_latency = sum(self.latencies) / len(self.latencies)
            
            self.log(f"Tally 업데이트: PGM={pgm} ({pgm_info.get('name', 'N/A')}), "
                    f"PVW={pvw} ({pvw_info.get('name', 'N/A')}), "
                    f"레이턴시={latency:.1f}ms (평균: {avg_latency:.1f}ms)")
        else:
            self.log(f"Tally 초기화: PGM={pgm}, PVW={pvw}")
            
        self.last_tally_time = current_time
        self.tally_count += 1
        
    def on_connection_status(self, status, color):
        """연결 상태 변경"""
        self.log(f"연결 상태: {status}")
        
    def test_tcp_listener(self):
        """TCP 리스너 테스트"""
        self.log("=" * 50)
        self.log("TCP 리스너 디버그 모드 시작")
        
        # 로깅 레벨 상승
        logging.getLogger('pd_app.core.vmix_manager').setLevel(logging.DEBUG)
        
        # 현재 연결 상태 확인
        if self.vmix_manager.is_connected:
            self.log("현재 vMix에 연결되어 있습니다")
            if self.vmix_manager.tcp_listener:
                self.log(f"TCP 리스너 상태: {'실행 중' if self.vmix_manager.tcp_listener.isRunning() else '중지됨'}")
        else:
            self.log("vMix에 연결되어 있지 않습니다")
            
    def update_status(self):
        """상태 업데이트"""
        if self.tally_count > 0 and self.latencies:
            avg_latency = sum(self.latencies) / len(self.latencies)
            self.status_label.setText(
                f"Tally 수신: {self.tally_count}회, "
                f"평균 레이턴시: {avg_latency:.1f}ms, "
                f"최근: {self.latencies[-1]:.1f}ms"
            )
        else:
            self.status_label.setText("Tally 대기 중...")

def main():
    app = QApplication(sys.argv)
    
    # 테스터 생성
    tester = VMixTallyTester()
    tester.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()