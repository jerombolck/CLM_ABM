import pandas as pd
import geopandas as gpd
import os

gdf_list = []

for i in range(0, 100):
    gdf_list.append(gpd.read_file(f"data/model_output/resident_scores_{i}.shp"))

results = gpd.GeoDataFrame(pd.concat(gdf_list))
results = results.to_crs("EPSG:28992")

if not os.path.exists("data/results"):
    os.makedirs("data/results")

results.to_file("data/results/resident_scores_combined.gpkg")