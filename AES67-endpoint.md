# 📘 Deployment Guide: brekithi AES67 Endpoint

## 1. Prerequisites
- **Hardware**: Raspberry Pi 4 Model B (Gigabit Ethernet), USB audio interface or I²S DAC/ADC HAT, stable 5 V/3 A PSU.  
- **Network**: Access to AES67‑compliant network with a grandmaster clock.  
- **Software**: PREEMPT‑RT kernel (RealtimePi or Ubuntu Server), `linuxptp`, `ffmpeg`, `pipewire`.

---

## 2. Installation

### 2.1 Base OS
```bash
sudo apt update && sudo apt upgrade -y
uname -a   # confirm PREEMPT RT kernel

