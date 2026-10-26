import pandas as pd
import geopandas as gpd
import os

resident_score_gdfs = []
score_point_gdfs = []

score_points = gpd.read_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="scores")

for i in range(0, 99):
    resident_score_gdfs.append(gpd.read_file(f"data/model_output/resident_scores_{i}.shp"))
    score_points = score_points.merge(gpd.read_file(f"data/model_output/score_points_{i}.shp"), on="geometry",suffixes=("", f"_{i}"))

resident_scores_combined = gpd.GeoDataFrame(pd.concat(resident_score_gdfs))
resident_scores_combined = resident_scores_combined.to_crs("EPSG:28992")

visits_columns = score_points.columns[score_points.columns.str.startswith("VISITS") == True]

score_points["total_visits"] = score_points[visits_columns].sum(axis=1)
score_points["average_visits"] = score_points[visits_columns].mean(axis=1)

keep_columns = ["geometry", "biodiversity_score", "layers_score", "archetypal_score", "peace_score", "CLM_score", "total_visits", "average_visits"]

score_points_visited = score_points[keep_columns].copy()

if not os.path.exists("data/results"):
    os.makedirs("data/results")

resident_scores_combined.to_file("data/results/resident_scores_combined.gpkg")
score_points_visited.to_file("data/results/score_points_visited.gpkg")