#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test for Enterprise Edition
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6 import OK")
except ImportError as e:
    print(f"✗ PyQt6 import failed: {e}")
    sys.exit(1)

try:
    import NDIlib as ndi
    print("✓ NDIlib import OK")
except ImportError:
    print("! NDIlib not found - will use simulation mode")
    ndi = None

try:
    from enterprise.ndi_manager_enterprise import NDIManagerEnterprise
    from enterprise.ndi_widget_enterprise import NDIWidgetEnterprise
    print("✓ Enterprise components import OK")
except ImportError as e:
    print(f"✗ Enterprise components import failed: {e}")
    # Try direct import
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'enterprise'))
        from ndi_manager_enterprise import NDIManagerEnterprise
        from ndi_widget_enterprise import NDIWidgetEnterprise
        print("✓ Enterprise components import OK (direct)")
    except ImportError as e:
        print(f"✗ Direct import also failed: {e}")
        sys.exit(1)

print("\nAll imports successful!")
print("\nStarting Enterprise Edition...")

from enterprise.main_enterprise import main

try:
    main()
except Exception as e:
    print(f"\nError during execution: {e}")
    import traceback
    traceback.print_exc()