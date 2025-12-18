import customtkinter as ctk
from tkinter import messagebox
import uuid
from datetime import datetime
import threading
import time

# Constanten
RAL_6002 = "#2D572C"
COLOR_HOVER = "#3A6B39"

class CameraTab(ctk.CTkFrame):
    def __init__(self, parent, config_manager, process_manager, main_app_ref):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        self.pm = process_manager
        self.main_app = main_app_ref
        
        self.selected_camera_id = None
        self.log_buffers = {} 
        
        # --- UI Opbouw ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar (Lijst met camera's)
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.sidebar, text="CAMERA'S", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_add_cam = ctk.CTkButton(self.sidebar, text="+ Nieuwe Camera", fg_color=RAL_6002, hover_color=COLOR_HOVER, command=self.add_new_camera)
        self.btn_add_cam.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.scroll_cams = ctk.CTkScrollableFrame(self.sidebar, label_text="")
        self.scroll_cams.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # 2. Main Content (Details & Logs)
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.cam_tabs = ctk.CTkTabview(self.main_area)
        self.cam_tabs.pack(fill="both", expand=True)
        
        self.tab_settings = self.cam_tabs.add("Camera Instellingen")
        self.tab_logs = self.cam_tabs.add("Status & Logs")
        
        self.setup_settings_form(self.tab_settings)
        self.setup_log_view(self.tab_logs)

        # 3. Initialisatie
        self.refresh_camera_list()
        
        # Selecteer eerste camera indien aanwezig
        cameras = self.cfg.get_cameras()
        if cameras:
            self.select_camera(cameras[0]['id'])

    # ==========================================
    #  UI SETUP METHODEN
    # ==========================================
    def setup_settings_form(self, frame):
        frame.grid_columnconfigure(1, weight=1)

        # Camera Naam
        ctk.CTkLabel(frame, text="Camera Naam:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_name = ctk.CTkEntry(frame)
        self.entry_name.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # RTSP URL
        ctk.CTkLabel(frame, text="RTSP URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_url = ctk.CTkEntry(frame, placeholder_text="rtsp://user:pass@ip...")
        self.entry_url.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Telegram Bot Selectie
        ctk.CTkLabel(frame, text="Telegram Bot:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.combo_bot = ctk.CTkComboBox(frame, values=["Geen"])
        self.combo_bot.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Thresholds
        ctk.CTkLabel(frame, text="Notify Threshold:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_notify = ctk.CTkEntry(frame)
        self.entry_notify.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(frame, text="Peak Threshold:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.entry_peak = ctk.CTkEntry(frame)
        self.entry_peak.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # Switches
        self.var_enabled = ctk.BooleanVar()
        self.switch_enabled = ctk.CTkSwitch(frame, text="Camera Ingeschakeld", variable=self.var_enabled, progress_color=RAL_6002)
        self.switch_enabled.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self.var_live = ctk.BooleanVar()
        self.switch_live = ctk.CTkSwitch(frame, text="Show Live Feed (Popup)", variable=self.var_live, progress_color=RAL_6002)
        self.switch_live.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Knoppen
        self.btn_save_cam = ctk.CTkButton(frame, text="Instellingen Opslaan", fg_color=RAL_6002, command=self.save_current_camera)
        self.btn_save_cam.grid(row=8, column=1, padx=10, pady=20, sticky="e")
        
        self.btn_del_cam = ctk.CTkButton(frame, text="Camera Verwijderen", fg_color="#8B0000", hover_color="#500000", command=self.delete_current_camera)
        self.btn_del_cam.grid(row=8, column=0, padx=10, pady=20, sticky="w")

    def setup_log_view(self, frame):
        # Knoppenbalk
        ctrl_frame = ctk.CTkFrame(frame)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start = ctk.CTkButton(ctrl_frame, text="Start Camera", fg_color="green", command=self.start_process)
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(ctrl_frame, text="Stop Camera", fg_color="red", command=self.stop_process)
        self.btn_stop.pack(side="left", padx=5)
        
        self.btn_stop_all = ctk.CTkButton(ctrl_frame, text="Stop ALLE Cameras", fg_color="#8B0000", command=self.stop_all_processes)
        self.btn_stop_all.pack(side="right", padx=5)

        self.btn_start_all = ctk.CTkButton(ctrl_frame, text="Start ALLE Cameras", fg_color="#2D572C", command=self.start_all_processes)
        self.btn_start_all.pack(side="right", padx=5)

        # Log Textbox
        self.log_box = ctk.CTkTextbox(frame, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_box.insert("0.0", "Selecteer een camera links om de status te zien.\n")

    # ==========================================
    #  CAMERA LIJST LOGICA
    # ==========================================
    def refresh_camera_list(self):
        for widget in self.scroll_cams.winfo_children():
            widget.destroy()

        cameras = self.cfg.get_cameras()
        for cam in cameras:
            if cam['id'] not in self.log_buffers:
                self.log_buffers[cam['id']] = ""

            text = f"{cam.get('name', 'Naamloos')}\n({cam['id']})"
            btn = ctk.CTkButton(self.scroll_cams, text=text, 
                                fg_color="transparent", border_width=1, border_color="gray",
                                command=lambda cid=cam['id']: self.select_camera(cid))
            btn.pack(fill="x", pady=2)

            if self.pm.is_running(cam['id']):
                btn.configure(border_color=RAL_6002, text=f"▶ {text}")
            
            if cam['id'] == self.selected_camera_id:
                btn.configure(fg_color=COLOR_HOVER, border_color=RAL_6002)

    def select_camera(self, cam_id):
        self.selected_camera_id = cam_id
        self.populate_camera_form(cam_id)
        self.update_log_view_for_selected()
        self.refresh_camera_list()
        
        # Update knop teksten
        self.btn_start.configure(text=f"Start {cam_id}")
        self.btn_stop.configure(text=f"Stop {cam_id}")

    def populate_camera_form(self, cam_id):
        cam = self.cfg.get_camera_by_id(cam_id)
        if not cam: return

        self.entry_name.delete(0, "end"); self.entry_name.insert(0, cam.get("name", ""))
        self.entry_url.delete(0, "end"); self.entry_url.insert(0, cam.get("rtsp_url", ""))
        self.entry_notify.delete(0, "end"); self.entry_notify.insert(0, str(cam.get("notify_threshold", 0.87)))
        self.entry_peak.delete(0, "end"); self.entry_peak.insert(0, str(cam.get("peak_detection_threshold", 0.89)))
        self.var_enabled.set(cam.get("enabled", True))
        self.var_live.set(cam.get("show_live_feed", False))

        # Update Telegram Bots in de dropdown (kan veranderd zijn in Config Tab)
        bots = [b['name'] for b in self.cfg.get_telegram_bots()]
        self.combo_bot.configure(values=bots if bots else ["Geen bots gevonden"])
        
        current_bot = cam.get("telegram_bot")
        if current_bot in bots:
            self.combo_bot.set(current_bot)
        elif bots:
            self.combo_bot.set(bots[0])
        else:
             self.combo_bot.set("Geen bots gevonden")

    def add_new_camera(self):
        new_id = f"camera_{uuid.uuid4().hex[:6]}"
        new_cam = {
            "id": new_id,
            "name": "Nieuwe Camera",
            "rtsp_url": "rtsp://admin:pass@192.168.1.x:554/stream",
            "enabled": True,
            "show_live_feed": False,
            "notify_threshold": 0.87,
            "peak_detection_threshold": 0.89,
            "save_images": True,
            "telegram_bot": ""
        }
        self.cfg.update_camera(new_cam)
        self.log_buffers[new_id] = "" 
        self.refresh_camera_list()
        self.select_camera(new_id)

    def save_current_camera(self):
        if not self.selected_camera_id: return
        try:
            data = {
                "id": self.selected_camera_id,
                "name": self.entry_name.get(),
                "rtsp_url": self.entry_url.get(),
                "enabled": self.var_enabled.get(),
                "show_live_feed": self.var_live.get(),
                "notify_threshold": float(self.entry_notify.get()),
                "peak_detection_threshold": float(self.entry_peak.get()),
                "save_images": True,
                "telegram_bot": self.combo_bot.get() if self.combo_bot.get() != "Geen bots gevonden" else ""
            }
            self.cfg.update_camera(data)
            self.refresh_camera_list()
            messagebox.showinfo("Succes", "Camera instellingen opgeslagen.")
        except ValueError:
            messagebox.showerror("Fout", "Controleer of de getallen correct zijn.")

    def delete_current_camera(self):
        if not self.selected_camera_id: return
        if messagebox.askyesno("Bevestig", "Weet je zeker dat je deze camera wilt verwijderen?"):
            if self.selected_camera_id in self.log_buffers:
                del self.log_buffers[self.selected_camera_id]
            self.cfg.delete_camera(self.selected_camera_id)
            self.selected_camera_id = None
            self.refresh_camera_list()
            self.log_box.delete("0.0", "end")

    # ==========================================
    #  PROCESS CONTROL
    # ==========================================
    def start_process(self):
        if not self.selected_camera_id: return
        self.pm.start_camera(self.selected_camera_id)
        self.refresh_camera_list()

    def stop_process(self):
        if not self.selected_camera_id: return
        self.pm.stop_camera(self.selected_camera_id)
        self.refresh_camera_list()

    def stop_all_processes(self):
        if messagebox.askyesno("Stop Alles", "Weet je zeker dat je alle camera processen wilt stoppen?"):
            self.pm.stop_all()
            self.refresh_camera_list()

    def start_all_processes(self):
        if not self.cfg.get_cameras(): return
        
        def start_sequence():
            for cam in self.cfg.get_cameras():
                if cam.get("enabled", False):
                    self.pm.start_camera(cam["id"])
                    self.append_log("SYSTEM", f"{cam['id']} gestart via Start ALL")
                    # We gebruiken master.after om UI updates te triggeren vanuit thread
                    self.master.after(0, self.refresh_camera_list)
                    time.sleep(2)
        
        threading.Thread(target=start_sequence, daemon=True).start()

    # ==========================================
    #  LOGGING
    # ==========================================
    def update_log_view_for_selected(self):
        self.log_box.delete("0.0", "end")
        if self.selected_camera_id and self.selected_camera_id in self.log_buffers:
            self.log_box.insert("0.0", self.log_buffers[self.selected_camera_id])
        elif self.selected_camera_id:
             self.log_box.insert("0.0", f"--- Log start voor {self.selected_camera_id} ---\n")
        self.log_box.see("end")

    def append_log(self, cam_id, message):
        """
        Deze functie wordt aangeroepen vanuit process_manager (via main_window).
        Gebruikt after(0) om thread-safe te zijn.
        """
        def _update():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"
            
            if cam_id not in self.log_buffers:
                self.log_buffers[cam_id] = ""
            
            self.log_buffers[cam_id] += log_line
            
            # Buffer beperken
            if len(self.log_buffers[cam_id]) > 50000:
                self.log_buffers[cam_id] = self.log_buffers[cam_id][-40000:]
            
            # Update textbox alleen als we naar deze camera kijken
            # Of als het een SYSTEM bericht is en we in de log tab zitten
            is_visible = (self.selected_camera_id == cam_id)
            is_system = ("SYSTEM" in str(cam_id))
            
            if is_visible or is_system:
                self.log_box.insert("end", log_line if is_visible else f"[SYSTEM] {message}\n")
                self.log_box.see("end")
            
            # Lijst verversen (voor 'play' icoontje status)
            if "status changed" in message.lower():
                self.refresh_camera_list()
                
        self.master.after(0, _update)