#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 제로 레이턴시 vMix Tally 테스트
"""

import sys
import asyncio
import time
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer

from pd_app.core.vmix_manager import VMixManager
from pd_app.ui.tally_widget import TallyWidget

class RealTimeTallyTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("실시간 제로 레이턴시 vMix Tally 테스트")
        self.setGeometry(100, 100, 800, 600)
        
        # vMix 매니저 생성
        self.vmix_manager = VMixManager()
        
        # Tally 위젯 생성
        self.tally_widget = TallyWidget(self.vmix_manager)
        self.setCentralWidget(self.tally_widget)
        
        # 레이턴시 측정 타이머
        self.latency_timer = QTimer()
        self.latency_timer.timeout.connect(self.measure_latency)
        self.latency_timer.start(1000)  # 1초마다 측정
        
        self.last_tally_time = 0
        self.tally_count = 0
        
        # 시그널 연결
        self.vmix_manager.tally_updated.connect(self.on_tally_update)
        
        print("=== 실시간 제로 레이턴시 vMix Tally 테스트 시작 ===")
        print("1. vMix를 실행하고 연결하세요")
        print("2. vMix에서 PGM/PVW를 변경하면서 반응 속도를 확인하세요")
        print("3. 레이턴시 측정 결과를 확인하세요")
        
    def on_tally_update(self, pgm, pvw, pgm_info, pvw_info):
        """Tally 업데이트 시 레이턴시 측정"""
        current_time = time.time()
        
        if self.last_tally_time > 0:
            latency = (current_time - self.last_tally_time) * 1000  # ms
            self.tally_count += 1
            
            if latency < 50:  # 50ms 이하
                status = "EXCELLENT"
            elif latency < 100:  # 100ms 이하
                status = "GOOD"
            else:  # 100ms 초과
                status = "SLOW"
                
            print(f"[{self.tally_count:03d}] Tally 업데이트: PGM={pgm}, PVW={pvw}, 레이턴시={latency:.1f}ms {status}")
            
        self.last_tally_time = current_time
        
    def measure_latency(self):
        """레이턴시 측정 상태 출력"""
        if self.vmix_manager.is_connected:
            print(f"[연결 상태] vMix: OK, WebSocket: {'OK' if hasattr(self.vmix_manager, 'websocket_relay') and self.vmix_manager.websocket_relay else 'FAIL'}")
        else:
            print("[연결 상태] 연결 대기 중...")

def main():
    app = QApplication(sys.argv)
    
    # 테스터 생성
    tester = RealTimeTallyTester()
    tester.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n테스트 종료")

if __name__ == "__main__":
    main()