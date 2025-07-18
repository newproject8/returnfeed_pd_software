# Troubleshooting Guide

## Quick Fixes

### 🚨 Application Won't Start
```batch
# Run diagnostic test
run_test.bat
# Select option 8 (Quick Diagnostic)
```

### 🎥 No NDI Video
1. Check NDI SDK installation: `C:\Program Files\NDI\NDI 6 SDK`
2. Verify vMix is sending NDI output
3. Run as Administrator
4. Disable antivirus temporarily

### ⚡ Performance Issues
```batch
# Use optimized settings
set QT_LOGGING_RULES=qt.multimedia.*=false;qt.rhi.*=false
run.bat
```

## Common Issues

### 1. NDI Source Not Found

**Symptoms**:
- Source list is empty
- "Source not found" error

**Solutions**:
- Ensure vMix External Output is enabled
- Check firewall settings (allow mDNS port 5353)
- Verify same network/subnet
- Try direct IP connection

### 2. Application Crashes After 5 Seconds

**Symptoms**:
- Consistent crash at ~5 second mark
- Works briefly then stops

**Solution**:
Environment variables are already set in run.bat. If still crashing:
```batch
# Force software rendering
set QT_QUICK_BACKEND=software
run.bat
```

### 3. Frame Rate Lower Than Expected

**Current Status**: Fixed - should achieve 60fps

If still experiencing issues:
- Close other NDI applications
- Check network bandwidth
- Reduce NDI quality in vMix

### 4. Video Aspect Ratio Issues

**Current Status**: Fixed - 16:9 ratio maintained

The application now:
- Always displays in 16:9 format
- Adds black bars for non-16:9 content
- Maintains ratio during resize

### 5. Import Errors

**Symptoms**:
```
ImportError: attempted relative import beyond top-level package
```

**Solution**:
- Run from correct directory
- Use run.bat instead of direct Python

### 6. Window Movement Crashes

**Symptoms**:
- Crash when dragging window
- Freeze during resize

**Solution**:
Already fixed with OpenGL backend. If persisting:
- Update graphics drivers
- Disable window animations

## Debug Mode

### Enable Detailed Logging
```batch
run_debug.bat
```

### Performance Monitoring
In `modules/ndi_module/ndi_receiver.py`:
```python
self.debug_enabled = True
self.memory_monitor_enabled = True
```

### Network Diagnostics
```batch
# Check NDI discovery
ndi-directory-service.exe

# List NDI sources
ndi-receive.exe -listonly
```

## System Requirements

### Minimum
- Windows 10/11 (64-bit)
- Python 3.8+
- 4GB RAM
- NDI SDK 5.x or 6.x

### Recommended
- Windows 11
- Python 3.10+
- 8GB RAM
- Gigabit network
- Dedicated GPU

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| -1073741819 | Access Violation | Reinstall NDI SDK |
| -1073741676 | Division by Zero | Update to latest version |
| -1073741571 | Stack Overflow | Increase stack size |
| 1 | General Python Error | Check logs |
| 2 | Import Error | Verify dependencies |
| 3 | NDI Init Failed | Reinstall NDI SDK |

## FAQ

### Q: Why is the video quality poor?
**A**: Check:
- NDI bandwidth setting (use HIGHEST)
- Network congestion
- vMix output quality settings

### Q: Can I use multiple NDI sources?
**A**: Currently supports one source at a time. Multi-source support planned.

### Q: Does it work with NDI 4.x?
**A**: Optimized for NDI 5.x/6.x. May work with 4.x but not tested.

### Q: Why does it use so much CPU?
**A**: 
- Disable debug mode
- Check for other NDI consumers
- Verify hardware acceleration

### Q: Can I record the NDI stream?
**A**: Not yet. Use vMix recording or OBS with NDI plugin.

## Getting Help

### Logs Location
```
logs/
├── ndi_module.log
├── vmix_module.log
└── debug_session_*.log
```

### Information to Provide
1. Error message/screenshot
2. Log files
3. System specs
4. vMix version
5. Steps to reproduce

### Quick System Info
```batch
run_test.bat
# Select option 8 (Quick Diagnostic)
# Copy output
```

## Advanced Troubleshooting

### Reset Configuration
```batch
# Backup current config
copy config\settings.json config\settings.backup.json

# Reset to defaults
del config\settings.json
run.bat
```

### Force Specific NDI Version
```python
# In main.py, before ndi.initialize()
os.environ['NDI_RUNTIME_DIR_V6'] = r'C:\Program Files\NDI\NDI 6 Runtime'
```

### Network Optimization
```python
# In ndi_receiver.py
recv_create_v3.bandwidth = ndi.RECV_BANDWIDTH_LOWEST  # For poor networks
```

### Memory Leak Detection
```batch
# Run memory test
run_test.bat
# Select option 5 (Memory Monitor)
```

## Contact Support

Before contacting support:
1. Try all relevant solutions above
2. Run diagnostic test
3. Collect log files
4. Document reproduction steps

Include:
- Diagnostic output
- Error screenshots
- Complete log files
- System specifications