#!/bin/bash

echo "=== AES67 PTP Clock Setup ==="

# 1. Prompt for Network Interface (Default: eno1)
read -p "Enter network interface [eno1]: " INTERFACE
INTERFACE=${INTERFACE:-eno1}

# 2. Prompt for Node Role (Default: slave)
read -p "Select node role - Master or Slave? (master/slave) [slave]: " ROLE
ROLE=${ROLE:-slave}

# 3. Prompt for Timestamping Mode (Default: hw)
read -p "Select timestamp mode - Hardware or Software? (hw/sw) [hw]: " MODE
MODE=${MODE:-hw}

# Normalize inputs to lowercase just in case
ROLE=${ROLE,,}
MODE=${MODE,,}

# 4. Dynamically generate the baseline configuration file
CONF_FILE="ptp4l_custom.conf"
echo "[global]" > $CONF_FILE

# Set slaveOnly status based on role
if [ "$ROLE" == "master" ]; then
    echo "slaveOnly             0" >> $CONF_FILE
else
    echo "slaveOnly             1" >> $CONF_FILE
fi

# Add common configurations
cat <<EOF >> $CONF_FILE
domainNumber          0
network_transport     UDPv4
EOF

echo "----------------------------------------"
echo "Initializing on $INTERFACE as $ROLE in $MODE mode..."
echo "----------------------------------------"

# 5. Execute based on selection
if [ "$MODE" == "hw" ]; then
    # Append hardware setting to conf
    echo "time_stamping         hardware" >> $CONF_FILE

    echo "Starting ptp4l (Hardware $ROLE) in the background..."
    sudo ptp4l -i $INTERFACE -f $CONF_FILE -H -m &

    echo "Waiting 2 seconds for ptp4l to initialize..."
    sleep 2

    # Configure phc2sys direction based on Master/Slave role
    if [ "$ROLE" == "master" ]; then
        echo "Starting phc2sys: Synchronizing NIC to System Clock (CLOCK_REALTIME -> NIC)..."
        # -c is the clock to be synced (destination), -s is the master clock (source)
        sudo phc2sys -c $INTERFACE -s CLOCK_REALTIME -w -m
    else
        echo "Starting phc2sys: Synchronizing System Clock to NIC (NIC -> CLOCK_REALTIME)..."
        sudo phc2sys -s $INTERFACE -c CLOCK_REALTIME -w -m
    fi

elif [ "$MODE" == "sw" ]; then
    # Append software setting to conf
    echo "time_stamping         software" >> $CONF_FILE

    echo "Starting ptp4l (Software $ROLE)..."
    echo "Note: phc2sys is skipped because software timestamping uses CLOCK_REALTIME directly."

    # Run ptp4l in the foreground
    sudo ptp4l -i $INTERFACE -f $CONF_FILE -S -m

else
    echo "Error: Invalid mode selected. Please run again and type 'hw' or 'sw'."
    exit 1
fi
