import osgeo
import geopandas as gpd
import requests
import rasterio
from rasterio.merge import merge
from io import BytesIO
import math

WCS_URL = "https://service.pdok.nl/rws/actueel-hoogtebestand-nederland/wcs/v1_0"
RESOLUTION = 0.5
MAX_PX = 4000

# Get bounds from study area
study_area = gpd.read_file("data/source/study_area.gpkg").to_crs("EPSG:28992")
minx, miny, maxx, maxy = study_area.total_bounds

# Calculate tile size (meters) and amount of tiles required
tile_size = MAX_PX * RESOLUTION
n_tiles_x = math.ceil((maxx - minx) / tile_size)
n_tiles_y = math.ceil((maxy - miny) / tile_size)
print(f"Downloading DTM from PDOK in {n_tiles_x * n_tiles_y} tiles ({n_tiles_x} x {n_tiles_y})")

datasets = []
for ty in range(n_tiles_y):
    for tx in range(n_tiles_x):
        tile_minx = minx + tx * tile_size
        tile_miny = miny + ty * tile_size
        tile_maxx = min(tile_minx + tile_size, maxx)
        tile_maxy = min(tile_miny + tile_size, maxy)

        width  = int((tile_maxx - tile_minx) / RESOLUTION)
        height = int((tile_maxy - tile_miny) / RESOLUTION)

        print(f"  Tile ({tx}, {ty}): {width}x{height} px", end="  ")
        response = requests.get(WCS_URL, params={
            "SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": "GetCoverage",
            "COVERAGEID": "dtm_05m", "FORMAT": "image/tiff",
            "SUBSET": [f"x({tile_minx},{tile_maxx})", f"y({tile_miny},{tile_maxy})"],
            "SCALESIZE": f"x({width}),y({height})",
            "SUBSETTINGCRS": "http://www.opengis.net/def/crs/EPSG/0/28992",
            "OUTPUTCRS": "http://www.opengis.net/def/crs/EPSG/0/28992",
        })
        response.raise_for_status()
        datasets.append(rasterio.open(BytesIO(response.content)))
        print("OK")

# Merge tile datasets and update profile to match
mosaic, transform = merge(datasets)
profile = datasets[0].profile
profile.update(transform=transform, width=mosaic.shape[2], height=mosaic.shape[1])

with rasterio.open("ahn_dtm.tif", "w", **profile) as dst:
    dst.write(mosaic)

for ds in datasets:
    ds.close()

print("DTM downloaded succesfully")