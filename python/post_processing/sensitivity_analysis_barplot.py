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

    fig, ax = plt.subplots(figsize=(10, 5))

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
    fig.legend(handles=activity_handles, title="Shopping activity",
               loc="upper left", bbox_to_anchor=(0.82, 0.9), frameon=False)

    # Legend 2: speed (shade), drawn in neutral grey
    speed_handles = [Patch(facecolor=lighten("#555555", shade_amounts[i]),
                           label=f"{s} km/h") for i, s in enumerate(speeds)]
    fig.legend(handles=speed_handles, title="Walking speed",
               loc="upper left", bbox_to_anchor=(0.82, 0.7), frameon=False)
    
    fig.subplots_adjust(right=0.82)

    if outfile:
        plt.savefig(outfile, dpi=300, bbox_inches="tight")

    return fig, ax, stats


def plot_delta_barplot(data, activity_order, base_colors,
                       ref_activity="baseline", ref_speed=5,
                       error="se", ylabel=None, outfile=None):
    groups = sorted(data["group"].unique())
    speeds = sorted(data["speed"].unique())
    n_a, n_s = len(activity_order), len(speeds)
    shade_amounts = np.linspace(0.55, 0.0, n_s)

    stats = (data.groupby(["group", "activity", "speed"])["score"]
                 .agg(mean="mean", std="std", n="count").reset_index())

    # Reference mean, std and n per resident group
    ref = (stats[(stats.activity == ref_activity) & (stats.speed == ref_speed)]
           .set_index("group")[["mean", "std", "n"]]
           .add_prefix("ref_"))
    stats = stats.join(ref, on="group")

    stats["delta"] = stats["mean"] - stats["ref_mean"]
    # Standard error of a difference of two independent means
    stats["se"] = np.sqrt(stats["std"]**2 / stats["n"]
                          + stats["ref_std"]**2 / stats["ref_n"])

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
                yerr = row["se"].iloc[0] if error == "se" else None
                ax.bar(
                    x, row["delta"].iloc[0], width=bar_w * 0.95,
                    color=lighten(base_colors[activity], shade_amounts[si]),
                    edgecolor="white", linewidth=0.5,
                    yerr=yerr, error_kw={"elinewidth": 0.8, "capsize": 1.5},
                )

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_xlabel("Resident group")
    ax.set_ylabel(ylabel or f"Δ CLM score vs. {ref_activity} activity, {ref_speed} km/h")
    ax.spines[["top", "right"]].set_visible(False)

    # Legend 1: activity level (colour)
    activity_handles = [Patch(facecolor=base_colors[a], label=a) for a in activity_order]
    fig.legend(handles=activity_handles, title="Shopping activity",
               loc="upper left", bbox_to_anchor=(0.82, 0.9), frameon=False)

    # Legend 2: speed (shade), drawn in neutral grey
    speed_handles = [Patch(facecolor=lighten("#555555", shade_amounts[i]),
                           label=f"{s} km/h") for i, s in enumerate(speeds)]
    fig.legend(handles=speed_handles, title="Walking speed",
               loc="upper left", bbox_to_anchor=(0.82, 0.7), frameon=False)
    
    fig.subplots_adjust(right=0.82)

    if outfile:
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
        
    return fig, ax, stats


if __name__ == "__main__":
    data = load_scores("data/post_processing",
                    group_col="RESGROUP", score_col="CLMSCR")

    fig, ax, stats = plot_delta_barplot(
        data,
        activity_order=["low_activity", "baseline", "high_activity"],
        base_colors={"low_activity": "#1f77b4", "baseline": "#2ca02c", "high_activity": "#d62728"},
        ref_activity="baseline",
        ref_speed=5,
        error="se",
        outfile="figures/delta_scores_by_group_activity_speed.png",
    )

    fig, ax, stats = plot_scores_barplot(
        data,
        activity_order=["low_activity", "baseline", "high_activity"],
        base_colors={"low_activity": "#1f77b4", "baseline": "#2ca02c", "high_activity": "#d62728"},
        error="std",
        outfile="figures/scores_by_group_activity_speed.png",
    )