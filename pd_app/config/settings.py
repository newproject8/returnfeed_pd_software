# pd_app/config/settings.py
"""
Settings Manager - 애플리케이션 설정 관리
"""

import json
import os
import logging
from .constants import *

logger = logging.getLogger(__name__)

class Settings:
    """설정 관리자"""
    
    def __init__(self):
        self.config_file = SETTINGS_FILE
        self.config = self.default_config()
        self.load_config()
        
    def default_config(self):
        """기본 설정"""
        return {
            'app': {
                'version': APP_VERSION,
                'auto_update': True
            },
            'server': {
                'websocket_url': DEFAULT_WEBSOCKET_URL,
                'media_mtx_server': DEFAULT_MEDIA_MTX_SERVER,
                'media_mtx_srt_port': DEFAULT_MEDIA_MTX_SRT_PORT,
                'media_mtx_api_port': DEFAULT_MEDIA_MTX_API_PORT
            },
            'vmix': {
                'default_ip': DEFAULT_VMIX_IP,
                'default_http_port': DEFAULT_VMIX_HTTP_PORT,
                'default_tcp_port': DEFAULT_VMIX_TCP_PORT
            },
            'streaming': {
                'default_bitrate': DEFAULT_BITRATE,
                'default_fps': DEFAULT_FPS,
                'preset': DEFAULT_PRESET,
                'tune': DEFAULT_TUNE
            },
            'ui': {
                'theme': 'default',
                'window_geometry': None,
                'last_tab': 0
            }
        }
        
    def load_config(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # 기본 설정과 병합
                self._merge_config(self.config, loaded_config)
                
                logger.info("설정 파일 로드 완료")
            else:
                # 디렉토리 생성
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                self.save_config()
                
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            
    def save_config(self):
        """설정 파일 저장"""
        try:
            # 설정 파일 경로가 없거나 빈 문자열이면 기본값 사용
            if not self.config_file or self.config_file == "":
                self.config_file = SETTINGS_FILE
                
            # 디렉토리가 있는 경우만 생성
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            
            # QByteArray 같은 직렬화할 수 없는 객체를 필터링
            serializable_config = self._make_serializable(self.config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_config, f, indent=4, ensure_ascii=False)
                
            logger.info("설정 파일 저장 완료")
            
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
            
    def _make_serializable(self, obj):
        """JSON으로 직렬화 가능한 객체로 변환"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # QByteArray 등 직렬화할 수 없는 객체는 문자열로 변환
            try:
                # PyQt6의 QByteArray인 경우
                if hasattr(obj, 'data'):
                    import base64
                    return base64.b64encode(obj.data()).decode('utf-8')
            except:
                pass
            return str(obj)
            
    def _merge_config(self, base, update):
        """설정 병합"""
        for key, value in update.items():
            if key in base:
                if isinstance(base[key], dict) and isinstance(value, dict):
                    self._merge_config(base[key], value)
                else:
                    base[key] = value
            else:
                base[key] = value
                
    def get(self, key, default=None):
        """설정 값 가져오기"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    def set(self, key, value):
        """설정 값 설정"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        self.save_config()
        
    def get_server_config(self):
        """서버 설정 반환"""
        return self.config.get('server', {})
        
    def get_vmix_config(self):
        """vMix 설정 반환"""
        return self.config.get('vmix', {})
        
    def get_streaming_config(self):
        """스트리밍 설정 반환"""
        return self.config.get('streaming', {})
        
    def get_ui_config(self):
        """UI 설정 반환"""
        return self.config.get('ui', {})
        
    def update_window_geometry(self, geometry):
        """윈도우 위치/크기 업데이트"""
        # QByteArray를 base64 문자열로 변환하여 저장
        if geometry is not None:
            try:
                import base64
                geometry_str = base64.b64encode(geometry.data()).decode('utf-8')
                self.set('ui.window_geometry', geometry_str)
            except Exception as e:
                logger.error(f"윈도우 geometry 저장 실패: {e}")
                self.set('ui.window_geometry', None)
        
    def update_last_tab(self, index):
        """마지막 탭 인덱스 업데이트"""
        self.set('ui.last_tab', index)