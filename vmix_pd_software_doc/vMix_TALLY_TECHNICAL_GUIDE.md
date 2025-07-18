# vMix Tally System Technical Guide

## Table of Contents
1. [vMix Tally Overview](#vmix-tally-overview)
2. [Communication Methods](#communication-methods)
3. [Hybrid Implementation](#hybrid-implementation)
4. [WebSocket Relay Architecture](#websocket-relay-architecture)
5. [Real-time Synchronization](#real-time-synchronization)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)
8. [Code Examples](#code-examples)

## vMix Tally Overview

### What is Tally?
In broadcast production, a tally light system indicates which camera or video source is currently live (Program) or queued for preview (Preview). This visual feedback is crucial for camera operators and production staff.

### vMix Tally System
vMix provides multiple methods to access tally information:
- **TCP API**: Legacy method, real-time but complex
- **HTTP API**: Modern RESTful approach
- **WebSocket**: Real-time bidirectional communication
- **Activators**: Event-based triggers

### Tally States
- **Program (PGM)**: Currently live on air (RED)
- **Preview (PVW)**: Selected for next transition (GREEN)
- **Off**: Not active (NO LIGHT)

## Communication Methods

### 1. TCP API (Port 8099)

**Pros:**
- Real-time updates
- Low latency
- Persistent connection

**Cons:**
- Complex protocol
- Manual parsing required
- Connection management overhead

**Connection Example:**
```python
import socket

class VMixTCPClient:
    def __init__(self, host='127.0.0.1', port=8099):
        self.host = host
        self.port = port
        self.socket = None
        
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.socket.settimeout(5.0)
```

### 2. HTTP API (Port 8088)

**Pros:**
- Simple REST interface
- JSON/XML responses
- Stateless
- Easy to implement

**Cons:**
- Requires polling
- Higher latency
- More bandwidth usage

**API Endpoints:**
```
GET http://vmix-host:8088/api           # Full state
GET http://vmix-host:8088/api/tally     # Tally only
GET http://vmix-host:8088/api/inputs    # Input list
```

### 3. WebSocket API

**Pros:**
- Real-time bidirectional
- Event-driven
- Modern protocol
- Lower overhead than polling

**Cons:**
- Requires WebSocket library
- More complex than HTTP
- Connection state management

## Hybrid Implementation

The most robust approach combines HTTP and TCP/WebSocket for optimal reliability and performance.

### Architecture Overview
```
┌─────────────────┐     HTTP API      ┌─────────────────┐
│                 │ ←───────────────→ │                 │
│   PD Software   │                   │   vMix Server   │
│                 │ ←───────────────→ │                 │
└─────────────────┘    TCP Socket     └─────────────────┘
         │
         │ WebSocket
         ↓
┌─────────────────┐
│  Relay Server   │
│ (8765)          │
└─────────────────┘
         │
         ↓
   Camera Clients
```

### Implementation Strategy

```python
class HybridTallyManager:
    def __init__(self):
        self.http_client = VMixHTTPClient()
        self.tcp_client = VMixTCPClient()
        self.tally_state = {}
        self.inputs = {}
        
    def start(self):
        """Start hybrid monitoring"""
        # Initial state from HTTP
        self.sync_initial_state()
        
        # Real-time updates from TCP
        self.start_tcp_monitoring()
        
        # Periodic HTTP sync for reliability
        self.start_http_polling()
        
    def sync_initial_state(self):
        """Get initial state via HTTP"""
        data = self.http_client.get_state()
        self.update_inputs(data['inputs'])
        self.update_tally(data['tally'])
```

## WebSocket Relay Architecture

### Relay Server Design

The relay server acts as a bridge between the PD software and multiple camera operators, broadcasting tally updates in real-time.

```python
import asyncio
import websockets
import json

class TallyRelayServer:
    def __init__(self, port=8765):
        self.port = port
        self.clients = set()
        self.current_state = {
            'tally': {},
            'inputs': [],
            'timestamp': None
        }
        
    async def handler(self, websocket, path):
        """Handle new WebSocket connection"""
        # Register client
        self.clients.add(websocket)
        
        try:
            # Send current state to new client
            await websocket.send(json.dumps({
                'type': 'initial_state',
                'data': self.current_state
            }))
            
            # Handle incoming messages
            async for message in websocket:
                await self.process_message(websocket, message)
                
        finally:
            # Unregister client
            self.clients.remove(websocket)
            
    async def broadcast(self, message):
        """Broadcast to all connected clients"""
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
```

### Message Protocol

```json
// Tally Update
{
    "type": "tally_update",
    "data": {
        "input_number": 1,
        "name": "Camera 1",
        "program": true,
        "preview": false
    },
    "timestamp": "2025-01-14T10:30:00Z"
}

// Input List Update
{
    "type": "inputs_update",
    "data": [
        {
            "number": 1,
            "name": "Camera 1",
            "type": "Camera"
        }
    ]
}
```

## Real-time Synchronization

### State Management

```python
class TallyStateManager:
    def __init__(self):
        self.state = {}
        self.lock = threading.Lock()
        self.observers = []
        
    def update_tally(self, input_num, program=False, preview=False):
        """Update tally state thread-safely"""
        with self.lock:
            old_state = self.state.get(input_num, {})
            new_state = {
                'program': program,
                'preview': preview,
                'timestamp': time.time()
            }
            
            # Only notify if changed
            if old_state != new_state:
                self.state[input_num] = new_state
                self.notify_observers(input_num, new_state)
                
    def notify_observers(self, input_num, state):
        """Notify all observers of state change"""
        for observer in self.observers:
            observer.on_tally_change(input_num, state)
```

### Polling Strategy

```python
class SmartPoller:
    def __init__(self, base_interval=100):
        self.base_interval = base_interval  # milliseconds
        self.current_interval = base_interval
        self.failure_count = 0
        
    def get_interval(self):
        """Adaptive polling interval"""
        # Exponential backoff on failures
        if self.failure_count > 0:
            return min(
                self.base_interval * (2 ** self.failure_count),
                5000  # Max 5 seconds
            )
        return self.base_interval
        
    def on_success(self):
        """Reset on successful poll"""
        self.failure_count = 0
        
    def on_failure(self):
        """Increase interval on failure"""
        self.failure_count += 1
```

## Error Handling

### Connection Recovery

```python
class ResilientConnection:
    def __init__(self, connector, max_retries=5):
        self.connector = connector
        self.max_retries = max_retries
        self.retry_count = 0
        self.connected = False
        
    async def maintain_connection(self):
        """Maintain connection with auto-recovery"""
        while True:
            try:
                if not self.connected:
                    await self.connect()
                    
                # Monitor connection health
                await self.health_check()
                
            except Exception as e:
                self.connected = False
                self.retry_count += 1
                
                if self.retry_count > self.max_retries:
                    raise ConnectionError("Max retries exceeded")
                    
                # Exponential backoff
                wait_time = min(2 ** self.retry_count, 30)
                await asyncio.sleep(wait_time)
```

### Error Types and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Connection Refused | vMix not running | Check vMix status, verify ports |
| Timeout | Network issues | Implement retry logic |
| Parse Error | Protocol mismatch | Validate vMix version |
| State Desync | Missed updates | Periodic full sync |

## Performance Considerations

### Optimization Techniques

#### 1. Batch Updates
```python
class BatchedUpdater:
    def __init__(self, batch_size=10, timeout=50):
        self.pending = []
        self.batch_size = batch_size
        self.timeout = timeout
        self.timer = None
        
    def add_update(self, update):
        """Add update to batch"""
        self.pending.append(update)
        
        if len(self.pending) >= self.batch_size:
            self.flush()
        elif not self.timer:
            self.timer = threading.Timer(
                self.timeout / 1000.0, 
                self.flush
            )
            self.timer.start()
```

#### 2. Delta Compression
```python
def create_delta(old_state, new_state):
    """Create minimal delta update"""
    delta = {}
    
    for key, value in new_state.items():
        if key not in old_state or old_state[key] != value:
            delta[key] = value
            
    return delta
```

#### 3. Connection Pooling
```python
class ConnectionPool:
    def __init__(self, size=5):
        self.pool = queue.Queue(maxsize=size)
        self.size = size
        
        # Pre-create connections
        for _ in range(size):
            self.pool.put(self.create_connection())
            
    def acquire(self):
        """Get connection from pool"""
        return self.pool.get()
        
    def release(self, conn):
        """Return connection to pool"""
        if conn.is_healthy():
            self.pool.put(conn)
        else:
            # Replace unhealthy connection
            self.pool.put(self.create_connection())
```

## Code Examples

### Complete vMix Tally Client

```python
import requests
import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal

class VMixTallyClient(QObject):
    tally_changed = pyqtSignal(int, bool, bool)  # input, program, preview
    connection_status = pyqtSignal(bool)
    
    def __init__(self, host='127.0.0.1', port=8088):
        super().__init__()
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api"
        self.running = False
        self.tally_state = {}
        
    def start(self):
        """Start tally monitoring"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        poller = SmartPoller(base_interval=100)
        
        while self.running:
            try:
                # Get current state
                response = requests.get(
                    self.base_url, 
                    timeout=2.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._process_tally_data(data)
                    poller.on_success()
                    self.connection_status.emit(True)
                else:
                    poller.on_failure()
                    
            except Exception as e:
                poller.on_failure()
                self.connection_status.emit(False)
                
            # Adaptive sleep
            time.sleep(poller.get_interval() / 1000.0)
            
    def _process_tally_data(self, data):
        """Process tally information"""
        # Parse active inputs
        active = data.get('active', '')
        preview = data.get('preview', '')
        
        # Get input list
        inputs = data.get('vmix', {}).get('inputs', {}).get('input', [])
        
        for input_data in inputs:
            number = int(input_data['@number'])
            is_program = str(number) in active.split(',')
            is_preview = str(number) in preview.split(',')
            
            # Check for changes
            old_state = self.tally_state.get(number, {})
            new_state = {'program': is_program, 'preview': is_preview}
            
            if old_state != new_state:
                self.tally_state[number] = new_state
                self.tally_changed.emit(number, is_program, is_preview)
```

### WebSocket Client for Camera Operators

```python
import asyncio
import websockets
import json

class CameramanTallyClient:
    def __init__(self, server_url, camera_number):
        self.server_url = server_url
        self.camera_number = camera_number
        self.callbacks = {
            'program': None,
            'preview': None
        }
        
    async def connect(self):
        """Connect to relay server"""
        async with websockets.connect(self.server_url) as websocket:
            # Send identification
            await websocket.send(json.dumps({
                'type': 'identify',
                'camera': self.camera_number
            }))
            
            # Listen for updates
            async for message in websocket:
                await self.handle_message(message)
                
    async def handle_message(self, message):
        """Process tally updates"""
        data = json.loads(message)
        
        if data['type'] == 'tally_update':
            update = data['data']
            
            if update['input_number'] == self.camera_number:
                # Update local tally lights
                if self.callbacks['program']:
                    self.callbacks['program'](update['program'])
                if self.callbacks['preview']:
                    self.callbacks['preview'](update['preview'])
```

## Best Practices

1. **Always implement connection recovery** - Network issues are inevitable
2. **Use hybrid approach** for maximum reliability
3. **Implement proper state management** to prevent race conditions
4. **Monitor performance metrics** to detect issues early
5. **Test with production loads** - Tally updates can be frequent
6. **Implement graceful degradation** - System should work even if tally fails
7. **Log all state changes** for debugging production issues

## Troubleshooting

### Common Issues

1. **No Tally Updates**
   - Check vMix Web Controller is enabled
   - Verify firewall allows ports 8088/8099
   - Confirm API access is not password protected

2. **Delayed Updates**
   - Reduce polling interval
   - Check network latency
   - Consider using TCP instead of HTTP

3. **Missing Inputs**
   - Some input types may not report tally
   - Virtual inputs may behave differently
   - Check vMix version compatibility

## References

- [vMix API Documentation](https://www.vmix.com/help/index.htm)
- [WebSocket Protocol RFC](https://tools.ietf.org/html/rfc6455)
- [Tally Light Standards](https://en.wikipedia.org/wiki/Tally_light)