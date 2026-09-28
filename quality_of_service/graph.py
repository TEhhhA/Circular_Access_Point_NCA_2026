import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scienceplots
import seaborn as sns
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
from pdf2image import convert_from_path
from scipy.interpolate import griddata

plt.style.use(['science','ieee'])

os.makedirs("./graphs", exist_ok=True)

suffixes = ["CAP", "UAP", "IAP"]

def plot_point(ax, x, y, label):
    ax.scatter(x, y)              # plot the point
    ax.text(x, y, label,      # label
            fontsize=10,
            ha="left", va="bottom")

def grid_f(a, grid_x, grid_y, df):
    valid = df[["x", "y", a]].notna().all(axis=1)
    return griddata(
        (df.loc[valid, "x"], df.loc[valid, "y"]),
        df.loc[valid, a],
        (grid_x, grid_y),
        method="linear"  # 'linear' or 'nearest' also possible
    )
page = convert_from_path("cropped_plan.pdf", dpi=300)[0]

background = np.array(page)

df = pd.read_csv("./meas_map.csv")

h, w, _ = background.shape
height, width, _ = background.shape

for i in suffixes:
    df["filename"+i] = "./data/apprt_"+i+"/"+df["name"]+".csv"

fig_se, axes_se = plt.subplots(3,2, sharex=True, sharey=False)

sns.set(style="whitegrid")

ref_delta = np.inf
for id_su, suffix in enumerate(suffixes):
    all_X = []
    all_y = []
    plot_df_list = []

    for index, row in df.iterrows():
        filename = row["filename" + suffix]

        if not os.path.exists(filename):
            continue

        df_row = pd.read_csv(filename)
        df_row["pwr_sta"] /= 100
        df_row["filename"] = filename

        df_row["rssi_ap"] = ( #Applying the path loss symetry trick
            df_row["rssi_sta"]
            + df_row["pwr_sta"] 
            - df_row["pwr_ap"]
        )
        
        
        ul_df = df_row[df_row["dir"] == "ul"].copy()
        dl_df = df_row[df_row["dir"] == "dl"].copy()

        plot_df_list.append(df_row.copy())

        df.loc[index, "rssi_sta_" + suffix] = np.mean(
            df_row[df_row["pwr_ap"] == df_row["pwr_ap"].max()]["rssi_sta"]
        )

        df.loc[index, "utput_" + suffix] = ul_df[ul_df["pwr_sta"] == ul_df["pwr_sta"].max()]["tput"].mean()
        df.loc[index, "dtput_" + suffix] = dl_df[dl_df["pwr_sta"] == dl_df["pwr_sta"].max()]["tput"].mean()
    
    plot_df = pd.concat(plot_df_list, ignore_index=True)
    plot_df["SE"] = plot_df["tput"] / 20

    ul_df = plot_df[plot_df["dir"] == "ul"].copy()
    dl_df = plot_df[plot_df["dir"] == "dl"].copy()
    
    for index, l_df, l_label, rx, tx in zip([1,0], [ul_df,dl_df], ["Upstream", "Downstream"], ["ap", "sta"], ["sta", "ap"]):
        ax = axes_se[id_su][index]

        if not (l_label == "Downstream" and suffix == "IAP"):
            # Keep only non-zero throughput samples
            nz = l_df[l_df["tput"] > 0].copy()

            min_rssi = nz["rssi_" + rx].min()
            max_rssi = min_rssi + 10 # window of size 10dB

            fit_df = nz[
                (nz["rssi_" + rx] >= min_rssi) &
                (nz["rssi_" + rx] <= max_rssi)
            ].copy()

            m, b = np.polyfit(fit_df["rssi_" + rx], fit_df["tput"], 1)

            rssi_zero = -b / m
            print(f"{l_label} , {suffix}: S={rssi_zero}dBm")
            x = fit_df["rssi_" + rx]
            y = fit_df["tput"]

            y_pred = m * x + b

            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            r2 = 1 - ss_res / ss_tot

            x_line = np.linspace(rssi_zero, max_rssi, 100)
            y_line = m * x_line + b

            ax.plot(
                x_line,
                y_line,
                'r--',
                label = "Linear regression"
            )

            # Mark zero-throughput crossing
            ax.axvline(rssi_zero, c='b', ls = ':', label="Sensitivity")
            ax.text(
                rssi_zero+2,
                200,
                f'$S=${rssi_zero:.2f}dB\n$R^2=${r2:.3f}',
                color='b',
                va='top',
                ha='left',
                fontsize=10,
                bbox=dict(
                    facecolor='white',
                    edgecolor='none',
                    alpha=0.8,
                    pad=2
                )
            )
        sns.scatterplot(
            data=l_df,
            x="rssi_"+rx,
            y="tput",
            alpha=0.5,
            s=3,
            ax=ax,
            rasterized=True,
        )

for i in range(3):
    axes_se[i, 1].sharey(axes_se[i, 0])
    axes_se[i, 1].tick_params(labelleft=False)
    for j in range(2):
        ax = axes_se[i, j]
        ax.set_xlim(-97,-35)
        ax.set_ylim(0, 220)
        ax.grid()
        ax.set_title("")
        if (i,j) != (2,0):
            ax.get_legend().remove()
        if i < 2:
            ax.set_xlabel("")
        else:
            if j == 0 :
                ax.set_xlabel("$P_{RX,\\text{DL}}$ (dBm)")
            else:
                ax.set_xlabel("$P_{RX,\\text{UL}}$ (dBm)")
        if i == 0:
            ax.set_title(["Downlink", "Uplink"][j], fontsize= 9)
        
        ax.set_ylabel(f"{suffixes[i]}")

        ax.set_yticks([0, 50, 100, 150, 200])
        ax.set_xticks([-80, -60, -40])
    axes_se[i, 0].set_ylabel('')
    axes_se[i, 1].yaxis.set_label_position("right")

