import os
import sys
import time
import signal
import threading
import subprocess
import customtkinter as ctk

# Ensure script is run as root for ptp4l/phc2sys
if os.geteuid() != 0:
    print("Error: This Pro-Audio Network setup requires root privileges.")
    print("Please run: sudo python3 ptp_option.py")
    sys.exit(1)

# --- GUI Theme Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AudioLanPTPApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AES67 PTP CONTROLLER - beta v1.0.0")
        self.geometry("750x650")
        self.minsize(600, 500)

        # Configure main grid to allow the console to expand
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Process Placeholders
        self.ptp4l_process = None
        self.phc2sys_process = None
        self.is_running = False

        self.build_ui()

    def build_ui(self):
        # --- 1. HEADER SECTION ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        # Main Title
        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text="AES67 PTP CONTROLLER",
            font=ctk.CTkFont(family="Roboto", size=28, weight="bold"),
            text_color="#e0e0e0"
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        # Credits & Version
        self.lbl_credit = ctk.CTkLabel(
            self.header_frame,
            text="beta v1.0.0 | by rekambergeraklab Yogyakarta-Indonesia",
            font=ctk.CTkFont(family="Roboto", size=12, slant="italic"),
            text_color="#888888"
        )
        self.lbl_credit.grid(row=1, column=0, sticky="w", pady=(0, 5))

        # Dynamic Status Badge
        self.lbl_status = ctk.CTkLabel(
            self.header_frame,
            text="● STOPPED",
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color="#666666"
        )
        self.lbl_status.grid(row=0, column=1, sticky="e")

        # Connection Status
        self.lbl_connection = ctk.CTkLabel(
            self.header_frame,
            text="Connection: OFFLINE",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="#888888"
        )
        self.lbl_connection.grid(row=1, column=1, sticky="e")

        # --- 2. CONFIGURATION PANEL ---
        self.config_frame = ctk.CTkFrame(self, corner_radius=8, fg_color="#242424", border_width=1, border_color="#333333")
        self.config_frame.grid(row=1, column=0, sticky="ew", padx=30, pady=10)
        self.config_frame.grid_columnconfigure(1, weight=1)

        # Network Interface
        self.lbl_interface = ctk.CTkLabel(self.config_frame, text="Network Interface", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_interface.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="w")

        self.entry_interface = ctk.CTkEntry(self.config_frame, placeholder_text="eno1", width=200)
        self.entry_interface.insert(0, "eno1")
        self.entry_interface.grid(row=0, column=1, padx=(10, 20), pady=(20, 10), sticky="w")

        # Node Role
        self.lbl_role = ctk.CTkLabel(self.config_frame, text="Node Role", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_role.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="w")

        self.role_var = ctk.StringVar(value="slave")
        self.seg_role = ctk.CTkSegmentedButton(
            self.config_frame,
            values=["Master", "Slave"],
            variable=self.role_var,
            width=200
        )
        self.seg_role.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="w")

        # Timestamp Mode
        self.lbl_mode = ctk.CTkLabel(self.config_frame, text="Timestamping", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_mode.grid(row=2, column=0, padx=(20, 10), pady=(10, 20), sticky="w")

        self.mode_var = ctk.StringVar(value="hw")
        self.seg_mode = ctk.CTkSegmentedButton(
            self.config_frame,
            values=["Hardware (hw)", "Software (sw)"],
            variable=self.mode_var,
            width=200
        )
        self.seg_mode.grid(row=2, column=1, padx=(10, 20), pady=(10, 20), sticky="w")

        # Action Buttons (Inside config frame, right-aligned)
        self.action_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.action_frame.grid(row=0, column=2, rowspan=3, padx=20, pady=20, sticky="e")

        self.btn_start = ctk.CTkButton(
            self.action_frame,
            text="START CLOCK",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1f6b35", hover_color="#144d24",
            height=40,
            command=self.start_clock
        )
        self.btn_start.pack(pady=(0, 10), fill="x")

        self.btn_stop = ctk.CTkButton(
            self.action_frame,
            text="STOP CLOCK",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8c2323", hover_color="#631717",
            height=40, state="disabled",
            command=self.stop_clock
        )
        self.btn_stop.pack(fill="x")

        # --- 3. CONSOLE / LOG SECTION ---
        self.log_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.log_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(10, 30))
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.lbl_console = ctk.CTkLabel(self.log_frame, text="SYNC LOG", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888888")
        self.lbl_console.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.console = ctk.CTkTextbox(
            self.log_frame,
            fg_color="#0d0d0d",
            text_color="#4af57a",
            font=ctk.CTkFont(family="Consolas", size=13),
            border_width=1, border_color="#333333",
            corner_radius=6
        )
        self.console.grid(row=1, column=0, sticky="nsew")

    def log(self, message):
        self.console.insert("end", message + "\n")
        self.console.see("end")

    def read_process_output(self, process, prefix):
        try:
            for line in iter(process.stdout.readline, b''):
                if line:
                    self.log(f"[{prefix}] {line.decode('utf-8').strip()}")
        except ValueError:
            pass

    def generate_conf(self, role, mode):
        conf_file = "/etc/ptp4l_custom.conf"
        self.log(f"[*] Generating configuration file at {conf_file}...")

        slave_only = "0" if role == "master" else "1"
        ts_mode = "hardware" if mode == "hardware (hw)" else "software"

        conf_content = f"""[global]
slaveOnly             {slave_only}
domainNumber          0
network_transport     UDPv4
time_stamping         {ts_mode}
"""
        with open(conf_file, "w") as f:
            f.write(conf_content)

        return conf_file

    def start_clock(self):
        if self.is_running:
            return

        interface = self.entry_interface.get().strip()
        role = self.role_var.get().lower()
        mode = self.mode_var.get().lower()

        if not interface:
            self.log("[!] Error: Interface cannot be empty.")
            return

        # Update State & UI
        self.is_running = True
        self.lbl_status.configure(text="● RUNNING", text_color="#4af57a")
        self.lbl_connection.configure(text=f"Connection: ACTIVE ({interface})", text_color="#4af57a")

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.entry_interface.configure(state="disabled")
        self.seg_role.configure(state="disabled")
        self.seg_mode.configure(state="disabled")

        self.console.delete("1.0", "end")
        self.log("=== Initializing AES67 PTP Service ===")
        self.log(f"[*] Interface: {interface} | Role: {role.upper()} | Mode: {mode.upper()}")

        # 1. Generate Config
        conf_file = self.generate_conf(role, mode)

        # 2. Start ptp4l
        ptp4l_cmd = ["ptp4l", "-i", interface, "-f", conf_file, "-m"]
        if mode == "hardware (hw)":
            ptp4l_cmd.append("-H")
        else:
            ptp4l_cmd.append("-S")

        self.log(f"[*] Starting: {' '.join(ptp4l_cmd)}")
        self.ptp4l_process = subprocess.Popen(ptp4l_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        threading.Thread(target=self.read_process_output, args=(self.ptp4l_process, "PTP4L"), daemon=True).start()

        # 3. Start phc2sys if Hardware Mode
        if mode == "hardware (hw)":
            self.log("[*] Hardware mode detected. Waiting 2 seconds before starting phc2sys...")
            self.after(2000, lambda: self.start_phc2sys(interface, role))
        else:
            self.log("[*] Software mode: phc2sys skipped (using CLOCK_REALTIME directly).")

    def start_phc2sys(self, interface, role):
        if not self.is_running: return

        if role == "master":
            self.log("[*] Synchronizing NIC to System Clock (CLOCK_REALTIME -> NIC)...")
            phc2sys_cmd = ["phc2sys", "-c", interface, "-s", "CLOCK_REALTIME", "-w", "-m"]
        else:
            self.log("[*] Synchronizing System Clock to NIC (NIC -> CLOCK_REALTIME)...")
            phc2sys_cmd = ["phc2sys", "-s", interface, "-c", "CLOCK_REALTIME", "-w", "-m"]

        self.log(f"[*] Starting: {' '.join(phc2sys_cmd)}")
        self.phc2sys_process = subprocess.Popen(phc2sys_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

        threading.Thread(target=self.read_process_output, args=(self.phc2sys_process, "PHC2SYS"), daemon=True).start()

    def stop_clock(self):
        if not self.is_running:
            return

        self.log("\n=== Stopping AES67 PTP Service ===")

        if self.phc2sys_process:
            self.log("[*] Terminating phc2sys...")
            self.phc2sys_process.terminate()
            self.phc2sys_process.wait()
            self.phc2sys_process = None

        if self.ptp4l_process:
            self.log("[*] Terminating ptp4l...")
            self.ptp4l_process.terminate()
            self.ptp4l_process.wait()
            self.ptp4l_process = None

        # Reset State & UI
        self.is_running = False
        self.log("[*] All processes stopped.")

        self.lbl_status.configure(text="● STOPPED", text_color="#666666")
        self.lbl_connection.configure(text="Connection: OFFLINE", text_color="#888888")

        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.entry_interface.configure(state="normal")
        self.seg_role.configure(state="normal")
        self.seg_mode.configure(state="normal")

    def on_closing(self):
        self.stop_clock()
        self.destroy()

if __name__ == "__main__":
    app = AudioLanPTPApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
