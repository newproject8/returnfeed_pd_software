"""
Material Design Icons for Professional UI
Using Unicode symbols and icon fonts
"""

# Material Design Icon Unicode symbols
ICONS = {
    # Connection Status
    'wifi_on': '📶',  # Will be replaced with Material Icon
    'wifi_off': '📵',
    'connected': '🔗',
    'disconnected': '🔌',
    
    # Media Controls
    'play': '▶',
    'pause': '⏸',
    'stop': '⏹',
    'record': '⏺',
    
    # Status
    'check_circle': '✓',
    'error': '⚠',
    'warning': '⚡',
    'info': 'ⓘ',
    
    # UI Elements  
    'settings': '⚙',
    'fullscreen': '⛶',
    'exit_fullscreen': '⛶',
    'menu': '☰',
    'close': '✕',
    
    # Account
    'person': '👤',
    'lock': '🔒',
    'login': '→',
    'logout': '←',
    
    # Broadcast
    'videocam': '📹',
    'videocam_off': '📷',
    'mic': '🎤',
    'mic_off': '🔇',
    
    # Tally
    'pgm': '●',
    'pvw': '●',
    'standby': '○',
}

# Professional color scheme (Adobe Premiere style)
PREMIERE_COLORS = {
    'bg_darkest': '#1a1a1a',
    'bg_dark': '#232323',
    'bg_medium': '#2d2d2d',
    'bg_light': '#3a3a3a',
    'bg_lighter': '#474747',
    
    'border': '#4a4a4a',
    'border_light': '#5a5a5a',
    
    'text_primary': '#e8e8e8',
    'text_secondary': '#b8b8b8',
    'text_disabled': '#6a6a6a',
    
    'accent_blue': '#4d9bff',
    'accent_blue_hover': '#6aabff',
    'accent_blue_pressed': '#3a8aee',
    
    'pgm_red': '#ff4444',
    'pvw_green': '#44ff44',
    'standby_gray': '#666666',
    
    'success': '#52c41a',
    'success_hover': '#73d13d',
    'warning': '#faad14',
    'error': '#ff4d4f',
    'info': '#1890ff',
    'info_hover': '#40a9ff',
    
    # Card and button colors
    'card_bg': '#2d2d2d',
    'button_bg': '#3a3a3a',
    'button_hover': '#474747',
}

def get_icon(name: str) -> str:
    """Get icon by name"""
    return ICONS.get(name, '?')

def get_color(name: str) -> str:
    """Get color by name"""
    return PREMIERE_COLORS.get(name, '#ffffff')