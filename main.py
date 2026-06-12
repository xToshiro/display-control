import threading
import time
import queue
import winreg
import sys
import os
import customtkinter as ctk
import pystray
from PIL import Image, ImageDraw
import screen_brightness_control as sbc
from monitorcontrol import get_monitors

# Standard Preset Configurations (Brightness, Contrast)
PRESETS = {
    "Leitura": (15, 45),
    "Trabalho": (45, 50),
    "Jogos": (75, 60),
    "Noite": (5, 35)
}

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DisplayControl"

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
                cmd = f'"{pythonw_path}" "{script_path}"'
            else:
                cmd = f'"{script_path}"'
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
            
            # 1. Fetch info using screen-brightness-control (includes EDID and Serials)
            try:
                sbc_list = sbc.list_monitors_info()
            except Exception as e:
                print(f"Error in sbc: {e}")
                sbc_list = []

            # 2. Fetch monitor objects using monitorcontrol
            try:
                mc_list = get_monitors()
            except Exception as e:
                print(f"Error in monitorcontrol: {e}")
                mc_list = []

            self.monitors_mc = mc_list

            # 3. Match them up
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
                        # VCP Code 0x14 (20)
                        color_preset, _ = mc_mon.vcp.get_vcp_feature(0x14)
                except Exception as e:
                    print(f"Error getting color preset for Monitor {idx+1}: {e}")

                self.monitors_info.append({
                    "index": idx,
                    "model": model,
                    "serial": serial,
                    "brightness": brightness,
                    "contrast": contrast,
                    "color_preset": color_preset,
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
                            
                    self.manager.log_status("Pronto")
            except Exception as e:
                self.manager.log_status(f"Erro ao atualizar monitor: {e}")
                print(f"Error writing feature {feature} to monitor {monitor_idx}: {e}")

            time.sleep(0.12)  # Prevent overloading DDC/CI communications


class DisplayControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Config
        self.title("Painel de Controle de Monitores")
        self.geometry("840x560")
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
            text="Display Control Panel", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(side="left")

        # Global Control Box / Checkboxes at top right
        self.top_controls = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.top_controls.pack(side="right")

        self.startup_check = ctk.CTkCheckBox(
            self.top_controls, 
            text="Iniciar com Windows", 
            command=self.toggle_startup,
            font=ctk.CTkFont(size=12)
        )
        self.startup_check.pack(side="left", padx=10)
        if is_run_on_startup():
            self.startup_check.select()

        self.sync_check = ctk.CTkCheckBox(
            self.top_controls, 
            text="Sincronizar Monitores", 
            command=self.toggle_sync,
            font=ctk.CTkFont(size=12)
        )
        self.sync_check.pack(side="left", padx=10)

        # --- Content Frame (Contains monitors or loading indicator) ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=5)
        
        # --- Bottom Status Bar Frame ---
        self.bottom_frame = ctk.CTkFrame(self, height=35, corner_radius=0)
        self.bottom_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        self.status_label = ctk.CTkLabel(
            self.bottom_frame, 
            text="Carregando...", 
            font=ctk.CTkFont(size=11), 
            text_color="gray"
        )
        self.status_label.pack(side="left", padx=15, pady=5)

        self.refresh_btn = ctk.CTkButton(
            self.bottom_frame, 
            text="Recarregar", 
            width=80, 
            height=24,
            command=self.trigger_scan,
            font=ctk.CTkFont(size=11)
        )
        self.refresh_btn.pack(side="right", padx=15, pady=5)

    def show_loading(self):
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.loading_label = ctk.CTkLabel(
            self.content_frame, 
            text="Procurando monitores DDC/CI...\nIsso pode levar alguns segundos.", 
            font=ctk.CTkFont(size=16)
        )
        self.loading_label.pack(expand=True)
        self.refresh_btn.configure(state="disabled")

    def show_error(self, message):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        error_box = ctk.CTkFrame(self.content_frame, fg_color="#331A1A", border_color="#FF4D4D", border_width=1)
        error_box.pack(expand=True, padx=40, pady=20, fill="both")
        
        err_title = ctk.CTkLabel(
            error_box, 
            text="Nenhum Monitor DDC/CI Encontrado", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FF6666"
        )
        err_title.pack(pady=(20, 10))

        instructions = (
            "DDC/CI é o protocolo que permite ajustar brilho/contraste pelo PC.\n\n"
            "Verificações recomendadas:\n"
            "1. Habilite o suporte a DDC/CI nas configurações físicas do monitor (menu OSD).\n"
            "2. Certifique-se de que os monitores estão conectados por HDMI, DisplayPort ou USB-C.\n"
            "3. Reinicie este aplicativo e tente recarregar."
        )
        
        err_desc = ctk.CTkLabel(
            error_box, 
            text=instructions, 
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
        self.after(0, self.render_monitors_ui)

    def render_monitors_ui(self):
        # Clear loading widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.refresh_btn.configure(state="normal")

        if not self.monitors:
            self.show_error("Nenhum monitor DDC/CI compatível encontrado.")
            return

        # Configure columns inside content frame based on monitor count
        self.content_frame.columnconfigure(0, weight=1)
        if len(self.monitors) > 1:
            self.content_frame.columnconfigure(1, weight=1)

        # Loop through found monitors and build their sliders
        for i, mon in enumerate(self.monitors):
            idx = mon["index"]
            col_frame = ctk.CTkFrame(self.content_frame, border_color="#1E293B", border_width=1, fg_color="#0F172A")
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
            b_label_var = ctk.StringVar(value=f"Brilho: {mon['brightness']}%")
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
            c_label_var = ctk.StringVar(value=f"Contraste: {mon['contrast']}%")
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
            color_label = ctk.CTkLabel(col_frame, text="Cor", font=ctk.CTkFont(size=13, weight="bold"))
            color_label.pack(anchor="w", padx=15, pady=(2, 4))

            # Buttons for Color Presets
            color_btn_frame = ctk.CTkFrame(col_frame, fg_color="transparent")
            color_btn_frame.pack(fill="x", padx=15, pady=(0, 15))

            color_options = [
                ("sRGB", 1),
                ("6500K", 5),
                ("7500K", 6),
                ("9300K", 8),
                ("Usuário", 11)
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

        # Global Presets Bar below monitors (makes applying presets very clean)
        self.presets_frame = ctk.CTkFrame(self.content_frame, fg_color="#0F172A", border_color="#1E293B", border_width=1)
        self.presets_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))
        
        lbl_pres = ctk.CTkLabel(self.presets_frame, text="Perfis Rápidos (Ambos):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_pres.pack(side="left", padx=15, pady=8)
        
        for name, values in PRESETS.items():
            btn = ctk.CTkButton(
                self.presets_frame, 
                text=name, 
                width=85, 
                height=26,
                fg_color="#1E293B",
                hover_color="#334155",
                font=ctk.CTkFont(size=11),
                command=lambda b=values[0], c=values[1]: self.apply_global_preset(b, c)
            )
            btn.pack(side="left", padx=6, pady=8)

        self.update_status_bar("Pronto")

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
        label_prefix = "Brilho" if feature == "brightness" else "Contraste"
        label_var.set(f"{label_prefix}: {value}%")

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
                label_prefix = "Brilho" if feature == "brightness" else "Contraste"
                label_var.set(f"{label_prefix}: {value}%")
                # Write command for other monitor
                self.worker.set_value(idx, feature, value)

    def apply_global_preset(self, b_val, c_val):
        self.update_status_bar("Aplicando perfil...")
        for mon in self.monitors:
            idx = mon["index"]
            
            # Brightness update
            b_slider = self.slider_vars.get((idx, "brightness_slider"))
            if b_slider:
                b_slider.set(b_val)
                self.slider_vars[(idx, "brightness")].set(f"Brilho: {b_val}%")
                self.worker.set_value(idx, "brightness", b_val)
                
            # Contrast update
            c_slider = self.slider_vars.get((idx, "contrast_slider"))
            if c_slider:
                c_slider.set(c_val)
                self.slider_vars[(idx, "contrast")].set(f"Contraste: {c_val}%")
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

    # --- System Tray & Minimizing logic ---
    def start_tray(self):
        # Create menu items
        menu = pystray.Menu(
            pystray.MenuItem('Abrir Painel', self.restore_from_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Perfil: Leitura', lambda: self.safe_apply_preset("Leitura")),
            pystray.MenuItem('Perfil: Trabalho', lambda: self.safe_apply_preset("Trabalho")),
            pystray.MenuItem('Perfil: Jogos', lambda: self.safe_apply_preset("Jogos")),
            pystray.MenuItem('Perfil: Noite', lambda: self.safe_apply_preset("Noite")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Sair', self.quit_app)
        )
        self.tray_icon = pystray.Icon("display_control", self.icon_image, "Display Control Panel", menu)
        # Start pystray loop in a background daemon thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def safe_apply_preset(self, name):
        vals = PRESETS[name]
        # Tkinter demands updates happen on main thread
        self.after(0, lambda: self.apply_global_preset(vals[0], vals[1]))

    def minimize_to_tray(self):
        self.withdraw()
        # Ensure status message
        self.update_status_bar("Minimizado na bandeja de sistema.")

    def restore_from_tray(self, icon=None, item=None):
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)


if __name__ == "__main__":
    app = DisplayControlApp()
    app.mainloop()
