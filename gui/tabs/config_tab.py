import customtkinter as ctk
from .sub_cowcatcher import CowCatcherSettings
from .sub_calving import CalvingSettings
from .sub_telegram import TelegramSettings

RAL_6002 = "#2D572C"

class ConfigTab(ctk.CTkFrame):
    def __init__(self, parent, config_manager, main_app_ref):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1) 
        
        ctk.CTkLabel(self.sidebar, text="CONFIGURATIE", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        self.btn_cow = ctk.CTkButton(self.sidebar, text="CowCatcher", fg_color="transparent", command=lambda: self.show_view("cow"))
        self.btn_cow.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.btn_calv = ctk.CTkButton(self.sidebar, text="CalvingCatcher", fg_color="transparent", command=lambda: self.show_view("calv"))
        self.btn_calv.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_tele = ctk.CTkButton(self.sidebar, text="Telegram", fg_color="transparent", command=lambda: self.show_view("tele"))
        self.btn_tele.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.views = {
            "cow": CowCatcherSettings(self.content_area, self.cfg),
            "calv": CalvingSettings(self.content_area, self.cfg),
            "tele": TelegramSettings(self.content_area, self.cfg)
        }
        
        self.show_view("cow")

    def show_view(self, name):
        for view in self.views.values(): view.pack_forget()
        self.btn_cow.configure(fg_color="transparent")
        self.btn_calv.configure(fg_color="transparent")
        self.btn_tele.configure(fg_color="transparent")

        self.views[name].pack(fill="both", expand=True)
        
        if name == "cow": self.btn_cow.configure(fg_color="gray")
        elif name == "calv": self.btn_calv.configure(fg_color="gray")
        elif name == "tele": self.btn_tele.configure(fg_color="gray")