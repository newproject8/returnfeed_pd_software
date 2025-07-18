from PyQt6.QtCore import QThread, pyqtSignal
import NDIlib as ndi
import numpy as np
import time
import queue
from dataclasses import dataclass
from typing import Optional

@dataclass
class FrameData:
    frame_type: int
    video_frame: any = None
    audio_frame: any = None
    timestamp: float = 0.0

class AdaptiveTimeout:
    def __init__(self, base_timeout=25):
        self.base_timeout = base_timeout
        self.current_timeout = base_timeout
        self.miss_count = 0
        
    def get_timeout(self):
        return self.current_timeout
        
    def on_frame_received(self):
        self.miss_count = 0
        if self.current_timeout > self.base_timeout:
            self.current_timeout = max(self.base_timeout, 
                                     self.current_timeout - 5)
    
    def on_frame_missed(self):
        self.miss_count += 1
        if self.miss_count > 3:
            self.current_timeout = min(100, self.current_timeout + 10)

class FPSCounter:
    def __init__(self, window_size=60):
        self.window_size = window_size
        self.frame_times = []
        
    def add_frame(self):
        current_time = time.time()
        self.frame_times.append(current_time)
        
        # 윈도우 크기 유지
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)
            
    def get_fps(self):
        if len(self.frame_times) < 2:
            return 0.0
            
        time_span = self.frame_times[-1] - self.frame_times[0]
        if time_span > 0:
            return (len(self.frame_times) - 1) / time_span
        return 0.0

