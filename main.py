import threading
import time
import queue
import winreg
import sys
import os
import socket
import json
import requests
import webbrowser
import ctypes
import locale
from tkinter import messagebox
import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
import screen_brightness_control as sbc
from monitorcontrol import get_monitors
import win32api
import win32con

VERSION = "v1.2.0"

TRANSLATIONS = {
    "pt": {
        "title": "Painel de Controle de Monitores",
        "tab_monitors": "Monitores",
        "tab_about": "Sobre",
        "start_with_windows": "Iniciar com Windows",
        "startup_profile": "Perfil Inicial:",
        "sync": "Sincronizar",
        "brightness": "Brilho: {}%",
        "contrast": "Contraste: {}%",
        "color": "Cor",
        "resolution": "Resolução",
        "screen_ratio": "Tela:",
        "system_res": "Sistema:",
        "standard_presets": "Perfis Padrão (Ambos):",
        "custom_presets": "Perfis Personalizados:",
        "save_current": "Salvar Atual",
        "delete": "Excluir",
        "reload": "Recarregar",
        "loading": "Procurando monitores DDC/CI...\nIsso pode levar alguns segundos.",
        "none_found": "Nenhum Monitor DDC/CI Encontrado",
        "check_updates": "Verificar Atualização",
        "no_updates": "Você está na versão mais recente!",
        "update_available": "Nova versão disponível: {}!",
        "error_checking_updates": "Erro ao verificar atualizações.",
        "creator": "Criador:",
        "repo": "Repositório:",
        "version": "Versão:",
        "select_lang": "Idioma:",
        "checking_updates": "Verificando...",
        "update_btn": "Baixar Atualização",
        "user_color": "Usuário",
        "none_option": "Nenhum",
        "presets": {
            "Leitura": "Leitura",
            "Trabalho": "Trabalho",
            "Jogos": "Jogos",
            "Noite": "Noite"
        },
        "dialog_save_title": "Salvar Perfil",
        "dialog_save_text": "Digite o nome para o perfil personalizado:",
        "dialog_save_invalid_title": "Nome Inválido",
        "dialog_save_invalid_text": "Este nome de perfil é reservado pelo sistema. Escolha outro nome.",
        "dialog_delete_title": "Confirmar Exclusão",
        "dialog_delete_text": "Tem certeza que deseja excluir o perfil '{}'?",
        "instructions": (
            "DDC/CI é o protocolo que permite ajustar brilho/contraste pelo PC.\n\n"
            "Verificações recomendadas:\n"
            "1. Habilite o suporte a DDC/CI nas configurações físicas do monitor (menu OSD).\n"
            "2. Certifique-se de que os monitores estão conectados por HDMI, DisplayPort ou USB-C.\n"
            "3. Reinicie este aplicativo e tente recarregar."
        ),
        "tray_open": "Abrir Painel",
        "tray_profile": "Perfil",
        "tray_quit": "Sair",
        "status_preset_applied": "Perfil '{}' aplicado.",
        "status_startup_preset_changed": "Perfil inicial alterado para '{}'.",
        "status_ready": "Pronto",
        "status_scanning": "Buscando...",
        "status_minimized": "Minimizado na bandeja de sistema.",
        "status_preset_saved": "Perfil '{}' salvo com sucesso.",
        "status_preset_deleted": "Perfil '{}' excluído.",
        "status_res_changed": "Resolução do Monitor {} alterada para {}.",
        "status_res_error_title": "Erro de Resolução",
        "status_res_error_text": "Não foi possível alterar a resolução do monitor para {}. Código: {}"
    },
    "en": {
        "title": "Monitor Control Panel",
        "tab_monitors": "Monitors",
        "tab_about": "About",
        "start_with_windows": "Start with Windows",
        "startup_profile": "Startup Profile:",
        "sync": "Synchronize",
        "brightness": "Brightness: {}%",
        "contrast": "Contrast: {}%",
        "color": "Color",
        "resolution": "Resolution",
        "screen_ratio": "Screen:",
        "system_res": "System:",
        "standard_presets": "Standard Profiles (Both):",
        "custom_presets": "Custom Profiles:",
        "save_current": "Save Current",
        "delete": "Delete",
        "reload": "Reload",
        "loading": "Scanning for DDC/CI monitors...\nThis may take a few seconds.",
        "none_found": "No DDC/CI Monitors Found",
        "check_updates": "Check for Updates",
        "no_updates": "You are on the latest version!",
        "update_available": "New version available: {}!",
        "error_checking_updates": "Error checking for updates.",
        "creator": "Creator:",
        "repo": "Repository:",
        "version": "Version:",
        "select_lang": "Language:",
        "checking_updates": "Checking...",
        "update_btn": "Download Update",
        "user_color": "User",
        "none_option": "None",
        "presets": {
            "Leitura": "Reading",
            "Trabalho": "Work",
            "Jogos": "Gaming",
            "Noite": "Night"
        },
        "dialog_save_title": "Save Profile",
        "dialog_save_text": "Enter name for the new custom profile:",
        "dialog_save_invalid_title": "Invalid Name",
        "dialog_save_invalid_text": "This profile name is reserved by the system. Please choose another name.",
        "dialog_delete_title": "Confirm Delete",
        "dialog_delete_text": "Are you sure you want to delete profile '{}'?",
        "instructions": (
            "DDC/CI is the protocol that allows PC control of brightness/contrast.\n\n"
            "Recommended checks:\n"
            "1. Enable DDC/CI support in your physical monitor's OSD menu.\n"
            "2. Ensure monitors are connected via HDMI, DisplayPort, or USB-C.\n"
            "3. Restart this app and try reloading."
        ),
        "tray_open": "Open Panel",
        "tray_profile": "Profile",
        "tray_quit": "Exit",
        "status_preset_applied": "Profile '{}' applied.",
        "status_startup_preset_changed": "Startup profile changed to '{}'.",
        "status_ready": "Ready",
        "status_scanning": "Scanning...",
        "status_minimized": "Minimized to system tray.",
        "status_preset_saved": "Profile '{}' saved successfully.",
        "status_preset_deleted": "Profile '{}' deleted.",
        "status_res_changed": "Monitor {} resolution changed to {}.",
        "status_res_error_title": "Resolution Error",
        "status_res_error_text": "Could not change monitor resolution to {}. Code: {}"
    }
}

def get_system_lang():
    try:
        # Get user default UI language from Windows
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        # Primary language identifier (lower 10 bits)
        prim_lang = lang_id & 0x3ff
        # 0x09 is English (LANG_ENGLISH)
        if prim_lang == 0x09:
            return "en"
    except Exception:
        pass
    try:
        # Fallback to locale
        loc = locale.getlocale()[0]
        if loc and loc.lower().startswith("en"):
            return "en"
    except Exception:
        pass
    return "pt"

SINGLE_INSTANCE_PORT = 28935

def check_single_instance():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
        return s
    except socket.error:
        # Another instance is already running
        try:
            s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s2.sendto(b"show", ('127.0.0.1', SINGLE_INSTANCE_PORT))
            s2.close()
        except Exception:
            pass
        sys.exit(0)

# Standard Preset Configurations (Brightness, Contrast)
PRESETS = {
    "Leitura": (15, 45),
    "Trabalho": (45, 50),
    "Jogos": (75, 60),
    "Noite": (5, 35)
}

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DisplayControl"

CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DisplayControl")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

SCALING_MAP = {"Inteiro": 3, "Proporcional": 2, "1:1": 1}
REVERSE_SCALING_MAP = {3: "Inteiro", 2: "Proporcional", 1: "1:1"}

