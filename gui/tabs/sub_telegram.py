import customtkinter as ctk
from tkinter import messagebox

RAL_6002 = "#2D572C"

class TelegramSettings(ctk.CTkFrame):
    def __init__(self, parent, config_manager):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        # We houden hier lijsten bij van dictionaries die de widgets bevatten
        self.bot_entries = []
        self.user_entries = []
        
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        self.grid_rowconfigure(0, weight=1) # Bots
        self.grid_rowconfigure(1, weight=1) # Users
        self.grid_columnconfigure(0, weight=1)
        
        # Bots Sectie
        self.frame_bots = ctk.CTkScrollableFrame(self, label_text="Telegram Bots")
        self.frame_bots.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        self.frame_bots.grid_columnconfigure(1, weight=1)
        
        # Users Sectie
        self.frame_users = ctk.CTkScrollableFrame(self, label_text="Telegram Users")
        self.frame_users.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 10))
        self.frame_users.grid_columnconfigure(1, weight=1)
        
        # Knoppen balk
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=10, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="+ Bot", command=self.add_dummy_bot, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="+ User", command=self.add_dummy_user, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Opslaan", fg_color=RAL_6002, command=self.save_telegram, width=150).pack(side="right", padx=10)

    def load_data(self):
        # Schoonmaken van de UI
        for w in self.frame_bots.winfo_children(): w.destroy()
        for w in self.frame_users.winfo_children(): w.destroy()
        self.bot_entries = []
        self.user_entries = []
        
        # Headers plaatsen
        self._add_headers(self.frame_bots, ["Naam", "Token", "Actief", ""])
        self._add_headers(self.frame_users, ["Naam", "Chat ID", "Actief", ""])

        # Data vullen vanuit config
        for bot in self.cfg.get_telegram_bots():
            self._create_bot_row(bot)
            
        for user in self.cfg.get_telegram_users():
            self._create_user_row(user)

    def _add_headers(self, parent, texts):
        for i, t in enumerate(texts):
            ctk.CTkLabel(parent, text=t, font=("",10,"bold")).grid(row=0, column=i, padx=5, sticky="w")

    def _create_bot_row(self, bot_data):
        # Huidige index bepalen op basis van lijstlengte + 1 (voor header)
        row_idx = len(self.bot_entries) + 1
        
        name = ctk.CTkEntry(self.frame_bots)
        name.insert(0, bot_data.get('name',''))
        name.grid(row=row_idx, column=0, padx=2, sticky="ew")
        
        token = ctk.CTkEntry(self.frame_bots)
        token.insert(0, bot_data.get('token',''))
        token.grid(row=row_idx, column=1, padx=2, sticky="ew")
        
        en_var = ctk.BooleanVar(value=bot_data.get('enabled', True))
        switch = ctk.CTkSwitch(self.frame_bots, text="", variable=en_var, width=40, progress_color=RAL_6002)
        switch.grid(row=row_idx, column=2)
        
        btn = ctk.CTkButton(self.frame_bots, text="X", width=30, fg_color="#8B0000")
        btn.grid(row=row_idx, column=3, padx=5)
        
        # Data object maken
        entry = {
            'name': name, 
            'token': token, 
            'enabled': en_var, 
            'switch': switch, # Opslaan om later te kunnen destroyen
            'btn': btn        # Opslaan om later te kunnen destroyen
        }
        
        # Command koppelen (met referentie naar dit specifieke entry object)
        btn.configure(command=lambda: self._delete_item(entry, "bot"))
        
        self.bot_entries.append(entry)

    def _create_user_row(self, user_data):
        row_idx = len(self.user_entries) + 1
        
        name = ctk.CTkEntry(self.frame_users)
        name.insert(0, user_data.get('name',''))
        name.grid(row=row_idx, column=0, padx=2, sticky="ew")
        
        chat = ctk.CTkEntry(self.frame_users)
        chat.insert(0, str(user_data.get('chat_id','')))
        chat.grid(row=row_idx, column=1, padx=2, sticky="ew")
        
        en_var = ctk.BooleanVar(value=user_data.get('enabled', True))
        switch = ctk.CTkSwitch(self.frame_users, text="", variable=en_var, width=40, progress_color=RAL_6002)
        switch.grid(row=row_idx, column=2)
        
        btn = ctk.CTkButton(self.frame_users, text="X", width=30, fg_color="#8B0000")
        btn.grid(row=row_idx, column=3, padx=5)
        
        entry = {
            'name': name, 
            'chat_id': chat, 
            'enabled': en_var,
            'switch': switch,
            'btn': btn
        }
        
        btn.configure(command=lambda: self._delete_item(entry, "user"))
        
        self.user_entries.append(entry)

    def _delete_item(self, entry, item_type):
        # 1. Bevestiging vragen
        if not messagebox.askokcancel("Bevestiging", "Weet u zeker dat u dit item wilt verwijderen?"):
            return

        # 2. Widgets vernietigen (visueel verwijderen)
        entry['name'].destroy()
        if 'token' in entry: entry['token'].destroy()
        if 'chat_id' in entry: entry['chat_id'].destroy()
        entry['switch'].destroy()
        entry['btn'].destroy()

        # 3. Uit de interne lijst halen
        if item_type == "bot":
            self.bot_entries.remove(entry)
            self._repack_rows(self.bot_entries) # Gaten dichten
        else:
            self.user_entries.remove(entry)
            self._repack_rows(self.user_entries) # Gaten dichten

    def _repack_rows(self, entries_list):
        """
        Loop door de overgebleven items en zet ze netjes onder elkaar 
        zodat er geen gaten in de grid vallen.
        Start bij row=1 (want row 0 is header).
        """
        for i, entry in enumerate(entries_list, start=1):
            entry['name'].grid(row=i, column=0, padx=2, sticky="ew")
            
            if 'token' in entry:
                entry['token'].grid(row=i, column=1, padx=2, sticky="ew")
            elif 'chat_id' in entry:
                entry['chat_id'].grid(row=i, column=1, padx=2, sticky="ew")
                
            entry['switch'].grid(row=i, column=2)
            entry['btn'].grid(row=i, column=3, padx=5)

    def add_dummy_bot(self):
        self._create_bot_row({'name':'Nieuw', 'token':'', 'enabled':True})

    def add_dummy_user(self):
        self._create_user_row({'name':'Nieuw', 'chat_id':'', 'enabled':True})

    def save_telegram(self):
        # Extract Bots
        bots = []
        for b in self.bot_entries:
            # We hoeven niet meer te checken op 'disabled' state, want verwijderde items zitten niet meer in de lijst
            if b['name'].get():
                bots.append({'name': b['name'].get(), 'token': b['token'].get(), 'enabled': b['enabled'].get()})
        
        # Extract Users
        users = []
        for u in self.user_entries:
            if u['name'].get():
                try: cid = int(u['chat_id'].get())
                except: cid = 0
                users.append({'name': u['name'].get(), 'chat_id': cid, 'enabled': u['enabled'].get()})

        self.cfg.update_telegram_config(bots, users)
        # Herladen is eigenlijk niet nodig als we visueel al up-to-date zijn, 
        # maar het bevestigt dat de save gelukt is.
        self.load_data() 
        messagebox.showinfo("Succes", "Telegram instellingen opgeslagen.")