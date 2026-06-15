import osgeo
import rasterio
import geopandas as gpd
from shapely.geometry import point
import numpy as np


def has_line_of_sight(dem, buildings, observer_loc, target_loc, observer_offset = 1):
    """Checks if an observer at observer_loc has a direct line of sight with target_loc. 
    Adapted from: https://spatial-dev.guru/2023/12/10/line-of-sight-analysis-in-digital-elevation-models-using-python/
    
    Assumes buildings will always block the direct line of sight.
    """
    x1, y1 = observer_loc
    x2, y2 = target_loc
    
    dx = x2 - x1
    dy = y2 - y1

    # Calculate the number of steps for iteration based on the greater of dx or dy
    steps = max(abs(dx), abs(dy))
 
    if steps == 0:
        return True
 
    # Calculate the increments for x and y
    x_inc = dx / steps
    y_inc = dy / steps
 
    # Start from the observer point
    x = x1
    y = y1
    z = dem.sample(observer_loc) + observer_offset

    # Get target elevation
    z2 = dem.sample(target_loc)
 
    # Iterate over the cells between observer and target
    for i in range(1, int(steps)):
        x += x_inc
        y += y_inc

        # Get the elevation of the direct line and the dem at this point
        line_elevation = z + (z2 - z) * (i / steps)
        dem_elevation = dem.sample((x, y))
        
        # If the direct line encounters a building, target point is not visible
        if buildings.overlaps(point(x, y)):
            return False
    
        # If the DEM elevation at this point is higher than the direct line, target point is not visible
        if dem_elevation != np.nan:
            if dem_elevation > line_elevation:
                return False
        
    # If the line iteration was succesful, the target point is visible
    return True


def create_los_matrix(dem, buildings, points):
    point_count = len(points)
    los_matrix = np.empty((point_count, point_count))

    # Iterate through all points
    for i in range(point_count):
        los_matrix[i, i] = True

        # If this is is last point, return the matrix
        if i == point_count - 1:
            return los_matrix

        # Determine line of sight for all remaining pairs with this point
        for j in range(i+1, point_count):
            los_matrix[i, j] = has_line_of_sight(dem, buildings, points[i], points[j])


if __name__ == "__main__":
    #buildings = gpd.read_file("data/source/overvecht_homes.tif")
    with rasterio.open("data/source/overvecht_dtm.tif") as dem:
        print(dem)

    


