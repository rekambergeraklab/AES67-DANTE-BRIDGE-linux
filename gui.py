import tkinter as tk
from tkinter import scrolledtext, ttk
import subprocess
import threading
import os
import signal
import re

class AES67Controller:
    def __init__(self, root):
        self.root = root
        self.root.geometry("780x660")
        self.root.resizable(False, False)
        
        # State Internal untuk Indikator Status
        self.current_state_main = "status_offline"
        self.current_state_sync = "status_idle"
        self.current_main_color = "#FF5252"
        self.current_sync_color = "#999999"

        # Dictionary Bahasa (Termasuk Status Mesin)
        self.lang_data = {
            "Bahasa Indonesia": {
                "title": "Pengendali Jaringan Audio AES67",
                "card1": "KONFIGURASI PERANGKAT",
                "iface": "Antarmuka Jaringan:",
                "sr": "Tingkat Sampel:",
                "ptime": "Waktu Paket (ptime):",
                "card2": "MANAJEMEN JAM (CLOCK)",
                "role": "Peran Jam:",
                "sync": "Status Sinkronisasi:",
                "jitter": "Jitter (Beda Waktu):",
                "card3": "MESIN ROUTING",
                "start": "▶ JALANKAN MESIN",
                "stop": "⬛ HENTIKAN MESIN",
                "log": "CATATAN SISTEM (LOG)",
                "roles": ["Pengikut (Hanya Slave)", "Negosiasi Otomatis"],
                "lang_lbl": "Bahasa / Language:",
                # Status Terjemahan
                "status_offline": "TERPUTUS",
                "status_starting": "MEMULAI...",
                "status_locked": "TERHUBUNG (TERKUNCI)",
                "status_master": "TERHUBUNG (MASTER)",
                "status_idle": "MENUNGGU",
                "sync_waiting": "MENUNGGU PTP",
                "sync_slave": "SINKRON (SLAVE)",
                "sync_master": "GRANDMASTER",
                "sync_calib": "MENGALIBRASI..."
            },
            "English": {
                "title": "AES67 Audio Network Controller",
                "card1": "DEVICE CONFIGURATION",
                "iface": "Network Interface:",
                "sr": "Sample Rate:",
                "ptime": "Packet Time (ptime):",
                "card2": "CLOCK MANAGEMENT",
                "role": "Clock Role:",
                "sync": "Clock Sync State:",
                "jitter": "Master Offset (Jitter):",
                "card3": "ROUTING ENGINE",
                "start": "▶ START ENGINE",
                "stop": "⬛ STOP ENGINE",
                "log": "SYSTEM LOG",
                "roles": ["Follower (SlaveOnly)", "Auto-Negotiate"],
                "lang_lbl": "Language / Bahasa:",
                # Translation Status
                "status_offline": "OFFLINE",
                "status_starting": "STARTING...",
                "status_locked": "ONLINE (LOCKED)",
                "status_master": "ONLINE (MASTER)",
                "status_idle": "IDLE",
                "sync_waiting": "WAITING FOR PTP",
                "sync_slave": "SYNCED (SLAVE)",
                "sync_master": "GRANDMASTER",
                "sync_calib": "CALIBRATING..."
            }
        }
        
        # Variabel Dinamis untuk UI
        self.current_lang = "Bahasa Indonesia"
        self.str_title = tk.StringVar()
        self.str_card1 = tk.StringVar()
        self.str_iface = tk.StringVar()
        self.str_sr = tk.StringVar()
        self.str_ptime = tk.StringVar()
        self.str_card2 = tk.StringVar()
        self.str_role = tk.StringVar()
        self.str_sync = tk.StringVar()
        self.str_jitter = tk.StringVar()
        self.str_card3 = tk.StringVar()
        self.str_start = tk.StringVar()
        self.str_stop = tk.StringVar()
        self.str_log = tk.StringVar()
        self.str_lang_lbl = tk.StringVar()
        
        self.update_language_texts()

        self.root.title(self.str_title.get())
        
        # Menerapkan Tema Desain Profesional
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.root.configure(bg="#EBEBEB")

        self.ptp_process = None
        self.phc_process = None
        self.pw_process = None
        
        self.build_ui()

    def update_language_texts(self):
        data = self.lang_data[self.current_lang]
        self.str_title.set(data["title"])
        self.str_card1.set(data["card1"])
        self.str_iface.set(data["iface"])
        self.str_sr.set(data["sr"])
        self.str_ptime.set(data["ptime"])
        self.str_card2.set(data["card2"])
        self.str_role.set(data["role"])
        self.str_sync.set(data["sync"])
        self.str_jitter.set(data["jitter"])
        self.str_card3.set(data["card3"])
        self.str_start.set(data["start"])
        self.str_stop.set(data["stop"])
        self.str_log.set(data["log"])
        self.str_lang_lbl.set(data["lang_lbl"])
        self.root.title(self.str_title.get())

        # Update Live Status dynamically based on the active language
        if hasattr(self, 'status_indicator'):
            self.status_indicator.config(text=data[self.current_state_main])
            self.sync_state_lbl.config(text=data[self.current_state_sync])

    def on_language_change(self, event):
        self.current_lang = self.lang_cb.get()
        self.update_language_texts()
        # Update Dropdown options
        self.clock_mode['values'] = self.lang_data[self.current_lang]["roles"]
        self.clock_mode.current(0)

    def configure_styles(self):
        bg_color = "#EBEBEB"
        card_bg = "#FFFFFF"
        text_color = "#333333"

        self.style.configure('TFrame', background=bg_color)
        self.style.configure('Card.TFrame', background=card_bg, relief="flat")
        self.style.configure('CardHeader.TLabel', font=("Segoe UI", 11, "bold"), background=card_bg, foreground="#555555")
        
        self.style.configure('Slogan.TLabel', font=("Segoe UI", 10, "italic", "bold"), background=bg_color, foreground="#555555")
        self.style.configure('Credit.TLabel', font=("Segoe UI", 9, "bold"), background=bg_color, foreground="#0066CC")
        self.style.configure('Lang.TLabel', font=("Segoe UI", 9, "bold"), background=bg_color, foreground="#555555")
        
        self.style.configure('Standard.TLabel', font=("Segoe UI", 10), background=card_bg, foreground=text_color)
        self.style.configure('Data.TLabel', font=("Consolas", 11, "bold"), background=card_bg, foreground="#0066CC")
        
        self.style.configure('Start.TButton', font=("Segoe UI", 10, "bold"), background="#4CAF50", foreground="white")
        self.style.map('Start.TButton', background=[('active', '#45A049'), ('disabled', '#A5D6A7')])

        self.style.configure('Stop.TButton', font=("Segoe UI", 10, "bold"), background="#E53935", foreground="white")
        self.style.map('Stop.TButton', background=[('active', '#D32F2F'), ('disabled', '#EF9A9A')])

    def build_ui(self):
        # --- BAGIAN HEADER ---
        header_frame = tk.Frame(self.root, bg="#333333", height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="AES67 / DANTE BRIDGE", font=("Segoe UI", 16, "bold"), fg="white", bg="#333333").pack(side=tk.LEFT, padx=20, pady=15)
        
        # Initial Status
        init_status = self.lang_data[self.current_lang][self.current_state_main]
        self.status_indicator = tk.Label(header_frame, text=init_status, font=("Segoe UI", 12, "bold"), fg=self.current_main_color, bg="#333333")
        self.status_indicator.pack(side=tk.RIGHT, padx=20, pady=15)

        # --- GRID KONTEN UTAMA ---
        content_frame = ttk.Frame(self.root, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Kolom Kiri
        left_col = ttk.Frame(content_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # --- MENU BAHASA (Dinaikkan ke atas Konfigurasi) ---
        lang_frame = ttk.Frame(left_col)
        lang_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(lang_frame, textvariable=self.str_lang_lbl, style='Lang.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.lang_cb = ttk.Combobox(lang_frame, values=["Bahasa Indonesia", "English"], state="readonly", width=18)
        self.lang_cb.current(0)
        self.lang_cb.pack(side=tk.LEFT)
        self.lang_cb.bind("<<ComboboxSelected>>", self.on_language_change)

        # KARTU 1: Informasi Perangkat & Audio
        card1 = ttk.Frame(left_col, style='Card.TFrame', padding="15")
        card1.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(card1, textvariable=self.str_card1, style='CardHeader.TLabel').grid(row=0, column=0, sticky=tk.W, columnspan=2, pady=(0, 10))
        
        ttk.Label(card1, textvariable=self.str_iface, style='Standard.TLabel').grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(card1, text="eno1 (Hardware PTP)", style='Data.TLabel').grid(row=1, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(card1, textvariable=self.str_sr, style='Standard.TLabel').grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(card1, text="48000 Hz", style='Data.TLabel').grid(row=2, column=1, sticky=tk.E, pady=2)
        
        ttk.Label(card1, textvariable=self.str_ptime, style='Standard.TLabel').grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(card1, text="1 ms (Dante Spec)", style='Data.TLabel').grid(row=3, column=1, sticky=tk.E, pady=2)

        # KARTU 2: Pengaturan Jam (Clock)
        card2 = ttk.Frame(left_col, style='Card.TFrame', padding="15")
        card2.pack(fill=tk.X)
        
        ttk.Label(card2, textvariable=self.str_card2, style='CardHeader.TLabel').grid(row=0, column=0, sticky=tk.W, columnspan=2, pady=(0, 10))
        
        ttk.Label(card2, textvariable=self.str_role, style='Standard.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.clock_mode = ttk.Combobox(card2, values=self.lang_data[self.current_lang]["roles"], state="readonly", width=18)
        self.clock_mode.current(0)
        self.clock_mode.grid(row=1, column=1, sticky=tk.E, pady=5)

        ttk.Label(card2, textvariable=self.str_sync, style='Standard.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        
        init_sync = self.lang_data[self.current_lang][self.current_state_sync]
        self.sync_state_lbl = ttk.Label(card2, text=init_sync, font=("Segoe UI", 10, "bold"), background="#FFFFFF", foreground=self.current_sync_color)
        self.sync_state_lbl.grid(row=2, column=1, sticky=tk.E, pady=5)

        ttk.Label(card2, textvariable=self.str_jitter, style='Standard.TLabel').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.jitter_lbl = ttk.Label(card2, text="-- ns", font=("Consolas", 12, "bold"), background="#FFFFFF", foreground="#333333")
        self.jitter_lbl.grid(row=3, column=1, sticky=tk.E, pady=5)

        # --- POJOK KIRI BAWAH (Slogan & Kredit) ---
        bottom_left_frame = ttk.Frame(left_col)
        bottom_left_frame.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.SW, pady=(10, 0))

        ttk.Label(bottom_left_frame, text="\"Dibalik kesulitan, ada kemudahan. !\"", style='Slogan.TLabel').pack(anchor=tk.W, pady=(0, 2))
        ttk.Label(bottom_left_frame, text="developed by rekambergerak Yogyakarta-Indonesia", style='Credit.TLabel').pack(anchor=tk.W)


        # Kolom Kanan (Kontrol & Log)
        right_col = ttk.Frame(content_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # KARTU 3: Kontrol Mesin Audio
        card3 = ttk.Frame(right_col, style='Card.TFrame', padding="15")
        card3.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(card3, textvariable=self.str_card3, style='CardHeader.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        btn_frame = tk.Frame(card3, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_start = tk.Button(btn_frame, textvariable=self.str_start, command=self.start_engine, bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"), relief="flat")
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=5)
        
        self.btn_stop = tk.Button(btn_frame, textvariable=self.str_stop, command=self.stop_engine, state=tk.DISABLED, bg="#A5D6A7", fg="white", font=("Segoe UI", 10, "bold"), relief="flat")
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0), ipady=5)

        # Jendela Log
        log_container = ttk.Frame(right_col, style='Card.TFrame', padding="10")
        log_container.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_container, textvariable=self.str_log, style='CardHeader.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        self.log_area = scrolledtext.ScrolledText(log_container, wrap=tk.WORD, bg="#2B2B2B", fg="#A9B7C6", font=("Consolas", 9), relief="flat")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.insert(tk.END, "Sistem Siap / System Ready.\n")
        self.log_area.configure(state='disabled')

    def log_message(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message)
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def read_ptp_output(self):
        for line in iter(self.ptp_process.stdout.readline, b''):
            if line:
                decoded = line.decode('utf-8')
                self.root.after(0, self.log_message, decoded)
                
                # Update status menggunakan Keys dictionary
                if "UNCALIBRATED to SLAVE" in decoded:
                    self.root.after(0, lambda: self.update_status("status_locked", "#4CAF50", "sync_slave", "#4CAF50"))
                elif "to MASTER" in decoded:
                    self.root.after(0, lambda: self.update_status("status_master", "#2196F3", "sync_master", "#2196F3"))
                elif "LISTENING to UNCALIBRATED" in decoded:
                    self.root.after(0, lambda: self.update_status(self.current_state_main, self.current_main_color, "sync_calib", "#FF9800"))

                if "master offset" in decoded:
                    match = re.search(r'master offset\s+(-?\d+)', decoded)
                    if match:
                        offset = match.group(1)
                        self.root.after(0, lambda: self.update_jitter(offset))

    def update_status(self, main_key, main_color, sync_key, sync_color):
        # Simpan state saat ini
        self.current_state_main = main_key
        self.current_state_sync = sync_key
        self.current_main_color = main_color
        self.current_sync_color = sync_color

        # Render teks sesuai bahasa aktif
        active_lang_data = self.lang_data[self.current_lang]
        self.status_indicator.config(text=active_lang_data[main_key], fg=main_color)
        self.sync_state_lbl.config(text=active_lang_data[sync_key], foreground=sync_color)

    def update_jitter(self, offset_str):
        offset = int(offset_str)
        color = "#4CAF50" if abs(offset) < 500 else ("#FF9800" if abs(offset) < 2000 else "#E53935")
        self.jitter_lbl.config(text=f"{offset} ns", foreground=color)

    def start_engine(self):
        self.btn_start.config(state=tk.DISABLED, bg="#A5D6A7")
        self.btn_stop.config(state=tk.NORMAL, bg="#E53935")
        
        self.update_status("status_starting", "#FF9800", "sync_waiting", "#FF9800")
        self.log_message("\n>>> MENGAKTIFKAN JAM AES67 DAN ROUTING <<<\n")

        ptp_flags = ["ptp4l", "-i", "eno1", "-m", "-H"]
        if "Slave" in self.clock_mode.get():
            ptp_flags.append("-s")

        self.ptp_process = subprocess.Popen(
            ["stdbuf", "-oL"] + ptp_flags, 
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

        threading.Thread(target=self.read_ptp_output, daemon=True).start()

        self.phc_process = subprocess.Popen(["phc2sys", "-s", "eno1", "-c", "CLOCK_REALTIME", "-w", "-q"], preexec_fn=os.setsid)

        real_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        pw_command = f"sudo -u {real_user} XDG_RUNTIME_DIR=/run/user/$(id -u {real_user}) pipewire -c /home/{real_user}/.config/pipewire/aes67-8ch.conf"
        self.pw_process = subprocess.Popen(pw_command, shell=True, preexec_fn=os.setsid)

    def stop_engine(self):
        self.log_message("\n>>> MENGHENTIKAN MESIN AUDIO <<<\n")
        
        self.update_status("status_offline", "#FF5252", "status_idle", "#999999")
        self.jitter_lbl.config(text="-- ns", foreground="#333333")
        
        self.btn_start.config(state=tk.NORMAL, bg="#4CAF50")
        self.btn_stop.config(state=tk.DISABLED, bg="#EF9A9A")

        try:
            if self.ptp_process: os.killpg(os.getpgid(self.ptp_process.pid), signal.SIGTERM)
            if self.phc_process: os.killpg(os.getpgid(self.phc_process.pid), signal.SIGTERM)
            if self.pw_process: os.killpg(os.getpgid(self.pw_process.pid), signal.SIGTERM)
        except Exception as e:
            self.log_message(f"Catatan Pembersihan: {e}\n")
            
        self.log_message("Semua proses telah dihentikan.\n")

    def on_close(self):
        self.stop_engine()
        self.root.destroy()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("❌ Error: Anda harus menjalankan GUI ini dengan sudo (akses root) untuk mengontrol perangkat keras.")
        exit(1)

    root = tk.Tk()
    app = AES67Controller(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
