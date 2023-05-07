
import pandas as pd
import geopandas as gpd
import os

# convert coastline to geojson

root = r'C:\Users\cristianij\Documents\Projects\mpa_connectivity_app'
shp = os.path.join(root, 'coastline/landmask_FINAL_wgs84.shp')

land = gpd.read_file(shp)
land['land'] = 'land'
land = land[['land', 'geometry']]
land.to_file('land.geojson', driver='GeoJSON')


# convert coastline to image
# it is too slow to load on a map. I don't need any interaction with it, so just do it as a raster.
# However, I want to get the symbology right, so do it in Desktop.




# remove geojson file from github