import rasterio
import geopandas as gpd
from shapely.geometry import Point, LineString
import numpy as np
from rasterio.transform import rowcol
from scipy.ndimage import distance_transform_edt
from joblib import Parallel, delayed
from tqdm import tqdm

import time


def fill_nodata(array):
    mask = array.mask
    indices = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return array.data[tuple(indices)]


def has_line_of_sight(dem_array, dem_transform, buildings, observer_loc, target_loc, z_offset = 1):
    """Checks if an observer at observer_loc has a direct line of sight with target_loc. 
    Adapted from: https://spatial-dev.guru/2023/12/10/line-of-sight-analysis-in-digital-elevation-models-using-python/
    
    Assumes buildings will always block the direct line of sight.
    """

    # If the direct line intersects with a building, target point is not visible
    line = LineString([observer_loc, target_loc])
    if any(buildings.intersects(line)):
        return False
    
    # If the line does not intersect any buildings: prepare to iterate over the dem

    x1, y1 = observer_loc
    x2, y2 = target_loc

    row1, col1 = rowcol(dem_transform, x1, y1)
    row2, col2 = rowcol(dem_transform, x2, y2)

    z1 = dem_array[row1, col1] + z_offset
    z2 = dem_array[row2, col2] + z_offset

    # Calculate the number of steps for iteration based on the greater of dx or dy
    steps = max(abs(row2 - row1), abs(col2 - col1))
 
    if steps == 0:
        return True
 
    # Calculate the increments for x and y
    x_inc = (x2 - x1) / steps
    y_inc = (y2 - y1) / steps

    # Start from the observer point
    x = x1
    y = y1

    # Iterate over the dem between observer and target
    for i in range(1, int(steps)):
        x += x_inc
        y += y_inc

        # Get the elevation of the direct line and the dem at this point
        line_elevation = z1 + (z2 - z1) * (i / steps)
        dem_elevation = dem_array[rowcol(dem_transform, x, y)]
    
        # If the DEM elevation at this point is higher than the direct line, target point is not visible
        if not np.isnan(dem_elevation):
            if dem_elevation > line_elevation:
                return False
        
    # If the line iteration was succesful, the target point is visible
    return True


def create_los_matrix(dem_array, dem_transform, buildings, points, max_dist = 500):
    point_count = len(points)
    los_matrix = np.identity(point_count, dtype=np.bool_)

    print(f"Creating line of sight matrix for {point_count} points.")

    pairs = [
        (i, j)
        for i in range(point_count)
        for j in range(i+1, point_count)
        if np.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1]) < max_dist
    ]

    los_results = Parallel(n_jobs=-1)(delayed(has_line_of_sight)(dem_array, dem_transform, buildings, points[i], points[j]) 
                                      for i, j in tqdm(pairs, f"Computing line of sight for {len(pairs)} pairs"))

    for pair_i in range(len(pairs)):
        i, j = pairs[pair_i]
        los_matrix[i, j] = los_matrix[j, i] = los_results[pair_i]

    return los_matrix


if __name__ == "__main__":
    sample_size = 1000
    plot_observer_id = 650

    buildings = gpd.read_file("data/source/overvecht_homes.gpkg")
    network = gpd.read_file("data/source/overvecht_network.gpkg")

    points = [(geom.centroid.x, geom.centroid.y) for geom in network.head(sample_size).geometry]
        
    with rasterio.open("data/source/overvecht_dtm.tif") as dem_src:
        dem_data = dem_src.read(1, masked=True)
        dem_filled = fill_nodata(dem_data)
        dem_extent = [dem_src.bounds.left, dem_src.bounds.right, dem_src.bounds.bottom, dem_src.bounds.top]
        dem_transform = dem_src.transform

    start = time.time()
    los_matrix = create_los_matrix(dem_filled, dem_transform, buildings, points)
    elapsed = time.time() - start

    sample_pair_count = ((sample_size*sample_size)-sample_size)/2
    total_size = len(network.geometry)
    total_pair_count = ((total_size*total_size)-total_size)/2

    time_per_pair = elapsed / sample_pair_count
    total_estimated = time_per_pair * total_pair_count
    print(f"Estimated time: {total_estimated / 60:.1f} minutes")


    # Plot Results
    import matplotlib.pyplot as plt

    # Create a GeoDataFrame for the points using the buildings CRS
    point_geoms = [Point(x, y) for x, y in points]
    pts_gdf = gpd.GeoDataFrame({'visible': los_matrix[plot_observer_id]}, geometry=point_geoms, crs=buildings.crs)

    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot the DEM with a colour ramp from 0 to 10 m
    ax.imshow(dem_filled, cmap='terrain', vmin=0, vmax=10, alpha=0.6, extent=dem_extent)
    plt.colorbar(ax.images[-1], ax=ax, fraction=0.046, pad=0.04).set_label('Elevation (m)')

    # Plot buildings
    buildings.plot(ax=ax, color='lightgrey', edgecolor='black')

    # Plot visible and non-visible points
    pts_gdf[~pts_gdf['visible']].plot(ax=ax, color='red', marker='x', markersize=50, label='not visible')
    pts_gdf[pts_gdf['visible']].plot(ax=ax, color='green', marker='o', markersize=50, label='visible')

    # Highlight the observer (first point)
    pts_gdf.iloc[[plot_observer_id]].plot(ax=ax, color='blue', marker='*', markersize=200, label='observer')

    ax.set_title(f'Buildings and Line of Sight from point {plot_observer_id}')
    ax.set_aspect('equal')
    ax.legend()
    plt.show()