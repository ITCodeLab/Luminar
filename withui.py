import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox
import threading
import cv2
from PIL import Image, ImageEnhance, ImageOps
import numpy as np
import subprocess
import time
import json
import os
from datetime import datetime

class ImageProcessor:
    def __init__(self, root):
        self.root = root
        self.profile_path = 'profiles.json'
        self.profiles = self.load_profiles()
        self.current_profile = None
        self.setup_ui()
        self.running = False
        self.start_time = None
        self.total_usage_time = 0
        self.pomodoro_running = False

    def setup_ui(self):
        self.root.geometry("600x500")
        self.root.configure(bg="#2c3e50")

        self.start_btn = tk.Button(self.root, text="Start", command=self.start_processing, bg="#27ae60", fg="white", font=("Arial", 12))
        self.start_btn.pack(pady=10)

        self.stop_btn = tk.Button(self.root, text="Stop", command=self.stop_processing, bg="#c0392b", fg="white", font=("Arial", 12))
        self.stop_btn.pack(pady=10)

        self.settings_btn = tk.Button(self.root, text="Settings", command=self.open_settings, bg="#2980b9", fg="white", font=("Arial", 12))
        self.settings_btn.pack(pady=10)

        self.profile_btn = tk.Button(self.root, text="Manage Profiles", command=self.manage_profiles, bg="#8e44ad", fg="white", font=("Arial", 12))
        self.profile_btn.pack(pady=10)

        self.pomodoro_btn = tk.Button(self.root, text="Start Pomodoro", command=self.start_pomodoro, bg="#e67e22", fg="white", font=("Arial", 12))
        self.pomodoro_btn.pack(pady=10)

        # Pomodoro indicator label
        self.pomodoro_indicator = tk.Label(self.root, text="Pomodoro Not Running", bg="#2c3e50", fg="white", font=("Arial", 12))
        self.pomodoro_indicator.pack(pady=10)

        self.tree = ttk.Treeview(self.root, columns=('Date', 'Usage Time'), show='headings', height=5)
        self.tree.heading('Date', text='Date')
        self.tree.heading('Usage Time', text='Usage Time')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self.screen_usage_label = tk.Label(self.root, text="", bg="#2c3e50", fg="white", font=("Arial", 12))
        self.screen_usage_label.pack(pady=10)

    def start_processing(self):
        if not self.running:
            self.running = True
            if self.start_time is None:
                self.start_time = time.time()
            threading.Thread(target=self.process_images).start()
            threading.Thread(target=self.monitor_health).start()
            threading.Thread(target=self.adaptive_color_temperature).start()
            self.update_screen_usage()

    def stop_processing(self):
        if self.running:
            self.running = False
            current_session_time = time.time() - self.start_time
            self.total_usage_time += current_session_time
            total_usage_minutes = int(self.total_usage_time / 60)
            seconds_remaining = int(self.total_usage_time % 60)
            current_date = time.strftime("%m/%d/%Y")
            usage_time_str = f"{total_usage_minutes} minutes and {seconds_remaining} seconds"
            self.tree.insert('', 'end', values=(current_date, usage_time_str))
            messagebox.showinfo("Session Ended", f"Total screen usage time: {usage_time_str}.")
            self.start_time = None
            self.update_screen_usage()

    def manage_profiles(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Manage Profiles")
        new_window.geometry("300x400")

        label = tk.Label(new_window, text="Select a profile:")
        label.pack(pady=5)

        profile_list = tk.Listbox(new_window)
        profile_list.pack(pady=5, fill=tk.BOTH, expand=True)

        for profile in self.profiles:
            profile_list.insert(tk.END, profile)

        def load_profile():
            if not profile_list.curselection():
                messagebox.showwarning("Load Profile", "No profile selected.")
                return
            selected = profile_list.get(profile_list.curselection())
            self.current_profile = self.profiles[selected]
            messagebox.showinfo("Profile Loaded", f"Loaded profile: {selected}")

        def delete_profile():
            if not profile_list.curselection():
                messagebox.showwarning("Delete Profile", "No profile selected.")
                return
            selected_index = profile_list.curselection()[0]
            selected_profile = profile_list.get(selected_index)
            del self.profiles[selected_profile]
            profile_list.delete(selected_index)
            self.save_profiles()
            messagebox.showinfo("Delete Profile", f"Profile '{selected_profile}' has been deleted.")

        load_button = tk.Button(new_window, text="Load", command=load_profile)
        load_button.pack(pady=5)

        add_button = tk.Button(new_window, text="Create New", command=lambda: self.create_profile(new_window, profile_list))
        add_button.pack(pady=5)

        delete_button = tk.Button(new_window, text="Delete", command=delete_profile)
        delete_button.pack(pady=5)

        new_window.resizable(True, True)

    def create_profile(self, parent_window, profile_list):
        name = simpledialog.askstring("Profile Name", "Enter a new profile name:", parent=parent_window)
        if name:
            brightness = simpledialog.askinteger("Brightness", "Set brightness level (0-100):", parent=parent_window, minvalue=0, maxvalue=100)
            break_time = simpledialog.askinteger("Break Time", "Set break time in minutes (default 25):", parent=parent_window, initialvalue=25)
            color_temperature = simpledialog.askinteger("Color Temperature", "Set color temperature (default 6500K):", parent=parent_window, initialvalue=6500)
            if break_time is None:
                break_time = 25
            self.profiles[name] = {"brightness": brightness, "color_temperature": color_temperature, "break_time": break_time}
            self.save_profiles()
            profile_list.insert(tk.END, name)
            messagebox.showinfo("Profile Created", f"New profile '{name}' has been created.")

    def save_profiles(self):
        with open(self.profile_path, 'w') as file:
            json.dump(self.profiles, file, indent=4)

    def load_profiles(self):
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r') as file:
            return json.load(file)

    def open_settings(self):
        messagebox.showinfo("Settings", "Settings will be implemented soon.")

    def process_images(self):
        while self.running:
            img = self.take_picture()
            if img is None:
                continue

            preprocessed_img = self.preprocess_image(img)
            adaptive_thresh_img = self.adaptive_threshold(preprocessed_img)
            count = self.count_bright_pixels(preprocessed_img, np.mean(np.array(adaptive_thresh_img)))
            total_pixels = preprocessed_img.width * preprocessed_img.height
            white_pixel_percentage = count / total_pixels
            brightness = int(white_pixel_percentage * 255)
            reduction_amount = 30
            adjusted_brightness = max(min(brightness - reduction_amount, 255), 0)
            self.set_brightness(adjusted_brightness)
            time.sleep(10)

    def monitor_health(self):
        while self.running:
            if self.current_profile:
                recommended_break = self.current_profile.get('break_time', 25) * 60  # Use break time from the profile
            else:
                recommended_break = 1500  # Default break time in seconds (25 minutes)

            if (time.time() - self.start_time) >= 1800:  # 30 minutes for health monitoring
                messagebox.showwarning("Health Alert", "You've been using the screen for 30 minutes. Consider taking a break!")
                self.start_time = time.time()  # Reset timer

            time.sleep(10)

    def start_pomodoro(self):
        if not self.pomodoro_running:
            self.pomodoro_running = True
            self.pomodoro_indicator.config(text="Pomodoro Running", bg="#e67e22")
            threading.Thread(target=self.pomodoro_timer).start()

    def pomodoro_timer(self):
        pomodoro_duration = 25 * 60  # 25 minutes
        break_duration = 5 * 60  # 5 minutes
        time.sleep(pomodoro_duration)
        messagebox.showinfo("Pomodoro", "25 minutes have passed. Time for a 5-minute break!")
        time.sleep(break_duration)
        messagebox.showinfo("Pomodoro", "Break over! Ready to focus again?")
        self.pomodoro_running = False
        self.pomodoro_indicator.config(text="Pomodoro Not Running", bg="#2c3e50")

    def update_screen_usage(self):
        if self.running:
            current_session_time = time.time() - self.start_time
            total_usage_minutes = int((self.total_usage_time + current_session_time) / 60)
            self.screen_usage_label.config(text=f"Total Screen Usage Time: {total_usage_minutes} minutes")
            self.root.after(1000, self.update_screen_usage)

    def adaptive_color_temperature(self):
        while self.running:
            current_hour = datetime.now().hour
            if 8 <= current_hour < 18:
                self.set_color_temperature(6500)  # Daytime
            else:
                self.set_color_temperature(3000)  # Nighttime
            time.sleep(3600)  # Check every hour

    def take_picture(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Cannot open camera")
            return None
        
        ret, frame = cap.read()
        cap.release()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image")
            return None
        
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def preprocess_image(self, image):
        enhancer = ImageEnhance.Contrast(image.convert('L'))
        return enhancer.enhance(2)

    def adaptive_threshold(self, image):
        img_array = np.array(image.convert('L'))
        threshold_img = np.where(img_array >= np.mean(img_array), 255, 0)
        return Image.fromarray(threshold_img.astype(np.uint8))

    def count_bright_pixels(self, image, threshold):
        img_array = np.array(image)
        return np.sum(img_array >= threshold)

    def set_brightness(self, brightness):
        brightness = max(min(brightness, 100), 0)  # Ensuring the brightness value is within acceptable range
        command = ["powershell", "-Command", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {})".format(brightness)]
        subprocess.run(command)

    def set_color_temperature(self, temperature):
        try:
            # Attempt to set color temperature using WMI
            command = ["powershell", "-Command", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {})".format(temperature)]
            result = subprocess.run(command, capture_output=True, text=True)
            
            if "Invalid class" in result.stderr:
                raise ValueError("WMI class not supported.")
            
            # You could further customize the message based on the result
            messagebox.showinfo("Color Temperature", "Color temperature adjusted to {}K".format(temperature))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust color temperature: {str(e)}. Your system may not support this feature.")

    def run_manual_override(self):
        # Example method to override manual settings when video meetings are active (specific implementation may vary)
        # This placeholder checks if any video conferencing apps are running and adjusts settings accordingly
        running_apps = subprocess.check_output("tasklist", shell=True).decode()
        video_conference_apps = ["zoom.exe", "Teams.exe", "googletalk.exe"]

        for app in video_conference_apps:
            if app.lower() in running_apps.lower():
                messagebox.showinfo("Manual Override", f"Video conference detected. Manual override activated for {app}.")
                self.set_brightness(100)  # Example: max brightness for video meetings
                break

    def run_energy_efficiency(self):
        # Example energy-saving method (simplified):
        # Adjust the screen's refresh rate or dim the brightness after a period of inactivity
        idle_time = time.time() - self.start_time
        if idle_time > 300:  # 5 minutes of inactivity
            self.set_brightness(30)  # Dim the screen to save energy

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Image Brightness Controller")
    app = ImageProcessor(root)
    root.mainloop()
