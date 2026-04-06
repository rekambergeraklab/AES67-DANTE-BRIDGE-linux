#!/bin/bash

# ==============================================================================
# Linux AES67 (Dante) PipeWire Installer - ON-DEMAND VERSION
# Target: eno1 HARDWARE PTP | 8 Channel TX/RX | Master/Slave Option
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run this script with sudo."
  exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)
NIC="eno1"

echo "🚀 Starting On-Demand AES67 Setup for user: $REAL_USER"
echo "------------------------------------------------------------"

# ==============================================================================
# STEP 1: DEPENDENCIES & SYSTEM PREP
# ==============================================================================
echo "⏳ Step 1: Installing tools and disabling conflicting time services..."

apt-get update -yqq
apt-get install -yqq linuxptp

# Disable NTP/Timesyncd so it doesn't fight our PTP clock
systemctl stop systemd-timesyncd 2>/dev/null
systemctl disable systemd-timesyncd 2>/dev/null

# Make sure old background services are dead
systemctl stop ptp4l-$NIC phc2sys-$NIC 2>/dev/null
systemctl disable ptp4l-$NIC phc2sys-$NIC 2>/dev/null

echo "✅ Step 1 Complete: System is ready for manual hardware clocking."

# ==============================================================================
# STEP 2: PERMISSION SETUP (Permanent Udev Rules)
# ==============================================================================
echo "⏳ Step 2: Granting PipeWire permanent access to $NIC clocks..."

usermod -aG audio $REAL_USER

cat << EOF > /etc/udev/rules.d/99-ptp-$NIC.rules
SUBSYSTEM=="ptp", ATTR{clock_name}=="$NIC", GROUP="audio", MODE="0660"
EOF

udevadm control --reload-rules
udevadm trigger

echo "✅ Step 2 Complete: Clock permissions secured."

# ==============================================================================
# STEP 3: AES67 8-CHANNEL CONFIGURATION
# ==============================================================================
echo "⏳ Step 3: Generating 8-Channel PipeWire AES67 Configuration..."

PW_DIR="$USER_HOME/.config/pipewire"
PW_FILE="$PW_DIR/aes67-8ch.conf"

sudo -u $REAL_USER mkdir -p $PW_DIR

cat << EOF > $PW_FILE
# --- CORE ENGINE REQUIREMENTS ---
context.spa-libs = {
    audio.convert.* = audioconvert/libspa-audioconvert
    support.* = support/libspa-support
}

context.modules = [
    { name = libpipewire-module-protocol-native }
    { name = libpipewire-module-client-node }
    { name = libpipewire-module-adapter }

    # --- AES67 DYNAMIC RECEIVER (RX VIA SAP) ---
    { name = libpipewire-module-rtp-sap
        args = {
            local.ifname = "$NIC"
            sap.ip = "239.255.255.255"
            sap.port = 9875
        }
    }

    # --- 8-CHANNEL AES67 TRANSMITTER (TX / OUTPUT) ---
    { name = libpipewire-module-rtp-sink
        args = {
            local.ifname = "$NIC"
            source.ip = "0.0.0.0"
            destination.ip = "239.69.0.1"
            destination.port = 5004
            sess.media = "audio"
            audio.rate = 48000
            audio.format = "S24BE"
            audio.channels = 8
            audio.position = [ AUX0 AUX1 AUX2 AUX3 AUX4 AUX5 AUX6 AUX7 ]
            rtp.ptime = 1
            sess.sap.announce = true
            sap.ip = "239.255.255.255"
            sap.port = 9875
            node.name = "AES67_TX_8ch"
            node.description = "AES67 Transmit (Channels 1-8)"
            sess.name = "Linux AES67 TX"
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

# Note: Variables escaping (\$) ensures they run in the launcher, not during install
cat << EOF > $LAUNCHER
#!/bin/bash

if [ "\$EUID" -ne 0 ]; then
  echo "❌ Please run this session script with sudo: sudo ./start-aes67-session.sh"
  exit 1
fi

echo "========================================="
echo " 🎛️  STARTING AES67 / DANTE SESSION"
echo "========================================="

echo "⏳ PTP Role selection for $NIC (Hardware Mode):"
echo "   1) Master (provide clock to network)"
echo "   2) Slave  (sync clock from grandmaster)"
read -rp "➡️  Enter 1 or 2 [default: 2]: " PTP_ROLE_INPUT

# Route Multicast Traffic correctly
echo "⏳ Configuring Multicast IP Routing..."
ip route add 224.0.0.0/4 dev $NIC 2>/dev/null || true

if [[ "\$PTP_ROLE_INPUT" == "1" ]]; then
    echo "⏳ Starting PTP in MASTER mode (Hardware Timestamping)..."
    # -H for hardware, no -s so it acts as master
    ptp4l -i $NIC -H -q &
    PTP_PID=\$!
    sleep 2
    
    echo "⏳ Syncing $NIC hardware clock FROM Ubuntu system clock..."
    # -s is source, -c is destination
    phc2sys -s CLOCK_REALTIME -c $NIC -w -q &
    PHC_PID=\$!
else
    echo "⏳ Starting PTP in SLAVE mode (Hardware Timestamping)..."
    # -H for hardware, -s to force slave to grandmaster
    ptp4l -i $NIC -H -s -q &
    PTP_PID=\$!
    sleep 2
    
    echo "⏳ Syncing Ubuntu system clock FROM $NIC hardware clock..."
    phc2sys -s $NIC -c CLOCK_REALTIME -w -q &
    PHC_PID=\$!
fi

# Wait for hardware clocks to settle phase
echo "⏳ Waiting 10 seconds for PTP clocks to stabilize..."
sleep 10

echo "🎵 Launching 8-Channel PipeWire Engine..."
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
echo "Run this command to start your session:"
echo "   sudo ~/start-aes67-session.sh"
echo "============================================================"
