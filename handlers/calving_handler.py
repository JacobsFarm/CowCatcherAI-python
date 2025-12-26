"""
CalvingCatcher Script met Automatische Model Download en Logica gelijk aan CowCatcher
"""

import sys
import os
import json
import time
import threading
import requests
import cv2
from datetime import datetime, timedelta
from queue import Queue
from ultralytics import YOLO

# --- PATH SETUP ---
# Zorg dat we altijd vanuit de root werken
BASE_DIR = os.getcwd()
CONFIG_PATH = os.path.join(BASE_DIR, "settings", "config.json")
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- MODEL DOWNLOADER (Gelijk aan CowCatcher) ---
def check_and_download_model(model_filename, download_url):
    """
    Controleert of het model bestaat in de 'weights' map.
    Zo niet, downloadt het bestand van de opgegeven URL.
    """
    if not os.path.exists(WEIGHTS_DIR):
        os.makedirs(WEIGHTS_DIR)

    model_local_path = os.path.join(WEIGHTS_DIR, model_filename)

    if not os.path.exists(model_local_path):
        print(f"⚠️ Model '{model_filename}' niet gevonden.")
        if not download_url:
            print("❌ Fout: Geen download URL beschikbaar in instellingen.")
            return model_local_path

        print(f"⬇️ Downloaden van: {download_url}...")
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            with open(model_local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Model succesvol gedownload naar: {model_local_path}")
        except Exception as e:
            print(f"❌ ERROR bij downloaden model: {e}")
    else:
        print(f"✅ Model lokaal gevonden: {model_local_path}")

    return model_local_path

# --- LOAD CONFIG ---
def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Laden van config mislukt: {e}")
        sys.exit(1)

# --- ARGUMENT PARSING ---
if len(sys.argv) < 2:
    print("ERROR: CAMERA_ID is vereist als argument.")
    sys.exit(1)

CAMERA_ID = sys.argv[1]
config = load_config()

# 1. Camera-specifieke data ophalen
camera = next((c for c in config.get("cameras", []) if c["id"] == CAMERA_ID), None)
if not camera:
    print(f"ERROR: Camera {CAMERA_ID} niet gevonden.")
    sys.exit(1)

# 2. Globale calving instellingen
# We gebruiken 'calvingcatcher_settings' zoals gedefinieerd in de config
global_settings = config.get("calvingcatcher_settings", {})

# --- READ SETTINGS ---
NOTIFY_THRESHOLD = camera.get("notify theshold", 0.8)
CHECK_INTERVAL = camera.get("check_interval", 1)
RTSP_URL = camera.get("rtsp_url")
CAMERA_NAME = camera.get("name", "Nieuwe Camera")

MIN_DETECTIONS = global_settings.get("min_detections", 30)
MANUAL_DURATION = global_settings.get("manual_mode_duration", 15) * 60
MANUAL_INTERVAL = global_settings.get("manual_mode_interval", 5)
SEND_NOTIFICATIONS = global_settings.get("send_notifications", False)

# --- MODEL BEPALING (Gelijk aan CowCatcher logica) ---
# 1. Kijk naar specifieke camera model_path
# 2. Als die leeg is, gebruik de filename uit de master URL (fallback)
camera_model_file = camera.get("model_path")
master_model_url = global_settings.get("master_model_url", "")

if not camera_model_file:
    if master_model_url:
        camera_model_file = master_model_url.split('/')[-1]
    else:
        # Ultieme fallback als alles leeg is
        camera_model_file = "cowcatcherV15.pt"

# --- INITIALISATIE ---
# Zorg dat het model gedownload is voordat we YOLO laden
final_model_path = check_and_download_model(camera_model_file, master_model_url)

print(f"Laden van model: {final_model_path}")
model = YOLO(final_model_path)

# Setup folders
save_folder = os.path.join(DATA_DIR, CAMERA_NAME.replace(" ", "_"))
os.makedirs(save_folder, exist_ok=True)

# --- TELEGRAM SETUP ---
BOT_NAME = camera.get("telegram_bot", "")
telegram_bots = config.get("telegram", {}).get("bots", [])
telegram_users = config.get("telegram", {}).get("users", [])
TOKEN = next((b["token"] for b in telegram_bots if b["name"] == BOT_NAME and b["enabled"]), None)
CHAT_IDS = [u["chat_id"] for u in telegram_users if u["enabled"]]

telegram_queue = Queue()
manual_expiry = None
last_manual_photo = 0
detection_counter = 0

# --- THREADS ---
def telegram_worker():
    while True:
        task = telegram_queue.get()
        if task is None: break
        t_type, path, msg = task
        if not TOKEN: continue
        for chat_id in CHAT_IDS:
            try:
                if t_type == 'photo':
                    with open(path, 'rb') as f:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                      files={'photo': f}, data={'chat_id': chat_id, 'caption': msg}, timeout=30)
            except Exception as e: print(f"Telegram Fout: {e}")
        telegram_queue.task_done()

