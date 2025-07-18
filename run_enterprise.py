#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enterprise Edition Launcher
Cross-platform launcher for the high-performance version
"""

import sys
import os
import subprocess

def main():
    """Launch Enterprise Edition"""
    print("="*60)
    print("PD Software - Enterprise Edition")
    print("High-performance, production-ready version")
    print("="*60)
    print()
    
    # Get paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        # Try Unix path
        venv_python = os.path.join(script_dir, "venv", "bin", "python")
        
    enterprise_main = os.path.join(script_dir, "enterprise", "main_enterprise.py")
    
    # Check if files exist
    if not os.path.exists(venv_python):
        print("Error: Virtual environment not found!")
        print("Please run: python -m venv venv")
        return 1
        
    if not os.path.exists(enterprise_main):
        print("Error: Enterprise edition not found!")
        print(f"Expected at: {enterprise_main}")
        return 1
        
    # Launch
    print(f"Launching with: {venv_python}")
    print()
    
    try:
        result = subprocess.run([venv_python, enterprise_main])
        return result.returncode
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        return 0
    except Exception as e:
        print(f"Error launching: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())