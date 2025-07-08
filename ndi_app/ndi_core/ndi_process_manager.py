import multiprocessing as mp
import queue
import time
import numpy as np
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import NDIlib as ndi
import os
import sys

class NDIProcessManager(QObject):
    """멀티프로세싱을 사용하여 NDI 작업을 별도 프로세스에서 처리하는 매니저"""
    frame_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    info_message = pyqtSignal(str)
    sources_changed = pyqtSignal(list)
    fps_updated = pyqtSignal(float)  # FPS 업데이트 시그널 추가
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_queue = None
        self.command_queue = None
        self.status_queue = None
        self.ndi_process = None
        self.is_running = False
        
        # GUI 업데이트를 위한 타이머
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._check_queues)
        
        # 프레임 버퍼링을 위한 설정
        self.max_frame_buffer = 5  # 최대 5프레임 버퍼
        
        # 현재 소스 정보
        self._current_source = None
        
        # 큐 확인 타이머
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self._check_queues)
        self.queue_timer.start(17)  # 59.94fps 정밀 타이밍 (16.683ms)
        
    def start_ndi_process(self):
        """NDI 프로세스 시작"""
        if self.is_running:
            self.info_message.emit("NDI 프로세스가 이미 실행 중입니다.")
            return
            
        try:
            # 큐 생성 (프로세스 간 통신용)
            self.frame_queue = mp.Queue(maxsize=self.max_frame_buffer)
            self.command_queue = mp.Queue()
            self.status_queue = mp.Queue()
            
            # NDI 프로세스 시작
            self.ndi_process = NDIWorkerProcess(
                self.frame_queue, 
                self.command_queue, 
                self.status_queue
            )
            self.ndi_process.start()
            
            self.is_running = True
            self.update_timer.start(17)  # 59.94fps 정밀 타이밍 (16.683ms)
            
            self.info_message.emit("NDI 프로세스가 시작되었습니다.")
            
        except Exception as e:
            self.error_occurred.emit(f"NDI 프로세스 시작 실패: {str(e)}")
            
    def stop_ndi_process(self):
        """NDI 프로세스 중지"""
        if not self.is_running:
            return
            
        try:
            # 중지 명령 전송
            if self.command_queue:
                self.command_queue.put({'command': 'stop'})
                
            # 프로세스 종료 대기
            if self.ndi_process and self.ndi_process.is_alive():
                self.ndi_process.join(timeout=3.0)
                if self.ndi_process.is_alive():
                    self.ndi_process.terminate()
                    self.ndi_process.join()
                    
            self.update_timer.stop()
            self.is_running = False
            
            self.connection_status_changed.emit(False)
            self.info_message.emit("NDI 프로세스가 중지되었습니다.")
            
        except Exception as e:
            self.error_occurred.emit(f"NDI 프로세스 중지 실패: {str(e)}")
            
    def set_source(self, source_name, source_url):
        """NDI 소스 설정"""
        if not self.is_running:
            self.error_occurred.emit("NDI 프로세스가 실행되지 않았습니다.")
            return
            
        command = {
            'command': 'set_source',
            'source_name': source_name,
            'source_url': source_url
        }
        
        try:
            self.command_queue.put(command)
            self.info_message.emit(f"소스 설정: {source_name}")
        except Exception as e:
            self.error_occurred.emit(f"소스 설정 실패: {str(e)}")
            
    def set_bandwidth_mode(self, bandwidth_mode):
        """대역폭 모드 설정"""
        if not self.is_running:
            return
            
        command = {
            'command': 'set_bandwidth',
            'bandwidth_mode': bandwidth_mode
        }
        
        try:
            self.command_queue.put(command)
            self.info_message.emit(f"대역폭 모드 설정: {bandwidth_mode}")
        except Exception as e:
            self.error_occurred.emit(f"대역폭 설정 실패: {str(e)}")
            
    def start_finder(self):
        """NDI 소스 검색 시작"""
        if not self.is_running:
            self.start_ndi_process()
            
        command = {'command': 'start_finder'}
        try:
            self.command_queue.put(command)
        except Exception as e:
            self.error_occurred.emit(f"소스 검색 시작 실패: {str(e)}")
            
    def is_receiver_connected(self):
        """수신기 연결 상태 확인"""
        # 간단한 구현: 프로세스가 실행 중이고 소스가 설정되었는지 확인
        return self.is_running and hasattr(self, '_current_source') and self._current_source is not None
        
    def connect_to_source(self, source_info, bandwidth_mode):
        """NDI 소스에 연결"""
        if not self.is_running:
            self.start_ndi_process()
            
        source_name = source_info.get('name')
        source_url = source_info.get('url')
        
        # 현재 소스 정보 저장
        self._current_source = source_info
        
        # 대역폭 모드 설정
        self.set_bandwidth_mode(bandwidth_mode)
        
        # 소스 설정
        self.set_source(source_name, source_url)
        
    def disconnect_source(self):
        """현재 소스 연결 해제"""
        if not self.is_running:
            return
            
        command = {'command': 'disconnect'}
        try:
            self.command_queue.put(command)
            self._current_source = None
        except Exception as e:
            self.error_occurred.emit(f"소스 연결 해제 실패: {str(e)}")
            
    def cleanup(self):
        """리소스 정리"""
        self.stop_ndi_process()
            
    def _check_queues(self):
        """큐에서 데이터 확인 및 처리"""
        # 프레임 큐 확인
        try:
            while not self.frame_queue.empty():
                frame_data = self.frame_queue.get_nowait()
                if frame_data is not None:
                    self.frame_received.emit(frame_data)
        except:
            pass
            
        # 상태 큐 확인
        try:
            while not self.status_queue.empty():
                status_data = self.status_queue.get_nowait()
                self._handle_status_message(status_data)
        except:
            pass
            
    def _handle_status_message(self, status_data):
        """상태 메시지 처리"""
        if not isinstance(status_data, dict):
            return
            
        msg_type = status_data.get('type')
        message = status_data.get('message', '')
        
        if msg_type == 'info':
            self.info_message.emit(message)
        elif msg_type == 'error':
            self.error_occurred.emit(message)
        elif msg_type == 'connection_status':
            connected = status_data.get('connected', False)
            self.connection_status_changed.emit(connected)
        elif msg_type == 'sources_found':
            sources = status_data.get('sources', [])
            self.sources_changed.emit(sources)
        elif msg_type == 'fps_update':
            fps = status_data.get('fps', 0.0)
            self.fps_updated.emit(fps)


