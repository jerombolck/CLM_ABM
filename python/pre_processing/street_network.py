import matplotlib.pyplot as plt

import numpy as np
import osmnx as ox
import pandas as pd
import geopandas as gpd


def download_network(place = "Utrecht, Netherlands"):
    # Get OSM street network for Utrecht
    print(f"Downloading street network for {place}.")
    walk_graph = ox.graph_from_place(place, network_type="walk", retain_all=False)
    walk_graph_undirected = ox.convert.to_undirected(walk_graph)

    # Turn into geodataframesd
    network_nodes, network_edges = ox.graph_to_gdfs(walk_graph_undirected, nodes=True, edges=True)
    network_nodes = network_nodes.to_crs("EPSG:28992")
    network_edges = network_edges.to_crs("EPSG:28992")

    # Clip to study area
    print("Clipping network to study area.")
    study_area = gpd.read_file("data/source/study_area.gpkg")
    network_nodes = gpd.clip(network_nodes, study_area)
    network_edges = gpd.clip(network_edges, study_area)

    return network_nodes, network_edges


def split_edge(edge, interval):
    """Takes an edge and splits into segments of interval length. Returns list of poins between segments.
    Adapted from: https://stackoverflow.com/questions/62990029/how-to-get-equally-spaced-points-on-a-line-in-shapely/62994304#62994304
    """    
    length = edge.length
    splits = np.arange(interval, length, interval)
    points = [edge.interpolate(s) for s in splits]
    return points


def split_network(network_nodes, network_edges, interval=50, threshold=100):
    print(f"Adding nodes to network edges along {interval}m intervals.")
    extra_points = [point 
                for e in network_edges.geometry 
                if e.length > threshold
                for point in split_edge(e, interval)]
    
    new_nodes = pd.concat([gpd.GeoSeries(extra_points, crs=network_nodes.crs), network_nodes.geometry])
    return new_nodes


if __name__ == "__main__":
    nodes, edges = download_network()
    new_nodes = split_network(nodes, edges)

    fig, ax = plt.subplots(figsize=(8, 8))
    edges.plot(ax=ax, linewidth=0.5, edgecolor="blue", zorder=1)
    new_nodes.plot(ax=ax, markersize=2, color="red", zorder=2)
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()
    