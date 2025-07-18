# NDI 프록시 모드 성능 프로파일링 전략

## 즉시 적용 가능한 측정 코드

### 1. recv_capture_v2 타이밍 분석
```python
# ndi_receiver.py에 추가할 프로파일링 코드
import time
from collections import deque
from dataclasses import dataclass
from typing import List

@dataclass
class FrameTimingStats:
    recv_start: float
    recv_end: float
    recv_duration: float
    frame_received: bool
    frame_size: int = 0

class TimingProfiler:
    def __init__(self, window_size: int = 1000):
        self.timings: deque[FrameTimingStats] = deque(maxlen=window_size)
        self.proxy_timings: deque[FrameTimingStats] = deque(maxlen=window_size)
        self.normal_timings: deque[FrameTimingStats] = deque(maxlen=window_size)
    
    def add_timing(self, stats: FrameTimingStats, is_proxy: bool):
        self.timings.append(stats)
        if is_proxy:
            self.proxy_timings.append(stats)
        else:
            self.normal_timings.append(stats)
    
    def analyze(self) -> dict:
        if not self.timings:
            return {}
        
        # recv_capture_v2 호출 시간 분석
        recv_times = [t.recv_duration for t in self.timings]
        hit_times = [t.recv_duration for t in self.timings if t.frame_received]
        miss_times = [t.recv_duration for t in self.timings if not t.frame_received]
        
        return {
            "avg_recv_time": sum(recv_times) / len(recv_times),
            "avg_hit_time": sum(hit_times) / len(hit_times) if hit_times else 0,
            "avg_miss_time": sum(miss_times) / len(miss_times) if miss_times else 0,
            "hit_rate": len(hit_times) / len(recv_times),
            "recv_time_variance": self._variance(recv_times),
        }
    
    def _variance(self, data: List[float]) -> float:
        if not data:
            return 0
        mean = sum(data) / len(data)
        return sum((x - mean) ** 2 for x in data) / len(data)

# 수신 루프에서 사용:
profiler = TimingProfiler()

# recv_capture_v2 전후로 측정
recv_start = time.perf_counter()
frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2(self.receiver, timeout_ms)
recv_end = time.perf_counter()

stats = FrameTimingStats(
    recv_start=recv_start,
    recv_end=recv_end,
    recv_duration=(recv_end - recv_start) * 1000,  # ms로 변환
    frame_received=(frame_type == ndi.FRAME_TYPE_VIDEO),
    frame_size=v_frame.data.nbytes if v_frame else 0
)
profiler.add_timing(stats, is_proxy=(self.bandwidth_mode == "lowest"))

# 주기적으로 분석 결과 출력
if len(profiler.timings) >= 100:
    analysis = profiler.analyze()
    self.logger.info(f"Profiling results: {analysis}")
```

### 2. 프레임 간격 히스토그램
```python
import numpy as np

class FrameIntervalAnalyzer:
    def __init__(self):
        self.last_frame_time = 0
        self.intervals = []
        self.proxy_intervals = []
        self.normal_intervals = []
    
    def record_frame(self, is_proxy: bool):
        current_time = time.perf_counter()
        if self.last_frame_time > 0:
            interval = (current_time - self.last_frame_time) * 1000  # ms
            self.intervals.append(interval)
            if is_proxy:
                self.proxy_intervals.append(interval)
            else:
                self.normal_intervals.append(interval)
        self.last_frame_time = current_time
    
    def get_histogram(self, intervals: List[float], bins: int = 20):
        if not intervals:
            return None
        
        hist, edges = np.histogram(intervals, bins=bins)
        return {
            "histogram": hist.tolist(),
            "bin_edges": edges.tolist(),
            "mean": np.mean(intervals),
            "std": np.std(intervals),
            "percentiles": {
                "p50": np.percentile(intervals, 50),
                "p90": np.percentile(intervals, 90),
                "p99": np.percentile(intervals, 99),
            }
        }
```

### 3. 시스템 리소스 모니터링
```python
import psutil
import threading

class SystemMonitor:
    def __init__(self):
        self.cpu_percent = []
        self.memory_mb = []
        self.running = False
        self.thread = None
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.start()
    
    def _monitor_loop(self):
        process = psutil.Process()
        while self.running:
            self.cpu_percent.append(process.cpu_percent(interval=0.1))
            self.memory_mb.append(process.memory_info().rss / 1024 / 1024)
            time.sleep(0.1)
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
    
    def get_stats(self):
        return {
            "cpu_avg": sum(self.cpu_percent) / len(self.cpu_percent) if self.cpu_percent else 0,
            "cpu_max": max(self.cpu_percent) if self.cpu_percent else 0,
            "memory_avg_mb": sum(self.memory_mb) / len(self.memory_mb) if self.memory_mb else 0,
        }
```

## 네트워크 레벨 분석

### 1. 패킷 캡처 스크립트
```bash
#!/bin/bash
# capture_ndi_traffic.sh

# 프록시 모드 캡처
echo "Starting proxy mode capture..."
sudo tcpdump -i any -w proxy_mode.pcap 'port 5960 or port 5961' &
TCPDUMP_PID=$!

# 10초 대기
sleep 10

# 프록시 모드 중지
kill $TCPDUMP_PID

# 일반 모드 캡처
echo "Starting normal mode capture..."
sudo tcpdump -i any -w normal_mode.pcap 'port 5960 or port 5961' &
TCPDUMP_PID=$!

# 10초 대기
sleep 10

# 캡처 중지
kill $TCPDUMP_PID

# 분석
echo "Analyzing packet patterns..."
tshark -r proxy_mode.pcap -T fields -e frame.time_relative -e frame.len > proxy_packets.txt
tshark -r normal_mode.pcap -T fields -e frame.time_relative -e frame.len > normal_packets.txt
```

