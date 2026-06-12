# 🖥️ AOC Display Control Panel

[![Python Version](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v1.1.0-orange.svg)](https://github.com/xToshiro/display-control/releases/tag/v1.1.0)

An optimized, lightweight, and modern alternative to the AOC I-Menu. This application provides a sleek side-by-side dark-mode control interface for managing image settings on dual AOC monitors using the VESA DDC/CI protocol.

---

## 🌟 Key Features

* **⚡ Zero-Lag Asynchronous Engine**: All hardware communications (reads and writes) are processed in sequential background worker threads. The GUI remains 100% fluid and responsive.
* **🖥️ Side-by-Side Dual-Monitor Panel**: View and control both displays independently side-by-side, identified by their correct model (`27B35H`) and serial numbers extracted directly from EDID metadata.
* **🔗 Dynamic Sync mode**: Bind parameters together so adjusting brightness or contrast on one monitor automatically mirrors it onto the other.
* **🎨 Low-Level Color Presets**: Supports raw VESA VCP Code `0x14` commands to instantly set monitor color temperatures:
  - `sRGB` (1)
  - `6500K` (5)
  - `7500K` (6)
  - `9300K` (8)
  - `User/Usuário` (11)
* **🌙 Global Profiles**: Apply pre-configured profile configurations (`Leitura`, `Trabalho`, `Jogos`, `Noite`) to both displays simultaneously.
* 📥 Minimize to System Tray: Closes directly to the system tray (pystray). Includes context menu presets so you can adjust your screens without even opening the main window.
* 🔒 Single Instance Protection: Prevents duplicate application windows from spawning. Re-running the application shortcut safely restores, lifts, and focuses the existing background process window.
* 📱 Dynamic Adapting Layout: Automatically adjusts the window width and columns dynamically depending on the number of connected monitors (works seamlessly for 1, 2, 3, or more displays).
* ⚙️ Start on Boot: A checkbox that creates a Windows registry key to automatically launch the application minimized on system startup.

---

## ⚙️ Hardware Prerequisites

To communicate with your monitors, please ensure:
1. **DDC/CI is Enabled** in the physical monitor's OSD (On-Screen Display) menu.
2. The displays are connected via modern video interfaces (**HDMI**, **DisplayPort**, or **USB-C**). VGA and older DVI connections do not support the protocol.

---

## 📦 Download the Executable

If you do not wish to run from source, you can download the compiled standalone executable:

👉 **[Download DisplayControl.exe (v1.1.0)](https://github.com/xToshiro/display-control/releases/download/v1.1.0/DisplayControl.exe)**

*(Built using PyInstaller with a custom icon, running silently without a console window).*

---

## 🚀 Running from Source

### 1. Requirements
Ensure you have **Python 3.14+** installed.

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/xToshiro/display-control.git
cd display-control

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch
```bash
python main.py
```
*To run the script in the background without launching a Command Prompt window, run with:*
```bash
pythonw.exe main.py
```

---

## 🛠️ Building Standalone Binary
To compile the source code into a standalone `.exe` executable file using PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="DisplayControl" --icon="app_icon.ico" main.py
```
The compiled file will be located inside the `dist/` directory.

---

## 📄 License
This project is licensed under the MIT License.
