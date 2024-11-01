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
from pathlib import Path
import tkinter.font as tkFont

# Define paths for assets and fonts
OUTPUT_PATH = Path(__file__).parent
ITALIANAFONT_PATH = OUTPUT_PATH / Path(r"Italiana\Italiana-Regular.ttf")
ISTOKREGFONT_PATH = OUTPUT_PATH / Path(r"Istok_Web\IstokWeb-Regular.ttf")
ISTOKBOLDFONT_PATH = OUTPUT_PATH / Path(r"Istok_Web\IstokWeb-Bold.ttf")

# Global variable for treeview
treeview = None

# List to store session logs in-memory
usage_logs = []

def create_horizontal_gradient(canvas, colors, width, height):
    """Creates a horizontal gradient with the given list of colors on the canvas."""
    sections = len(colors) - 1
    section_width = width // sections

    for i in range(sections):
        color1 = colors[i]
        color2 = colors[i + 1]
        for x in range(section_width):
            ratio = x / section_width
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(i * section_width + x, 0, i * section_width + x, height, fill=color)

def rgb_to_tuple(hex_color):
    """Convert a hex color to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def center_window(window):
    """Center the window on the screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = window.winfo_width()
    window_height = window.winfo_height()

    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    window.geometry(f'{window_width}x{window_height}+{x}+{y}')

def rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Draws a rounded rectangle with the given radius."""
    points = [x1 + radius, y1,
              x1 + radius, y1,
              x2 - radius, y1,
              x2 - radius, y1,
              x2, y1,
              x2, y1 + radius,
              x2, y1 + radius,
              x2, y2 - radius,
              x2, y2 - radius,
              x2, y2,
              x2 - radius, y2,
              x2 - radius, y2,
              x1 + radius, y2,
              x1 + radius, y2,
              x1, y2,
              x1, y2 - radius,
              x1, y2 - radius,
              x1, y1 + radius,
              x1, y1 + radius,
              x1, y1]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def log_session_start():
    """Logs the start of a session with the current timestamp."""
    usage_logs.append({'start_time': datetime.now(), 'end_time': None})

def log_session_stop():
    """Logs the stop time of the latest session."""
    if usage_logs and usage_logs[-1]['end_time'] is None:
        usage_logs[-1]['end_time'] = datetime.now()

def calculate_duration(start_time, end_time):
    """Calculates the duration between start and stop times."""
    duration = end_time - start_time
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{int(hours)} hours {int(minutes)} minutes"

def update_treeview():
    """Update the Treeview with new session data."""
    global treeview
    if treeview:
        # Clear existing entries
        for item in treeview.get_children():
            treeview.delete(item)

        # Insert updated data
        for log in usage_logs:
            if log['end_time']:
                date_str = log['start_time'].strftime('%m/%d/%Y')
                duration_str = calculate_duration(log['start_time'], log['end_time'])
                treeview.insert('', 'end', values=(date_str, duration_str))

def on_start():
    """Callback when the user starts the session."""
    log_session_start()
    print("Session started!")
    update_treeview()

def on_stop():
    """Callback when the user stops the session and updates the Treeview."""
    log_session_stop()
    print("Session stopped!")
    update_treeview()

def bind_button(canvas, button_rect, button_text, hover_color, original_color, on_click_action):
    """Bind hover and click events to both button rectangle and button text."""
    def on_enter_combined(event):
        canvas.master.config(cursor="hand2")
        canvas.itemconfig(button_rect, fill=hover_color)
    
    def on_leave_combined(event):
        canvas.master.config(cursor="")
        canvas.itemconfig(button_rect, fill=original_color)

    for item in (button_rect, button_text):
        canvas.tag_bind(item, "<Enter>", on_enter_combined)
        canvas.tag_bind(item, "<Leave>", on_leave_combined)
        canvas.tag_bind(item, "<Button-1>", lambda event: on_click_action())

def create_treeview(canvas, parent_frame):
    """Create and configure the Treeview widget."""
    global treeview
    
    try:
        istok_regular_font = tkFont.Font(family="Istok Web", size=17)
        istok_bold_font = tkFont.Font(family="Istok Web", size=20, weight="bold")
    except:
        istok_regular_font = tkFont.Font(family="Arial", size=20)
        istok_bold_font = tkFont.Font(family="Arial", size=20, weight="bold")

    treeview_frame = tk.Frame(parent_frame, bg='#ADD8E6')
    treeview_frame.pack(expand=True, fill="both") 

    treeview = ttk.Treeview(treeview_frame, columns=("date", "duration"), show='headings', height=3)

    treeview.heading("date", text="DATE")
    treeview.heading("duration", text="DURATION")

    treeview.column("date", width=250, anchor="center")
    treeview.column("duration", width=250, anchor="center")

    treeview.pack(expand=True, fill="both", padx=10, pady=10)
    
    canvas.create_window(100, 400, anchor="nw", window=treeview_frame, width=800, height=200)

class ImageProcessor:
    def __init__(self, root):
        self.root = root
        self.profile_path = 'profiles.json'
        self.profiles = self.load_profiles()
        self.current_profile = None
        self.running = False
        self.start_time = None
        self.total_usage_time = 0
        self.pomodoro_running = False
        self.pomodoro_thread = None
        self.canvas = None
        self.setup_ui()
        
    def manage_profiles(self):
        # Load custom font
        try:
            istok_regular_font = tkFont.Font(family="Istok Web", size=17)
            istok_bold_font = tkFont.Font(family="Istok Web", size=20, weight="bold")
        except:
            istok_regular_font = tkFont.Font(family="Arial", size=20)
            istok_bold_font = tkFont.Font(family="Arial", size=20, weight="bold")

        new_window = tk.Toplevel(self.root)
        new_window.title("Manage Profiles")
        new_window.geometry("400x300")

        # Disable resizing the new window if desired
        new_window.resizable(False, False)

        # Set a background color
        new_window.configure(bg='#ADD8E6')

        # Header Label
        header_label = tk.Label(new_window, text="Select a Profile", font=istok_bold_font, bg='#ADD8E6')
        header_label.pack(pady=(20, 10))
        
         # Frame for profile list and details
        main_frame = tk.Frame(new_window, bg='#ADD8E6')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Listbox for profiles
        profile_list = tk.Listbox(new_window, font=istok_regular_font, bg='white', selectbackground='#87CEEB')
        profile_list.pack(pady=5, fill=tk.BOTH, expand=True)

        # Insert profiles into the Listbox
        for profile in self.profiles:
            profile_list.insert(tk.END, profile)

        # Frame for profile details
        details_frame = tk.Frame(main_frame, bg='#ADD8E6')
        details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Labels for profile details
        brightness_label = tk.Label(details_frame, text="Brightness:", font=istok_regular_font, bg='#ADD8E6', anchor='w')
        brightness_label.pack(fill=tk.X)

        color_temp_label = tk.Label(details_frame, text="Color Temperature:", font=istok_regular_font, bg='#ADD8E6', anchor='w')
        color_temp_label.pack(fill=tk.X)

        break_time_label = tk.Label(details_frame, text="Break Time:", font=istok_regular_font, bg='#ADD8E6', anchor='w')
        break_time_label.pack(fill=tk.X)

        def update_profile_details(event):
         if profile_list.curselection():
            selected = profile_list.get(profile_list.curselection())
            profile = self.profiles[selected]
            brightness_label.config(text=f"Brightness: {profile['brightness']}")
            color_temp_label.config(text=f"Color Temperature: {profile['color_temperature']}K")
            break_time_label.config(text=f"Break Time: {profile['break_time']} minutes")

        profile_list.bind('<<ListboxSelect>>', update_profile_details)

        # Frame for buttons
        button_frame = tk.Frame(new_window, bg='#ADD8E6')
        button_frame.pack(pady=(10, 20))

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

        # Button to close the window
        close_button = tk.Button(button_frame, text="Close", font=istok_regular_font, bg='white', fg='black', command=new_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

        # Center the window on the screen
        new_window.update_idletasks()
        x = (new_window.winfo_screenwidth() // 2) - (new_window.winfo_width() // 2)
        y = (new_window.winfo_screenheight() // 2) - (new_window.winfo_height() // 2)
        new_window.geometry(f"+{x}+{y}")

    def load_profiles(self):
        print("samol")
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r') as file:
            print(json.load(file))
            return json.load(file)
        print("sampol")
        # Load custom font
        try:
            italiana_font = tkFont.Font(family="Italiana", size=70)
            istok_regular_font = tkFont.Font(family="Istok Web", size=17)
            istok_bold_font = tkFont.Font(family="Istok Web", size=20, weight="bold")
        except:
            italiana_font = tkFont.Font(family="Arial", size=20)
            istok_regular_font = tkFont.Font(family="Arial", size=20)
            istok_bold_font = tkFont.Font(family="Arial", size=20, weight="bold")

        new_window = tk.Toplevel(self.root)
        new_window.title("Manage Profiles")
        new_window.geometry("400x300")

        # Disable resizing the new window if desired
        new_window.resizable(False, False)

        # Set a background color
        new_window.configure(bg='#ADD8E6')

        # Header Label
        header_label = tk.Label(new_window, text="Select a Profile", font=istok_bold_font, bg='#ADD8E6')
        header_label.pack(pady=(20, 10))

        # Listbox for profiles
        profile_list = tk.Listbox(new_window, font=istok_regular_font, bg='white', selectbackground='#87CEEB')
        profile_list.pack(pady=5, fill=tk.BOTH, expand=True)

        # Insert profiles into the Listbox
        for profile in self.profiles:
            profile_list.insert(tk.END, profile)

        # Frame for buttons
        button_frame = tk.Frame(new_window, bg='#ADD8E6')
        button_frame.pack(pady=(10, 20))

        # Button to close the window
        close_button = tk.Button(button_frame, text="Close", font=istok_regular_font, bg='white', fg='black', command=new_window.destroy)
        close_button.pack(side=tk.LEFT, padx=5)

        # Center the window on the screen
        new_window.update_idletasks()
        x = (new_window.winfo_screenwidth() // 2) - (new_window.winfo_width() // 2)
        y = (new_window.winfo_screenheight() // 2) - (new_window.winfo_height() // 2)
        new_window.geometry(f"+{x}+{y}")

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
        
    def setup_ui(self):
        self.root.geometry("1000x700")
        self.root.configure(bg="#FFFFFF")

        try:
            italiana_font = tkFont.Font(family="Italiana", size=70)
            istok_regular_font = tkFont.Font(family="Istok Web", size=17)
            istok_bold_font = tkFont.Font(family="Istok Web", size=20, weight="bold")
        except:
            italiana_font = tkFont.Font(family="Arial", size=20)
            istok_regular_font = tkFont.Font(family="Arial", size=20)
            istok_bold_font = tkFont.Font(family="Arial", size=20, weight="bold")

        self.canvas = tk.Canvas(self.root, width=1000, height=700)
        self.canvas.pack()

        # Create the canvas and apply the gradient background
        color1 = rgb_to_tuple("#89CFF0")
        color2 = rgb_to_tuple("#96D8B9")
        color3 = rgb_to_tuple("#C9A0DC")
        colors = [color1, color2, color3]
        create_horizontal_gradient(self.canvas, colors, 1000, 700)

        # Define button colors
        green_color = "#8FBC8F"
        hover_green = "#556B2F"
        blue_color = "#4682B4"
        hover_blue = "#4169E1"

        # Place the white rounded rectangle
        rounded_rectangle(self.canvas, 15.0, 30.0, 985.0, 670.0, radius=25, fill="#FFFFFF", outline="")

        # Create the header rounded rectangle and text
        rounded_rectangle(self.canvas, 15.0, 30.0, 986.0, 129.0, radius=25, fill="#6A5ACD", outline="")
        self.canvas.create_text(300.0, 26.0, anchor="nw", text="LUMINAR", fill="#FFFFFF", font=italiana_font)

        start_button = rounded_rectangle(self.canvas, 26.0, 154.0, 249.0, 205.0, radius=20, fill=green_color, outline="")
        start_button_text = self.canvas.create_text(137.5, 180.0, text="Start", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, start_button, start_button_text, hover_green, green_color, self.start_processing)

        stop_button = rounded_rectangle(self.canvas, 268.0, 154.0, 491.0, 205.0, radius=20, fill=green_color, outline="")
        stop_button_text = self.canvas.create_text(379.0, 180.0, text="Stop", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, stop_button, stop_button_text, hover_green, green_color, self.stop_processing)

        settings_button = rounded_rectangle(self.canvas, 510.0, 154.0, 733.0, 205.0, radius=20, fill=green_color, outline="")
        settings_button_text = self.canvas.create_text(621.0, 180.0, text="Settings", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, settings_button, settings_button_text, hover_green, green_color, self.open_settings)

        profile_button = rounded_rectangle(self.canvas, 752.0, 154.0, 975.0, 205.0, radius=20, fill=green_color, outline="")
        profile_button_text = self.canvas.create_text(863.0, 180.0, text="Manage Profiles", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, profile_button, profile_button_text, hover_green, green_color, self.manage_profiles)

        pomodoro_button = rounded_rectangle(self.canvas, 376.0, 238.0, 625.0, 297.0, radius=20, fill=blue_color, outline="")
        self.pomodoro_button_text = self.canvas.create_text(500.5, 267.5, text="Start Pomodoro", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, pomodoro_button, self.pomodoro_button_text, hover_blue, blue_color, self.toggle_pomodoro)

        # Screen usage history labels
        self.canvas.create_text(41.0, 363.0, anchor="nw", text="Screen Usage History", fill="#6A5ACD", font=istok_bold_font)

        rounded_rectangle(self.canvas, 66, 400, 935, 600, radius=20, fill="#ADD8E6", outline='')
        create_treeview(self.canvas, self.root)

        # Pomodoro indicator label
        self.pomodoro_status_text = self.canvas.create_text(350.0, 311.0, anchor="nw", text="Pomodoro Status: Idle", fill="#483D8B", font=istok_bold_font)

        # Screen usage label
        self.screen_usage_label = tk.Label(self.root, text="Screen Usage: Not started", bg="#FFFFFF", fg="#6A5ACD", font=istok_regular_font)
        self.screen_usage_label.pack(pady=10)

    def start_processing(self):
        if not self.running:
            self.running = True

            # Disable buttons while processing
            # self.disable_buttons()

            if self.start_time is None:
                self.start_time = time.time()
            on_start()
            threading.Thread(target=self.process_images).start()
            threading.Thread(target=self.monitor_health).start()
            threading.Thread(target=self.adaptive_color_temperature).start()
            self.update_screen_usage()

    def stop_processing(self):
        if self.running:
            self.running = False

            # Enable buttons after processing
            # self.enable_buttons()

            current_session_time = time.time() - self.start_time
            self.total_usage_time += current_session_time
            total_usage_minutes = int(self.total_usage_time / 60)
            seconds_remaining = int(self.total_usage_time % 60)
            current_date = time.strftime("%m/%d/%Y")
            usage_time_str = f"{total_usage_minutes} minutes and {seconds_remaining} seconds"
            
            # Update usage_logs
            log_session_stop()
            
            # Update treeview
            update_treeview()
            
            messagebox.showinfo("Session Ended", f"Total screen usage time: {usage_time_str}.")
            self.start_time = None
            self.update_screen_usage()
    
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
            time.sleep(5) # Seconds of before adjusting

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

    def toggle_pomodoro(self):
        if not self.pomodoro_running:
            self.start_pomodoro()
        else:
            self.stop_pomodoro()
            
    def start_pomodoro(self):
        if not self.pomodoro_running:
            self.pomodoro_running = True
            self.canvas.itemconfig(self.pomodoro_button_text, text="Stop Pomodoro")
            self.canvas.itemconfig(self.pomodoro_status_text, text="Pomodoro Status: Running")
            self.pomodoro_thread = threading.Thread(target=self.pomodoro_timer)
            self.pomodoro_thread.start()

    def stop_pomodoro(self):
        if self.pomodoro_running:
            self.pomodoro_running = False
            self.canvas.itemconfig(self.pomodoro_button_text, text="Start Pomodoro")
            self.canvas.itemconfig(self.pomodoro_status_text, text="Pomodoro Status: Idle")
            if self.pomodoro_thread:
                self.pomodoro_thread.join()

    def pomodoro_timer(self):
        pomodoro_duration = 25 * 60  # 25 minutes
        break_duration = 5 * 60  # 5 minutes
        
        while self.pomodoro_running:
            # Work session
            for remaining in range(pomodoro_duration, 0, -1):
                if not self.pomodoro_running:
                    return
                mins, secs = divmod(remaining, 60)
                self.canvas.itemconfig(self.pomodoro_status_text, text=f"Pomodoro Status: Working - {mins:02d}:{secs:02d}")
                time.sleep(1)
            
            if not self.pomodoro_running:
                return

            # Break time
            messagebox.showinfo("Pomodoro", "Time for a 5-minute break!")
            for remaining in range(break_duration, 0, -1):
                if not self.pomodoro_running:
                    return
                mins, secs = divmod(remaining, 60)
                self.canvas.itemconfig(self.pomodoro_status_text, text=f"Pomodoro Status: Break - {mins:02d}:{secs:02d}")
                time.sleep(1)
            
            if not self.pomodoro_running:
                return

            messagebox.showinfo("Pomodoro", "Break over! Ready to focus again?")

        self.canvas.itemconfig(self.pomodoro_status_text, text="Pomodoro Status: Idle")
        self.canvas.itemconfig(self.pomodoro_button_text, text="Start Pomodoro")

    def update_screen_usage(self):
        if self.running:
            current_session_time = time.time() - self.start_time
            total_usage_minutes = int((self.total_usage_time + current_session_time) / 60)
            self.screen_usage_label.config(text=f"Total Screen Usage Time: {total_usage_minutes} minutes")
            self.canvas.after(1000, self.update_screen_usage)

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
    root.title("Luminar - Adaptive Screen Brightness")

    # Center the window after its initial configuration
    root.after(1, lambda: center_window(root))

    # Disable window resizing
    root.resizable(False, False)

    app = ImageProcessor(root)
    root.mainloop()
