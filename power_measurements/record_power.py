#!/usr/bin/env python3
import time
import signal
import sys
import os
import math
import argparse
import csv

INTERVAL = 1 / 3  # seconds
data = {"values": [], "timestamps": []}
fpaths = {}
vars =[] 

# Argument parsing
parser = argparse.ArgumentParser(description="Read multiple files and compute stats.")
parser.add_argument(
    "files",
    nargs="+",
    help="Pairs of file and variable names: file1 var1 file2 var2 ..."
)
parser.add_argument("--time_output", action=argparse.BooleanOptionalAction, help="Output values over time?")
parser.add_argument("--start-after", type=float, default=0, help="Seconds to wait before starting recording")
parser.add_argument("--ignore-last", type=float, default=0, help="Seconds to ignore from the end when calculating stats")
parser.add_argument("--f", type=float, default=1, help="Factor to apply to output")
parser.add_argument("--t_ref", type=float, default=1, help="Time to set as start")
parser.add_argument("--csv", help="File to export results as CSV")
args = parser.parse_args()

# Validate file-variable pairs
if len(args.files) % 2 != 0:
    sys.exit("Error: Please provide file-variable pairs (e.g., file1 var1 file2 var2).")

# Build data dictionary
for i in range(0, len(args.files), 2):
    fpath, varname = args.files[i], args.files[i + 1]
    fpaths[varname] = fpath
    vars.append(varname)
start_time = time.time()

def read_file(fpath, varname):
    """Read numeric values from a file and append them with timestamps."""
    if not os.path.exists(fpath):
        return
    try:
        with open(fpath, "r") as f:
            for line in f:
                try:
                    return float(line.strip())
                except ValueError:
                    pass
    except Exception as e:
        print(f"Error reading {fpath}: {e}")

def calculate_mean_std(vals, ignore_last_seconds):
    """Compute mean and std, ignoring last samples if needed."""
    ignore_samples = int(ignore_last_seconds / INTERVAL)
    if ignore_samples > 0:
        vals = vals[:-ignore_samples] if ignore_samples < len(vals) else []
    n = len(vals)
    if n == 0:
        return 0, 0
    mean = sum(vals) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in vals) / n)
    return mean, std

def export_to_csv():
    """Export both summary and time-series CSVs."""
    if not args.csv:
        return
    base_csv = args.csv
    summary_csv = base_csv if base_csv.endswith(".csv") else f"{base_csv}.csv"
    time_csv = summary_csv.replace(".csv", "_time.csv")

    try:
        with open(time_csv, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp", *vars])
            for i in range(len(data["timestamps"])):
                writer.writerow([data["timestamps"][i], *data["values"][i]])
        print(f"Time-based data exported to {time_csv}")

    except Exception as e:
        print(f"CSV export failed: {e}")

def signal_handler(sig, frame):
    export_to_csv()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

print(f"Monitoring {len(vars)} files every {INTERVAL}s...")
print(f"Will start after {args.start_after}s and ignore last {args.ignore_last}s when computing stats.")
print("Press Ctrl+C to stop and print results.")

while True:
    elapsed = time.time() - start_time
    if elapsed >= args.start_after:
        current = []
        for var in vars:
            current.append(read_file(fpaths[var], var))
        data["values"].append(current)
        data["timestamps"].append(time.time() - start_time + args.t_ref)
    time.sleep(INTERVAL)
