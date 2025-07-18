#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로컬 실시간 제로 레이턴시 vMix Tally 테스트 (WebSocket 없음)
"""

import sys
import time
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from pd_app.core.vmix_manager import VMixManager
from pd_app.ui.tally_widget import TallyWidget

class LocalTallyTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("로컬 실시간 제로 레이턴시 vMix Tally 테스트")
        self.setGeometry(100, 100, 900, 700)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 테스트 정보 표시
        info_label = QLabel("=== 로컬 실시간 제로 레이턴시 vMix Tally 테스트 ===")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(info_label)
        
        # 성능 측정 라벨
        self.performance_label = QLabel("성능 측정 대기 중...")
        self.performance_label.setStyleSheet("font-size: 12px; margin: 10px;")
        layout.addWidget(self.performance_label)
        
        # vMix 매니저 생성
        self.vmix_manager = VMixManager()
        
        # Tally 위젯 생성
        self.tally_widget = TallyWidget(self.vmix_manager)
        layout.addWidget(self.tally_widget)
        
        # 테스트 버튼
        self.test_button = QPushButton("성능 테스트 시작")
        self.test_button.clicked.connect(self.start_performance_test)
        layout.addWidget(self.test_button)
        
        # 성능 측정 변수
        self.tally_times = []
        self.test_start_time = 0
        self.test_count = 0
        self.max_latency = 0
        self.min_latency = float('inf')
        self.total_latency = 0
        
        # 성능 측정 타이머
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance_stats)
        self.performance_timer.start(1000)  # 1초마다 업데이트
        
        # 시그널 연결
        self.vmix_manager.tally_updated.connect(self.on_tally_update)
        self.vmix_manager.connection_status_changed.connect(self.on_connection_status)
        
        print("=== 로컬 실시간 제로 레이턴시 vMix Tally 테스트 시작 ===")
        print("1. vMix를 실행하고 Connect 버튼을 클릭하세요")
        print("2. vMix에서 PGM/PVW를 빠르게 변경하면서 반응 속도를 확인하세요")
        print("3. '성능 테스트 시작' 버튼을 클릭하여 정확한 레이턴시를 측정하세요")
        
    def on_tally_update(self, pgm, pvw, pgm_info, pvw_info):
        """Tally 업데이트 시 레이턴시 측정"""
        current_time = time.time()
        
        if self.test_start_time > 0:
            # 성능 테스트 중인 경우만 측정
            latency = (current_time - self.test_start_time) * 1000  # ms
            
            self.tally_times.append(latency)
            self.test_count += 1
            
            # 통계 업데이트
            self.max_latency = max(self.max_latency, latency)
            self.min_latency = min(self.min_latency, latency)
            self.total_latency += latency
            
            # 상태 평가
            if latency < 10:
                status = "EXCELLENT"
            elif latency < 50:
                status = "VERY_GOOD"
            elif latency < 100:
                status = "GOOD"
            else:
                status = "SLOW"
                
            print(f"[{self.test_count:03d}] PGM={pgm}, PVW={pvw}, 레이턴시={latency:.1f}ms [{status}]")
        
        # 테스트 시작 시간 업데이트 (다음 측정을 위해)
        self.test_start_time = current_time
        
    def on_connection_status(self, status, color):
        """연결 상태 변경"""
        print(f"[연결 상태] {status} ({color})")
        
    def start_performance_test(self):
        """성능 테스트 시작"""
        if not self.vmix_manager.is_connected:
            print("[오류] vMix에 먼저 연결하세요!")
            return
            
        # 통계 초기화
        self.tally_times = []
        self.test_start_time = time.time()
        self.test_count = 0
        self.max_latency = 0
        self.min_latency = float('inf')
        self.total_latency = 0
        
        self.test_button.setText("성능 테스트 중... (30초)")
        self.test_button.setEnabled(False)
        
        # 30초 후 테스트 종료
        QTimer.singleShot(30000, self.stop_performance_test)
        
        print("\n=== 성능 테스트 시작 ===")
        print("30초 동안 vMix에서 PGM/PVW를 빠르게 변경하세요!")
        
    def stop_performance_test(self):
        """성능 테스트 종료"""
        self.test_button.setText("성능 테스트 시작")
        self.test_button.setEnabled(True)
        
        if self.test_count > 0:
            avg_latency = self.total_latency / self.test_count
            
            print(f"\n=== 성능 테스트 결과 ===")
            print(f"총 측정 횟수: {self.test_count}")
            print(f"평균 레이턴시: {avg_latency:.1f}ms")
            print(f"최소 레이턴시: {self.min_latency:.1f}ms")
            print(f"최대 레이턴시: {self.max_latency:.1f}ms")
            
            # 성능 등급 평가
            if avg_latency < 10:
                grade = "A+ (EXCELLENT)"
            elif avg_latency < 50:
                grade = "A (VERY_GOOD)"
            elif avg_latency < 100:
                grade = "B (GOOD)"
            else:
                grade = "C (NEEDS_IMPROVEMENT)"
                
            print(f"성능 등급: {grade}")
            
            # 실시간 레이턴시 분석
            excellent_count = sum(1 for t in self.tally_times if t < 10)
            good_count = sum(1 for t in self.tally_times if 10 <= t < 50)
            
            print(f"실시간 반응 (10ms 이하): {excellent_count}/{self.test_count} ({excellent_count/self.test_count*100:.1f}%)")
            print(f"양호한 반응 (50ms 이하): {good_count}/{self.test_count} ({good_count/self.test_count*100:.1f}%)")
            
        else:
            print("테스트 중 Tally 변경이 감지되지 않았습니다.")
            
    def update_performance_stats(self):
        """성능 통계 업데이트"""
        if self.vmix_manager.is_connected:
            if self.test_count > 0:
                avg_latency = self.total_latency / self.test_count
                self.performance_label.setText(
                    f"성능 통계 - 측정 횟수: {self.test_count}, "
                    f"평균 레이턴시: {avg_latency:.1f}ms, "
                    f"최소: {self.min_latency:.1f}ms, "
                    f"최대: {self.max_latency:.1f}ms"
                )
            else:
                self.performance_label.setText("성능 측정 준비 완료 - vMix에서 PGM/PVW를 변경하세요")
        else:
            self.performance_label.setText("vMix 연결 대기 중...")

def main():
    app = QApplication(sys.argv)
    
    # 테스터 생성
    tester = LocalTallyTester()
    tester.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n테스트 종료")

if __name__ == "__main__":
    main()