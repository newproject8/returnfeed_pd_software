"""
레이턴시 측정 및 관리 시스템
실시간 리턴신호를 위한 end-to-end 레이턴시 측정
"""
import time
import threading
import queue
import json
import websocket
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class LatencyMeasurement:
    """레이턴시 측정 데이터"""
    timestamp: float
    sequence_id: str
    source: str  # 'pd_software', 'mediamtx', 'browser'
    measurement_type: str  # 'send', 'receive', 'process'
    session_id: str
    camera_id: str
    metadata: Dict = None

@dataclass
class BitrateSettings:
    """비트레이트 설정"""
    session_id: str
    camera_id: str
    max_bitrate: int  # bps
    current_percentage: float  # 0.1 ~ 1.0
    adaptive_enabled: bool = True
    quality_preset: str = "balanced"  # "low_latency", "balanced", "quality"

class LatencyManager:
    """레이턴시 측정 및 관리 매니저"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8080/ws/latency"):
        self.websocket_url = websocket_url
        self.ws = None
        self.is_running = False
        self.measurements = queue.Queue()
        self.latency_history = []
        self.current_latency = 0.0
        self.bitrate_settings = {}
        self.callbacks = {
            'latency_update': [],
            'bitrate_change': [],
            'quality_change': []
        }
        
        # 레이턴시 측정 설정
        self.measurement_interval = 0.1  # 100ms마다 측정
        self.max_history_size = 100
        self.latency_threshold = 0.5  # 500ms 임계값
        
        # 스레드 관리
        self.measurement_thread = None
        self.websocket_thread = None
        
    def start(self):
        """레이턴시 측정 시작"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("레이턴시 측정 시스템 시작")
        
        # WebSocket 연결 시작
        self.websocket_thread = threading.Thread(target=self._websocket_handler)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()
        
        # 측정 스레드 시작
        self.measurement_thread = threading.Thread(target=self._measurement_loop)
        self.measurement_thread.daemon = True
        self.measurement_thread.start()
        
    def stop(self):
        """레이턴시 측정 중지"""
        self.is_running = False
        
        if self.ws:
            self.ws.close()
            
        logger.info("레이턴시 측정 시스템 중지")
        
    def _websocket_handler(self):
        """WebSocket 연결 및 메시지 처리"""
        while self.is_running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.websocket_url,
                    on_open=self._on_websocket_open,
                    on_message=self._on_websocket_message,
                    on_error=self._on_websocket_error,
                    on_close=self._on_websocket_close
                )
                self.ws.run_forever()
            except Exception as e:
                logger.error(f"WebSocket 연결 오류: {e}")
                time.sleep(5)  # 5초 후 재연결 시도
                
    def _on_websocket_open(self, ws):
        """WebSocket 연결 열림"""
        logger.info("레이턴시 측정 WebSocket 연결됨")
        
        # 레이턴시 측정 서비스 등록
        register_message = {
            'type': 'register_latency_service',
            'source': 'pd_software',
            'capabilities': {
                'timestamp_injection': True,
                'bitrate_control': True,
                'quality_monitoring': True
            }
        }
        ws.send(json.dumps(register_message))
        
    def _on_websocket_message(self, ws, message):
        """WebSocket 메시지 수신"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'latency_measurement':
                self._handle_latency_measurement(data)
            elif message_type == 'bitrate_request':
                self._handle_bitrate_request(data)
            elif message_type == 'quality_feedback':
                self._handle_quality_feedback(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"메시지 파싱 오류: {e}")
            
    def _on_websocket_error(self, ws, error):
        """WebSocket 오류"""
        logger.error(f"WebSocket 오류: {error}")
        
    def _on_websocket_close(self, ws, close_status_code, close_msg):
        """WebSocket 연결 종료"""
        logger.info("레이턴시 측정 WebSocket 연결 종료")
        
    def _measurement_loop(self):
        """레이턴시 측정 루프"""
        while self.is_running:
            try:
                # 타임스탬프 생성 및 전송
                timestamp = time.time()
                sequence_id = f"lat_{int(timestamp * 1000000)}"
                
                # PD소프트웨어에서 타임스탬프 삽입
                measurement = LatencyMeasurement(
                    timestamp=timestamp,
                    sequence_id=sequence_id,
                    source='pd_software',
                    measurement_type='send',
                    session_id='current_session',
                    camera_id='all',
                    metadata={'pgm_timestamp': timestamp}
                )
                
                self._send_measurement(measurement)
                
                # 측정 간격 대기
                time.sleep(self.measurement_interval)
                
            except Exception as e:
                logger.error(f"레이턴시 측정 루프 오류: {e}")
                time.sleep(1)
                
    def _send_measurement(self, measurement: LatencyMeasurement):
        """레이턴시 측정 데이터 전송"""
        if not self.ws:
            return
            
        message = {
            'type': 'latency_measurement',
            'measurement': {
                'timestamp': measurement.timestamp,
                'sequence_id': measurement.sequence_id,
                'source': measurement.source,
                'measurement_type': measurement.measurement_type,
                'session_id': measurement.session_id,
                'camera_id': measurement.camera_id,
                'metadata': measurement.metadata or {}
            }
        }
        
        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"레이턴시 측정 전송 오류: {e}")
            
    def _handle_latency_measurement(self, data):
        """레이턴시 측정 처리"""
        measurement = data.get('measurement', {})
        
        if measurement.get('measurement_type') == 'receive':
            # 브라우저에서 수신 완료 알림
            self._calculate_end_to_end_latency(measurement)
            
    def _calculate_end_to_end_latency(self, receive_measurement):
        """end-to-end 레이턴시 계산"""
        sequence_id = receive_measurement.get('sequence_id')
        receive_timestamp = receive_measurement.get('timestamp')
        
        # 해당 시퀀스의 송신 시간 찾기
        send_timestamp = receive_measurement.get('metadata', {}).get('pgm_timestamp')
        
        if send_timestamp and receive_timestamp:
            latency = receive_timestamp - send_timestamp
            self.current_latency = latency
            
            # 히스토리 업데이트
            self.latency_history.append({
                'timestamp': receive_timestamp,
                'latency': latency,
                'sequence_id': sequence_id
            })
            
            # 히스토리 크기 제한
            if len(self.latency_history) > self.max_history_size:
                self.latency_history.pop(0)
                
            # 레이턴시 업데이트 콜백 호출
            self._notify_callbacks('latency_update', {
                'latency': latency,
                'average_latency': self.get_average_latency(),
                'jitter': self.get_jitter()
            })
            
            logger.debug(f"End-to-end 레이턴시: {latency:.3f}초")
            
    def _handle_bitrate_request(self, data):
        """비트레이트 요청 처리"""
        session_id = data.get('session_id')
        camera_id = data.get('camera_id')
        percentage = data.get('percentage', 1.0)
        
        # 비트레이트 설정 업데이트
        settings = self.bitrate_settings.get(f"{session_id}_{camera_id}")
        if settings:
            settings.current_percentage = max(0.1, min(1.0, percentage))
            
            # MediaMTX 서버에 비트레이트 변경 요청
            self._apply_bitrate_settings(settings)
            
            # 콜백 호출
            self._notify_callbacks('bitrate_change', {
                'session_id': session_id,
                'camera_id': camera_id,
                'percentage': percentage,
                'effective_bitrate': int(settings.max_bitrate * settings.current_percentage)
            })
            
    def _handle_quality_feedback(self, data):
        """품질 피드백 처리"""
        session_id = data.get('session_id')
        camera_id = data.get('camera_id')
        quality_metrics = data.get('metrics', {})
        
        # 품질 메트릭 분석
        packet_loss = quality_metrics.get('packet_loss', 0)
        jitter = quality_metrics.get('jitter', 0)
        
        # 자동 품질 조정
        if packet_loss > 0.02:  # 2% 이상 패킷 손실
            self._auto_adjust_quality(session_id, camera_id, 'decrease')
        elif packet_loss < 0.005 and jitter < 0.05:  # 품질 여유 있음
            self._auto_adjust_quality(session_id, camera_id, 'increase')
            
    def _apply_bitrate_settings(self, settings: BitrateSettings):
        """비트레이트 설정 적용"""
        if not self.ws:
            return
            
        message = {
            'type': 'apply_bitrate_settings',
            'settings': {
                'session_id': settings.session_id,
                'camera_id': settings.camera_id,
                'max_bitrate': settings.max_bitrate,
                'current_percentage': settings.current_percentage,
                'adaptive_enabled': settings.adaptive_enabled,
                'quality_preset': settings.quality_preset
            }
        }
        
        try:
            self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"비트레이트 설정 적용 오류: {e}")
            
    def _auto_adjust_quality(self, session_id: str, camera_id: str, direction: str):
        """자동 품질 조정"""
        key = f"{session_id}_{camera_id}"
        settings = self.bitrate_settings.get(key)
        
        if not settings:
            return
            
        if direction == 'decrease':
            new_percentage = max(0.1, settings.current_percentage - 0.1)
        else:  # increase
            new_percentage = min(1.0, settings.current_percentage + 0.1)
            
        settings.current_percentage = new_percentage
        self._apply_bitrate_settings(settings)
        
        logger.info(f"자동 품질 조정: {camera_id} -> {new_percentage:.1%}")
        
    def set_bitrate_settings(self, session_id: str, camera_id: str, 
                           max_bitrate: int, percentage: float = 1.0):
        """비트레이트 설정"""
        key = f"{session_id}_{camera_id}"
        
        settings = BitrateSettings(
            session_id=session_id,
            camera_id=camera_id,
            max_bitrate=max_bitrate,
            current_percentage=max(0.1, min(1.0, percentage))
        )
        
        self.bitrate_settings[key] = settings
        self._apply_bitrate_settings(settings)
        
        logger.info(f"비트레이트 설정: {camera_id} -> {max_bitrate}bps @ {percentage:.1%}")
        
    def get_current_latency(self) -> float:
        """현재 레이턴시 반환"""
        return self.current_latency
        
    def get_average_latency(self) -> float:
        """평균 레이턴시 계산"""
        if not self.latency_history:
            return 0.0
            
        latencies = [item['latency'] for item in self.latency_history]
        return np.mean(latencies)
        
    def get_jitter(self) -> float:
        """지터 계산"""
        if len(self.latency_history) < 2:
            return 0.0
            
        latencies = [item['latency'] for item in self.latency_history]
        return np.std(latencies)
        
    def get_latency_stats(self) -> Dict:
        """레이턴시 통계 반환"""
        if not self.latency_history:
            return {
                'current': 0.0,
                'average': 0.0,
                'min': 0.0,
                'max': 0.0,
                'jitter': 0.0,
                'samples': 0
            }
            
        latencies = [item['latency'] for item in self.latency_history]
        
        return {
            'current': self.current_latency,
            'average': np.mean(latencies),
            'min': np.min(latencies),
            'max': np.max(latencies),
            'jitter': np.std(latencies),
            'samples': len(latencies)
        }
        
    def add_callback(self, event_type: str, callback: Callable):
        """콜백 추가"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            
    def _notify_callbacks(self, event_type: str, data: Dict):
        """콜백 알림"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"콜백 실행 오류: {e}")


# 사용 예제
if __name__ == "__main__":
    # 레이턴시 매니저 생성
    latency_manager = LatencyManager()
    
    # 레이턴시 업데이트 콜백
    def on_latency_update(data):
        print(f"레이턴시 업데이트: {data['latency']:.3f}초 (평균: {data['average_latency']:.3f}초)")
        
    def on_bitrate_change(data):
        print(f"비트레이트 변경: {data['camera_id']} -> {data['effective_bitrate']}bps")
        
    # 콜백 등록
    latency_manager.add_callback('latency_update', on_latency_update)
    latency_manager.add_callback('bitrate_change', on_bitrate_change)
    
    # 시작
    latency_manager.start()
    
    # 비트레이트 설정 예제
    latency_manager.set_bitrate_settings('session_1', 'camera_1', 5000000, 0.8)  # 5Mbps @ 80%
    
    try:
        # 메인 루프
        while True:
            stats = latency_manager.get_latency_stats()
            print(f"현재 레이턴시: {stats['current']:.3f}초")
            time.sleep(1)
            
    except KeyboardInterrupt:
        latency_manager.stop()
        print("레이턴시 측정 시스템 종료")