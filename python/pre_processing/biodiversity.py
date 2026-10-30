import geopandas as gpd
from rasterstats import zonal_stats
import numpy as np

""""
fid: 14783
OBJECTID: 97392
Nederlandse_naam: Zomereik
Wetenschappelijke_naam: Quercus robur
Plantjaar: 1975
Eigenaar: Gemeentelijk
Buurt: Amazonedreef-zuid
Wijk: Overvecht
Zeldzaam: nee
Oud: nee
Bospltsn: 0
Legenda: Quercus
Exportdat: 20250404
layer: park_street_trees — park_en_straatbomen_20250404
path: /home/jerom/Thesis/CLM_ABM/data/qgis/park_street_trees.gpkg|layername=park_en_straatbomen_20250404
"""

def compute_biodiversity_score(isovist, trees, raster_file_paths, less_strict=False):
    visible_trees = trees.clip(isovist)
    
    n_visible_trees = len(visible_trees)
    n_visible_old_trees = len(visible_trees[visible_trees["Oud"] == "ja"])
    n_visible_rare_trees = len(visible_trees[visible_trees["Zeldzaam"] == "ja"])
    n_visible_bospltsn_trees = len(visible_trees[visible_trees["Bospltsn"] == 1])
    n_visible_tree_species = visible_trees["Wetenschappelijke_naam"].nunique()
    

    mean_bee_richness = zonal_stats(isovist, raster_file_paths["bee_richness"])[0]["mean"]
    mean_grass_perc = zonal_stats(isovist, raster_file_paths["grass_vegetation"])[0]["mean"]
    mean_shrub_perc = zonal_stats(isovist, raster_file_paths["shrub_vegetation"])[0]["mean"]
    mean_tree_perc = zonal_stats(isovist, raster_file_paths["tree_vegetation"])[0]["mean"]

    biodiversity_score = 1

    if less_strict:
        high_bee_richness_threshold = 70
        medium_bee_richness_threshold = 50
        high_tree_diversity_threshold = 30
        medium_tree_diversity_threshold = 15
        bosplantsoen_percentage_threshold = 0.2
    else:
        high_bee_richness_threshold = 90
        medium_bee_richness_threshold = 70
        high_tree_diversity_threshold = 40
        medium_tree_diversity_threshold = 20
        bosplantsoen_percentage_threshold = 0.3

    ## 'High diversity of plant and animal species'
    # High bee diversity increases score by 2
    # Medium bee diversity increases score by 1
    # High tree diversity increases score by 2
    # Medium tree diversity increases score by 1
    # Presence of any rare tree species increases score by 1
    if mean_bee_richness != None:
        if mean_bee_richness > high_bee_richness_threshold:
            biodiversity_score += 2
        elif mean_bee_richness > medium_bee_richness_threshold:
            biodiversity_score += 1

    if n_visible_tree_species > high_tree_diversity_threshold:
        biodiversity_score += 2
    elif n_visible_tree_species > medium_tree_diversity_threshold:
        biodiversity_score += 1

    if n_visible_rare_trees > 0:
        biodiversity_score += 1

    ## 'Vegetation seems native and spontaneous'
    # Score has to be at least 4 so far
    # Considers the following:
    # - Is at least 30% of the visible trees in a 'bosplantsoen'?
    # - Are any old trees visible?
    # - Are all three vegetation layers (grass, shrubs, trees) are present?
    # Increase score by 2 if all three statements are true
    # Increase score by 1 if any two statemets are true
    # Do not increase score if only one statement is true
    # Score cannot exceed 4 if none of the statements are true
    if biodiversity_score >= 4:
        high_bospltsn_factor = n_visible_bospltsn_trees / n_visible_trees > bosplantsoen_percentage_threshold
        any_old_trees = n_visible_old_trees > 0
        layered_vegetation = mean_grass_perc > 10 and mean_shrub_perc > 10 and mean_tree_perc > 10

        if not high_bospltsn_factor and not any_old_trees and not layered_vegetation:
            biodiversity_score = 4
        else:
            biodiversity_score += high_bospltsn_factor + any_old_trees + layered_vegetation - 1

    # Score cannot exceed 6
    if biodiversity_score > 6:
        biodiversity_score = 6

    return biodiversity_score


if __name__ == "__main__":
    isovists = gpd.read_file("data/pre_processing/overvecht_score_nodes.gpkg", layer="isovists").sample(100)
    trees = gpd.read_file("data/source/overvecht_trees.gpkg")
    file_paths = {
        "bee_richness": "data/source/overvecht_bee_richness.tif",
        "grass_vegetation": "data/source/overvecht_grass_raster.tif",
        "shrub_vegetation": "data/source/overvecht_shrubs_raster.tif",
        "tree_vegetation": "data/source/overvecht_trees_raster.tif",
    }

    scores = [compute_biodiversity_score(iso, trees, file_paths) for iso in isovists.geometry]
    print("Mean: ", sum(scores) / len(scores))
    
    n_bospltsn_trees = len(trees[trees["Bospltsn"] == 1])

    print(f"Percentage of trees that is in a bosplantsoen: {n_bospltsn_trees / len(trees)%2}")

    import matplotlib.pyplot as plt

    plt.bar(x=[1, 2, 3, 4, 5, 6], height=np.histogram(scores, bins=6, range=(1, 6))[0])
    plt.show()