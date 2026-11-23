from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

"""Code made with the help of genAI: Claude Sonnet 5.5"""

def load_scenarios(files, group_col="RESGROUP", score_col="CLMSCR"):
    """
    files: {scenario_name: path to .gpkg}
    Returns a long DataFrame with columns: group, score, scenario.
    """
    frames = []
    for scenario, path in files.items():
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"{scenario}: {path} does not exist")
        gdf = gpd.read_file(path)
        df = pd.DataFrame(gdf[[group_col, score_col]]).rename(
            columns={group_col: "group", score_col: "score"})
        df["scenario"] = scenario
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _group_order(data, include_overall):
    groups = sorted(data["group"].unique())
    return groups + ["All residents"] if include_overall else groups


def _add_overall(data):
    overall = data.copy()
    overall["group"] = "All residents"
    return pd.concat([data, overall], ignore_index=True)


def plot_scenario_comparison(data, scenario_order, colors, include_overall=True,
                             error="sd", ylabel="Mean CLM exposure score",
                             outfile=None):
    """Grouped bars: resident groups on the x-axis, one bar per scoring scenario."""
    d = _add_overall(data) if include_overall else data
    groups = _group_order(data, include_overall)

    stats = (d.groupby(["group", "scenario"])["score"]
               .agg(mean="mean", sd="std").reset_index())

    total_width = 0.8
    bar_w = total_width / len(scenario_order)

    fig, ax = plt.subplots(figsize=(9, 5))
    for si, scenario in enumerate(scenario_order):
        sub = stats[stats.scenario == scenario].set_index("group").reindex(groups)
        x = np.arange(len(groups)) - total_width / 2 + (si + 0.5) * bar_w
        ax.bar(x, sub["mean"], width=bar_w * 0.95, color=colors[scenario],
               edgecolor="white", linewidth=0.5, label=scenario,
               yerr=sub["sd"] if error == "sd" else None,
               error_kw={"elinewidth": 0.8, "capsize": 2})

    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_xlabel("Resident group")
    ax.set_ylabel(ylabel)
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(title="Scoring scenario", loc="upper left",
              bbox_to_anchor=(1.01, 1.0), frameon=False)

    fig.subplots_adjust(right=0.80)
    if outfile:
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    return fig, ax, stats


def plot_scenario_deltas(data, scenario_order, colors, ref_scenario="baseline",
                         include_overall=True, error=None,
                         ylabel="Δ CLM score vs. baseline scenario",
                         outfile=None):
    """Grouped bars of the difference to the baseline scenario per resident group."""
    d = _add_overall(data) if include_overall else data
    groups = _group_order(data, include_overall)

    stats = (d.groupby(["group", "scenario"])["score"]
               .agg(mean="mean", sd="std", n="count").reset_index())
    ref = (stats[stats.scenario == ref_scenario]
           .set_index("group")[["mean", "sd", "n"]].add_prefix("ref_"))
    stats = stats.join(ref, on="group")
    stats["delta"] = stats["mean"] - stats["ref_mean"]
    stats["se"] = np.sqrt(stats["sd"]**2 / stats["n"]
                          + stats["ref_sd"]**2 / stats["ref_n"])

    scenarios = [s for s in scenario_order if s != ref_scenario]
    total_width = 0.8
    bar_w = total_width / len(scenarios)

    fig, ax = plt.subplots(figsize=(9, 5))
    for si, scenario in enumerate(scenarios):
        sub = stats[stats.scenario == scenario].set_index("group").reindex(groups)
        x = np.arange(len(groups)) - total_width / 2 + (si + 0.5) * bar_w
        ax.bar(x, sub["delta"], width=bar_w * 0.95, color=colors[scenario],
               edgecolor="white", linewidth=0.5, label=scenario,
               yerr=sub["se"] if error == "se" else None,
               error_kw={"elinewidth": 0.8, "capsize": 2})

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_xlabel("Resident group")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(title="Scoring scenario", loc="upper left",
              bbox_to_anchor=(1.01, 1.0), frameon=False)

    fig.subplots_adjust(right=0.80)
    if outfile:
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    return fig, ax, stats



if __name__ == "__main__":
    folder = Path("data/post_processing")
    files = {
        "baseline":            folder / "resident_scores_baseline_5kmh_combined.gpkg",
        "less_strict_biodiversity":       folder / "resident_scores_less_strict_biodiversity_combined.gpkg",
        "less_strict_archetypal_elements":            folder / "resident_scores_less_strict_archetypal_elements_combined.gpkg",
        "combined_less_strict": folder / "resident_scores_combined_less_strict_combined.gpkg",
    }

    data = load_scenarios(files)
    print(data.groupby("scenario")["score"].agg(["count", "mean"]))   # sanity check

    scenario_order = ["baseline", "less_strict_biodiversity", "less_strict_archetypal_elements", "combined_less_strict"]
    colors = {"baseline": "#4d4d4d", "less_strict_biodiversity": "#2ca02c",
            "less_strict_archetypal_elements": "#1f77b4", "combined_less_strict": "#d62728"}

    plot_scenario_comparison(data, scenario_order, colors,
                            outfile="figures/scenario_comparison_bars.png")
    plot_scenario_deltas(data, scenario_order, colors,
                        outfile="figures/scenario_deltas_bars.png")