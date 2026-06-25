import geopandas as gpd

def create_home_centroids(home_buildings):
    points = []
    for _, row in home_buildings.iterrows():
        # Try to get the aantal value or fall back to 1
        count = row.get('aantal', 1)
        count = int(count)

        # Calculate centroid geometry and copy other building data
        centroid = row.geometry.centroid
        centroid_data = row.drop(labels='geometry').to_dict()

        # Create as many points with the centroid geometry and building data as 'aantal'
        for _ in range(count):
            point = centroid_data.copy()
            point['geometry'] = centroid
            points.append(point)

    return gpd.GeoDataFrame(points, crs='EPSG:28992', geometry='geometry')
