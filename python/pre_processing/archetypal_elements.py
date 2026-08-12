import pandas as pd
import geopandas as gpd
from shapely import Point, buffer, from_wkt
import numpy as np

def compute_archetypal_score(location, isovist, monuments, trees, water_bodies, near_threshold=100):
    visible_monuments = monuments.clip(isovist)
    visible_old_trees = trees[trees["Oud"] == "ja"].clip(isovist)
    visible_water = water_bodies.clip(isovist)

    visible_landmarks = pd.concat([
        visible_monuments,
        visible_old_trees,
        visible_water,
    ])

    n_visible_landmarks = len(visible_landmarks)

    near_buffer = buffer(Point(location), near_threshold)
    near_landmarks = visible_landmarks.clip(near_buffer)

    n_near_landmarks = len(near_landmarks)

    # Present, more than one and near = 6
    # Present, near = 5
    # Present, more than one and not near = 4
    # Present, not near = 3
    # None = 1

    if n_near_landmarks >= 2:
        archetypal_score = 6
    elif n_near_landmarks == 1:
        archetypal_score = 5
    elif n_visible_landmarks >= 2:
        archetypal_score = 4
    elif n_visible_landmarks == 1:
        archetypal_score = 3
    else:
        archetypal_score = 1
    
    return archetypal_score


if __name__ == "__main__":
    isovists = gpd.read_file("data/overvecht_isovists.gpkg", layer="isovists").geometry
    monuments = gpd.read_file("data/source/overvecht_monuments.gpkg")
    trees = gpd.read_file("data/source/overvecht_trees.gpkg")
    water = gpd.read_file("data/source/overvecht_water.gpkg")
    nodes = gpd.read_file("data/overvecht_isovists.gpkg", layer="nodes").geometry

    scores = [compute_archetypal_score((nodes[i].x, nodes[i].y), isovists[i], monuments, trees, water) for i in range(len(isovists))]
    print("Mean: ", sum(scores) / len(scores))
    
    import matplotlib.pyplot as plt

    plt.bar(x=[1, 2, 3, 4, 5, 6], height=np.histogram(scores, bins=6, range=(1, 6))[0])
    plt.show()