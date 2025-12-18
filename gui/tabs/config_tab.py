import customtkinter as ctk
from tkinter import filedialog, messagebox

# Constanten (hetzelfde als in main_window)
RAL_6002 = "#2D572C"
COLOR_HOVER = "#3A6B39"

class ConfigTab(ctk.CTkFrame):
    def __init__(self, parent, config_manager, main_app_ref):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        self.main_app = main_app_ref
        
        # Variabelen voor opslag van input velden
        self.global_input_vars = {}
        self.bot_entries = []
        self.user_entries = []

        # --- Layout Opbouw ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Sidebar (Links)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(3, weight=1) # Spacer onderaan
        
        ctk.CTkLabel(self.sidebar, text="CONFIGURATIE", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        
        self.btn_global = ctk.CTkButton(self.sidebar, text="Global Settings", fg_color="gray", command=lambda: self.show_view("global"))
        self.btn_global.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_telegram = ctk.CTkButton(self.sidebar, text="Telegram Config", fg_color="transparent", command=lambda: self.show_view("telegram"))
        self.btn_telegram.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # 2. Content Area (Rechts)
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # 3. De twee sub-schermen aanmaken
        self.view_global = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.view_telegram = ctk.CTkFrame(self.content_area, fg_color="transparent")
        
        # Inhoud inladen
        self.setup_global_view()
        self.setup_telegram_view()
        
        # Start met Global view
        self.show_view("global")

    def show_view(self, view_name):
        """Wisselt tussen Global en Telegram weergave"""
        self.view_global.pack_forget()
        self.view_telegram.pack_forget()
        
        # Reset knop kleuren
        self.btn_global.configure(fg_color="transparent")
        self.btn_telegram.configure(fg_color="transparent")

        if view_name == "global":
            self.view_global.pack(fill="both", expand=True)
            self.btn_global.configure(fg_color="gray")
            self.load_global_settings_ui() # Ververs data bij openen
        else:
            self.view_telegram.pack(fill="both", expand=True)
            self.btn_telegram.configure(fg_color="gray")
            self.load_telegram_ui() # Ververs data bij openen

    # ==========================================
    #  GLOBAL SETTINGS LOGICA
    # ==========================================
    def setup_global_view(self):
        self.view_global.grid_rowconfigure(0, weight=1)
        self.view_global.grid_columnconfigure(0, weight=1)
        
        self.global_scroll = ctk.CTkScrollableFrame(self.view_global, label_text="Global Settings")
        self.global_scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.global_scroll.grid_columnconfigure(1, weight=1)
        
        btn_save = ctk.CTkButton(self.view_global, text="Global Settings Opslaan", fg_color=RAL_6002, command=self.save_global_settings)
        btn_save.grid(row=1, column=0, pady=10)

        self.load_global_settings_ui()

    def load_global_settings_ui(self):
        # Maak frame leeg
        for widget in self.global_scroll.winfo_children(): 
            widget.destroy()
            
        self.global_input_vars = {}
        settings = self.cfg.get_global_settings()
        
        row = 0
        for key, value in settings.items():
            # Label
            lbl_text = key.replace("_", " ").title() + ":"
            lbl = ctk.CTkLabel(self.global_scroll, text=lbl_text, anchor="w")
            lbl.grid(row=row, column=0, padx=10, pady=5, sticky="w")
            
            # Input velden logica
            if key == "model_path":
                container = ctk.CTkFrame(self.global_scroll, fg_color="transparent")
                container.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                
                var = ctk.StringVar(value=str(value))
                inp = ctk.CTkEntry(container, textvariable=var)
                inp.pack(side="left", fill="x", expand=True, padx=(0, 5))
                
                btn_browse = ctk.CTkButton(container, text="📂", width=40, fg_color=RAL_6002, 
                                           command=lambda v=var: self.browse_for_model(v))
                btn_browse.pack(side="right")
                self.global_input_vars[key] = {'type': 'str', 'var': var}
                
            elif key == "process_every_n_frames":
                var = ctk.StringVar(value=str(value))
                inp = ctk.CTkComboBox(self.global_scroll, values=["1", "2", "3", "4", "5"], variable=var, state="readonly")
                inp.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                self.global_input_vars[key] = {'type': 'int', 'var': var}
                
            elif isinstance(value, bool):
                var = ctk.BooleanVar(value=value)
                inp = ctk.CTkSwitch(self.global_scroll, text="Actief", variable=var, progress_color=RAL_6002)
                inp.grid(row=row, column=1, padx=10, pady=5, sticky="w")
                self.global_input_vars[key] = {'type': 'bool', 'var': var}
                
            else:
                # Standaard tekst/getal veld
                var = ctk.StringVar(value=str(value))
                inp = ctk.CTkEntry(self.global_scroll, textvariable=var)
                inp.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                
                # Type detectie voor opslaan later
                orig_type = 'str'
                if isinstance(value, int): orig_type = 'int'
                elif isinstance(value, float): orig_type = 'float'
                self.global_input_vars[key] = {'type': orig_type, 'var': var}
                
            row += 1

    def browse_for_model(self, text_var):
        filename = filedialog.askopenfilename(title="Selecteer AI Model",
            filetypes=[("AI Models", "*.pt *.onnx *.engine"), ("PyTorch Model", "*.pt"), ("All Files", "*.*")])
        if filename: 
            text_var.set(filename)

    def save_global_settings(self):
        new_settings = {}
        try:
            for key, data in self.global_input_vars.items():
                val = data['var'].get()
                t = data['type']
                
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
            messagebox.showerror("Invoer Fout", f"Fout bij het opslaan: {e}")

    # ==========================================
    #  TELEGRAM LOGICA
    # ==========================================
    def setup_telegram_view(self):
        self.view_telegram.grid_rowconfigure(0, weight=1)
        self.view_telegram.grid_rowconfigure(1, weight=1)
        self.view_telegram.grid_columnconfigure(0, weight=1)
        
        # Frame voor Bots
        self.frame_bots = ctk.CTkScrollableFrame(self.view_telegram, label_text="Telegram Bots")
        self.frame_bots.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        self.frame_bots.grid_columnconfigure(1, weight=1)
        
        # Frame voor Users
        self.frame_users = ctk.CTkScrollableFrame(self.view_telegram, label_text="Telegram Users")
        self.frame_users.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 10))
        self.frame_users.grid_columnconfigure(1, weight=1)
        
        # Knoppenbalk onderaan
        btn_frame = ctk.CTkFrame(self.view_telegram, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="+ Bot Toevoegen", command=self.add_dummy_bot, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="+ User Toevoegen", command=self.add_dummy_user, width=120).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="Alles Opslaan", fg_color=RAL_6002, command=self.save_telegram, width=150).pack(side="right", padx=10)
        
        self.load_telegram_ui()

    def load_telegram_ui(self):
        # 1. Bots inladen
        for widget in self.frame_bots.winfo_children(): widget.destroy()
        self.bot_entries = []
        bots = self.cfg.get_telegram_bots()
        
        # Headers Bots
        ctk.CTkLabel(self.frame_bots, text="Naam", font=("",10,"bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_bots, text="Token", font=("",10,"bold")).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_bots, text="Actief", font=("",10,"bold")).grid(row=0, column=2, sticky="w", padx=5)
        
        for i, bot in enumerate(bots, start=1): 
            self._create_bot_row(i, bot)

        # 2. Users inladen
        for widget in self.frame_users.winfo_children(): widget.destroy()
        self.user_entries = []
        users = self.cfg.get_telegram_users()
        
        # Headers Users
        ctk.CTkLabel(self.frame_users, text="Naam", font=("",10,"bold")).grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_users, text="Chat ID", font=("",10,"bold")).grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(self.frame_users, text="Actief", font=("",10,"bold")).grid(row=0, column=2, sticky="w", padx=5)
        
        for i, user in enumerate(users, start=1): 
            self._create_user_row(i, user)

    def _create_bot_row(self, row_idx, bot_data):
        ent_name = ctk.CTkEntry(self.frame_bots, width=120)
        ent_name.insert(0, bot_data.get('name', ''))
        ent_name.grid(row=row_idx, column=0, padx=5, pady=2)
        
        ent_token = ctk.CTkEntry(self.frame_bots)
        ent_token.insert(0, bot_data.get('token', ''))
        ent_token.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
        
        var_en = ctk.BooleanVar(value=bot_data.get('enabled', True))
        sw_en = ctk.CTkSwitch(self.frame_bots, text="", variable=var_en, width=40, progress_color=RAL_6002)
        sw_en.grid(row=row_idx, column=2, padx=5, pady=2)
        
        btn_del = ctk.CTkButton(self.frame_bots, text="X", width=30, fg_color="red", command=lambda: self.delete_bot_row(ent_name))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2)
        
        self.bot_entries.append({'name': ent_name, 'token': ent_token, 'enabled': var_en})

    def _create_user_row(self, row_idx, user_data):
        ent_name = ctk.CTkEntry(self.frame_users, width=120)
        ent_name.insert(0, user_data.get('name', ''))
        ent_name.grid(row=row_idx, column=0, padx=5, pady=2)
        
        ent_chat = ctk.CTkEntry(self.frame_users)
        ent_chat.insert(0, str(user_data.get('chat_id', '')))
        ent_chat.grid(row=row_idx, column=1, padx=5, pady=2, sticky="ew")
        
        var_en = ctk.BooleanVar(value=user_data.get('enabled', True))
        sw_en = ctk.CTkSwitch(self.frame_users, text="", variable=var_en, width=40, progress_color=RAL_6002)
        sw_en.grid(row=row_idx, column=2, padx=5, pady=2)
        
        btn_del = ctk.CTkButton(self.frame_users, text="X", width=30, fg_color="red", command=lambda: self.delete_user_row(ent_name))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2)
        
        self.user_entries.append({'name': ent_name, 'chat_id': ent_chat, 'enabled': var_en})

    def add_dummy_bot(self):
        # Voeg een nieuwe lege rij toe
        self._create_bot_row(len(self.bot_entries) + 1, {"name": "Nieuwe Bot", "token": "", "enabled": True})

    def add_dummy_user(self):
        # Voeg een nieuwe lege rij toe
        self._create_user_row(len(self.user_entries) + 1, {"name": "Nieuwe User", "chat_id": "", "enabled": True})

    def delete_bot_row(self, entry_widget_ref):
        # We zetten de widget op disabled om hem te markeren als verwijderd bij opslaan
        # of we halen hem visueel weg. Voor nu visueel markeren als 'leeg':
        entry_widget_ref.delete(0, "end")
        entry_widget_ref.configure(state="disabled", fg_color="red")
        
    def delete_user_row(self, entry_widget_ref):
        entry_widget_ref.delete(0, "end")
        entry_widget_ref.configure(state="disabled", fg_color="red")

    def save_telegram(self):
        new_bots = []
        for item in self.bot_entries:
            name = item['name'].get().strip()
            # Als naam leeg is of veld is disabled (verwijderd), sla over
            if not name or item['name'].cget('state') == 'disabled': continue
            
            if not name.lower().endswith(" bot"): name += " bot"
            
            new_bots.append({
                "name": name, 
                "token": item['token'].get().strip(), 
                "enabled": item['enabled'].get()
            })

        new_users = []
        for item in self.user_entries:
            name = item['name'].get().strip()
            if not name or item['name'].cget('state') == 'disabled': continue
            
            try: 
                c_id = int(item['chat_id'].get().strip())
            except ValueError: 
                c_id = 0 
            
            new_users.append({
                "name": name, 
                "chat_id": c_id, 
                "enabled": item['enabled'].get()
            })

        self.cfg.update_telegram_config(new_bots, new_users)
        
        # Herlaad de UI om alles weer netjes te tonen
        self.load_telegram_ui()
        messagebox.showinfo("Succes", "Telegram configuratie opgeslagen.")