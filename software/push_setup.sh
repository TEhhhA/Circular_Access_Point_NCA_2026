adb wait-for-device

adb push startup.sh /
adb push 2.4hapd.conf /etc/hostapd.conf

adb push dnsmasq.conf /etc/dnsmasq.conf
adb shell killall dnsmasq
adb shell dnsmasq
adb shell mkdir /lib/firmware
mkdir firmware
cd firmware

curl -L -O "https://raw.githubusercontent.com/TheMuppets/proprietary_vendor_google_oriole/lineage-23.2/proprietary/vendor/firmware/bcmdhd.cal_ROW" \
     -L -O "https://raw.githubusercontent.com/TheMuppets/proprietary_vendor_google_oriole/lineage-23.2/proprietary/vendor/firmware/fw_bcmdhd.bin" \
     -L -O "https://raw.githubusercontent.com/TheMuppets/proprietary_vendor_google_oriole/lineage-23.2/proprietary/vendor/firmware/sarconfig.info" \
     -L -O "https://raw.githubusercontent.com/TheMuppets/proprietary_vendor_google_oriole/lineage-23.2/proprietary/vendor/firmware/bcmdhd_clm.blob" \
     -L -O "https://raw.githubusercontent.com/TheMuppets/proprietary_vendor_google_oriole/lineage-23.2/proprietary/vendor/firmware/fw_bcmdhd.map" 

mkdir -p rtl_nic
cd rtl_nic

curl -s https://api.github.com/repos/ophub/firmware/contents/firmware/rtl_nic \
| grep '"download_url"' \
| cut -d '"' -f 4 \
| xargs -n1 curl -L -O
cd ../..

adb push firmware/* /lib/firmware/
