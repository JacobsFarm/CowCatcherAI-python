import json
import os
import shutil
import sys

# Hulpfunctie om het pad van de ROOT folder te bepalen
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Als we als .exe draaien
        return os.path.dirname(sys.executable)
    
    # Als we als script draaien in /logic/, moeten we één stap omhoog (..)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir) # Gaat van /logic naar / (root)

# Pad naar settings/config.json
CONFIG_FILE = os.path.join(get_base_path(), 'settings', 'config.json')

class ConfigManager:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        """
        Laad de configuratie vanuit settings/config.json.
        """
        # Controleer of de settings map bestaat, zo niet, maak aan
        settings_dir = os.path.dirname(CONFIG_FILE)
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)

        if not os.path.exists(CONFIG_FILE):
            print(f"'{CONFIG_FILE}' niet gevonden. Nieuw standaardbestand wordt aangemaakt...")
            self.create_default_config()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        except json.JSONDecodeError:
            print("Fout bij lezen config.json. Backup gemaakt en default geladen.")
            # Sla backup ook op in settings map
            backup_path = os.path.join(settings_dir, 'config_backup_error.json')
            shutil.copy(CONFIG_FILE, backup_path)
            self.create_default_config()

    def save_config(self):
        """Schrijf de huidige status naar settings/config.json."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            print("Configuratie opgeslagen.")
        except Exception as e:
            print(f"Fout bij opslaan config: {e}")

    def create_default_config(self):
        """Maakt de volledige standaardstructuur aan."""
        default_data = {
          "cameras": [
            {
              "id": "camera1",
              "name": "first camera",
              "rtsp_url": "rtsp://admin:pass@192.168.1.x:554/stream",
              "enabled": True,
              "show_live_feed": False,
              "notify_threshold": 0.87,
              "peak_detection_threshold": 0.89,
              "save_images": True,
              "telegram_bot": "primary bot"
            }
          ],
          "global_settings": {
            "model_path": "cowcatcherVx.pt",
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
          "telegram": {
            "bots": [],
            "users": []
          }
        }
        
        self.config = default_data
        self.save_config()

    # --- Getters & Setters ---
    def get_cameras(self):
        return self.config.get('cameras', [])

    def get_camera_by_id(self, cam_id):
        for cam in self.config['cameras']:
            if cam['id'] == cam_id:
                return cam
        return None

    def update_camera(self, cam_data):
        for i, cam in enumerate(self.config['cameras']):
            if cam['id'] == cam_data['id']:
                self.config['cameras'][i] = cam_data
                self.save_config()
                return
        self.config['cameras'].append(cam_data)
        self.save_config()

    def delete_camera(self, cam_id):
        self.config['cameras'] = [c for c in self.config['cameras'] if c['id'] != cam_id]
        self.save_config()

    def get_global_settings(self):
        return self.config.get('global_settings', {})

    def update_global_settings(self, settings):
        self.config['global_settings'] = settings
        self.save_config()

    def get_telegram_bots(self):
        return self.config.get('telegram', {}).get('bots', [])

    def get_telegram_users(self):
        return self.config.get('telegram', {}).get('users', [])

    def update_telegram_config(self, bots, users):
        if 'telegram' not in self.config:
            self.config['telegram'] = {}
        self.config['telegram']['bots'] = bots
        self.config['telegram']['users'] = users
        self.save_config()