#!/usr/bin/env bash

########################################
# CONFIG
########################################

#Interface of the client device (which launches the script)
IFACE="wlp0s20f3"
SERVER="10.0.1.20" #IP address of the "server" device
PORT=5201
DURATION=10
REPETITIONS=3
CSV_OUT="results.csv"
AP_TYPE="GP6" 

AP_HOST="root@10.0.0.1"
AP_IFACE="wlan0"
AP_STA_MAC="80:c0:1e:54:55:1a"

STA_POWERS=(0 100 200 300 400 500 600 700 800 900 1000 1100 1200 1300 1400 1500 1600 1700)
AP_POWERS=(0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)

STA_MAX=1700
AP_MAX=15

# possible MCS indices to track
MCS_LIST=(0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15)
NSS_LIST=(1 2)
GI_LIST=(-1 0 1 2)

########################################
# HELPERS
########################################

log() { echo "$@" >&2; }

set_sta_power() {
    sudo iw dev "$IFACE" set txpower fixed "$1"
    sleep 2
}

set_ap_power() {
    local TX_POWER="$1"

    case "$AP_TYPE" in
        "GP6")
            ssh "$AP_HOST" \
                "python3 /send_private_ioctl.py $AP_IFACE TEST_SET_TX_POWER $TX_POWER"
            ;;
        "UB")
            sudo -u TA uv run set_RSSI.py $TX_POWER
            nmcli connection up ubnt
            ;;
        "IBox")
            # Cannot access modem, skip
            echo "IBox: skipping AP TX power configuration"
            ;;
        *)
            echo "Unknown AP_TYPE: $AP_TYPE" >&2
            return 1
            ;;
    esac

    sleep 10
}

get_sta_rssi() {
    iw dev "$IFACE" link | awk '/signal:/ {print $2}'
}

get_ap_rssi() {
    case "$AP_TYPE" in
        "GP6")
#            ssh "$AP_HOST" \
#                "python3 /send_private_ioctl.py $AP_IFACE GETSTAINFO $AP_STA_MAC" \
#                | awk '{ rssi1=$(NF-6); rssi2=$(NF-5); print rssi1 "," rssi2 }'
            echo "-1,-1"
            ;;
        "UB")
            sudo -u TA uv run get_RSSI.py
            ;;
        "IBox")
            # Cannot access modem, skip
            echo "-1,-1"
            ;;
        *)
            echo "Unknown AP_TYPE: $AP_TYPE" >&2
            return 1
            ;;
    esac
}

########################################
# SAMPLING LOOP
########################################

collect_samples() {

    local pid=$1
    local direction=$2

    MCS_SAMPLES=()
    NSS_SAMPLES=()
    GI_SAMPLES=()
    RSSI_STA_SAMPLES=()
    RSSI_AP_SAMPLES_0=()
    RSSI_AP_SAMPLES_1=()

    while kill -0 "$pid" 2>/dev/null; do

        if [[ "$direction" == "ul" ]]; then
            LINE=$(iw dev "$IFACE" link | grep "tx bitrate")
        else
            LINE=$(iw dev "$IFACE" link | grep "rx bitrate")
        fi

        MCS=$(echo "$LINE" | sed -n 's/.*MCS \([0-9]\+\).*/\1/p')
        NSS=$(echo "$LINE" | sed -n 's/.*NSS \([0-9]\+\).*/\1/p')
        GI=$(echo "$LINE" | sed -n 's/.*GI \([0-9]\+\).*/\1/p')

        [[ -n "$MCS" ]] && MCS_SAMPLES+=("$MCS")
        [[ -n "$NSS" ]] && NSS_SAMPLES+=("$NSS")
        [[ -n "$NSS" ]] && GI_SAMPLES+=("$([ "$GI" = "short-GI" ] && echo -1 || echo "$GI")")
#        [[ -n "$NSS" ]] && GI_SAMPLES+=("$GI")

        RSSI_STA_SAMPLES+=("$(get_sta_rssi)")


        IFS=',' read -ra split_rssi <<< $(get_ap_rssi)
        RSSI_AP_SAMPLES_0+=("${split_rssi[0]}")
        RSSI_AP_SAMPLES_1+=("${split_rssi[1]}")

        #sleep 0.5
    done
}

########################################
# STATS
########################################

mean_array() {
    local arr=("$@")
    local sum=0
    local count=0

    for v in "${arr[@]}"; do
        [[ -n "$v" ]] && sum=$((sum+v)) && count=$((count+1))
    done

    if [[ $count -eq 0 ]]; then
        echo ""
    else
        echo "$sum $count" | awk '{printf "%.1f", $1/$2}'
    fi
}

