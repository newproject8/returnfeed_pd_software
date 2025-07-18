#!/usr/bin/env python3
"""
GPU 벤더 독립적 H.264 인코더 감지 및 선택
다양한 GPU 제조사 지원: NVIDIA, Intel, AMD
"""

import subprocess
import platform
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPUEncoderDetector:
    """GPU 벤더를 감지하고 최적의 H.264 인코더를 선택"""
    
    def __init__(self):
        self.system = platform.system()
        self.available_encoders = []
        self.selected_encoder = None
        
    def check_encoder_support(self, encoder_name):
        """FFmpeg에서 특정 인코더 지원 여부 확인"""
        try:
            cmd = ['ffmpeg', '-hide_banner', '-encoders']
            result = subprocess.run(cmd, capture_output=True, text=True)
            return encoder_name in result.stdout
        except Exception as e:
            logger.error(f"FFmpeg 인코더 확인 실패: {e}")
            return False
    
    def detect_nvidia_gpu(self):
        """NVIDIA GPU 감지"""
        try:
            # nvidia-smi 명령 실행
            result = subprocess.run(['nvidia-smi'], capture_output=True)
            if result.returncode == 0:
                logger.info("✓ NVIDIA GPU 감지됨")
                if self.check_encoder_support('h264_nvenc'):
                    return 'h264_nvenc'
        except FileNotFoundError:
            pass
        return None
    
    def detect_intel_gpu(self):
        """Intel GPU (Quick Sync) 감지"""
        try:
            if self.system == "Linux":
                # Intel GPU 디바이스 확인
                if os.path.exists('/dev/dri/renderD128'):
                    # i915 드라이버 확인
                    with open('/proc/modules', 'r') as f:
                        if 'i915' in f.read():
                            logger.info("✓ Intel GPU 감지됨")
                            if self.check_encoder_support('h264_qsv'):
                                return 'h264_qsv'
            elif self.system == "Windows":
                # Windows에서 Intel GPU 확인
                cmd = ['wmic', 'path', 'win32_VideoController', 'get', 'name']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if 'Intel' in result.stdout:
                    logger.info("✓ Intel GPU 감지됨")
                    if self.check_encoder_support('h264_qsv'):
                        return 'h264_qsv'
        except Exception as e:
            logger.debug(f"Intel GPU 감지 중 오류: {e}")
        return None
    
    def detect_amd_gpu(self):
        """AMD GPU 감지"""
        try:
            if self.system == "Linux":
                # AMD GPU 드라이버 확인
                with open('/proc/modules', 'r') as f:
                    modules = f.read()
                    if 'amdgpu' in modules or 'radeon' in modules:
                        logger.info("✓ AMD GPU 감지됨")
                        if self.check_encoder_support('h264_amf'):
                            return 'h264_amf'
                        elif self.check_encoder_support('h264_vaapi'):
                            # Linux에서는 VAAPI 사용
                            return 'h264_vaapi'
            elif self.system == "Windows":
                cmd = ['wmic', 'path', 'win32_VideoController', 'get', 'name']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if 'AMD' in result.stdout or 'Radeon' in result.stdout:
                    logger.info("✓ AMD GPU 감지됨")
                    if self.check_encoder_support('h264_amf'):
                        return 'h264_amf'
        except Exception as e:
            logger.debug(f"AMD GPU 감지 중 오류: {e}")
        return None
    
    def detect_apple_silicon(self):
        """Apple Silicon (M1/M2) 감지"""
        try:
            if self.system == "Darwin":
                # macOS에서 VideoToolbox 지원 확인
                result = subprocess.run(['sysctl', '-n', 'hw.optional.arm64'], 
                                      capture_output=True, text=True)
                if result.stdout.strip() == '1':
                    logger.info("✓ Apple Silicon 감지됨")
                    if self.check_encoder_support('h264_videotoolbox'):
                        return 'h264_videotoolbox'
        except Exception:
            pass
        return None
    
    def detect_best_encoder(self):
        """시스템에서 사용 가능한 최적의 인코더 감지"""
        logger.info("GPU 인코더 감지 시작...")
        
        # 우선순위에 따라 확인
        detectors = [
            ('NVIDIA', self.detect_nvidia_gpu),
            ('Intel', self.detect_intel_gpu),
            ('AMD', self.detect_amd_gpu),
            ('Apple', self.detect_apple_silicon),
        ]
        
        for vendor, detector in detectors:
            encoder = detector()
            if encoder:
                self.selected_encoder = encoder
                self.available_encoders.append((vendor, encoder))
                logger.info(f"선택된 인코더: {encoder} ({vendor})")
                return encoder
        
        # GPU 인코더를 찾지 못한 경우 CPU 인코더 사용
        if self.check_encoder_support('libx264'):
            logger.warning("GPU 인코더를 찾을 수 없음. CPU 인코더 사용")
            self.selected_encoder = 'libx264'
            return 'libx264'
        
        raise Exception("사용 가능한 H.264 인코더가 없습니다")
    
    def get_encoder_params(self, encoder, resolution="640x360", fps=60, bitrate="1M"):
        """인코더별 최적화된 파라미터 반환"""
        base_params = [
            '-s', resolution,
            '-r', str(fps),
            '-c:v', encoder,
            '-profile:v', 'baseline',
            '-level', '4.1',  # 60fps 지원
            '-b:v', bitrate,
            '-maxrate', bitrate,
            '-bufsize', '2M',
            '-g', str(fps),  # 1초 GOP
            '-bf', '0',  # B-프레임 없음
        ]
        
        # 인코더별 특수 설정
        if encoder == 'h264_nvenc':
            base_params.extend([
                '-preset', 'llhq',  # Low Latency High Quality
                '-rc:v', 'cbr',
                '-zerolatency', '1',
                '-forced-idr', '1'
            ])
        elif encoder == 'h264_qsv':
            base_params.extend([
                '-preset', 'veryfast',
                '-look_ahead', '0',
                '-async_depth', '1',
                '-low_delay_brc', '1'
            ])
        elif encoder == 'h264_amf':
            base_params.extend([
                '-usage', 'ultralowlatency',
                '-rc', 'cbr',
                '-preanalysis', 'false'
            ])
        elif encoder == 'h264_vaapi':
            base_params.extend([
                '-vaapi_device', '/dev/dri/renderD128',
                '-rc_mode', 'CBR',
                '-compression_level', '1'
            ])
        elif encoder == 'h264_videotoolbox':
            base_params.extend([
                '-realtime', '1',
                '-allow_sw', '1'  # 필요시 소프트웨어 폴백
            ])
        elif encoder == 'libx264':
            base_params.extend([
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-x264opts', 'keyint=60:min-keyint=60:no-scenecut'
            ])
        
        return base_params
    
    def get_system_info(self):
        """시스템 정보 수집"""
        info = {
            'platform': self.system,
            'selected_encoder': self.selected_encoder,
            'available_encoders': self.available_encoders,
            'cpu_count': os.cpu_count()
        }
        
        # GPU 정보 추가 수집
        if self.system == "Linux":
            try:
                # lspci로 GPU 정보 수집
                result = subprocess.run(['lspci', '-nn'], 
                                      capture_output=True, text=True)
                vga_lines = [line for line in result.stdout.split('\n') 
                           if 'VGA' in line or '3D' in line]
                info['gpu_devices'] = vga_lines
            except:
                pass
                
        return info


