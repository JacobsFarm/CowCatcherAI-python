import customtkinter as ctk
import uuid
from .camera_settings import CameraSettingsFrame
from .camera_status import CameraStatusFrame

RAL_6002 = "#2D572C"
COLOR_HOVER = "#3A6B39"

class CameraTab(ctk.CTkFrame):
    def __init__(self, parent, config_manager, process_manager, main_app_ref):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        self.pm = process_manager
        self.main_app = main_app_ref
        self.selected_camera_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.sidebar, text="CAMERAS", font=("", 14, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        ctk.CTkButton(self.sidebar, text="+ New Camera", fg_color=RAL_6002, command=self.add_new_camera)\
            .grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.scroll_cams = ctk.CTkScrollableFrame(self.sidebar, label_text="")
        self.scroll_cams.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # 2. Main Content
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.tabs = ctk.CTkTabview(self.main_area)
        self.tabs.pack(fill="both", expand=True)
        
        settings_tab = self.tabs.add("Settings")
        status_tab = self.tabs.add("Status & Logs")

        # 3. Load Sub-modules
        self.settings_view = CameraSettingsFrame(settings_tab, self.cfg, self.refresh_camera_list)
        self.settings_view.pack(fill="both", expand=True)

        self.status_view = CameraStatusFrame(status_tab, self.pm, self.refresh_camera_list)
        self.status_view.pack(fill="both", expand=True)

        self.refresh_camera_list()
        cameras = self.cfg.get_cameras()
        if cameras: 
            self.select_camera(cameras[0]['id'])

    def refresh_camera_list(self):
        for w in self.scroll_cams.winfo_children(): 
            w.destroy()
        
        for cam in self.cfg.get_cameras():
            cid = cam['id']
            c_type = cam.get('type', 'cowcatcher')
            name = cam.get('name', 'Unnamed')
            
            btn = ctk.CTkButton(self.scroll_cams, text=f"{name}\n({c_type})", 
                                fg_color="transparent", border_width=1, border_color="gray",
                                command=lambda c=cid: self.select_camera(c))
            btn.pack(fill="x", pady=2)
            
            if self.pm.is_running(cid):
                btn.configure(border_color=RAL_6002, text=f"▶ {name}\n({c_type})")
            
            if cid == self.selected_camera_id:
                btn.configure(fg_color=COLOR_HOVER, border_color=RAL_6002)

    def select_camera(self, cam_id):
        self.selected_camera_id = cam_id
        self.refresh_camera_list()
        
        self.settings_view.load_camera(cam_id)
        self.status_view.set_camera(cam_id)

    def add_new_camera(self):
        new_id = f"camera_{uuid.uuid4().hex[:6]}"
        self.cfg.update_camera({"id": new_id, "name": "New Camera", "type": "cowcatcher", "enabled": True})
        self.refresh_camera_list()
        self.select_camera(new_id)

    def append_log(self, cam_id, message):
        self.master.after(0, lambda: self.status_view.append_log(cam_id, message))
    
    def populate_camera_form(self, cam_id):
        self.select_camera(cam_id)