def get_registry_monitor_uids():
    mapping = {}
    try:
        display_root = "SYSTEM\\CurrentControlSet\\Enum\\DISPLAY"
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, display_root, 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                model = winreg.EnumKey(key, i)
                model_key = winreg.OpenKey(key, model, 0, winreg.KEY_READ)
                j = 0
                while True:
                    try:
                        instance = winreg.EnumKey(model_key, j)
                        instance_key = winreg.OpenKey(model_key, instance, 0, winreg.KEY_READ)
                        try:
                            driver, _ = winreg.QueryValueEx(instance_key, "Driver")
                            if "UID" in instance:
                                uid_str = instance.split("UID")[-1]
                                uid = int(uid_str)
                                mapping[driver.lower()] = uid
                        except Exception:
                            pass
                        winreg.CloseKey(instance_key)
                        j += 1
                    except Exception:
                        break
                winreg.CloseKey(model_key)
                i += 1
            except Exception:
                break
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Registry error mapping UIDs: {e}")
    return mapping

def get_monitor_name_from_edid(edid_hex):
    try:
        edid_bytes = bytes.fromhex(edid_hex)
        for offset in (54, 72, 90, 108):
            block = edid_bytes[offset:offset+18]
            if block[0:5] == b'\x00\x00\x00\xfc\x00':
                name_bytes = block[5:]
                name = name_bytes.split(b'\n')[0].split(b'\x00')[0].decode('ascii', errors='ignore').strip()
                if name:
                    return name
    except Exception:
        pass
    return "Generic Monitor"

def set_run_on_startup(enabled):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            script_path = os.path.abspath(sys.argv[0])
            if script_path.endswith('.py'):
                pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
                cmd = f'"{pythonw_path}" "{script_path}" --minimized'
            else:
                cmd = f'"{script_path}" --minimized'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)

def is_run_on_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False

def create_app_icon():
    image = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Stylized Monitor Outer Frame (Sleek Blue border, dark blue interior)
    draw.rounded_rectangle((8, 12, 56, 44), radius=5, fill=(15, 23, 42), outline=(14, 165, 233), width=2)
    # Monitor stand
    draw.polygon([(26, 44), (38, 44), (44, 54), (20, 54)], fill=(100, 116, 139))
    
    # Graphic representation of brightness adjustment (slider bar + slider handle)
    draw.rounded_rectangle((16, 26, 48, 30), radius=2, fill=(30, 41, 59))
    draw.ellipse((28, 24, 36, 32), fill=(14, 165, 233))
    
    return image


class MonitorManager:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.monitors_info = []
        self.monitors_mc = []
        self.refresh_lock = threading.Lock()

    def log_status(self, message):
        if self.status_callback:
            self.status_callback(message)
        else:
            print(message)

    def scan_monitors(self):
        with self.refresh_lock:
            self.log_status("Buscando monitores...")
            self.monitors_info = []
            
            # 1. Fetch registry UID mapping
            reg_mapping = get_registry_monitor_uids()
            
            # 2. Map GDI devices to UIDs
            gdi_to_uid = {}
            device_index = 0
            while True:
                try:
                    device = win32api.EnumDisplayDevices(None, device_index)
                    if device.StateFlags & win32con.DISPLAY_DEVICE_ATTACHED_TO_DESKTOP:
                        mon_idx = 0
                        while True:
                            try:
                                monitor = win32api.EnumDisplayDevices(device.DeviceName, mon_idx)
                                parts = monitor.DeviceID.split("\\")
                                if len(parts) >= 4:
                                    driver_key = f"{parts[2]}\\{parts[3]}"
                                    uid = reg_mapping.get(driver_key.lower())
                                    if uid is not None:
                                        gdi_to_uid[device.DeviceName] = uid
                                mon_idx += 1
                            except Exception:
                                break
                    device_index += 1
                except Exception:
                    break

            # 3. Fetch info using screen-brightness-control (includes EDID and Serials)
            try:
                sbc_list = sbc.list_monitors_info()
            except Exception as e:
                print(f"Error in sbc: {e}")
                sbc_list = []

            # 4. Fetch monitor objects using monitorcontrol
            try:
                mc_list = get_monitors()
            except Exception as e:
                print(f"Error in monitorcontrol: {e}")
                mc_list = []

            self.monitors_mc = mc_list

            # 5. Match them up
            for idx, mc_mon in enumerate(mc_list):
                sbc_data = None
                if idx < len(sbc_list):
                    sbc_data = sbc_list[idx]

                model = "Generic Monitor"
                serial = "Unknown"
                if sbc_data:
                    serial = sbc_data.get("serial", "Unknown")
                    edid_hex = sbc_data.get("edid", "")
                    if edid_hex:
                        model = get_monitor_name_from_edid(edid_hex)
                    else:
                        model = sbc_data.get("model", "Generic Monitor")
                
                # Fetch current levels safely
                brightness = 50
                contrast = 50
                color_preset = 5  # Default to 6500K (5)
                display_scaling = 2  # Default to Proportional
                
                try:
                    with mc_mon:
                        brightness = mc_mon.get_luminance()
                except Exception as e:
                    print(f"Error getting brightness for Monitor {idx+1}: {e}")

                try:
                    with mc_mon:
                        contrast = mc_mon.get_contrast()
                except Exception as e:
                    print(f"Error getting contrast for Monitor {idx+1}: {e}")

                try:
                    with mc_mon:
                        color_preset, _ = mc_mon.vcp.get_vcp_feature(0x14)
                except Exception as e:
                    print(f"Error getting color preset for Monitor {idx+1}: {e}")

                try:
                    with mc_mon:
                        display_scaling, _ = mc_mon.vcp.get_vcp_feature(0x86)
                except Exception as e:
                    print(f"Error getting display scaling for Monitor {idx+1}: {e}")

                # Match to GDI device
                gdi_device = None
                current_resolution = None
                resolutions_list = []
                modes_dict = {}
                
                if sbc_data:
                    sbc_uid = sbc_data.get("uid")
                    if sbc_uid is not None:
                        for dev, dev_uid in gdi_to_uid.items():
                            if str(dev_uid) == str(sbc_uid):
                                gdi_device = dev
                                break
                                
                if gdi_device:
                    try:
                        # Get current settings
                        current = win32api.EnumDisplaySettings(gdi_device, win32con.ENUM_CURRENT_SETTINGS)
                        current_resolution = f"{current.PelsWidth}x{current.PelsHeight}-{current.DisplayFrequency}Hz"
                        
                        # Get all unique modes
                        m_idx = 0
                        while True:
                            try:
                                m = win32api.EnumDisplaySettings(gdi_device, m_idx)
                                key = f"{m.PelsWidth}x{m.PelsHeight}-{m.DisplayFrequency}Hz"
                                modes_dict[key] = m
                                m_idx += 1
                            except Exception:
                                break
                        
                        sorted_keys = sorted(
                            list(modes_dict.keys()), 
                            key=lambda x: [int(v) for v in x.replace("x", "-").replace("Hz", "").split("-")], 
                            reverse=True
                        )
                        resolutions_list = sorted_keys
                    except Exception as e:
                        print(f"Error enumerating settings for display {gdi_device}: {e}")

                self.monitors_info.append({
                    "index": idx,
                    "model": model,
                    "serial": serial,
                    "brightness": brightness,
                    "contrast": contrast,
                    "color_preset": color_preset,
                    "display_scaling": display_scaling,
                    "device_name": gdi_device,
                    "current_resolution": current_resolution,
                    "resolutions_list": resolutions_list,
                    "modes_dict": modes_dict,
                    "object": mc_mon
                })

            self.log_status(f"Busca finalizada. Encontrados {len(self.monitors_info)} monitor(es).")
            return self.monitors_info


