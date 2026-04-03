`markdown

📘 Deployment Guide: brekithi AES67 Endpoint

1. Prerequisites
- Hardware: Raspberry Pi 4 Model B (Gigabit Ethernet), USB audio interface or I²S DAC/ADC HAT, stable 5 V/3 A PSU.  
- Network: Access to AES67‑compliant network with a grandmaster clock.  
- Software: PREEMPT‑RT kernel (RealtimePi or Ubuntu Server), linuxptp, ffmpeg, pipewire.

---

2. Installation

2.1 Base OS
`bash
sudo apt update && sudo apt upgrade -y
uname -a   # confirm PREEMPT RT kernel
`

2.2 Kernel & Performance Tuning
`bash
sudo apt install cpufrequtils
sudo cpufreq-set -g performance
`
Optional /boot/cmdline.txt tuning:
`
isolcpus=2,3 nohzfull=2,3 rcunocbs=2,3
`

2.3 Required Packages
`bash
sudo apt install linuxptp ffmpeg pipewire pipewire-audio-client-libraries
`

---

3. Configuration

3.1 PTP Synchronization (Follower Mode)
`bash
ptp4l -i eth0 -m -S -s
phc2sys -s CLOCKREALTIME -c CLOCKREALTIME -O 0
`

3.2 Audio Streaming (48 kHz, 1024 buffer)
`bash
ffmpeg -f alsa -i hw:1 -ac 2 -ar 48000 -audiobuffersize 1024 \
       -f rtp rtp://239.69.22.11:5004
`

PipeWire config (/etc/pipewire/pipewire.conf):
`ini
default.clock.rate = 48000
default.clock.quantum = 1024
default.clock.min-quantum = 1024
default.clock.max-quantum = 1024
`

3.3 SDP File
/home/pi/aes67.sdp:
`sdp
v=0
o=- 0 0 IN IP4 239.69.22.11
s=brekithi AES67 Stream
c=IN IP4 239.69.22.11/32
t=0 0
m=audio 5004 RTP/AVP 96
a=rtpmap:96 L16/48000/2
`

---

4. Auto‑Run Setup

4.1 Startup Script /usr/local/bin/aes67.sh
`bash

!/bin/bash
LOGDIR=/var/log/aes67
mkdir -p $LOGDIR

ptp4l -i eth0 -m -S -s >> $LOGDIR/ptp4l.log 2>&1 &
phc2sys -s CLOCKREALTIME -c CLOCKREALTIME -O 0 >> $LOGDIR/phc2sys.log 2>&1 &
ffmpeg -f alsa -i hw:1 -ac 2 -ar 48000 -audiobuffersize 1024 \
       -f rtp rtp://239.69.22.11:5004 >> $LOGDIR/ffmpeg.log 2>&1 &
`

`bash
sudo chmod +x /usr/local/bin/aes67.sh
`

4.2 Systemd Unit /etc/systemd/system/aes67.service
`ini
[Unit]
Description=brekithi AES67 Endpoint Follower Service
After=network.target sound.target

[Service]
ExecStart=/usr/local/bin/aes67.sh
Restart=always
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
`

Enable service:
`bash
sudo systemctl daemon-reload
sudo systemctl enable aes67.service
sudo systemctl start aes67.service
`

---

5. Maintenance

5.1 Log Rotation /etc/logrotate.d/aes67
`ini
/var/log/aes67/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 pi pi
}
`

5.2 Health‑Check Script /usr/local/bin/aes67-health.sh
`bash

!/bin/bash
LOGDIR=/var/log/aes67
REPORT=$LOGDIR/health_report.txt

echo "=== brekithi Health Report $(date) ===" > $REPORT

OFFSET=$(grep "offset" $LOGDIR/ptp4l.log | tail -n1)
echo "PTP Offset: $OFFSET" >> $REPORT

CLOCK=$(tail -n1 $LOGDIR/phc2sys.log)
echo "Clock Sync: $CLOCK" >> $REPORT

STREAM=$(tail -n1 $LOGDIR/ffmpeg.log)
echo "Audio Stream: $STREAM" >> $REPORT

echo "Report saved to $REPORT"
`

`bash
sudo chmod +x /usr/local/bin/aes67-health.sh
`

Add cron job (crontab -e):
`
0     /usr/local/bin/aes67-health.sh
`

---

6. Monitoring

- PTP offsets → tail -f /var/log/aes67/ptp4l.log  
- Clock sync → tail -f /var/log/aes67/phc2sys.log  
- Audio health → tail -f /var/log/aes67/ffmpeg.log  
- Systemd journal → journalctl -u aes67.service -f  
- Health reports → /var/log/aes67/health_report.txt  

---

7. Troubleshooting

7.1 Jitter Spikes
- Symptom: PTP offset jumps >500 µs.  
- Fix:  
  - Ensure Pi is on wired Gigabit Ethernet (no Wi‑Fi).  
  - Use isolcpus to dedicate cores.  
  - Check for background processes consuming CPU.

7.2 Buffer Underruns
- Symptom: Audio dropouts in FFmpeg log.  
- Fix:  
  - Increase -audiobuffersize (e.g., 2048).  
  - Verify USB audio interface stability.  
  - Use PipeWire with fixed quantum.

7.3 Sync Drift
- Symptom: Clock gradually drifts from grandmaster.  
- Fix:  
  - Confirm phc2sys is running.  
  - Check offset values in ptp4l.log.  
  - Restart service if drift persists.

7.4 Service Fails at Boot
- Symptom: aes67.service not active.  
- Fix:  
  - Run systemctl status aes67.service.  
  - Check logs in /var/log/aes67/.  
  - Ensure script is executable (chmod +x).

---

✅ Final Outcome
- brekithi boots directly into AES67 follower mode.  
- Streams stereo RTP at 48 kHz, 1024 buffer.  
- Syncs to grandmaster clock with software timestamping.  
- Logs rotate daily, health reports generated hourly.  
- Troubleshooting section ensures field engineers can resolve common issues.  
- Fully autonomous, clean, and self‑maintaining endpoint.
`

---
