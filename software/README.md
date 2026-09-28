This repo contains everything needed to setup a Google Pixel 6 as WiFi AP.

First, follow
[this tutorial from Linaro](https://gitlab.com/LinaroLtd/googlelt/pixelscripts)
containing everything you need to boot the mainline kernel on the phone.

As in their instructions, `repo sync` and setup kernel build and the yocto workspace.

### Before building the kernel

Go inside the `src/linux` where the kernel source used
when building is found and run
```
git checkout 2433b84761658ef123ae683508bc461b07c5b0f0
```
Then use
```
git fetch (path_to_this_repo)/kernel.bundle HEAD:refs/heads/CAP_NCA
git checkout CAP_NCA
```

This bundle is mainly composed of
- Custom patches
- Patches from [linked Linaro repo](https://gitlab.com/LinaroLtd/googlelt/linuxlt) which have since been integrated into the mainline kernel.
- A modified version of [the exynos pcie driver available on Google's repo.](https://android.googlesource.com/kernel/google-modules/soc/gs/+/refs/heads/android-gs-raviole-6.1-android16-dp/drivers/pci/controller/dwc/) 

All commit messages are contained in the bundle to conserve proper credit.

To `src/pixelscripts/gs101_config.fragment`, add 
```
CONFIG_PCI_EXYNOS=m
CONFIG_PCI_EXYNOS_CAL_GS101=m
CONFIG_PCI_EXYNOS_GS=m

CONFIG_IP_ADVANCED_ROUTER=y
CONFIG_IP_MULTIPLE_TABLES=y
CONFIG_PCI_TEGRA=n

CONFIG_NF_TABLES=y
CONFIG_NF_TABLES_INET=y
CONFIG_NF_TABLES_IPV4=y
CONFIG_NF_TABLES_IPV6=y

CONFIG_NF_NAT=y
CONFIG_NFT_NAT=y
CONFIG_NFT_CT=y
CONFIG_NFT_MASQ=y
CONFIG_NFT_REDIR=y
CONFIG_IP_FORWARD=y
CONFIG_NF_CONNTRACK_IPV4=y
CONFIG_NF_NAT_IPV4=y

CONFIG_NF_CONNTRACK_FTP=y
CONFIG_NF_CONNTRACK_TFTP=y
CONFIG_NF_CONNTRACK_IPV6=y

```

### Before building the rootfs

Add `python3 nftables hostapd dnsmasq iw wireless-regdb-static` to `IMAGE_INSTAL:append` in `conf/local.conf` in the yocto environment.

## Booting the device

First, [unlock your bootloader](https://wiki.postmarketos.org/wiki/Google_Pixel_6_(google-oriole)).
Then, as explained in the Linaro repo, build the yocto rootfs, flash it.
Build the linux kernel, flash it. You can then boot the phone.

## Making WiFi work
From this repository, `(path_to_linaro)` with the path you used in the setup, run
```
cd bcm4389
git apply ../wifi.patch
make -C (path_to_linaro)/out/linux M=$PWD ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -I ./include
adb push ./bcmdhd4389.ko /
```

Then, from this folder,
```
./push_setup.sh
```

### Setting up the device as AP
Everything should now be ready. Do
```
adb shell /startup.sh
```

The 2.4GHz WiFi interface should be up.

By default, we set the AP as 2.4GHz. You can change it to 5GHz
by using
```
adb push hapd.conf /etc/hostapd.conf
 
adb shell systemctl restart hostapd
```
It is also possible to enable both at the same time by running `hostapd` manually on wlan0 and wlan1.

## Maintenance

The kernel build depends on the gcc version of your system.
The given commit and patch were successfully built with<br>
gcc (GCC) 16.2.1 20260810<br>
Other versions of GCC might require changes to the kernel
to build successfully.