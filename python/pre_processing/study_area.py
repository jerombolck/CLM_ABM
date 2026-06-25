import geopandas as gpd
from owslib.wfs import WebFeatureService
import os

def download_study_area():
    # Connect to WFS
    wfs_url = "https://geodata.utrecht.nl/geoserver/UtrechtOpen/ows"
    wfs = WebFeatureService(url=wfs_url, version='1.1.0')

    # Get the neighbourhood vector data and select Overvecht
    response = wfs.getfeature(typename='UtrechtOpen:GIS_WIJK', outputFormat='application/json')
    gdf = gpd.read_file(response)

    overvecht = gdf[gdf['NAAM_WIJK'] == 'OVERVECHT'].copy()
    overvecht = overvecht.to_crs('EPSG:28992')

    os.makedirs('data/source', exist_ok=True)
    overvecht.to_file("data/source/study_area.gpkg")

