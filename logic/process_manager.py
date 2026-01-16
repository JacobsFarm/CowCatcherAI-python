import subprocess
import sys
import threading
import time
import os
import requests
from datetime import datetime

# SETTINGS
WATCHDOG_TIMEOUT = 90   
WATCHDOG_INTERVAL = 5   
MAX_RETRIES = 5         
HIBERNATION_TIME = 3600 

class ProcessManager:
    def __init__(self, config_manager, log_callback=None):
        self.cfg = config_manager
        self.processes = {}  
        self.heartbeats = {} 
        self.restarting = set() 
        self.retry_counts = {} 
        self.log_callback = log_callback 
        
        self.hibernating_cameras = {} 
        self.alert_sent = {}          
        
        self.watchdog_running = True
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()

    def log(self, cam_id, message):
        if self.log_callback:
            self.log_callback(cam_id, message)
        else:
            print(f"[{cam_id}] {message}")

    def _send_watchdog_alert(self, cam_id):
        if self.alert_sent.get(cam_id, False):
            self.log(cam_id, "ℹ️ No new alert sent (already reported).")
            return

        def _send():
            try:
                cam = self.cfg.get_camera_by_id(cam_id)
                if not cam: return
                bot_name = cam.get("telegram_bot", "")
                bots = self.cfg.get_telegram_bots()
                token = next((b['token'] for b in bots if b['name'] == bot_name and b['enabled']), None)
                if not token: return
                users = self.cfg.get_telegram_users()
                chat_ids = [u['chat_id'] for u in users if u['enabled']]
                if not chat_ids: return

                msg = (f"🚨 <b>WATCHDOG ALERT</b> 🚨\n\n"
                       f"Camera: <b>{cam.get('name', cam_id)}</b>\n"
                       f"Status: 🛑 <b>STOPPED (Hibernation)</b>\n\n"
                       f"The watchdog made {MAX_RETRIES} attempts. Failed.\n"
                       f"The system will automatically retry in <b>1 hour</b>.\n"
                       f"You will not receive further notifications unless it succeeds.")

                for chat_id in chat_ids:
                    url = f"https://api.telegram.org/bot{token}/sendMessage"
                    try:
                        requests.post(url, data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'HTML'}, timeout=10)
                    except Exception: pass
                
                self.log(cam_id, "🚨 Telegram emergency message sent.")
                
            except Exception as e:
                self.log(cam_id, f"Error in telegram alert: {e}")

        self.alert_sent[cam_id] = True
        threading.Thread(target=_send, daemon=True).start()

    def start_camera(self, camera_id):
            if camera_id in self.processes and self.processes[camera_id].poll() is None:
                return

            # Retrieve camera configuration to determine type
            cam_config = self.cfg.get_camera_by_id(camera_id)
            if not cam_config:
                self.log(camera_id, "Error: Camera configuration not found.")
                return

            # DETERMINE WHICH SCRIPT TO RUN
            handler_type = cam_config.get("type", "cowcatcher") # Default is cowcatcher
            
            script_name = ""
            if handler_type == "cowcatcher":
                script_name = "cowcatcher_handler.py"
            elif handler_type == "calvingcatcher":
                script_name = "calving_handler.py"
            else:
                self.log(camera_id, f"Error: Unknown handler type '{handler_type}'")
                return

            self.heartbeats[camera_id] = time.time()
            if camera_id not in self.retry_counts:
                self.retry_counts[camera_id] = 0

            if camera_id in self.hibernating_cameras:
                del self.hibernating_cameras[camera_id]

            if getattr(sys, 'frozen', False):
                # .EXE MODE (Relevant later for compilation)
                # You should create separate .exe files or pass arguments here later
                base_path = os.path.dirname(sys.executable)
                worker_exe = os.path.join(base_path, "cowcatcher_worker.exe") 
                cmd = [worker_exe, camera_id]
            else:
                # SCRIPT MODE (Development)
                # ADJUSTMENT: Choose script dynamically
                worker_script = os.path.join("handlers", script_name)
                
                if not os.path.exists(worker_script):
                     self.log(camera_id, f"Error: Script '{worker_script}' not found.")
                     return
                     
                cmd = [sys.executable, '-u', worker_script, camera_id]
            
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            try:
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, bufsize=1, creationflags=creation_flags, encoding='utf-8', errors='replace'
                )
                self.processes[camera_id] = process
                
                t_out = threading.Thread(target=self._read_output, args=(process, camera_id, "INFO"))
                t_err = threading.Thread(target=self._read_output, args=(process, camera_id, "ERROR"))
                t_out.daemon = True; t_err.daemon = True
                t_out.start(); t_err.start()
                
                self.log(camera_id, f"Process started ({handler_type}) - Attempt {self.retry_counts[camera_id]}/{MAX_RETRIES}")
            except Exception as e:
                self.log(camera_id, f"Error starting: {str(e)}")

    def stop_camera(self, camera_id):
        if camera_id in self.heartbeats: del self.heartbeats[camera_id]
        if camera_id in self.retry_counts: del self.retry_counts[camera_id]
            
        if camera_id in self.processes:
            proc = self.processes[camera_id]
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: proc.kill()
            del self.processes[camera_id]
            self.log(camera_id, "Process stopped.")

    def restart_camera(self, camera_id):
        if camera_id in self.restarting: return
        self.restarting.add(camera_id)
        
        current_retries = self.retry_counts.get(camera_id, 0)
        
        if current_retries >= MAX_RETRIES:
            self.log(camera_id, f"❌ WATCHDOG: Limit ({MAX_RETRIES}x) reached. Camera entering hibernation for 1 hour.")
            self._send_watchdog_alert(camera_id)
            self.stop_camera(camera_id)
            self.hibernating_cameras[camera_id] = time.time()
            if camera_id in self.restarting: self.restarting.remove(camera_id)
            return

        self.retry_counts[camera_id] = current_retries + 1
        self.log(camera_id, f"⚠️ WATCHDOG: No response. Restarting (Attempt {self.retry_counts[camera_id]})...")
        
        if camera_id in self.processes:
            proc = self.processes[camera_id]
            try: proc.terminate(); proc.wait(timeout=2)
            except: proc.kill()
            del self.processes[camera_id]

        time.sleep(2)
        self.start_camera(camera_id)
        
        if camera_id in self.restarting: self.restarting.remove(camera_id)

    def stop_all(self):
        self.watchdog_running = False
        ids = list(self.processes.keys())
        for cam_id in ids: self.stop_camera(cam_id)

    def is_running(self, camera_id):
        return camera_id in self.processes and self.processes[camera_id].poll() is None

    def _read_output(self, process, cam_id, level):
        stream = process.stdout if level == "INFO" else process.stderr
        for line in iter(stream.readline, ''):
            if line:
                stripped_line = line.strip()
                self.log(cam_id, stripped_line)
                
                if "Frames processed" in stripped_line or "Opening camera stream" in stripped_line:
                    self.heartbeats[cam_id] = time.time()
                    if self.retry_counts.get(cam_id, 0) > 0:
                        self.retry_counts[cam_id] = 0
                    if self.alert_sent.get(cam_id, False):
                        self.alert_sent[cam_id] = False
                        self.log(cam_id, "✅ System is stable again. Alarm reset.")
            else:
                break
        stream.close()

    def _watchdog_loop(self):
        while self.watchdog_running:
            current_time = time.time()
            active_cameras = list(self.processes.keys())
            for cam_id in active_cameras:
                if cam_id in self.heartbeats and cam_id not in self.restarting:
                    last_seen = self.heartbeats[cam_id]
                    if (current_time - last_seen) > WATCHDOG_TIMEOUT:
                        msg = f"Watchdog timeout! {int(current_time - last_seen)}s no activity."
                        if self.log_callback: self.log_callback(cam_id, f"[SYSTEM] {msg}")
                        threading.Thread(target=self.restart_camera, args=(cam_id,)).start()
            
            hibernating_ids = list(self.hibernating_cameras.keys())
            for cam_id in hibernating_ids:
                sleep_start = self.hibernating_cameras[cam_id]
                if (current_time - sleep_start) > HIBERNATION_TIME:
                    self.log(cam_id, "⏰ Hibernation over (1 hour). Attempting to restart...")
                    del self.hibernating_cameras[cam_id]
                    self.retry_counts[cam_id] = 0
                    threading.Thread(target=self.start_camera, args=(cam_id,)).start()

            time.sleep(WATCHDOG_INTERVAL)