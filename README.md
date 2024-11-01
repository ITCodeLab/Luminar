# Luminar 1.4

**Luminar** is a Python application that provides customizable screen brightness and image enhancement controls through an interactive GUI. Built with Tkinter and leveraging OpenCV for image processing, Luminar enables users to optimize visual settings for comfort and clarity.

## Features

- **Image Enhancement**: Adjust brightness, contrast, and apply filters to images.
- **Real-Time Adjustments**: Smooth, real-time updates using multithreading for fast, responsive controls.
- **Custom Fonts and UI**: Includes Italian and Istok fonts, with a dynamic, easy-to-navigate GUI.
- **Session Persistence**: Saves settings locally, restoring preferences on each launch.

## Installation

### Prerequisites

- **Python 3.8+**
- Required libraries (install with `pip`):
  
  ```bash
  pip install tkinter opencv-python-headless pillow numpy
  ```

### Fonts and Resources

Place the following font files in the specified directories:

- `Italiana/Italiana-Regular.ttf`
- `Istok/Istok-Regular.ttf`

### Running the Application

1. Clone or download this repository.
2. From the main project directory, run:

   ```bash
   python luminar.py
   ```

## File Structure

```plaintext
Luminar/
├── luminar.py               # Main application script
├── Italiana/              # Font directory for Italiana
│   └── Italiana-Regular.ttf
├── Istok/                 # Font directory for Istok
│   └── Istok-Regular.ttf
└── assets/                # (Optional) Add any required images or resources
```

## Usage

Launch the app to access a range of image adjustment tools, including real-time brightness and contrast settings. All user preferences are saved automatically.

## License

This project is licensed under the MIT License.
