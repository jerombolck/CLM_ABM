import geopandas as gpd
import numpy as np
from osgeo import gdal, ogr
import os
import rasterio

def grid_nearest_neigbour(point_features_fp, point_features_zfield, output_fp, point_features_layer = None, cell_size = 10):
    study_area_fp = "data/source/study_area.gpkg"
    study_area_dataset = ogr.Open(study_area_fp)
    study_area_layer = study_area_dataset.GetLayer()

    tmp_fp = "/vsimem/rasterize_nn.tif"

    xmin, xmax, ymin, ymax = study_area_layer.GetExtent()
    srs_wkt = study_area_layer.GetSpatialRef().ExportToWkt()

    width = int(round((xmax-xmin)/cell_size))
    height = int(round((ymax-ymin)/cell_size))

    grid_kwargs = dict(
        format="GTiff",
        outputType=gdal.GDT_Float32,
        algorithm=f"nearest:radius1=0:radius2=0:nodata={np.nan}",
        zfield=point_features_zfield,
        outputBounds=[xmin, ymax, xmax, ymin],
        width=width,
        height=height,
        outputSRS=srs_wkt,
    )

    if point_features_layer:
        grid_kwargs["layers"] = [point_features_layer]

    gdal.Grid(tmp_fp, point_features_fp, options=gdal.GridOptions(**grid_kwargs))

    warp_options = gdal.WarpOptions(
        format="GTiff",
        cutlineDSName=study_area_fp,
        cutlineLayer=study_area_layer.GetName(),
        cropToCutline=False,        # keep the grid exactly as created (no resampling or shifting)
        dstNodata=np.nan,
        creationOptions=["COMPRESS=LZW"],
    )

    gdal.Warp(output_fp, tmp_fp, options=warp_options)

    gdal.Unlink(tmp_fp)


def difference(rast1_fp, rast2_fp, out_fp):
    with rasterio.open(rast1_fp) as rast1:
        rast1_data = rast1.read()

    with rasterio.open(rast2_fp) as rast2:
        rast2_data = rast2.read()

    diff_data = rast1_data - rast2_data
    diff_kwargs = rast1.meta

    with rasterio.open(out_fp, 'w', **diff_kwargs) as diff:
        diff.write(diff_data.astype(rasterio.float32))