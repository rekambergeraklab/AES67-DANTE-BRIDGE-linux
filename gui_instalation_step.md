To add the professional GUI to your system, we need to create the `.py` file and then link it to a desktop launcher. This ensures you can open the **rekambergerak** dashboard just like any other professional audio software.

### Step 1: Create the Python File
1. Open your terminal.
2.    ```bash
   sudo apt update && sudo apt install python3-tk -y
   ```
3. Create and edit the file using the following command:
   ```bash
   nano ~/aes67_gui.py
   ```
4. Paste the **entire Python code** we developed (the one with the Slogan, Credit, and Language options) into the editor.
5. Save and exit (Press `Ctrl+O`, then `Enter`, then `Ctrl+X`).

---

### Step 2: Grant Hardware Access
Because the GUI controls high-precision hardware clocks, it needs special permissions to run without crashing. Run these commands:

```bash
# Allow the root user to draw the window on your current screen
xhost +si:localuser:root

# Ensure the command runs every time you log in
echo "xhost +si:localuser:root > /dev/null 2>&1" >> ~/.bashrc
```

---

### Step 3: Create the Desktop Shortcut (The Launcher)
This step creates the icon in your "Show Applications" menu so you don't have to use the terminal anymore.

```bash
# Get your username and script path
REAL_USER=${SUDO_USER:-$USER}
SCRIPT_PATH="/home/$REAL_USER/aes67_gui.py"

# Create the applications folder
mkdir -p /home/$REAL_USER/.local/share/applications

# Create the .desktop file
cat << EOF > /home/$REAL_USER/.local/share/applications/aes67-bridge.desktop
[Desktop Entry]
Version=1.0
Name=AES67 Bridge
GenericName=Audio Network Controller
Comment=rekambergerak Yogyakarta-Indonesia
# pkexec handles the password prompt; env DISPLAY ensures the GUI appears
Exec=pkexec env DISPLAY=:0 XAUTHORITY=/run/user/$(id -u)/gdm/Xauthority /usr/bin/python3 $SCRIPT_PATH
Icon=audio-card
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
StartupNotify=true
EOF

# Make the shortcut executable
chmod +x /home/$REAL_USER/.local/share/applications/aes67-bridge.desktop
update-desktop-database ~/.local/share/applications
```

---

### Step 4: Launching for the First Time
1. Click the **9-dot "Show Applications"** icon at the bottom left of your Ubuntu screen.
2. Search for **"AES67"**.
3. Click the **AES67 Bridge** icon.
4. **Enter your password** in the system pop-up.
5. The **rekambergerak** dashboard will appear!

---

### ⚠️ Pro-Tip for Ubuntu 24.04 (Wayland vs Xorg)
Ubuntu 24.04 uses **Wayland** by default, which is very strict about "Root" apps showing a GUI. If your password window appears but the GUI does not open:

1. **Log Out** of your computer.
2. On the login screen, click your name.
3. Before typing your password, click the **small gear icon** in the bottom-right corner.
4. Select **"Ubuntu on Xorg"**.
5. Log in. 

Everything will now run perfectly. **"Dibalik kesulitan, ada kemudahan. !"** Selamat berkarya, **rekambergerak**!