class NDIReceiver(QThread):
    frame_received = pyqtSignal(np.ndarray)
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    info_message = pyqtSignal(str)
    fps_updated = pyqtSignal(float)  # FPS 업데이트 시그널 추가

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._ndi_source_name = None
        self._ndi_source_obj = None
        self.ndi_recv = None
        self.recv_bandwidth = ndi.RECV_BANDWIDTH_HIGHEST
        self.color_format = ndi.RECV_COLOR_FORMAT_FASTEST  # 최고 성능 포맷으로 변경
        
        # 성능 최적화 관련 추가
        self.adaptive_timeout = AdaptiveTimeout()
        self.fps_counter = FPSCounter()
        self.frame_queue = queue.Queue(maxsize=3)  # 최소 버퍼링
        self.last_fps_update = time.time()

    def set_source(self, ndi_source_object: ndi.Source):
        self._log_info(f"set_source called with object: {ndi_source_object}, type: {type(ndi_source_object)}")
        if ndi_source_object:
            self._log_info(f"ndi_source_object is not None. Checking for 'ndi_name' attribute...")
            has_ndi_name = hasattr(ndi_source_object, 'ndi_name')
            self._log_info(f"hasattr(ndi_source_object, 'ndi_name') is {has_ndi_name}")
            if has_ndi_name:
                actual_name = "<Error getting name>"
                try:
                    actual_name = ndi_source_object.ndi_name
                except Exception as e:
                    self._log_info(f"Error accessing ndi_source_object.ndi_name: {e}")
                self._log_info(f"ndi_source_object.ndi_name is '{actual_name}'")
                self._ndi_source_name = actual_name
                self._log_info(f"Setting internal source to: {self._ndi_source_name}")
                self._ndi_source_obj = ndi_source_object
                self._log_info(f"self._ndi_source_obj is now: {self._ndi_source_obj}, type: {type(self._ndi_source_obj)}")
                if self._ndi_source_obj and hasattr(self._ndi_source_obj, 'ndi_name'): # Re-check after assignment
                     self._log_info(f"self._ndi_source_obj.ndi_name is now: {self._ndi_source_obj.ndi_name}")
            else:
                self._log_info("ndi_source_object does not have 'ndi_name' attribute.")
                self._ndi_source_name = None
                self._ndi_source_obj = None
        else:
            self._log_info("ndi_source_object is None or Falsy.")
            self._ndi_source_name = None
            self._ndi_source_obj = None

    def set_bandwidth_mode(self, bandwidth_mode: str):
        # 항상 Proxy 모드(LOWEST bandwidth)로 고정하여 레이턴시 최소화
        new_bandwidth = ndi.RECV_BANDWIDTH_LOWEST
        
        if new_bandwidth != self.recv_bandwidth:
            self.recv_bandwidth = new_bandwidth
            self._log_info(f"Bandwidth set to: Proxy (low latency mode)")
            if self.isRunning():
                self._log_info("Restarting receiver for proxy mode...")
                self.request_stop_and_wait() # Custom method to stop and wait
                if self._ndi_source_obj: # Check if source object is set
                    self.start() # Restart the thread
                else:
                    self._log_info("Cannot restart receiver: source not set.")
        else:
            self._log_info(f"Bandwidth already set to: Proxy (low latency mode)")

    def run(self):
        self._running = True
        self._log_info(f"Run method started. Initial self._ndi_source_obj: {self._ndi_source_obj}, type: {type(self._ndi_source_obj)}")
        initial_source_name_for_log = self._ndi_source_name or "unknown source (obj is None/invalid or lacks name)"

        # Ensure _ndi_source_name is properly set if _ndi_source_obj exists
        if self._ndi_source_obj and hasattr(self._ndi_source_obj, 'ndi_name'):
            try:
                initial_source_name_for_log = self._ndi_source_obj.ndi_name
                if not self._ndi_source_name:
                    self._ndi_source_name = initial_source_name_for_log # Ensure _ndi_source_name is set
                self._log_info(f"Run method: self._ndi_source_obj.ndi_name: {initial_source_name_for_log}")
            except Exception as e:
                self._log_info(f"Run method: Error accessing self._ndi_source_obj.ndi_name: {e}")
        elif not self._ndi_source_name and self._ndi_source_obj:
            self._log_info(f"Run method: self._ndi_source_obj exists but lacks 'ndi_name' or _ndi_source_name not set.")
        elif not self._ndi_source_obj:
            self._log_info(f"Run method: self._ndi_source_obj is None. Current _ndi_source_name attribute: {self._ndi_source_name}")

        self._log_info(f"NDIReceiver run loop preparing for source: {initial_source_name_for_log}.")

        if not self._ndi_source_obj:
            self._log_info("NDI source object not properly set before run(). Aborting thread.")
            if hasattr(self, 'error_occurred'): self.error_occurred.emit("NDI source object not properly set before run().")
            if hasattr(self, 'connection_status_changed'): self.connection_status_changed.emit(False)
            self._running = False
            return

        # Ensure _ndi_source_name is set for logging within try/except/finally
        current_source_name_for_logs = self._ndi_source_name or initial_source_name_for_log

        # Create NDI receiver with optimized settings for maximum performance
        recv_create_v3 = ndi.RecvCreateV3()
        # NDI SDK 최적화 설정: 최고 성능 모드
        recv_create_v3.color_format = ndi.RECV_COLOR_FORMAT_FASTEST  # 최고 성능 포맷
        recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_HIGHEST  # 최고 대역폭으로 품질 확보
        recv_create_v3.allow_video_fields = True  # 필드 처리 허용으로 프레임 레이트 향상
        recv_create_v3.source_to_connect_to = self._ndi_source_obj  # Direct source connection

        try:
            self.ndi_recv = ndi.recv_create_v3(recv_create_v3)
            # self._log_info(f"[DEBUG][NDIReceiver.run] ndi.recv_create_v3 called. self.ndi_recv is {'valid' if self.ndi_recv else 'None'}")

            if not self.ndi_recv:
                self._log_info(f"Failed to create NDI receiver for {current_source_name_for_logs}.")
                # print(f"[ERROR][NDIReceiver.run] Failed to create NDI receiver for {current_source_name_for_logs}. self.ndi_recv is None.")
                if hasattr(self, 'error_occurred'): self.error_occurred.emit(f"Failed to create NDI receiver for {current_source_name_for_logs}.")
                # connection_status_changed will be emitted in finally
                self._running = False # Set running to false before returning from try block
                return # Exit run method if receiver creation fails

            # self._log_info(f"[DEBUG][NDIReceiver.run] Attempting to connect to source: {current_source_name_for_logs} (URL: {self._ndi_source_obj.url_address if self._ndi_source_obj else 'N/A'})...")
            ndi.recv_connect(self.ndi_recv, self._ndi_source_obj)
            # self._log_info(f"[DEBUG][NDIReceiver.run] ndi.recv_connect call completed for {current_source_name_for_logs}.")
            if hasattr(self, 'connection_status_changed'): self.connection_status_changed.emit(True)
            self._log_info(f"NDI receiver connected to {current_source_name_for_logs}.")

            while self._running:
                # NDI SDK 최적화: 적응형 타임아웃으로 프레임 레이트 기반 최적화
                # 59.94fps 기준 16.6ms 프레임 간격의 1.5배인 25ms 기본 타임아웃
                timeout_ms = self.adaptive_timeout.get_timeout()
                frame_type, v_frame, a_frame, m_frame = ndi.recv_capture_v2(self.ndi_recv, timeout_ms)

                if frame_type == ndi.FRAME_TYPE_VIDEO:
                    try:
                        if v_frame is not None and v_frame.data is not None and v_frame.data.size > 0:
                            # 적응형 타임아웃 - 프레임 수신 성공
                            self.adaptive_timeout.on_frame_received()
                            
                            # FPS 카운터 업데이트
                            self.fps_counter.add_frame()
                            
                            # FPS 정보를 1초마다 업데이트
                            current_time = time.time()
                            if current_time - self.last_fps_update >= 1.0:
                                current_fps = self.fps_counter.get_fps()
                                self.fps_updated.emit(current_fps)
                                self.last_fps_update = current_time
                            
                            # Process all frames without skipping to maintain full quality and frame rate
                            # Ensure frame data is contiguous for efficient processing
                            if not v_frame.data.flags['C_CONTIGUOUS']:
                                frame_data = np.ascontiguousarray(v_frame.data)
                            else:
                                frame_data = v_frame.data
                            
                            # 프레임 큐를 통한 버퍼링 관리
                            try:
                                frame_info = FrameData(
                                    frame_type=frame_type,
                                    video_frame=frame_data.copy(),  # 안전한 복사
                                    timestamp=current_time
                                )
                                self.frame_queue.put_nowait(frame_info)
                            except queue.Full:
                                # 오래된 프레임 제거 후 새 프레임 추가
                                try:
                                    self.frame_queue.get_nowait()
                                except queue.Empty:
                                    pass
                                frame_info = FrameData(
                                    frame_type=frame_type,
                                    video_frame=frame_data.copy(),
                                    timestamp=current_time
                                )
                                self.frame_queue.put_nowait(frame_info)
                            
                            # Emit frame for GUI display
                            self.frame_received.emit(frame_data)
                            
                    except Exception as e_video_proc:
                        self._log_info(f"Error processing video frame for {current_source_name_for_logs}: {e_video_proc}")
                    finally:
                        # 즉시 메모리 해제
                        if v_frame is not None:
                            ndi.recv_free_video_v2(self.ndi_recv, v_frame)

                elif frame_type == ndi.FRAME_TYPE_AUDIO:
                    try:
                        if a_frame is not None and a_frame.data is not None and a_frame.data.size > 0:
                            pass # Placeholder for actual audio processing
                    except Exception as e_audio_proc:
                        self._log_info(f"Error processing audio frame for {current_source_name_for_logs}: {e_audio_proc}")
                    finally:
                        if a_frame is not None:
                            ndi.recv_free_audio_v2(self.ndi_recv, a_frame)

                elif frame_type == ndi.FRAME_TYPE_METADATA:
                    try:
                        if m_frame is not None and m_frame.data is not None:
                            metadata_payload = m_frame.data
                            metadata_str = ""
                            if isinstance(metadata_payload, bytes):
                                metadata_str = metadata_payload.decode('utf-8', errors='ignore')
                            elif isinstance(metadata_payload, str):
                                metadata_str = metadata_payload
                            else:
                                metadata_str = str(metadata_payload)
                            # self._log_info(f"Metadata for {current_source_name_for_logs}: {metadata_str[:100]}")
                    except Exception as e_meta_proc:
                        self._log_info(f"Error processing metadata for {current_source_name_for_logs}: {e_meta_proc}")
                    finally:
                        if m_frame is not None:
                            ndi.recv_free_metadata(self.ndi_recv, m_frame)

                elif frame_type == ndi.FRAME_TYPE_ERROR:
                    self._log_info(f"NDI FRAME_TYPE_ERROR received for {current_source_name_for_logs}. Stopping receiver.")
                    if hasattr(self, 'error_occurred'): self.error_occurred.emit(f"NDI source reported an error for {current_source_name_for_logs}.")
                    self._running = False # Stop the loop

                elif frame_type == ndi.FRAME_TYPE_NONE:
                    # 적응형 타임아웃 - 프레임 누락
                    self.adaptive_timeout.on_frame_missed()
                    pass # Timeout, just continue loop

        except Exception as e_outer_loop:
            self._log_info(f"[CRITICAL RUNTIME ERROR] Unhandled exception in NDIReceiver run loop for {current_source_name_for_logs}: {e_outer_loop}")
            # print(f"[CRITICAL RUNTIME ERROR][NDIReceiver.run] Exception: {e_outer_loop}", flush=True)
            import traceback
            traceback.print_exc() # Print stack trace to console
            if hasattr(self, 'error_occurred'): self.error_occurred.emit(f"Critical runtime error in NDI stream for {current_source_name_for_logs}: {str(e_outer_loop)}")
            # self._running will be set to False in finally

        finally:
            self._log_info(f"NDIReceiver run method's 'finally' block reached for {current_source_name_for_logs}.")
            if self.ndi_recv:
                try:
                    self._log_info(f"Destroying NDI receiver for {current_source_name_for_logs} in 'finally' block.")
                    ndi.recv_destroy(self.ndi_recv)
                    self.ndi_recv = None
                except Exception as e_destroy:
                    self._log_info(f"Exception during ndi.recv_destroy for {current_source_name_for_logs}: {e_destroy}")
                    if hasattr(self, 'error_occurred'): self.error_occurred.emit(f"Error closing NDI Receiver for {current_source_name_for_logs}: {str(e_destroy)}")
            
            # Ensure connection status is False as the thread is stopping.
            if hasattr(self, 'connection_status_changed'): self.connection_status_changed.emit(False)
            
            self._running = False # Explicitly set running to false at the very end
            self._log_info(f"NDIReceiver run loop fully finished for {current_source_name_for_logs}.")
            self._log_info(f"NDIReceiver run loop finished for {self._ndi_source_name if self._ndi_source_name else 'unknown source'}.")

    def request_stop_and_wait(self):
        self._log_info(f"Requesting stop for receiver: {self._ndi_source_name if self._ndi_source_name else 'N/A'}")
        self._running = False
        if self.isRunning():
            if QThread.currentThread() != self: # Ensure not called from within the same thread's run() method directly if wait() is used
                self.wait() # Wait for run() to finish
            else:
                self._log_info("Stop requested from within the thread. Loop will exit on next iteration.")
        self._log_info(f"Receiver stopped: {self._ndi_source_name if self._ndi_source_name else 'N/A'}")

    def request_stop(self): # Public method to stop the thread
        self.request_stop_and_wait()

    def _log_info(self, message):
        print(f"[NDIReceiver]: {message}") # For console debugging
        self.info_message.emit(f"[NDIReceiver]: {message}") # For GUI
