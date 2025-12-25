import customtkinter as ctk
from datetime import datetime
import threading
import time
from tkinter import messagebox

class CameraStatusFrame(ctk.CTkFrame):
    def __init__(self, parent, process_manager, refresh_callback):
        super().__init__(parent, fg_color="transparent")
        self.pm = process_manager
        self.refresh_callback = refresh_callback
        self.current_cam_id = None
        self.log_buffers = {} # Logs per camera opslaan

        self.setup_ui()

    def setup_ui(self):
        # Controls
        ctrl = ctk.CTkFrame(self)
        ctrl.pack(fill="x", padx=10, pady=10)
        
        self.btn_start = ctk.CTkButton(ctrl, text="Start Camera", fg_color="green", command=self.start_cam)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(ctrl, text="Stop Camera", fg_color="red", command=self.stop_cam)
        self.btn_stop.pack(side="left", padx=5)
        
        ctk.CTkButton(ctrl, text="Stop ALLE", fg_color="#8B0000", command=self.stop_all).pack(side="right", padx=5)
        ctk.CTkButton(ctrl, text="Start ALLE", fg_color="#2D572C", command=self.start_all).pack(side="right", padx=5)

        # Logbox
        self.log_box = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_box.insert("0.0", "Selecteer een camera...\n")

    def set_camera(self, cam_id):
        self.current_cam_id = cam_id
        
        # Knoppen updaten
        self.btn_start.configure(text=f"Start {cam_id}")
        self.btn_stop.configure(text=f"Stop {cam_id}")
        
        # Logs tonen
        self.log_box.delete("0.0", "end")
        if cam_id in self.log_buffers:
            self.log_box.insert("0.0", self.log_buffers[cam_id])
        else:
            self.log_box.insert("0.0", f"--- Log start voor {cam_id} ---\n")
            self.log_buffers[cam_id] = ""

    def append_log(self, cam_id, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        
        if cam_id not in self.log_buffers:
            self.log_buffers[cam_id] = ""
        
        self.log_buffers[cam_id] += line
        # Beperk buffer grootte
        if len(self.log_buffers[cam_id]) > 50000:
            self.log_buffers[cam_id] = self.log_buffers[cam_id][-40000:]

        # Als dit de actieve camera is (of SYSTEM bericht), update scherm
        if self.current_cam_id == cam_id or "SYSTEM" in str(cam_id):
            self.log_box.insert("end", line if self.current_cam_id == cam_id else f"[SYSTEM] {message}\n")
            self.log_box.see("end")
            
        if "status changed" in message.lower():
            self.refresh_callback() # Sidebar update (voor play icoontje)

    def start_cam(self):
        if self.current_cam_id: 
            self.pm.start_camera(self.current_cam_id)
            self.refresh_callback()

    def stop_cam(self):
        if self.current_cam_id:
            self.pm.stop_camera(self.current_cam_id)
            self.refresh_callback()

    def stop_all(self):
        if messagebox.askyesno("Stop", "Alles stoppen?"):
            self.pm.stop_all()
            self.refresh_callback()

    def start_all(self):
        # Start alle enabled camera's via thread om UI niet te freezen
        def run():
            # We moeten de config hier ophalen, dit kan via self.pm.cfg
            cams = self.pm.cfg.get_cameras()
            for c in cams:
                if c.get("enabled"):
                    self.pm.start_camera(c['id'])
                    time.sleep(1)
                    # UI update via after (thread safe)
                    self.after(0, self.refresh_callback)
        threading.Thread(target=run, daemon=True).start()