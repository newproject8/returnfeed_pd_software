#!/usr/bin/env python3
"""
시뮬캐스트 인코딩 시스템
동일한 NDI 소스에서 3개의 다른 품질 스트림을 동시에 생성
패스스루 모드를 유지하면서 네트워크 적응성 제공
"""

import subprocess
import threading
import time
import logging
import json
import os
from dataclasses import dataclass
from typing import List, Optional, Dict
from gpu_vendor_detector import GPUEncoderDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SimulcastLayer:
    """시뮬캐스트 레이어 정의"""
    rid: str  # 레이어 식별자 (h, m, l)
    resolution: str
    fps: int
    bitrate: str
    scale_factor: float
    
class SimulcastEncoder:
    """시뮬캐스트 인코더 - 3개 품질의 스트림을 동시에 생성"""
    
    # 시뮬캐스트 레이어 정의 (2개로 간소화)
    LAYERS = [
        SimulcastLayer('h', '640x360', 60, '1000k', 1.0),    # High: 1Mbps
        SimulcastLayer('l', '640x360', 30, '100k', 1.0),     # Low: 0.1Mbps (100kbps)
    ]
    
    def __init__(self, mediamtx_url="localhost:8890"):
        self.mediamtx_url = mediamtx_url
        self.processes = {}
        self.is_encoding = False
        
        # GPU 인코더 감지
        self.detector = GPUEncoderDetector()
        self.encoder = self.detector.detect_best_encoder()
        logger.info(f"시뮬캐스트 인코더: {self.encoder}")
        
    def get_layer_params(self, layer: SimulcastLayer) -> List[str]:
        """레이어별 인코딩 파라미터 생성"""
        
        # 기본 비디오 파라미터
        video_params = self.detector.get_encoder_params(
            self.encoder,
            layer.resolution,
            layer.fps,
            layer.bitrate
        )
        
        # 시뮬캐스트 최적화
        if self.encoder == 'h264_nvenc':
            # NVIDIA 시뮬캐스트 최적화
            video_params.extend([
                '-rc-lookahead', '0',  # 실시간 인코딩
                '-no-scenecut', '1',   # 씬 컷 비활성화
                '-forced-idr', '1',    # 강제 IDR
            ])
        elif self.encoder == 'h264_qsv':
            # Intel Quick Sync 최적화
            video_params.extend([
                '-low_delay_brc', '1',
                '-adaptive_i', '0',
                '-adaptive_b', '0',
            ])
        
        # 오디오 파라미터 (모든 레이어 동일)
        audio_params = [
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-ar', '48000',
            '-ac', '2',
            '-application', 'lowdelay'
        ]
        
        return video_params + audio_params
    
    def start_simulcast(self, ndi_source: str, session_key: str):
        """시뮬캐스트 인코딩 시작"""
        if self.is_encoding:
            logger.warning("이미 인코딩 중입니다")
            return False
        
        self.is_encoding = True
        results = []
        
        # NDI Proxy 소스 확인
        if '(NDI Proxy)' not in ndi_source:
            ndi_source = f"{ndi_source} (NDI Proxy)"
        
        # 각 레이어별로 인코딩 프로세스 시작
        for layer in self.LAYERS:
            stream_key = f"simulcast_{session_key}_{layer.rid}"
            
            # FFmpeg 명령 구성
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'libndi_newtek',
                '-i', ndi_source,
                '-filter:v', f'scale={layer.resolution}:force_original_aspect_ratio=decrease,fps={layer.fps}',
            ] + self.get_layer_params(layer) + [
                '-f', 'mpegts',
                '-flush_packets', '0',
                f'srt://{self.mediamtx_url}?streamid={stream_key}&latency=20'
            ]
            
            try:
                logger.info(f"시뮬캐스트 레이어 {layer.rid} 시작")
                logger.info(f"  해상도: {layer.resolution}")
                logger.info(f"  FPS: {layer.fps}")
                logger.info(f"  비트레이트: {layer.bitrate}")
                
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                self.processes[layer.rid] = {
                    'process': process,
                    'stream_key': stream_key,
                    'layer': layer
                }
                
                # 로그 모니터링 스레드
                log_thread = threading.Thread(
                    target=self._monitor_layer_logs,
                    args=(layer.rid,)
                )
                log_thread.start()
                
                results.append({
                    'rid': layer.rid,
                    'stream_key': stream_key,
                    'url': f"http://{self.mediamtx_url.split(':')[0]}/{stream_key}",
                    'resolution': layer.resolution,
                    'bitrate': layer.bitrate
                })
                
                # 레이어 간 시작 간격
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"레이어 {layer.rid} 시작 실패: {e}")
        
        # 시뮬캐스트 메타데이터 생성
        simulcast_info = {
            'session_key': session_key,
            'layers': results,
            'encoder': self.encoder,
            'timestamp': time.time()
        }
        
        # 메타데이터 저장
        with open(f'/tmp/simulcast_{session_key}.json', 'w') as f:
            json.dump(simulcast_info, f)
        
        logger.info(f"시뮬캐스트 인코딩 시작 완료: {len(results)}개 레이어")
        return simulcast_info
    
    def stop_simulcast(self):
        """모든 시뮬캐스트 스트림 중지"""
        if not self.is_encoding:
            logger.warning("인코딩 중이 아닙니다")
            return False
        
        for rid, info in self.processes.items():
            try:
                process = info['process']
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"레이어 {rid} 정상 종료")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"레이어 {rid} 강제 종료")
            except Exception as e:
                logger.error(f"레이어 {rid} 종료 실패: {e}")
        
        self.processes.clear()
        self.is_encoding = False
        logger.info("모든 시뮬캐스트 스트림 종료")
        return True
    
    def get_layer_stats(self) -> Dict:
        """각 레이어의 실시간 통계"""
        stats = {}
        
        for rid, info in self.processes.items():
            process = info['process']
            if process.poll() is None:  # 실행 중
                try:
                    import psutil
                    p = psutil.Process(process.pid)
                    stats[rid] = {
                        'status': 'active',
                        'cpu_percent': p.cpu_percent(interval=0.1),
                        'memory_mb': p.memory_info().rss / 1024 / 1024,
                        'layer': info['layer'].__dict__
                    }
                except:
                    stats[rid] = {'status': 'active', 'layer': info['layer'].__dict__}
            else:
                stats[rid] = {'status': 'stopped'}
        
        return stats
    
    def _monitor_layer_logs(self, rid: str):
        """레이어별 로그 모니터링"""
        if rid not in self.processes:
            return
        
        process = self.processes[rid]['process']
        layer = self.processes[rid]['layer']
        
        while process.poll() is None:
            try:
                line = process.stderr.readline()
                if line and any(keyword in line for keyword in ['fps=', 'bitrate=', 'speed=']):
                    logger.debug(f"[{rid}:{layer.resolution}] {line.strip()}")
                    
                    # FPS 체크
                    if 'fps=' in line:
                        try:
                            actual_fps = float(line.split('fps=')[1].split()[0])
                            if actual_fps < layer.fps * 0.9:
                                logger.warning(f"레이어 {rid} FPS 저하: {actual_fps}/{layer.fps}")
                        except:
                            pass
            except Exception as e:
                logger.error(f"레이어 {rid} 로그 모니터링 오류: {e}")
                break
    
    def update_bitrates(self, factor: float):
        """모든 레이어의 비트레이트 동적 조절"""
        if not self.is_encoding:
            return False
        
        # 0.1 ~ 1.0 범위로 제한
        factor = max(0.1, min(1.0, factor))
        
        logger.info(f"시뮬캐스트 비트레이트 조절: {factor * 100:.0f}%")
        
        # TODO: 실행 중인 FFmpeg 프로세스의 비트레이트 조절
        # 일부 인코더는 실시간 조절을 지원하지 않으므로
        # 재시작이 필요할 수 있음
        
        return True


