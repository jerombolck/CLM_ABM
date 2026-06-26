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
    """Cast a ray from an observer location towards a target location. Returns the end point of the ray.
    
    Assumes buildings will always block the direct line of sight.
    """
    endpoint = target

    x1, y1 = observer
    x2, y2 = target

    # Create ray 
    ray = LineString([observer, target])
    ray_length = ray.length
    
    # Check if ray passes through buildings
    ray_diff_buildings = ray.difference(buildings_union)
    if not ray_diff_buildings.is_empty:

        # Set endpoint to the first intersection with buildings
        if ray_diff_buildings.geom_type == "MultiLineString":
            endpoint = list(ray_diff_buildings.geoms)[0].coords[-1]
        else:
            endpoint = ray_diff_buildings.coords[-1]

        # Update the ray length and target coordinates to the found endpoint
        ray_length = np.hypot(endpoint[0] - x1, endpoint[1] - y1)
        x2, y2 = endpoint

    # Get the size and spatial resolution of the DEM
    dem_rows, dem_cols = dem_array.shape
    spatial_resolution = dem_transform[0]

    # Calculate the steps for sampling DEM elevation
    steps = int(ray_length / spatial_resolution)

    if steps == 0:
        return endpoint

    # Get the coordinates of all sample points along the ray
    x_coords = np.linspace(x1, x2, steps)
    y_coords = np.linspace(y1, y2, steps)
    rows, cols = rowcol(dem_transform, x_coords, y_coords)
    rows = np.clip(rows, 0, dem_rows - 1)
    cols = np.clip(cols, 0, dem_cols - 1)

    # Get start and end elevation
    z1 = dem_array[rows[0], cols[0]] + z_offset
    z2 = dem_array[rows[-1], cols[-1]] + z_offset

    # Get elevations of DEM along the ray and interpolate between start and end elevation
    dem_elevations = dem_array[rows, cols]
    ray_elevations = np.linspace(z1, z2, steps)
 
    # Find the indices where the DEM elevation exceeds the ray elevation
    terrain_intersects = np.where(~np.isnan(dem_elevations) & (dem_elevations > ray_elevations))[0]
    if terrain_intersects.size > 0:
        endpoint = (x_coords[terrain_intersects[0]], y_coords[terrain_intersects[0]])
   
    return endpoint


def compute_isovist(observer, buildings_union, dem_array, dem_transform, max_distance=500, angle_step=1):
    endpoints = []

    for angle in np.arange(0, 360, angle_step):
        rad = np.radians(angle)
        target = (
            observer[0] + max_distance * np.cos(rad),
            observer[1] + max_distance * np.sin(rad),
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
    from street_network import download_network, split_network
    import matplotlib.pyplot as plt
    import time

    sample_size = 50
    plot_observer_id = 10

    buildings = gpd.read_file("data/source/overvecht_homes.gpkg")
    study_area = gpd.read_file("data/source/study_area.gpkg")

    nodes, edges = download_network()
    nodes = split_network(nodes, edges)

    points = [(geom.x, geom.y) for geom in nodes.geometry]

    with rasterio.open("data/source/overvecht_dtm.tif") as dem_src:
        dem_data = dem_src.read(1, masked=True)
        dem_filled = fill_nodata(dem_data)
        dem_extent = [dem_src.bounds.left, dem_src.bounds.right, dem_src.bounds.bottom, dem_src.bounds.top]
        dem_transform = dem_src.transform

    isovists = create_isovist_gdf(points, buildings, dem_filled, dem_transform)
    isovists_clipped = isovists.clip(study_area)

    isovists_clipped.to_file("data/overvecht_network_isovists.gpkg")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(dem_filled, cmap='terrain', vmin=0, vmax=10, alpha=0.6, extent=dem_extent)
    plt.colorbar(ax.images[-1], ax=ax, fraction=0.046, pad=0.04).set_label('Elevation (m)')

    buildings.plot(ax=ax, color="gray")
    gpd.GeoSeries(isovists_clipped.iloc[plot_observer_id]).plot(ax=ax, color="yellow", alpha=0.5)
    gpd.GeoSeries(isovists_clipped.loc[plot_observer_id, "observer"]).plot(ax=ax, color="red", markersize=10)

    plt.show()