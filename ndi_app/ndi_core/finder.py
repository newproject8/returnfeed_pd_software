# ndi_app/ndi_core/finder.py
import time
from PyQt6.QtCore import QThread, pyqtSignal
import NDIlib as ndi

class NDIFinder(QThread):
    sources_changed = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    info_message = pyqtSignal(str) # For logging within the class

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self.ndi_find = None
        self.current_sources = []
        # NDIlib_initialize should be called globally once by the main application.

    def run(self):
        self._running = True
        # Ensure NDI is initialized (globally by main.py)

        try:
            self.ndi_find = ndi.find_create_v2()
        except Exception as e:
            self.error_occurred.emit(f"Failed to create NDI Find instance: {e}. NDIlib might not be initialized or SDK is missing.")
            self._running = False
            return

        if not self.ndi_find:
            self.error_occurred.emit("NDI Find instance is None after creation. NDIlib might not be initialized.")
            self._running = False
            return

        self._log_info("NDIFinder thread started, actively searching for sources...")
        print("[DEBUG][NDIFinder.run] Loop starting...")
        while self._running:
            try:
                # Wait up to 1000ms for sources to change.
                print("[DEBUG][NDIFinder.run] Calling ndi.find_wait_for_sources...")
                if ndi.find_wait_for_sources(self.ndi_find, 1000):
                    print("[DEBUG][NDIFinder.run] ndi.find_wait_for_sources returned True (sources changed or initial list)")
                    print("[DEBUG][NDIFinder.run] Calling ndi.find_get_current_sources...")
                    raw_ndi_sources = ndi.find_get_current_sources(self.ndi_find) # This is a list of actual NDIlib.Source objects
                    print(f"[DEBUG][NDIFinder.run] ndi.find_get_current_sources returned: {len(raw_ndi_sources) if raw_ndi_sources else 'None'} NDI Source objects")
                    
                    new_source_identifiers = [] # List of (name, url_address) tuples for comparison
                    
                    if raw_ndi_sources:
                        for source_obj in raw_ndi_sources:
                            new_source_identifiers.append((source_obj.ndi_name, source_obj.url_address))
                    
                    # Sort for consistent comparison, as order might not be guaranteed
                    new_source_identifiers.sort() 
                    print(f"[DEBUG][NDIFinder.run] Processed new_source_identifiers: {new_source_identifiers}")
                    
                    # self.current_sources in NDIFinder stores list of (name, url) tuples for change detection
                    if new_source_identifiers != self.current_sources:
                        self.current_sources = new_source_identifiers # Update the list of known source identifiers
                        print(f"[DEBUG][NDIFinder.run] Source identifiers changed. Emitting sources_changed signal with {len(raw_ndi_sources) if raw_ndi_sources else 0} NDI Source objects.")
                        # Emit the list of actual NDIlib.Source objects. If raw_ndi_sources is None, emit an empty list.
                        self.sources_changed.emit(raw_ndi_sources if raw_ndi_sources else []) 
                        self._log_info(f"NDI sources updated: {len(raw_ndi_sources) if raw_ndi_sources else 0} found.")
                else:
                    print("[DEBUG][NDIFinder.run] ndi.find_wait_for_sources returned False (timeout, no change)")
                    QThread.msleep(200) # Add delay to reduce CPU load when no sources change
            except Exception as e:
                self.error_occurred.emit(f"Error during NDI source discovery: {e}")
                # Decide if we should stop or try to recover
                # For now, log and continue, but a more robust solution might be needed
                QThread.msleep(1000) # Wait a bit before retrying to avoid spamming errors

        # Cleanup when the thread is stopped
        try:
            if self.ndi_find:
                ndi.find_destroy(self.ndi_find) 
                self.ndi_find = None
        except Exception as e:
            self.error_occurred.emit(f"Error closing NDI Find instance: {e}")
        
        self._log_info("NDIFinder thread finished.")

    def stop_finder(self):
        self._log_info("Stopping NDIFinder thread...")
        self._running = False
        if self.isRunning():
            self.wait() 
        self._log_info("NDIFinder thread stopped successfully.")

    def _log_info(self, message):
        # This internal log can be connected to the main log if needed
        # For now, just print or emit a specific signal
        print(f"[NDIFinder]: {message}")
        self.info_message.emit(f"[NDIFinder]: {message}")

    # QThread's stop method is not virtual, so we use a custom name
    def request_stop(self):
        self.stop_finder()

