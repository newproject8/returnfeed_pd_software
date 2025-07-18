"""
Professional Dark Theme - Adobe Premiere CC Inspired
Using Gmarket Sans font for Korean text
"""

from ..styles.icons import PREMIERE_COLORS

# Extended color palette
COLORS = PREMIERE_COLORS

# Component Styles - Professional Broadcast Software
STYLES = {
    'QMainWindow': f"""
        QMainWindow {{
            background-color: {COLORS['bg_darkest']};
            color: {COLORS['text_primary']};
        }}
    """,
    
    'CommandBar': f"""
        QFrame#CommandBar {{
            background-color: {COLORS['bg_dark']};
            border: none;
        }}
        QFrame#TopFrame {{
            background-color: {COLORS['bg_darkest']};
            border: none;
        }}
        QFrame#BottomFrame {{
            background-color: {COLORS['bg_dark']};
            border: none;
        }}
        QFrame#HorizontalSeparator {{
            background-color: {COLORS['border']};
        }}
    """,
    
    'LoginFrame': f"""
        QFrame#LoginFrame {{
            background-color: transparent;
        }}
        QLineEdit#LoginInput {{
            background-color: {COLORS['bg_medium']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 5px 10px;
            color: {COLORS['text_primary']};
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 12px;
            height: 36px;
        }}
        QLineEdit#LoginInput:focus {{
            border-color: {COLORS['accent_blue']};
            background-color: {COLORS['bg_light']};
        }}
        QPushButton#LoginButton, QPushButton#SignupButton {{
            background-color: {COLORS['bg_medium']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 5px 15px;
            color: {COLORS['text_primary']};
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 12px;
            font-weight: 500;
            min-width: 60px;
        }}
        QPushButton#LoginButton:hover, QPushButton#SignupButton:hover {{
            background-color: {COLORS['bg_light']};
            border-color: {COLORS['border_light']};
        }}
        QPushButton#LoginButton:pressed, QPushButton#SignupButton:pressed {{
            background-color: {COLORS['bg_lighter']};
        }}
    """,
    
    'StatusIndicator': f"""
        QLabel#StatusIndicator {{
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
            padding: 3px 10px;
            min-height: 20px;
        }}
    """,
    
    'TallyDisplay': f"""
        QFrame#TallyDisplay {{
            background-color: {COLORS['bg_medium']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            min-height: 26px;
            max-height: 30px;
        }}
        QLabel#TallyPGM, QLabel#TallyPVW {{
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
            font-weight: 300;
            padding: 0px;
        }}
    """,
    
    'VideoDisplay': f"""
        QFrame#VideoDisplay {{
            background-color: #000000;
            border: 2px solid {COLORS['bg_dark']};
            border-radius: 4px;
        }}
        QFrame#VideoDisplay:hover {{
            border-color: {COLORS['border']};
        }}
    """,
    
    'ControlPanel': f"""
        QFrame#ControlPanel {{
            background-color: {COLORS['bg_dark']};
            border: none;
            border-top: 1px solid {COLORS['border']};
        }}
    """,
    
    'QPushButton': f"""
        QPushButton {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 8px 16px;
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
            font-weight: 500;
            min-width: 80px;
            height: 36px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: {COLORS['bg_light']};
            border-color: {COLORS['border_light']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['bg_lighter']};
        }}
        QPushButton:disabled {{
            background-color: {COLORS['bg_dark']};
            color: {COLORS['text_disabled']};
            border-color: {COLORS['bg_medium']};
        }}
        QPushButton#PrimaryButton {{
            background-color: {COLORS['accent_blue']};
            border-color: {COLORS['accent_blue']};
            color: #ffffff;
        }}
        QPushButton#PrimaryButton:hover {{
            background-color: {COLORS['accent_blue_hover']};
            border-color: {COLORS['accent_blue_hover']};
        }}
        QPushButton#PrimaryButton:pressed {{
            background-color: {COLORS['accent_blue_pressed']};
            border-color: {COLORS['accent_blue_pressed']};
        }}
        QPushButton#PrimaryButton:disabled {{
            background-color: {COLORS['bg_medium']};
            border-color: {COLORS['bg_medium']};
            color: {COLORS['text_disabled']};
        }}
    """,
    
    'QComboBox': f"""
        QComboBox {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 6px 12px;
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
            min-width: 150px;
            height: 36px;
        }}
        QComboBox:hover {{
            border-color: {COLORS['border_light']};
            background-color: {COLORS['bg_light']};
        }}
        QComboBox:focus {{
            border-color: {COLORS['accent_blue']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {COLORS['text_secondary']};
            margin-right: 8px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            selection-background-color: {COLORS['accent_blue']};
            selection-color: #ffffff;
            padding: 4px;
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 4px;
            min-height: 25px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {COLORS['bg_light']};
        }}
    """,
    
    'QLabel': f"""
        QLabel {{
            color: {COLORS['text_primary']};
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
        }}
        QLabel#Title {{
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        }}
        QLabel#Subtitle {{
            font-size: 14px;
            color: {COLORS['text_secondary']};
        }}
        QLabel#StatusText {{
            font-size: 12px;
            color: {COLORS['text_secondary']};
        }}
    """,
    
    'TallyIndicator': f"""
        QFrame#TallyIndicator {{
            background-color: {COLORS['bg_medium']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 8px;
        }}
        QFrame#TallyIndicator[tally="pgm"] {{
            border-color: {COLORS['pgm_red']};
            background-color: rgba(255, 68, 68, 0.15);
        }}
        QFrame#TallyIndicator[tally="pvw"] {{
            border-color: {COLORS['pvw_green']};
            background-color: rgba(68, 255, 68, 0.15);
        }}
        QLabel#TallyLabel {{
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-weight: 600;
        }}
        QLabel#TallyLabel[tally="pgm"] {{
            color: {COLORS['pgm_red']};
        }}
        QLabel#TallyLabel[tally="pvw"] {{
            color: {COLORS['pvw_green']};
        }}
    """,
    
    'StatusBar': f"""
        QFrame#StatusBar {{
            background-color: {COLORS['bg_dark']};
            border: none;
            border-top: 1px solid {COLORS['border']};
            padding: 5px 10px;
        }}
    """,
    
    'QScrollBar': f"""
        QScrollBar:vertical {{
            background-color: {COLORS['bg_dark']};
            width: 10px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background-color: {COLORS['bg_light']};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['bg_lighter']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
            height: 0px;
        }}
    """,
    
    'QToolTip': f"""
        QToolTip {{
            background-color: {COLORS['bg_light']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            padding: 5px;
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 12px;
        }}
    """,
    
    'BandwidthToggle': f"""
        QPushButton#BandwidthToggle {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 18px;
            padding: 8px 16px;
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 13px;
            font-weight: 500;
            min-width: 80px;
            height: 36px;
            text-align: center;
        }}
        QPushButton#BandwidthToggle:hover {{
            background-color: {COLORS['bg_light']};
            border-color: {COLORS['border_light']};
        }}
        QPushButton#BandwidthToggle:pressed {{
            background-color: {COLORS['bg_lighter']};
        }}
        QPushButton#BandwidthToggle:checked {{
            background-color: {COLORS['accent_blue']};
            color: #ffffff;
            border-color: {COLORS['accent_blue']};
        }}
        QPushButton#BandwidthToggle:checked:hover {{
            background-color: {COLORS['accent_blue_hover']};
            border-color: {COLORS['accent_blue_hover']};
        }}
    """,
    
    'SecondaryButton': f"""
        QPushButton#SecondaryButton {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 3px;
            padding: 8px 16px;
            font-family: 'Gmarket Sans', 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 500;
            min-width: 80px;
            height: 36px;
            text-align: center;
        }}
        QPushButton#SecondaryButton:hover {{
            background-color: {COLORS['bg_light']};
            border-color: {COLORS['border_light']};
        }}
        QPushButton#SecondaryButton:pressed {{
            background-color: {COLORS['bg_lighter']};
        }}
        QPushButton#SecondaryButton:disabled {{
            background-color: {COLORS['bg_dark']};
            color: {COLORS['text_disabled']};
            border-color: {COLORS['bg_medium']};
        }}
    """,
}

def get_stylesheet():
    """완전한 스타일시트 반환"""
    return '\n'.join(STYLES.values())

def apply_theme(app):
    """애플리케이션에 다크 테마 적용"""
    # Set font
    from PyQt6.QtGui import QFont
    default_font = QFont("Gmarket Sans", 10)
    default_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(default_font)
    
    # Apply stylesheet
    app.setStyleSheet(get_stylesheet())
    
    # Set application palette
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtCore import Qt
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['bg_darkest']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['bg_dark']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['bg_medium']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['bg_light']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['bg_medium']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(COLORS['text_primary']))
    palette.setColor(QPalette.ColorRole.Link, QColor(COLORS['accent_blue']))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent_blue']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    
    # Disabled colors
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, 
                     QColor(COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, 
                     QColor(COLORS['text_disabled']))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, 
                     QColor(COLORS['text_disabled']))
    
    app.setPalette(palette)