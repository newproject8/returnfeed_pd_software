# ReturnFeed PD Software Assets

This directory should contain the following icon files for the application:

## Required Icons

### Windows
- `icon.ico` - Windows application icon (256x256, ICO format)

### macOS  
- `icon.icns` - macOS application icon (ICNS format with multiple sizes)

### Linux
- `icon.png` - Linux application icon (256x256 PNG)

### System Tray
- `tray.png` - System tray icon (16x16 or 32x32 PNG)

## Icon Design Guidelines

- Use the ReturnFeed brand colors (purple/blue gradient)
- Include a camera or broadcast symbol
- Ensure good visibility at small sizes
- Follow platform-specific design guidelines

## Temporary Solution

Until proper icons are created, you can:
1. Use any 256x256 PNG image renamed appropriately
2. Convert PNG to ICO/ICNS using online tools
3. Or remove icon references from package.json temporarily

The application will work without icons, but will use default system icons.