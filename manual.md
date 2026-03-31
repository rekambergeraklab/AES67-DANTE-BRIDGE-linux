This is the comprehensive technical documentation for the **AES67 / Dante Bridge** system, tailored for the **rekambergerak** studio in Yogyakarta, Indonesia.

---

## 📘 System Overview
The **AES67 Dante Bridge** is a professional-grade software solution that allows a Linux-based workstation (Ubuntu 24.04) to act as an 8-channel audio interface within a Dante network. It leverages **Hardware PTP (Precision Time Protocol)** on the Intel `eno1` interface to achieve sub-microsecond synchronization.

---

## 1. Network Requirements & Topology
For high-performance AoIP (Audio over IP), the network infrastructure must be optimized for multicast traffic and clock synchronization.

### Infrastructure Standards:
* **Interface:** Physical Intel Gigabit Ethernet (e.g., `i219-V` or `i210`).
* **Cable:** Shielded **Cat6** is highly recommended to minimize EMI/RFI interference.
* **Switching:** A managed or "Green-Ethernet-Disabled" switch with **IGMP Snooping** and **QoS (Quality of Service)** prioritized for DSCP 56 (PTP) and DSCP 46 (Audio).



---

## 2. Technical Specifications
The bridge is locked to industry-standard parameters to ensure 100% compatibility with Audinate Dante hardware.

| Feature | Specification |
| :--- | :--- |
| **Clock Protocol** | PTPv2 (IEEE 1588-2008) L2/UDP |
| **Audio Protocol** | RTP (Real-time Transport Protocol) |
| **Sampling Rate** | 48 kHz (Studio Standard) |
| **Bit Depth** | 24-bit PCM / 32-bit Float |
| **Channel Count** | 8 Inputs (RX) / 8 Outputs (TX) |
| **Packet Time** | 1.0 ms (48 samples per packet) |
| **Discovery** | SAP (Session Announcement Protocol) via Multicast |

---

## 3. Installation & System Setup

### Step 1: Core Dependencies
Install the required PTP stack and audio engine components:
`sudo apt update && sudo apt install linuxptp pipewire python3-tk`

### Step 2: Hardware Clock Access (Udev)
To allow the GUI and PipeWire to interact with the hardware clock without constant permission errors:
`echo 'SUBSYSTEM=="ptp", ATTR{clock_name}=="eno1", GROUP="audio", MODE="0660"' | sudo tee /etc/udev/rules.d/99-ptp-eno1.rules`

### Step 3: Multicast Routing
Linux requires an explicit route for multicast traffic (used by Dante for discovery and clocking):
`sudo ip route add 224.0.0.0/4 dev eno1`

---

## 4. GUI User Manual
The **rekambergerak Controller** is designed to be a "Mission Control" for your audio network.

### Control Panel (Left)
* **Language Menu:** Toggle between English and Bahasa Indonesia.
* **Clock Management:**
    * **Follower (SlaveOnly):** Forces the PC to sync to an existing Dante Master (e.g., a Digital Mixer).
    * **Auto-Negotiate:** Allows the PC to become the Grandmaster if no other clock is present.
* **Jitter Monitor:** Displays the **Master Offset** in nanoseconds. 
    * **Green:** < 500ns (Broadcast Quality).
    * **Amber:** 500ns - 2000ns (Stable, but check cables).
    * **Red:** > 2000ns (Sync danger; audio may pop).

### Routing Engine (Right)
* **Start/Stop:** Initializes the three-stage boot: PTP Clock -> System Sync -> PipeWire Engine.
* **System Log:** A real-time terminal output for diagnosing network handshakes and clock lock-in.



---

## 5. Troubleshooting Guide

| Symptom | Probable Cause | Action |
| :--- | :--- | :--- |
| **Host is Down** | Interface has no IP | Assign a static IP or check DHCP connection on `eno1`. |
| **GUI won't open** | Wayland Security | Switch to **Ubuntu on Xorg** at the login screen. |
| **High Jitter (>5k ns)** | Software Syncing | Ensure you are using the hardware port (`eno1`) and not a virtual bridge. |
| **Audio Distortion** | Clock Mismatch | Ensure the Sample Rate in Dante Controller matches (48kHz). |

---

## 🚦 Pre-Session Checklist
1.  [ ] **Hardware Check:** Verify Cat6 cable is securely locked into the Intel port.
2.  [ ] **Identity Check:** Ensure `eno1` has a valid IP address in the studio range.
3.  [ ] **Clock Lock:** Wait for the Jitter readout to stabilize below **500ns**.
4.  [ ] **Patching:** Confirm all 8 channels are "green" in **Dante Controller**.

---
> **"Dibalik kesulitan, ada kemudahan. !"**
> *Developed by rekambergerak - Yogyakarta, Indonesia.*
