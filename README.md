# ReturnFeed PD Software

Professional broadcast production software for vMix integration with real-time tally system.

## 🎯 Overview

ReturnFeed PD Software is an Electron-based desktop application that connects vMix with the ReturnFeed cloud platform, enabling:

- **Real-time vMix Tally Integration**: Automatic tally signal distribution to camera operators
- **Multi-Camera Management**: Support for unlimited camera inputs with live status monitoring
- **Cloud-Based Staff URLs**: Generate unique URLs for camera operators to receive personalized tally signals
- **SRT Streaming**: Secure, reliable streaming to MediaMTX servers
- **Global Multi-Tenant Support**: Multiple PDs can use the system simultaneously worldwide

## 🚀 Features

### Core Functionality
- ✅ **vMix API Integration**: Official TCP (8099) and HTTP (8088) API support
- ✅ **Real-time Tally Distribution**: Live program/preview status for each camera
- ✅ **Camera Input Detection**: Automatic discovery of vMix inputs with metadata
- ✅ **Cloud Registration**: Seamless registration with ReturnFeed servers
- ✅ **Cross-Platform**: Windows, macOS, and Linux support

### Professional Features
- ✅ **Enterprise-Grade Security**: JWT authentication with 30-day tokens
- ✅ **Session Management**: Isolated sessions for multiple productions
- ✅ **WebSocket Communication**: Low-latency real-time messaging
- ✅ **Automatic Reconnection**: Robust connection handling with exponential backoff
- ✅ **System Tray Integration**: Minimizes to tray for background operation

## 📦 Installation

### Prerequisites
- **vMix**: Version 24.0 or later
- **Node.js**: Version 16.0 or later
- **Internet Connection**: For cloud registration and tally distribution

### Quick Start

1. **Download & Install**
   ```bash
   git clone https://github.com/newproject8/returnfeed_pd_software.git
   cd returnfeed_pd_software
   npm install
   ```

2. **Development Mode**
   ```bash
   npm run dev
   ```

3. **Build Application**
   ```bash
   npm run build
   npm run dist
   ```

## 🔧 Configuration

### vMix Setup
1. **Enable Web Controller** in vMix Settings
2. **TCP Port**: 8099 (for TALLY subscription)
3. **HTTP Port**: 8088 (for XML API)
4. **Allow IP Access**: Configure firewall for the PD Software computer

### SRT Streaming Setup
1. vMix → **Add Output** → **SRT Caller**
2. **URL**: `srt://returnfeed.net:8890?streamid={your_session_key}`
3. **Mode**: Caller
4. **Latency**: 120ms (recommended)

## 🌍 Global Usage

### For International PDs
1. **Register**: Create account at ReturnFeed servers
2. **Unique Session**: Get dedicated session key and stream URLs
3. **Staff URLs**: Share personalized URLs with camera operators
4. **Independent Operation**: Completely isolated from other PDs worldwide

### Multi-Tenant Architecture
- **Unlimited PDs**: No limit on simultaneous users
- **Global Isolation**: Each PD gets independent streaming infrastructure
- **Regional Support**: Works from any country with internet access

## 🎮 Usage

### Step 1: Registration
1. Launch PD Software
2. Click **"vMix 연결"** to connect to your vMix instance
3. Click **"릴레이 연결"** to register with ReturnFeed servers
4. Browser will auto-open for account registration

### Step 2: Camera Setup
1. Configure cameras in vMix
2. PD Software automatically detects all inputs
3. Camera metadata syncs in real-time

### Step 3: Staff Distribution
1. Get staff URL from PD Software
2. Share URL with camera operators via QR code or link
3. Camera operators select their camera number on mobile/tablet
4. Real-time tally signals begin immediately

## 🔌 API Integration

### vMix Commands Used
```javascript
// Subscribe to real-time tally updates
SUBSCRIBE TALLY

// Get full input information
XML

// Query specific input status
Function=GetText&Input=1&SelectedName=Key
```

### WebSocket Messages
```javascript
// Tally update to staff
{
  "type": "tally_update",
  "program": 1,
  "preview": 2,
  "inputs": { "1": "Camera 1", "2": "Camera 2" }
}

// Camera inputs update
{
  "type": "inputs_update", 
  "inputs": { /* vMix input data */ },
  "vmixVersion": "26.0.0.49"
}
```

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    vMix     │◄──►│  PD Software     │◄──►│ ReturnFeed      │
│   (Local)   │    │   (Desktop)      │    │ Cloud Platform  │
└─────────────┘    └──────────────────┘    └─────────────────┘
                           │                         │
                           ▼                         ▼
                   ┌──────────────────┐    ┌─────────────────┐
                   │  SRT Streaming   │    │  Staff Browsers │
                   │   (MediaMTX)     │    │   (Worldwide)   │
                   └──────────────────┘    └─────────────────┘
```

## 🔒 Security

- **JWT Authentication**: Secure token-based authentication
- **HTTPS/WSS**: All communication encrypted
- **Session Isolation**: Complete data separation between PDs
- **No Local Storage**: Sensitive data stored securely in cloud

## 🛠️ Development

### Project Structure
```
pd-software/
├── src/
│   ├── main.js          # Electron main process
│   ├── vmixClient.js    # vMix API client
│   ├── relayClient.js   # Cloud WebSocket client
│   ├── preload.js       # Security bridge
│   └── index.html       # UI interface
├── assets/              # Application icons
├── package.json         # Dependencies & build config
└── README.md           # This file
```

### Build Commands
```bash
npm run start      # Start application
npm run dev        # Development mode with DevTools
npm run build      # Build for production
npm run dist       # Create distributable packages
```

### Supported Platforms
- **Windows**: NSIS installer (.exe)
- **macOS**: DMG package (.dmg)
- **Linux**: AppImage (.AppImage)

## 🌟 Production Features

- **Enterprise Logging**: Winston-based structured logging
- **Error Handling**: Comprehensive error recovery
- **Performance Monitoring**: Real-time performance metrics
- **Auto-Updates**: Built-in update mechanism (future)
- **Crash Reporting**: Automatic crash report collection (future)

## 🤝 Support

### Requirements
- **Minimum vMix**: Version 24.0+
- **Network**: Stable internet connection (10Mbps+ upload recommended)
- **Hardware**: Any computer capable of running Electron applications

### Troubleshooting
1. **vMix Connection Issues**: Check TCP port 8099 firewall settings
2. **Tally Not Working**: Verify WebSocket connection to cloud
3. **Staff URL Issues**: Ensure session is active and properly registered

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Projects

- **ReturnFeed Backend**: [Backend API Server](https://github.com/newproject8/returnfeed_backend)
- **ReturnFeed Frontend**: Web interface for staff and viewers
- **MediaMTX Integration**: SRT streaming infrastructure

---

**Made with ❤️ for the global broadcast community**

For support: [Issues](https://github.com/newproject8/returnfeed_pd_software/issues)