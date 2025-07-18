# PD 통합 소프트웨어 기술 명세서

## 📋 시스템 아키텍처

### 전체 구조도
```
┌─────────────────────────────────────────────────────────┐
│                    PD 통합 소프트웨어                     │
├─────────────────────────────────────────────────────────┤
│  메인 애플리케이션 (main_v2.py)                         │
├─────────────────┬─────────────────┬─────────────────────┤
│   NDI Manager   │  vMix Manager   │  WebSocket Client   │
│                 │                 │                     │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────┐ │
│ │ NDI Sources │ │ │ TCP Listener│ │ │ Real-time Relay │ │
│ │ Discovery   │ │ │ (Port 8099) │ │ │ (WebSocket)     │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────────┘ │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────┐ │
│ │ Video Frame │ │ │ HTTP API    │ │ │ Message Queue   │ │
│ │ Receiver    │ │ │ (Port 8088) │ │ │ (Async)         │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────────┘ │
└─────────────────┴─────────────────┴─────────────────────┘
                            │
├─────────────────────────────────────────────────────────┤
│                    GUI Layer (PyQt6)                   │
├─────────────────┬─────────────────┬─────────────────────┤
│   NDI Widget    │  Tally Widget   │    SRT Widget       │
│                 │                 │                     │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────┐ │
│ │ Video       │ │ │ PGM/PVW     │ │ │ Stream Status   │ │
│ │ Preview     │ │ │ Indicators  │ │ │ Control         │ │
│ └─────────────┘ │ └─────────────┘ │ └─────────────────┘ │
└─────────────────┴─────────────────┴─────────────────────┘
```

## 🔧 핵심 컴포넌트

### 1. NDI Manager
**파일**: `pd_app/core/ndi_manager.py`

**기능**:
- NDI 소스 자동 검색
- 실시간 비디오 프레임 수신
- 90도 회전 보정 (vMix 출력용)
- 프레임 스키핑 (3:1 비율)

**주요 클래스**:
```python
class NDIManager(QObject):
    # 시그널
    sources_updated = pyqtSignal(list)
    frame_received = pyqtSignal(object)
    connection_status_changed = pyqtSignal(str, str)
    
    # 주요 메서드
    def initialize()              # NDI 라이브러리 초기화
    def start_source_discovery()  # 소스 검색 시작
    def start_preview(source)     # 프리뷰 시작
    def stop_preview()            # 프리뷰 중지
```

**성능 최적화**:
- 스레드 우선순위 설정 (THREAD_PRIORITY_ABOVE_NORMAL)
- 프레임 타임아웃 관리 (100ms)
- 메모리 효율적인 프레임 처리

### 2. vMix Manager
**파일**: `pd_app/core/vmix_manager.py`

**기능**:
- TCP 실시간 Tally 감지 (포트 8099)
- HTTP API 상태 조회 (포트 8088)
- WebSocket 실시간 브로드캐스트
- 제로 레이턴시 구현

**주요 클래스**:
```python
class VMixManager(QObject):
    # 시그널
    tally_updated = pyqtSignal(int, int, dict, dict)
    connection_status_changed = pyqtSignal(str, str)
    input_list_updated = pyqtSignal(dict)
    websocket_status_changed = pyqtSignal(str, str)
    
    # 주요 메서드
    def connect_to_vmix()         # vMix 연결
    def fetch_and_broadcast_vmix_state()  # 상태 조회 및 브로드캐스트
```

**실시간 처리 플로우**:
```
TCP Event → TALLY OK 감지 → HTTP API 조회 → 상태 변경 감지 → 
WebSocket 브로드캐스트 → GUI 업데이트
```

**성능 지표**:
- TCP 타임아웃: 100ms
- HTTP 타임아웃: 500ms
- 레이턴시: < 50ms

### 3. WebSocket Client
**파일**: `pd_app/network/websocket_client.py`

**기능**:
- 실시간 서버 통신
- 자동 재연결
- 메시지 큐 관리
- 핑/퐁 하트비트

**주요 기능**:
```python
class WebSocketClient(QObject):
    # 시그널
    connection_status_changed = pyqtSignal(str)
    message_received = pyqtSignal(dict)
    
    # 주요 메서드
    def start()                   # 연결 시작
    def send_message(message)     # 메시지 전송
    def stop()                    # 연결 종료
```

## 📊 데이터 플로우

### 1. NDI 비디오 스트림
```
NDI Source → NDI Receiver → Frame Decode → 
90° Rotation → Frame Skip (3:1) → Qt Widget Display
```

