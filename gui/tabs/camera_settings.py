import customtkinter as ctk
from tkinter import messagebox
from .rtsp_helper import RTSPHelper

RAL_6002 = "#2D572C"

class CameraSettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager, refresh_callback):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        self.refresh_callback = refresh_callback # Functie om de lijst in de sidebar te verversen
        self.current_cam_id = None
        self.dynamic_vars = {}

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)

        # --- Algemeen ---
        ctk.CTkLabel(self, text="Algemeen", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        ctk.CTkLabel(self, text="Camera Naam:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_name = ctk.CTkEntry(self)
        self.entry_name.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # --- RTSP URL (Met Helper Knop) ---
        ctk.CTkLabel(self, text="RTSP URL:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        rtsp_container = ctk.CTkFrame(self, fg_color="transparent")
        rtsp_container.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        rtsp_container.grid_columnconfigure(0, weight=1)

        self.entry_url = ctk.CTkEntry(rtsp_container, placeholder_text="rtsp://...")
        self.entry_url.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_rtsp_helper = ctk.CTkButton(rtsp_container, text="+", width=30, 
                                             fg_color=RAL_6002, command=self.open_rtsp_helper)
        self.btn_rtsp_helper.grid(row=0, column=1)

        # --- Overige velden ---
        ctk.CTkLabel(self, text="Telegram Bot:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.combo_bot = ctk.CTkComboBox(self, values=["Geen"])
        self.combo_bot.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Switches
        self.var_enabled = ctk.BooleanVar()
        self.switch_enabled = ctk.CTkSwitch(self, text="Ingeschakeld", variable=self.var_enabled, progress_color=RAL_6002)
        self.switch_enabled.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.var_live = ctk.BooleanVar()
        self.switch_live = ctk.CTkSwitch(self, text="Show Live Feed", variable=self.var_live, progress_color=RAL_6002)
        self.switch_live.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        # --- Handler Type ---
        ctk.CTkLabel(self, text="Handler Type:", font=("", 12, "bold")).grid(row=6, column=0, sticky="w", padx=10, pady=(15, 0))
        self.combo_type = ctk.CTkComboBox(self, values=["cowcatcher", "calvingcatcher"], command=self.on_type_change)
        self.combo_type.grid(row=6, column=1, padx=10, pady=(15, 5), sticky="ew")

        # --- Dynamisch Frame ---
        self.frame_dynamic = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_dynamic.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.frame_dynamic.grid_columnconfigure(1, weight=1)

        # Knoppen
        self.btn_save = ctk.CTkButton(self, text="Opslaan", fg_color=RAL_6002, command=self.save_camera)
        self.btn_save.grid(row=9, column=1, padx=10, pady=20, sticky="e")
        
        self.btn_del = ctk.CTkButton(self, text="Verwijderen", fg_color="#8B0000", hover_color="#500000", command=self.delete_camera)
        self.btn_del.grid(row=9, column=0, padx=10, pady=20, sticky="w")

    def open_rtsp_helper(self):
        """Opent de popup om RTSP links te genereren."""
        RTSPHelper(self, self.fill_rtsp_field)

    def fill_rtsp_field(self, url):
        """Callback functie voor de RTSPHelper."""
        self.entry_url.delete(0, "end")
        self.entry_url.insert(0, url)

    def load_camera(self, cam_id):
        self.current_cam_id = cam_id
        cam = self.cfg.get_camera_by_id(cam_id)
        if not cam: return

        self.entry_name.delete(0, "end"); self.entry_name.insert(0, cam.get("name", ""))
        self.entry_url.delete(0, "end"); self.entry_url.insert(0, cam.get("rtsp_url", ""))
        self.var_enabled.set(cam.get("enabled", True))
        self.var_live.set(cam.get("show_live_feed", False))

        # Update bots dropdown
        bots = [b['name'] for b in self.cfg.get_telegram_bots()]
        self.combo_bot.configure(values=bots if bots else ["Geen bots gevonden"])
        current_bot = cam.get("telegram_bot")
        self.combo_bot.set(current_bot if current_bot in bots else (bots[0] if bots else ""))

        # Type en dynamische velden
        c_type = cam.get("type", "cowcatcher")
        self.combo_type.set(c_type)
        self._render_dynamic_fields(c_type, cam)

    def on_type_change(self, choice):
        self._render_dynamic_fields(choice)

    def _render_dynamic_fields(self, handler_type, data=None):
        for widget in self.frame_dynamic.winfo_children(): widget.destroy()
        self.dynamic_vars = {}
        if data is None: data = {}

        # --- STAP 1: Model Selectie ---
        models = []
        if handler_type == "cowcatcher":
            settings = self.cfg.get_cowcatcher_settings()
            models = settings.get("available_models", [])
        elif handler_type == "calvingcatcher":
            settings = self.cfg.get_calvingcatcher_settings()
            models = settings.get("available_models", [])

        current_model = data.get("model_path", "")
        if not current_model and models:
            current_model = models[0]
            
        self._add_dropdown("Kies Model:", "model_path", current_model, models, 0)

        # --- STAP 2: Specifieke velden per type ---
        if handler_type == "cowcatcher":
            self._add_field("Notify Threshold:", "notify_threshold", data.get("notify_threshold", 0.87), float, 1)
            self._add_field("Peak Threshold:", "peak_detection_threshold", data.get("peak_detection_threshold", 0.89), float, 2)
            self._add_switch("Save Images", "save_images", data.get("save_images", True), 3)
        
        elif handler_type == "calvingcatcher":
            self._add_field("Save Threshold:", "save_threshold", data.get("save_threshold", 0.80), float, 1)
            self._add_field("notify threshold:", "notify_threshold", data.get("notify_threshold", 0.87), float, 2)
            self._add_field("Check Interval (sec):", "check_interval", data.get("check_interval", 1), int, 3)


    def _add_dropdown(self, label, key, current_value, options, row):
        ctk.CTkLabel(self.frame_dynamic, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        if current_value and current_value not in options:
            options.append(current_value)
        if not options:
            options = ["Geen modellen beschikbaar"]
            
        combo = ctk.CTkComboBox(self.frame_dynamic, values=options)
        combo.set(current_value if current_value else options[0])
        combo.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        self.dynamic_vars[key] = {'var': combo, 'type': str}

    def _add_field(self, label, key, value, dtype, row):
        ctk.CTkLabel(self.frame_dynamic, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = ctk.StringVar(value=str(value))
        ctk.CTkEntry(self.frame_dynamic, textvariable=var).grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        self.dynamic_vars[key] = {'var': var, 'type': dtype}

    def _add_switch(self, label, key, value, row):
        ctk.CTkLabel(self.frame_dynamic, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
        var = ctk.BooleanVar(value=value)
        ctk.CTkSwitch(self.frame_dynamic, text="", variable=var, progress_color=RAL_6002).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self.dynamic_vars[key] = {'var': var, 'type': bool}

    def save_camera(self):
        if not self.current_cam_id: return
        try:
            data = {
                "id": self.current_cam_id,
                "name": self.entry_name.get(),
                "rtsp_url": self.entry_url.get(),
                "enabled": self.var_enabled.get(),
                "show_live_feed": self.var_live.get(),
                "telegram_bot": self.combo_bot.get(),
                "type": self.combo_type.get()
            }
            for key, info in self.dynamic_vars.items():
                val = info['var'].get()
                if info['type'] == bool: data[key] = bool(val)
                elif info['type'] == int: data[key] = int(val)
                elif info['type'] == float: data[key] = float(val)
                else: data[key] = str(val)

            self.cfg.update_camera(data)
            self.refresh_callback()
            messagebox.showinfo("Succes", "Opgeslagen")
        except ValueError:
            messagebox.showerror("Fout", "Controleer invoer")

    def delete_camera(self):
        if not self.current_cam_id: return
        if messagebox.askyesno("Delete", "Verwijderen?"):
            self.cfg.delete_camera(self.current_cam_id)
            self.refresh_callback()
