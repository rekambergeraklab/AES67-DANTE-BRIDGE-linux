#!/bin/bash

# ==============================================================================
# Linux AES67 (Dante) PipeWire Installer - ON-DEMAND VERSION
# Target: eno1 Hardware PTP | 8 Channel TX/RX (AUX 1-8) | 1ms Packet Time
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run this script with sudo."
  exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)

echo "🚀 Starting On-Demand AES67 Setup for user: $REAL_USER"
echo "------------------------------------------------------------"

# ==============================================================================
# STEP 1: DEPENDENCIES & SYSTEM PREP
# ==============================================================================
echo "⏳ Step 1: Installing tools and disabling conflicting time services..."

apt-get update -yqq
apt-get install -yqq linuxptp

# Disable NTP/Timesyncd so it doesn't fight our PTP hardware clock
systemctl stop systemd-timesyncd 2>/dev/null
systemctl disable systemd-timesyncd 2>/dev/null

# Make sure old background services are dead (if you ran the previous script)
systemctl stop ptp4l-eno1 phc2sys-eno1 2>/dev/null
systemctl disable ptp4l-eno1 phc2sys-eno1 2>/dev/null

echo "✅ Step 1 Complete: System is ready for manual clocking."

# ==============================================================================
# STEP 2: PERMISSION SETUP (Permanent Udev Rules)
# ==============================================================================
echo "⏳ Step 2: Granting PipeWire permanent access to eno1 hardware clocks..."

usermod -aG audio $REAL_USER

cat << 'EOF' > /etc/udev/rules.d/99-ptp-eno1.rules
SUBSYSTEM=="ptp", ATTR{clock_name}=="eno1", GROUP="audio", MODE="0660"
EOF

udevadm control --reload-rules
udevadm trigger

echo "✅ Step 2 Complete: Hardware clock permissions secured."

# ==============================================================================
# STEP 3: AES67 8-CHANNEL CONFIGURATION (Fixed Protocols & SAP Discovery)
# ==============================================================================
echo "⏳ Step 3: Generating 8-Channel PipeWire AES67 Configuration..."

PW_DIR="$USER_HOME/.config/pipewire"
PW_FILE="$PW_DIR/aes67-8ch.conf"

sudo -u $REAL_USER mkdir -p $PW_DIR

cat << 'EOF' > $PW_FILE
# --- CORE ENGINE REQUIREMENTS ---
# These are mandatory to connect to your existing desktop audio session
context.spa-libs = {
    audio.convert.* = audioconvert/libspa-audioconvert
    support.* = support/libspa-support
}

context.modules = [
    { name = libpipewire-module-protocol-native }
    { name = libpipewire-module-client-node }
    { name = libpipewire-module-adapter }

    # --- AES67 RECEIVER (RX VIA SAP) ---
    # Automatically discovers Dante streams on the network and creates nodes for them
    { name = libpipewire-module-rtp-sap
        args = {
            local.ifname = "eno1"
        }
    }

    # --- 8-CHANNEL AES67 TRANSMITTER (TX) ---
    { name = libpipewire-module-rtp-sink
        args = {
            local.ifname = "eno1"
            sess.media = "audio"
            audio.rate = 48000
            audio.channels = 8
            audio.position = [ AUX0 AUX1 AUX2 AUX3 AUX4 AUX5 AUX6 AUX7 ]
            rtp.ptime = 1
            node.name = "AES67_TX_8ch"
            node.description = "AES67 Transmit (Channels 1-8)"
        }
    }
]
EOF

chown $REAL_USER:$REAL_USER $PW_FILE
echo "✅ Step 3 Complete: PipeWire config generated at $PW_FILE"

# ==============================================================================
# STEP 4: GENERATE THE ON-DEMAND LAUNCHER SCRIPT
# ==============================================================================
echo "⏳ Step 4: Building the Session Launcher Script..."

LAUNCHER="$USER_HOME/start-aes67-session.sh"

cat << EOF > $LAUNCHER
#!/bin/bash

if [ "\$EUID" -ne 0 ]; then
  echo "❌ Please run this session script with sudo: sudo ./start-aes67-session.sh"
  exit 1
fi

echo "========================================="
echo " 🎛️  STARTING AES67 / DANTE SESSION"
echo "========================================="

echo "⏳ Locking eno1 to the network grandmaster..."
ptp4l -i eno1 -H -S -q &
PTP_PID=\$!
sleep 2

echo "⏳ Syncing Ubuntu system clock to eno1..."
phc2sys -s eno1 -c CLOCK_REALTIME -w -q &
PHC_PID=\$!
sleep 3

echo "🎵 Launching 8-Channel PipeWire Engine..."
# Explicitly set XDG_RUNTIME_DIR to ensure PipeWire connects to the user's socket
sudo -u $REAL_USER XDG_RUNTIME_DIR=/run/user/\$(id -u $REAL_USER) pipewire -c $PW_FILE &
PW_PID=\$!

echo "========================================="
echo " ✅ SESSION ACTIVE (Press Ctrl+C to stop)"
echo "========================================="

trap 'echo ""; echo "🛑 Shutting down AES67 session..."; kill \$PTP_PID \$PHC_PID \$PW_PID 2>/dev/null; echo "Done."; exit' INT

wait
EOF

chown $REAL_USER:$REAL_USER $LAUNCHER
chmod +x $LAUNCHER

echo "✅ Step 4 Complete: Launcher created at $LAUNCHER"
echo "------------------------------------------------------------"
echo "🎉 INSTALLATION SUCCESSFUL!"
echo ""
echo "Whenever you want to use Dante/AES67, just run this command:"
echo "   sudo ~/start-aes67-session.sh"
echo ""
echo "Press Ctrl+C in that terminal when you are done working to turn everything off."
echo "============================================================"
