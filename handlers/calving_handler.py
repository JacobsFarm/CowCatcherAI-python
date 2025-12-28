import sys
import os
import json
import time
import threading
import requests
import cv2
from datetime import datetime, timedelta
from queue import Queue, Empty
from ultralytics import YOLO

# --- PATH SETUP ---
BASE_DIR = os.getcwd()
CONFIG_PATH = os.path.join(BASE_DIR, "settings", "config.json")
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- MODEL DOWNLOADER ---
def check_and_download_model(model_filename, download_url):
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
            response = requests.get(download_url, stream=True, timeout=30)
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
        print(f"ERROR: Laden van config mislukt ({CONFIG_PATH}): {e}")
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
    print(f"ERROR: Camera {CAMERA_ID} niet gevonden in config.")
    sys.exit(1)

# 2. Globale instellingen
global_settings = config.get("calvingcatcher_settings", {})

# --- READ SETTINGS ---
NOTIFY_THRESHOLD = camera.get("notify_threshold", camera.get("notify theshold", 0.8))
CHECK_INTERVAL = camera.get("check_interval", 1)
RTSP_URL = camera.get("rtsp_url")
CAMERA_NAME = camera.get("name", "Nieuwe Camera")

MIN_DETECTIONS = global_settings.get("min_detections", 30)
MANUAL_DURATION_MINUTES = global_settings.get("manual_mode_duration", 15)
MANUAL_DURATION = MANUAL_DURATION_MINUTES * 60
MANUAL_INTERVAL = global_settings.get("manual_mode_interval", 30)
HARDCODED_SAVE_INTERVAL = 10 # hardcoded interval  = multiple from 10

# --- NIEUWE LOGICA INSTELLINGEN ---
SEND_CALVING_NOTIFICATIONS = global_settings.get("send_calving_notifications", False)
SEND_CALVING_SCREENSHOTS = global_settings.get("send_calving_screenshots", False)
SCREENSHOTS_INTERVAL = global_settings.get("Calving_screenshots_interval", 30)


# --- MODEL BEPALING ---
camera_model_file = camera.get("model_path")
master_model_url = global_settings.get("master_model_url", "")

if not camera_model_file:
    if master_model_url:
        camera_model_file = master_model_url.split('/')[-1]
    else:
        camera_model_file = "cowcatcherV15.pt"

# --- INITIALISATIE ---
final_model_path = check_and_download_model(camera_model_file, master_model_url)

print(f"🚀 Starten CalvingCatcher voor: {CAMERA_NAME}")
print(f"📂 Model: {final_model_path}")

try:
    model = YOLO(final_model_path)
except Exception as e:
    print(f"❌ FATAL ERROR: Kon YOLO model niet laden. Corrupt bestand? {e}")
    sys.exit(1)

# Mappen aanmaken
save_folder = os.path.join(DATA_DIR, CAMERA_NAME.replace(" ", "_"))
os.makedirs(save_folder, exist_ok=True)

manual_save_folder = os.path.join(DATA_DIR, "manual", CAMERA_ID)
os.makedirs(manual_save_folder, exist_ok=True)

# --- TELEGRAM SETUP ---
BOT_NAME = camera.get("telegram_bot", "")
telegram_bots = config.get("telegram", {}).get("bots", [])
telegram_users = config.get("telegram", {}).get("users", [])
TOKEN = next((b["token"] for b in telegram_bots if b["name"] == BOT_NAME and b["enabled"]), None)
CHAT_IDS = [u["chat_id"] for u in telegram_users if u["enabled"]]

telegram_queue = Queue()

# Globale variabelen
manual_expiry = None
last_manual_save = 0
last_manual_send = 0
detection_counter = 0

# --- THREADS ---
def telegram_worker():
    while True:
        task = telegram_queue.get()
        if task is None: break 
        
        t_type, path, msg, silent = task
        
        if not TOKEN: 
            telegram_queue.task_done()
            continue

        for chat_id in CHAT_IDS:
            try:
                # FOTO
                if t_type == 'photo':
                    with open(path, 'rb') as f:
                        requests.post(
                            f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                            files={'photo': f}, 
                            data={
                                'chat_id': chat_id, 
                                'caption': msg,
                                'disable_notification': silent
                            }, 
                            timeout=30
                        )
                
                # TEKST
                elif t_type == 'text':
                    requests.post(
                        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        data={
                            'chat_id': chat_id,
                            'text': msg,
                            'disable_notification': silent
                        },
                        timeout=30
                    )

            except Exception as e:
                print(f"Telegram Fout: {e}")
        
        telegram_queue.task_done()

