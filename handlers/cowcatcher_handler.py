"""
CowCatcher Script with Threading Optimization, Multi-Chat Support & Auto-Model Download
"""

from ultralytics import YOLO
import sys
import cv2
import os
import time
import requests
import json
from datetime import datetime
from collections import deque
from threading import Thread
from queue import Queue

# --- PATH SETUP ---
# Zorg dat we altijd vanuit de root werken, ongeacht waar het script wordt aangeroepen
BASE_DIR = os.getcwd() 
CONFIG_PATH = os.path.join(BASE_DIR, "settings", "config.json")
WEIGHTS_DIR = os.path.join(BASE_DIR, "weights")
DATA_DIR = os.path.join(BASE_DIR, "data")

# --- MODEL DOWNLOADER ---
def check_and_download_model(model_filename, download_url):
    """
    Controleert of het model bestaat in de 'weights' map.
    Zo niet, downloadt het bestand van de opgegeven URL.
    """
    if not os.path.exists(WEIGHTS_DIR):
        os.makedirs(WEIGHTS_DIR)
        print(f"Created weights directory: {WEIGHTS_DIR}")

    model_local_path = os.path.join(WEIGHTS_DIR, model_filename)

    if not os.path.exists(model_local_path):
        print(f"⚠️ Model '{model_filename}' not found locally.")
        print(f"⬇️ Downloading from: {download_url}...")
        
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(model_local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Model successfully downloaded to: {model_local_path}")
        except Exception as e:
            print(f"❌ ERROR downloading model: {e}")
            sys.exit(1)
    else:
        print(f"✅ Model found locally: {model_local_path}")

    return model_local_path

# --- LOAD CONFIG ---
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"ERROR: {CONFIG_PATH} not found.")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"ERROR: {CONFIG_PATH} is invalid JSON.")
    sys.exit(1)

# --- ARGUMENT PARSING ---
if len(sys.argv) < 2:
    print("ERROR: CAMERA_ID is required as a command-line argument.")
    sys.exit(1)

CAMERA_ID = sys.argv[1] 
camera = next((c for c in config["cameras"] if c["id"] == CAMERA_ID), None)

if camera is None:
    print(f"ERROR: Camera ID '{CAMERA_ID}' not found in config.")
    sys.exit(1)

# --- READ SETTINGS (CORRECTED MAPPING) ---
# We gebruiken hier 'cowcatcher_settings' omdat dat in je JSON staat (niet global_settings)
cc_settings = config.get("cowcatcher_settings", {})

# Individual camera settings
CAMERA_NAME = camera.get("name", "Unknown Camera")
RTSP_URL = camera.get("rtsp_url")
SHOW_LIVE_FEED = camera.get("show_live_feed", False)
NOTIFY_THRESHOLD = camera.get("notify_threshold", 0.80)
PEAK_DETECTION_THRESHOLD = camera.get("peak_detection_threshold", 0.85)

# Bepaal welk model we moeten gebruiken
# 1. Kijk naar specifieke camera model_path
# 2. Als die leeg is, gebruik de filename uit de master URL (fallback)
camera_model_file = camera.get("model_path")
master_model_url = cc_settings.get("master_model_url")

if not camera_model_file:
    # Probeer bestandsnaam uit URL te halen als er niks in de config staat
    camera_model_file = master_model_url.split('/')[-1]

# Global settings mapping
SOUND_EVERY_N_NOTIFICATIONS = cc_settings.get("sound_every_n_notifications", 5)
SAVE_THRESHOLD = cc_settings.get("save_threshold", 0.83)
process_every_n_frames = cc_settings.get("process_every_n_frames", 2)
MIN_HIGH_CONFIDENCE_DETECTIONS = cc_settings.get("min_high_confidence_detections", 3)
MAX_SCREENSHOTS = cc_settings.get("max_screenshots", 2)
SEND_ANNOTATED_IMAGES = cc_settings.get("send_annotated_images", True)
COLLECTION_TIME = cc_settings.get("collection_time", 50)
MIN_COLLECTION_TIME = cc_settings.get("min_collection_time", 4)
INACTIVITY_STOP_TIME = cc_settings.get("inactivity_stop_time", 6)
cooldown_period = cc_settings.get("cooldown_period", 40)
SEND_STATUS_NOTIFICATIONS = cc_settings.get("send_status_notifications", True)

