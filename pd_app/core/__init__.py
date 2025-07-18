# pd_app/core/__init__.py
"""
Core modules for PD integrated software
"""

# NDI Manager - 최적화된 버전 우선 사용
try:
    from .ndi_manager_optimized import NDIManager
except ImportError:
    from .ndi_manager import NDIManager

from .vmix_manager import VMixManager
from .srt_manager import SRTManager
from .auth_manager import AuthManager

__all__ = ['NDIManager', 'VMixManager', 'SRTManager', 'AuthManager']