class MonitorCommandWorker:
    def __init__(self, manager):
        self.manager = manager
        self.pending_tasks = {}  # key: (monitor_index, feature), value: target_value
        self.lock = threading.Lock()
        self.cond = threading.Condition(self.lock)
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()

    def set_value(self, monitor_index, feature, value):
        with self.lock:
            self.pending_tasks[(monitor_index, feature)] = value
            self.cond.notify()

    def _worker_loop(self):
        while True:
            task = None
            with self.lock:
                while not self.pending_tasks:
                    self.cond.wait()
                # Get the first task and remove it
                key = next(iter(self.pending_tasks))
                val = self.pending_tasks.pop(key)
                monitor_idx, feature = key

            # Apply change to monitor
            try:
                monitors = self.manager.monitors_info
                if monitor_idx < len(monitors):
                    mon_obj = monitors[monitor_idx]["object"]
                    
                    # Log activity
                    label = f"{val}%"
                    if feature == "color_preset":
                        label = {1: "sRGB", 5: "6500K", 6: "7500K", 8: "9300K", 11: "Usuário"}.get(val, "Usuário")
                    elif feature == "display_scaling":
                        label = {1: "1:1", 2: "Proporcional", 3: "Inteiro"}.get(val, "Proporcional")
                    
                    self.manager.log_status(f"Ajustando {feature} do Monitor {monitor_idx+1} para {label}...")
                    
                    with mon_obj:
                        if feature == "brightness":
                            mon_obj.set_luminance(val)
                            monitors[monitor_idx]["brightness"] = val
                        elif feature == "contrast":
                            mon_obj.set_contrast(val)
                            monitors[monitor_idx]["contrast"] = val
                        elif feature == "color_preset":
                            mon_obj.vcp.set_vcp_feature(0x14, val)
                            monitors[monitor_idx]["color_preset"] = val
                        elif feature == "display_scaling":
                            mon_obj.vcp.set_vcp_feature(0x86, val)
                            monitors[monitor_idx]["display_scaling"] = val
                            
                    self.manager.log_status("Pronto")
            except Exception as e:
                self.manager.log_status(f"Erro ao atualizar monitor: {e}")
                print(f"Error writing feature {feature} to monitor {monitor_idx}: {e}")

            time.sleep(0.12)  # Prevent overloading DDC/CI communications


