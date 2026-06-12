# Display Control Panel

An optimized, lightweight, and modern Python application to replace the AOC I-Menu. It provides a side-by-side graphical interface to control the image parameters (brightness, contrast, and color temperature presets) of dual monitors using the VESA DDC/CI protocol.

## Features

- **Asynchronous Execution**: All monitor read and write commands run in background worker threads, preventing GUI freezes.
- **Side-by-Side Control Layout**: Control two monitors independently from a single, clean CustomTkinter dark-mode panel.
- **Linked Adjustment (Sync)**: A toggle checkbox allows you to change parameters on both monitors simultaneously.
- **Color Presets**: Quick preset buttons for `sRGB`, `6500K`, `7500K`, `9300K`, and `User` mode (bypasses default library constraints to write low-level DDC/CI commands).
- **Quick Profiles**: Global profile presets (`Leitura`, `Trabalho`, `Jogos`, `Noite`) to adjust both monitors with a single click.
- **System Tray Integration**: Intercepts the window close action to minimize to the system tray (`pystray`). Includes quick presets right from the taskbar context menu.
- **Start on Boot**: A checkbox that configures a registry run key to automatically launch the application minimized on Windows startup.

## Technologies Used

- **Python 3.14+**
- **CustomTkinter** for the premium dark UI theme.
- **monitorcontrol** & **screen-brightness-control** for hardware enumeration and VESA DDC/CI commands.
- **pystray** & **Pillow** for the system tray loop and graphics.
- **PyInstaller** for standalone executable generation.

## How to Run

1. Clone this repository.
2. Initialize and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```
   *(To run without a console window in the background, use `pythonw.exe main.py`)*

## Standalone Executable

You can build a single-file standalone `.exe` using PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="DisplayControl" --icon="app_icon.ico" main.py
```
The compiled output will be generated inside the `dist/` directory.
