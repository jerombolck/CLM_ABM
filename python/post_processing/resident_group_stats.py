import geopandas as gpd
import matplotlib.pyplot as plt

resident_scores = gpd.read_file("data/post_processing/resident_scores_high-activity_20kmh_combined.gpkg")

stats = resident_scores.groupby(by="RESGROUP").agg(
    mean_biodiversity_score = ("BIODIVSCR", "mean"),
    mean_layers_score = ("LAYERSSCR", "mean"),
    mean_archetypal_score = ("ARCHTPSCR", "mean"),
    mean_peace_score = ("PEACESCR", "mean"),
    mean_CLM_score = ("CLMSCR", "mean"),
    min_CLM_score = ("CLMSCR", "min"),
    max_CLM_score = ("CLMSCR", "max"),
    std_CLM_score = ("CLMSCR", "std")
)

print(stats)

plt.bar(stats.index, stats.mean_CLM_score)
plt.show()