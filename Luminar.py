import json
import os
import tkinter.font as tkFont
import time
import threading
import subprocess
import tkinter as tk
import numpy as np
import cv2
import pyautogui
import screen_brightness_control as sbc
from tkinter import simpledialog, messagebox
from datetime import datetime
from tkinter import ttk
from PIL import Image, ImageEnhance
from pathlib import Path
from plyer import notification

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

def log_session_start(status='Luminar'):
    """Logs the start of a session with the current timestamp and status."""
    usage_logs.append({'start_time': datetime.now(), 'status': status, 'duration': None})

def log_session_stop():
    """Logs the stop time of the latest session."""
    if usage_logs and usage_logs[-1]['duration'] is None:
        # Check the last session's status
        last_status = usage_logs[-1]['status']

        # Finalize the status at the end of the session
        if 'Luminar' in last_status and 'Pomodoro' in last_status:
            usage_logs[-1]['status'] = 'Luminar, Pomodoro'  # Combined status if both were active
        elif 'Luminar' in last_status:
            usage_logs[-1]['status'] = 'Luminar'  # Only Luminar if it was the only activity
        elif 'Pomodoro' in last_status:
            usage_logs[-1]['status'] = 'Pomodoro'  # Only Pomodoro if it was the only activity
        else:
            usage_logs[-1]['status'] = 'Unknown'  # Handle as needed

        # Log the stop time and calculate the duration
        end_time = datetime.now()  # Get the current time as end time
        start_time = usage_logs[-1]['start_time']  # Get the start time from the last log
        usage_logs[-1]['duration'] = calculate_duration(start_time, end_time)

        print(f"Logged stop for session: {usage_logs[-1]}")  # Debugging print

def calculate_duration(start_time, end_time):
    """Calculates the duration between start and stop times."""
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours} hours, {minutes} minutes"

def update_treeview():
    """Update the Treeview with new session data."""
    global treeview
    if treeview:
        # Clear existing entries
        for item in treeview.get_children():
            treeview.delete(item)

        # Insert updated data
        for log in usage_logs:
            if log['duration'] is not None:
                # Display the status and duration
                status_str = log['status']
                duration_str = log['duration']
                treeview.insert('', 'end', values=(status_str, duration_str))
            elif log['status'] == 'Running':
                # If there's an ongoing Pomodoro session, show it as the latest entry
                treeview.insert('', 'end', values=(log['status'], 'In Progress'))

def on_start(has_luminar):
    """Callback when the user starts the session."""
    print("==START BTN")
    if has_luminar:
        log_session_start(status="Luminar, Pomodoro")
    else :
        log_session_start(status='Luminar')  # Log 'Luminar' when 
    update_treeview()  # Update the Treeview to show the new status