BOT_NAME = camera.get("telegram_bot", "")
telegram_config = config.get("telegram", {})
telegram_bots = telegram_config.get("bots", [])
telegram_users = telegram_config.get("users", [])

TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_IDS = []

# Probeer Token te vinden (Soft check)
try:
    if telegram_bots:
        if not BOT_NAME:
            # Fallback: pak de eerste enabled bot
            TELEGRAM_BOT_TOKEN = next(b["token"] for b in telegram_bots if b.get("enabled"))
        else:
            TELEGRAM_BOT_TOKEN = next(b["token"] for b in telegram_bots if b["name"] == BOT_NAME and b.get("enabled"))
except StopIteration:
    print(f"⚠️ WAARSCHUWING: Geen actieve Telegram bot gevonden (zocht naar '{BOT_NAME}').")
    print("   -> Script gaat door zonder notificaties.")
    TELEGRAM_BOT_TOKEN = None

# Laad Chat IDs alleen als er een token is
if TELEGRAM_BOT_TOKEN:
    TELEGRAM_CHAT_IDS = [u["chat_id"] for u in telegram_users if u.get("enabled")]
    if not TELEGRAM_CHAT_IDS:
        print("⚠️ WAARSCHUWING: Wel een bot, maar geen actieve gebruikers (chat_ids) gevonden.")

telegram_users = config.get("telegram", {}).get("users", [])
TELEGRAM_CHAT_IDS = [u["chat_id"] for u in telegram_users if u.get("enabled")]

# --- INITIALIZATION ---

print("Starting CowCatcherAI...")

# 1. Zorg dat het model bestaat (download indien nodig)
final_model_path = check_and_download_model(camera_model_file, master_model_url)

# 2. Laad Model
print(f"Loading detection model: {final_model_path}")
model = YOLO(final_model_path, task='detect')
print("Detection model successfully loaded")

print(f"Connecting to camera: {CAMERA_NAME}")

# 3. Setup folders
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

save_folder = os.path.join(DATA_DIR, f"mounting_detections_{CAMERA_ID}")
if not os.path.exists(save_folder):
    os.makedirs(save_folder)
    print(f"Folder '{save_folder}' created")

print(f"Telegram bot active for {len(TELEGRAM_CHAT_IDS)} chat(s)")

# --- THREADING SETUP FOR TELEGRAM ---
telegram_queue = Queue()
telegram_stats = {'sent': 0, 'failed': 0}

def telegram_worker():
    while True:
        try:
            task = telegram_queue.get()
            if task is None: break
            
            task_type, *args = task
            
            if task_type == 'photo':
                image_path, caption, disable_notification = args
                result = _send_telegram_photo_sync(image_path, caption, disable_notification)
                telegram_stats['sent' if result else 'failed'] += 1
                    
            elif task_type == 'message':
                message = args[0]
                result = _send_telegram_message_sync(message)
                telegram_stats['sent' if result else 'failed'] += 1
            
            telegram_queue.task_done()
        except Exception as e:
            print(f"ERROR in telegram worker: {str(e)}")

def _send_telegram_photo_sync(image_path, caption, disable_notification=False):
    success_count = 0
    if not TELEGRAM_CHAT_IDS: return False
    
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'disable_notification': disable_notification
                }
                response = requests.post(url, files=files, data=data, timeout=30)
                
            if response.status_code != 200:
                print(f"ERROR sending Telegram photo to chat {chat_id}: {response.text}")
            else:
                success_count += 1
        except Exception as e:
            print(f"ERROR sending Telegram photo to chat {chat_id}: {str(e)}")
    return success_count > 0

