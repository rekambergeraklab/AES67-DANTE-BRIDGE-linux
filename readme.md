This is the professional **README.md** file for your project. It is written in clear, technical yet accessible English, perfect for GitHub or your internal studio documentation.

---

# AES67 Dante Bridge 8-Channel
### Developed by rekambergerak | Yogyakarta, Indonesia
> *"Dibalik kesulitan, ada kemudahan. !"*

A professional-grade Linux audio bridge that connects **Ubuntu 24.04** to a **Dante/AES67** network using the **Intel eno1** hardware clock (PTPv2). This system is designed for high-fidelity studio recording with 8-channel I/O and ultra-low jitter.

---

## 📋 Table of Contents
1. [Prerequisites](#-prerequisites)
2. [Technical Specifications](#-technical-specifications)
3. [Installation](#-installation)
4. [Operation Manual](#-operation-manual)
5. [Troubleshooting](#-troubleshooting)

---

## ⚡ Prerequisites
To ensure stable audio without dropouts, your network must meet these criteria:
* **Hardware:** Intel Network Interface (e.g., `eno1`) with Hardware PTP support.
* **Cable:** Minimum Cat5e (Cat6 recommended for jitter < 500ns).
* **Switch:** Gigabit Switch with **IGMP Snooping** enabled (to manage multicast traffic).
* **Connection:** Wired LAN connection only. **Do not use Wi-Fi.**

---

## 🛠 Technical Specifications
| Parameter | Specification |
| :--- | :--- |
| **Sample Rate** | 48000 Hz |
| **Channels** | 8 Input (RX) / 8 Output (TX) |
| **Packet Time ($P_{time}$)** | 1.0 ms (Dante/AES67 Standard) |
| **Clocking** | PTPv2 (IEEE 1588-2008) Hardware Timestamping |
| **Audio Engine** | PipeWire with RTP/SAP Modules |
| **Latency** | Sub-5ms internal engine latency |

---

## 🚀 Installation
1. **Install Dependencies:**
   ```bash
   sudo apt update && sudo apt install python3-tk -y
   ```
2. **Configure Hardware Permissions:**
   Grant PipeWire access to the hardware clock:
   ```bash
   echo 'SUBSYSTEM=="ptp", ATTR{clock_name}=="eno1", GROUP="audio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-ptp-eno1.rules
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```
3. **Run the Setup Script:**
   Use the provided `install_AES67_Dante.sh` to generate the PipeWire configuration and the Desktop Shortcut.

---

## 🎮 Operation Manual

### Launching the Session
1. Open the Ubuntu App Menu (Super/Windows key).
2. Search for **"AES67 Bridge"**.
3. A system password prompt will appear; enter your **Root/Sudo password**.
4. Set the **Language** and **Clock Mode** (Slave is recommended for most setups).
5. Click **[START ENGINE]**.

### Monitoring
* **Status Indicator:** Must turn **GREEN (ONLINE)**.
* **Master Offset (Jitter):** Ideal values are **< 500 ns**. If it exceeds 2000 ns, check your network cables.
* **Routing:** Use **Dante Controller** on a secondary PC to patch the 8 channels to your Mixer or DAW.

---

## 🔧 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **GUI does not appear** | Wayland Security | Log out and select **"Ubuntu on Xorg"** at the login screen gear icon. |
| **"Host is Down" Error** | No IP Address | Assign a manual IP to `eno1` in Ubuntu Network Settings. |
| **No audio in Dante** | Multicast Blocked | Run: `sudo ip route add 224.0.0.0/4 dev eno1` and disable Firewall. |
| **Crackling/Pops** | High Jitter | Replace LAN cable with Cat6. Ensure only one device is "Preferred Master". |
| **Nothing happens on Start** | Interface Down | Run: `sudo ip link set eno1 up` in the terminal. |

---

## 🚦 Pre-Session Checklist
- [ ] LAN Cable (Cat6) connected to Intel port.
- [ ] Dashboard shows **GREEN / LOCKED**.
- [ ] Jitter is stable below **500 ns**.
- [ ] Devices patched in **Dante Controller**.
- [ ] DAW (Reaper/Ardour) shows active signal levels.

---

**Developed by rekambergerak**
*Yogyakarta, Indonesia - Precision Audio Engineering.*