axes_se[2,1].legend(
                    loc="upper center",
                    bbox_to_anchor=(0, -0.3),  # below the axes
                    fontsize=9,
                    handlelength=1.5,
                    ncols=2,
                    markerscale=2,
)
fig_se.supylabel("Throughput (Mbit/s)", fontsize=10)
fig_se.set_size_inches(fig_se.get_size_inches()[0], 3.3)
fig_se.subplots_adjust(left=0.17, right=1, top=0.9, bottom=0.1,
                    wspace=0.05, hspace=0.05)
fig_se.savefig(f"./graphs/{suffix}_{l_label}_SE.pdf")


fig, ax = plt.subplots(1, 1, figsize=(3, 3))
ax.imshow(background)
sns.scatterplot(ax=ax, data = df, x= "x", y="y", s=50, label="Client positions")

for spine in ax.spines.values():
    spine.set_visible(False)

# Define the shape of our reference for the phone orientation

verts = [
    # x axis
    (0, 0.6), (0, 0), (0.6, 0),

    # x arrowhead triangle
    (0.6, 0),
    (0.45, 0.125),
    (0.45, -0.125),
    (0.6, 0),


    # y arrowhead triangle
    (0, 0.6),
    (0.125, 0.45),
    (-0.125, 0.45),
    (0, 0.6),
]

codes = [
    # x axis
    Path.MOVETO, Path.LINETO, Path.LINETO,

    # x triangle
    Path.MOVETO,
    Path.LINETO,
    Path.LINETO,
    Path.CLOSEPOLY,

    # y triangle
    Path.MOVETO,
    Path.LINETO,
    Path.LINETO,
    Path.CLOSEPOLY,
]
axis_marker = Path(verts, codes)

marker_rot = Affine2D().rotate_deg(180).transform_path(axis_marker)
ax.scatter([1370],[275],color='r',
           marker = marker_rot, linewidth=1.2,
           s=300, label="AP position",
           facecolors='none',
       )

ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlim(0, w)
ax.set_ylim(h, 0)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 0),  # below the axes
    fontsize=9,
    handlelength=1,
    ncols=2,
    handletextpad=0.3,
    columnspacing=1,  # default is ~2.0
)
plt.annotate(
             text='',
             xy=(50,50),
             xytext=(50,1950),
             arrowprops=dict(arrowstyle='<->', color='xkcd:black'),
         )
ax.text(
    50,
    2000/2,
    '7.4m',
    va='center',
    ha='right',
    rotation=90,
    fontsize=10,
)
plt.annotate(
             text='',
             xy=(100, 25),
             xytext=(2100,25),
             arrowprops=dict(arrowstyle='<->', color='xkcd:black')
         )
ax.text(
    2200/2,
    25,
    '7.7m',
    va='bottom',
    ha='center',
    fontsize=10,
)
ax.text(
    750,
    1300,
    '52m²',
    va='top',
    ha='left',
    fontsize=10,
)
fig.tight_layout()
fig.set_size_inches(fig_se.get_size_inches()[0], 2.25)
fig.savefig("./graphs/plan_croppd.pdf")

fig, ax = plt.subplots(1, 1, figsize=(3, 3))
ax.imshow(background)
sns.scatterplot(ax=ax, data = df, x= "x", y="y", s=50, label="Client positions")
ax.scatter([1370],[275],color='r',
           marker = marker_rot, linewidth=1.2,
           s=300, label="AP position",
           facecolors='none',
       )


grid_x, grid_y = np.meshgrid(
    np.linspace(0, w, 300),
    np.linspace(0, h, 300)
)

grid_z = grid_f("dtput_CAP", grid_x, grid_y, df)

vmin = np.nanmin(grid_z)
vmax = np.nanmax(grid_z)
heat = ax.imshow(
    grid_z,
    extent=(0, w, h, 0),
    alpha=0.5,
    vmin=vmin,
    vmax=vmax
)
levels = [50, 75]

contours = ax.contour(
    grid_x,
    grid_y,
    grid_z,
    levels=levels,
    colors=['yellow', 'red'],
    linewidths=1.5,
    alpha=0.9
)

ax.clabel(contours, inline=True, fontsize=8, fmt='%d')
cbar = fig.colorbar(heat, ax=ax, orientation='vertical',fraction=0.04, pad=0.04)
cbar.set_label("Throughput (Mbit/s)", fontsize=8)

ax.set_xlabel("")
ax.set_ylabel("")
ax.set_xticks([])
ax.set_yticks([])
ax.set_xlim(0, w)
ax.set_ylim(h, 0)

ax.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 0),
    fontsize=9,
    handlelength=1.5,
    ncols=2,
)
plt.tight_layout()
fig.savefig("./graphs/plan_througput_CAP.pdf")

print(f"Minimum downstream throughput measured for CAP: {df['dtput_CAP'].min():.2f}Mbps")
print(f"Minimum upstream throughput measured for CAP: {df['utput_CAP'].min():.2f}Mbps")
