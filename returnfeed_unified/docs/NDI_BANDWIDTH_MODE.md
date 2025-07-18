# NDI Bandwidth Mode Feature

## Overview

The NDI module now supports switching between Normal (high quality) and Proxy (low bandwidth) modes. This feature allows users to optimize network usage based on their requirements and network conditions.

## Modes

### Normal Mode (High Quality)
- Uses `RECV_BANDWIDTH_HIGHEST` setting
- Full quality video stream
- Higher bandwidth usage
- Recommended for local networks or high-speed connections
- Default mode

### Proxy Mode (Low Bandwidth)
- Uses `RECV_BANDWIDTH_LOWEST` setting
- Reduced quality video stream
- Lower bandwidth usage
- Recommended for remote connections or limited bandwidth
- Useful for monitoring multiple sources

## Usage

### UI Controls
- A dropdown selector is available in the NDI module header
- Located between the module title and the Refresh button
- Options:
  - "Normal (High Quality)" - Full quality mode
  - "Proxy (Low Bandwidth)" - Reduced quality mode

### Switching Modes
1. Select the desired mode from the dropdown
2. If currently connected to a source, it will automatically reconnect with the new bandwidth setting
3. The connection status will show the current mode (e.g., "Connected to: Source Name (Proxy mode)")

### Settings Persistence
- The selected bandwidth mode is saved in the configuration
- The mode will be restored when the application restarts
- Stored in `config/settings.json` under `NDIDiscovery.bandwidth_mode`

## Technical Implementation

### Components Modified

1. **NDI Receiver** (`ndi_receiver.py`)
   - Added `bandwidth_mode` property
   - Modified `connect_to_source()` to apply bandwidth setting
   - Added `set_bandwidth_mode()` method for runtime switching

2. **NDI Widget** (`ndi_widget.py`)
   - Added bandwidth mode dropdown (QComboBox)
   - Added `bandwidth_mode_changed` signal
   - Updated connection status display to show current mode
   - Optional technical info overlay shows mode indicator

3. **NDI Module** (`ndi_module.py`)
   - Added bandwidth mode to settings
   - Connected bandwidth change signal
   - Apply saved mode on initialization
   - Handle mode changes in `apply_settings()`

### Configuration
```json
{
  "NDIDiscovery": {
    "auto_refresh": true,
    "refresh_interval": 2000,
    "show_addresses": true,
    "bandwidth_mode": "highest"  // or "lowest"
  }
}
```

## Use Cases

1. **Studio Environment**
   - Use Normal mode for full quality preview
   - All sources on local network

2. **Remote Production**
   - Use Proxy mode to reduce bandwidth
   - Monitor multiple remote sources

3. **Mobile/Limited Connection**
   - Use Proxy mode for basic monitoring
   - Switch to Normal mode only when needed

## Future Enhancements

Potential improvements:
- Audio-only mode support
- Custom bandwidth limits
- Automatic mode switching based on network conditions
- Per-source bandwidth settings