NDI-Python과 PyQt GUI 조합에서 발생하는 GUI 끊김 문제 분석

핵심 문제: GIL (Global Interpreter Lock) 관련 이슈

문제 설명

•
GitHub 이슈: Ndi-python leaves the GIL locked during all library calls #38

•
보고자: JC3 (2024년 9월 28일)

문제의 핵심

NDI-Python 라이브러리가 모든 라이브러리 호출 중에 GIL을 잠금 상태로 유지하여, NDI 라이브러리 호출이 실행되는 동안 모든 다른 Python 스레드가 중단됩니다.

기술적 세부사항

1.
GIL 미해제: NDI 라이브러리 호출 중 GIL이 해제되지 않음

2.
스레드 블로킹: find_wait_for_sources 같은 NDI 함수 호출 시 메인 스레드가 실행되지 않음

3.
GUI 응답성 문제: PyQt GUI가 NDI 작업 중 완전히 멈춤

예제 코드 분석

Python


import threading
import time
import NDIlib as ndi

def p(message: str) -> None:
    print(f"[{time.time():.3f}] {message}")

def threadproc() -> None:
    finder = ndi.find_create_v2()
    while True:
        p("find_wait_for_sources enter")
        ndi.find_wait_for_sources(finder, 3000)  # 3초 대기
        p("find_wait_for_sources leave")

ndi.initialize()
thread = threading.Thread(target=threadproc)
thread.start()
while True:
    p("ding")
    time.sleep(0.1)  # 0.1초마다 "ding" 출력 예상


실제 출력 결과

Plain Text


[1727534088.330] find_wait_for_sources enter
[1727534091.330] ding
[1727534091.330] find_wait_for_sources leave
[1727534091.330] find_wait_for_sources enter
[1727534094.331] ding
[1727534094.331] find_wait_for_sources leave


예상: 0.1초마다 "ding" 출력
실제: NDI 함수 실행 중 메인 스레드가 완전히 멈춤

결과 및 영향

•
스레드 컨텍스트에서 NDI-Python 사용 불가능

•
중간 복잡도 이상의 애플리케이션에서 성능 문제 발생

•
특히 성능이 중요한 애플리케이션에서 치명적

관련 이슈들

1. 스레딩 관련 이슈

•
GitHub 이슈: thread in python #36

•
보고자: changxiyan-ai (2024년 4월 22일)

원인 분석

1. 핵심 원인: GIL (Global Interpreter Lock) 문제

•
NDI-Python 라이브러리의 설계 결함: 모든 NDI 라이브러리 호출 중 GIL을 해제하지 않음

•
결과: NDI 함수 실행 중 모든 Python 스레드가 블로킹됨

•
PyQt GUI에 미치는 영향: GUI 이벤트 루프가 멈춰서 사용자 인터페이스가 응답하지 않음

2. 기술적 세부 원인

1.
C 확장 모듈의 GIL 관리 부재

•
NDI-Python이 C 라이브러리 호출 시 Py_BEGIN_ALLOW_THREADS/Py_END_ALLOW_THREADS 사용하지 않음

•
장시간 실행되는 NDI 함수들이 GIL을 계속 보유



2.
스레딩 아키텍처 문제

•
NDI 작업을 별도 스레드로 분리해도 GIL로 인해 효과 없음

•
PyQt의 QThread 사용해도 근본적 해결 불가



3.
실시간 처리 요구사항과의 충돌

•
NDI는 실시간 비디오/오디오 처리 요구

•
Python GIL은 이러한 실시간 요구사항과 근본적으로 충돌



해결법

1. 즉시 적용 가능한 해결책

A. cyndilib 라이브러리로 교체 (권장)

Bash


pip uninstall ndi-python
pip install cyndilib


장점:

•
Cython으로 작성되어 성능 최적화

•
GIL 관련 문제 해결

•
더 나은 스레딩 지원

•
활발한 개발 및 유지보수

예제 코드:

Python


import cyndilib as ndi
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow

class NDIWorker(QThread):
    frame_received = pyqtSignal(object)
    
    def run(self):
        # cyndilib는 GIL 해제를 적절히 처리
        finder = ndi.Finder()
        receiver = ndi.Receiver()
        
        while self.isRunning():
            frame = receiver.capture_video()
            if frame:
                self.frame_received.emit(frame)


