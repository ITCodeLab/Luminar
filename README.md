# Luminar-1.2
## Overview

This application is a desktop tool designed to manage and optimize screen usage and brightness based on various user-defined profiles and real-time image processing. It leverages a combination of computer vision, image processing, and user interaction to enhance user comfort and productivity.

## Features

- **Image Processing**: Adjusts screen brightness based on the analysis of live images captured from the camera.
- **Profile Management**: Create, load, and delete user profiles with settings for brightness, color temperature, and break times.
- **Pomodoro Timer**: Implements the Pomodoro technique with automatic reminders for work and break intervals.
- **Health Monitoring**: Alerts users to take breaks after prolonged screen use.
- **Adaptive Color Temperature**: Adjusts the color temperature of the screen based on the time of day.
- **Manual Overrides**: Customizable settings for video conferences and energy-saving modes.

## Requirements

- Python 3.x
- `tkinter` for GUI
- `cv2` (OpenCV) for camera access
- `Pillow` for image processing
- `numpy` for numerical operations
- `subprocess` for system commands

## Installation

1. **Clone the Repository:**
   ```sh
   git clone https://github.com/yourusername/image-processor.git
   cd image-processor
   ```

2. **Install Dependencies:**
   ```sh
   pip install opencv-python pillow numpy
   ```

## Usage

1. **Run the Application:**
   ```sh
   python image_processor.py
   ```

2. **UI Components:**
   - **Start Button**: Begins image processing, health monitoring, and adaptive color temperature adjustments.
   - **Stop Button**: Stops all processes and logs the session's screen usage time.
   - **Settings Button**: Placeholder for future settings customization.
   - **Manage Profiles Button**: Opens a dialog to create, load, or delete user profiles.
   - **Start Pomodoro Button**: Initiates the Pomodoro timer for focused work sessions.
   - **Pomodoro Indicator**: Displays the status of the Pomodoro timer.
   - **Tree View**: Displays screen usage history with dates and duration.

3. **Profile Management:**
   - **Create Profile**: Define new profiles with specific brightness, color temperature, and break time settings.
   - **Load Profile**: Apply settings from the selected profile.
   - **Delete Profile**: Remove an existing profile.

## Configuration

Profiles are stored in `profiles.json`. Each profile includes:
- `brightness`: Desired screen brightness level (0-100).
- `color_temperature`: Screen color temperature in Kelvin.
- `break_time`: Recommended break time in minutes.

## Troubleshooting

- **Camera Access Issues**: Ensure that the camera is connected and accessible. The application may fail to open the camera if it's in use by another application or if permissions are restricted.
- **WMI Errors**: If you encounter errors related to WMI commands for brightness or color temperature adjustments, ensure that your system supports these features.

## Contribution

Feel free to contribute by opening issues or submitting pull requests. Your feedback and improvements are welcome!
