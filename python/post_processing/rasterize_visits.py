import os
import raster
from osgeo.ogr import UseExceptions

UseExceptions()

for file in os.listdir("data/post_processing"):
    if file.startswith("score_points_"):
        i1 = len("score_points_")
        i2 = file.rindex("_")
        output_fp = f"data/results/visits_{file[i1:i2]}_rasterized.tif"
        raster.grid_nearest_neigbour(f"data/post_processing/{file}", "mean_visits", output_fp)