compute_mcs_histogram() {

    local total=${#MCS_SAMPLES[@]}

    for mcs in "${MCS_LIST[@]}"; do
        count=0
        for v in "${MCS_SAMPLES[@]}"; do
            [[ "$v" == "$mcs" ]] && ((count++))
        done

        if [[ $total -gt 0 ]]; then
            pct=$(awk "BEGIN {printf \"%.2f\", ($count/$total)*100}")
        else
            pct=0
        fi

        HIST_VALUES+=("$pct")
    done
}

compute_nss_histogram() {

    local total=${#NSS_SAMPLES[@]}

    for nss in "${NSS_LIST[@]}"; do
        count=0
        for v in "${NSS_SAMPLES[@]}"; do
            [[ "$v" == "$nss" ]] && ((count++))
        done

        if [[ $total -gt 0 ]]; then
            pct=$(awk "BEGIN {printf \"%.2f\", ($count/$total)*100}")
        else
            pct=0
        fi

        NSS_VALUES+=("$pct")
    done
}
compute_gi_histogram() {

    local total=${#GI_SAMPLES[@]}

    for nss in "${GI_LIST[@]}"; do
        count=0
        for v in "${GI_SAMPLES[@]}"; do
            [[ "$v" == "$nss" ]] && ((count++))
        done

        if [[ $total -gt 0 ]]; then
            pct=$(awk "BEGIN {printf \"%.2f\", ($count/$total)*100}")
        else
            pct=0
        fi

        GI_VALUES+=("$pct")
    done
}
########################################
# MEASUREMENT
########################################

run_measurement() {

    local dir=$1
    local iperf_args=""
    [[ "$dir" == "dl" ]] && iperf_args="-R"

    log "Running $dir test..."

    iperf3 -c "$SERVER" -p "$PORT" -t "$DURATION" -P 4 $iperf_args > iperf_tmp.txt &
    IPERF_PID=$!

    collect_samples "$IPERF_PID" "$dir"

    wait "$IPERF_PID"

    TPUT=$(grep receiver iperf_tmp.txt | tail -1 | awk '{print $(NF-2)}')

    RSSI_STA_MEAN=$(mean_array "${RSSI_STA_SAMPLES[@]}")
    RSSI_AP_MEAN_0=$(mean_array "${RSSI_AP_SAMPLES_0[@]}")
    RSSI_AP_MEAN_1=$(mean_array "${RSSI_AP_SAMPLES_1[@]}")

    HIST_VALUES=()
    compute_mcs_histogram


    NSS_VALUES=()
    compute_nss_histogram


    GI_VALUES=()
    compute_gi_histogram

    echo "$RSSI_STA_MEAN,$RSSI_AP_MEAN_0,$RSSI_AP_MEAN_1,$TPUT,${HIST_VALUES[*]} ${NSS_VALUES[*]} ${GI_VALUES[*]}"
}

########################################
# CSV HEADER
########################################

HEADER="pwr_sta,pwr_ap,rssi_sta,rssi1_ap,rssi2_ap,tput,dir"

for mcs in "${MCS_LIST[@]}"; do
    HEADER="$HEADER,mcs$mcs"
done

for nss in "${NSS_LIST[@]}"; do
    HEADER="$HEADER,nss$nss"
done

for gi in "${GI_LIST[@]}"; do
    HEADER="$HEADER,gi$gi"
done

echo "$HEADER" > "$CSV_OUT"

########################################
# STA SWEEP (UL)
########################################
set_sta_power "$STA_MAX"

for ap_pwr in "${AP_POWERS[@]}"; do
    set_ap_power "$ap_pwr"

    for ((i=1;i<=REPETITIONS;i++)); do

        RESULT=$(run_measurement dl)

        IFS="," read RSSI_STA RSSI_AP_0 RSSI_AP_1 TPUT MCS_VALUES <<< "$RESULT"

        echo "$STA_MAX,$ap_pwr,$RSSI_STA,$RSSI_AP_0,$RSSI_AP_1,$TPUT,dl,$MCS_VALUES" \
            | sed 's/ /,/g' >> "$CSV_OUT"
    done
done


set_ap_power "$AP_MAX"

for sta_pwr in "${STA_POWERS[@]}"; do
    set_sta_power "$sta_pwr"

    for ((i=1;i<=REPETITIONS;i++)); do

        RESULT=$(run_measurement ul)

        IFS="," read RSSI_STA RSSI_AP_0 RSSI_AP_1 TPUT MCS_VALUES <<< "$RESULT"

        echo "$sta_pwr,$AP_MAX,$RSSI_STA,$RSSI_AP_0,$RSSI_AP_1,$TPUT,ul,$MCS_VALUES" \
            | sed 's/ /,/g' >> "$CSV_OUT"
    done
done

########################################
# AP SWEEP (DL)
########################################

log "Done → $CSV_OUT"