class DisplayControlApp(ctk.CTk):
    def translate(self, key):
        keys = key.split(".")
        val = TRANSLATIONS.get(self.lang, TRANSLATIONS["pt"])
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, k)
            else:
                return key
        return val

    def ui_to_preset_key(self, ui_name):
        if ui_name == self.translate("none_option"):
            return "Nenhum"
        for k in PRESETS.keys():
            if ui_name == self.translate(f"presets.{k}"):
                return k
        return ui_name

    def preset_key_to_ui(self, key):
        if key == "Nenhum":
            return self.translate("none_option")
        if key in PRESETS:
            return self.translate(f"presets.{key}")
        return key

    def get_scaling_label(self, val):
        if self.lang == "en":
            mapping = {3: "Full", 2: "Aspect", 1: "1:1"}
        else:
            mapping = {3: "Inteiro", 2: "Proporcional", 1: "1:1"}
        return mapping.get(val, "Aspect" if self.lang == "en" else "Proporcional")

    def __init__(self, bound_socket):
        super().__init__()
        
        # Start single instance listener
        self.start_single_instance_listener(bound_socket)

        # Check if starting minimized
        if "--minimized" in sys.argv:
            self.withdraw()

        # Load configuration
        self.load_config()
        self.lang = self.config.get("language", "pt")

        self.is_first_scan = True

        # Window Config
        self.title(self.translate("title"))
        self.geometry("800x730")
        self.resizable(False, False)
        
        # UI Styling options
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Apply custom window icon
        self.icon_image = create_app_icon()
        self.icon_photo = ctk.CTkImage(light_image=self.icon_image, dark_image=self.icon_image, size=(32, 32))
        
        # Initialize Logic Components
        self.manager = MonitorManager(status_callback=self.update_status_bar)
        self.worker = MonitorCommandWorker(self.manager)
        
        self.monitors = []
        self.sync_enabled = False
        self.slider_vars = {}  # maps (index, feature) -> ctk.IntVar/DoubleVar
        self.color_buttons = {}  # maps (index, color_val) -> ctk.CTkButton
        
        # Intercept window closing
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)

        # Build GUI Base Shell
        self.build_gui()

        # Start Tray in Background
        self.tray_icon = None
        self.start_tray()

        # Run Scan in Background Thread to prevent initial UI lockup
        self.initial_scan()

    def update_status_bar(self, message):
        if hasattr(self, 'status_label'):
            # Must modify label in Tkinter thread safely
            self.after(0, lambda: self.status_label.configure(text=message))

    def build_gui(self):
        # Configure layout weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Header Frame ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        
        # Icon representation next to title
        self.icon_label = ctk.CTkLabel(self.header_frame, image=self.icon_photo, text="")
        self.icon_label.pack(side="left", padx=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text=self.translate("title"), 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(side="left")

        # Global Control Box / Checkboxes at top right
        self.top_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.top_controls.pack(side="right")

        self.startup_check = ctk.CTkCheckBox(
            self.top_controls, 
            text=self.translate("start_with_windows"), 
            command=self.toggle_startup,
            font=ctk.CTkFont(size=12)
        )
        self.startup_check.pack(side="left", padx=10)
        if is_run_on_startup():
            self.startup_check.select()

        # Startup Preset Dropdown in top right
        self.startup_preset_container = ctk.CTkFrame(self.top_controls, fg_color="transparent")
        self.startup_preset_container.pack(side="left", padx=10)
        
        self.lbl_start_pres = ctk.CTkLabel(self.startup_preset_container, text=self.translate("startup_profile"), font=ctk.CTkFont(size=12))
        self.lbl_start_pres.pack(side="left", padx=(0, 5))
        
        self.startup_preset_var = ctk.StringVar(value=self.translate("none_option"))
        self.startup_preset_menu = ctk.CTkOptionMenu(
            self.startup_preset_container,
            variable=self.startup_preset_var,
            values=[self.translate("none_option")],
            width=120,
            height=24,
            font=ctk.CTkFont(size=11),
            command=self.on_startup_preset_changed
        )
        self.startup_preset_menu.pack(side="left")

        self.sync_check = ctk.CTkCheckBox(
            self.top_controls, 
            text=self.translate("sync"), 
            command=self.toggle_sync,
            font=ctk.CTkFont(size=12)
        )

        # --- Content Frame (Contains monitors or loading indicator) ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        
        # Create TabView inside content_frame
        self.tabview = ctk.CTkTabview(self.content_frame, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True)

        self.tab_monitors = self.tabview.add(self.translate("tab_monitors"))
        self.tab_about = self.tabview.add(self.translate("tab_about"))
        
        # Build static about tab content
        self.build_about_tab()
        
        # --- Bottom Status Bar Frame ---
        self.bottom_frame = ctk.CTkFrame(self, height=35, corner_radius=0)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        self.status_label = ctk.CTkLabel(
            self.bottom_frame, 
            text=self.translate("loading"), 
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=15, pady=5)

        self.refresh_btn = ctk.CTkButton(
            self.bottom_frame, 
            text=self.translate("reload"), 
            width=80, 
            height=24,
            command=self.trigger_scan,
            font=ctk.CTkFont(size=11)
        )
        self.refresh_btn.pack(side="right", padx=15, pady=5)

    def build_about_tab(self):
        tab = self.tab_about
        for widget in tab.winfo_children():
            widget.destroy()
            
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        about_card = ctk.CTkFrame(tab, fg_color="#0F172A", border_color="#1E293B", border_width=1)
        about_card.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        about_card.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            about_card, 
            text="AOC Display Control Panel", 
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#0EA5E9"
        )
        title.pack(pady=(20, 5))
        
        desc = ctk.CTkLabel(
            about_card, 
            text="Alternativa leve e moderna ao AOC I-Menu." if self.lang == "pt" else "A lightweight, modern alternative to AOC I-Menu.",
            font=ctk.CTkFont(size=12)
        )
        desc.pack(pady=(0, 15))
        
        info_frame = ctk.CTkFrame(about_card, fg_color="transparent")
        info_frame.pack(pady=10, padx=20)
        info_frame.grid_columnconfigure(0, weight=0)
        info_frame.grid_columnconfigure(1, weight=1)
        
        lbl_ver_name = ctk.CTkLabel(info_frame, text=self.translate("version"), font=ctk.CTkFont(size=11, weight="bold"), anchor="w", width=90)
        lbl_ver_name.grid(row=0, column=0, sticky="w", pady=4)
        lbl_ver_val = ctk.CTkLabel(info_frame, text=VERSION, font=ctk.CTkFont(size=11), anchor="w")
        lbl_ver_val.grid(row=0, column=1, sticky="w", pady=4)
        
        lbl_creator_name = ctk.CTkLabel(info_frame, text=self.translate("creator"), font=ctk.CTkFont(size=11, weight="bold"), anchor="w", width=90)
        lbl_creator_name.grid(row=1, column=0, sticky="w", pady=4)
        lbl_creator_val = ctk.CTkLabel(info_frame, text="xToshiro", font=ctk.CTkFont(size=11), anchor="w")
        lbl_creator_val.grid(row=1, column=1, sticky="w", pady=4)
        
        lbl_repo_name = ctk.CTkLabel(info_frame, text=self.translate("repo"), font=ctk.CTkFont(size=11, weight="bold"), anchor="w", width=90)
        lbl_repo_name.grid(row=2, column=0, sticky="w", pady=4)
        
        btn_repo = ctk.CTkButton(
            info_frame,
            text="github.com/xToshiro/display-control",
            font=ctk.CTkFont(size=11, underline=True),
            text_color="#38BDF8",
            fg_color="transparent",
            hover_color="#1E293B",
            width=200,
            anchor="w",
            height=20,
            command=lambda: webbrowser.open_new_tab("https://github.com/xToshiro/display-control")
        )
        btn_repo.grid(row=2, column=1, sticky="w", pady=4)
        
        lbl_lang_name = ctk.CTkLabel(info_frame, text=self.translate("select_lang"), font=ctk.CTkFont(size=11, weight="bold"), anchor="w", width=90)
        lbl_lang_name.grid(row=3, column=0, sticky="w", pady=4)
        
        lang_var = ctk.StringVar(value="Português (BR)" if self.lang == "pt" else "English")
        lang_menu = ctk.CTkOptionMenu(
            info_frame,
            variable=lang_var,
            values=["Português (BR)", "English"],
            width=140,
            height=24,
            font=ctk.CTkFont(size=11),
            command=self.on_language_selector_changed
        )
        lang_menu.grid(row=3, column=1, sticky="w", pady=4)
        
        sep = ctk.CTkFrame(about_card, height=1, fg_color="#1E293B")
        sep.pack(fill="x", padx=30, pady=15)
        
        update_container = ctk.CTkFrame(about_card, fg_color="transparent")
        update_container.pack(fill="x", padx=30, pady=(0, 20))
        
        self.update_status_label = ctk.CTkLabel(
            update_container,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.update_status_label.pack(pady=(0, 10))
        
        self.check_updates_btn = ctk.CTkButton(
            update_container,
            text=self.translate("check_updates"),
            width=150,
            height=28,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.trigger_update_check
        )
        self.check_updates_btn.pack()
        
        self.download_update_btn = ctk.CTkButton(
            update_container,
            text=self.translate("update_btn"),
            width=150,
            height=28,
            fg_color="#10B981",
            hover_color="#059669",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.open_download_url
        )
        self.download_url = None

    def on_language_selector_changed(self, selected_label):
        new_lang = "pt" if selected_label == "Português (BR)" else "en"
        if new_lang != self.lang:
            self.lang = new_lang
            self.config["language"] = new_lang
            self.save_config()
            self.after(50, self.apply_translations)

    def check_for_updates(self):
        def parse_version(v_str):
            try:
                return tuple(int(x) for x in v_str.lstrip('v').split('.'))
            except Exception:
                return (0, 0, 0)
        try:
            r = requests.get("https://api.github.com/repos/xToshiro/display-control/releases/latest", timeout=5)
            if r.status_code == 200:
                data = r.json()
                latest_version = data.get("tag_name", VERSION)
                html_url = data.get("html_url", "https://github.com/xToshiro/display-control/releases")
                
                if parse_version(latest_version) > parse_version(VERSION):
                    return latest_version, html_url
                else:
                    return None, None
            else:
                return False, None
        except Exception:
            return False, None

    def trigger_update_check(self):
        self.update_status_label.configure(text=self.translate("checking_updates"), text_color="gray")
        self.check_updates_btn.configure(state="disabled")
        self.download_update_btn.pack_forget()
        threading.Thread(target=self._update_check_thread, daemon=True).start()

    def _update_check_thread(self):
        latest_version, html_url = self.check_for_updates()
        self.after(0, lambda: self.on_update_check_finished(latest_version, html_url))

    def on_update_check_finished(self, latest_version, html_url):
        self.check_updates_btn.configure(state="normal")
        if latest_version is False:
            self.update_status_label.configure(text=self.translate("error_checking_updates"), text_color="#FF6666")
        elif latest_version is None:
            self.update_status_label.configure(text=self.translate("no_updates"), text_color="gray")
        else:
            self.update_status_label.configure(
                text=self.translate("update_available").format(latest_version),
                text_color="#10B981"
            )
            self.download_url = html_url
            self.download_update_btn.pack(pady=10)

    def open_download_url(self):
        if self.download_url:
            webbrowser.open_new_tab(self.download_url)
        else:
            webbrowser.open_new_tab("https://github.com/xToshiro/display-control/releases")

    def apply_translations(self):
        self.title(self.translate("title"))
        self.title_label.configure(text=self.translate("title"))
        self.startup_check.configure(text=self.translate("start_with_windows"))
        self.lbl_start_pres.configure(text=self.translate("startup_profile"))
        self.sync_check.configure(text=self.translate("sync"))
        self.refresh_btn.configure(text=self.translate("reload"))
        
        self.recreate_tabview()
        self.update_tray_menu()

    def recreate_tabview(self):
        selected_tab = None
        try:
            if hasattr(self, 'tabview'):
                selected_tab = self.tabview.get()
        except Exception:
            pass

        if hasattr(self, 'tabview'):
            self.tabview.destroy()
            
        self.tabview = ctk.CTkTabview(self.content_frame, fg_color="transparent")
        self.tabview.pack(fill="both", expand=True)

        tab_monitors_name = self.translate("tab_monitors")
        tab_about_name = self.translate("tab_about")

        self.tab_monitors = self.tabview.add(tab_monitors_name)
        self.tab_about = self.tabview.add(tab_about_name)
        
        self.build_about_tab()
        
        if self.monitors:
            self.render_monitors_ui()
        else:
            if self.refresh_btn.cget("state") == "disabled":
                self.show_loading()
            else:
                self.show_error("Nenhum monitor DDC/CI compatível encontrado.")

        if selected_tab:
            is_monitors_tab = selected_tab in ["Monitores", "Monitors"]
            is_about_tab = selected_tab in ["Sobre", "About"]
            try:
                if is_monitors_tab:
                    self.tabview.set(tab_monitors_name)
                elif is_about_tab:
                    self.tabview.set(tab_about_name)
            except Exception:
                pass

    def show_loading(self):
        # Clear tab_monitors frame
        for widget in self.tab_monitors.winfo_children():
            widget.destroy()
            
        self.tab_monitors.grid_rowconfigure(0, weight=1)
        self.tab_monitors.grid_columnconfigure(0, weight=1)
            
        self.loading_label = ctk.CTkLabel(
            self.tab_monitors, 
            text=self.translate("loading"), 
            font=ctk.CTkFont(size=16)
        )
        self.loading_label.grid(row=0, column=0)
        self.refresh_btn.configure(state="disabled")

    def show_error(self, message):
        for widget in self.tab_monitors.winfo_children():
            widget.destroy()

        self.tab_monitors.grid_rowconfigure(0, weight=1)
        self.tab_monitors.grid_columnconfigure(0, weight=1)

        error_box = ctk.CTkFrame(self.tab_monitors, fg_color="#331A1A", border_color="#FF4D4D", border_width=1)
        error_box.grid(row=0, column=0, padx=40, pady=20, sticky="nsew")
        
        err_title = ctk.CTkLabel(
            error_box, 
            text=self.translate("none_found"), 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF6666"
        )
        err_title.pack(pady=(20, 10))
        
        err_desc = ctk.CTkLabel(
            error_box, 
            text=self.translate("instructions"), 
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        err_desc.pack(pady=10, padx=20)
        
        self.refresh_btn.configure(state="normal")

    def initial_scan(self):
        self.show_loading()
        threading.Thread(target=self._scan_thread_worker, daemon=True).start()

    def trigger_scan(self):
        self.show_loading()
        threading.Thread(target=self._scan_thread_worker, daemon=True).start()

    def _scan_thread_worker(self):
        self.monitors = self.manager.scan_monitors()
        if self.is_first_scan:
            self.is_first_scan = False
            self.apply_startup_preset_if_needed()
        self.after(0, self.render_monitors_ui)

    def render_monitors_ui(self):
        # Clear loading widgets in tab_monitors
        for widget in self.tab_monitors.winfo_children():
            widget.destroy()

        self.refresh_btn.configure(state="normal")

        if not self.monitors:
            self.show_error("Nenhum monitor DDC/CI compatível encontrado.")
            return

        # Adjust window width dynamically based on monitor count
        num_monitors = len(self.monitors)
        window_width = max(680, 20 + num_monitors * 410)
        self.geometry(f"{window_width}x730")

        # Dynamically handle sync monitors checkbox
        if num_monitors > 1:
            self.sync_check.pack(side="left", padx=10)
        else:
            self.sync_check.pack_forget()

        # Configure columns and rows inside the Monitors tab frame
        self.tab_monitors.grid_rowconfigure(0, weight=1)
        self.tab_monitors.grid_rowconfigure(1, weight=0)
        for col_idx in range(num_monitors):
            self.tab_monitors.grid_columnconfigure(col_idx, weight=1)

        # Loop through found monitors and build their sliders inside self.tab_monitors
        for i, mon in enumerate(self.monitors):
            idx = mon["index"]
            col_frame = ctk.CTkFrame(self.tab_monitors, border_color="#1E293B", border_width=1, fg_color="#0F172A")
            col_frame.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
            
            # Header of column
            header = ctk.CTkLabel(
                col_frame, 
                text=f"AOC {mon['model']}", 
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#0EA5E9"
            )
            header.pack(pady=(12, 2))
            
            serial = ctk.CTkLabel(
                col_frame, 
                text=f"S/N: {mon['serial']}", 
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            serial.pack(pady=(0, 8))

            # Separator line
            sep = ctk.CTkFrame(col_frame, height=1, fg_color="#1E293B")
            sep.pack(fill="x", padx=15, pady=5)

            # Brightness Controls
            b_label_var = ctk.StringVar(value=self.translate("brightness").format(mon['brightness']))
            self.slider_vars[(idx, "brightness")] = b_label_var
            
            b_text_label = ctk.CTkLabel(col_frame, textvariable=b_label_var, font=ctk.CTkFont(size=13, weight="bold"))
            b_text_label.pack(anchor="w", padx=15, pady=(5, 0))

            b_slider_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            b_slider_frame.pack(fill="x", padx=15, pady=5)

            b_slider = ctk.CTkSlider(
                b_slider_frame, 
                from_=0, 
                to=100, 
                number_of_steps=100,
                command=lambda val, idx=idx: self.slider_changed(idx, "brightness", int(val))
            )
            b_slider.set(mon['brightness'])
            b_slider.pack(side="left", fill="x", expand=True)
            # Store slider widget to allow external sets (e.g. during sync)
            self.slider_vars[(idx, "brightness_slider")] = b_slider

            # Brightness adjustment buttons
            b_btn_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            b_btn_frame.pack(fill="x", padx=15, pady=(0, 8))
            
            ctk.CTkButton(b_btn_frame, text="-5", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=b_slider: self.adjust_step(idx, "brightness", s, -5)).pack(side="left", padx=2)
            ctk.CTkButton(b_btn_frame, text="-1", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=b_slider: self.adjust_step(idx, "brightness", s, -1)).pack(side="left", padx=2)
            ctk.CTkButton(b_btn_frame, text="+1", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=b_slider: self.adjust_step(idx, "brightness", s, 1)).pack(side="right", padx=2)
            ctk.CTkButton(b_btn_frame, text="+5", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=b_slider: self.adjust_step(idx, "brightness", s, 5)).pack(side="right", padx=2)

            # Contrast Controls
            c_label_var = ctk.StringVar(value=self.translate("contrast").format(mon['contrast']))
            self.slider_vars[(idx, "contrast")] = c_label_var
            
            c_text_label = ctk.CTkLabel(col_frame, textvariable=c_label_var, font=ctk.CTkFont(size=13, weight="bold"))
            c_text_label.pack(anchor="w", padx=15, pady=(5, 0))

            c_slider_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            c_slider_frame.pack(fill="x", padx=15, pady=5)

            c_slider = ctk.CTkSlider(
                c_slider_frame, 
                from_=0, 
                to=100, 
                number_of_steps=100,
                command=lambda val, idx=idx: self.slider_changed(idx, "contrast", int(val))
            )
            c_slider.set(mon['contrast'])
            c_slider.pack(side="left", fill="x", expand=True)
            self.slider_vars[(idx, "contrast_slider")] = c_slider

            # Contrast adjustment buttons
            c_btn_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            c_btn_frame.pack(fill="x", padx=15, pady=(0, 12))
            
            ctk.CTkButton(c_btn_frame, text="-5", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=c_slider: self.adjust_step(idx, "contrast", s, -5)).pack(side="left", padx=2)
            ctk.CTkButton(c_btn_frame, text="-1", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=c_slider: self.adjust_step(idx, "contrast", s, -1)).pack(side="left", padx=2)
            ctk.CTkButton(c_btn_frame, text="+1", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=c_slider: self.adjust_step(idx, "contrast", s, 1)).pack(side="right", padx=2)
            ctk.CTkButton(c_btn_frame, text="+5", width=35, height=20, font=ctk.CTkFont(size=10),
                          command=lambda idx=idx, s=c_slider: self.adjust_step(idx, "contrast", s, 5)).pack(side="right", padx=2)

            # Separator line before Color
            sep_color = ctk.CTkFrame(col_frame, height=1, fg_color="#1E293B")
            sep_color.pack(fill="x", padx=15, pady=8)

            # Color Presets Header
            color_label = ctk.CTkLabel(col_frame, text=self.translate("color"), font=ctk.CTkFont(size=13, weight="bold"))
            color_label.pack(anchor="w", padx=15, pady=(2, 4))

            # Buttons for Color Presets
            color_btn_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            color_btn_frame.pack(fill="x", padx=15, pady=(0, 15))

            color_options = [
                ("sRGB", 1),
                ("6500K", 5),
                ("7500K", 6),
                ("9300K", 8),
                (self.translate("user_color"), 11)
            ]

            for label, val in color_options:
                btn = ctk.CTkButton(
                    color_btn_frame,
                    text=label,
                    width=48,
                    height=24,
                    font=ctk.CTkFont(size=10),
                    command=lambda idx=idx, v=val: self.color_preset_changed(idx, v)
                )
                btn.pack(side="left", padx=2, expand=True, fill="x")
                self.color_buttons[(idx, val)] = btn

            # Set initial active button highlight
            self.update_color_presets_ui(idx, mon["color_preset"])

            # Separator line before Resolution
            sep_res = ctk.CTkFrame(col_frame, height=1, fg_color="#1E293B")
            sep_res.pack(fill="x", padx=15, pady=8)

            # Resolution Header
            res_header = ctk.CTkLabel(col_frame, text=self.translate("resolution"), font=ctk.CTkFont(size=13, weight="bold"))
            res_header.pack(anchor="w", padx=15, pady=(2, 4))

            # Controls grid container
            res_controls_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            res_controls_frame.pack(fill="x", padx=15, pady=(0, 10))
            
            # Row 0: Display Scaling
            lbl_scale = ctk.CTkLabel(res_controls_frame, text=self.translate("screen_ratio"), font=ctk.CTkFont(size=11), width=60, anchor="w")
            lbl_scale.grid(row=0, column=0, sticky="w", pady=4)
            
            scaling_modes = ["Inteiro", "Proporcional", "1:1"] if self.lang == "pt" else ["Full", "Aspect", "1:1"]
            current_scaling_val = mon.get("display_scaling", 2)
            current_scaling_label = self.get_scaling_label(current_scaling_val)
            
            scale_var = ctk.StringVar(value=current_scaling_label)
            scale_menu = ctk.CTkOptionMenu(
                res_controls_frame,
                variable=scale_var,
                values=scaling_modes,
                width=160,
                height=24,
                font=ctk.CTkFont(size=11),
                command=lambda val, idx=idx: self.display_scaling_changed(idx, val)
            )
            scale_menu.grid(row=0, column=1, sticky="ew", pady=4)
            self.slider_vars[(idx, "display_scaling_dropdown")] = scale_menu
            
            # Row 1: System Resolution
            lbl_sys_res = ctk.CTkLabel(res_controls_frame, text=self.translate("system_res"), font=ctk.CTkFont(size=11), width=60, anchor="w")
            lbl_sys_res.grid(row=1, column=0, sticky="w", pady=4)
            
            resolutions_list = mon.get("resolutions_list", [])
            current_sys_res = mon.get("current_resolution", self.translate("none_option"))
            if not resolutions_list:
                resolutions_list = [current_sys_res] if current_sys_res else ["N/A"]
                
            sys_res_var = ctk.StringVar(value=current_sys_res if current_sys_res else "N/A")
            sys_res_menu = ctk.CTkOptionMenu(
                res_controls_frame,
                variable=sys_res_var,
                values=resolutions_list,
                width=160,
                height=24,
                font=ctk.CTkFont(size=11),
                command=lambda val, idx=idx: self.change_system_resolution(idx, val)
            )
            sys_res_menu.grid(row=1, column=1, sticky="ew", pady=4)
            self.slider_vars[(idx, "system_res_dropdown")] = sys_res_menu

        # Global Presets Bar below monitors (makes applying presets very clean)
        self.presets_frame = ctk.CTkFrame(self.tab_monitors, fg_color="#0F172A", border_color="#1E293B", border_width=1)
        self.presets_frame.grid(row=1, column=0, columnspan=max(1, len(self.monitors)), sticky="ew", padx=10, pady=(5, 10))
        
        # Row 0: Standard Presets
        std_container = ctk.CTkFrame(self.presets_frame, fg_color="transparent")
        std_container.pack(fill="x", padx=10, pady=5)
        
        lbl_pres = ctk.CTkLabel(std_container, text=self.translate("standard_presets"), font=ctk.CTkFont(size=12, weight="bold"))
        lbl_pres.pack(side="left", padx=(5, 10))
        
        for name, values in PRESETS.items():
            btn = ctk.CTkButton(
                std_container, 
                text=self.translate(f"presets.{name}"), 
                width=85, 
                height=26,
                fg_color="#1E293B",
                hover_color="#334155",
                font=ctk.CTkFont(size=11),
                command=lambda b=values[0], c=values[1]: self.apply_global_preset(b, c)
            )
            btn.pack(side="left", padx=5)

        # Row 1: Custom Presets
        custom_container = ctk.CTkFrame(self.presets_frame, fg_color="transparent")
        custom_container.pack(fill="x", padx=10, pady=(0, 10))
        
        lbl_custom = ctk.CTkLabel(custom_container, text=self.translate("custom_presets"), font=ctk.CTkFont(size=12, weight="bold"))
        lbl_custom.pack(side="left", padx=(5, 10))
        
        self.custom_presets_options = [self.translate("none_option")]
        self.custom_preset_var = ctk.StringVar(value=self.translate("none_option"))
        self.custom_preset_menu = ctk.CTkOptionMenu(
            custom_container,
            variable=self.custom_preset_var,
            values=self.custom_presets_options,
            width=140,
            height=26,
            font=ctk.CTkFont(size=11),
            command=self.on_custom_preset_selected
        )
        self.custom_preset_menu.pack(side="left", padx=5)
        
        self.save_preset_btn = ctk.CTkButton(
            custom_container,
            text=self.translate("save_current"),
            width=90,
            height=26,
            fg_color="#0EA5E9",
            hover_color="#0284c7",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.save_current_preset
        )
        self.save_preset_btn.pack(side="left", padx=5)
        
        self.delete_preset_btn = ctk.CTkButton(
            custom_container,
            text=self.translate("delete"),
            width=70,
            height=26,
            fg_color="#331A1A",
            hover_color="#552222",
            text_color="#FF6666",
            font=ctk.CTkFont(size=11),
            command=self.delete_selected_preset
        )
        self.delete_preset_btn.pack(side="left", padx=5)

        # Load option menus dropdown selections
        self.update_presets_menus()

        self.update_status_bar(self.translate("status_ready"))

    def toggle_sync(self):
        self.sync_enabled = self.sync_check.get() == 1
        if self.sync_enabled and len(self.monitors) > 1:
            # Sync Monitor 2 to Monitor 1 immediately
            m1_b = self.slider_vars[(0, "brightness_slider")].get()
            m1_c = self.slider_vars[(0, "contrast_slider")].get()
            self.apply_value_sync(0, "brightness", int(m1_b))
            self.apply_value_sync(0, "contrast", int(m1_c))
            
            # Sync color preset too
            m1_color = self.manager.monitors_info[0].get("color_preset", 5)
            self.color_preset_changed(0, m1_color)

            # Sync display scaling too
            m1_scaling = self.manager.monitors_info[0].get("display_scaling", 2)
            self.display_scaling_changed(0, REVERSE_SCALING_MAP.get(m1_scaling, "Proporcional"))

    def toggle_startup(self):
        enabled = self.startup_check.get() == 1
        try:
            set_run_on_startup(enabled)
            status = "ativada" if enabled else "desativada"
            self.update_status_bar(f"Inicialização automática {status}.")
        except Exception as e:
            self.update_status_bar(f"Falha ao configurar inicialização: {e}")

    def adjust_step(self, monitor_index, feature, slider, step):
        current = int(slider.get())
        new_val = max(0, min(100, current + step))
        slider.set(new_val)
        self.slider_changed(monitor_index, feature, new_val)

    def slider_changed(self, monitor_index, feature, value):
        # Update text label instantly
        label_var = self.slider_vars[(monitor_index, feature)]
        if feature == "brightness":
            label_var.set(self.translate("brightness").format(value))
        else:
            label_var.set(self.translate("contrast").format(value))

        # Push command to background worker
        self.worker.set_value(monitor_index, feature, value)

        # Handle Sync
        if self.sync_enabled:
            self.apply_value_sync(monitor_index, feature, value)

    def apply_value_sync(self, source_index, feature, value):
        for mon in self.monitors:
            idx = mon["index"]
            if idx != source_index:
                # Update other slider
                slider = self.slider_vars[(idx, f"{feature}_slider")]
                slider.set(value)
                # Update other text label
                label_var = self.slider_vars[(idx, feature)]
                if feature == "brightness":
                    label_var.set(self.translate("brightness").format(value))
                else:
                    label_var.set(self.translate("contrast").format(value))
                # Write command for other monitor
                self.worker.set_value(idx, feature, value)

    def apply_global_preset(self, b_val, c_val):
        self.update_status_bar(self.translate("status_preset_applied").format("Padrão" if self.lang == "pt" else "Standard"))
        for mon in self.monitors:
            idx = mon["index"]
            
            # Brightness update
            b_slider = self.slider_vars.get((idx, "brightness_slider"))
            if b_slider:
                b_slider.set(b_val)
                self.slider_vars[(idx, "brightness")].set(self.translate("brightness").format(b_val))
                self.worker.set_value(idx, "brightness", b_val)
                
            # Contrast update
            c_slider = self.slider_vars.get((idx, "contrast_slider"))
            if c_slider:
                c_slider.set(c_val)
                self.slider_vars[(idx, "contrast")].set(self.translate("contrast").format(c_val))
                self.worker.set_value(idx, "contrast", c_val)

    def color_preset_changed(self, monitor_index, value):
        self.update_color_presets_ui(monitor_index, value)
        self.worker.set_value(monitor_index, "color_preset", value)
        if self.sync_enabled:
            for mon in self.monitors:
                idx = mon["index"]
                if idx != monitor_index:
                    self.update_color_presets_ui(idx, value)
                    self.worker.set_value(idx, "color_preset", value)

    def update_color_presets_ui(self, monitor_index, active_val):
        color_options = [1, 5, 6, 8, 11]
        for val in color_options:
            btn = self.color_buttons.get((monitor_index, val))
            if btn:
                if val == active_val:
                    btn.configure(fg_color="#0ea5e9", hover_color="#0284c7")
                else:
                    btn.configure(fg_color="#1e293b", hover_color="#334155")

    def display_scaling_changed(self, monitor_index, selected_label):
        val = SCALING_MAP.get(selected_label)
        if val is not None:
            self.worker.set_value(monitor_index, "display_scaling", val)
            if self.sync_enabled:
                for mon in self.monitors:
                    idx = mon["index"]
                    if idx != monitor_index:
                        dropdown = self.slider_vars.get((idx, "display_scaling_dropdown"))
                        if dropdown:
                            dropdown.set(selected_label)
                        self.worker.set_value(idx, "display_scaling", val)

    def change_system_resolution(self, monitor_index, selected_res):
        if monitor_index >= len(self.monitors):
            return
        mon = self.monitors[monitor_index]
        gdi_device = mon.get("device_name")
        modes_dict = mon.get("modes_dict", {})
        
        if not gdi_device or not modes_dict:
            return
            
        selected_mode = modes_dict.get(selected_res)
        if not selected_mode:
            return
            
        selected_mode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT | win32con.DM_DISPLAYFREQUENCY
        if hasattr(selected_mode, "DisplayOrientation"):
            selected_mode.Fields |= win32con.DM_DISPLAYORIENTATION
            
        result = win32api.ChangeDisplaySettingsEx(gdi_device, selected_mode, 0)
        if result == win32con.DISP_CHANGE_SUCCESSFUL:
            self.update_status_bar(self.translate("status_res_changed").format(monitor_index+1, selected_res))
            mon["current_resolution"] = selected_res
        else:
            messagebox.showerror(self.translate("status_res_error_title"), self.translate("status_res_error_text").format(selected_res, result))
            dropdown = self.slider_vars.get((monitor_index, "system_res_dropdown"))
            if dropdown:
                dropdown.set(mon.get("current_resolution", ""))

    def load_config(self):
        self.config = {
            "startup_preset": "Nenhum",
            "custom_presets": {},
            "language": get_system_lang()
        }
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
            except Exception as e:
                print(f"Error creating config dir: {e}")
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.config.update(loaded)
            except Exception as e:
                print(f"Error reading config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_presets_menus(self):
        custom_names = list(self.config.get("custom_presets", {}).keys())
        none_lbl = self.translate("none_option")
        
        # 1. Update Custom Presets dropdown in presets frame
        custom_options = [none_lbl] + custom_names
        self.custom_preset_menu.configure(values=custom_options)
        
        current_custom = self.custom_preset_var.get()
        if current_custom not in custom_options:
            self.custom_preset_var.set(none_lbl)
            
        if custom_names:
            self.delete_preset_btn.configure(state="normal")
        else:
            self.delete_preset_btn.configure(state="disabled")
            
        # 2. Update Startup Preset dropdown in header
        startup_options = [none_lbl] + [self.translate(f"presets.{k}") for k in PRESETS.keys()] + custom_names
        self.startup_preset_menu.configure(values=startup_options)
        
        current_startup = self.config.get("startup_preset", "Nenhum")
        self.startup_preset_var.set(self.preset_key_to_ui(current_startup))

    def on_startup_preset_changed(self, selected_value):
        internal_key = self.ui_to_preset_key(selected_value)
        self.config["startup_preset"] = internal_key
        self.save_config()
        self.update_status_bar(self.translate("status_startup_preset_changed").format(selected_value))

    def on_custom_preset_selected(self, name):
        none_lbl = self.translate("none_option")
        if name == none_lbl or not name:
            return
        custom_presets = self.config.get("custom_presets", {})
        if name in custom_presets:
            preset_data = custom_presets[name]
            self.apply_custom_preset_data(preset_data)
            self.update_status_bar(self.translate("status_preset_applied").format(name))

    def apply_custom_preset_data(self, preset_data):
        if not isinstance(preset_data, list):
            return
        for mon in self.monitors:
            idx = mon["index"]
            if idx < len(preset_data):
                m_data = preset_data[idx]
                b_val = m_data.get("brightness", mon["brightness"])
                c_val = m_data.get("contrast", mon["contrast"])
                col_val = m_data.get("color_preset", mon["color_preset"])
                scaling_val = m_data.get("display_scaling", mon.get("display_scaling", 2))
                
                mon["brightness"] = b_val
                mon["contrast"] = c_val
                mon["color_preset"] = col_val
                mon["display_scaling"] = scaling_val
                
                b_slider = self.slider_vars.get((idx, "brightness_slider"))
                if b_slider:
                    b_slider.set(b_val)
                    self.slider_vars[(idx, "brightness")].set(self.translate("brightness").format(b_val))
                
                c_slider = self.slider_vars.get((idx, "contrast_slider"))
                if c_slider:
                    c_slider.set(c_val)
                    self.slider_vars[(idx, "contrast")].set(self.translate("contrast").format(c_val))
                
                self.update_color_presets_ui(idx, col_val)
                
                # Update display scaling UI
                scale_dropdown = self.slider_vars.get((idx, "display_scaling_dropdown"))
                if scale_dropdown:
                    scale_dropdown.set(self.get_scaling_label(scaling_val))
                
                self.worker.set_value(idx, "brightness", b_val)
                self.worker.set_value(idx, "contrast", c_val)
                self.worker.set_value(idx, "color_preset", col_val)
                self.worker.set_value(idx, "display_scaling", scaling_val)

    def apply_startup_preset_if_needed(self):
        if not self.monitors:
            return
            
        preset_name = self.config.get("startup_preset", "Nenhum")
        if not preset_name or preset_name == "Nenhum":
            return
            
        if preset_name in PRESETS:
            b_val, c_val = PRESETS[preset_name]
            for mon in self.monitors:
                idx = mon["index"]
                mon["brightness"] = b_val
                mon["contrast"] = c_val
                self.worker.set_value(idx, "brightness", b_val)
                self.worker.set_value(idx, "contrast", c_val)
            self.update_status_bar(self.translate("status_preset_applied").format(self.preset_key_to_ui(preset_name)))
            
        elif preset_name in self.config.get("custom_presets", {}):
            preset_data = self.config["custom_presets"][preset_name]
            if isinstance(preset_data, list):
                for mon in self.monitors:
                    idx = mon["index"]
                    if idx < len(preset_data):
                        m_data = preset_data[idx]
                        b_val = m_data.get("brightness", mon["brightness"])
                        c_val = m_data.get("contrast", mon["contrast"])
                        col_val = m_data.get("color_preset", mon["color_preset"])
                        scaling_val = m_data.get("display_scaling", mon.get("display_scaling", 2))
                        
                        mon["brightness"] = b_val
                        mon["contrast"] = c_val
                        mon["color_preset"] = col_val
                        mon["display_scaling"] = scaling_val
                        
                        self.worker.set_value(idx, "brightness", b_val)
                        self.worker.set_value(idx, "contrast", c_val)
                        self.worker.set_value(idx, "color_preset", col_val)
                        self.worker.set_value(idx, "display_scaling", scaling_val)
            self.update_status_bar(self.translate("status_preset_applied").format(preset_name))

    def save_current_preset(self):
        dialog = ctk.CTkInputDialog(text=self.translate("dialog_save_text"), title=self.translate("dialog_save_title"))
        name = dialog.get_input()
        if not name:
            return
        name = name.strip()
        if not name:
            return
            
        reserved = ["Nenhum", "None"] + list(PRESETS.keys()) + [self.translate(f"presets.{k}") for k in PRESETS.keys()]
        if name in reserved:
            messagebox.showerror(self.translate("dialog_save_invalid_title"), self.translate("dialog_save_invalid_text"))
            return
            
        preset_data = []
        for mon in self.monitors:
            idx = mon["index"]
            b_val = int(self.slider_vars[(idx, "brightness_slider")].get())
            c_val = int(self.slider_vars[(idx, "contrast_slider")].get())
            col_val = mon.get("color_preset", 5)
            scaling_val = mon.get("display_scaling", 2)
            preset_data.append({
                "brightness": b_val,
                "contrast": c_val,
                "color_preset": col_val,
                "display_scaling": scaling_val
            })
            
        self.config["custom_presets"][name] = preset_data
        self.save_config()
        self.update_presets_menus()
        self.update_tray_menu()
        self.custom_preset_var.set(name)
        self.update_status_bar(self.translate("status_preset_saved").format(name))

    def delete_selected_preset(self):
        name = self.custom_preset_var.get()
        none_lbl = self.translate("none_option")
        if name == none_lbl or not name:
            return
        if messagebox.askyesno(self.translate("dialog_delete_title"), self.translate("dialog_delete_text").format(name)):
            if name in self.config.get("custom_presets", {}):
                del self.config["custom_presets"][name]
                if self.config.get("startup_preset") == name:
                    self.config["startup_preset"] = "Nenhum"
                self.save_config()
                self.update_presets_menus()
                self.update_tray_menu()
                self.update_status_bar(self.translate("status_preset_deleted").format(name))

    def safe_apply_custom_preset(self, name):
        custom_presets = self.config.get("custom_presets", {})
        if name in custom_presets:
            preset_data = custom_presets[name]
            self.after(0, lambda: self.apply_custom_preset_data(preset_data))

    def update_tray_menu(self):
        if not self.tray_icon:
            return
        menu_items = [
            pystray.MenuItem(self.translate("tray_open"), self.restore_from_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"{self.translate('tray_profile')}: {self.translate('presets.Leitura')}", lambda: self.safe_apply_preset("Leitura")),
            pystray.MenuItem(f"{self.translate('tray_profile')}: {self.translate('presets.Trabalho')}", lambda: self.safe_apply_preset("Trabalho")),
            pystray.MenuItem(f"{self.translate('tray_profile')}: {self.translate('presets.Jogos')}", lambda: self.safe_apply_preset("Jogos")),
            pystray.MenuItem(f"{self.translate('tray_profile')}: {self.translate('presets.Noite')}", lambda: self.safe_apply_preset("Noite")),
        ]
        custom_presets = self.config.get("custom_presets", {})
        if custom_presets:
            menu_items.append(pystray.Menu.SEPARATOR)
            for name in custom_presets.keys():
                menu_items.append(
                    pystray.MenuItem(f"{self.translate('tray_profile')}: {name}", lambda idx=None, n=name: self.safe_apply_custom_preset(n))
                )
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem(self.translate("tray_quit"), self.quit_app))
        self.tray_icon.menu = pystray.Menu(*menu_items)

    # --- System Tray & Minimizing logic ---
    def start_tray(self):
        # Create base menu
        menu = pystray.Menu(pystray.MenuItem(self.translate("tray_open"), self.restore_from_tray, default=True))
        self.tray_icon = pystray.Icon("display_control", self.icon_image, "Display Control Panel", menu)
        self.update_tray_menu()
        # Start pystray loop in a background daemon thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def safe_apply_preset(self, name):
        vals = PRESETS[name]
        # Tkinter demands updates happen on main thread
        self.after(0, lambda: self.apply_global_preset(vals[0], vals[1]))

    def minimize_to_tray(self):
        self.withdraw()
        # Ensure status message
        self.update_status_bar(self.translate("status_minimized"))

    def restore_from_tray(self, icon=None, item=None):
        def restore():
            self.deiconify()
            self.lift()
            self.focus_force()
        self.after(0, restore)

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)

    def start_single_instance_listener(self, bound_socket):
        self.instance_socket = bound_socket
        self.instance_thread = threading.Thread(target=self._single_instance_worker, daemon=True)
        self.instance_thread.start()

    def _single_instance_worker(self):
        while True:
            try:
                data, addr = self.instance_socket.recvfrom(1024)
                if data == b"show":
                    self.restore_from_tray()
            except Exception:
                break


if __name__ == "__main__":
    bound_socket = check_single_instance()
    app = DisplayControlApp(bound_socket)
    app.mainloop()