### 2. vMix Tally 데이터
```
vMix → TCP TALLY OK → HTTP API Query → 
JSON Parse → State Compare → Signal Emit → 
WebSocket Broadcast → GUI Update
```

### 3. WebSocket 통신
```
Local State → Message Queue → WebSocket Send → 
Server Relay → Remote Clients → Real-time Update
```

## 🎛️ 설정 및 구성

### 환경 변수
```bash
# NDI SDK 경로
NDI_SDK_DLL_PATH="C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

# vMix 연결 설정
VMIX_IP="127.0.0.1"
VMIX_HTTP_PORT=8088
VMIX_TCP_PORT=8099

# WebSocket 서버
WEBSOCKET_URL="ws://returnfeed.net:8765"
```

### 성능 튜닝 매개변수
```python
# NDI 설정
NDI_FRAME_TIMEOUT = 100  # ms
NDI_FRAME_SKIP_RATIO = 3  # 3:1

# vMix 설정
VMIX_TCP_TIMEOUT = 0.1    # 100ms
VMIX_HTTP_TIMEOUT = 0.5   # 500ms
VMIX_RECONNECT_DELAY = 5  # 5초

# WebSocket 설정
WS_PING_INTERVAL = 20     # 20초
WS_PING_TIMEOUT = 10      # 10초
WS_RECONNECT_DELAY = 5    # 5초
```

## 🔒 오류 처리 및 복구

### 1. NDI 오류 처리
```python
# NDI 라이브러리 없음
if not NDI_AVAILABLE:
    logger.warning("NDI 시뮬레이터 모드 활성화")
    
# NDI 소스 없음
if not sources:
    self.connection_status_changed.emit("NDI 소스 없음", "orange")
    
# 프레임 수신 오류
except Exception as e:
    logger.error(f"프레임 수신 오류: {e}")
    self.restart_receiver()
```

### 2. vMix 연결 오류 처리
```python
# TCP 연결 실패
except ConnectionRefusedError:
    logger.warning("vMix TCP 연결 거부됨")
    self.schedule_reconnect()
    
# HTTP API 오류
except requests.RequestException as e:
    logger.error(f"vMix API 요청 실패: {e}")
    self.connection_status_changed.emit("API 요청 실패", "orange")
```

### 3. WebSocket 오류 처리
```python
# 연결 끊김
except ConnectionClosed:
    logger.info("WebSocket 연결 종료")
    self.schedule_reconnect()
    
# 메시지 오류
except json.JSONDecodeError:
    logger.error("잘못된 JSON 메시지")
```

## 📈 성능 모니터링

### 메트릭 수집
```python
# 프레임율 측정
frame_count = 0
start_time = time.time()
fps = frame_count / (time.time() - start_time)

# 레이턴시 측정
tally_latency = current_time - last_tally_time

# 메모리 사용량
memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
```

### 로깅 시스템
```python
# 로그 레벨
DEBUG: 상세한 디버깅 정보
INFO:  일반적인 상태 정보
WARNING: 경고 (기능은 동작)
ERROR: 오류 (일부 기능 제한)
CRITICAL: 치명적 오류 (프로그램 종료)

# 로그 파일
logs/pd_app_YYYYMMDD_HHMMSS.log
```

## 🧪 테스트 전략

### 1. 단위 테스트
- 각 Manager 클래스별 독립 테스트
- 모의 객체(Mock) 사용한 격리 테스트
- 오류 상황 시뮬레이션

### 2. 통합 테스트
- 전체 시스템 연동 테스트
- 실제 vMix/NDI 환경에서 테스트
- 성능 및 안정성 테스트

### 3. 사용자 시나리오 테스트
- 일반적인 사용 패턴 검증
- 오류 복구 시나리오 검증
- 장시간 구동 안정성 테스트

## 🔧 개발 도구 및 설정

### VSCode 설정
```json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.analysis.typeCheckingMode": "basic",
    "python.linting.pylintEnabled": false,
    "python.languageServer": "Pylance"
}
```

### 타입 힌트
```python
from typing import Optional, Dict, List, Callable, Any

def process_frame(frame: Optional[np.ndarray]) -> bool:
    ...

def update_tally(pgm: int, pvw: int, inputs: Dict[int, str]) -> None:
    ...
```

### 코드 품질 도구
- **Pylance**: 정적 타입 검사
- **Black**: 코드 포맷팅 (옵션)
- **isort**: import 정렬 (옵션)

---
**문서 버전**: v2.1  
**최종 업데이트**: 2025년 7월 10일  
**다음 검토 예정**: 필요시