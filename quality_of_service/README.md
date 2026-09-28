This folder contains the data gathered during the measurement campaign and the script
used to generate them.

Please change the parameters at the start of the `measure.sh` script to match your setup.
AP_TYPE in particular can be GP6 for the CAP, UB for the Ubiquiti UFiber WiFi6
and IBox for APs which do not allow for RSSI collection.

To add support for new devices, please add them in the `get_ap_rssi` and `set_ap_rssi`
functions.

Note that many more values are monitored than are actually shown in the paper.
They are still included for possible future usage.

After running `graphs.py`, the results will be contained in the `graphs` folder
