import customtkinter as ctk
from tkinter import filedialog, messagebox

RAL_6002 = "#2D572C"
COLOR_GRAY_ITEM = "#404040"

class DynamicSettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, config_manager, settings_key, title):
        super().__init__(parent, fg_color="transparent")
        self.cfg = config_manager
        self.settings_key = settings_key
        self.title = title
        self.input_vars = {}
        self.list_cache = {} 

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self, label_text=self.title)
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(1, weight=1)

        self.btn_save = ctk.CTkButton(self, text="Save Settings", fg_color=RAL_6002, command=self.save_settings)
        self.btn_save.grid(row=1, column=0, pady=10)

        self.refresh_form()

    def refresh_form(self):
        for widget in self.scroll.winfo_children(): 
            widget.destroy()
        self.input_vars = {}
        self.list_cache = {}

        if self.settings_key == "cowcatcher":
            data = self.cfg.get_cowcatcher_settings()
        else:
            data = self.cfg.get_calvingcatcher_settings()

        self._build_form(data)

    def save_settings(self):
        try:
            new_settings = self._extract_form()
            if self.settings_key == "cowcatcher":
                self.cfg.update_cowcatcher_settings(new_settings)
            else:
                self.cfg.update_calvingcatcher_settings(new_settings)
            messagebox.showinfo("Success", f"{self.title} saved successfully.")
        except ValueError as e:
            messagebox.showerror("Error", f"Input error: {e}")

    def _build_form(self, settings):
            row = 0
            for key, value in settings.items():
                lbl_text = key.replace("_", " ").title() + ":"
                
                if key == "manual_mode_interval":
                    ctk.CTkLabel(self.scroll, text="Telegram Interval (sec):", anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="nw")
                    
                    values_list = [str(x) for x in range(10, 110, 10)]
                    current_val = str(value)
                    if int(float(current_val)) < 10: 
                        current_val = "10"
                    
                    var = ctk.StringVar(value=current_val)
                    dropdown = ctk.CTkOptionMenu(self.scroll, values=values_list, variable=var, fg_color=RAL_6002)
                    dropdown.grid(row=row, column=1, sticky="w", padx=10)
                    
                    self.input_vars[key] = {'type': 'int', 'var': var}

                elif key == "master_model_url":
                    ctk.CTkLabel(self.scroll, text="Default Model Link (Master):", anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="nw")
                    
                    container = ctk.CTkFrame(self.scroll, fg_color="transparent")
                    container.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                    
                    var_url = ctk.StringVar(value=str(value))
                    entry_url = ctk.CTkEntry(container, textvariable=var_url, fg_color="#2b2b2b", text_color="gray")
                    entry_url.configure(state="disabled") 
                    entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))
                    
                    var_unlock = ctk.BooleanVar(value=False)
                    chk_unlock = ctk.CTkCheckBox(container, text="Edit", variable=var_unlock, width=80,
                                                 command=lambda e=entry_url, v=var_unlock: self._toggle_entry_lock(e, v))
                    chk_unlock.pack(side="right")
                    
                    self.input_vars[key] = {'type': 'str', 'var': var_url}
                
                elif isinstance(value, list):
                     ctk.CTkLabel(self.scroll, text=lbl_text, anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="nw")
                     self.list_cache[key] = list(value)
                     container = ctk.CTkFrame(self.scroll, fg_color="transparent")
                     container.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
                     list_frame = ctk.CTkScrollableFrame(container, height=100, fg_color="transparent", border_width=1)
                     list_frame.pack(fill="x", expand=True)
                     btn_add = ctk.CTkButton(container, text="+ Add Item", width=100, fg_color=RAL_6002,
                                            command=lambda k=key, f=list_frame: self._add_list_item(k, f))
                     btn_add.pack(anchor="w", pady=5)
                     self._render_list(list_frame, key)
                     self.input_vars[key] = {'type': 'list'}

                elif isinstance(value, bool):
                    ctk.CTkLabel(self.scroll, text=lbl_text, anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="nw")
                    var = ctk.BooleanVar(value=value)
                    ctk.CTkSwitch(self.scroll, text="Active", variable=var, progress_color=RAL_6002).grid(row=row, column=1, sticky="w", padx=10)
                    self.input_vars[key] = {'type': 'bool', 'var': var}

                else:
                    ctk.CTkLabel(self.scroll, text=lbl_text, anchor="w").grid(row=row, column=0, padx=10, pady=5, sticky="nw")
                    var = ctk.StringVar(value=str(value))
                    ctk.CTkEntry(self.scroll, textvariable=var).grid(row=row, column=1, sticky="ew", padx=10)
                    if "model" in key and "path" in key:
                        ctk.CTkButton(self.scroll, text="📂", width=30, 
                                      command=lambda v=var: self._browse_file(v)).grid(row=row, column=2, padx=5)
                    dtype = 'int' if isinstance(value, int) else 'float' if isinstance(value, float) else 'str'
                    self.input_vars[key] = {'type': dtype, 'var': var}
                
                row += 1

    def _extract_form(self):
        result = {}
        for key, data in self.input_vars.items():
            t = data['type']
            if t == 'list':
                result[key] = self.list_cache.get(key, [])
            elif t == 'bool': result[key] = data['var'].get()
            elif t == 'int': result[key] = int(data['var'].get())
            elif t == 'float': result[key] = float(data['var'].get())
            else: result[key] = str(data['var'].get())
        return result

    def _toggle_entry_lock(self, entry, var):
        if var.get():
            entry.configure(state="normal", fg_color="#343638", text_color="white")
        else:
            entry.configure(state="disabled", fg_color="#2b2b2b", text_color="gray")

    def _render_list(self, scroll_frame, key):
        for w in scroll_frame.winfo_children(): 
            w.destroy()
        items = self.list_cache.get(key, [])
        
        for item in items:
            row = ctk.CTkFrame(scroll_frame, fg_color=COLOR_GRAY_ITEM)
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=item, anchor="w", wraplength=300).pack(side="left", padx=5, fill="x", expand=True)
            ctk.CTkButton(row, text="X", width=30, fg_color="#8B0000", 
                          command=lambda k=key, i=item, f=scroll_frame: self._remove_list_item(k, i, f)).pack(side="right", padx=5, pady=2)

    def _add_list_item(self, key, frame):
        if len(self.list_cache.get(key, [])) >= 5:
            messagebox.showwarning("Limit", "Maximum of 5 models allowed.")
            return
        f = filedialog.askopenfilename(
            filetypes=[
                ("Models", "*.pt *.onnx *.engine *.xml *.tflite *.torchscript *.mlpackage *.mlmodel"), 
                ("All", "*.*")
            ]
        )
        if f and f not in self.list_cache[key]:
            self.list_cache[key].append(f)
            self._render_list(frame, key)

    def _remove_list_item(self, key, item, frame):
        if item in self.list_cache.get(key, []):
            self.list_cache[key].remove(item)
            self._render_list(frame, key)

    def _browse_file(self, var):
        f = filedialog.askopenfilename()
        if f: 
            var.set(f)