def command_listener():
    global manual_expiry
    last_id = 0
    while True:
        if not TOKEN: 
            time.sleep(10)
            continue
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}&timeout=5").json()
            for u in r.get("result", []):
                last_id = u["update_id"]
                msg_text = u.get("message", {}).get("text", "").lower()
                if "check" in msg_text or "start" in msg_text:
                    manual_expiry = datetime.now() + timedelta(seconds=MANUAL_DURATION)
                    print(f"📸 Handmatige monitoring gestart voor {CAMERA_NAME}.")
        except: pass
        time.sleep(5)

threading.Thread(target=telegram_worker, daemon=True).start()
threading.Thread(target=command_listener, daemon=True).start()

# --- HOOFD LOOP ---
cap = cv2.VideoCapture(RTSP_URL)
last_scan_time = 0
last_print_time = 0
frame_count = 0
processed_count = 0

print(f"CalvingCatcher actief voor: {CAMERA_NAME}")
print(f"Drempel: {NOTIFY_THRESHOLD} | Scan interval: {CHECK_INTERVAL}s")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(2)
            cap = cv2.VideoCapture(RTSP_URL)
            continue

        frame_count += 1
        current_time = time.time()

        if current_time - last_scan_time >= CHECK_INTERVAL:
            last_scan_time = current_time
            processed_count += 1
            
            results = model.predict(source=frame, conf=NOTIFY_THRESHOLD, verbose=False)
            
            top_conf = 0
            if len(results[0].boxes) > 0:
                top_conf = float(results[0].boxes[0].conf)

            if top_conf >= NOTIFY_THRESHOLD:
                detection_counter += 1
                if detection_counter >= MIN_DETECTIONS:
                    if SEND_NOTIFICATIONS:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = os.path.join(save_folder, f"calving_{ts}.jpg")
                        cv2.imwrite(path, results[0].plot())
                        telegram_queue.put(('photo', path, f"🚨 AFKALVEN GEDETECTEERD: {CAMERA_NAME}\nConf: {top_conf:.2f}"))
                    detection_counter = 0 
            else:
                detection_counter = max(0, detection_counter - 1)

        if current_time - last_print_time >= 5:
            last_print_time = current_time
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] AI Scans: {processed_count} | Stream Frames: {frame_count} | Detectie-score: {detection_counter}/{MIN_DETECTIONS}", flush=True)

        if manual_expiry and datetime.now() < manual_expiry:
            if current_time - last_manual_photo >= MANUAL_INTERVAL:
                path = os.path.join(save_folder, f"manual_{datetime.now().strftime('%H%M%S')}.jpg")
                cv2.imwrite(path, frame)
                telegram_queue.put(('photo', path, f"🕒 Check: {CAMERA_NAME}"))
                last_manual_photo = current_time
        elif manual_expiry:
            manual_expiry = None

except KeyboardInterrupt:
    print("Script handmatig gestopt.")
finally:
    cap.release()
    telegram_queue.put(None)