#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 NAME DURATION_SECONDS"
    exit 1
fi

adb shell killall python3

NAME="$1"
DURATION="$2"

RESULT_DIR="result"
mkdir -p "$RESULT_DIR"

USB_FILE="${RESULT_DIR}/usb_data_${NAME}.csv"
BATTERY_FILE="${RESULT_DIR}/battery_data_${NAME}.csv"

NAME_CSV="out"
DEVICE_CSV="/${NAME_CSV}_time.csv"

rm -f $USB_FILE
rm -f $BATTERY_FILE

echo "Starting device power recording..."

# Start recorder on device in background and save PID

adb shell "rm ${DEVICE_CSV}"

adb shell "nohup \
/record_power.py --time_output /sys/class/power_supply/max77759-fg/current_now current_uA\
 --csv ${NAME_CSV}.csv --t_ref $(date +%s)\
 "

echo "Starting FNIRSI logger..."

(
    cd ../fnirsi-usb-power-data-logger/
    uv run python fnirsi_logger.py
) > "$USB_FILE" &
FNIRSI_PID=$!

echo "FNIRSI PID: ${FNIRSI_PID}"

echo "Recording for ${DURATION} seconds..."
sleep "$DURATION"

echo "Stopping FNIRSI logger..."
kill "$FNIRSI_PID" 2>/dev/null || true

echo "Reconnecting adb..."
adb wait-for-device

echo "Stopping device recorder..."
adb shell "killall python3" || true

# Give it a moment to flush CSV
sleep 2

echo "Pulling battery data..."
adb pull "${DEVICE_CSV}" "$BATTERY_FILE"


if [ ! -f "$USB_FILE" ]; then
  echo "Warning: file '$USB_FILE' does not exist."
fi
echo
echo "Done."
echo "USB data:     $USB_FILE"
echo "Battery data: $BATTERY_FILE"
