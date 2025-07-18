# Changelog

All notable changes to ReturnFeed Unified will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-07-14

### 🎉 Initial Release

#### Added
- **NDI Module**
  - Real-time NDI source discovery
  - 60fps video preview with QPainter direct rendering
  - Automatic 16:9 aspect ratio maintenance
  - Bulletproof memory management
  - Support for BGRA and YUV formats

- **vMix Module**
  - WebSocket tally light integration
  - Real-time status monitoring
  - Automatic reconnection handling
  - Multi-input tally support

- **Core Features**
  - Modular architecture with independent components
  - Protocol-based design pattern
  - Thread-safe operation
  - Comprehensive error handling
  - Professional dark theme UI

- **Performance Optimizations**
  - 60fps playback capability
  - < 15% CPU usage on modern systems
  - < 200MB memory footprint
  - Optimized frame processing pipeline

- **Stability Improvements**
  - WSL2 compatibility fixes
  - OpenGL backend enforcement
  - Crash prevention mechanisms
  - Memory leak prevention

- **Developer Tools**
  - Comprehensive test suite
  - Debug mode with detailed logging
  - Performance monitoring tools
  - Memory leak detection

### Fixed
- Import errors with modular architecture
- Metaclass conflicts between ABC and Protocol
- 5-second crash issue in virtualized environments
- Frame format mismatches (YUV vs BGRA)
- QPainter rendering errors
- 16:9 aspect ratio distortion on resize
- Window movement crashes
- Thread safety issues

### Security
- Secure WebSocket implementation for vMix
- Input validation for all user data
- Safe memory management practices

## [0.5.0-beta] - 2024-07-10

### Added
- Initial beta release
- Basic NDI discovery and preview
- Simple vMix tally integration
- PyQt6-based UI

### Known Issues
- Crashes after 5 seconds of playback
- Frame rate limited to ~33fps
- Aspect ratio not maintained during resize
- Import errors in modular structure

## Roadmap

### [1.1.0] - Planned
- Multiple NDI source support (PiP)
- Recording capabilities
- Hardware acceleration
- Custom tally light protocols

### [1.2.0] - Planned
- HDR support
- Advanced color management
- Network bandwidth optimization
- Remote control API

### [2.0.0] - Future
- Cross-platform support (macOS, Linux)
- Cloud integration
- AI-powered scene detection
- Professional streaming features