def test_encoder_performance(encoder, params):
    """인코더 성능 테스트"""
    logger.info(f"\n{encoder} 인코더 성능 테스트 시작...")
    
    # 테스트 비디오 생성
    test_cmd = [
        'ffmpeg', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=60',
        '-t', '5'  # 5초 테스트
    ] + params + [
        '-f', 'null', '-'
    ]
    
    try:
        start_time = subprocess.run(['date', '+%s.%N'], 
                                  capture_output=True, text=True).stdout.strip()
        
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        end_time = subprocess.run(['date', '+%s.%N'], 
                                capture_output=True, text=True).stdout.strip()
        
        if result.returncode == 0:
            # 인코딩 속도 분석
            for line in result.stderr.split('\n'):
                if 'fps=' in line:
                    logger.info(f"인코딩 성능: {line.strip()}")
            
            elapsed = float(end_time) - float(start_time)
            logger.info(f"테스트 완료 시간: {elapsed:.2f}초")
            return True
        else:
            logger.error(f"테스트 실패: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"테스트 중 오류: {e}")
        return False


def main():
    """메인 실행 함수"""
    detector = GPUEncoderDetector()
    
    # 최적 인코더 감지
    try:
        encoder = detector.detect_best_encoder()
        logger.info(f"\n=== 최종 선택된 인코더: {encoder} ===")
        
        # 시스템 정보 출력
        info = detector.get_system_info()
        logger.info(f"플랫폼: {info['platform']}")
        logger.info(f"CPU 코어: {info['cpu_count']}")
        
        # 인코더 파라미터 생성
        params = detector.get_encoder_params(encoder)
        logger.info(f"\n인코더 파라미터:")
        logger.info(' '.join(params))
        
        # 성능 테스트
        if '--test' in sys.argv:
            test_encoder_performance(encoder, params)
        
        # 결과를 파일로 저장 (다른 스크립트에서 사용)
        with open('/tmp/selected_encoder.txt', 'w') as f:
            f.write(f"{encoder}\n")
            f.write(' '.join(params))
        
        return encoder
        
    except Exception as e:
        logger.error(f"인코더 감지 실패: {e}")
        return None


if __name__ == "__main__":
    main()