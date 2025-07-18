# pd_app/ui/__init__.py
"""
UI modules for PD integrated software
"""

# MainWindow - 최적화 및 오류 수정 버전 우선 사용
try:
    from .main_window_optimized_fixed import MainWindowOptimizedFixed as MainWindow
except ImportError:
    try:
        from .main_window_optimized import MainWindowOptimized as MainWindow
    except ImportError:
        from .main_window import MainWindow

# NDIWidget - 최적화된 버전 우선 사용
try:
    from .ndi_widget_optimized import NDIWidgetOptimized as NDIWidget
except ImportError:
    from .ndi_widget import NDIWidget

from .tally_widget import TallyWidget
from .srt_widget import SRTWidget
from .login_widget import LoginWidget

__all__ = ['MainWindow', 'NDIWidget', 'TallyWidget', 'SRTWidget', 'LoginWidget']