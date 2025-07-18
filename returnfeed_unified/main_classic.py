#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReturnFeed Classic Mode Application
Professional Single-Channel NDI Monitor
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer

# NDI DLL path setup
NDI_SDK_DLL_PATH = r"C:\Program Files\NDI\NDI 6 SDK\Bin\x64"

if sys.platform == "win32":
    if hasattr(os, 'add_dll_directory'):
        try:
            if os.path.isdir(NDI_SDK_DLL_PATH):
                os.add_dll_directory(NDI_SDK_DLL_PATH)
                print(f"✅ Added NDI SDK DLL path: {NDI_SDK_DLL_PATH}")
            else:
                print(f"⚠️  NDI SDK DLL path not found: {NDI_SDK_DLL_PATH}")
        except Exception as e:
            print(f"⚠️  Failed to add NDI SDK DLL path: {e}")

# Add module path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ui.classic_mode import ClassicMainWindow
from utils.logger import setup_logging
from modules import ModuleManager
from modules.ndi_module import NDIModule
from modules.vmix_module import vMixModule
from modules.srt_module import SRTModule

# NDI library import
try:
    import NDIlib as ndi
    NDI_AVAILABLE = True
except ImportError:
    NDI_AVAILABLE = False
    ndi = None


def main():
    """Main function for Classic Mode"""
    
    # Enable high-resolution timers on Windows for better frame timing
    if sys.platform == "win32":
        try:
            import ctypes
            # Set process priority to high for better timing
            kernel32 = ctypes.windll.kernel32
            PROCESS_HIGH_PRIORITY_CLASS = 0x00000080
            kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), PROCESS_HIGH_PRIORITY_CLASS)
            print("✅ Process priority set to HIGH")
            
            # Enable 1ms timer resolution
            winmm = ctypes.windll.winmm
            winmm.timeBeginPeriod(1)  # 1ms timer resolution
            print("✅ High-resolution timers enabled (1ms)")
        except Exception as e:
            print(f"⚠️  Could not enable high-resolution timers: {e}")
    
    # Environment setup for stability
    os.environ['QSG_RHI_BACKEND'] = 'opengl'
    os.environ['QT_MULTIMEDIA_PREFERRED_PLUGINS'] = 'ffmpeg'
    os.environ['QT_LOGGING_RULES'] = 'qt.multimedia.*=false;qt.rhi.*=false;qt.rhi.backend=false'
    
    print("🎬 ReturnFeed Classic Mode - Professional NDI Monitor")
    print("✅ OpenGL backend enabled for stability")
    print("✅ FFmpeg multimedia backend configured")
    print("✅ Optimized logging for performance")
    
    # Initialize NDI
    if NDI_AVAILABLE and ndi:
        if not ndi.initialize():
            print("❌ CRITICAL: Failed to initialize NDI library")
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "NDI Initialization Error", 
                                "Failed to initialize the NDI library.\n"
                                "Please ensure the NDI SDK is correctly installed.\n"
                                "The application will now close.")
            sys.exit(1)
        print("✅ NDI library initialized successfully")
    else:
        print("⚠️  NDI library not available. NDI features will be disabled.")
    
    # Setup logging
    setup_logging()
    
    # High DPI settings
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("ReturnFeed Classic")
    app.setOrganizationName("ReturnFeed")
    app.setStyle("Fusion")  # Modern look
    
    print("\n🚀 Starting Classic Mode Interface...")
    
    # Initialize modules
    module_manager = ModuleManager()
    
    try:
        # Create modules (without parent for independence)
        ndi_module = NDIModule(None)
        vmix_module = vMixModule(None)
        srt_module = SRTModule(None)
        
        # Register modules
        module_manager.register_module(ndi_module)
        module_manager.register_module(vmix_module)
        module_manager.register_module(srt_module)
        
        # Initialize all modules
        print("📡 Initializing modules...")
        if module_manager.initialize_all():
            print("✅ All modules initialized successfully")
        else:
            print("⚠️  Some modules failed to initialize")
        
        # Start modules
        module_manager.start_all()
        
        # Auto-connect vMix for tally
        vmix_connected = False
        if vmix_module and hasattr(vmix_module, 'manager'):
            try:
                print("📡 Connecting to vMix for tally...")
                if vmix_module.manager.connect_vmix():
                    print("✅ vMix tally connected")
                    vmix_connected = True
                else:
                    print("⚠️  vMix tally connection failed (non-critical)")
            except Exception as e:
                print(f"⚠️  vMix auto-connect error (non-critical): {e}")
        
        # Create and show main window
        window = ClassicMainWindow(
            ndi_module=ndi_module,
            vmix_module=vmix_module,
            srt_module=srt_module
        )
        
        # Setup module communication
        setup_module_communication(ndi_module, vmix_module, srt_module)
        
        # Show window
        window.show()
        print("✅ 클래식 모드 윈도우 표시됨")
        
        # Update vMix status after window is shown
        if vmix_connected:
            QTimer.singleShot(500, lambda: window.command_bar.update_status("vMix", "online"))
        print("\n📌 키보드 단축키:")
        print("  Space - 연결/해제 토글")
        print("  R - 녹화 토글")
        print("  S - 스트리밍 토글")
        print("  F - 전체화면 토글")
        print("  G - 세이프 영역 토글")
        print("  I - 정보 오버레이 토글")
        print("  A - 오디오 미터 토글")
        print("  Esc - 전체화면 종료")
        
        # Connect cleanup
        window.closing.connect(lambda: cleanup(module_manager))
        
    except Exception as e:
        print(f"❌ Error creating application: {e}")
        import traceback
        traceback.print_exc()
        QMessageBox.critical(None, "Startup Error", 
                            f"Failed to start application:\n{str(e)}")
        sys.exit(1)
    
    # Run application
    exit_code = app.exec()
    
    # Cleanup
    cleanup(module_manager)
    
    if NDI_AVAILABLE and ndi:
        ndi.destroy()
        print("✅ NDI library cleaned up")
    
    # Restore normal timer resolution on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            winmm.timeEndPeriod(1)
            print("✅ Timer resolution restored")
        except:
            pass
    
    sys.exit(exit_code)


def setup_module_communication(ndi_module, vmix_module, srt_module):
    """Setup inter-module communication"""
    try:
        # Connect NDI source updates to SRT module
        if hasattr(ndi_module, 'sources_updated') and hasattr(srt_module, 'update_ndi_sources'):
            ndi_module.sources_updated.connect(
                lambda sources: srt_module.update_ndi_sources(
                    [s.get('name', '') for s in sources]
                )
            )
        
        # Connect SRT stats to NDI module
        if hasattr(srt_module, 'stream_stats_updated') and hasattr(ndi_module, 'update_srt_stats'):
            srt_module.stream_stats_updated.connect(ndi_module.update_srt_stats)
        
        print("✅ Module communication configured")
        
    except Exception as e:
        print(f"⚠️  Error setting up module communication: {e}")


def cleanup(module_manager):
    """Cleanup modules on exit"""
    print("\n🔄 Shutting down...")
    module_manager.stop_all()
    module_manager.cleanup_all()
    print("✅ Cleanup complete")


if __name__ == '__main__':
    main()