import customtkinter as ctk

class RTSPHelper(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Camera RTSP Helper")
        
        # --- Venster Grootte en Centreren ---
        width = 450
        height = 580 # Iets hoger gemaakt voor het extra veld
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.callback = callback
        self.after(100, self.lift)
        self.attributes("-topmost", True)

        # Kleur instellingen
        self.color_normal = "#343638"
        self.color_locked = "#151515"

        # Basis paden (worden overschreven door NVR logica indien van toepassing)
        self.brands = {
            "Reolink": "/h264Preview_01_main",
            "Dahua": "/cam/realmonitor?channel=1&subtype=0",
            "Hikvision": "/Streaming/Channels/101",
            "Amcrest": "/cam/realmonitor?channel=1&subtype=0",
            "Swann": "/cam/realmonitor?channel=1&subtype=0",
            "Annke": "/Streaming/Channels/101",
            "Axis": "/axis-media/media.amp?videocodec=h264",
            "Foscam": "/videoMain",
            "TP-Link": "/stream1",
            "Tapo": "/stream1",
            "Uniview": "/unicast/c1/s0/live",
            "ctronics": "/11", 
            "custom": "/"
        }

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="RTSP Configurator", font=("", 16, "bold")).pack(pady=10)

        # 1. Merk Selectie
        ctk.CTkLabel(self, text="Selecteer Merk:").pack(pady=(5, 0))
        self.brand_var = ctk.StringVar(value="Reolink")
        self.brand_menu = ctk.CTkComboBox(self, values=list(self.brands.keys()), variable=self.brand_var, width=250)
        self.brand_menu.pack(pady=5)

        # 2. IP Adres
        ctk.CTkLabel(self, text="IP Adres:").pack(pady=(5, 0))
        ip_frame = ctk.CTkFrame(self, fg_color="transparent")
        ip_frame.pack(pady=5)

        self.chk_ip = ctk.CTkCheckBox(ip_frame, text="", width=20, command=self.toggle_ip_prefix)
        self.chk_ip.pack(side="left", padx=(0, 10))

        self.entry_ip_prefix = ctk.CTkEntry(ip_frame, width=140, justify="right")
        self.entry_ip_prefix.insert(0, "192.168.178.") 
        self.entry_ip_prefix.configure(state="disabled", fg_color=self.color_locked) 
        self.entry_ip_prefix.pack(side="left", padx=(0, 2)) 

        self.entry_ip_suffix = ctk.CTkEntry(ip_frame, width=60, placeholder_text="XXX")
        self.entry_ip_suffix.pack(side="left")

        # 3. Wachtwoord
        ctk.CTkLabel(self, text="Wachtwoord:").pack(pady=(5, 0))
        self.entry_pass = ctk.CTkEntry(self, placeholder_text="wachtwoord", width=250)
        self.entry_pass.pack(pady=5)

        # 4. Gebruikersnaam
        ctk.CTkLabel(self, text="Gebruikersnaam:").pack(pady=(5, 0))
        user_frame = ctk.CTkFrame(self, fg_color="transparent")
        user_frame.pack(pady=5)

        self.chk_user = ctk.CTkCheckBox(user_frame, text="", width=20, command=self.toggle_username)
        self.chk_user.pack(side="left", padx=(0, 10))

        self.entry_user = ctk.CTkEntry(user_frame, width=200)
        self.entry_user.insert(0, "admin")
        self.entry_user.configure(state="disabled", fg_color=self.color_locked)
        self.entry_user.pack(side="left")

        # 5. Poort
        ctk.CTkLabel(self, text="Poort (Standaard 554):").pack(pady=(5, 0))
        port_frame = ctk.CTkFrame(self, fg_color="transparent")
        port_frame.pack(pady=5)

        self.chk_port = ctk.CTkCheckBox(port_frame, text="", width=20, command=self.toggle_port)
        self.chk_port.pack(side="left", padx=(0, 10))

        self.entry_port = ctk.CTkEntry(port_frame, width=200)
        self.entry_port.insert(0, "554")
        self.entry_port.configure(state="disabled", fg_color=self.color_locked)
        self.entry_port.pack(side="left")

        # 6. NVR Kanaal (NIEUW)
        ctk.CTkLabel(self, text="NVR Kanaal:").pack(pady=(5, 0))
        nvr_frame = ctk.CTkFrame(self, fg_color="transparent")
        nvr_frame.pack(pady=5)

        self.chk_nvr = ctk.CTkCheckBox(nvr_frame, text="", width=20, command=self.toggle_nvr)
        self.chk_nvr.pack(side="left", padx=(0, 10))

        self.entry_nvr = ctk.CTkEntry(nvr_frame, width=200)
        self.entry_nvr.insert(0, "1") # Standaard op 1
        self.entry_nvr.configure(state="disabled", fg_color=self.color_locked)
        self.entry_nvr.pack(side="left")

        # Knop
        self.btn_gen = ctk.CTkButton(self, text="Invoegen in Instellingen", fg_color="#2D572C", command=self.generate)
        self.btn_gen.pack(pady=30)

    # --- Toggle Functies ---
    def toggle_ip_prefix(self):
        if self.chk_ip.get() == 1:
            self.entry_ip_prefix.configure(state="normal", fg_color=self.color_normal)
        else:
            self.entry_ip_prefix.configure(state="disabled", fg_color=self.color_locked)

    def toggle_username(self):
        if self.chk_user.get() == 1:
            self.entry_user.configure(state="normal", fg_color=self.color_normal)
        else:
            self.entry_user.configure(state="disabled", fg_color=self.color_locked)

    def toggle_port(self):
        if self.chk_port.get() == 1:
            self.entry_port.configure(state="normal", fg_color=self.color_normal)
        else:
            self.entry_port.configure(state="disabled", fg_color=self.color_locked)

    def toggle_nvr(self):
        if self.chk_nvr.get() == 1:
            self.entry_nvr.configure(state="normal", fg_color=self.color_normal)
        else:
            self.entry_nvr.configure(state="disabled", fg_color=self.color_locked)

    def generate(self):
        brand = self.brand_var.get()
        
        # Gegevens ophalen
        ip_prefix = self.entry_ip_prefix.get()
        ip_suffix = self.entry_ip_suffix.get()
        full_ip = f"{ip_prefix}{ip_suffix}"
        user = self.entry_user.get()
        password = self.entry_pass.get()
        port = self.entry_port.get()
        
        # --- NVR / Kanaal Logica ---
        try:
            channel = int(self.entry_nvr.get())
        except ValueError:
            channel = 1 # Fallback als er tekst ipv cijfer wordt ingevoerd

        # Hier bepalen we het pad op basis van het merk én het kanaalnummer
        if brand == "Reolink":
            # Reolink: /h264Preview_01_main (Let op de leading zero: 01, 02)
            path = f"/h264Preview_{channel:02d}_main"
            
        elif brand in ["Dahua", "Amcrest", "Swann"]:
            # Dahua stijl: channel=1, channel=2
            path = f"/cam/realmonitor?channel={channel}&subtype=0"
            
        elif brand in ["Hikvision", "Annke"]:
            # Hikvision NVR stijl: 101 (ch1), 201 (ch2), etc.
            # We plakken het kanaalnummer voor '01'
            path = f"/Streaming/Channels/{channel}01"
            
        elif brand == "Uniview":
            # Uniview: unicast/c1/s0/live
            path = f"/unicast/c{channel}/s0/live"
            
        else:
            # Fallback voor merken zonder NVR logica of Custom
            path = self.brands.get(brand, "/")

        # RTSP String bouwen
        if user and password:
            rtsp_url = f"rtsp://{user}:{password}@{full_ip}:{port}{path}"
        else:
            rtsp_url = f"rtsp://{full_ip}:{port}{path}"

        self.callback(rtsp_url)
        self.destroy()