B. 멀티프로세싱 아키텍처 (대안)

Python


import multiprocessing as mp
from PyQt6.QtCore import QTimer
import NDIlib as ndi

class NDIProcess(mp.Process):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        
    def run(self):
        # 별도 프로세스에서 NDI 처리
        ndi.initialize()
        finder = ndi.find_create_v2()
        
        while True:
            # NDI 데이터 처리
            sources = ndi.find_get_current_sources(finder)
            self.queue.put(sources)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.queue = mp.Queue()
        self.ndi_process = NDIProcess(self.queue)
        self.ndi_process.start()
        
        # 타이머로 큐 확인
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_queue)
        self.timer.start(16)  # ~60fps
        
    def check_queue(self):
        try:
            data = self.queue.get_nowait()
            # GUI 업데이트
        except:
            pass


2. 코드 구조 개선 방안

A. 비동기 패턴 적용

Python


from PyQt6.QtCore import QThread, QMutex, QWaitCondition
import queue
import threading

class NDIManager:
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=10)
        self.worker_thread = None
        
    def start_capture(self):
        self.worker_thread = threading.Thread(target=self._capture_worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        
    def _capture_worker(self):
        # NDI 캡처 작업 (별도 프로세스에서 실행)
        pass
        
    def get_latest_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None


B. 프레임 버퍼링 전략

Python


class FrameBuffer:
    def __init__(self, max_size=30):  # 0.5초 버퍼 (60fps 기준)
        self.buffer = collections.deque(maxlen=max_size)
        self.lock = threading.Lock()
        
    def add_frame(self, frame):
        with self.lock:
            self.buffer.append(frame)
            
    def get_frame(self):
        with self.lock:
            return self.buffer.popleft() if self.buffer else None


3. 성능 최적화 방안

A. GUI 업데이트 최적화

Python


class VideoWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_frame)
        self.update_timer.start(16)  # 60fps
        
    def update_frame(self):
        # 프레임 업데이트 로직
        frame = self.ndi_manager.get_latest_frame()
        if frame:
            # QPixmap 변환 및 표시
            pass


B. 메모리 관리 최적화

Python


class OptimizedNDIReceiver:
    def __init__(self):
        self.frame_pool = []  # 프레임 객체 재사용
        self.max_pool_size = 10
        
    def get_frame_object(self):
        if self.frame_pool:
            return self.frame_pool.pop()
        return self.create_new_frame()
        
    def return_frame_object(self, frame):
        if len(self.frame_pool) < self.max_pool_size:
            self.frame_pool.append(frame)


추가 고려사항

1. 네트워크 최적화

•
NDI 스트림의 품질 설정 조정

•
네트워크 버퍼 크기 최적화

•
대역폭 제한 설정

2. 시스템 리소스 관리

•
CPU 코어 할당 최적화

•
메모리 사용량 모니터링

•
GPU 가속 활용 (가능한 경우)

3. 에러 처리 및 복구

•
연결 끊김 감지 및 자동 재연결

•
프레임 드롭 처리

•
예외 상황 로깅

요약 및 권장사항

핵심 문제

NDI-Python 라이브러리의 GIL (Global Interpreter Lock) 미해제 문제로 인해 NDI 작업 중 PyQt GUI가 완전히 멈추는 현상이 발생합니다.

최우선 권장 해결책

1.
cyndilib로 라이브러리 교체 (가장 효과적)

2.
멀티프로세싱 아키텍처 적용 (대안)

3.
비동기 프레임 처리 패턴 구현

즉시 적용 가능한 조치

Bash


# 1. 기존 라이브러리 제거
pip uninstall ndi-python

# 2. cyndilib 설치
pip install cyndilib

# 3. 코드에서 import 변경
# 기존: import NDIlib as ndi
# 변경: import cyndilib as ndi


장기적 개선 방향

•
프레임 버퍼링 시스템 구축

•
네트워크 최적화

•
에러 처리 및 복구 메커니즘 강화

•
성능 모니터링 시스템 도입

