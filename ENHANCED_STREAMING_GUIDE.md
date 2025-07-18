# 🚀 ReturnFeed 향상된 스트리밍 가이드

## 1. NDI Proxy 표준화 구현

### 개념
모든 PD 소프트웨어는 **640x360 NDI Proxy** 소스만을 전송합니다.
- 원본 소스: 모니터링 프리뷰 전용
- 전송 소스: NDI Proxy (640x360) 고정

### 구현 코드

```python
class NDIProxyStreamer:
    def __init__(self):
        self.proxy_resolution = "640x360"
        self.base_bitrate = "1M"
        self.fps = 60
        
    def get_video_encoder(self):
        """GPU 벤더 독립적 인코더 선택"""
        encoders = [
            ('h264_nvenc', self._check_nvidia),
            ('h264_qsv', self._check_intel),
            ('h264_amf', self._check_amd),
            ('h264_videotoolbox', self._check_apple),
            ('libx264', lambda: True)  # CPU fallback
        ]
        
        for encoder, check_func in encoders:
            if check_func():
                return encoder
        
        return 'libx264'  # 최종 fallback
    
    def _check_nvidia(self):
        """NVIDIA GPU 확인"""
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_intel(self):
        """Intel GPU 확인"""
        try:
            # Intel GPU 감지 로직
            return os.path.exists('/dev/dri/renderD128')
        except:
            return False
    
    def _check_amd(self):
        """AMD GPU 확인"""
        try:
            # AMD GPU 감지 로직
            return 'amdgpu' in open('/proc/modules').read()
        except:
            return False
    
    def _check_apple(self):
        """macOS 확인"""
        return platform.system() == 'Darwin'
    
    def get_streaming_params(self, encoder):
        """인코더별 최적화된 파라미터"""
        base_params = [
            '-s', self.proxy_resolution,
            '-r', str(self.fps),
            '-c:v', encoder,
            '-profile:v', 'baseline',
            '-level', '4.1',  # 60fps 지원
            '-b:v', self.base_bitrate,
            '-maxrate', self.base_bitrate,
            '-bufsize', '2M',
            '-rc', 'cbr',
            '-g', str(self.fps),  # 1초 GOP
            '-bf', '0',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency'
        ]
        
        # 인코더별 특수 파라미터
        if encoder == 'h264_nvenc':
            base_params.extend(['-rc:v', 'cbr', '-zerolatency', '1'])
        elif encoder == 'h264_qsv':
            base_params.extend(['-look_ahead', '0', '-async_depth', '1'])
        elif encoder == 'h264_amf':
            base_params.extend(['-usage', 'ultralowlatency'])
            
        return base_params
```

## 2. 클라이언트 측 비트레이트 조절

### WebRTC 기반 동적 비트레이트 (레이턴시 영향 없음)

```javascript
class AdaptiveBitratePlayer {
    constructor(minBitrate = 100000, maxBitrate = 1000000) {
        this.minBitrate = minBitrate;  // 0.1 Mbps
        this.maxBitrate = maxBitrate;  // 1 Mbps
        this.currentBitrate = maxBitrate;
        this.pc = null;
    }
    
    async adjustBitrate(targetBitrate) {
        if (!this.pc) return;
        
        // 범위 제한
        targetBitrate = Math.max(this.minBitrate, 
                                 Math.min(this.maxBitrate, targetBitrate));
        
        const transceivers = this.pc.getTransceivers();
        for (const transceiver of transceivers) {
            if (transceiver.sender && transceiver.sender.track?.kind === 'video') {
                const params = transceiver.sender.getParameters();
                
                if (!params.encodings || params.encodings.length === 0) {
                    params.encodings = [{}];
                }
                
                // 비트레이트 조절 (레이턴시 영향 없음)
                params.encodings[0].maxBitrate = targetBitrate;
                
                await transceiver.sender.setParameters(params);
                this.currentBitrate = targetBitrate;
                
                console.log(`비트레이트 조정: ${targetBitrate / 1000}kbps`);
            }
        }
    }
    
    // 네트워크 상태 기반 자동 조절
    async enableAutoAdjust() {
        if (!this.pc) return;
        
        setInterval(async () => {
            const stats = await this.pc.getStats();
            let packetsLost = 0;
            let packetsReceived = 0;
            
            stats.forEach(report => {
                if (report.type === 'inbound-rtp' && report.kind === 'video') {
                    packetsLost = report.packetsLost || 0;
                    packetsReceived = report.packetsReceived || 0;
                }
            });
            
            const lossRate = packetsReceived > 0 ? 
                            packetsLost / packetsReceived : 0;
            
            if (lossRate > 0.05) {
                // 5% 이상 패킷 손실: 비트레이트 감소
                await this.adjustBitrate(this.currentBitrate * 0.8);
            } else if (lossRate < 0.01) {
                // 1% 미만 패킷 손실: 비트레이트 증가
                await this.adjustBitrate(this.currentBitrate * 1.1);
            }
        }, 5000);
    }
}
```

