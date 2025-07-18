#!/usr/bin/env python3
"""Diagnose SRT module initialization issues"""

import sys
import os
import subprocess

print("=== SRT Module Diagnostic Tool ===\n")

# Check Python version
print(f"1. Python version: {sys.version}")

# Check current directory
print(f"\n2. Current directory: {os.getcwd()}")

# Check if PyQt6 is installed
print("\n3. Checking PyQt6...")
try:
    import PyQt6
    print(f"✓ PyQt6 installed - Version: {PyQt6.QtCore.PYQT_VERSION_STR}")
except ImportError as e:
    print(f"✗ PyQt6 not installed: {e}")
    print("  Run: pip install PyQt6")

# Check if ffmpeg-python is installed
print("\n4. Checking ffmpeg-python...")
try:
    import ffmpeg
    print("✓ ffmpeg-python installed")
except ImportError:
    print("✗ ffmpeg-python not installed")
    print("  Run: pip install ffmpeg-python")

# Check FFmpeg executable
print("\n5. Checking FFmpeg executable...")
ffmpeg_found = False
for cmd in ['ffmpeg', 'ffmpeg.exe']:
    try:
        result = subprocess.run([cmd, '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg found: {version_line}")
            ffmpeg_found = True
            break
    except:
        pass

if not ffmpeg_found:
    print("✗ FFmpeg not found in PATH")
    print("  Install FFmpeg or run install_ffmpeg_portable.bat")

# Check module structure
print("\n6. Checking module structure...")
module_files = [
    "modules/__init__.py",
    "modules/srt_module/__init__.py",
    "modules/srt_module/srt_module.py",
    "modules/srt_module/srt_manager.py",
    "modules/srt_module/srt_widget.py"
]

all_present = True
for file in module_files:
    if os.path.exists(file):
        print(f"✓ {file} exists")
    else:
        print(f"✗ {file} missing")
        all_present = False

# Try to import the module
if all_present:
    print("\n7. Testing module import...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from modules import BaseModule
        print("✓ BaseModule imported")
    except Exception as e:
        print(f"✗ Failed to import BaseModule: {e}")
    
    try:
        from modules.srt_module import SRTModule
        print("✓ SRTModule imported")
    except Exception as e:
        print(f"✗ Failed to import SRTModule: {e}")
        import traceback
        traceback.print_exc()

# Check logs
print("\n8. Checking recent logs...")
log_dir = "logs"
if os.path.exists(log_dir):
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')])
    if log_files:
        latest_log = os.path.join(log_dir, log_files[-1])
        print(f"Latest log: {latest_log}")
        
        # Look for SRT errors in the last 50 lines
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                srt_errors = [line for line in lines[-50:] if 'SRT' in line and ('ERROR' in line or 'Failed' in line)]
                if srt_errors:
                    print("\nRecent SRT errors:")
                    for error in srt_errors[-5:]:  # Show last 5 errors
                        print(f"  {error.strip()}")
                else:
                    print("No recent SRT errors found")
        except Exception as e:
            print(f"Could not read log file: {e}")
else:
    print("No logs directory found")

print("\n=== Diagnostic Complete ===")