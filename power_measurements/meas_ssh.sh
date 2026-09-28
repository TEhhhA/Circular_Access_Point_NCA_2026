#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 SSH_TARGET NAME DURATION_SECONDS"
    exit 1
fi

SSH_TARGET="$1"
NAME="$2"
DURATION="$3"

RESULT_DIR="result"
mkdir -p "$RESULT_DIR"

USB_FILE="${RESULT_DIR}/usb_data_${NAME}.csv"
BATTERY_FILE="${RESULT_DIR}/battery_data_${NAME}.csv"

NAME_CSV="out"
DEVICE_CSV="/${NAME_CSV}_time.csv"

rm -f "$USB_FILE"
rm -f "$BATTERY_FILE"

echo "Starting device power recording..."

# ssh "$SSH_TARGET" "rm ${DEVICE_CSV}"
ssh "$SSH_TARGET" "killall python3" || true

ssh "$SSH_TARGET" "nohup \
/record_power.py --time_output /sys/class/power_supply/max77759-fg/current_now current_uA \
--csv ${NAME_CSV}.csv --t_ref $(date +%s)" &

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

echo "Stopping device recorder..."
ssh "$SSH_TARGET" "killall python3" || true

# Give it a moment to flush CSV
sleep 2

echo "Pulling battery data..."
scp "${SSH_TARGET}:${DEVICE_CSV}" "$BATTERY_FILE"

if [ ! -f "$USB_FILE" ]; then
    echo "Warning: file '$USB_FILE' does not exist."
fi

echo
echo "Done."
echo "USB data:     $USB_FILE"
echo "Battery data: $BATTERY_FILE"
