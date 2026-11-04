import pandas as pd
import geopandas as gpd
import os
import re

def combine_resident_scores(file_prefix, file_extension=".shp"):
    gdf_list = []

    for file in os.listdir("data/model_output"):
        if file.startswith(file_prefix) and file.endswith(file_extension):
            gdf_list.append(gpd.read_file(f"data/model_output/{file}"))

    print(f"Combining results from {len(gdf_list)} files starting with '{file_prefix}'")

    results = gpd.GeoDataFrame(pd.concat(gdf_list))
    results = results.to_crs("EPSG:28992")

    if not os.path.exists("data/post_processing"):
        os.makedirs("data/post_processing")

    results.to_file(f"data/post_processing/{file_prefix}_combined.gpkg")


def aggregate_score_point_visits(file_prefix, file_extension=".shp"):
    gdf_list = []

    for file in os.listdir("data/model_output"):
        if file.startswith(file_prefix) and file.endswith(file_extension):
            gdf = gpd.read_file(f"data/model_output/{file}")
            gdf["model_run"] = re.findall(r'\d+', file)[-1]
            gdf_list.append(gdf)

    print(f"Aggregating the visit numbers of the score points from {len(gdf_list)} files starting with '{file_prefix}'")
    
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

    if not os.path.exists("data/post_processing"):
        os.makedirs("data/post_processing")

    aggregated_gdf.to_file(f"data/post_processing/{file_prefix}_aggregated.gpkg")


if __name__ == "__main__":
    activity_levels = ["baseline", "high-activity", "low-activity"]
    resident_speeds = [5, 15, 20]
    alt_scoring_scenarios = ["less-strict-archetypal-elements", "less-strict-biodiversity", "combined-less-strict"]

    model_states = [f"{activity}_{speed}kmh" for activity in activity_levels for speed in resident_speeds]
    model_states += alt_scoring_scenarios

    for state in model_states:
        combine_resident_scores(f"resident_scores_{state}")
        aggregate_score_point_visits(f"score_points_{state}")