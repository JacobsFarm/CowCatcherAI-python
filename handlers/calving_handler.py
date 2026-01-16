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
BASE_DIR = os.getcwd()
CONFIG_PATH = os.path.join(BASE_DIR, "settings", "config.json")
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- MODEL DOWNLOADER ---
def check_and_download_model(model_filename, download_url):
    """
    Checks if model exists. 
    YES -> Prints 'Model found locally' and continues.
    NO  -> Prints 'Not found', starts download, and warns about wait time.
    """
    if not os.path.exists(WEIGHTS_DIR):
        os.makedirs(WEIGHTS_DIR)

    model_local_path = os.path.join(WEIGHTS_DIR, model_filename)

    # Check happens here:
    if not os.path.exists(model_local_path):
        # Model is NOT present
        print(f"⚠️ Model '{model_filename}' not found locally.")
        
        if not download_url:
            print("❌ Error: No download URL available in settings.")
            sys.exit(1)

        print(f"⬇️ Starting to download from: {download_url}")
        print("⏳ Downloading model can take up to multiple minutes...")

        sys.stdout.flush()
        time.sleep(0.5)
        
        try:
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            with open(model_local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Model successfully downloaded to: {model_local_path}")
        except Exception as e:
            print(f"❌ ERROR downloading model: {e}")
            sys.exit(1)
    else:
        # Model IS present
        print(f"✅ Model found locally: {model_local_path}")

    return model_local_path

# --- LOAD CONFIG ---
def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Loading config failed ({CONFIG_PATH}): {e}")
        sys.exit(1)

# --- ARGUMENT PARSING ---
if len(sys.argv) < 2:
    print("ERROR: CAMERA_ID is required as argument.")
    sys.exit(1)

CAMERA_ID = sys.argv[1]
config = load_config()

camera = next((c for c in config.get("cameras", []) if c["id"] == CAMERA_ID), None)
if not camera:
    print(f"ERROR: Camera {CAMERA_ID} not found in config.")
    sys.exit(1)

global_settings = config.get("calvingcatcher_settings", {})

# --- SETTINGS ---
NOTIFY_THRESHOLD = camera.get("notify_threshold", 0.87)
SAVE_THRESHOLD = camera.get("save_threshold", 0.80)  # <--- NEW: Threshold for direct saving
CHECK_INTERVAL = camera.get("check_interval", 1)
RTSP_URL = camera.get("rtsp_url")
CAMERA_NAME = camera.get("name", "Unknown Camera")

# Interval to prevent flood of save-images (e.g. max 1 per 5 sec at high confidence)
HIGH_CONF_SAVE_INTERVAL = 5 

MIN_DETECTIONS = global_settings.get("min_detections", 30)
MANUAL_DURATION_MINUTES = global_settings.get("manual_mode_duration", 15)
MANUAL_DURATION = MANUAL_DURATION_MINUTES * 60
MANUAL_INTERVAL = global_settings.get("manual_mode_interval", 30)
HARDCODED_SAVE_INTERVAL = 10 
SEND_CALVING_NOTIFICATIONS = global_settings.get("send_calving_notifications", False)
SEND_CALVING_SCREENSHOTS = global_settings.get("send_calving_screenshots", False)
SCREENSHOTS_INTERVAL = global_settings.get("Calving_screenshots_interval", 30)

# --- MODEL SELECTION ---
camera_model_file = camera.get("model_path")
master_model_url = global_settings.get("master_model_url", "")

if not camera_model_file:
    if master_model_url:
        camera_model_file = master_model_url.split('/')[-1]
    else:
        camera_model_file = "cowcatcherV15.pt"

# --- TELEGRAM SETUP ---
BOT_NAME = camera.get("telegram_bot", "")
telegram_bots = config.get("telegram", {}).get("bots", [])
telegram_users = config.get("telegram", {}).get("users", [])
TOKEN = next((b["token"] for b in telegram_bots if b["name"] == BOT_NAME and b["enabled"]), None)
CHAT_IDS = [u["chat_id"] for u in telegram_users if u["enabled"]]

telegram_queue = Queue()

# --- INITIALIZATION START ---

print("Starting CalvingCatcherAI...")

# 1. Model Check (Downloads only if necessary)
final_model_path = check_and_download_model(camera_model_file, master_model_url)

# 2. Load Model
print(f"Loading detection model: {final_model_path}")
try:
    model = YOLO(final_model_path)
    print("Detection model successfully loaded")
except Exception as e:
    print(f"❌ FATAL ERROR: Could not load model. {e}")
    sys.exit(1)

# 3. Connect Camera
print(f"Connecting to camera: {CAMERA_NAME}")

# Create directories (silently)
save_folder = os.path.join(DATA_DIR, CAMERA_NAME.replace(" ", "_"))
os.makedirs(save_folder, exist_ok=True)
manual_save_folder = os.path.join(DATA_DIR, "manual", CAMERA_ID)
os.makedirs(manual_save_folder, exist_ok=True)

# 4. Telegram Status
num_chats = len(CHAT_IDS) if TOKEN else 0
print(f"Telegram bot active for {num_chats} chat(s)")

# Threads definitions
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
                if t_type == 'photo':
                    with open(path, 'rb') as f:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                            files={'photo': f}, data={'chat_id': chat_id, 'caption': msg, 'disable_notification': silent}, timeout=30)
                elif t_type == 'text':
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                        data={'chat_id': chat_id, 'text': msg, 'disable_notification': silent}, timeout=30)
            except Exception as e:
                print(f"Telegram Error: {e}")
        telegram_queue.task_done()

global manual_expiry
manual_expiry = None

