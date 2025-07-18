# modules/__init__.py
from typing import Protocol, Dict, Any, runtime_checkable
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget
from typing import Optional
import logging

__all__ = ['ModuleProtocol', 'BaseModule', 'ModuleStatus', 'ModuleManager']


class ModuleStatus:
    """모듈 상태 정의"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


@runtime_checkable
class ModuleProtocol(Protocol):
    """모듈이 구현해야 할 프로토콜 (구조적 타이핑)"""
    
    name: str
    status: str
    
    def initialize(self) -> bool:
        """모듈 초기화. 성공 시 True 반환"""
        ...
        
    def start(self) -> bool:
        """모듈 시작. 성공 시 True 반환"""
        ...
        
    def stop(self) -> bool:
        """모듈 정지. 성공 시 True 반환"""
        ...
        
    def cleanup(self) -> None:
        """리소스 정리"""
        ...
        
    def get_widget(self) -> QWidget:
        """모듈의 UI 위젯 반환"""
        ...
        
    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 반환"""
        ...
        
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 적용. 성공 시 True 반환"""
        ...


class BaseModule(QObject):
    """모든 모듈이 상속받을 기본 클래스 (QObject 기반)"""
    
    # 공통 시그널
    status_changed = pyqtSignal(str, str)  # status, message
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    
    def __init__(self, name: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.name = name
        self.status = ModuleStatus.IDLE
        self.logger = logging.getLogger(f"module.{name}")
        
    def set_status(self, status: str, message: str = "") -> None:
        """모듈 상태 변경"""
        self.status = status
        self.status_changed.emit(status, message)
        self.logger.info(f"Status changed to {status}: {message}")
        
    def emit_error(self, error_type: str, message: str) -> None:
        """에러 발생 시그널 발송"""
        self.error_occurred.emit(error_type, message)
        self.logger.error(f"{error_type}: {message}")
        self.set_status(ModuleStatus.ERROR, message)
    
    # 서브클래스에서 구현해야 할 메서드들 (NotImplementedError 사용)
    def initialize(self) -> bool:
        """모듈 초기화. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement initialize()")
        
    def start(self) -> bool:
        """모듈 시작. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement start()")
        
    def stop(self) -> bool:
        """모듈 정지. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement stop()")
        
    def cleanup(self) -> None:
        """리소스 정리. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement cleanup()")
        
    def get_widget(self) -> QWidget:
        """모듈의 UI 위젯 반환. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement get_widget()")
        
    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 반환. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement get_settings()")
        
    def apply_settings(self, settings: Dict[str, Any]) -> bool:
        """설정 적용. 서브클래스에서 구현 필요"""
        raise NotImplementedError("Subclass must implement apply_settings()")


class ModuleManager:
    """모듈 관리자 - 모든 모듈의 생명주기 관리"""
    
    def __init__(self):
        self.modules: Dict[str, ModuleProtocol] = {}
        self.logger = logging.getLogger("ModuleManager")
        
    def register_module(self, module: ModuleProtocol) -> bool:
        """모듈 등록"""
        if not hasattr(module, 'name'):
            self.logger.error("Module must have a 'name' attribute")
            return False
            
        if module.name in self.modules:
            self.logger.error(f"Module {module.name} already registered")
            return False
            
        self.modules[module.name] = module
        self.logger.info(f"Module {module.name} registered")
        return True
        
    def initialize_all(self) -> bool:
        """모든 모듈 초기화"""
        for name, module in self.modules.items():
            try:
                if not module.initialize():
                    self.logger.error(f"Failed to initialize module {name}")
                    return False
            except Exception as e:
                self.logger.error(f"Exception during initialization of {name}: {e}")
                return False
        return True
        
    def start_all(self) -> bool:
        """모든 모듈 시작"""
        for name, module in self.modules.items():
            try:
                if not module.start():
                    self.logger.error(f"Failed to start module {name}")
                    return False
            except Exception as e:
                self.logger.error(f"Exception during start of {name}: {e}")
                return False
        return True
        
    def stop_all(self) -> None:
        """모든 모듈 정지"""
        for name, module in self.modules.items():
            try:
                module.stop()
            except Exception as e:
                self.logger.error(f"Exception during stop of {name}: {e}")
                
    def cleanup_all(self) -> None:
        """모든 모듈 정리"""
        for name, module in self.modules.items():
            try:
                module.cleanup()
            except Exception as e:
                self.logger.error(f"Exception during cleanup of {name}: {e}")
                
    def get_module(self, name: str) -> Optional[ModuleProtocol]:
        """특정 모듈 반환"""
        return self.modules.get(name)