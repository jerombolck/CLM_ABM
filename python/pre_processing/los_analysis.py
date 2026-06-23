import rasterio
import geopandas as gpd
from shapely import Polygon, box
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import numpy as np
from rasterio.transform import rowcol
from scipy.ndimage import distance_transform_edt
from joblib import Parallel, delayed
from tqdm import tqdm


def fill_nodata(array):
    mask = array.mask
    indices = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return array.data[tuple(indices)]


def cast_ray(observer, target, buildings_union, dem_array, dem_transform, z_offset = 1):
    """Cast a ray from an observer location to a target location. Returns the end point of the ray
    Adapted from: https://spatial-dev.guru/2023/12/10/line-of-sight-analysis-in-digital-elevation-models-using-python/
    
    Assumes buildings will always block the direct line of sight.
    """
    building_endpoint = None
    dem_endpoint = None

    # Create ray and crop it to extent
    ray = LineString([observer, target])
    ray_diff_buildings = ray.difference(buildings_union)
    
    # Check if ray passes through buildings
    if not ray_diff_buildings.is_empty:
        if ray_diff_buildings.geom_type == "MultiLineString":
            building_endpoint = Point(list(ray_diff_buildings.geoms)[0].coords[-1])
        else:
            building_endpoint = Point(ray_diff_buildings.coords[-1])

    x1, y1 = observer.x, observer.y
    x2, y2 = target.x, target.y

    row1, col1 = rowcol(dem_transform, x1, y1)
    row2, col2 = rowcol(dem_transform, x2, y2)

    # clamp indices to valid raster bounds
    nrows, ncols = dem_array.shape
    row1 = int(np.clip(row1, 0, nrows - 1))
    row2 = int(np.clip(row2, 0, nrows - 1))
    col1 = int(np.clip(col1, 0, ncols - 1))
    col2 = int(np.clip(col2, 0, ncols - 1))

    z1 = dem_array[row1, col1] + z_offset
    z2 = dem_array[row2, col2] + z_offset

    # Calculate the number of steps for iteration
    steps = max(abs(row2 - row1), abs(col2 - col1))
 
    # Calculate the increments for x and y
    x_inc = (x2 - x1) / steps
    y_inc = (y2 - y1) / steps

    # Start from the observer point
    x, y = x1, y1

    # Iterate over the dem between observer and target
    for i in range(1, int(steps)):
        x += x_inc
        y += y_inc
        row, col = rowcol(dem_transform, x, y)

        # clamp indices each step to be safe
        row = int(np.clip(row, 0, nrows - 1))
        col = int(np.clip(col, 0, ncols - 1))

        # Get the elevation of the direct line and the dem at this point
        line_elevation = z1 + (z2 - z1) * (i / steps)
        dem_elevation = dem_array[row, col]
    
        # If the DEM elevation at this point is higher than the direct line, target point is not visible
        if not np.isnan(dem_elevation):
            if dem_elevation > line_elevation:
                dem_endpoint = Point(x, y)
                break
   
    if building_endpoint is None and dem_endpoint is None:
        return target
    
    elif dem_endpoint is None:
        return building_endpoint
    elif building_endpoint is None:
        return dem_endpoint
    
    observer_point = Point(x1, y1)
    if observer_point.distance(building_endpoint) <= observer_point.distance(dem_endpoint):
        return building_endpoint
    else:
        return dem_endpoint


def compute_isovist(observer, buildings_union, dem_array, dem_transform, max_distance=500, angle_step=1):
    endpoints = []

    for angle in np.arange(0, 360, angle_step):
        rad = np.radians(angle)
        target = Point(
            observer.x + max_distance * np.cos(rad),
            observer.y + max_distance * np.sin(rad),
        )

        endpoints.append(cast_ray(observer, target, buildings_union, dem_array, dem_transform))
    
    return Polygon(endpoints)


def create_isovist_gdf(points, buildings, dem_array, dem_transform):
    buildings_union = unary_union(buildings.geometry)

    isovist_results = Parallel(n_jobs=-1)(delayed(compute_isovist)(point, buildings_union, dem_array, dem_transform)
                                          for point in tqdm(points,"Computing isovists"))
    
    isovist_gdf = gpd.GeoDataFrame({"observer": [Point(p) for p in points]}, geometry=isovist_results, crs = buildings.crs)
    return isovist_gdf


if __name__ == "__main__":
    from create_street_network import download_network, split_network
    import matplotlib.pyplot as plt
    import time

    sample_size = 50
    plot_observer_id = 10

    buildings = gpd.read_file("data/source/overvecht_homes.gpkg")
    nodes, edges = download_network()
    nodes = split_network(nodes, edges)

    points = list(nodes.sample(sample_size).geometry)
    print(points)

    with rasterio.open("data/source/overvecht_dtm.tif") as dem_src:
        dem_data = dem_src.read(1, masked=True)
        dem_filled = fill_nodata(dem_data)
        dem_extent = [dem_src.bounds.left, dem_src.bounds.right, dem_src.bounds.bottom, dem_src.bounds.top]
        dem_transform = dem_src.transform

    start = time.time()
    isovists = create_isovist_gdf(points, buildings, dem_filled, dem_transform)
    elapsed = time.time() - start

    total_size = len(nodes.geometry)
    time_per_node = elapsed / sample_size
    total_estimated = time_per_node * total_size

    print(f"Estimated time for all nodes: {total_estimated / 60:.1f} minutes")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(dem_filled, cmap='terrain', vmin=0, vmax=10, alpha=0.6, extent=dem_extent)
    plt.colorbar(ax.images[-1], ax=ax, fraction=0.046, pad=0.04).set_label('Elevation (m)')

    buildings.plot(ax=ax, color="gray")
    gpd.GeoSeries(isovists.iloc[plot_observer_id]).plot(ax=ax, color="yellow", alpha=0.5)
    gpd.GeoSeries(isovists.loc[plot_observer_id, "observer"]).plot(ax=ax, color="red", markersize=10)

    plt.show()