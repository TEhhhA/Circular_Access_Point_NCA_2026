!# /bin/bash

modprobe pcie-exynos-gs
modprobe /bcmdhd4389.ko
ip addr add 10.0.0.1/24 dev wlan0

# Flush any existing ruleset
nft flush ruleset

# Create table
nft add table inet nat_forward

# Create NAT chain
nft add chain inet nat_forward nat_postrouting '{ type nat hook postrouting priority srcnat; }'
nft add rule inet nat_forward nat_postrouting oifname "eth0" masquerade

# Create forwarding chain
nft add chain inet nat_forward forward '{ type filter hook forward priority 0; policy drop; }'
nft add rule inet nat_forward forward ct state related,established accept
nft add rule inet nat_forward forward iifname "wlan0" oifname "eth0" accept
 
#Uncomment the line below if facing problems while sharing PPPoE
#iptables -I FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
 
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.core.rmem_max=26214400
sysctl -w net.core.wmem_max=26214400
sysctl -w net.core.wmem_default=26214400
sysctl -w net.core.wmem_default=26214400

systemctl start hostapd
