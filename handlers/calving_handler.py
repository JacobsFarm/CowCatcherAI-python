import sys
import os
import json
import time
from datetime import datetime

# Configuratie laden
CONFIG_PATH = os.path.join("settings", "config.json")

def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Config load failed: {e}")
        sys.exit(1)

if len(sys.argv) < 2:
    print("ERROR: CAMERA_ID is required.")
    sys.exit(1)

CAMERA_ID = sys.argv[1]
config = load_config()

# Haal specifieke data op
camera = next((c for c in config["cameras"] if c["id"] == CAMERA_ID), None)
settings = config.get("calvingcatcher_settings", {})
telegram_settings = config.get("telegram", {})

if not camera:
    print(f"ERROR: Camera {CAMERA_ID} not found.")
    sys.exit(1)

print(f"Started CalvingCatcher for: {camera['name']}")
print(f"Using Model: {settings.get('model_path')}")
print(f"Sensitivity: {settings.get('alert_sensitivity')}")

# --- HOOFD LOOP ---
try:
    while True:
        # HIER KOMT JOUW CALVING LOGICA
        # Bijv: Model inladen, beeld analyseren, checken op 'liggen' of 'staart omhoog'
        
        print(f"Checking calving status... (Interval: {settings.get('check_interval', 10)}s)")
        
        # Simuleer werk
        time.sleep(settings.get('check_interval', 10))
        
except KeyboardInterrupt:
    print("CalvingCatcher stopped by user.")