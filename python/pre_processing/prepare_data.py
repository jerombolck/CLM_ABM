from study_area import download_study_area
from terrain import load_terrain
from visibility import visibility_analysis
from biodiversity import compute_biodiversity_score
from archetypal_elements import compute_archetypal_score
from peace_and_silence import compute_peace_score
import street_network as nw

import pandas as pd
import geopandas as gpd
from pyogrio.errors import DataSourceError
from rasterio.errors import RasterioIOError

from joblib import Parallel, delayed
from tqdm import tqdm
import os


if not os.path.exists("data/source/study_area.gpkg"):
    print("Downloading study area")
    download_study_area()

try:
    print("Opening required data files")
    buildings = gpd.read_file("data/source/overvecht_buildings.gpkg")
    workplaces = gpd.read_file("data/source/overvecht_workplaces.gpkg")
    homes = gpd.read_file("data/source/overvecht_homes.gpkg")
    shops = gpd.read_file("data/source/overvecht_shops.gpkg")
    trees = gpd.read_file("data/source/overvecht_trees.gpkg")
    water = gpd.read_file("data/source/overvecht_water.gpkg")
    monuments = gpd.read_file("data/source/overvecht_monuments.gpkg")

    study_area = gpd.read_file("data/source/study_area.gpkg")
    dtm, dtm_extent, dtm_transform = load_terrain("data/source/overvecht_dtm_test.tif")

except (DataSourceError, RasterioIOError) as e:
    print(f"Cannot prepare data, because one or more of the required data files cannot be opened: {e}")
    exit()

nw_nodes, nw_edges = nw.download_network()
score_nodes = nw.split_network(nw_nodes, nw_edges)

visibility_gdf = visibility_analysis([(node.x, node.y) for node in score_nodes.sample(25)], buildings, dtm, dtm_transform)

score_gdf = gpd.GeoDataFrame(visibility_gdf[["node_id", "layers_score"]], geometry=visibility_gdf.geometry, crs=study_area.crs)
isovist_gdf = gpd.GeoDataFrame(visibility_gdf["node_id"], geometry=visibility_gdf["isovist"], crs=study_area.crs)

isovist_gdf = isovist_gdf.clip(study_area, sort=True)

score_gdf = score_gdf.merge(isovist_gdf, on="node_id", suffixes=(None, "_isovist"))

biodiversity_file_paths = {
        "bee_richness": "data/source/overvecht_bee_richness.tif",
        "grass_vegetation": "data/source/overvecht_grass_raster.tif",
        "shrub_vegetation": "data/source/overvecht_shrubs_raster.tif",
        "tree_vegetation": "data/source/overvecht_trees_raster.tif",
    }

score_gdf["biodiversity_score"] = Parallel(n_jobs=-1)(
        delayed(compute_biodiversity_score)(node["properties"]["geometry_isovist"], trees, biodiversity_file_paths)
        for node in tqdm(score_gdf.iterfeatures(), "Computing biodiversity scores")
    )

score_gdf["archetypal_score"] = Parallel(n_jobs=-1)(
        delayed(compute_archetypal_score)(node["geometry"]["coordinates"], node["properties"]["geometry_isovist"], monuments, trees, water, buildings)
        for node in tqdm(score_gdf.iterfeatures(), "Computing archetypal elements scores")
    )

score_gdf["peace_score"] = Parallel(n_jobs=-1)(
        delayed(compute_peace_score)(node["geometry"]["coordinates"], "data/source/overvecht_noise_raster.tif")
        for node in tqdm(score_gdf.iterfeatures(), "Computing peace and silence scores")
    )

if not os.path.exists("data/pre_processing"):
    os.makedirs("data/pre_processing")

score_gdf.drop("geometry_isovist", axis=1).to_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="scores")
isovist_gdf.to_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="isovists")