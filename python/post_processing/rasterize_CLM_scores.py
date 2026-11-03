import rasterize
import geopandas as gpd
from osgeo.ogr import UseExceptions

UseExceptions()

scores_fp = "data/pre_processing/overvecht_score_nodes.gpkg"

columns = gpd.read_file(scores_fp, layer="scores").columns

for col in columns:
    if col.find("_score") > -1:
        rasterize.nearest_neigbour(scores_fp, col, f"data/results/{col}_rasterized.tif", point_features_layer="scores")
