#!/usr/bin/env python3
"""Test script for NDI bandwidth mode switching"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.ndi_module import NDIModule

def main():
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("NDI Bandwidth Mode Test")
    window.resize(800, 600)
    
    # Create central widget
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Create NDI module
    ndi_module = NDIModule()
    
    # Initialize module
    if ndi_module.initialize():
        print("NDI module initialized successfully")
        
        # Get widget and add to layout
        ndi_widget = ndi_module.get_widget()
        layout.addWidget(ndi_widget)
        
        # Start discovery
        if ndi_module.start():
            print("NDI discovery started")
        else:
            print("Failed to start NDI discovery")
    else:
        print("Failed to initialize NDI module")
    
    window.setCentralWidget(central_widget)
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()