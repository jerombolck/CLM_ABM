import geopandas as gpd
from rasterstats import zonal_stats

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

def compute_biodiversity_score(isovist, trees, raster_file_paths):
    visible_trees = trees.clip(isovist)
    
    n_visible_trees = len(visible_trees)
    n_visible_old_trees = len(visible_trees[visible_trees["Oud"] == "ja"])
    n_visible_rare_trees = len(visible_trees[visible_trees["Zeldzaam"] == "ja"])
    n_visible_bospltsn_trees = len(visible_trees[visible_trees["Bospltsn"] == 1])
    
    visible_tree_species_count = visible_trees["Wetenschappelijke_naam"].nunique()
    mean_bee_species_count = zonal_stats(isovist, raster_file_paths["bee_richness"], stats="mean")

    mean_grass_perc = zonal_stats(isovist, raster_file_paths["grass_vegetation"], stats="mean")
    mean_shrub_perc = zonal_stats(isovist, raster_file_paths["shrub_vegetation"], stats="mean")
    mean_tree_perc = zonal_stats(isovist, raster_file_paths["tree_vegetation"], stats="mean")
    
    biodiversity_score = 1

    ## 'High diversity of plant and animal species'
    # High bee diversity increases score by 2
    # Medium bee diversity increases score by 1
    # High tree diversity increases score by 2
    # Medium tree diversity increases score by 1
    # Presence of any rare tree species increase by 1
    if mean_bee_species_count > 90:
        biodiversity_score + 2
    elif mean_bee_species_count > 60:
        biodiversity_score + 1

    if visible_tree_species_count > 12:
        biodiversity_score + 2
    elif visible_tree_species_count > 6:
        biodiversity_score + 1

    if n_visible_rare_trees > 0:
        biodiversity_score + 1

    ## 'Vegetation seems native and spontaneous'
    # Biodivirsity score has to be at least a four so far
    # - Is at least 30% of the visible trees in a 'bosplantsoen'?
    # - Are any old trees visible?
    # - Are all three vegetation layers (grass, shrubs, trees) are present?
    # Increase score by 1 if at least two are true
    # Increase score by 2 if all three are true
    # Score cannot exceed 4 if none are true
    if biodiversity_score >= 4:
        high_bospltsn_factor = n_visible_bospltsn_trees / n_visible_trees > 0.3
        any_old_trees = n_visible_old_trees > 0
        layered_vegetation = mean_grass_perc > 0.1 and mean_shrub_perc > 0.1 and mean_tree_perc > 0.1

        if not high_bospltsn_factor and not any_old_trees and not layered_vegetation:
            biodiversity_score = 4
        else:
            biodiversity_score += (high_bospltsn_factor + any_old_trees + layered_vegetation) - 1

    # Score cannot exceed 6
    if biodiversity_score > 6:
        biodiversity_score = 6

    return biodiversity_score