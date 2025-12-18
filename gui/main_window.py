import customtkinter as ctk
from tkinter import messagebox
from .tabs.camera_tab import CameraTab
from .tabs.config_tab import ConfigTab

# Stijl constanten
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

        # Layout setup
        self.pack(fill="both", expand=True)
        self.grid_rowconfigure(0, weight=0)  # Top bar
        self.grid_rowconfigure(1, weight=1)  # Content area
        self.grid_columnconfigure(0, weight=1)

        self.create_top_bar()
        self.create_content_area()

    def create_top_bar(self):
        self.top_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=RAL_6002)
        self.top_frame.grid(row=0, column=0, sticky="new")
        self.top_frame.grid_columnconfigure(0, weight=1)

        # Titel
        self.lbl_title = ctk.CTkLabel(self.top_frame, text="CowCatcher AI", 
                                      font=ctk.CTkFont(size=24, weight="bold"), 
                                      text_color="white")
        self.lbl_title.pack(side="left", padx=20, pady=5)

        # Help knop
        self.btn_help = ctk.CTkButton(
            self.top_frame, text="❓ Help", width=80, fg_color="white",
            text_color="black", hover_color="#DDDDDD", command=self.open_help_popup
        )
        self.btn_help.pack(side="right", padx=10)

        # Hoofd Tabs (Switch)
        self.main_tabs = ctk.CTkTabview(self.top_frame, height=40, width=400, 
                                        fg_color=RAL_6002, command=self.on_tab_change)
        self.main_tabs.pack(side="right", padx=10, pady=5)
        self.main_tabs.add("Overzicht Camera's")
        self.main_tabs.add("Configuratie")
        
        # Styling van de tab buttons
        self.main_tabs.configure(segmented_button_selected_color=COLOR_HOVER, 
                                 segmented_button_selected_hover_color=COLOR_HOVER)
        self.main_tabs.set("Overzicht Camera's")

    def create_content_area(self):
        # Container voor de tabbladen
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")

        # Initialiseer de sub-schermen
        self.camera_view = CameraTab(self.content_frame, self.cfg, self.pm, self)
        self.config_view = ConfigTab(self.content_frame, self.cfg, self)

        # Start met Camera view
        self.camera_view.pack(fill="both", expand=True)

    def on_tab_change(self):
        current = self.main_tabs.get()
        # Verberg alles
        self.camera_view.pack_forget()
        self.config_view.pack_forget()

        if current == "Overzicht Camera's":
            self.camera_view.pack(fill="both", expand=True)
        elif current == "Configuratie":
            self.config_view.pack(fill="both", expand=True)

    def open_help_popup(self):
        help_win = ctk.CTkToplevel(self)
        help_win.title("CowCatcher AI – Help")
        help_win.geometry("600x500")
        ctk.CTkLabel(help_win, text="Handleiding", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=10)
        # ... rest van help tekst ...
        
    # Proxy method voor logging (zodat app.py dit kan aanroepen zonder te weten welke tab open is)
    def append_log(self, cam_id, message):
        self.camera_view.append_log(cam_id, message)