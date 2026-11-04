import re
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch

"""Made with the help of genAI"""

PATTERN = re.compile(r"resident_scores_(?P<activity>.+?)_(?P<speed>\d+)kmh_combined\.gpkg$")

def load_scores(folder, group_col="RES_GROUP", score_col="CLM_SCR"):
    """Load all post-processed files into one long DataFrame."""
    frames = []
    for f in Path(folder).glob("resident_scores_*_combined.gpkg"):
        m = PATTERN.match(f.name)
        if m is None:
            continue
        gdf = gpd.read_file(f)
        df = pd.DataFrame(gdf[[group_col, score_col]]).rename(
            columns={group_col: "group", score_col: "score"}
        )
        df["activity"] = m.group("activity")
        df["speed"] = int(m.group("speed"))
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def lighten(color, amount):
    """Blend a colour with white. amount=0 -> original, amount=1 -> white."""
    rgb = np.array(to_rgb(color))
    return tuple(rgb + (1 - rgb) * amount)


def plot_scores_barplot(data, activity_order, base_colors, error="std",
                        ylabel="Mean CLM exposure score", outfile=None):
    groups = sorted(data["group"].unique())
    speeds = sorted(data["speed"].unique())
    n_a, n_s = len(activity_order), len(speeds)

    # Lightest shade for the slowest speed, original colour for the fastest
    shade_amounts = np.linspace(0.55, 0.0, n_s)

    stats = (data.groupby(["group", "activity", "speed"])["score"]
                 .agg(mean="mean", std="std").reset_index())

    total_width = 0.85
    bar_w = total_width / (n_a * n_s)

    fig, ax = plt.subplots(figsize=(9, 5))

    for gi, group in enumerate(groups):
        for ai, activity in enumerate(activity_order):
            for si, speed in enumerate(speeds):
                row = stats[(stats.group == group)
                            & (stats.activity == activity)
                            & (stats.speed == speed)]
                if row.empty:
                    continue
                slot = ai * n_s + si
                x = gi - total_width / 2 + (slot + 0.5) * bar_w
                yerr = row["std"].iloc[0] if error == "std" else None
                ax.bar(
                    x, row["mean"].iloc[0], width=bar_w * 0.95,
                    color=lighten(base_colors[activity], shade_amounts[si]),
                    edgecolor="white", linewidth=0.5,
                    yerr=yerr, error_kw={"elinewidth": 0.8, "capsize": 1.5},
                )

    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Resident group")
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)

    # Legend 1: activity level (colour)
    activity_handles = [Patch(facecolor=base_colors[a], label=a) for a in activity_order]
    leg1 = ax.legend(handles=activity_handles, title="Shopping activity",
                     loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    ax.add_artist(leg1)

    # Legend 2: speed (shade), drawn in neutral grey
    speed_handles = [Patch(facecolor=lighten("#555555", shade_amounts[i]),
                           label=f"{s} km/h") for i, s in enumerate(speeds)]
    ax.legend(handles=speed_handles, title="Walking speed",
              loc="upper left", bbox_to_anchor=(1.01, 0.62), frameon=False)

    plt.tight_layout()
    if outfile:
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    return fig, ax, stats


# Usage
data = load_scores("data/post_processing",
                   group_col="RESGROUP", score_col="CLMSCR")

fig, ax, stats = plot_scores_barplot(
    data,
    activity_order=["low", "baseline", "high"],
    base_colors={"low": "#1f77b4", "baseline": "#2ca02c", "high": "#d62728"},
    error="std",
    outfile="figures/scores_by_group_activity_speed.png",
)