def command_listener():
    global manual_expiry
    last_id = 0
    while True:
        if not TOKEN: 
            time.sleep(30)
            continue
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}&timeout=10"
            r = requests.get(url, timeout=15).json()
            
            for u in r.get("result", []):
                last_id = u["update_id"]
                msg_text = u.get("message", {}).get("text", "").lower()
                
                # --- COMMANDO: START / CHECK ---
                if "check" in msg_text or "start" in msg_text:
                    manual_expiry = datetime.now() + timedelta(seconds=MANUAL_DURATION)
                    print(f"📸 Handmatige monitoring gestart via Telegram.")
                    
                    reply_msg = f"✅ Proces started for {MANUAL_DURATION_MINUTES} min."
                    if SEND_CALVING_SCREENSHOTS:
                        reply_msg += f", sends screenshots every {MANUAL_INTERVAL} seconds."
                    
                    telegram_queue.put(('text', None, reply_msg, False))

                # --- COMMANDO: STOP (NIEUW) ---
                elif "stop" in msg_text:
                    if manual_expiry is not None:
                        manual_expiry = None # Zet de tijd direct op None = STOP
                        print("🛑 Handmatige monitoring gestopt door gebruiker.")
                        # Stuur bericht terug
                        telegram_queue.put(('text', None, "manual save process stopped", False))

        except Exception as e:
            pass
        time.sleep(2)

t_tele = threading.Thread(target=telegram_worker, daemon=True)
t_tele.start()

t_cmd = threading.Thread(target=command_listener, daemon=True)
t_cmd.start()

# --- HOOFD LOOP ---
cap = cv2.VideoCapture(RTSP_URL)
last_scan_time = 0
last_print_time = 0
frame_count = 0
processed_count = 0
last_trigger_time = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Stream verloren, opnieuw verbinden in 5 sec...")
            cap.release()
            time.sleep(5)
            cap = cv2.VideoCapture(RTSP_URL)
            continue

        frame_count += 1
        current_time = time.time()

        # --- AI DETECTIE (Achtergrond) ---
        if current_time - last_scan_time >= CHECK_INTERVAL:
            last_scan_time = current_time
            processed_count += 1
            
            results = model.predict(source=frame, conf=NOTIFY_THRESHOLD, verbose=False, classes=[1])
            
            top_conf = 0.0
            if len(results[0].boxes) > 0:
                top_conf = float(results[0].boxes[0].conf)

            if top_conf >= NOTIFY_THRESHOLD:
                detection_counter += 1
                if detection_counter > (MIN_DETECTIONS + 5):
                    detection_counter = MIN_DETECTIONS + 5

                if detection_counter >= MIN_DETECTIONS:
                    if (current_time - last_trigger_time) >= SCREENSHOTS_INTERVAL:
                        
                        print(f"🚨 DETECTIE EVENT (Conf: {top_conf:.2f})")
                        last_trigger_time = current_time 
                        
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = os.path.join(save_folder, f"calving_{ts}.jpg")
                        cv2.imwrite(path, results[0].plot())
                        print(f"💾 Foto lokaal opgeslagen: {path}")

                        if SEND_CALVING_NOTIFICATIONS:
                            if SEND_CALVING_SCREENSHOTS:
                                caption = f"🚨 AFKALVEN ({CAMERA_NAME})\nConf: {top_conf:.2f}"
                                telegram_queue.put(('photo', path, caption, False)) 
                            else:
                                print("ℹ️ Telegram aan, maar screenshots uit.")
                        else:
                            print("🔕 Notificaties staan UIT.")
            else:
                detection_counter = max(0, detection_counter - 1)

        # Console Log
        if current_time - last_print_time >= 10:
            last_print_time = current_time
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Frames processed {processed_count} | Detectie: {detection_counter}/{MIN_DETECTIONS}", flush=True)

        # --- HANDMATIGE MONITORING ---
        if manual_expiry:
                    if datetime.now() < manual_expiry:
                        
                        # CHECK 1: Opslaan (Elke 10s hardcoded)
                        if current_time - last_manual_save >= HARDCODED_SAVE_INTERVAL:
                            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                            path = os.path.join(manual_save_folder, f"manual_{ts}.jpg")
                            
                            # Foto opslaan
                            cv2.imwrite(path, frame)
                            print(f"📸 Manual save: {path}")
                            last_manual_save = current_time

                            # CHECK 2: Telegram (Alleen als interval verstreken is)
                            if current_time - last_manual_send >= MANUAL_INTERVAL:
                                telegram_queue.put(('photo', path, f"🕒 Check: {CAMERA_NAME}", True))
                                last_manual_send = current_time
                                print(f"📤 Foto verzonden naar Telegram (Interval: {MANUAL_INTERVAL}s)")
                    else:
                        manual_expiry = None
                        print("⏹️ Handmatige monitoring verlopen.")

except KeyboardInterrupt:
    print("\nScript gestopt.")
finally:
    cap.release()
    telegram_queue.put(None)
