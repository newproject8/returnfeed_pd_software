#!/usr/bin/env python3
"""
NDI Proxy 기반 스트리밍 시스템
640x360 해상도 고정, 60fps 지원, GPU 벤더 독립적
"""

import subprocess
import json
import time
import sys
import os
import threading
import logging
from datetime import datetime
from gpu_vendor_detector import GPUEncoderDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NDIProxyStreamer:
    """NDI Proxy 기반 스트리밍 관리자"""
    
    def __init__(self, mediamtx_url="localhost:8890"):
        self.mediamtx_url = mediamtx_url
        self.resolution = "640x360"
        self.fps = 60
        self.base_bitrate = "1M"
        self.current_bitrate = 1000000  # bps
        self.process = None
        self.is_streaming = False
        
        # GPU 인코더 감지
        self.detector = GPUEncoderDetector()
        self.encoder = self.detector.detect_best_encoder()
        logger.info(f"선택된 인코더: {self.encoder}")
        
    def find_ndi_sources(self):
        """사용 가능한 NDI 소스 찾기"""
        try:
            # NDI 소스 목록 가져오기
            cmd = ['ffmpeg', '-f', 'libndi_newtek', '-list_sources', '1', '-i', 'dummy']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            sources = []
            proxy_sources = []
            
            for line in result.stderr.split('\n'):
                if '#' in line and 'NDI' in line:
                    source_name = line.split('"')[1] if '"' in line else line.strip()
                    sources.append(source_name)
                    
                    # NDI Proxy 소스 확인
                    if '(NDI Proxy)' in source_name:
                        proxy_sources.append(source_name)
            
            logger.info(f"발견된 NDI 소스: {len(sources)}개")
            logger.info(f"NDI Proxy 소스: {len(proxy_sources)}개")
            
            return sources, proxy_sources
            
        except Exception as e:
            logger.error(f"NDI 소스 검색 실패: {e}")
            return [], []
    
    def get_stream_params(self):
        """스트리밍 파라미터 생성"""
        # 기본 파라미터
        params = self.detector.get_encoder_params(
            self.encoder, 
            self.resolution, 
            self.fps, 
            self.base_bitrate
        )
        
        # 오디오 파라미터 추가
        audio_params = [
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-ar', '48000',
            '-ac', '2',
            '-application', 'lowdelay'  # 낮은 레이턴시
        ]
        
        return params + audio_params
    
    def start_streaming(self, ndi_source_name, session_key):
        """NDI Proxy 스트리밍 시작"""
        if self.is_streaming:
            logger.warning("이미 스트리밍 중입니다")
            return False
        
        # NDI Proxy 소스 확인
        if '(NDI Proxy)' not in ndi_source_name:
            # 일반 소스인 경우 Proxy 버전 찾기
            proxy_name = f"{ndi_source_name} (NDI Proxy)"
            logger.info(f"NDI Proxy 소스로 변경: {proxy_name}")
        else:
            proxy_name = ndi_source_name
        
        # 스트림 키 생성
        stream_key = f"ndi_proxy_{session_key}_{int(time.time())}"
        
        # FFmpeg 명령 구성
        params = self.get_stream_params()
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'libndi_newtek',
            '-i', proxy_name,
            '-filter:v', f'scale={self.resolution}:force_original_aspect_ratio=decrease,pad={self.resolution}:(ow-iw)/2:(oh-ih)/2',
            '-r', str(self.fps)
        ] + params + [
            '-f', 'mpegts',
            '-flush_packets', '0',
            f'srt://{self.mediamtx_url}?streamid={stream_key}&latency=20'
        ]
        
        try:
            logger.info(f"스트리밍 시작: {proxy_name}")
            logger.info(f"스트림 키: {stream_key}")
            logger.info(f"명령: {' '.join(ffmpeg_cmd)}")
            
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.is_streaming = True
            self.stream_key = stream_key
            
            # 로그 모니터링 스레드 시작
            self.log_thread = threading.Thread(target=self._monitor_logs)
            self.log_thread.start()
            
            # 통계 모니터링 스레드 시작
            self.stats_thread = threading.Thread(target=self._monitor_stats)
            self.stats_thread.start()
            
            return {
                'success': True,
                'stream_key': stream_key,
                'url': f"http://{self.mediamtx_url.split(':')[0]}/ndi_proxy_{stream_key}",
                'encoder': self.encoder,
                'resolution': self.resolution,
                'fps': self.fps
            }
            
        except Exception as e:
            logger.error(f"스트리밍 시작 실패: {e}")
            self.is_streaming = False
            return {'success': False, 'error': str(e)}
    
    def stop_streaming(self):
        """스트리밍 중지"""
        if not self.is_streaming:
            logger.warning("스트리밍 중이 아닙니다")
            return False
        
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("스트리밍 정상 종료")
            
            self.is_streaming = False
            return True
            
        except subprocess.TimeoutExpired:
            self.process.kill()
            logger.warning("스트리밍 강제 종료")
            self.is_streaming = False
            return True
            
        except Exception as e:
            logger.error(f"스트리밍 중지 실패: {e}")
            return False
    
    def adjust_bitrate(self, new_bitrate):
        """비트레이트 동적 조절 (0.1-1 Mbps)"""
        # 범위 제한
        new_bitrate = max(100000, min(1000000, new_bitrate))
        
        if not self.is_streaming or not self.process:
            logger.warning("스트리밍 중이 아니므로 비트레이트를 조절할 수 없습니다")
            return False
        
        try:
            # FFmpeg 프로세스에 명령 전송
            # 실시간 비트레이트 조절은 인코더에 따라 다름
            self.current_bitrate = new_bitrate
            logger.info(f"비트레이트 조정: {new_bitrate/1000:.0f}kbps")
            
            # TODO: 실시간 비트레이트 조절 구현
            # 일부 인코더는 실행 중 조절을 지원하지 않을 수 있음
            
            return True
            
        except Exception as e:
            logger.error(f"비트레이트 조절 실패: {e}")
            return False
    
    def _monitor_logs(self):
        """FFmpeg 로그 모니터링"""
        while self.is_streaming and self.process:
            try:
                line = self.process.stderr.readline()
                if line:
                    # 중요한 로그만 출력
                    if any(keyword in line for keyword in ['error', 'fps=', 'bitrate=', 'speed=']):
                        logger.info(f"[FFmpeg] {line.strip()}")
                        
                        # FPS 정보 추출
                        if 'fps=' in line:
                            try:
                                fps = float(line.split('fps=')[1].split()[0])
                                if fps < self.fps * 0.9:  # 90% 미만
                                    logger.warning(f"FPS 저하 감지: {fps}")
                            except:
                                pass
                                
            except Exception as e:
                logger.error(f"로그 모니터링 오류: {e}")
                break
    
    def _monitor_stats(self):
        """스트리밍 통계 모니터링"""
        stats_interval = 5  # 5초마다
        
        while self.is_streaming:
            try:
                time.sleep(stats_interval)
                
                if self.process and self.process.poll() is None:
                    # 프로세스 상태 확인
                    cpu_usage = self._get_process_cpu_usage()
                    memory_usage = self._get_process_memory_usage()
                    
                    stats = {
                        'timestamp': datetime.now().isoformat(),
                        'encoder': self.encoder,
                        'bitrate': self.current_bitrate,
                        'resolution': self.resolution,
                        'fps': self.fps,
                        'cpu_usage': cpu_usage,
                        'memory_usage': memory_usage
                    }
                    
                    logger.info(f"스트리밍 통계: CPU {cpu_usage:.1f}%, Memory {memory_usage:.1f}MB")
                    
                    # 통계를 파일로 저장
                    with open('/tmp/streaming_stats.json', 'w') as f:
                        json.dump(stats, f)
                        
            except Exception as e:
                logger.error(f"통계 모니터링 오류: {e}")
    
    def _get_process_cpu_usage(self):
        """프로세스 CPU 사용률"""
        try:
            if self.process:
                import psutil
                p = psutil.Process(self.process.pid)
                return p.cpu_percent(interval=1)
        except:
            return 0.0
    
    def _get_process_memory_usage(self):
        """프로세스 메모리 사용량 (MB)"""
        try:
            if self.process:
                import psutil
                p = psutil.Process(self.process.pid)
                return p.memory_info().rss / 1024 / 1024
        except:
            return 0.0


def main():
    """테스트 실행"""
    streamer = NDIProxyStreamer()
    
    # NDI 소스 찾기
    sources, proxy_sources = streamer.find_ndi_sources()
    
    if not proxy_sources:
        logger.error("NDI Proxy 소스를 찾을 수 없습니다")
        return
    
    # 첫 번째 Proxy 소스로 스트리밍 시작
    result = streamer.start_streaming(proxy_sources[0], "test_session")
    
    if result['success']:
        logger.info(f"스트리밍 URL: {result['url']}")
        
        try:
            # 60초 동안 스트리밍
            time.sleep(60)
        except KeyboardInterrupt:
            logger.info("사용자 중단")
        
        streamer.stop_streaming()
    else:
        logger.error(f"스트리밍 시작 실패: {result.get('error')}")


if __name__ == "__main__":
    main()