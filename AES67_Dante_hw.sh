#!/bin/bash

# ==============================================================================
# Linux AES67 (Dante) PipeWire Installer - ON-DEMAND VERSION
# Interactive: NIC selection, hardware/software PTP mode
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run this script with sudo."
  exit 1
fi

echo ""
echo "============================================="
echo " AES67 (Dante) PipeWire On-Demand Installer"
echo "============================================="
echo ""

# ------------------------------------------------------------------------------
# NETWORK INTERFACE SELECTION
# ------------------------------------------------------------------------------

echo ""
echo "Available network interfaces on this system:"
ip -o link show | awk -F': ' '{print $2}' | grep -v "lo"
echo ""

read -rp "➡️  Enter the network interface you want to use for AES67 (e.g., eno1, eth0, etc.): " SELECTED_NIC
if [[ -z "$SELECTED_NIC" ]]; then
    echo "❌ Error: Network interface must not be empty!"
    exit 1
fi

# Validate the interface exists
if ! ip link show "$SELECTED_NIC" > /dev/null 2>&1; then
    echo "❌ Error: Network interface '$SELECTED_NIC' not found!"
    exit 1
fi

# ------------------------------------------------------------------------------
# HARDWARE/SOFTWARE MODE SELECTION
# ------------------------------------------------------------------------------

echo ""
echo "PTP (clock sync) mode options:"
echo "1) Hardware (recommended, precise, uses PTP hardware clock syncing)"
echo "2) Software  (fallback, less precise, NTP/system clock only)"
read -rp "➡️  Enter 1 for hardware or 2 for software mode: " PTP_MODE_INPUT

if [[ "$PTP_MODE_INPUT" == "1" ]]; then
    PTP_MODE="hardware"
elif [[ "$PTP_MODE_INPUT" == "2" ]]; then
    PTP_MODE="software"
else
    echo "❌ Error: Invalid selection"
    exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)

echo ""
echo "------------------------------------------------------------"
echo "Summary:"
echo "  🎚️  Network Interface : $SELECTED_NIC"
echo "  ⏱️  PTP Mode          : $PTP_MODE"
echo "  👤  Target User       : $REAL_USER"
echo "------------------------------------------------------------"
echo ""

# ==============================================================================
# STEP 1: DEPENDENCIES & SYSTEM PREP
# ==============================================================================
echo "⏳ Step 1: Installing tools and disabling conflicting time services..."

if [[ "$PTP_MODE" == "hardware" ]]; then
    apt-get update -yqq
    apt-get install -yqq linuxptp
fi

systemctl stop systemd-timesyncd 2>/dev/null
systemctl disable systemd-timesyncd 2>/dev/null

# Clean up previous custom PTP services
systemctl stop ptp4l-"$SELECTED_NIC" phc2sys-"$SELECTED_NIC" 2>/dev/null
systemctl disable ptp4l-"$SELECTED_NIC" phc2sys-"$SELECTED_NIC" 2>/dev/null

echo "✅ Step 1 Complete: System is ready."

# ==============================================================================
# STEP 2: PERMISSION SETUP (Udev Rules for Hardware Mode)
# ==============================================================================
if [[ "$PTP_MODE" == "hardware" ]]; then
    echo "⏳ Step 2: Granting PipeWire permanent access to $SELECTED_NIC hardware clocks..."

    usermod -aG audio $REAL_USER

    cat << EOF > /etc/udev/rules.d/99-ptp-${SELECTED_NIC}.rules
SUBSYSTEM=="ptp", ATTR{clock_name}=="${SELECTED_NIC}", GROUP="audio", MODE="0660"
EOF

    udevadm control --reload-rules
    udevadm trigger

    echo "✅ Step 2 Complete: Hardware clock permissions secured."
else
    echo "⏳ Step 2: Skipped udev rules (software mode; no hardware PTP involved)."
fi

# ==============================================================================
# STEP 3: AES67 8-CHANNEL CONFIG (SAP TX/RX)
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

    # AES67 RECEIVER (RX VIA SAP)
    { name = libpipewire-module-rtp-sap
        args = {
            local.ifname = "${SELECTED_NIC}"
        }
    }

    # 8-CHANNEL AES67 TRANSMITTER (TX & SAP ANNOUNCE)
    { name = libpipewire-module-rtp-sink
        args = {
            local.ifname = "${SELECTED_NIC}"
            sess.media = "audio"
            audio.rate = 48000
            audio.channels = 8
            audio.position = [ AUX0 AUX1 AUX2 AUX3 AUX4 AUX5 AUX6 AUX7 ]
            rtp.ptime = 1
            node.name = "AES67_TX_8ch"
            node.description = "AES67 Transmit (Channels 1-8)"
            sap.enabled = true
            sap.ip = "239.255.255.255"
            sap.port = 9875
            sess.name = "AES67 TX from $REAL_USER"
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

EOF

if [[ "$PTP_MODE" == "hardware" ]]; then
cat << EOF >> $LAUNCHER
echo "⏳ Locking ${SELECTED_NIC} to the network grandmaster (Hardware PTP)..."
ptp4l -i ${SELECTED_NIC} -H -S -q &
PTP_PID=\$!
sleep 2

echo "⏳ Syncing system clock to ${SELECTED_NIC} PTP hardware..."
phc2sys -s ${SELECTED_NIC} -c CLOCK_REALTIME -w -q &
PHC_PID=\$!
sleep 3
EOF
else
cat << EOF >> $LAUNCHER
echo "ℹ️  Software mode: Using system clock (no hardware PTP syncing started)" 
EOF
fi

cat << EOF >> $LAUNCHER

echo "🎵 Launching 8-Channel PipeWire Engine..."
sudo -u $REAL_USER XDG_RUNTIME_DIR=/run/user/\$(id -u $REAL_USER) pipewire -c $PW_FILE &
PW_PID=\$!

echo "========================================="
echo " ✅ SESSION ACTIVE (Press Ctrl+C to stop)"
echo "========================================="

trap 'echo ""; echo "🛑 Shutting down AES67 session..."; \\
EOF

if [[ "$PTP_MODE" == "hardware" ]]; then
    echo "kill \$PTP_PID \$PHC_PID \$PW_PID 2>/dev/null;" >> $LAUNCHER
else
    echo "kill \$PW_PID 2>/dev/null;" >> $LAUNCHER
fi

cat << EOF >> $LAUNCHER
echo "Done."; exit' INT

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