def _send_telegram_message_sync(message):
    success_count = 0
    if not TELEGRAM_CHAT_IDS: return False

    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {'chat_id': chat_id, 'text': message}
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code != 200:
                print(f"ERROR sending Telegram message to chat {chat_id}: {response.text}")
            else:
                success_count += 1
        except Exception as e:
            print(f"ERROR sending Telegram message to chat {chat_id}: {str(e)}")
    return success_count > 0

def send_telegram_photo(image_path, caption, disable_notification=False):
    telegram_queue.put(('photo', image_path, caption, disable_notification))
    return True

def send_telegram_message(message):
    telegram_queue.put(('message', message))
    return True

def test_telegram_connection():
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("Telegram bot connection successfully tested.")
            return True
        else:
            print(f"ERROR testing Telegram connection: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR testing Telegram connection: {str(e)}")
        return False

# Test Telegram connection
if not test_telegram_connection():
    print("WARNING: Telegram connection failed or not configured. Script continues without alerts.")
else:
    # Start Telegram worker thread only if connection works
    telegram_thread = Thread(target=telegram_worker, daemon=True)
    telegram_thread.start()
    print("Telegram worker thread started")

# Open the camera stream
print("Opening camera stream...")
cap = cv2.VideoCapture(RTSP_URL)
if not cap.isOpened():
    print("ERROR: Cannot open camera stream")
    exit()
else:
    print("Camera stream successfully opened")

frame_count = 0
last_detection_time = None
notification_counter = 0
confidence_history = deque(maxlen=10)
frame_history = deque(maxlen=10)
timestamp_history = deque(maxlen=10)
collecting_screenshots = False
collection_start_time = None
event_detections = []
peak_detected = False
inactivity_period = 0

print(f"Processing started, every {process_every_n_frames} frames will be analyzed")

start_message = f"📋 Cowcatcher detection script started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
if SEND_STATUS_NOTIFICATIONS:
    send_telegram_message(start_message)