class NDIWorkerProcess(mp.Process):
    """별도 프로세스에서 실행되는 NDI 워커"""
    
    def __init__(self, frame_queue, command_queue, status_queue):
        super().__init__()
        self.frame_queue = frame_queue
        self.command_queue = command_queue
        self.status_queue = status_queue
        self.running = False
        
        # NDI 관련 객체들
        self.ndi_recv = None
        self.ndi_find = None
        self.current_source = None
        self.bandwidth_mode = ndi.RECV_BANDWIDTH_HIGHEST
        self.frame_count = 0
        
        # FPS 카운터
        self.fps_frame_count = 0
        self.fps_start_time = time.time()
        self.last_fps_update = time.time()
        
    def run(self):
        """프로세스 메인 루프"""
        try:
            # NDI 초기화
            if not ndi.initialize():
                self._send_status('error', 'NDI 라이브러리 초기화 실패')
                return
                
            self.running = True
            self._send_status('info', 'NDI 워커 프로세스 시작됨')
            
            while self.running:
                # 명령 처리
                self._process_commands()
                
                # NDI 프레임 캡처 (연속적으로 수행)
                if self.ndi_recv:
                    self._capture_frames()
                    
                # NDI 소스 검색 (덜 빈번하게)
                if self.ndi_find and self.frame_count % 100 == 0:  # 100프레임마다 한 번
                    self._find_sources()
                    
                # CPU 사용량 조절을 위한 최소 대기 (마이크로초 단위)
                time.sleep(0.0001)  # 0.1ms로 단축
                
        except Exception as e:
            self._send_status('error', f'NDI 워커 프로세스 오류: {str(e)}')
        finally:
            self._cleanup()
            
    def _process_commands(self):
        """명령 큐에서 명령 처리"""
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                
                if command['command'] == 'stop':
                    self.running = False
                    
                elif command['command'] == 'set_source':
                    self._set_source(command['source_name'], command['source_url'])
                    
                elif command['command'] == 'set_bandwidth':
                    self._set_bandwidth(command['bandwidth_mode'])
                    
                elif command['command'] == 'start_finder':
                    self._start_finder()
                    
                elif command['command'] == 'disconnect':
                    self._disconnect_source()
                    
        except queue.Empty:
            pass
        except Exception as e:
            self._send_status('error', f'명령 처리 오류: {str(e)}')
            
    def _set_source(self, source_name, source_url):
        """NDI 소스 설정"""
        try:
            self._send_status('info', f'[DEBUG] _set_source 시작: {source_name}, {source_url}')
            
            # 기존 수신기 정리
            if self.ndi_recv:
                ndi.recv_destroy(self.ndi_recv)
                self.ndi_recv = None
                self._send_status('info', '[DEBUG] 기존 수신기 정리 완료')
                
            # 새 수신기 생성
            recv_create = ndi.RecvCreateV3()
            recv_create.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
            recv_create.bandwidth = self.bandwidth_mode
            recv_create.allow_video_fields = False
            
            self._send_status('info', f'[DEBUG] 수신기 생성 시도, 대역폭: {self.bandwidth_mode}')
            self.ndi_recv = ndi.recv_create_v3(recv_create)
            
            if not self.ndi_recv:
                self._send_status('error', f'NDI 수신기 생성 실패: {source_name}')
                return
                
            self._send_status('info', '[DEBUG] NDI 수신기 생성 성공')
                
            # 소스 연결
            source = ndi.Source()
            source.ndi_name = source_name
            source.url_address = source_url
            
            self._send_status('info', f'[DEBUG] 소스 연결 시도: {source_name}')
            ndi.recv_connect(self.ndi_recv, source)
            self.current_source = source
            
            self._send_status('info', '[DEBUG] 연결 상태 신호 전송 중...')
            self._send_status('connection_status', '', {'connected': True})
            self._send_status('info', f'NDI 소스 연결됨: {source_name}')
            
        except Exception as e:
            self._send_status('error', f'소스 설정 오류: {str(e)}')
            import traceback
            self._send_status('error', f'상세 오류: {traceback.format_exc()}')
            
    def _set_bandwidth(self, bandwidth_mode):
        """대역폭 모드 설정"""
        if bandwidth_mode == "Original":
            self.bandwidth_mode = ndi.RECV_BANDWIDTH_HIGHEST
        elif bandwidth_mode == "Proxy":
            self.bandwidth_mode = ndi.RECV_BANDWIDTH_LOWEST
            
        # 현재 연결된 소스가 있으면 재연결
        if self.current_source:
            self._set_source(self.current_source.ndi_name, self.current_source.url_address)
            
    def _start_finder(self):
        """NDI 소스 검색 시작"""
        try:
            if not self.ndi_find:
                self.ndi_find = ndi.find_create_v2()
                if not self.ndi_find:
                    self._send_status('error', 'NDI 검색기 생성 실패')
                    return
                    
            self._send_status('info', 'NDI 소스 검색 시작')
            
        except Exception as e:
            self._send_status('error', f'소스 검색 시작 오류: {str(e)}')
            
    def _disconnect_source(self):
        """현재 NDI 소스 연결 해제"""
        try:
            if self.ndi_recv:
                ndi.recv_destroy(self.ndi_recv)
                self.ndi_recv = None
                
            self.current_source = None
            self._send_status('connection_status', '', {'connected': False})
            self._send_status('info', 'NDI 소스 연결 해제됨')
            
        except Exception as e:
            self._send_status('error', f'소스 연결 해제 오류: {str(e)}')
            
    def _capture_frames(self):
        """NDI 프레임 캡처"""
        try:
            result = ndi.recv_capture_v2(self.ndi_recv, 0)
            frame_type, v_frame, a_frame, m_frame = result
            
            if frame_type == ndi.FRAME_TYPE_VIDEO and v_frame is not None:
                if v_frame.data is not None and v_frame.data.size > 0:
                    # 프레임 카운터 증가
                    self.frame_count += 1
                    self.fps_frame_count += 1
                    
                    # FPS 계산 및 전송 (1초마다)
                    current_time = time.time()
                    if current_time - self.last_fps_update >= 1.0:
                        elapsed_time = current_time - self.fps_start_time
                        if elapsed_time > 0:
                            fps = self.fps_frame_count / elapsed_time
                            self._send_status('fps_update', '', {'fps': fps})
                        
                        # FPS 카운터 리셋
                        self.fps_frame_count = 0
                        self.fps_start_time = current_time
                        self.last_fps_update = current_time
                    
                    # 프레임 데이터 복사 (프로세스 간 전송을 위해)
                    if not v_frame.data.flags['C_CONTIGUOUS']:
                        frame_data = np.ascontiguousarray(v_frame.data.copy())
                    else:
                        frame_data = v_frame.data.copy()
                        
                    # 프레임 큐가 가득 찬 경우 오래된 프레임 제거
                    try:
                        self.frame_queue.put_nowait(frame_data)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()  # 오래된 프레임 제거
                            self.frame_queue.put_nowait(frame_data)  # 새 프레임 추가
                        except:
                            pass
                            
                # 프레임 해제
                ndi.recv_free_video_v2(self.ndi_recv, v_frame)
                
            elif frame_type == ndi.FRAME_TYPE_AUDIO and a_frame is not None:
                ndi.recv_free_audio_v2(self.ndi_recv, a_frame)
                
            elif frame_type == ndi.FRAME_TYPE_METADATA and m_frame is not None:
                ndi.recv_free_metadata(self.ndi_recv, m_frame)
                
        except Exception as e:
            self._send_status('error', f'프레임 캡처 오류: {str(e)}')
            
    def _find_sources(self):
        """NDI 소스 검색"""
        try:
            if ndi.find_wait_for_sources(self.ndi_find, 100):  # 100ms 대기
                sources = ndi.find_get_current_sources(self.ndi_find)
                if sources:
                    source_list = []
                    for source in sources:
                        source_info = {
                            'name': source.ndi_name,
                            'url': source.url_address
                        }
                        source_list.append(source_info)
                        
                    self._send_status('sources_found', '', {'sources': source_list})
                    
        except Exception as e:
            self._send_status('error', f'소스 검색 오류: {str(e)}')
            
    def _send_status(self, msg_type, message, extra_data=None):
        """상태 메시지 전송"""
        try:
            status_data = {
                'type': msg_type,
                'message': message
            }
            
            if extra_data:
                status_data.update(extra_data)
                
            self.status_queue.put_nowait(status_data)
            
        except queue.Full:
            pass  # 큐가 가득 찬 경우 무시
        except Exception:
            pass  # 오류 발생 시 무시
            
    def _cleanup(self):
        """리소스 정리"""
        try:
            if self.ndi_recv:
                ndi.recv_destroy(self.ndi_recv)
                self.ndi_recv = None
                
            if self.ndi_find:
                ndi.find_destroy(self.ndi_find)
                self.ndi_find = None
                
            ndi.destroy()
            self._send_status('info', 'NDI 워커 프로세스 정리 완료')
            
        except Exception as e:
            self._send_status('error', f'정리 중 오류: {str(e)}')