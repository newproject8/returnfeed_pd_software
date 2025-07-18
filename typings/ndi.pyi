# ndi 타입 스텁 파일
"""NDI Python bindings type stubs (alternative import)"""

from typing import Any, List, Optional, Tuple

# ndi 모듈의 함수들 (NDIlib과 동일한 인터페이스)
def initialize() -> bool:
    """Initialize NDI library"""
    ...

def destroy() -> None:
    """Destroy NDI library"""
    ...

def find_create_v2() -> Optional[Any]:
    """Create NDI finder instance"""
    ...

def find_destroy(finder: Any) -> None:
    """Destroy NDI finder instance"""
    ...

def find_wait_for_sources(finder: Any, timeout_ms: int) -> bool:
    """Wait for NDI sources"""
    ...

def find_get_current_sources(finder: Any) -> List[Any]:
    """Get current NDI sources"""
    ...

def recv_create_v3() -> Optional[Any]:
    """Create NDI receiver instance"""
    ...

def recv_destroy(receiver: Any) -> None:
    """Destroy NDI receiver instance"""
    ...

def recv_connect(receiver: Any, source: Any) -> None:
    """Connect to NDI source"""
    ...

def recv_capture_v2(receiver: Any, timeout_ms: int) -> Tuple[int, Optional[Any], Any, Any]:
    """Capture NDI frame"""
    ...

def recv_free_video_v2(receiver: Any, frame: Any) -> None:
    """Free video frame"""
    ...

# 상수들
FRAME_TYPE_NONE: int = 0
FRAME_TYPE_VIDEO: int = 1
FRAME_TYPE_AUDIO: int = 2
FRAME_TYPE_METADATA: int = 3
FRAME_TYPE_ERROR: int = 4