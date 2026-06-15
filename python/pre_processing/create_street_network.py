import matplotlib.pyplot as plt

import numpy as np
import os
import osmnx as ox
import pandas as pd
import geopandas as gpd
import neatnet as nn


def download_network():
    # Get OSM street network for Utrecht
    place = "Utrecht, Netherlands"
    walk_graph = ox.graph_from_place(place, network_type="walk", retain_all=False)

    # Turn into geodataframe and exclude motorways and unclassified
    network_gdf = ox.graph_to_gdfs(walk_graph, nodes=False, edges=True, fill_edge_geometry=True)
    network_gdf = network_gdf.to_crs("EPSG:28992")

    # Clip to study area
    study_area = gpd.read_file("data/source/study_area.gpkg")
    network_gdf = gpd.clip(network_gdf, study_area)
    
    print(network_gdf.head())
    print("Attributes:", list(network_gdf.columns))

    return network_gdf


def clean_network(network):
    # Use homes as mask
    mask = gpd.read_file("data/source/overvecht_homes.gpkg").geometry

    # Explode MultiLineStrings to LineStrings
    network = network.explode(index_parts=False)

    # Clean network
    clean_network = nn.extend_lines(network, tolerance=5, barrier=mask)
    clean_network = nn.close_gaps(clean_network, tolerance=5)

    # Simplify network
    '''simplified_network = nn.neatify(clean_network, 
                                    exclusion_mask=mask, 
                                    max_segment_length=10,
                                    min_dangle_length=10)'''

    return clean_network


if __name__ == "__main__":
    original_file_path = "data/source/overvecht_network.gpkg"
    simplified_file_path = "data/model_input/street_network.gpkg"

    if os.path.exists(original_file_path):
        original_network = gpd.read_file(original_file_path)
    else:
        original_network = download_network()
        original_network.to_file(original_file_path)

    ax = original_network.plot(linewidth=0.05)
    ax.set_axis_off()
    plt.show()

    simplified_network = clean_network(original_network)
    simplified_network.to_file(simplified_file_path)

    fig, axs = plt.subplots(1, 2, figsize=(18, 10))

    original_network.plot(ax=axs[0], linewidth=0.5)
    simplified_network.plot(color="red", linewidth=0.5, ax=axs[1])
    for ax in axs:
        ax.set_axis_off()
    axs[0].set_title("original")
    axs[1].set_title("simplifiied")
    plt.show()
    