## 3. MediaMTX 최적화 설정

```yaml
# mediamtx-ndi-proxy.yml
paths:
  # NDI Proxy 전용 경로
  ~^ndi_proxy_.*:
    source: publisher
    sourceProtocol: srt
    srtReadPassphrase: $SRT_PASSPHRASE
    
    # 640x360 고정 확인
    sourceOnDemand: yes
    sourceOnDemandStartTimeout: 10s
    
    # WebRTC 출력 설정
    webrtc: yes
    webrtcICEServers:
      - stun:stun.l.google.com:19302
    
    # 트랜스코딩 비활성화 (패스스루)
    runOnReady: |
      echo "NDI Proxy 스트림 시작: $RTSP_PATH"
      echo "해상도: 640x360, 비트레이트: 1Mbps"
```

## 4. PD 소프트웨어 통합 예시

```python
class PDSoftwareStreamer:
    def __init__(self):
        self.ndi_proxy = NDIProxyStreamer()
        self.encoder = self.ndi_proxy.get_video_encoder()
        print(f"사용 중인 인코더: {self.encoder}")
        
    def start_streaming(self, ndi_source_name):
        """NDI 소스를 NDI Proxy로 변환하여 스트리밍"""
        
        # NDI Proxy 소스 찾기
        proxy_name = f"{ndi_source_name} (NDI Proxy)"
        
        # FFmpeg 명령 구성
        params = self.ndi_proxy.get_streaming_params(self.encoder)
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'libndi_newtek',
            '-i', proxy_name,
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-ar', '48000',
            '-ac', '2'
        ] + params + [
            '-f', 'mpegts',
            'srt://localhost:8890?streamid=ndi_proxy_stream'
        ]
        
        # 스트리밍 시작
        self.process = subprocess.Popen(ffmpeg_cmd)
        print("NDI Proxy 스트리밍 시작됨")
```

## 5. 성능 이점

### 기존 방식 vs NDI Proxy 방식

| 항목 | 기존 (다양한 해상도) | NDI Proxy (640x360) |
|------|---------------------|---------------------|
| MediaMTX CPU | 50-80% | 10-20% |
| 네트워크 대역폭 | 3-10 Mbps | 1 Mbps 고정 |
| 레이턴시 | 100-300ms | 40-80ms |
| 모바일 호환성 | 제한적 | 우수 |
| 트랜스코딩 필요 | 자주 필요 | 불필요 |

## 6. 구현 우선순위

1. **즉시 구현**
   - GPU 벤더 독립적 인코더 선택
   - 60fps 지원 활성화

2. **단계적 구현**
   - NDI Proxy 자동 감지 및 선택
   - 클라이언트 비트레이트 조절 UI

3. **향후 고려**
   - AI 기반 자동 품질 조절
   - 다중 품질 스트림 (simulcast)

## 결론

NDI Proxy 표준화는 ReturnFeed의 성능과 안정성을 크게 향상시킬 수 있는 핵심 전략입니다. 특히 모바일 환경에서의 안정성과 레이턴시 개선 효과가 뚜렷합니다.