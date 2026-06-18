from pygbif import species
import pandas as pd

print(species.name_lookup("salix alba")["results"][1].keys())
