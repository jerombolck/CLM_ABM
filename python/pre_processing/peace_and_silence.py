import rasterio
import numpy as np
import geopandas as gpd
from shapely import from_wkt

def compute_peace_score(location, noise_file_path):
    with rasterio.open(noise_file_path) as noise_dataset:
        noise_data = noise_dataset.read(1)
        row, col = noise_dataset.index(location[0], location[1])
        noise = noise_data[row, col]

    if noise < 40:
        peace_score = 6
    elif noise < 50:
        peace_score = 5
    elif noise < 55:
        peace_score = 4
    elif noise < 60:
        peace_score = 3
    elif noise < 70:
        peace_score = 2
    else:
        peace_score = 1
    
    return peace_score


if __name__ == "__main__":
    nodes = gpd.read_file("data/overvecht_isovists.gpkg", layer="nodes")

    scores = [compute_peace_score((node.x, node.y), "data/source/overvecht_noise_raster.tif") for node in nodes.geometry]
    print("Mean: ", sum(scores) / len(scores))
    
    import matplotlib.pyplot as plt

    plt.bar(x=[1, 2, 3, 4, 5, 6], height=np.histogram(scores, bins=6, range=(1, 6))[0])
    plt.show()