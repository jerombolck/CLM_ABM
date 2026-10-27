import pandas as pd
import geopandas as gpd
import os

gdf_list = []

for i in range(0, 99):
    gdf_list.append(gpd.read_file(f"data/model_output/score_points_{i}.shp"))