def format_timestamp_for_display(ts):
    return f"{ts[6:8]}-{ts[4:6]}-{ts[:4]}"

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Cannot read frame from camera")
            cap.release()
            time.sleep(5)
            cap = cv2.VideoCapture(RTSP_URL)
            continue
            
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"Frames: {frame_count} | Queue: {telegram_queue.qsize()} | Sent: {telegram_stats['sent']}", flush=True)
        
        if frame_count % process_every_n_frames == 0:
            results = model.predict(source=frame, classes=[0], conf=0.2, verbose=False)
            
            highest_conf_detection = None
            highest_conf = 0.0
            if len(results[0].boxes) > 0:
                sorted_detections = sorted(results[0].boxes, key=lambda x: float(x.conf), reverse=True)
                if len(sorted_detections) > 0:
                    highest_conf_detection = sorted_detections[0]
                    highest_conf = float(highest_conf_detection.conf)
            
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            # History bijhouden
            confidence_history.append(highest_conf if highest_conf_detection else 0.0)
            frame_history.append(frame.copy())
            timestamp_history.append(timestamp)
                
            can_send_notification = (last_detection_time is None or 
                                    (current_time - last_detection_time).total_seconds() > cooldown_period)
            
            # Start conditie
            if highest_conf >= SAVE_THRESHOLD and not collecting_screenshots and can_send_notification:
                print(f"Starting screenshot collection for {COLLECTION_TIME} seconds")
                collecting_screenshots = True
                collection_start_time = current_time
                event_detections = []
                peak_detected = False
                
                # Voeg historie toe
                for i in range(len(confidence_history)):
                    if confidence_history[i] >= SAVE_THRESHOLD:
                        hist_frame = frame_history[i]
                        hist_ts = timestamp_history[i]
                        hist_conf = confidence_history[i]
                        
                        hist_path = os.path.join(save_folder, f"mounting_detected_{hist_ts}_conf{hist_conf:.2f}_history.jpg")
                        cv2.imwrite(hist_path, hist_frame)
                        event_detections.append((hist_conf, None, hist_ts, hist_path, None))
                
            if collecting_screenshots:
                # Tijdens collectie
                if highest_conf >= SAVE_THRESHOLD:
                    orig_path = os.path.join(save_folder, f"mounting_detected_{timestamp}_conf{highest_conf:.2f}.jpg")
                    cv2.imwrite(orig_path, frame)
                    
                    # Bewaar resultaat object voor later annoteren
                    event_detections.append((highest_conf, None, timestamp, orig_path, results[0]))
                    
                    inactivity_period = 0
                    last_detection_time = current_time
                    
                    if highest_conf >= PEAK_DETECTION_THRESHOLD and not peak_detected:
                        peak_detected = True
                        print(f"Possible peak detected: {highest_conf:.2f}")
                else:
                    if last_detection_time is not None:
                        inactivity_period = (current_time - last_detection_time).total_seconds()
                
                collection_duration = (current_time - collection_start_time).total_seconds()
                
                # Stop condities
                stop_collection = False
                if (peak_detected and collection_duration >= MIN_COLLECTION_TIME): stop_collection = True
                elif collection_duration >= COLLECTION_TIME: stop_collection = True
                elif inactivity_period >= INACTIVITY_STOP_TIME: stop_collection = True
                
                if stop_collection:
                    print(f"Collection stopped. Detections: {len(event_detections)}")
                    
                    # Filter relevante detecties
                    valid_detections = [d for d in event_detections if d[0] >= NOTIFY_THRESHOLD]
                    
                    if len(valid_detections) >= MIN_HIGH_CONFIDENCE_DETECTIONS:
                        # Sorteer op confidence
                        event_detections.sort(key=lambda x: x[0], reverse=True)
                        top_selection = event_detections[:MAX_SCREENSHOTS]
                        
                        notification_counter += 1
                        play_sound = (notification_counter % SOUND_EVERY_N_NOTIFICATIONS == 0)
                        
                        for idx, (conf, _, ts, orig_path, res_obj) in enumerate(top_selection):
                            final_send_path = orig_path
                            
                            # Annoteren indien gewenst
                            if SEND_ANNOTATED_IMAGES and res_obj is not None:
                                annotated_path = orig_path.replace(".jpg", "_annotated.jpg")
                                annotated_img = res_obj.plot()
                                cv2.imwrite(annotated_path, annotated_img)
                                final_send_path = annotated_path
                            
                            sound_icon = "🔊" if play_sound else "🔇"
                            msg = f"{sound_icon} Mounting detected {format_timestamp_for_display(ts)} - Conf: {conf:.2f}\nCapture {idx+1}/{len(top_selection)}"
                            
                            send_telegram_photo(final_send_path, msg, disable_notification=not play_sound)
                            print(f"Telegram queued: {conf:.2f}")
                            
                        last_detection_time = current_time
                    
                    collecting_screenshots = False
                    peak_detected = False
            
            if SHOW_LIVE_FEED and len(results) > 0:
                annotated_frame = results[0].plot()
                cv2.imshow(f"Cam {CAMERA_ID}", annotated_frame)
        
        if SHOW_LIVE_FEED and (cv2.waitKey(1) & 0xFF == ord('q')):
            break

except KeyboardInterrupt:
    print("Script stopped by user")
    stop_reason = "Manual Stop (Ctrl+C)"
except Exception as e:
    print(f"Critical Error: {str(e)}")
    stop_reason = f"Error: {str(e)}"
    
finally:
    print("Cleaning up...")
    telegram_queue.put(None)
    if 'telegram_thread' in locals() and telegram_thread.is_alive():
        telegram_thread.join(timeout=5)
    
    cap.release()
    if SHOW_LIVE_FEED: cv2.destroyAllWindows()
    
    if SEND_STATUS_NOTIFICATIONS and 'stop_reason' in locals():
        _send_telegram_message_sync(f"⚠️ Script Stopped: {stop_reason}")