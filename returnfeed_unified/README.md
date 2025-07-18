# ReturnFeed Unified

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-orange.svg)
![NDI](https://img.shields.io/badge/NDI-5.x%20%7C%206.x-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**Professional NDI Discovery & vMix Tally Broadcasting Solution**

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Troubleshooting](#troubleshooting)

</div>

## Overview

ReturnFeed Unified is a professional-grade application that combines NDI video preview and vMix tally light broadcasting in a single, optimized interface. Built with PyQt6 and featuring robust error handling, it provides reliable 60fps NDI playback with automatic 16:9 aspect ratio maintenance.

## ✨ Features

### Core Capabilities
- **Real-time NDI Discovery & Preview** - Automatic source detection with 60fps playback
- **vMix Tally Integration** - Real-time tally light status broadcasting
- **Modular Architecture** - Independent NDI and vMix modules for maximum reliability
- **Professional UI** - Clean, responsive interface with dark theme

### Technical Highlights
- **Bulletproof Stability** - Advanced memory management prevents crashes
- **Optimized Performance** - 60fps with < 15% CPU usage
- **WSL2 Compatible** - Full support for virtualized environments
- **16:9 Aspect Lock** - Maintains perfect aspect ratio during resize

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.8 or higher
- [NDI SDK 5.x or 6.x](https://ndi.video/for-developers/ndi-sdk/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/returnfeed_unified.git
   cd returnfeed_unified
   ```

2. **Run the application**
   ```batch
   run.bat
   ```
   
   The script will automatically:
   - Check Python installation
   - Install required dependencies
   - Configure environment for optimal performance
   - Launch the application

### First Run
1. Click **Refresh** to discover NDI sources
2. Select your vMix output from the list
3. Click **Connect** to start preview
4. Configure vMix tally settings in the Tally tab

## 📖 Documentation

### User Guides
- [Quick Start Guide](#quick-start)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Configuration Options](config/README.md)

### Developer Documentation
- [Technical Documentation](TECHNICAL_DOCUMENTATION.md)
- [API Reference](TECHNICAL_DOCUMENTATION.md#api-reference)
- [Development Guidelines](CLAUDE.md)

## 🎯 Usage

### NDI Preview
1. **Discovery**: Sources are automatically discovered on network
2. **Connection**: Double-click or select + Connect
3. **Preview**: 60fps preview with locked 16:9 aspect ratio
4. **Switching**: Disconnect before selecting new source

### vMix Tally
1. **Setup**: Enter vMix IP address (default: 127.0.0.1)
2. **Connect**: Establishes WebSocket connection
3. **Monitor**: Real-time tally status for all inputs
4. **Broadcast**: Automatic tally light updates

### Keyboard Shortcuts
- `F5` - Refresh NDI sources
- `Space` - Connect/Disconnect selected source
- `Ctrl+Q` - Quit application
- `F11` - Toggle fullscreen (NDI preview)

## 🔧 Configuration

### Environment Variables
```batch
# Performance optimized (default)
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false

# Debug mode
set QT_LOGGING_RULES=*=true
set PYTHONUNBUFFERED=1
```

### Settings File
Located at `config/settings.json`:
```json
{
  "ndi": {
    "bandwidth": "highest",
    "color_format": "BGRX_BGRA"
  },
  "vmix": {
    "host": "127.0.0.1",
    "port": 8099
  }
}
```

## 🐛 Troubleshooting

### Common Issues
- **No NDI sources found**: Check firewall and network settings
- **Low frame rate**: Ensure debug logging is disabled
- **Aspect ratio issues**: Update to latest version

See [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions.

## 📊 Performance

### System Requirements
- **Minimum**: 4GB RAM, Dual-core CPU
- **Recommended**: 8GB RAM, Quad-core CPU, Dedicated GPU

### Benchmarks
- **1080p60 NDI**: < 15% CPU, < 200MB RAM
- **Latency**: < 50ms end-to-end
- **Stability**: 24+ hour continuous operation

## 🛠️ Development

### Building from Source
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development version
python main.py
```

### Running Tests
```batch
run_test.bat
```

### Debug Mode
```batch
run_debug.bat
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## 🙏 Acknowledgments

- NDI® is a registered trademark of Vizrt NDI AB
- vMix is a product of StudioCoast Pty Ltd
- Built with PyQt6 by Riverbank Computing

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/returnfeed_unified/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/returnfeed_unified/discussions)
- **Email**: support@yourdomain.com

---

<div align="center">
Made with ❤️ for the broadcast community
</div>