### 2. 패킷 간격 분석 Python 스크립트
```python
def analyze_packet_timing(filename):
    times = []
    sizes = []
    
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                times.append(float(parts[0]))
                sizes.append(int(parts[1]))
    
    if len(times) < 2:
        return None
    
    intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
    
    return {
        "packet_count": len(times),
        "avg_interval_ms": np.mean(intervals) * 1000,
        "interval_std_ms": np.std(intervals) * 1000,
        "avg_packet_size": np.mean(sizes),
        "total_bytes": sum(sizes),
        "duration_seconds": times[-1] - times[0],
        "packets_per_second": len(times) / (times[-1] - times[0]) if times[-1] > times[0] else 0,
    }

# 사용 예
proxy_stats = analyze_packet_timing("proxy_packets.txt")
normal_stats = analyze_packet_timing("normal_packets.txt")
print(f"Proxy mode: {proxy_stats}")
print(f"Normal mode: {normal_stats}")
```

## CPU 프로파일링

### 1. Python cProfile 통합
```python
import cProfile
import pstats
from io import StringIO

class CPUProfiler:
    def __init__(self):
        self.profiler = cProfile.Profile()
        self.is_profiling = False
    
    def start(self):
        if not self.is_profiling:
            self.profiler.enable()
            self.is_profiling = True
    
    def stop_and_report(self, top_n=20):
        if self.is_profiling:
            self.profiler.disable()
            self.is_profiling = False
            
            s = StringIO()
            ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(top_n)
            
            return s.getvalue()
        return ""

# 사용 예
cpu_profiler = CPUProfiler()

# 프로파일링 시작 (프록시 모드에서)
if self.bandwidth_mode == "lowest":
    cpu_profiler.start()

# ... 일정 시간 후 ...
if self.frame_count % 1000 == 0:  # 1000 프레임마다
    report = cpu_profiler.stop_and_report()
    self.logger.info(f"CPU Profile Report:\n{report}")
```

### 2. 고정밀 타이머 래퍼
```python
class HighResTimer:
    def __init__(self, name: str):
        self.name = name
        self.times = []
    
    def __enter__(self):
        self.start = time.perf_counter_ns()
        return self
    
    def __exit__(self, *args):
        self.end = time.perf_counter_ns()
        self.duration_us = (self.end - self.start) / 1000
        self.times.append(self.duration_us)
    
    def report(self):
        if not self.times:
            return ""
        
        return (f"{self.name}: "
                f"avg={np.mean(self.times):.1f}μs, "
                f"max={np.max(self.times):.1f}μs, "
                f"min={np.min(self.times):.1f}μs")

# 사용 예
qimage_timer = HighResTimer("QImage Creation")

with qimage_timer:
    image = self._create_qimage_fast(frame_data_copy)

# 주기적으로 리포트
if self.frame_count % 100 == 0:
    self.logger.info(qimage_timer.report())
```

## 실시간 모니터링 대시보드

### 1. 간단한 텍스트 기반 대시보드
```python
import os
import sys

class PerformanceDashboard:
    def __init__(self):
        self.data = {
            "fps": 0,
            "recv_time_avg": 0,
            "frame_interval_avg": 0,
            "cpu_percent": 0,
            "mode": "unknown",
        }
    
    def update(self, **kwargs):
        self.data.update(kwargs)
    
    def display(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("=" * 50)
        print(f"NDI Performance Monitor - Mode: {self.data['mode']}")
        print("=" * 50)
        print(f"FPS: {self.data['fps']:.1f}")
        print(f"Avg recv_capture_v2 time: {self.data['recv_time_avg']:.2f} ms")
        print(f"Avg frame interval: {self.data['frame_interval_avg']:.2f} ms")
        print(f"CPU usage: {self.data['cpu_percent']:.1f}%")
        print("=" * 50)
        
        # 시각적 FPS 바
        fps_bar_length = int(self.data['fps'] / 60 * 40)
        fps_bar = "█" * fps_bar_length + "░" * (40 - fps_bar_length)
        print(f"FPS: [{fps_bar}] {self.data['fps']:.0f}/60")
```

## 권장 테스트 시나리오

### 1. A/B 비교 테스트
1. 동일한 NDI 소스에서 두 개의 수신기 실행
2. 하나는 프록시 모드, 하나는 일반 모드
3. 동시에 프로파일링 데이터 수집
4. 네트워크 트래픽 패턴 비교

### 2. 단계별 타임아웃 테스트
```python
timeout_values = [10, 15, 20, 25, 30, 40, 50]
results = {}

for timeout in timeout_values:
    # timeout_ms 변경하여 테스트
    # FPS 및 CPU 사용률 측정
    results[timeout] = {
        "fps": measured_fps,
        "cpu": measured_cpu,
    }
```

### 3. 부하 테스트
- 백그라운드 CPU 부하 생성
- 네트워크 대역폭 제한
- 메모리 압박 상황 시뮬레이션

이러한 프로파일링 도구와 전략을 통해 프록시 모드 40fps 제한의 정확한 원인을 파악할 수 있을 것입니다.