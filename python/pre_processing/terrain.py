from scipy.ndimage import distance_transform_edt
import rasterio


def fill_nodata(array):
    mask = array.mask
    indices = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return array.data[tuple(indices)]


def load_terrain(path):
    with rasterio.open("data/source/overvecht_dtm.tif") as src:
        data = src.read(1, masked=True)
        data_filled = fill_nodata(data)
        extent = [src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top]
        transform = src.transform

    return data_filled, extent, transform