def command_listener():
    global manual_expiry
    last_id = 0
    while True:
        if not TOKEN: 
            time.sleep(30); continue
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_id+1}&timeout=10"
            r = requests.get(url, timeout=15).json()
            for u in r.get("result", []):
                last_id = u["update_id"]
                msg_text = u.get("message", {}).get("text", "").lower()
                if "check" in msg_text or "start" in msg_text:
                    manual_expiry = datetime.now() + timedelta(seconds=MANUAL_DURATION)
                    print(f"📸 Manual monitoring started via Telegram.")
                    reply = f"✅ Started manual mode for {MANUAL_DURATION_MINUTES} min."
                    telegram_queue.put(('text', None, reply, False))
                elif "stop" in msg_text:
                    manual_expiry = None
                    print("🛑 Manual monitoring stopped by user.")
                    telegram_queue.put(('text', None, "Manual process stopped", False))
        except Exception: pass
        time.sleep(2)

if TOKEN and CHAT_IDS:
    # Test connection
    try:
        if requests.get(f"https://api.telegram.org/bot{TOKEN}/getMe", timeout=5).status_code == 200:
            print("Telegram bot connection tested")
        else:
            print("⚠️ Telegram connection test failed")
    except:
        print("⚠️ Telegram connection test failed (Network error)")

    # Start threads
    t_tele = threading.Thread(target=telegram_worker, daemon=True)
    t_tele.start()
    t_cmd = threading.Thread(target=command_listener, daemon=True)
    t_cmd.start()
    
    # Optional start msg
    if SEND_CALVING_NOTIFICATIONS:
        telegram_queue.put(('text', None, f"📋 CalvingCatcher started at {datetime.now().strftime('%H:%M')}", True))

# 5. Stream
print("Opening camera stream...")
cap = cv2.VideoCapture(RTSP_URL)
if not cap.isOpened():
    print("ERROR: Cannot open camera stream")
    sys.exit(1)
else:
    print("Camera stream successfully opened")

print("Processing started")

# --- MAIN LOOP ---
last_scan_time = 0
last_print_time = 0
frame_count = 0
processed_count = 0
last_trigger_time = 0
last_manual_save = 0
last_manual_send = 0
last_threshold_save_time = 0 # <--- NEW: Timer for threshold saves
detection_counter = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Stream lost, reconnecting in 5s...")
            cap.release()
            time.sleep(5)
            cap = cv2.VideoCapture(RTSP_URL)
            continue

        frame_count += 1
        current_time = time.time()

        # AI Detection
        if current_time - last_scan_time >= CHECK_INTERVAL:
            last_scan_time = current_time
            processed_count += 1
            
            # Run inference
            # We set conf slightly lower here (e.g. 0.4) so we can filter for SAVE vs NOTIFY ourselves
            results = model.predict(source=frame, conf=0.4, verbose=False, classes=[1])
            
            top_conf = 0.0
            if len(results[0].boxes) > 0:
                top_conf = float(results[0].boxes[0].conf)

            # --- NEW: SAVE THRESHOLD LOGIC ---
            # If detection is higher than save_threshold, save immediately (independent of alarm)
            if top_conf >= SAVE_THRESHOLD:
                if (current_time - last_threshold_save_time) >= HIGH_CONF_SAVE_INTERVAL:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    # Filename now includes the confidence score
                    path = os.path.join(save_folder, f"calving_highconf_{ts}_conf{top_conf:.2f}.jpg")
                    cv2.imwrite(path, frame)
                    print(f"💾 High Conf Save ({top_conf:.2f}): {path}")
                    last_threshold_save_time = current_time
            # -------------------------------------

            if top_conf >= NOTIFY_THRESHOLD:
                detection_counter += 1
                if detection_counter > (MIN_DETECTIONS + 5): detection_counter = MIN_DETECTIONS + 5

                if detection_counter >= MIN_DETECTIONS:
                    if (current_time - last_trigger_time) >= SCREENSHOTS_INTERVAL:
                        print(f"🚨 DETECTION EVENT (Conf: {top_conf:.2f})")
                        last_trigger_time = current_time 
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = os.path.join(save_folder, f"calving_alarm_{ts}.jpg")
                        cv2.imwrite(path, results[0].plot())

                        if SEND_CALVING_NOTIFICATIONS:
                            if SEND_CALVING_SCREENSHOTS:
                                caption = f"🚨 CALVING ({CAMERA_NAME})\nConf: {top_conf:.2f}"
                                telegram_queue.put(('photo', path, caption, False))
            else:
                detection_counter = max(0, detection_counter - 1)

        # Console Log (every 10s)
        if current_time - last_print_time >= 10:
            last_print_time = current_time
            ts_str = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts_str}] Frames processed {processed_count} | Detection: {detection_counter}/{MIN_DETECTIONS}", flush=True)

        # Manual Monitoring
        if manual_expiry:
            if datetime.now() < manual_expiry:
                if current_time - last_manual_save >= HARDCODED_SAVE_INTERVAL:
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    path = os.path.join(manual_save_folder, f"manual_{ts}.jpg")
                    cv2.imwrite(path, frame)
                    print(f"📸 Manual save: {path}")
                    last_manual_save = current_time

                    if current_time - last_manual_send >= MANUAL_INTERVAL:
                        telegram_queue.put(('photo', path, f"🕒 Check: {CAMERA_NAME}", True))
                        last_manual_send = current_time
                        print(f"📤 Photo sent to Telegram")
            else:
                manual_expiry = None
                print("⏹️ Manual monitoring expired.")

except KeyboardInterrupt:
    print("\nScript stopped by user.")
finally:
    cap.release()
    telegram_queue.put(None)