def on_stop():
    print("Stop BTN")
    """Callback when the user stops the session and updates the Treeview."""
    log_session_stop()
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
    """Create and configure the Treeview widget with a custom font."""
    global treeview
    
    try:
        istok_regular_font = tkFont.Font(family="Istok Web", size=15)
        istok_bold_font = tkFont.Font(family="Istok Web", size=17, weight="bold")
    except:
        istok_regular_font = tkFont.Font(family="Arial", size=15)
        istok_bold_font = tkFont.Font(family="Arial", size=17, weight="bold")

    # Configure Treeview style with custom font
    style = ttk.Style()
    style.configure("Custom.Treeview", font=istok_regular_font)  # Cells font
    style.configure("Custom.Treeview.Heading", font=istok_bold_font)  # Header font

    treeview_frame = tk.Frame(parent_frame, bg='#ADD8E6')
    treeview_frame.pack(expand=True, fill="both")

    # Apply the custom style to the Treeview widget
    treeview = ttk.Treeview(treeview_frame, columns=("status", "duration"), show='headings', height=3, style="Custom.Treeview")

    # Update the headings
    treeview.heading("status", text="STATUS")
    treeview.heading("duration", text="DURATION")

    treeview.column("status", width=250, anchor="center")
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
        self.is_video_conference_active = False  # Flag to track video conference state
        self.current_brightness = 100  # Default brightness level
        self.brightness_label = None  # To hold the brightness label
        self.tutorial_window = None
        
        self.setup_ui()

    def check_camera_availability_async(self):
        """Run the camera availability check in a separate thread."""
        def check_camera():
            if not hasattr(self, "_camera_checked"):  # Check if the status has already been checked
                self._camera_checked = True  # Mark the camera as checked
                
                cap = cv2.VideoCapture(0)  # Try to open the default camera
                if not cap.isOpened():
                    messagebox.showwarning("Camera Status", "Camera is not detected.\n Proceeding with Screen-shot mode.")
                else:
                    messagebox.showinfo("Camera Status", "Camera Detected, Please Proceed!")
                    cap.release()  # Release the camera if it was opened

        # Run the check in a new thread
        threading.Thread(target=check_camera, daemon=True).start()
        
    def show_tutorial(self):
        """Display a tutorial window with key features of the application."""
        # Check if the tutorial window is already open
        if self.tutorial_window and self.tutorial_window.winfo_exists():
            self.tutorial_window.lift()  # Bring the existing window to the front
            return  # Exit the method to avoid creating a new window
        
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("Tutorial - Luminar")
        tutorial_window.geometry("1050x850")
        tutorial_window.configure(bg='#ADD8E6')
        tutorial_window.resizable(False, False)
        tutorial_window.overrideredirect(True)
        tutorial_window.grab_set()

        # Disable the X (close button)
        tutorial_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Center the window on the screen
        tutorial_window.update_idletasks()
        screen_width = tutorial_window.winfo_screenwidth()
        screen_height = tutorial_window.winfo_screenheight()
        x = (screen_width // 2) - (1050 // 2)
        y = (screen_height // 2) - (850 // 2)
        tutorial_window.geometry(f"1050x850+{x}+{y}")
        
        # Create fonts
        regular_font = tkFont.Font(family="Arial", size=13)
        bold_font = tkFont.Font(family="Arial", size=14, weight="bold")

         # Create a canvas and a scrollbar
        canvas = tk.Canvas(tutorial_window, bg='#ADD8E6')
        scrollbar = tk.Scrollbar(tutorial_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ADD8E6')

        # Configure the canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Create a window in the canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Tutorial content
        tutorial_text = (
            "I. Key Features of LUMINAR\n"
            "\n"
            "1. Adaptive Brightness:\n"
            "   - Automatically adjusts your screen brightness based on ambient lighting.\n"
            "   - Reduces eye strain and enhances screen visibility in varying light conditions.\n"
            "2. Image Processing:\n"
            "   - Enhance images by adjusting brightness and contrast.\n"
            "   - Click 'Start' to process images captured by your camera.\n"
            "3. Pomodoro Timer:\n"
            "   - Boost productivity with structured work intervals (25 minutes) followed by 5-minute breaks.\n"
            "   - Helps improve focus and reduces fatigue.\n"
            "4. Profile Management:\n"
            "   - Create and manage profiles for preferred brightness and color settings.\n"
            "   - Quickly switch settings for activities like working, gaming, or reading.\n"
            "5. Health Monitoring:\n"
            "   - Notifications remind you to take breaks for better eye health.\n"
             "\n"
            "II. Getting Started\n"
            "- Start: Capture and process images to adjust screen brightness.\n"
            "- Stop: End the current image processing session.\n"
            "- Profile Settings: Access and modify saved profiles.\n"
            "- Pomodoro On: Activate the Pomodoro timer.\n"
            "\n"
            "III. Tips for Using LUMINAR\n"
            "\n"
            "- Ensure your camera is connected and functional for image capture.\n"
            "- Customize profiles for different times of day or activities.\n"
            "\n"
            "IV. User Guide for LUMINAR\n"
            "Why Certain Actions Are Necessary:\n"
            "\n"
            "1. Camera Access:\n"
            "   - Captures images to assess lighting and adjust brightness.\n"
            "2. Brightness Modification:\n"
            "   - Ensures screen comfort by adapting brightness dynamically.\n"
            "3. Screen Usage Tracking:\n"
            "   - Provides break reminders and usage insights to promote well-being.\n"
            "4. Screen-Shot Mode:\n"
            "  - Automatically switch to using a screenshot-based method to analyze your screen brightness and adjust it accordingly.\n"
            "\n"
            "V. Security Measures:\n"
            "At LUMINAR, your security and privacy are our top priorities. Here’s how we ensure a safe experience:\n"
            "\n"
            "1. Reputable Libraries:\n"
            "   - Utilizes industry-standard libraries with regular updates.\n"
            "2. Data Privacy:\n"
            "   - Processes data locally and never shares it without consent.\n"
            "3. Transparency:\n"
            "   - Clearly documents permissions and data handling.\n"
            "4. Regular Updates:\n"
            "   - Provides security patches, performance improvements, and new features.\n"
            "5. Guaranteed Privacy: \n"
            "   -  The app does not save any data or images. Your privacy is guaranteed.\n"
            "\n"
            "Thank you for choosing LUMINAR! We hope it enhances your screen experience and productivity.\n"
        )
        
        # Split the text into lines and create labels for each line with text wrapping
        for line in tutorial_text.splitlines():
            if (
                line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.")or line.startswith("3.") or line.startswith("5.") or 
                line.startswith("I.") or line.startswith("II.") or line.startswith("III.") or line.startswith("IV.")or line.startswith("V.") or
                line.startswith("To get started:") or line.startswith("Tips for Using Luminar:")
            ):
                label = tk.Label(scrollable_frame, text=line, font=bold_font, bg='#ADD8E6', anchor='w', wraplength=950)
            else:
                label = tk.Label(scrollable_frame, text=line, font=regular_font, bg='#ADD8E6', anchor='w', wraplength=950)
            label.pack(pady=(0, 2), padx=(30, 10), anchor='w')
       
       # Close button at the bottom of the scrollable content
        close_button = tk.Button(
            scrollable_frame,
            text="DONE",
            command=lambda: [
                self.check_camera_availability_async(),
                tutorial_window.destroy(),
                notification.notify(
                    title="Loading",
                    message="Checking Camera Availability",
                    timeout=3  # Time out in seconds
                )
            ],
            bg='#6A5ACD',
            fg='white',
            font=bold_font,
            activebackground='#483D8B',
            activeforeground='white'
        )
        close_button.pack(pady=20, padx=(50, 0), anchor='center')
        
    def apply_profile(self):
        """Apply the current profile settings to the application."""
        if self.current_profile:
            brightness = self.current_profile["brightness"]
            color_temperature = self.current_profile["color_temperature"]
            break_time = self.current_profile["break_time"]
            
            # Set brightness
            self.set_brightness(brightness)
            # Set color temperature
            self.set_color_temperature(color_temperature)
            # Open Night Light settings if the color temperature is 3000K
            if color_temperature == 'Warm':
                self.open_night_light_settings()  # Open Night Light settings
            messagebox.showinfo("Profile Applied", f"Applied Profile:\nBrightness: {brightness}%\nColor Temperature: {color_temperature} \nBreak Time: {break_time} minutes")
    
    def open_night_light_settings(self):
        """Open Night Light settings in Windows."""
        try:
            messagebox.showinfo("Night Light", "Please toggle Night Light manually in the settings for more accuracy.")
            subprocess.run("start ms-settings:display", shell=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open settings: {str(e)}")

    def manage_profiles(self):
        """Manage user profiles for brightness and color settings."""
        try:
            istok_regular_font = tkFont.Font(family="Istok Web", size=17)
            istok_bold_font = tkFont.Font(family="Istok Web", size=20, weight="bold")
        except:
            istok_regular_font = tkFont.Font(family="Arial", size=17)
            istok_bold_font = tkFont.Font(family="Arial", size=20, weight="bold")

        new_window = tk.Toplevel(self.root)
        new_window.title("Profile Settings")
        new_window.geometry("400x600")
        new_window.configure(bg='#ADD8E6')
        new_window.resizable(False, False)

        # Center the window on the screen
        new_window.update_idletasks()
        x = (new_window.winfo_screenwidth() // 2) - (new_window.winfo_width() // 2)
        y = (new_window.winfo_screenheight() // 2) - (new_window.winfo_height() // 2)
        new_window.geometry(f"+{x}+{y}")

        # Header Label
        header_label = tk.Label(new_window, text="Select a Profile", font=istok_bold_font, bg='#ADD8E6')
        header_label.pack(pady=(20, 10))

        # Main Frame for profile list and details
        main_frame = tk.Frame(new_window, bg='#ADD8E6')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Listbox for profiles with margins and rounded corner effect
        profile_frame = tk.Frame(main_frame, bg='#87CEEB', bd=1, relief="solid")
        profile_frame.pack(pady=(10, 10), padx=10, fill=tk.BOTH, expand=False)

        profile_list = tk.Listbox(profile_frame, font=istok_regular_font, bg='white', selectbackground='#87CEEB', bd=0, highlightthickness=0, relief="flat", width=10, height=5)
        profile_list.pack(pady=2, padx=2, fill=tk.BOTH, expand=True)

        # Populate the Listbox
        for profile in self.profiles:
            profile_list.insert(tk.END, profile)

        # Frame for profile details
        details_frame = tk.Frame(main_frame, bg='#ADD8E6')
        details_frame.pack(pady=10, padx=10, fill=tk.X)

        # Labels for profile details
        brightness_label = tk.Label(details_frame, text="Brightness:", font=istok_regular_font, bg='#ADD8E6', anchor='w')
        brightness_label.pack(fill=tk.X)

        color_temp_label = tk.Label(details_frame, text="Color Temperature:", font=istok_regular_font, bg='#ADD8E6', anchor='w')
        color_temp_label.pack(fill=tk.X)


        break_time_label = tk.Label(details_frame, text="Break Time:", font=istok_regular_font, bg='#ADD8E6', anchor='w')
        break_time_label.pack(fill=tk.X)
        
        def update_profile_details(event):
            """Update the profile details displayed when a profile is selected."""
            if profile_list.curselection():
                selected = profile_list.get(profile_list.curselection())
                profile = self.profiles[selected]
                
                # Check if selected_temp is set, and use it for the color temperature
                if color_temp_label == 3000:
                    color_temp_label.config(text=f"Color Temperature: Warm")
                elif color_temp_label == 6500:
                    color_temp_label.config(text=f"Color Temperature: Cool")
                else:
                    color_temp_label.config(text=f"Color Temperature: {profile['color_temperature']}")
                
                brightness_label.config(text=f"Brightness: {profile['brightness']}")
                break_time_label.config(text=f"Break Time: {profile['break_time']} minutes")

        profile_list.bind('<<ListboxSelect>>', update_profile_details)

        # Button Frame with updated layout
        button_frame = tk.Frame(new_window, bg='#ADD8E6')
        button_frame.pack(pady=(10, 0))
        
        def apply_selected_profile():
            """Apply the selected profile settings."""
            if profile_list.curselection():
                selected = profile_list.get(profile_list.curselection())
                self.current_profile = self.profiles[selected]
                self.apply_profile()  # Apply the profile settings
       
        def load_profile(self):
            """Load the selected profile and apply its settings."""
            if not profile_list.curselection():
                messagebox.showwarning("Load Profile", "No profile selected.")
                return
            
            selected = profile_list.get(profile_list.curselection())
            self.current_profile = self.profiles[selected]
            
            # Ensure the current profile has all required keys
            if 'brightness' not in self.current_profile or 'color_temperature' not in self.current_profile or 'break_time' not in self.current_profile:
                messagebox.showerror("Error", "The selected profile is missing required settings.")
                return
            
            self.apply_profile()  # Apply the profile settings
            messagebox.showinfo("Profile Loaded", f"Loaded profile: {selected}")
            
        def delete_profile():
            """Delete the selected profile from the list."""
            if not profile_list.curselection():
                messagebox.showwarning("Delete Profile", "No profile selected.")
                return
            selected_index = profile_list.curselection()[0]
            selected_profile = profile_list.get(selected_index)
            del self.profiles[selected_profile]
            profile_list.delete(selected_index)
            self.save_profiles()
            messagebox.showinfo("Delete Profile", f"Profile '{selected_profile}' has been deleted.")
            new_window.lift()
        
        # Create a helper function for making rounded buttons
        def create_rounded_button(canvas, x1, y1, x2, y2, text, command, color, hover_color):
            button = rounded_rectangle(canvas, x1, y1, x2, y2, radius=20, fill=color, outline=color)
            label = canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, font=istok_bold_font, fill="black")
            
            # Bind actions
            canvas.tag_bind(button, "<Button-1>", lambda e: command())
            canvas.tag_bind(label, "<Button-1>", lambda e: command())
            
            # Hover effects
            canvas.tag_bind(button, "<Enter>", lambda e: canvas.itemconfig(button, fill=hover_color))
            canvas.tag_bind(button, "<Leave>", lambda e: canvas.itemconfig(button, fill=color))
            canvas.tag_bind(label, "<Enter>", lambda e: canvas.itemconfig(button, fill=hover_color))
            canvas.tag_bind(label, "<Leave>", lambda e: canvas.itemconfig(button, fill=color))
            
        # "New" button with padding
        new_button_canvas = tk.Canvas(button_frame, width=120, height=60, bg='#ADD8E6', highlightthickness=0) 
        new_button_canvas.pack(side=tk.LEFT, padx=(0, 10))  
        create_rounded_button(new_button_canvas, 5, 5, 115, 55, "New", lambda: self.create_profile(new_window, profile_list), "#ADD8E6", "#B0C4DE")

        # "Delete" button with padding
        delete_button_canvas = tk.Canvas(button_frame, width=120, height=60, bg='#ADD8E6', highlightthickness=0)  
        delete_button_canvas.pack(side=tk.LEFT, padx=(10, 0))  
        create_rounded_button(delete_button_canvas, 5, 5, 115, 55, "Delete", delete_profile, "#ADD8E6", "#B0C4DE")

        # Separate frame for the "Apply" button below with extended width
        apply_button_frame = tk.Frame(new_window, bg='#ADD8E6')
        apply_button_frame.pack(pady=(10, 20))  

        # "Apply" button with padding and longer width
        apply_button_canvas = tk.Canvas(apply_button_frame, width=240, height=60, bg='#ADD8E6', highlightthickness=0) 
        apply_button_canvas.pack()
        create_rounded_button(apply_button_canvas, 5, 5, 235, 55, "Apply", apply_selected_profile, "#87CEEB", "#6CA6CD")

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
        # Create the brightness percentage label
        self.brightness_label = self.canvas.create_text(800, 380, text=f"Brightness: {self.current_brightness}%", fill="#000000", font=istok_bold_font)

        start_button = rounded_rectangle(self.canvas, 26.0, 154.0, 249.0, 205.0, radius=20, fill=green_color, outline="")
        start_button_text = self.canvas.create_text(137.5, 180.0, text="Start", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, start_button, start_button_text, hover_green, green_color, self.start_processing)

        stop_button = rounded_rectangle(self.canvas, 268.0, 154.0, 491.0, 205.0, radius=20, fill=green_color, outline="")
        stop_button_text = self.canvas.create_text(379.0, 180.0, text="Stop", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, stop_button, stop_button_text, hover_green, green_color, self.stop_processing)

        about_us_button = rounded_rectangle(self.canvas, 510.0, 154.0, 733.0, 205.0, radius=20, fill=green_color, outline="")
        about_us_button_text = self.canvas.create_text(621.0, 180.0, text="About Us", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, about_us_button, about_us_button_text, hover_green, green_color, self.open_about_us)

        profile_button = rounded_rectangle(self.canvas, 752.0, 154.0, 975.0, 205.0, radius=20, fill=green_color, outline="")
        profile_button_text = self.canvas.create_text(863.0, 180.0, text="Profile Settings", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, profile_button, profile_button_text, hover_green, green_color, self.manage_profiles)

        pomodoro_button = rounded_rectangle(self.canvas, 376.0, 238.0, 625.0, 297.0, radius=20, fill=blue_color, outline="")
        self.pomodoro_button_text = self.canvas.create_text(500.5, 267.5, text="Pomodoro On", fill="#FFFFFF", font=istok_bold_font)
        bind_button(self.canvas, pomodoro_button, self.pomodoro_button_text, hover_blue, blue_color, self.toggle_pomodoro)

        # Screen usage history labels
        self.canvas.create_text(41.0, 363.0, anchor="nw", text="Screen Usage History", fill="#6A5ACD", font=istok_bold_font)

        rounded_rectangle(self.canvas, 66, 400, 935, 600, radius=20, fill="#ADD8E6", outline='')
        create_treeview(self.canvas, self.root)

        # Pomodoro indicator label
        self.pomodoro_status_text = self.canvas.create_text(350.0, 311.0, anchor="nw", text="Pomodoro Status: Idle", fill="#483D8B", font=istok_bold_font)
        self.screen_usage_label = tk.Label(self.root, text="Screen Usage: Not started", bg="#FFFFFF", fg="#6A5ACD", font=istok_regular_font)
        self.screen_usage_label.pack(pady=10)
        
        messagebox.showinfo(
            "Reminder",
            "Discover Adaptive Brightness, Image Processing, Pomodoro Timer, Profile Management, and Health Monitoring."
        )

    def start_processing(self):
        if not self.running:
            self.running = True
            self.session_time = 0  # Reset session time for a new session
            self.start_time = time.time()  # Start tracking the current session
            on_start(self.pomodoro_running)
            update_treeview() # fishy
            messagebox.showinfo("Application Started",  "The application has started successfully.")
            threading.Thread(target=self.process_images).start()
            threading.Thread(target=self.monitor_health).start()
            threading.Thread(target=self.adaptive_color_temperature).start()
            self.update_screen_usage()

    def stop_processing(self):
        if self.running:
            self.running = False

            # Calculate session time and update total usage
            current_session_time = time.time() - self.start_time
            self.session_time = current_session_time
            self.total_usage_time += current_session_time

            # Format time for display
            session_minutes = int(self.session_time / 60)
            session_seconds = int(self.session_time % 60)
            total_minutes = int(self.total_usage_time / 60)
            total_seconds = int(self.total_usage_time % 60)

            # Update usage logs (implement these methods as needed)
            log_session_stop()
            update_treeview()

            self.start_time = None
            self.session_time = 0  # Reset session time for next start
            self.update_screen_usage()
    
    def create_profile(self, parent_window, profile_list):
        name = simpledialog.askstring("Profile Name", "Enter a new profile name:", parent=parent_window)
        if name:
            brightness = simpledialog.askinteger("Brightness", "Set brightness level (0-100):", parent=parent_window, minvalue=0, maxvalue=100)
            break_time = simpledialog.askinteger("Break Time", "Set break time in minutes (default 5):", parent=parent_window, initialvalue=5)
            
            # Create a new window for selecting color temperature
            color_temp_window = tk.Toplevel(parent_window)
            color_temp_window.title("Select Color Temperature")

            # Set fixed size for the window (optional for better centering)
            window_width = 300
            window_height = 200
            color_temp_window.geometry(f"{window_width}x{window_height}")

            # Calculate position to center the window on the screen
            screen_width = color_temp_window.winfo_screenwidth()
            screen_height = color_temp_window.winfo_screenheight()
            x_position = (screen_width // 2) - (window_width // 2)
            y_position = (screen_height // 2) - (window_height // 2)

            # Set the geometry with the calculated position
            color_temp_window.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")


            # Label for instructions
            tk.Label(color_temp_window, text="Select Color Temperature:").pack(pady=10)

            # Combobox for selecting color temperature
            color_temp_combobox = ttk.Combobox(color_temp_window, values=["Warm", "Cool"])
            color_temp_combobox.current(0)  # Set default value

            # Center the combobox within the window using `place`
            color_temp_combobox.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            # Button to confirm selection
            def confirm_selection():
                selected_temp = color_temp_combobox.get()
                if selected_temp == "Warm":
                    color_temperature = 3000
                elif selected_temp == "Cool":
                    color_temperature = 6500
                else:
                    color_temperature = None  # Handle unexpected values

                if color_temperature is not None:
                    # Save the profile
                    print(f"Creating profile: {name}, Brightness: {brightness}, Color Temperature: {selected_temp}, Break Time: {break_time}")
                    self.profiles[name] = {"brightness": brightness, "color_temperature": selected_temp, "break_time": break_time}
                    self.save_profiles()
                    profile_list.insert(tk.END, name)
                    messagebox.showinfo("Profile Created", f"New profile '{name}' has been created.")
                    color_temp_window.destroy()
                else:
                    messagebox.showwarning("Selection Error", "Please select a valid color temperature.")

            tk.Button(color_temp_window, text="Confirm", command=confirm_selection).pack(pady=10)

    def load_profiles(self):
        """Load user profiles from a JSON file."""
        if not os.path.exists(self.profile_path):
            return {}
        with open(self.profile_path, 'r') as file:
            return json.load(file)

    def save_profiles(self):
        """Save user profiles to a JSON file."""
        with open(self.profile_path, 'w') as file:
            json.dump(self.profiles, file, indent=4)

    def open_about_us(self):
        """Open the About Us window with information about the application."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Us - Luminar")
        about_window.geometry("800x700")
        about_window.configure(bg='#ADD8E6')
        about_window.resizable(False, False)

        # Center the window on the screen
        about_window.update_idletasks()
        screen_width = about_window.winfo_screenwidth()
        screen_height = about_window.winfo_screenheight()
        x = (screen_width // 2) - (800 // 2)
        y = (screen_height // 2) - (700 // 2)
        about_window.geometry(f"800x700+{x}+{y}")

        # Try to use custom fonts, fallback to Arial if unavailable
        try:
            istok_bold_font = tkFont.Font(family="Istok Web", size=18, weight="bold")
            istok_regular_font = tkFont.Font(family="Istok Web", size=16)
        except:
            istok_bold_font = tkFont.Font(family="Arial", size=18, weight="bold")
            istok_regular_font = tkFont.Font(family="Arial", size=16)

        # Text content for the About Us section
        about_text = (
            "Welcome to Luminar! Our mission is to improve your screen experience with adaptive brightness and image "
            "enhancement for visual comfort. With user-focused design, Luminar lets you adjust screen settings easily.\n\n"
            "Key Features:\n\n"
            "• Adaptive Brightness: Real-time adjustments for screen brightness and contrast, ensuring smooth performance.\n\n"
            "• Elegant, Customizable UI: Navigate easily with our sleek design and personalized fonts.\n\n"
            "• Persistent Preferences: Your settings are saved for a consistent experience each time.\n\n"
            "• Image Tools: Adjust brightness, contrast, and apply filters with our image processing capabilities.\n\n"
            "Meet the Team\n\n"
            "Adviser: Roma Bondoc Pare\n"
            "Developers:\n"
            "Tanedo, Connerry L.\n"
            "Villareal, Genesis D.\n"
            "Tolentino, Ian D.\n\n"
        )

        # Create a canvas and scrollbar for scrolling functionality
        canvas = tk.Canvas(about_window, bg='#ADD8E6')
        scrollbar = ttk.Scrollbar(about_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ADD8E6')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar in the about_window
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add the Header and Content to scrollable_frame
        header_label = tk.Label(scrollable_frame, text="About Us - Luminar", font=istok_bold_font, bg='#ADD8E6', fg='black')
        header_label.pack(pady=(20, 15))

        about_label = tk.Label(scrollable_frame, text=about_text, font=istok_regular_font, bg='#ADD8E6', fg='black', justify="left", wraplength=750)
        about_label.pack(pady=10, padx=30)
    
    def set_brightness(self, brightness):
        """Adjust screen brightness using the screen_brightness_control module."""
        try:
            # Ensure brightness is within the range of 0 to 100
            brightness = max(min(brightness, 100), 0)
            
            # Set the brightness
            sbc.set_brightness(brightness)
            self.current_brightness = brightness  
            print(f"Brightness set to {brightness}%")
            self.canvas.itemconfig(self.brightness_label, text=f"Brightness: {self.current_brightness}%")
        except Exception as e:
            print(f"Failed to set brightness: {e}")
            
    def process_images(self):
            """Main loop to capture images, process them, and adjust screen brightness accordingly."""
            while self.running:
                start_time = time.time()  # Start time of the loop

                img = self.take_picture()

                if img is None:
                    messagebox.showwarning("Capture Warning", "Both camera and screenshot failed. Please check your setup.")
                    time.sleep(3)  # Fixed wait time for error handling
                    continue

                # Process the captured image
                preprocessed_img = self.preprocess_image(img)
                adaptive_thresh_img = self.adaptive_threshold(preprocessed_img)
                count = self.count_bright_pixels(preprocessed_img, np.mean(np.array(adaptive_thresh_img)))
                total_pixels = preprocessed_img.width * preprocessed_img.height
                white_pixel_percentage = count / total_pixels
                brightness = int(white_pixel_percentage * 255)
                adjusted_brightness = max(min(brightness - 30, 80), 30)  # Apply a reduction to brightness
                self.set_brightness(adjusted_brightness)

                processing_time = time.time() - start_time  # Calculate processing time
                sleep_time = max(0, 3 - processing_time)  # Calculate remaining time to sleep (min 0)
                time.sleep(sleep_time)  # Sleep for the calculated time

    def monitor_health(self):
        """Notify the user to take breaks after prolonged screen usage for eye health."""
        while self.running:
            # Check every 60 seconds
            if (time.time() - self.start_time) >= 1800:  # 1800 seconds = 30 minutes
                messagebox.showwarning("Reminder", "Screen time: 30 minutes. Take a break!")
                self.start_time = time.time()  # Reset the start time after the alert
            time.sleep(60)  # Check every 60 seconds 

    def toggle_pomodoro(self):
        """Toggle the Pomodoro timer on or off."""
        if not self.pomodoro_running:
            self.start_pomodoro()
        else:
            self.stop_pomodoro()
                
    def start_pomodoro(self):
        """Start the Pomodoro timer with work and break intervals."""
        if not self.pomodoro_running:
            self.pomodoro_running = True
            self.canvas.itemconfig(self.pomodoro_button_text, text="Pomodoro Off")
            self.canvas.itemconfig(self.pomodoro_status_text, text="Pomodoro Status: Running")

            # Log to console and update usage logs
            print("Pomodoro session started. Status: Pomodoro On")

            # If the last session is 'Luminar', combine Luminar and Pomodoro into one session
            has_session = usage_logs[-1]['duration'] is None
            if usage_logs and usage_logs[-1]['status'] == 'Luminar' and has_session:
                log_session_start(status='Luminar, Pomodoro')
            else:
                # Start a new Pomodoro session if no Luminar session is currently active
                log_session_start(status='Pomodoro')

            update_treeview()  # Update the Treeview to show the new status

            # Start the Pomodoro timer in a separate thread
            self.pomodoro_thread = threading.Thread(target=self.pomodoro_timer)
            self.pomodoro_thread.start()

    def stop_pomodoro(self):
        """Stop the Pomodoro timer and reset the display."""
        if self.pomodoro_running:
            self.pomodoro_running = False
            self.canvas.itemconfig(self.pomodoro_button_text, text="Pomodoro On")
            self.canvas.itemconfig(self.pomodoro_status_text, text="Pomodoro Status: Idle")

            # Log to console
            print("Pomodoro session stopped. Status: Pomodoro Off")

            # Stop the Pomodoro session and log its stop time
            log_session_stop()  # Log the stop of the Pomodoro session

            update_treeview()  # Update the Treeview to reflect the new status

            if self.pomodoro_thread:
                self.pomodoro_thread.join()

    def pomodoro_timer(self):
        """Implements the Pomodoro work and break intervals."""
        pomodoro_duration = 1 * 5  # 25 minutes  2560
        # Set default values if current_profile is None
        if self.current_profile is None:
            break_duration = 5 * 60  # Default to 5 minutes if no profile is set
        else:
            break_duration = self.current_profile.get('break_time', 5) * 60  # Use break time from profile, default to 5 minutes

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
            messagebox.showinfo("Reminder", "Break Time!")
            for remaining in range(break_duration, 0, -1):
                if not self.pomodoro_running:
                    return
                mins, secs = divmod(remaining, 60)
                self.canvas.itemconfig(self.pomodoro_status_text, text=f"Pomodoro Status: Break - {mins:02d}:{secs:02d}")
                time.sleep(1)
            
            if not self.pomodoro_running:
                return

            messagebox.showinfo("Reminder", "Break's over! Ready?")

        self.canvas.itemconfig(self.pomodoro_status_text, text="Pomodoro Status: Idle")
  
    def update_screen_usage(self):
        """Update the screen usage label with the current session time or total time."""
        if self.running:
            # Calculate the current session time
            current_session_time = time.time() - self.start_time
            session_minutes = int(current_session_time / 60)
            self.screen_usage_label.config(text=f"Total Screen Usage Time: {session_minutes} minutes")
            self.canvas.after(1000, self.update_screen_usage)
        else:
            # Display total usage when not running
            total_minutes = int(self.total_usage_time / 60)
            # self.screen_usage_label.config(text=f"Total Screen Usage Time: {session_minutes} minutes")

    def adaptive_color_temperature(self):
        """Adapts screen color temperature based on time of day, checked every hour."""
        while self.running:
            current_hour = datetime.now().hour
            self.set_color_temperature(6500 if 8 <= current_hour < 18 else 3000)  # Daytime else Nighttime
            time.sleep(3600)  # Check every hour

    def take_picture(self):
        """Capture an image using the camera. Falls back to screenshot if the camera is unavailable."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            # Log that the camera is unavailable and fall back to screenshot
            print("Camera not available, taking a screenshot instead.")
            return self.take_screenshot()  # Fallback to screenshot if camera fails
        ret, frame = cap.read()
        cap.release()
        if not ret:
            # Log that the camera failed to capture an image and fall back to screenshot
            print("Failed to capture image with camera, taking a screenshot instead.")
            return self.take_screenshot() 
        print("Picture captured successfully using the camera.")
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def take_screenshot(self):
        """Capture a screenshot as a fallback when the camera is unavailable or during video conferencing.
        The brightness of the screenshot is reduced by 20%."""
        try:
            screenshot = pyautogui.screenshot()
            print("Screenshot taken successfully.")
            
            # Convert screenshot to a Pillow Image object and reduce brightness
            img = Image.fromarray(np.array(screenshot))
            enhancer = ImageEnhance.Brightness(img)
            reduced_brightness_img = enhancer.enhance(0.85)  # Reduce brightness by 15%
            
            print("Brightness reduced by 15%.")
            return reduced_brightness_img
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None

    def preprocess_image(self, image):
        """Enhance contrast and convert to grayscale."""
        enhancer = ImageEnhance.Contrast(image.convert('L'))
        return enhancer.enhance(2)

    def adaptive_threshold(self, image):
        """Apply adaptive thresholding to the grayscale image."""
        img_array = np.array(image.convert('L'))
        threshold_img = np.where(img_array >= np.mean(img_array), 255, 0)
        return Image.fromarray(threshold_img.astype(np.uint8))

    def count_bright_pixels(self, image, threshold):
        """Count pixels in the image above a brightness threshold."""
        img_array = np.array(image)
        return np.sum(img_array >= threshold)

    def set_color_temperature(self, temperature):
        """Adjust the screen's color temperature based on time of day."""
        try:
            command = ["powershell", "-Command", "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {})".format(temperature)]
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            # result = subprocess.run(command, capture_output=True, text=True)
            if "Invalid class" in result.stderr:
                raise ValueError("WMI class not supported.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to adjust color temperature: {str(e)}. Your system may not support this feature.")

    def run_energy_efficiency(self):
        """Adjust the screen's brightness after a period of inactivity to save energy."""
        idle_time = time.time() - self.start_time
        if idle_time > 300:  # 5 minutes of inactivity
            self.set_brightness(10)  # Dim the screen to save energy

if __name__ == "__main__":
    # Initialize the main application window using Tkinter
    root = tk.Tk()
    
    # Set the title of the application window to "Luminar - Adaptive Screen Brightness"
    root.title("Luminar - Adaptive Screen Brightness")
    
    # Schedule the 'center_window' function to run after 1 millisecond to center the window on the screen
    root.after(1, lambda: center_window(root))
    
    # Prevent the user from resizing the application window
    root.resizable(False, False)
    
    # Create an instance of the ImageProcessor class, passing the main window (root) as an argument
    app = ImageProcessor(root)  # Create the application instance
    
    # # Call the 'show_tutorial' method to display the tutorial window when the application starts
    app.show_tutorial()  # Show the tutorial when the application starts 
    
    # Start the Tkinter event loop, which waits for user interaction and updates the UI
    root.mainloop()