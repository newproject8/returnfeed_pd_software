# MediaMTX Setup Guide for ReturnFeed

## Problem Summary
MediaMTX was failing to start due to:
1. WSL compatibility issues - needed to use cmd.exe to run Windows executables
2. Configuration file format errors - incorrect YAML keys
3. Port conflicts - default config was trying to bind to port 8000
4. API access from WSL - needed to use Windows host IP instead of localhost

## Solution Implemented

### 1. Fixed setup_local_mediamtx.py
- Added WSL detection
- Use cmd.exe to run mediamtx.exe in WSL environment
- Updated config file format with correct YAML keys

### 2. Created Background Startup Script
- `start_mediamtx_background.py` - Starts MediaMTX in background
- `START_MEDIAMTX.bat` - Windows batch file for easy startup

### 3. Created Status Check Utility
- `check_mediamtx.py` - Checks if MediaMTX is running properly
- Handles WSL networking properly

## How to Use

### Starting MediaMTX

#### Option 1: Use the batch file (Recommended)
```batch
START_MEDIAMTX.bat
```

#### Option 2: Use Python script
```bash
python start_mediamtx_background.py
```

### Checking MediaMTX Status
```bash
python check_mediamtx.py
```

### Stopping MediaMTX
```batch
taskkill /F /IM mediamtx.exe
```

## Configuration
- SRT Port: 8890
- API Port: 9997
- Config File: `mediamtx_local/mediamtx.yml`

## Troubleshooting

### If MediaMTX fails to start:
1. Check if ports 8890 and 9997 are available
2. Ensure mediamtx.exe exists in mediamtx_local directory
3. Check Windows Firewall settings

### If API is not responding from WSL:
- The scripts automatically handle this by using the Windows host IP
- You can manually find the host IP with: `ip route show | grep default`

## Integration with ReturnFeed
The SRT module in ReturnFeed will now work properly with MediaMTX running in the background.