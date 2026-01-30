import mss
import time
import os
import datetime
import re
import threading
import customtkinter as ctk
import subprocess
import sys

# Configure appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ScreenshotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Auto Screenshot Recorder")
        self.geometry("500x400")
        self.resizable(False, False)

        # Variables
        self.is_running = False
        self.capture_thread = None
        self.base_dir = os.path.join(os.getcwd(), "Screenshots")

        # Layout
        self.create_widgets()
        
        # Ensure base directory exists just in case
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def create_widgets(self):
        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(pady=20, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(
            self.header_frame, 
            text="Status: Stopped", 
            font=("Roboto", 16, "bold"),
            text_color="gray"
        )
        self.status_label.pack(pady=10)

        # Log Area
        self.log_textbox = ctk.CTkTextbox(self, height=200)
        self.log_textbox.pack(pady=10, padx=20, fill="x")
        self.log_textbox.configure(state="disabled") # Read-only initially

        # Controls
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(pady=20, padx=20, fill="x")

        self.start_button = ctk.CTkButton(
            self.button_frame, 
            text="START", 
            command=self.start_recording,
            fg_color="#2CC985",
            hover_color="#229966",
            text_color="white",
            font=("Roboto", 14, "bold")
        )
        self.start_button.pack(side="left", expand=True, padx=5)

        self.stop_button = ctk.CTkButton(
            self.button_frame, 
            text="STOP", 
            command=self.stop_recording,
            fg_color="#FF5555",
            hover_color="#CC4444",
            text_color="white",
            state="disabled",
            font=("Roboto", 14, "bold")
        )
        self.stop_button.pack(side="left", expand=True, padx=5)

        self.open_folder_button = ctk.CTkButton(
            self.button_frame, 
            text="Open Folder", 
            command=self.open_output_folder,
            fg_color="#3B8ED0",
            hover_color="#36719F"
        )
        self.open_folder_button.pack(side="left", expand=True, padx=5)

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def get_next_sequence_number(self, directory):
        if not os.path.exists(directory):
            return 1
        
        max_num = 0
        pattern = re.compile(r'_(\d{5})\.png$')
        
        for filename in os.listdir(directory):
            match = pattern.search(filename)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        
        return max_num + 1

    def capture_loop(self):
        with mss.mss() as sct:
            while self.is_running:
                now = datetime.datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H-%M")
                
                daily_dir = os.path.join(self.base_dir, date_str)
                if not os.path.exists(daily_dir):
                    os.makedirs(daily_dir)
                    self.log(f"Created folder: {date_str}")
                
                seq_num = self.get_next_sequence_number(daily_dir)
                
                self.log(f"[{now.strftime('%H:%M:%S')}] Capturing...")

                for i, monitor in enumerate(sct.monitors[1:], 1):
                    monitor_letter = chr(65 + i - 1)
                    filename = f"Monitor{monitor_letter}_{time_str}_{seq_num:05d}.png"
                    filepath = os.path.join(daily_dir, filename)
                    
                    try:
                        sct.shot(mon=i, output=filepath)
                        self.log(f"Saved: {filename}")
                    except Exception as e:
                        self.log(f"Error: {e}")

                # Wait logic
                # Check every 0.1s to allow immediate stop
                target_time = datetime.datetime.now().replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
                
                while self.is_running and datetime.datetime.now() < target_time:
                    time.sleep(0.5)

    def start_recording(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.status_label.configure(text="Status: Recording...", text_color="#2CC985")
        self.start_button.configure(state="disabled", fg_color="gray")
        self.stop_button.configure(state="normal", fg_color="#FF5555")
        
        self.log("Started recording.")
        
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()

    def stop_recording(self):
        if not self.is_running:
            return
            
        self.is_running = False
        self.status_label.configure(text="Status: Stopped", text_color="gray")
        self.start_button.configure(state="normal", fg_color="#2CC985")
        self.stop_button.configure(state="disabled", fg_color="gray")
        self.log("Stopped recording.")

    def open_output_folder(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        
        if sys.platform == 'win32':
            os.startfile(self.base_dir)
        else:
            # Fallback for other OS if needed, though user is on Windows
            subprocess.Popen(['explorer', self.base_dir])

    def on_close(self):
        if self.is_running:
            self.stop_recording()
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1.0)
            
        self.destroy()

if __name__ == "__main__":
    app = ScreenshotApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
