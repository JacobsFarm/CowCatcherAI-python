import json
import os
import shutil
import sys

# Hulpfunctie om het pad van de ROOT folder te bepalen
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)

CONFIG_FILE = os.path.join(get_base_path(), 'settings', 'config.json')

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        settings_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)

        if not os.path.exists(CONFIG_FILE):
            print(f"'{CONFIG_FILE}' niet gevonden. Nieuw bestand wordt aangemaakt...")
            self.create_default_config()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        except json.JSONDecodeError:
            print("Fout bij lezen config.json. Backup gemaakt en default geladen.")
            backup_path = os.path.join(settings_dir, 'config_backup_error.json')
            shutil.copy(CONFIG_FILE, backup_path)
            self.create_default_config()

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            print("Configuratie opgeslagen.")
        except Exception as e:
            print(f"Fout bij opslaan config: {e}")

    def create_default_config(self):
        COW_URL = "https://github.com/CowCatcherAI/CowCatcherAI/releases/download/modelv-14/cowcatcherV15.pt"
        CALV_URL = "https://github.com/CowCatcherAI/CalvingCatcherAI/releases/download/CalvingcatcherV1/calvingcatcherV1.pt"
        
        default_data = {
          "cameras": [
            {
              "id": "camera1",
              "name": "Standaard Camera",
              "type": "cowcatcher",
              "rtsp_url": "rtsp://admin:pass@192.168.1.x:554/stream",
              "enabled": True,
              "show_live_feed": False,
              "telegram_bot": "",
              "notify_threshold": 0.87,
              "peak_detection_threshold": 0.89,
              "save_images": True,
              "model_path": "cowcatcherV15.pt" 
            }
          ],
          "cowcatcher_settings": {
            "master_model_url": COW_URL,
            "available_models": [], 
            "save_threshold": 0.83,
            "process_every_n_frames": 2,
            "min_high_confidence_detections": 3,
            "max_screenshots": 2,
            "send_annotated_images": True,
            "collection_time": 50,
            "min_collection_time": 4,
            "inactivity_stop_time": 6,
            "sound_every_n_notifications": 5,
            "cooldown_period": 40,
            "send_status_notifications": True
          },
          "calvingcatcher_settings": {
            "master_model_url": CALV_URL,
            "available_models": [],            
            "min_detections": 30,
            "manual_mode_duration": 15,
            "manual_mode_interval": 5,
            "send_calving_notifications": False,
            "Calving_screenshots_interval": 30,
            "send_calving_screenshots": False,
          },
          "telegram": {
            "bots": [],
            "users": []
          }
        }
        
        self.config = default_data
        self.save_config()

    # --- Interne helper om modellen gelijk te trekken ---
    def _fix_available_models(self, settings_key):
        """Zorgt dat het model uit de master_url in available_models staat als de lijst leeg is."""
        settings = self.config.get(settings_key, {})
        master_url = settings.get("master_model_url", "")
        
        if master_url and not settings.get("available_models"):
            model_name = master_url.split('/')[-1]
            settings["available_models"] = [model_name]
            self.config[settings_key] = settings
            # We slaan het niet direct op om recursie te voorkomen bij getters, 
            # maar het is nu wel aanwezig in het geheugen voor de GUI.

    # --- Getters & Setters ---
    def get_cameras(self): return self.config.get('cameras', [])
    
    def get_cowcatcher_settings(self): 
        # Voer de check uit voor CowCatcher
        self._fix_available_models("cowcatcher_settings")
        return self.config.get('cowcatcher_settings', {})

    def update_cowcatcher_settings(self, settings):
        self.config['cowcatcher_settings'] = settings
        self.save_config()

    def get_calvingcatcher_settings(self): 
        # Voer de check uit voor CalvingCatcher (Nu gelijk aan CowCatcher)
        self._fix_available_models("calvingcatcher_settings")
        return self.config.get('calvingcatcher_settings', {})

    def update_calvingcatcher_settings(self, settings):
        self.config['calvingcatcher_settings'] = settings
        self.save_config()

    # Overige methodes blijven ongewijzigd
    def get_camera_by_id(self, cam_id): 
        return next((c for c in self.config.get('cameras', []) if c['id'] == cam_id), None)
    
    def update_camera(self, cam_data):
        if 'cameras' not in self.config: self.config['cameras'] = []
        for i, cam in enumerate(self.config['cameras']):
            if cam['id'] == cam_data['id']:
                self.config['cameras'][i] = cam_data
                self.save_config(); return
        self.config['cameras'].append(cam_data)
        self.save_config()

    def delete_camera(self, cam_id):
        self.config['cameras'] = [c for c in self.config['cameras'] if c['id'] != cam_id]
        self.save_config()

    def get_telegram_bots(self): return self.config.get('telegram', {}).get('bots', [])
    def get_telegram_users(self): return self.config.get('telegram', {}).get('users', [])
    def update_telegram_config(self, bots, users):
        if 'telegram' not in self.config: self.config['telegram'] = {}
        self.config['telegram']['bots'] = bots
        self.config['telegram']['users'] = users
        self.save_config()