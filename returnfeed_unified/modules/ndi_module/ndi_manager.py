# ndi_manager.py
import os
import sys
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging

# NDI SDK DLL 경로 설정
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

# Windows에서 DLL 경로 추가
if sys.platform == "win32" and hasattr(os, 'add_dll_directory'):
    try:
        if os.path.isdir(NDI_SDK_DLL_PATH):
            os.add_dll_directory(NDI_SDK_DLL_PATH)
            print(f"Added to DLL search path: {NDI_SDK_DLL_PATH}")
    except Exception as e:
        print(f"Warning: Failed to add NDI SDK DLL path: {e}")

try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    ndi = None


class NDISource:
    """NDI 소스 정보"""
    def __init__(self, name: str, address: str = "", ndi_source_obj=None):
        self.name = name
        self.address = address
        self.ndi_source_obj = ndi_source_obj  # 실제 NDI 소스 객체 저장
        
    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "address": self.address}


class NDIManager(QObject):
    """NDI 통신 관리자"""
    
    # 시그널
    sources_updated = pyqtSignal(list)  # List[NDISource]
    status_changed = pyqtSignal(str, str)  # status, message
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.logger = logging.getLogger("NDIManager")
        self.is_initialized = False
        self.finder = None
        self.sources = []
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self._scan_sources)
        
    def initialize(self) -> bool:
        """NDI 라이브러리 초기화"""
        if not NDI_AVAILABLE:
            error_msg = "NDI library not available. Please install NDI SDK."
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
        if self.is_initialized:
            self.logger.info("NDI already initialized")
            return True
            
        try:
            if not ndi.initialize():
                error_msg = "Failed to initialize NDI library"
                self.logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
                
            self.is_initialized = True
            self.logger.info("NDI library initialized successfully")
            self.status_changed.emit("initialized", "NDI 초기화 성공")
            return True
            
        except Exception as e:
            error_msg = f"NDI initialization error: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
    def start_discovery(self) -> bool:
        """NDI 소스 검색 시작"""
        if not self.is_initialized:
            self.logger.error("NDI not initialized")
            return False
            
        try:
            # NDI Finder 생성 - 다양한 함수명 시도
            finder_functions = ['find_create_v2', 'find_create', 'Find_create_v2', 'Find_create']
            
            for func_name in finder_functions:
                if hasattr(ndi, func_name):
                    try:
                        func = getattr(ndi, func_name)
                        self.finder = func()
                        if self.finder:
                            self.logger.info(f"NDI finder created using {func_name}")
                            break
                    except Exception as e:
                        self.logger.warning(f"Failed to create finder with {func_name}: {e}")
                        continue
            
            if not self.finder:
                self.logger.error("Failed to create NDI finder with any available function")
                return False
                
            # 주기적 스캔 시작 (2초마다)
            self.scan_timer.start(2000)
            self.status_changed.emit("discovering", "NDI 소스 검색 중...")
            
            # 초기 스캔
            self._scan_sources()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start discovery: {e}")
            return False
            
    def stop_discovery(self) -> None:
        """NDI 소스 검색 중지"""
        self.scan_timer.stop()
        
        if self.finder:
            try:
                # 다양한 함수명 시도
                destroy_functions = ['find_destroy', 'Find_destroy']
                for func_name in destroy_functions:
                    if hasattr(ndi, func_name):
                        try:
                            func = getattr(ndi, func_name)
                            func(self.finder)
                            self.logger.info(f"NDI finder destroyed using {func_name}")
                            break
                        except Exception as e:
                            self.logger.warning(f"Failed to destroy finder with {func_name}: {e}")
                            continue
            except Exception as e:
                self.logger.warning(f"Error destroying finder: {e}")
            finally:
                self.finder = None
            
        self.status_changed.emit("stopped", "NDI 검색 중지됨")
        
    def _scan_sources(self):
        """NDI 소스 스캔"""
        if not self.finder:
            return
            
        try:
            # NDI 소스 찾기 - 다양한 함수명 시도
            source_functions = [
                'find_get_current_sources', 'Find_get_current_sources',
                'find_get_sources', 'Find_get_sources',
                'get_current_sources', 'get_sources'
            ]
            
            sources_raw = None
            for func_name in source_functions:
                if hasattr(ndi, func_name):
                    try:
                        func = getattr(ndi, func_name)
                        sources_raw = func(self.finder)
                        if sources_raw is not None:
                            self.logger.debug(f"Got sources using {func_name}")
                            break
                    except Exception as e:
                        self.logger.warning(f"Failed to get sources with {func_name}: {e}")
                        continue
            
            # 소스 리스트 업데이트
            new_sources = []
            if sources_raw:
                for source in sources_raw:
                    try:
                        # 소스 정보 추출 - 다양한 속성명 시도
                        name = ""
                        address = ""
                        
                        # 이름 추출
                        name_attrs = ['name', 'ndi_name', 'source_name']
                        for attr in name_attrs:
                            if hasattr(source, attr):
                                name = getattr(source, attr)
                                if name:
                                    break
                        
                        # 주소 추출
                        addr_attrs = ['address', 'url_address', 'ip_address']
                        for attr in addr_attrs:
                            if hasattr(source, attr):
                                address = getattr(source, attr)
                                break
                        
                        # 문자열로 변환된 경우 처리
                        if not name and hasattr(source, '__str__'):
                            name = str(source)
                        
                        if name:
                            new_sources.append(NDISource(name, address, ndi_source_obj=source))
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing source: {e}")
                        continue
                        
            # 변경사항이 있으면 시그널 발송
            if len(new_sources) != len(self.sources) or any(
                ns.name != os.name for ns, os in zip(new_sources, self.sources)
            ):
                self.sources = new_sources
                self.sources_updated.emit([s.to_dict() for s in self.sources])
                self.logger.info(f"Found {len(self.sources)} NDI sources")
                
        except Exception as e:
            self.logger.error(f"Error scanning sources: {e}")
            
    def cleanup(self) -> None:
        """리소스 정리"""
        self.stop_discovery()
        
        if self.is_initialized and NDI_AVAILABLE:
            try:
                ndi.destroy()
                self.logger.info("NDI library deinitialized")
            except Exception as e:
                self.logger.warning(f"Error during NDI cleanup: {e}")
                
        self.is_initialized = False
        
    def get_sources(self) -> List[Dict[str, str]]:
        """현재 발견된 소스 목록 반환"""
        return [s.to_dict() for s in self.sources]
    
    def get_source_names(self) -> List[str]:
        """현재 발견된 NDI 소스 이름 목록 반환"""
        return [s.name for s in self.sources]
    
    def get_source_object(self, source_name: str):
        """이름으로 NDI 소스 객체 찾기"""
        for source in self.sources:
            if source.name == source_name:
                return source.ndi_source_obj
        return None