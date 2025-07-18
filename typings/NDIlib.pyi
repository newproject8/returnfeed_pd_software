# NDIlib 타입 스텁 파일
"""NDIlib Python bindings type stubs"""

from typing import Any, List, Optional, Tuple

class Source:
    """NDI Source"""
    ndi_name: bytes
    url_address: bytes

class FindInstance:
    """NDI Find Instance"""
    pass

class RecvInstance:
    """NDI Receive Instance"""
    pass

class VideoFrame:
    """NDI Video Frame"""
    data: Any
    xres: int
    yres: int
    line_stride_in_bytes: int
    FourCC: int
    
def initialize() -> bool:
    """Initialize NDI library"""
    ...

def destroy() -> None:
    """Destroy NDI library"""
    ...

def find_create_v2() -> Optional[FindInstance]:
    """Create NDI finder instance"""
    ...

def find_destroy(finder: FindInstance) -> None:
    """Destroy NDI finder instance"""
    ...

def find_wait_for_sources(finder: FindInstance, timeout_ms: int) -> bool:
    """Wait for NDI sources"""
    ...

def find_get_current_sources(finder: FindInstance) -> List[Source]:
    """Get current NDI sources"""
    ...

def recv_create_v3() -> Optional[RecvInstance]:
    """Create NDI receiver instance"""
    ...

def recv_destroy(receiver: RecvInstance) -> None:
    """Destroy NDI receiver instance"""
    ...

def recv_connect(receiver: RecvInstance, source: Source) -> None:
    """Connect to NDI source"""
    ...

def recv_capture_v2(receiver: RecvInstance, timeout_ms: int) -> Tuple[int, Optional[VideoFrame], Any, Any]:
    """Capture NDI frame"""
    ...

def recv_free_video_v2(receiver: RecvInstance, frame: VideoFrame) -> None:
    """Free video frame"""
    ...

# Frame type constants
FRAME_TYPE_NONE: int = 0
FRAME_TYPE_VIDEO: int = 1
FRAME_TYPE_AUDIO: int = 2
FRAME_TYPE_METADATA: int = 3
FRAME_TYPE_ERROR: int = 4

# FourCC constants
FOURCC_UYVY: int
FOURCC_BGRA: int
FOURCC_BGRX: int
FOURCC_RGBA: int
FOURCC_RGBX: int