***

# The Complete AES67 PTP Clock Architecture Guide

## Overview
Precision Time Protocol (PTP) clocking can be notoriously tricky because standard computer operating systems are not designed for microsecond-level audio synchronization out of the box.

This guide provides the complete blueprint for transforming a standard Linux machine into an AES67-compliant PTP Master or Slave. It covers dependency installation, critical kernel-level permissions, routing logic, and the tools needed to launch and verify your network clock.

---

## Phase 1: Installation & Dependencies
Before configuring the network, the host machine must have the necessary daemons and networking tools installed.

**Dependencies required:**
* `linuxptp`: Provides `ptp4l` (the network clock daemon) and `phc2sys` (the system clock bridge).
* `ethtool`: Used to verify hardware timestamping capabilities on your Network Interface Card (NIC).
* `gstreamer` & `pipewire` (Optional, but required if you are using this node for audio transmission/reception).

**Run the following command to install the core packages:**
```bash
sudo apt-get update
sudo apt-get install -y linuxptp ethtool python3 awk
```

---

## Phase 2: Network Setup & Permissions
AES67 relies heavily on **Multicast UDP** and **Real-Time CPU Scheduling**. By default, Linux drops multicast packets and restricts daemons from demanding real-time CPU priority. We must explicitly grant these permissions.

Save the following code as `0_setup_permissions.sh` and run it once per boot:

```bash
#!/bin/bash
echo "=== AES67 Network Setup & Permissions ==="

read -p "Enter network interface [enp2s0]: " INTERFACE
INTERFACE=${INTERFACE:-enp2s0}

echo "Configuring interface $INTERFACE for Multicast..."
# Bring the interface online and explicitly enable multicast hardware routing
sudo ip link set dev $INTERFACE up
sudo ip link set dev $INTERFACE multicast on

echo "Setting Linux Capabilities (Permissions) for precise timing..."
# Grant ptp4l and phc2sys the ability to use real-time scheduling (cap_sys_nice)
# and bind to secure network ports (cap_net_bind_service) without running entirely as root
sudo setcap cap_net_bind_service,cap_sys_nice+ep $(which ptp4l)
sudo setcap cap_net_bind_service,cap_sys_nice+ep $(which phc2sys)

echo "Setup complete. The network is ready for AES67."
```

---

## Phase 3: Guaranteeing a Node Becomes the Grandmaster
In a PTP network, you do not manually assign a master. Instead, devices hold an automated election called the **Best Master Clock Algorithm (BMCA)** to decide who has the most accurate clock.

If you want to guarantee that your specific Linux machine wins this election and becomes the Master, you must manipulate its priority.

1.  **Understand `slaveOnly`:** For a node to even be *allowed* to run in the election, it must have `slaveOnly 0` in its configuration. (Setting `slaveOnly 1` forces a device to just listen).
2.  **Rig the Election with `priority1`:** Devices are graded on a `priority1` scale from `0` to `255`. The *lowest* number wins. The default for most hardware is `128`.

To guarantee your Linux machine becomes the Grandmaster, you add this to its `ptp4l.conf` file:
```ini
[global]
slaveOnly             0
# Lower number wins the BMCA election. Default is 128.
priority1             127
domainNumber          0
network_transport     UDPv4
```
*(Note: The interactive script in Phase 4 handles the `slaveOnly` parameter for you automatically, but if you have multiple Master-eligible devices on your network, you must manually lower the `priority1` value to guarantee dominance).*

---

## Phase 4: The Interactive Clock Engine Script
This script (`linux_ptp_option.sh`) is the core engine. It dynamically generates your PTP configuration based on your answers and orchestrates the complex routing between the network and your Linux system clock.

**Key Under-the-Hood Routing (`phc2sys`):**
When running in Hardware Timestamping mode, the script reverses synchronization direction based on your role:
* **Slave Mode:** Pulls time from the network (NIC) and forces the Linux system clock to match it (`NIC -> OS`).
* **Master Mode:** Pulls time from the Linux system clock and pushes it to the NIC to be broadcasted (`OS -> NIC`).

Save this as `1_run_clock.sh`:
```bash
#!/bin/bash
echo "=== AES67 PTP Clock Setup ==="

# Prompt for Variables
read -p "Enter network interface [enp2s0]: " INTERFACE
INTERFACE=${INTERFACE:-enp2s0}
read -p "Select node role - Master or Slave? (master/slave) [slave]: " ROLE
ROLE=${ROLE:-slave}
read -p "Select timestamp mode - Hardware or Software? (hw/sw) [hw]: " MODE
MODE=${MODE:-hw}

ROLE=${ROLE,,}
MODE=${MODE,,}

# Generate Configuration
CONF_FILE="ptp4l_custom.conf"
echo "[global]" > $CONF_FILE

if [ "$ROLE" == "master" ]; then
    echo "slaveOnly             0" >> $CONF_FILE
    # Optional: Uncomment the next line to guarantee this node wins the Master election
    # echo "priority1             127" >> $CONF_FILE
else
    echo "slaveOnly             1" >> $CONF_FILE
fi

cat <<EOF >> $CONF_FILE
domainNumber          0
network_transport     UDPv4
EOF

echo "Initializing on $INTERFACE as $ROLE in $MODE mode..."

# Execute Daemons
if [ "$MODE" == "hw" ]; then
    echo "time_stamping         hardware" >> $CONF_FILE
    echo "Starting ptp4l (Hardware $ROLE) in the background..."
    sudo ptp4l -i $INTERFACE -f $CONF_FILE -H -m &
    sleep 2

    if [ "$ROLE" == "master" ]; then
        echo "Starting phc2sys: Synchronizing NIC to System Clock (OS -> NIC)..."
        sudo phc2sys -c $INTERFACE -s CLOCK_REALTIME -w -m
    else
        echo "Starting phc2sys: Synchronizing System Clock to NIC (NIC -> OS)..."
        sudo phc2sys -s $INTERFACE -c CLOCK_REALTIME -w -m
    fi

elif [ "$MODE" == "sw" ]; then
    echo "time_stamping         software" >> $CONF_FILE
    echo "Starting ptp4l (Software $ROLE) in the foreground..."
    sudo ptp4l -i $INTERFACE -f $CONF_FILE -S -m
else
    echo "Invalid mode. Exiting."
    exit 1
fi
```

---

## Phase 5: Verification & Testing
Once your clock engine is running, you can verify your network synchronization. Open a **new terminal window** and run the PTP Management Client:

```bash
sudo pmc -u -b 0 'GET TIME_STATUS_NP'
```

**How to read the results:**
* **`master_offset`**: Shows the nanosecond drift from the Grandmaster. You want this as close to `0` as possible.
* **`gmIdentity`**: The MAC address of the current network Grandmaster.
* **`portState`**:
    * `SLAVE`: You are successfully receiving time.
    * `MASTER`: You won the BMCA election and are successfully broadcasting time.
    * `LISTENING`: Something is blocking your network traffic (usually a firewall or switch configuration).

**To cleanly shut down the clock engine when finished:**
```bash
sudo killall ptp4l phc2sys
```
