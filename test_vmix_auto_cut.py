#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vMix 자동 컷 테스트 소프트웨어

기능:
- vMix의 1-4번 인풋을 랜덤하게 프리뷰로 이동
- 2-5초 간격으로 랜덤하게 프리뷰를 프로그램으로 컷
- 중지될 때까지 계속 순환
"""

import requests
import time
import random
import threading
import sys
from typing import Optional

class VMixAutoController:
    def __init__(self, host: str = "127.0.0.1", port: int = 8088):
        """
        vMix 자동 컨트롤러 초기화
        
        Args:
            host: vMix 서버 호스트 (기본값: 127.0.0.1)
            port: vMix 서버 포트 (기본값: 8088)
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api"
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # 사용할 인풋 번호 (1-4번)
        self.inputs = [1, 2, 3, 4]
        
        print(f"vMix 자동 컨트롤러 초기화됨: {self.base_url}")
    
    def send_command(self, function: str, input_num: Optional[int] = None) -> bool:
        """
        vMix에 명령 전송
        
        Args:
            function: vMix 함수명 (예: 'PreviewInput', 'Cut')
            input_num: 인풋 번호 (선택사항)
            
        Returns:
            bool: 명령 전송 성공 여부
        """
        try:
            params = {'Function': function}
            if input_num is not None:
                params['Input'] = str(input_num)
            
            response = requests.get(self.base_url, params=params, timeout=5)
            
            if response.status_code == 200:
                if input_num:
                    print(f"✅ 명령 전송 성공: {function} (Input {input_num})")
                else:
                    print(f"✅ 명령 전송 성공: {function}")
                return True
            else:
                print(f"❌ 명령 전송 실패: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 연결 오류: {e}")
            return False
    
    def preview_random_input(self) -> bool:
        """
        랜덤한 인풋을 프리뷰로 이동
        
        Returns:
            bool: 명령 전송 성공 여부
        """
        input_num = random.choice(self.inputs)
        print(f"🎯 인풋 {input_num}을(를) 프리뷰로 이동...")
        return self.send_command('PreviewInput', input_num)
    
    def cut_to_program(self) -> bool:
        """
        프리뷰를 프로그램으로 컷
        
        Returns:
            bool: 명령 전송 성공 여부
        """
        print(f"✂️ 프리뷰를 프로그램으로 컷...")
        return self.send_command('Cut')
    
    def get_random_delay(self) -> float:
        """
        2-5초 사이의 랜덤 지연 시간 생성
        
        Returns:
            float: 랜덤 지연 시간 (초)
        """
        return random.uniform(2.0, 5.0)
    
    def test_connection(self) -> bool:
        """
        vMix 연결 테스트
        
        Returns:
            bool: 연결 성공 여부
        """
        try:
            response = requests.get(f"http://{self.host}:{self.port}/api", timeout=5)
            if response.status_code == 200:
                print(f"✅ vMix 연결 성공: {self.base_url}")
                return True
            else:
                print(f"❌ vMix 연결 실패: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ vMix 연결 오류: {e}")
            return False
    
    def auto_cut_loop(self):
        """
        자동 컷 루프 실행
        """
        print("🔄 자동 컷 루프 시작...")
        
        while self.running:
            try:
                # 1. 랜덤 인풋을 프리뷰로 이동
                if not self.preview_random_input():
                    print("⚠️ 프리뷰 명령 실패, 계속 진행...")
                
                # 2. 랜덤 지연 (2-5초)
                delay = self.get_random_delay()
                print(f"⏱️ {delay:.1f}초 대기 중...")
                
                # 지연 시간 동안 0.1초마다 running 상태 확인
                elapsed = 0
                while elapsed < delay and self.running:
                    time.sleep(0.1)
                    elapsed += 0.1
                
                if not self.running:
                    break
                
                # 3. 프리뷰를 프로그램으로 컷
                if not self.cut_to_program():
                    print("⚠️ 컷 명령 실패, 계속 진행...")
                
                # 4. 다음 사이클을 위한 랜덤 지연
                delay = self.get_random_delay()
                print(f"⏱️ 다음 사이클까지 {delay:.1f}초 대기 중...")
                
                # 지연 시간 동안 0.1초마다 running 상태 확인
                elapsed = 0
                while elapsed < delay and self.running:
                    time.sleep(0.1)
                    elapsed += 0.1
                    
            except KeyboardInterrupt:
                print("\n🛑 사용자에 의해 중단됨")
                break
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")
                time.sleep(1)  # 오류 발생 시 1초 대기
        
        print("🔄 자동 컷 루프 종료")
    
    def start(self):
        """
        자동 컷 시작
        """
        if self.running:
            print("⚠️ 이미 실행 중입니다.")
            return
        
        # 연결 테스트
        if not self.test_connection():
            print("❌ vMix에 연결할 수 없습니다. vMix가 실행 중인지 확인하세요.")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.auto_cut_loop, daemon=True)
        self.thread.start()
        print("🚀 자동 컷 시작됨")
    
    def stop(self):
        """
        자동 컷 중지
        """
        if not self.running:
            print("⚠️ 실행 중이 아닙니다.")
            return
        
        print("🛑 자동 컷 중지 중...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        
        print("🛑 자동 컷 중지됨")

def main():
    """
    메인 함수
    """
    print("="*50)
    print("🎬 vMix 자동 컷 테스트 소프트웨어")
    print("="*50)
    print("기능:")
    print("- 1-4번 인풋을 랜덤하게 프리뷰로 이동")
    print("- 2-5초 간격으로 프리뷰를 프로그램으로 컷")
    print("- Ctrl+C로 중지")
    print("="*50)
    
    # vMix 컨트롤러 생성
    controller = VMixAutoController()
    
    try:
        # 자동 컷 시작
        controller.start()
        
        if controller.running:
            print("\n💡 Ctrl+C를 눌러 중지하세요...\n")
            
            # 메인 스레드에서 대기
            while controller.running:
                time.sleep(0.5)
        
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    finally:
        controller.stop()
        print("\n👋 프로그램 종료")

if __name__ == "__main__":
    main()