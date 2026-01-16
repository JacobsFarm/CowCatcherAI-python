import customtkinter as ctk
from tkinter import messagebox
from .tabs.camera_tab import CameraTab
from .tabs.config_tab import ConfigTab
from .tabs.help import HelpPopup

RAL_6002 = "#2D572C"
COLOR_HOVER = "#3A6B39"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class CowCatcherGUI(ctk.CTkFrame):
    def __init__(self, master, config_manager, process_manager):
        super().__init__(master)
        self.master = master
        self.cfg = config_manager
        self.pm = process_manager

        self.pack(fill="both", expand=True)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_top_bar()
        self.create_content_area()

    def create_top_bar(self):
        self.top_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=RAL_6002)
        self.top_frame.grid(row=0, column=0, sticky="new")
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(self.top_frame, text="CowCatcher AI", 
                                      font=ctk.CTkFont(size=24, weight="bold"), 
                                      text_color="white")
        self.lbl_title.pack(side="left", padx=20, pady=5)

        self.btn_help = ctk.CTkButton(
            self.top_frame, text="❓ Help", width=80, fg_color="white",
            text_color="black", hover_color="#DDDDDD", command=self.open_help_popup
        )
        self.btn_help.pack(side="right", padx=10)

        self.main_tabs = ctk.CTkTabview(self.top_frame, height=40, width=400, 
                                        fg_color=RAL_6002, command=self.on_tab_change)
        self.main_tabs.pack(side="right", padx=10, pady=5)
        self.main_tabs.add("Camera Overview")
        self.main_tabs.add("Configuration")
        
        self.main_tabs.configure(segmented_button_selected_color=COLOR_HOVER, 
                                 segmented_button_selected_hover_color=COLOR_HOVER)
        self.main_tabs.set("Camera Overview")

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")

        self.camera_view = CameraTab(self.content_frame, self.cfg, self.pm, self)
        self.config_view = ConfigTab(self.content_frame, self.cfg, self)

        self.camera_view.pack(fill="both", expand=True)

    def on_tab_change(self):
            current = self.main_tabs.get()
            
            self.camera_view.pack_forget()
            self.config_view.pack_forget()

            if current == "Camera Overview":
                self.camera_view.pack(fill="both", expand=True)
                
                if self.camera_view.selected_camera_id:
                    self.camera_view.populate_camera_form(self.camera_view.selected_camera_id)
                    
            elif current == "Configuration":
                self.config_view.pack(fill="both", expand=True)

    def open_help_popup(self):
        HelpPopup(self)

    def append_log(self, cam_id, message):
        self.camera_view.append_log(cam_id, message)