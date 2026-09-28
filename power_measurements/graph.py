import os

import pandas as pd
import matplotlib.pyplot as plt
import scienceplots
import numpy as np

plt.style.use(['science', 'ieee'])
plt.close('all')
plt.rcParams.update({
    "figure.figsize": (3.3, 2.2),
    "font.family": "serif",
    "text.usetex": True,
    "axes.labelsize": 8,
    "font.size": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    'hatch.linewidth': 2.5,
})

os.makedirs("./graphs", exist_ok=True)

# Obtained from
# R. Dethienne, J. Louveaux, and D. Bol, “A power consumption model
# for customer premise equipment: Methodology and application,” in
# 2025 International Conference on Software, Telecommunications and
# Computer Networks (SoftCOM), 2025, pp. 01–06,
# doi: 10.23919/Soft-COM66362.2025.11197346
ONU = 2.113896 #W
IBOX = 6.237828 #W

names = [
    "6_13",
    "white_no_dvfs_no_idle",
    "black_no_dvfs_no_idle",
    "screenPG_no_dvfs_no_idle",
    "idle",
    "2_5_Gbps_none",
    "2_5Gbps_2_4GHz",
    "2_5Gbps_5GHz",
    "2_5Gbps_2_4_GHZ_5GHz",
    "2_5Gbps_eth",
    "2_5Gbps_eth_2_4GHz_5GHz",
]

usb_df =pd.read_csv(f"./data/ufiber_wifi6_2_int_up_connected_fiber.csv", sep=" ")

usb_df["power_W"] = usb_df["voltage_V"] * usb_df["current_A"]
usb_df["timestamp"] = pd.to_datetime(usb_df["timestamp"], unit="s")

UB = usb_df["power_W"].mean()

def interpolate_and_subtract(A: pd.DataFrame,
                             B: pd.DataFrame,
                             time_col: str = "timestamp",
                             value_col: str = "power_W",
                             agg: str = "mean") -> pd.DataFrame:

    A = A.copy()
    B = B.copy()

    # Set index
    A = A.set_index(time_col).sort_index()
    B = B.set_index(time_col).sort_index()


    # Common timeline
    common_index = A.index.union(B.index).sort_values()

    # Interpolate
    A_interp = A.reindex(common_index).interpolate(method="time")
    B_interp = B.reindex(common_index).interpolate(method="time")

    # Difference
    out = pd.DataFrame({
        "power_W": A_interp[value_col] - B_interp[value_col]
    }, index=common_index)


    return out.reset_index().rename(columns={"index": time_col}).dropna()

measurements = {}

for name in names:
    usb_df =pd.read_csv(f"./data/usb_data_{name}.csv", sep=" ")
    bat_df =pd.read_csv(f"./data/battery_data_{name}.csv")

    usb_df["power_W"] = usb_df["voltage_V"] * usb_df["current_A"]
    bat_df["power_W"] = 4e-6 * bat_df["current_uA"]
    
    usb_df["timestamp"] = pd.to_datetime(usb_df["timestamp"], unit="s")
    bat_df["timestamp"] = pd.to_datetime(bat_df["timestamp"], unit="s")


    df = interpolate_and_subtract(usb_df, bat_df)
    measurements[name] = df["power_W"].mean()

fig, ax = plt.subplots(1,1)

vals = [
    measurements["6_13"],
    measurements["white_no_dvfs_no_idle"],
    measurements["black_no_dvfs_no_idle"],
    measurements["screenPG_no_dvfs_no_idle"],
    measurements["idle"],
]

idle_GP6 = vals[-1]
labs = [
    "Linux 6.13\n(default)",
    "Linux 6.18\nWhite screen\nNo CPU idle\nNo DVFS",
    "Black screen",
    "Screen\npower gated",
    "CPU idle\nDVFS"
]
bars = ax.bar(labs, vals, width=0.4)
ax.bar_label(bars, fmt='%.2f', padding=3)
ax.grid(axis='y')
ax.set_ylabel("Power consumption (W)")
fig.tight_layout()
ax.set_ylim(0,3.8)
fig.set_size_inches(fig.get_size_inches()[0], 2)
fig.savefig("./graphs/prototype_consumption_gain.pdf")

fig, ax = plt.subplots(1,1)

mvals = [
    measurements["2_5_Gbps_none"],
    measurements["2_5Gbps_2_4GHz"],
    measurements["2_5Gbps_5GHz"],
    measurements["2_5Gbps_2_4_GHZ_5GHz"],
    measurements["2_5Gbps_eth"],
    measurements["2_5Gbps_eth_2_4GHz_5GHz"],
]
idle_transceiver = mvals[0] - idle_GP6
base = np.array([
                    idle_GP6,
                    mvals[1]- idle_transceiver,
                    mvals[2]- idle_transceiver,
                    mvals[3]- idle_transceiver,
                    idle_GP6,
                    mvals[3]- idle_transceiver,
                ])
                    

vals = np.array(mvals) - base
labs = [
    "Wi-Fi off\nWAN off",
    "2.4GHz",
    "5GHz",
    "2.4GHz\n5GHz",
    "WAN",
    "WAN\n2.4GHz\n5GHz",

]
bars = ax.bar(labs, base, color="xkcd:black", width=0.4, label = "GP6")
bars = ax.bar(labs, vals, bottom=base, color="xkcd:gray", width=0.4, label="Adapter")

ax.bar_label(bars, fmt='%.2f', padding=3)
ax.set_ylim(0,2.5)
ax.grid(axis='y')
ax.set_ylabel("Power consumption (W)")

ax.legend(
    frameon=True,
    facecolor="white",
    framealpha=1,  # fully opaque
)
fig.tight_layout()
fig.set_size_inches(fig.get_size_inches()[0], 2)

fig.savefig("./graphs/prototype_consumption.pdf")

fig, ax = plt.subplots(1,1)

vals = [
    mvals[-1],
     IBOX,
]
labs = [
    "CAP\n+ONU",
    "IAP\n+ONU",
]
ax.bar(labs, [ONU, ONU], color="xkcd:gray", label="ONU", width=0.4)
bars =ax.bar(labs, vals, bottom=ONU, color= "xkcd:black", label="AP", width=0.4)
ax.bar_label(bars, fmt='%.2f', padding=3)
bars = ax.bar("UAP", UB,
       color="xkcd:grey",
       edgecolor="xkcd:black",
       linewidth=0,
       hatch="///",
       width=0.4,
)
ax.bar_label(bars, fmt='%.2f', padding=3)
ax.grid(axis='y')

ax.legend(
    frameon=True,
    facecolor="white",
    framealpha=1,
)
ax.set_ylim(0,10)
ax.set_ylabel("Power consumption (W)")
fig.tight_layout()
fig.set_size_inches(fig.get_size_inches()[0], 1.8)
fig.savefig("./graphs/comp_consumption.pdf")
    
