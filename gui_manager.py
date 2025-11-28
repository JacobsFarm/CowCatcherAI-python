import customtkinter as ctk
from tkinter import messagebox, filedialog
import uuid
from datetime import datetime
import json # Nodig voor de config tabs
import threading, time

# Kleuren
RAL_6002 = "#2D572C"  # Loofgroen
COLOR_HOVER = "#3A6B39"
COLOR_BG = "#1E1E1E"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class CowCatcherGUI(ctk.CTkFrame):
    def __init__(self, master, config_manager, process_manager):
        super().__init__(master)
        self.master = master
        self.cfg = config_manager
        self.pm = process_manager
        
        self.selected_camera_id = None
        # Dictionary om logs per camera op te slaan: {'cam_id': "regel1\nregel2\n"}
        self.log_buffers = {} 
        
        self.pack(fill="both", expand=True)

        # Nieuwe Grid Layout:
        # Rij 0: Top Bar (over 2 kolommen)
        # Rij 1: Links (Sidebar) | Rechts (Content)
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=0)   
        self.grid_rowconfigure(1, weight=1)   

        self.create_top_bar()
        self.create_side_and_main_frames()
        
        # Laad initiële data
        self.refresh_camera_list()
        
        # Selecteer de eerste camera indien beschikbaar
        if self.cfg.get_cameras():
            self.select_camera(self.cfg.get_cameras()[0]['id'])

    def create_top_bar(self):
        """Creëert de bovenbalk met de titel en de hoofd-tabs."""
        # Frame voor de bovenbalk (fg_color=RAL_6002 om de top bar groen te maken)
        self.top_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=RAL_6002)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="new")
        self.top_frame.grid_columnconfigure(0, weight=1)

        # Titel links
        self.lbl_title = ctk.CTkLabel(self.top_frame, text="CowCatcher AI", 
                                      font=ctk.CTkFont(size=24, weight="bold"), 
                                      text_color="white")
        self.lbl_title.pack(side="left", padx=20, pady=5)

                # HELP knop rechts in de top bar
        self.btn_help = ctk.CTkButton(
            self.top_frame,
            text="❓ Help",
            width=80,
            fg_color="white",
            text_color="black",
            hover_color="#DDDDDD",
            command=self.open_help_popup
        )
        self.btn_help.pack(side="right", padx=10)

        
        # Hoofd Tabs rechts
        self.main_tabs = ctk.CTkTabview(self.top_frame, height=40, width=400, 
                                        fg_color=RAL_6002, command=self.on_main_tab_change)
        self.main_tabs.pack(side="right", padx=10, pady=5)
        
        # Tabs aanmaken:
        self.tab_overview = self.main_tabs.add("Overzicht Camera's")
        self.tab_config = self.main_tabs.add("Configuratie")
        
        # Zorg dat de tabs er uitzien als knoppen in de top bar
        self.main_tabs.configure(segmented_button_selected_color=COLOR_HOVER, 
                                 segmented_button_selected_hover_color=COLOR_HOVER)
        
        self.main_tabs.set("Overzicht Camera's")

    def create_side_and_main_frames(self):
        """Creëert de containers voor de sidebar en de hoofdcontent (Rij 1)."""
        # Zijbalk Container (Links)
        self.sidebar_container = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar_container.grid(row=1, column=0, sticky="nsew")
        self.sidebar_container.grid_rowconfigure(0, weight=1)

        # Hoofd Content Container (Rechts)
        self.main_content_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_content_container.grid(row=1, column=1, sticky="nsew")
        self.main_content_container.grid_rowconfigure(0, weight=1)
        self.main_content_container.grid_columnconfigure(0, weight=1)
        
        # Roep de setup functies aan om de inhoud te creëren
        self.setup_overview_section()
        self.setup_config_section()
        
        # Begin met de 'Overzicht' sectie zichtbaar
        self.overview_frame.pack(fill="both", expand=True)
        self.config_frame.pack_forget()
        self.sidebar_config.pack_forget()
        self.sidebar_camera.pack(fill="both", expand=True)

    def on_main_tab_change(self):
        """Wordt aangeroepen als de gebruiker wisselt tussen 'Overzicht' en 'Configuratie'"""
        current_tab = self.main_tabs.get()
        
        # Wissel de Grote Content Area
        if current_tab == "Overzicht Camera's":
            self.overview_frame.pack(fill="both", expand=True)
            self.config_frame.pack_forget()
            
            # Wissel de Sidebar inhoud naar Camera Lijst
            self.sidebar_config.pack_forget()
            self.sidebar_camera.pack(fill="both", expand=True)
            
        elif current_tab == "Configuratie":
            self.config_frame.pack(fill="both", expand=True)
            self.overview_frame.pack_forget()
            
            # Wissel de Sidebar inhoud naar Config Navigatie
            self.sidebar_camera.pack_forget()
            self.sidebar_config.pack(fill="both", expand=True)
            
            # Zorg dat de Global settings UI geladen wordt bij de eerste switch
            self.select_config_view("global")
    
    # --- SECTIE 1: OVERZICHT (Camera Lijst + Instellingen/Logs) ---
    def setup_overview_section(self):
        # Frame voor de inhoud van de Overzicht sectie
        self.overview_frame = ctk.CTkFrame(self.main_content_container, fg_color="transparent")
        
        # --- Links: Camera Sidebar Inhoud ---
        self.sidebar_camera = ctk.CTkFrame(self.sidebar_container, corner_radius=0)
        self.sidebar_camera.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self.sidebar_camera, text="CAMERA'S", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        self.btn_add_cam = ctk.CTkButton(self.sidebar_camera, text="+ Nieuwe Camera", fg_color=RAL_6002, hover_color=COLOR_HOVER, command=self.add_new_camera)
        self.btn_add_cam.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Lijst met cameras (scrollable)
        self.scroll_cams = ctk.CTkScrollableFrame(self.sidebar_camera, label_text="")
        self.scroll_cams.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        # --- Rechts: Tabs voor de geselecteerde Camera ---
        self.cam_tabs = ctk.CTkTabview(self.overview_frame, fg_color="transparent")
        self.cam_tabs.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.tab_cam = self.cam_tabs.add("Camera Instellingen")
        self.tab_logs = self.cam_tabs.add("Status & Logs")
        
        # Gebruik de bestaande setup functies, maar verwijs naar de nieuwe tabs
        self.setup_camera_tab(self.tab_cam)
        self.setup_log_tab(self.tab_logs)

    # --- SECTIE 2: CONFIGURATIE (Global/Telegram Navigatie + Formulieren) ---
    def setup_config_section(self):
        # Frame voor de inhoud van de Configuratie sectie
        self.config_frame = ctk.CTkFrame(self.main_content_container, fg_color="transparent")

        # --- Links: Configuratie Sidebar Inhoud ---
        self.sidebar_config = ctk.CTkFrame(self.sidebar_container, corner_radius=0)
        self.sidebar_config.grid_rowconfigure(2, weight=1)
        
        ctk.CTkLabel(self.sidebar_config, text="CONFIGURATIE", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.btn_global = ctk.CTkButton(self.sidebar_config, text="Global Settings", command=lambda: self.select_config_view("global"), fg_color="gray", hover_color=COLOR_HOVER)
        self.btn_global.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        self.btn_telegram = ctk.CTkButton(self.sidebar_config, text="Telegram Config", command=lambda: self.select_config_view("telegram"), fg_color="transparent", hover_color=COLOR_HOVER)
        self.btn_telegram.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        # --- Rechts: Container voor Global/Telegram formulieren ---
        self.config_content = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.config_content.pack(fill="both", expand=True, padx=20, pady=20)

        # De Global en Telegram formulieren worden hier direct in gepakt
        self.tab_global = ctk.CTkFrame(self.config_content, fg_color="transparent")
        self.tab_tele = ctk.CTkFrame(self.config_content, fg_color="transparent")
        
        # Gebruik de bestaande setup functies, maar verwijs naar de nieuwe frames
        self.setup_global_tab(self.tab_global)
        self.setup_telegram_tab(self.tab_tele)

    def select_config_view(self, view_name):
        """Wisselt tussen Global en Telegram settings en update de sidebar knoppen."""
        self.tab_global.pack_forget()
        self.tab_tele.pack_forget()

        # Reset knop kleuren
        self.btn_global.configure(fg_color="transparent")
        self.btn_telegram.configure(fg_color="transparent")

        if view_name == "global":
            self.tab_global.pack(fill="both", expand=True)
            self.load_global_settings_ui() 
            self.btn_global.configure(fg_color="gray")
        elif view_name == "telegram":
            self.tab_tele.pack(fill="both", expand=True)
            self.load_telegram_ui() 
            self.btn_telegram.configure(fg_color="gray")

    # --- SIDEBAR LOGIC ---
    def refresh_camera_list(self):
        # Verwijder oude knoppen
        for widget in self.scroll_cams.winfo_children():
            widget.destroy()

        cameras = self.cfg.get_cameras()
        for cam in cameras:
            # Zorg dat er een log buffer bestaat voor elke camera
            if cam['id'] not in self.log_buffers:
                self.log_buffers[cam['id']] = ""

            text = f"{cam.get('name', 'Naamloos')}\n({cam['id']})"
            
            btn = ctk.CTkButton(self.scroll_cams, text=text, 
                                fg_color="transparent", border_width=1, border_color="gray",
                                command=lambda cid=cam['id']: self.select_camera(cid))
            btn.pack(fill="x", pady=2)

            # Kleine indicator als het draait
            if self.pm.is_running(cam['id']):
                btn.configure(border_color=RAL_6002, text=f"▶ {text}")
            
            # Markeer de geselecteerde camera
            if cam['id'] == self.selected_camera_id:
                btn.configure(fg_color=COLOR_HOVER, border_color=RAL_6002)

    def select_camera(self, cam_id):
        self.selected_camera_id = cam_id
        
        # 1. Vul het instellingen formulier
        self.populate_camera_form(cam_id)
        
        # 2. Update de LOG tab met de geschiedenis van DEZE camera
        self.update_log_view_for_selected()
        
        # 3. Update de sidebar om de selectie te markeren
        self.refresh_camera_list()
        
        # 4. Update titel van de log tab buttons
        self.btn_start.configure(text=f"Start {cam_id}")
        self.btn_stop.configure(text=f"Stop {cam_id}")

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
        self.log_buffers[new_id] = "" # Init buffer
        self.refresh_camera_list()
        self.select_camera(new_id)

    # --- TAB: CAMERA SETTINGS ---
    def setup_camera_tab(self, frame):
        frame.grid_columnconfigure(1, weight=1)

        # Formulier velden
        ctk.CTkLabel(frame, text="Camera Naam:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_name = ctk.CTkEntry(frame)
        self.entry_name.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame, text="RTSP URL:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_url = ctk.CTkEntry(frame, placeholder_text="rtsp://user:pass@ip...")
        self.entry_url.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame, text="Telegram Bot:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.combo_bot = ctk.CTkComboBox(frame, values=["Geen"])
        self.combo_bot.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Sliders / Thresholds
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

        # Save Button
        self.btn_save_cam = ctk.CTkButton(frame, text="Instellingen Opslaan", fg_color=RAL_6002, command=self.save_current_camera)
        self.btn_save_cam.grid(row=8, column=1, padx=10, pady=20, sticky="e")
        
        self.btn_del_cam = ctk.CTkButton(frame, text="Camera Verwijderen", fg_color="#8B0000", hover_color="#500000", command=self.delete_current_camera)
        self.btn_del_cam.grid(row=8, column=0, padx=10, pady=20, sticky="w")

    def populate_camera_form(self, cam_id):
        cam = self.cfg.get_camera_by_id(cam_id)
        if not cam: return

        self.entry_name.delete(0, "end"); self.entry_name.insert(0, cam.get("name", ""))
        self.entry_url.delete(0, "end"); self.entry_url.insert(0, cam.get("rtsp_url", ""))
        self.entry_notify.delete(0, "end"); self.entry_notify.insert(0, str(cam.get("notify_threshold", 0.87)))
        self.entry_peak.delete(0, "end"); self.entry_peak.insert(0, str(cam.get("peak_detection_threshold", 0.89)))
        self.var_enabled.set(cam.get("enabled", True))
        self.var_live.set(cam.get("show_live_feed", False))

        bots = [b['name'] for b in self.cfg.get_telegram_bots()]
        self.combo_bot.configure(values=bots if bots else ["Geen bots gevonden"])
        current_bot = cam.get("telegram_bot")
        if current_bot in bots:
            self.combo_bot.set(current_bot)
        elif bots:
            self.combo_bot.set(bots[0])
        else:
             self.combo_bot.set("Geen bots gevonden")


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
            messagebox.showerror("Fout", "Controleer of de getallen (thresholds) correct zijn (punt in plaats van komma).")

    def delete_current_camera(self):
        if not self.selected_camera_id: return
        if messagebox.askyesno("Bevestig", "Weet je zeker dat je deze camera wilt verwijderen?"):
            # Verwijder ook de log buffer
            if self.selected_camera_id in self.log_buffers:
                del self.log_buffers[self.selected_camera_id]
                
            self.cfg.delete_camera(self.selected_camera_id)
            self.selected_camera_id = None
            self.refresh_camera_list()
            # Leeg de views
            self.log_box.delete("0.0", "end")

    def open_help_popup(self):
        """Popup venster met scrollbare helptekst."""
        help_win = ctk.CTkToplevel(self)
        help_win.title("CowCatcher AI – Help & Uitleg")
        help_win.geometry("600x500")
        help_win.grab_set()  # modal

        # Titel
        title = ctk.CTkLabel(
            help_win,
            text="📘 CowCatcher AI – Handleiding",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(pady=10)

        # Scroll Frame
        scroll = ctk.CTkScrollableFrame(help_win, width=560, height=400)
        scroll.pack(padx=10, pady=10, fill="both", expand=True)

        help_text = """
Welkom bij CowCatcher AI!

➡ Deze software monitort koeien via camera’s.
➡ Detecteert tocht/piekactiviteit.
➡ Stuurt meldingen via Telegram bots.
➡ Je kunt meerdere camera’s tegelijk laten draaien.

———————————————
📌 BELANGRIJKSTE ONDERDELEN
———————————————

• Overzicht Camera’s  
  Links zie je alle camera’s.  
  Rechts kun je de instellingen en logs zien.

• Start / Stop Camera  
  Start of stop een specifieke camera.

• Start ALLE camera’s  
  Start elke camera tegelijk.

• Logs  
  Hier zie je realtime status van de AI, verbinding en events.

• Configuratie → Global Settings  
  Algemene instellingen voor het gehele systeem.

• Configuratie → Telegram  
  Voeg hier je Telegram bots toe die meldingen moeten ontvangen.

———————————————
📺 LIVE FEED POPUP
———————————————
Als 'Show Live Feed' aan staat opent een extra venster zodra de camera draait.

———————————————
❓ HEB JE VRAGEN?
———————————————
Stel gerust al je vragen – ik help je verder!
        """

        label = ctk.CTkLabel(scroll, text=help_text, justify="left")
        label.pack(anchor="w", padx=10, pady=10)


    # --- TAB: STATUS & LOGS (Specifiek per camera) ---
    def setup_log_tab(self, frame):
        
        # Control Buttons - Nu specifiek voor de geselecteerde camera
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


        # Log Box
        self.log_box = ctk.CTkTextbox(frame, font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_box.insert("0.0", "Selecteer een camera links om de status te zien.\n")

    def update_log_view_for_selected(self):
        """Ververst de text box met de buffer van de geselecteerde camera"""
        self.log_box.delete("0.0", "end")
        if self.selected_camera_id and self.selected_camera_id in self.log_buffers:
            self.log_box.insert("0.0", self.log_buffers[self.selected_camera_id])
        elif self.selected_camera_id:
             self.log_box.insert("0.0", f"--- Log start voor {self.selected_camera_id} ---\n")
        self.log_box.see("end")

    def append_log(self, cam_id, message):
        """Callback functie aangeroepen vanuit process_manager thread"""
        # Thread-safe GUI update
        def _update():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"
            
            # 1. Altijd opslaan in de buffer van de betreffende camera
            if cam_id not in self.log_buffers:
                self.log_buffers[cam_id] = ""
            self.log_buffers[cam_id] += log_line
            
            # Houd buffer niet oneindig groot (optioneel, bijv max 1000 regels)
            if len(self.log_buffers[cam_id]) > 50000: # grofweg karakters
                self.log_buffers[cam_id] = self.log_buffers[cam_id][-40000:]

            # 2. Als deze camera NU geselecteerd is in de GUI, update dan direct het scherm
            if self.selected_camera_id == cam_id and self.main_tabs.get() == "Overzicht Camera's":
                self.log_box.insert("end", log_line)
                self.log_box.see("end")
                
            # 3. Als het een SYSTEM message is, toon het misschien overal of in een aparte buffer
            if "SYSTEM" in str(cam_id) and self.selected_camera_id and self.main_tabs.get() == "Overzicht Camera's":
                # Voeg toe aan huidige view ter info
                self.log_box.insert("end", f"[SYSTEM] {message}\n")
            
            # 4. Controleer op statusverandering
            self.refresh_camera_list()


        self.master.after(0, _update)

    def start_process(self):
        if not self.selected_camera_id:
            messagebox.showwarning("Let op", "Selecteer eerst een camera links.")
            return
        
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
        """Start alle camera's die in config.json op 'enabled=True' staan, 1 voor 1."""
        if not self.cfg.get_cameras():
            return

        def start_sequence():
            for cam in self.cfg.get_cameras():
                if cam.get("enabled", False):
                    self.pm.start_camera(cam["id"])
                    self.append_log("SYSTEM", f"{cam['id']} gestart via Start ALL")
                    self.refresh_camera_list()
                    time.sleep(2)  # vertraging tussen camera's, aanpasbaar

        threading.Thread(target=start_sequence, daemon=True).start()

# --- TAB: GLOBAL SETTINGS (in Config sectie) ---
    def setup_global_tab(self, frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # We gebruiken een scrollable frame omdat de lijst lang kan zijn
        self.global_scroll = ctk.CTkScrollableFrame(frame, label_text="Global Settings")
        self.global_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.global_scroll.grid_columnconfigure(1, weight=1)

        # Opslag voor de variabelen die we aan de inputs koppelen
        self.global_input_vars = {} 

        # Save knop onderaan
        btn = ctk.CTkButton(frame, text="Global Settings Opslaan", fg_color=RAL_6002, command=self.save_global_settings)
        btn.grid(row=1, column=0, pady=10)
        
        # Laad de UI
        self.load_global_settings_ui()

    def load_global_settings_ui(self):
        # Maak het frame leeg
        for widget in self.global_scroll.winfo_children():
            widget.destroy()

        self.global_input_vars = {}
        settings = self.cfg.get_global_settings()
        
        row = 0
        for key, value in settings.items():
            # Label (links)
            lbl = ctk.CTkLabel(self.global_scroll, text=key.replace("_", " ").title() + ":", anchor="w")
            lbl.grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            # --- 1. MODEL PATH (Met Browse knop) ---
            if key == "model_path":
                # We maken een container frame zodat de Entry en Button naast elkaar staan
                container = ctk.CTkFrame(self.global_scroll, fg_color="transparent")
                container.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                
                var = ctk.StringVar(value=str(value))
                
                # Het invulveld (neemt alle ruimte behalve de knop)
                inp = ctk.CTkEntry(container, textvariable=var)
                inp.pack(side="left", fill="x", expand=True, padx=(0, 5))
                
                # De blader knop
                btn_browse = ctk.CTkButton(container, text="📂", width=40, fg_color=RAL_6002, 
                                           command=lambda v=var: self.browse_for_model(v))
                btn_browse.pack(side="right")
                
                self.global_input_vars[key] = {'type': 'str', 'var': var}

            # --- 2. DROPDOWN (Process Every N Frames) ---
            elif key == "process_every_n_frames":
                var = ctk.StringVar(value=str(value))
                inp = ctk.CTkComboBox(self.global_scroll, values=["1", "2", "3", "4", "5"], variable=var, state="readonly")
                inp.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                self.global_input_vars[key] = {'type': 'int', 'var': var}

            # --- 3. SCHAKELAARS (True/False) ---
            elif isinstance(value, bool):
                var = ctk.BooleanVar(value=value)
                inp = ctk.CTkSwitch(self.global_scroll, text="Actief", variable=var, progress_color=RAL_6002)
                inp.grid(row=row, column=1, padx=10, pady=5, sticky="w")
                self.global_input_vars[key] = {'type': 'bool', 'var': var}
                
            # --- 4. STANDAARD TEKSTVELDEN ---
            else:
                var = ctk.StringVar(value=str(value))
                inp = ctk.CTkEntry(self.global_scroll, textvariable=var)
                inp.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                
                orig_type = 'str'
                if isinstance(value, int): orig_type = 'int'
                elif isinstance(value, float): orig_type = 'float'
                
                self.global_input_vars[key] = {'type': orig_type, 'var': var}
            
            row += 1

    def browse_for_model(self, text_var):
            """Opent verkenner om een .pt bestand te zoeken"""
            filename = filedialog.askopenfilename(
                title="Selecteer AI Model",
                filetypes=[
                ("AI Models", "*.pt *.onnx *.engine"),
                ("PyTorch Model", "*.pt"),
                ("ONNX Model", "*.onnx"),
                ("TensorRT Engine", "*.engine"),
                ("Alle bestanden", "*.*"),
              ]
            )
            # Als de gebruiker een bestand kiest (en niet op Annuleren drukt)
            if filename:
                # Update de variabele in het invulveld
                text_var.set(filename)

    def save_global_settings(self):
        new_settings = {}
        try:
            for key, data in self.global_input_vars.items():
                val = data['var'].get()
                t = data['type']
                
                # Type conversie terug naar origineel formaat
                if t == 'bool':
                    new_settings[key] = bool(val)
                elif t == 'int':
                    new_settings[key] = int(val)
                elif t == 'float':
                    new_settings[key] = float(val)
                else:
                    new_settings[key] = str(val)

            self.cfg.update_global_settings(new_settings)
            messagebox.showinfo("Succes", "Global settings succesvol opgeslagen.")
            
        except ValueError as e:
            messagebox.showerror("Invoer Fout", f"Fout bij het opslaan.\nControleer of alle getallen correct zijn ingevoerd.\n\nDetail: {e}")

    # --- TAB: TELEGRAM (in Config sectie) ---
    def setup_telegram_tab(self, frame):
        # We splitsen het scherm in twee scrollable frames: Bots (boven) en Users (onder)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # --- BOTS SECTIE ---
        self.frame_bots = ctk.CTkScrollableFrame(frame, label_text="Telegram Bots")
        self.frame_bots.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        self.frame_bots.grid_columnconfigure(1, weight=1) # Token kolom krijgt ruimte

        # --- USERS SECTIE ---
        self.frame_users = ctk.CTkScrollableFrame(frame, label_text="Telegram Users")
        self.frame_users.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.frame_users.grid_columnconfigure(1, weight=1) # Chat ID kolom krijgt ruimte

        # --- KNOPPEN BALK ---
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="+ Bot Toevoegen", command=self.add_dummy_bot, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="+ User Toevoegen", command=self.add_dummy_user, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Alles Opslaan", fg_color=RAL_6002, command=self.save_telegram, width=150).pack(side="right", padx=10)

        # Interne lijsten om widgets bij te houden
        self.bot_entries = []
        self.user_entries = []

        self.load_telegram_ui()

    def load_telegram_ui(self):
        # 1. Bots laden
        for widget in self.frame_bots.winfo_children(): widget.destroy()
        self.bot_entries = []
        
        bots = self.cfg.get_telegram_bots()
        # Headers
        ctk.CTkLabel(self.frame_bots, text="Naam", font=("",10,"bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_bots, text="Token", font=("",10,"bold")).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_bots, text="Actief", font=("",10,"bold")).grid(row=0, column=2, sticky="w", padx=5)

        for i, bot in enumerate(bots, start=1):
            self._create_bot_row(i, bot)

        # 2. Users laden
        for widget in self.frame_users.winfo_children(): widget.destroy()
        self.user_entries = []
        
        users = self.cfg.get_telegram_users()
        # Headers
        ctk.CTkLabel(self.frame_users, text="Naam", font=("",10,"bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_users, text="Chat ID", font=("",10,"bold")).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_users, text="Actief", font=("",10,"bold")).grid(row=0, column=2, sticky="w", padx=5)

        for i, user in enumerate(users, start=1):
            self._create_user_row(i, user)

    def _create_bot_row(self, row_idx, bot_data):
        # Naam
        ent_name = ctk.CTkEntry(self.frame_bots, width=120)
        ent_name.insert(0, bot_data.get('name', ''))
        ent_name.grid(row=row_idx, column=0, padx=5, pady=2)
        
        # Token
        ent_token = ctk.CTkEntry(self.frame_bots)
        ent_token.insert(0, bot_data.get('token', ''))
        ent_token.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
        
        # Enabled Switch
        var_en = ctk.BooleanVar(value=bot_data.get('enabled', True))
        sw_en = ctk.CTkSwitch(self.frame_bots, text="", variable=var_en, width=40, progress_color=RAL_6002)
        sw_en.grid(row=row_idx, column=2, padx=5, pady=2)
        
        # Delete knop (klein kruisje)
        btn_del = ctk.CTkButton(self.frame_bots, text="X", width=30, fg_color="red", 
                                command=lambda: self.delete_bot_row(ent_name))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2)

        self.bot_entries.append({
            'name': ent_name,
            'token': ent_token,
            'enabled': var_en,
            'row_widget': btn_del # just to verify existence
        })

    def _create_user_row(self, row_idx, user_data):
        # Naam
        ent_name = ctk.CTkEntry(self.frame_users, width=120)
        ent_name.insert(0, user_data.get('name', ''))
        ent_name.grid(row=row_idx, column=0, padx=5, pady=2)
        
        # Chat ID
        ent_chat = ctk.CTkEntry(self.frame_users)
        ent_chat.insert(0, str(user_data.get('chat_id', '')))
        ent_chat.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
        
        # Enabled Switch
        var_en = ctk.BooleanVar(value=user_data.get('enabled', True))
        sw_en = ctk.CTkSwitch(self.frame_users, text="", variable=var_en, width=40, progress_color=RAL_6002)
        sw_en.grid(row=row_idx, column=2, padx=5, pady=2)

        # Delete knop
        btn_del = ctk.CTkButton(self.frame_users, text="X", width=30, fg_color="red",
                                command=lambda: self.delete_user_row(ent_name))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2)

        self.user_entries.append({
            'name': ent_name,
            'chat_id': ent_chat,
            'enabled': var_en
        })

    def add_dummy_bot(self):
        # Voegt tijdelijk een regel toe in de UI.
        # Een echte save gebeurt pas als op "Alles Opslaan" wordt geklikt.
        # Om het simpel te houden herladen we de UI met 1 extra lege entry in de config data (in memory, niet op schijf)
        # of we tekenen gewoon een nieuwe regel.
        new_idx = len(self.bot_entries) + 1
        self._create_bot_row(new_idx, {"name": "Nieuwe Bot", "token": "", "enabled": True})

    def add_dummy_user(self):
        new_idx = len(self.user_entries) + 1
        self._create_user_row(new_idx, {"name": "Nieuwe User", "chat_id": "", "enabled": True})

    def delete_bot_row(self, entry_widget_ref):
        # Dit is complex om live te verwijderen uit grid, makkelijker is om 
        # de entry als 'deleted' te markeren en te negeren bij save, 
        # of de regel direct weg te halen.
        # Simpele aanpak: Verwijder UI element en haal uit lijst.
        for item in self.bot_entries:
            if item['name'] == entry_widget_ref:
                # Zet waarden op leeg zodat we weten dat we hem niet moeten opslaan of markeer hem
                item['name'].delete(0, "end") # Leeg maken = signaal om niet op te slaan
                item['name'].configure(placeholder_text="VERWIJDERD")
                item['name'].configure(state="disabled")
                break

    def delete_user_row(self, entry_widget_ref):
        for item in self.user_entries:
            if item['name'] == entry_widget_ref:
                item['name'].delete(0, "end")
                item['name'].configure(placeholder_text="VERWIJDERD", state="disabled")
                break

    def save_telegram(self):
            # --- DEEL 1: BOTS ---
            new_bots = []
            for item in self.bot_entries:
                # .strip() haalt spaties weg
                name = item['name'].get().strip()
                
                # Als naam leeg is of gemarkeerd als verwijderd, slaan we hem over
                if not name or item['name'].cget('state') == 'disabled': 
                    continue
                
                # Automatisch ' bot' toevoegen als het er nog niet staat
                if not name.lower().endswith(" bot"):
                    name += " bot"
                
                new_bots.append({
                    "name": name,
                    "token": item['token'].get().strip(),
                    "enabled": item['enabled'].get()
                })

            # --- DEEL 2: USERS ---
            # Let op: deze regel moet recht onder 'new_bots = []' staan
            new_users = []
            for item in self.user_entries:
                name = item['name'].get().strip()
                if not name or item['name'].cget('state') == 'disabled':
                    continue
                
                try:
                    # Zorg dat chat_id een getal is
                    raw_id = item['chat_id'].get().strip()
                    c_id = int(raw_id) if raw_id else 0
                except ValueError:
                    c_id = 0 

                new_users.append({
                    "name": name,
                    "chat_id": c_id,
                    "enabled": item['enabled'].get()
                })

            # --- DEEL 3: OPSLAAN & UI VERVERSEN ---
            self.cfg.update_telegram_config(new_bots, new_users)
            
            # Ververs UI om rijen netjes te maken (verwijderde rijen weghalen)
            self.load_telegram_ui()
            
            # Ververs camera formulier (zodat de nieuwe bot direct in de dropdown staat)
            if self.selected_camera_id:
                self.populate_camera_form(self.selected_camera_id)
                
            messagebox.showinfo("Succes", "Telegram configuratie opgeslagen.")
