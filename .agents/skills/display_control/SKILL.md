---
name: display-control
description: Guidelines and specifications for the AOC Display Control Panel project, including DDC/CI communication, layout rules, and PyInstaller compilation.
---

# AOC Display Control Panel Development Guide

This skill outlines the architectural rules, design constraints, and guidelines for maintaining and developing the AOC Display Control Panel.

## Project Overview
* **Description**: A lightweight, modern Python/CustomTkinter control panel to manage monitors using the VESA DDC/CI protocol on Windows.
* **Stack**: Python 3.14+, `customtkinter`, `monitorcontrol`, `screen_brightness_control`, `win32api`.

---

## Architectural Guidelines

### 1. DDC/CI Communication Threading
* **Worker Thread**: DDC/CI read/write hardware commands are slow and blocking. Always queue feature writes in `MonitorCommandWorker` to keep the UI fluid.
* **Timing constraints**: Maintain a write delay of `0.12s` (via `time.sleep(0.12)`) in the worker loop to avoid overloading the monitor's DDC controller.

### 2. VCP Codes and Control Parameters
* **Power Mode (`0xD6`)**: 
  * `1` = Power On
  * `4` = Standby / Power Save (recommended for turning off, since it preserves the controller's ability to receive the "Power On" command).
* **Color Preset (`0x14`)**: 
  * `1` = sRGB, `5` = 6500K, `6` = 7500K, `8` = 9300K, `11` = User.
* **Display Scaling (`0x86`)**: 
  * `1` = 1:1, `2` = Proportional (Aspect), `3` = Full.

### 3. Layout & Geometry Constraints
* **Geometry**: 
  * Height is fixed at `850px` to fit all control modules (Brightness, Contrast, Color, Scaling/Resolution, and Power controls) without clipping.
  * Width scales dynamically with the number of monitors: `window_width = max(680, 20 + num_monitors * 410)`.
* **DPI Scales**: Keep headers at a maximum of `16 bold` and dropdown widths at `120px` to prevent layout breakdown on High-DPI screens.

### 4. Compilation
* Use the following command to package the single-file executable:
  ```powershell
  .\venv\Scripts\pyinstaller --onefile --noconsole --name="DisplayControl" --icon="app_icon.ico" main.py
  ```
