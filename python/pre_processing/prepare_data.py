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


def prepare_directories():
    if not os.path.exists("data/pre_processing"):
        os.makedirs("data/pre_processing")

    if not os.path.exists("data/model_input"):
        os.makedirs("data/model_input")

    if not os.path.exists("data/model_output"):
        os.makedirs("data/model_output")


def prepare_study_area():
    if not os.path.exists("data/source/study_area.gpkg"):
        print("Downloading study area")
        download_study_area()

    return gpd.read_file("data/source/study_area.gpkg")


def prepare_network_locations(recompute=False):
    if (recompute or not os.path.exists("data/model_input/workplaces.shp")):
        workplaces = gpd.read_file("data/source/overvecht_workplaces.gpkg")
        workplaces.geometry.to_crs("EPSG:32632").to_file("data/model_input/workplaces.shp") 
    
    if (recompute or not os.path.exists("data/model_input/homes.shp")):
        homes = gpd.read_file("data/source/overvecht_homes.gpkg")
        homes.geometry.to_crs("EPSG:32632").to_file("data/model_input/homes.shp")
    
    if (recompute or not os.path.exists("data/model_input/shops.shp")):
        shops = gpd.read_file("data/source/overvecht_shops.gpkg")
        shops.geometry.to_crs("EPSG:32632").to_file("data/model_input/shops.shp")


def prepare_network():
    nw_nodes, nw_edges = nw.download_network()
    nw_edges.to_crs("EPSG:32632").to_file("data/model_input/street_network.shp")

    return nw.split_network(nw_nodes, nw_edges)


def prepare_isovists(study_area, score_points, recompute=False):
    buildings = gpd.read_file("data/source/overvecht_buildings.gpkg")
    dtm, dtm_extent, dtm_transform = load_terrain("data/source/overvecht_dtm_test.tif")

    if (recompute or not os.path.exists("data/pre_processing/overvecht_score_nodes.gpkg")):
        visibility_gdf = visibility_analysis([(node.x, node.y) for node in score_points], buildings, dtm, dtm_transform)

        score_gdf = gpd.GeoDataFrame(visibility_gdf[["node_id", "layers_score"]], geometry=visibility_gdf.geometry, crs=study_area.crs)
        isovist_gdf = gpd.GeoDataFrame(visibility_gdf["node_id"], geometry=visibility_gdf["isovist"], crs=study_area.crs)

        print("Clipping isovists to study area")
        isovist_gdf = isovist_gdf.clip(study_area)

        score_gdf.to_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="scores")
        isovist_gdf.to_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="isovists")


def prepare_scores():
    trees = gpd.read_file("data/source/overvecht_trees.gpkg")
    water = gpd.read_file("data/source/overvecht_water.gpkg")
    monuments = gpd.read_file("data/source/overvecht_monuments.gpkg")
    buildings = gpd.read_file("data/source/overvecht_buildings.gpkg")

    score_gdf = gpd.read_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="scores")
    isovist_gdf = gpd.read_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="isovists")

    score_gdf = score_gdf.merge(isovist_gdf, on="node_id", suffixes=(None, "_isovist"))

    print(score_gdf.columns)

    total_score_points = len(score_gdf)

    biodiversity_file_paths = {
            "bee_richness": "data/source/overvecht_bee_richness.tif",
            "grass_vegetation": "data/source/overvecht_grass_raster.tif",
            "shrub_vegetation": "data/source/overvecht_shrubs_raster.tif",
            "tree_vegetation": "data/source/overvecht_trees_raster.tif",
        }

    score_gdf["biodiversity_score"] = Parallel(n_jobs=-1)(
            delayed(compute_biodiversity_score)(node["properties"]["geometry_isovist"], trees, biodiversity_file_paths)
            for node in tqdm(score_gdf.iterfeatures(), "Computing biodiversity scores", total_score_points)
        )
    
    score_gdf["biodiversity_score_less_strict"] = Parallel(n_jobs=-1)(
            delayed(compute_biodiversity_score)(node["properties"]["geometry_isovist"], trees, biodiversity_file_paths, True)
            for node in tqdm(score_gdf.iterfeatures(), "Computing biodiversity scores", total_score_points)
        )

    score_gdf["archetypal_score"] = Parallel(n_jobs=-1)(
            delayed(compute_archetypal_score)(node["geometry"]["coordinates"], node["properties"]["geometry_isovist"], monuments, trees, water, buildings)
            for node in tqdm(score_gdf.iterfeatures(), "Computing archetypal elements scores", total_score_points)
        )
    
    score_gdf["archetypal_score_less_strict"] = Parallel(n_jobs=-1)(
            delayed(compute_archetypal_score)(node["geometry"]["coordinates"], node["properties"]["geometry_isovist"], monuments, trees, water, buildings, 60)
            for node in tqdm(score_gdf.iterfeatures(), "Computing archetypal elements scores", total_score_points)
        )

    score_gdf["peace_score"] = Parallel(n_jobs=-1)(
            delayed(compute_peace_score)(node["geometry"]["coordinates"], "data/source/overvecht_noise_raster.tif")
            for node in tqdm(score_gdf.iterfeatures(), "Computing peace and silence scores", total_score_points)
        )

    score_gdf["CLM_score"] = score_gdf[["layers_score", "biodiversity_score", "archetypal_score", "peace_score"]].mean(axis=1)
    score_gdf["CLM_score_less_strict_biodiversity"] = score_gdf[["layers_score", "biodiversity_score_less_strict", "archetypal_score", "peace_score"]].mean(axis=1)
    score_gdf["CLM_score_less_strict_archetypal"] = score_gdf[["layers_score", "biodiversity_score", "archetypal_score_less_strict", "peace_score"]].mean(axis=1)
    score_gdf["CLM_score_less_strict_combined"] = score_gdf[["layers_score", "biodiversity_score_less_strict", "archetypal_score_less_strict", "peace_score"]].mean(axis=1)
    
    score_gdf = score_gdf.drop("geometry_isovist", axis=1)

    score_gdf.to_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="scores")

    scores_model_input = score_gdf.to_crs("EPSG:32632").rename(columns={
        "layers_score": "layers_scr",
        "biodiversity_score": "biodiv_scr",
        "archetypal_score": "archtp_scr",
        "peace_score": "peace_scr",
        "CLM_score": "CLM_scr",
        "biodiversity_score_less_strict": "biodiv_ls",
        "archetypal_score_less_strict": "archtp_ls",
        "CLM_score_less_strict_biodiversity": "CLM_ls_bio",
        "CLM_score_less_strict_archetypal": "CLM_ls_arc",
        "CLM_score_less_strict_combined": "CLM_ls_com",

    })
    scores_model_input.to_file(f"data/model_input/score_points.shp")


if __name__ == "__main__":
    prepare_directories()
    prepare_network_locations()

    study_area = prepare_study_area()
    score_points = prepare_network()
    score_gdf = prepare_isovists(study_area, score_points)

    prepare_scores()