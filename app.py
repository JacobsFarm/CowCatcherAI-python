import customtkinter as ctk
import sys
import atexit

from logic.config_manager import ConfigManager
from logic.process_manager import ProcessManager
from gui.main_window import CowCatcherGUI

def main():
    config_manager = ConfigManager()
    
    app = ctk.CTk()
    app.title("CowCatcher AI")
    app.geometry("1100x700")
    
    process_manager = ProcessManager(config_manager)
    
    gui = CowCatcherGUI(app, config_manager, process_manager)
    
    process_manager.log_callback = gui.append_log

    def on_close():
        process_manager.stop_all()
        app.destroy()
        sys.exit(0)

    app.protocol("WM_DELETE_WINDOW", on_close)
    atexit.register(process_manager.stop_all)

    app.mainloop()

if __name__ == "__main__":
    main()
