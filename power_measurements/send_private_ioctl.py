#!/usr/bin/env python3
import socket
import fcntl
import ctypes
import sys

# Constants
IFNAMSIZ = 16
SIOCDEVPRIVATE = 0x89F0
IOCTL_PRIV_CMD = SIOCDEVPRIVATE + 1

# Structures
class ifreq(ctypes.Structure):
    _fields_ = [
        ("ifr_name", ctypes.c_char * IFNAMSIZ),
        ("ifr_data", ctypes.c_void_p)
    ]

class android_wifi_priv_cmd(ctypes.Structure):
    _fields_ = [
        ("buf", ctypes.c_void_p),
        ("used_len", ctypes.c_int),
        ("total_len", ctypes.c_int),
    ]

def send_priv_cmd(ifname: str, cmd: str, buf_size: int = 4096) -> str:
    # Open socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)

    # Create buffer
    buf = ctypes.create_string_buffer(buf_size)
    buf.value = cmd.encode()

    # Prepare android_wifi_priv_cmd
    priv_cmd = android_wifi_priv_cmd()
    priv_cmd.buf = ctypes.cast(buf, ctypes.c_void_p)
    priv_cmd.used_len = len(cmd)
    priv_cmd.total_len = buf_size

    # Prepare ifreq
    ifr = ifreq()
    ifr.ifr_name = ifname.encode()
    ifr.ifr_data = ctypes.addressof(priv_cmd)

    # Send ioctl
    try:
        fcntl.ioctl(sock.fileno(), IOCTL_PRIV_CMD, ifr)
    except OSError as e:
        raise RuntimeError(f"ioctl failed: {e}")

    # Read back the result
    return buf.value.decode(errors="ignore").strip()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <iface> <command>")
        print(f"Example: {sys.argv[0]} wlan0 GET_SNR")
        sys.exit(1)

    iface = sys.argv[1]
    command = " ".join(sys.argv[2:])  # allow commands with arguments

    try:
        result = send_priv_cmd(iface, command)
        print("Result:", result)
    except Exception as e:
        print("Error:", e)