class SimulcastWebRTCGenerator:
    """시뮬캐스트 WebRTC SDP 생성기"""
    
    @staticmethod
    def generate_offer_sdp(layers: List[Dict]) -> str:
        """시뮬캐스트를 위한 WebRTC Offer SDP 생성"""
        
        # 기본 SDP 템플릿
        sdp_template = """v=0
o=- 0 0 IN IP4 127.0.0.1
s=Simulcast Stream
t=0 0
a=group:BUNDLE video
a=msid-semantic: WMS stream

m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:4cP9
a=ice-pwd:by1GZGG1lw+040DuA0hXM5Bz
a=ice-options:trickle
a=fingerprint:sha-256 7B:8B:7A:9E:2C:8C:5C:B2:48:AD:91:60:A0:A5:5C:E5:41:5E:84:DB:67:DC:B9:E0:57:AD:B4:FE:A5:50:9C:A1
a=setup:actpass
a=mid:video
a=sendonly
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:96 H264/90000
a=fmtp:96 level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42e01f
"""
        
        # 시뮬캐스트 확장 추가
        simulcast_lines = []
        rids = []
        
        for layer in layers:
            rid = layer.get('rid', 'h')
            simulcast_lines.append(f"a=rid:{rid} send")
            rids.append(rid)
        
        # 시뮬캐스트 지시자
        simulcast_lines.append(f"a=simulcast:send {';'.join(rids)}")
        
        return sdp_template + '\n'.join(simulcast_lines)
    
    @staticmethod
    def parse_answer_sdp(sdp: str) -> Dict:
        """WebRTC Answer SDP 파싱"""
        selected_layers = []
        
        lines = sdp.split('\n')
        for line in lines:
            if line.startswith('a=rid:'):
                # a=rid:h recv
                parts = line.split()
                if len(parts) >= 3 and parts[2] == 'recv':
                    selected_layers.append(parts[0].split(':')[1])
        
        return {
            'selected_layers': selected_layers,
            'simulcast_enabled': len(selected_layers) > 1
        }


def test_simulcast():
    """시뮬캐스트 테스트"""
    encoder = SimulcastEncoder()
    
    # 테스트 NDI 소스
    test_source = "Test Pattern (NDI Proxy)"
    
    # 시뮬캐스트 시작
    result = encoder.start_simulcast(test_source, "test_session")
    
    if result:
        logger.info("시뮬캐스트 스트리밍 URL:")
        for layer in result['layers']:
            logger.info(f"  {layer['rid']}: {layer['url']} ({layer['resolution']})")
        
        try:
            # 30초 테스트
            for i in range(30):
                time.sleep(1)
                stats = encoder.get_layer_stats()
                
                # 통계 출력
                if i % 5 == 0:
                    logger.info("레이어 통계:")
                    for rid, stat in stats.items():
                        if stat['status'] == 'active':
                            logger.info(f"  {rid}: CPU {stat.get('cpu_percent', 0):.1f}%, "
                                      f"Memory {stat.get('memory_mb', 0):.1f}MB")
                
        except KeyboardInterrupt:
            logger.info("사용자 중단")
        
        # 종료
        encoder.stop_simulcast()
    else:
        logger.error("시뮬캐스트 시작 실패")


if __name__ == "__main__":
    test_simulcast()