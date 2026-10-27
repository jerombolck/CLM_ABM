import pandas as pd
import geopandas as gpd
import os

gdf_list = []

for i in range(0, 100):
    gdf = gpd.read_file(f"data/model_output/score_points_{i}.shp")
    gdf["model_run"] = i
    gdf_list.append(gdf)

combined = pd.concat(gdf_list, ignore_index=True)
combined["geom_wkt"] = combined.geometry.to_wkt()

aggregated = combined.dissolve(
        by="geom_wkt",
        aggfunc={
            "VISITS": ["sum", "mean", "std", "min", "max"],
            "model_run": ["count"],
            "BIODIVSCR": ["mean"],
            "LAYERSSCR": ["mean"],
            "ARCHTPSCR": ["mean"],
            "PEACESCR": ["mean"],
            "CLMSCR": ["mean"],
        }
    ).reset_index()

aggregated = aggregated.drop("geom_wkt", axis=1)
aggregated = aggregated.rename(columns={
    ('VISITS', 'sum'): "total_visits",
    ('VISITS', 'mean'): "mean_visits",       
    ('VISITS', 'std'): "std_visits",
    ('VISITS', 'min'): "min_visits",       
    ('VISITS', 'max'): "max_visits",
    ('model_run', 'count'): "model_runs", 
    ('BIODIVSCR', 'mean'): "biodiversity_score",   
    ('LAYERSSCR', 'mean'): "layers_score",
    ('ARCHTPSCR', 'mean'): "archetypal_score",    
    ('PEACESCR', 'mean'): "peace_score",
    ('CLMSCR', 'mean'): "CLM_score"
})

aggregated_gdf = gpd.GeoDataFrame(aggregated)

if not os.path.exists("data/results"):
    os.makedirs("data/results")

aggregated_gdf.to_file("data/results/score_points_aggregated.gpkg")