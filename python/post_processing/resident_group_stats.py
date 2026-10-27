import geopandas as gpd
import matplotlib.pyplot as plt

resident_scores = gpd.read_file("data/results/resident_scores_combined.gpkg")

stats = resident_scores.groupby(by="RESGROUP").agg(
    mean_biodiversity_score = ("BIODIVSCR", "mean"),
    mean_layers_score = ("LAYERSSCR", "mean"),
    mean_archetypal_score = ("ARCHTPSCR", "mean"),
    mean_peace_score = ("PEACESCR", "mean"),
    mean_CLM_score = ("CLMSCR", "mean"),
    min_CLM_score = ("CLMSCR", "min"),
    max_CLM_score = ("CLMSCR", "max"),
)

stats_sample = stats.sample(5)

plt.bar(stats_sample.index, stats_sample.mean_CLM_score)
plt.show()