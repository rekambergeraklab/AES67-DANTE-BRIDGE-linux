#!bin/bash
for nic in $(ls /sys/class/net | grep enp); do
    echo "------------------------------------------------"
    echo "AUDIT FOR INTERFACE: $nic"
    echo "------------------------------------------------"
    # 1. Check Driver (Intel is king for Milan/AES67)
    ethtool -i $nic | grep -E "driver|version"
    
    # 2. Check PTP/Hardware Timestamping
    ethtool -T $nic | grep -A 8 "Capabilities"
    
    # 3. Check for Energy Efficient Ethernet (Must be DISABLED for PTP)
    ethtool --show-eee $nic 2>/dev/null | grep "EEE status" || echo "EEE: Not supported (Good for PTP)"
    
    # 4. Check for AVB Hardware Shaper (Required for Milan)
    tc qdisc add dev $nic root handle 100: mqprio num_tc 3 map 2 2 1 0 2 2 2 2 2 2 2 2 2 2 2 2 queues 1@0 1@1 2@2 hw 0 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "AVB Hardware Shaper: SUPPORTED"
        sudo tc qdisc del dev $nic root 2>/dev/null
    else
        echo "AVB Hardware Shaper: SOFTWARE ONLY"
    fi
done
