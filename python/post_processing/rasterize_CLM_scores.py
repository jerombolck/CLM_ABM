import raster
import geopandas as gpd
from osgeo.ogr import UseExceptions

UseExceptions()

scores_fp = "data/pre_processing/overvecht_score_nodes.gpkg"

columns = gpd.read_file(scores_fp, layer="scores").columns

print("Interpolating scores")

for col in columns:
    if col.find("_score") > -1:
        raster.grid_nearest_neigbour(scores_fp, col, f"data/results/{col}_rasterized.tif", point_features_layer="scores")

print("Computing difference between scoring scenarios")

raster.difference(f"data/results/biodiversity_score_less_strict_rasterized.tif", "data/results/biodiversity_score_rasterized.tif", "data/results/biodiversity_score_less_strict_difference.tif")
raster.difference(f"data/results/archetypal_score_less_strict_rasterized.tif", "data/results/archetypal_score_rasterized.tif", "data/results/archetypal_score_less_strict_difference.tif")

for col in columns:
    if col.startswith("CLM_score_less_strict"):
        raster.difference(f"data/results/{col}_rasterized.tif", "data/results/CLM_score_rasterized.tif", f"data/results/{col}_difference.tif")