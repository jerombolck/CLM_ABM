import rasterio
import pandas as pd
import geopandas as gpd
from shapely import Polygon, box
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import numpy as np
from rasterio.transform import rowcol
from scipy.ndimage import distance_transform_edt
from joblib import Parallel, delayed
from tqdm import tqdm
from layers_of_landscape import compute_layers_score
from terrain import load_terrain


def cast_ray(observer, target, buildings_union, dem_array, dtm_transform, z_offset = 1):
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
    spatial_resolution = dtm_transform[0]

    # Calculate the steps for sampling DEM elevation
    steps = int(ray_length / spatial_resolution)

    if steps == 0:
        return endpoint, ray_length

    # Get the coordinates of all sample points along the ray
    x_coords = np.linspace(x1, x2, steps)
    y_coords = np.linspace(y1, y2, steps)
    rows, cols = rowcol(dtm_transform, x_coords, y_coords)
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
        ray_length = np.hypot(endpoint[0] - x1, endpoint[1] - y1)

    return endpoint, ray_length


def compute_isovist(observer, buildings_union, dem_array, dtm_transform, max_distance=500, angle_step=1):
    endpoints = []
    ray_lengths = []

    for angle in np.arange(0, 360, angle_step):
        rad = np.radians(angle)
        target = (
            observer[0] + max_distance * np.cos(rad),
            observer[1] + max_distance * np.sin(rad),
        )

        endpoint, ray_length = cast_ray(observer, target, buildings_union, dem_array, dtm_transform)
        endpoints.append(endpoint)
        ray_lengths.append(ray_length)
    
    isovist = Polygon(endpoints)
    layers_score = compute_layers_score(ray_lengths)

    return gpd.GeoDataFrame({"isovist": [isovist], "layers_score": [layers_score]}, geometry=[Point(observer)])


def create_isovist_gdf(points, buildings, dem_array, dtm_transform):
    buildings_union = unary_union(buildings.geometry)

    isovist_results = Parallel(n_jobs=-1)(delayed(compute_isovist)(point, buildings_union, dem_array, dtm_transform)
                                          for point in tqdm(points,"Computing isovists"))

    gdf = pd.concat(isovist_results)
    gdf = gdf.reset_index()

    return gdf


if __name__ == "__main__":
    from street_network import download_network, split_network
    import matplotlib.pyplot as plt

    sample_size = 50
    plot_observer_id = 10

    buildings = gpd.read_file("data/source/overvecht_homes.gpkg")
    study_area = gpd.read_file("data/source/study_area.gpkg")

    nodes, edges = download_network()
    nodes = split_network(nodes, edges)

    points = [(geom.x, geom.y) for geom in nodes.sample(sample_size).geometry]

    dtm, dtm_extent, dtm_transform = load_terrain("data/source/overvecht_dtm.tif")

    iso_node_gdf = create_isovist_gdf(points, buildings, dtm, dtm_transform)

    iso_gdf = gpd.GeoSeries(iso_node_gdf["isovist"], crs=study_area.crs)
    iso_gdf = iso_gdf.clip(study_area, sort=True)

    node_gdf = gpd.GeoDataFrame(iso_node_gdf["layers_score"], geometry=iso_node_gdf.geometry)

    iso_gdf.to_file("data/overvecht_isovists.gpkg", layer="isovists")
    node_gdf.to_file("data/overvecht_isovists.gpkg", layer="nodes")

    layers_scores = list(iso_node_gdf.layers_score)
    print("Mean layers of the landscape score: ", sum(layers_scores) / len(layers_scores))

    # Plot
    plt.bar(x=[1, 2, 3, 4, 5, 6], height=np.histogram(layers_scores, bins=6, range=(1, 6))[0])
    plt.show()
    
    fig, ax = plt.subplots(figsize=(10, 10))

    ax.imshow(dtm, cmap='terrain', vmin=0, vmax=10, alpha=0.6, extent=dtm_extent)
    plt.colorbar(ax.images[-1], ax=ax, fraction=0.046, pad=0.04).set_label('Elevation (m)')

    buildings.plot(ax=ax, color="gray")
    gpd.GeoSeries(iso_gdf.iloc[plot_observer_id]).plot(ax=ax, color="yellow", alpha=0.5)
    gpd.GeoSeries(node_gdf.iloc[plot_observer_id].geometry).plot(ax=ax, color="red", markersize=10)

    plt.show()