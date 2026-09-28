The measurement scripts are `meas.sh` if the connection to the CAP is done through adb, `meas_ssh.sh` if the connection to the CAP is through the an ssh connection and `ssh_none.sh` if no connection to the measured device is available. This last script is useful to use alternative connection means which do not have a dedicated script.

To do a measurement on the CAP, make sur you have pulled submodules as explained in the
main README and do
```
  adb push record_power.py /
  adb push send_private_ioctl.py /
```
while the smartphone is plugged.

After running `graphs.py`, the results will be contained in the `graphs` folder
