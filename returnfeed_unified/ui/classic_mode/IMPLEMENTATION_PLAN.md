# Classic Mode GUI Implementation Plan
## Single-Channel Monitor Focus with Modern Design

### 1. Design Principles
- **Single Channel Focus**: 하나의 NDI 소스에 집중하여 최고의 모니터링 경험 제공
- **Modern Dark Theme**: PyDracula 스타일의 세련된 다크 테마
- **Professional Grade**: 방송 현장에서 즉시 사용 가능한 안정성
- **Zero Distraction**: 필수 정보만 표시하여 집중도 극대화

### 2. Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Bar (최상단)                      │
│  🟢 NDI  🟢 vMix  🟢 리턴피드 스트림 │ ⏺ REC │ 📡 LIVE │ 14:32:15      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Main Video Display                       │
│                     (16:9 Ratio)                           │
│                                                             │
│                   [NDI VIDEO PREVIEW]                       │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Source: CAM-01 │ 1920x1080 60fps │ 125Mbps │ Audio: -48dB │
├─────────────────────────────────────────────────────────────┤
│                    Control Panel                            │
│ [Source Select ▼] [Connect] │ Tally: ●PGM │ 리턴피드: ⏸ Ready  │
└─────────────────────────────────────────────────────────────┘
```

### 3. Color Scheme (PyDracula Dark)
```python
COLORS = {
    # Background
    'bg_main': '#1e1e1e',
    'bg_secondary': '#2b2b2b',
    'bg_tertiary': '#373737',
    
    # Accent (Modern Blue)
    'accent': '#3797ff',
    'accent_hover': '#4ea5ff',
    'accent_pressed': '#2485ee',
    
    # Status Colors
    'status_online': '#00ff88',
    'status_pgm': '#ff3737',
    'status_pvw': '#37ff00',
    'status_offline': '#666666',
    
    # Text
    'text_primary': '#ffffff',
    'text_secondary': '#aaaaaa',
    'text_disabled': '#666666',
    
    # Borders
    'border': '#3c3c3c',
    'border_hover': '#4c4c4c'
}
```

### 4. Components

#### 4.1 Command Bar
- Flat design with status indicators
- Real-time connection status
- Master recording/streaming controls
- System time display

#### 4.2 Main Video Display
- Full HD preview with GPU acceleration
- 16:9 aspect ratio maintained
- Smooth 60fps playback
- Minimal UI overlay

#### 4.3 Status Bar
- Source information
- Technical details (resolution, fps, bitrate)
- Audio level meter
- Compact single line design

#### 4.4 Control Panel
- Source selector dropdown
- Connect/Disconnect button
- Tally status indicator
- 리턴피드 streaming control

### 5. Features

#### Essential Features
1. **Single NDI Source Selection**: Dropdown으로 소스 선택
2. **One-Click Connection**: 즉시 연결/해제
3. **Real-Time Tally Display**: PGM/PVW 상태 표시
4. **리턴피드 Quick Control**: 스트리밍 시작/중지
5. **Auto-Reconnect**: 연결 끊김 시 자동 재연결

#### Advanced Features
1. **Keyboard Shortcuts**:
   - Space: Toggle connection
   - R: Start/Stop recording
   - S: Start/Stop streaming
   - F: Fullscreen video
   - Esc: Exit fullscreen

2. **Error Prevention**:
   - Confirmation dialogs
   - Auto-save settings
   - Crash recovery

3. **Performance Optimization**:
   - Frame skipping on overload
   - Memory pool management
   - GPU-accelerated rendering

### 6. Implementation Steps

#### Phase 1: Core Structure (Day 1)
- [ ] Create new classic_mode package
- [ ] Implement ClassicMainWindow with PyDracula styling
- [ ] Setup basic layout structure
- [ ] Integrate qt-material-icons

#### Phase 2: Video Display (Day 2)
- [ ] Port VideoDisplayWidget to single-channel mode
- [ ] Optimize for single source monitoring
- [ ] Add fullscreen support
- [ ] Implement smooth rendering

#### Phase 3: Controls & Status (Day 3)
- [ ] Implement CommandBar component
- [ ] Create ControlPanel with source selector
- [ ] Add StatusBar with real-time info
- [ ] Connect to existing modules

#### Phase 4: Styling & Polish (Day 4)
- [ ] Apply PyDracula theme fully
- [ ] Add animations and transitions
- [ ] Implement keyboard shortcuts
- [ ] Error handling and dialogs

#### Phase 5: Testing & Optimization (Day 5)
- [ ] Performance testing
- [ ] Memory leak checks
- [ ] User experience testing
- [ ] Final adjustments

### 7. File Structure
```
classic_mode/
├── __init__.py
├── main_window.py          # ClassicMainWindow
├── components/
│   ├── __init__.py
│   ├── command_bar.py      # Top status bar
│   ├── video_display.py    # Single channel viewer
│   ├── control_panel.py    # Bottom controls
│   └── status_bar.py       # Info display
├── styles/
│   ├── __init__.py
│   ├── dark_theme.py       # PyDracula dark theme
│   └── resources.qrc       # Icons and assets
└── utils/
    ├── __init__.py
    └── shortcuts.py        # Keyboard shortcuts
```