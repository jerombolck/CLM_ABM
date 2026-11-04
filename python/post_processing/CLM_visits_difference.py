import numpy as np
import rasterio
import os

with rasterio.open("data/results/visits_baseline_5kmh_rasterized.tif") as visits:
    visits_data = visits.read()

with rasterio.open("data/results/CLM_score_rasterized.tif") as clm:
    clm_data = clm.read()

# 0: low CLM score and not visited often
result = np.multiply(visits_data, 0)

# 1: low CLM score and visisted often
result = np.where((visits_data >= 1000) & (clm_data <= 3), 1, result)

# 2: high CLM score but not visited often
result = np.where((visits_data < 1000) & (clm_data > 3), 2, result)

# 3: high CLM score and visited often
result = np.where((visits_data >= 1000) & (clm_data > 3), 3, result)

result_kwargs = visits.meta

with rasterio.open("data/results/CLM_visits_difference_analysis.tif", 'w', **result_kwargs) as out:
    out.write(result.astype(rasterio.float32))