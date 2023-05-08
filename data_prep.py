
import pandas as pd
import geopandas as gpd
import os
import json

root = r'C:\Users\cristianij\Documents\Projects\mpa_connectivity_app'

######################################
# Coastline


# self intersections in the coastline (and this is probably why I got errors in my original analysis in those inlets)
# repair geometry does not fix it adequately, but I found that moving the bounding points out fixes
# the issue.
# Copy and manually edit the vertices there.

# shp_land = os.path.join(root, 'spatial_original/coastline/landmask_REPAIRGEOMETRY.shp')
# # convert coastline to geojson
# land = gpd.read_file(shp_land)
# land['land'] = 'land'
# land = land[['land', 'geometry']]
# land.to_file('land.geojson', driver='GeoJSON')

# It ends up loading way too slowly on the map.
# Try to convert coastline to image
# I did it out to bmp, png, tif, and it always looked like shit loading into pydeck. Just abandon this.


######################################
# MPAs

# To get the coordinates in the format that pydeck needs I ended going from shp to gpd to json to
# pd. I tried pickle and parquet and it works locally, but I get errors when loading from a url.
# I also tried with csv, but it stores the array or coordinates as a big string and it takes a while
# to convert back.
mpas = os.path.join(root, 'spatial_original/mpas/mpa_.shp')
df = gpd.read_file(mpas)
df = df[['uID_202011', 'geometry']]
df = df.to_crs(4326) # project
df.to_file('mpas.geojson', driver='GeoJSON')

# with open('mpas.geojson') as data_file:
#     d = json.load(data_file)
# dfjson = pd.DataFrame.from_dict(d['features'])
# df = pd.DataFrame()
# df["coordinates"] = dfjson.apply(lambda row: row['geometry']["coordinates"][0], axis=1) # This was hard to figure out because the coordinates get double wrapped in list brackets, so you need to go in 1 level.
# df["MPA ID"] = dfjson.apply(lambda row: row['properties']['uID_202011'], axis=1)


######################################
# Connectivity lines

# TODO
# eventually wrap this in a for loop to do for all lines
# Put everything in one large df and then that just gets loaded once
# See if that runs quick enough, or if I will have to do individual loads as a pld/date is called.

gdb = os.path.join(root, 'spatial_original/lines/COMBINED.gdb')
lines = gpd.read_file(gdb, layer='conn_avg_pld60')
lines = lines.drop(['date_start', 'Shape_Length'], axis=1)
lines = lines[lines.from_id != lines.to_id]  # remove self connections. See notes below.
lines = lines.explode(index_parts=False)  # now that we removed the arcs, we can change from multilinestring to linestring. It should not create any new features
lines = lines.to_crs(4326) # project

# get xy of start and end points
lines['start'] = lines.geometry.apply(lambda g: list(g.coords[0]))
lines['end'] = lines.geometry.apply(lambda g: list(g.coords[-1]))

lines = pd.DataFrame(lines.drop(columns='geometry'))
lines.to_json('lines.json.gz')

######################################
# TO do in the future:

# 0
# Simplify MPA polygon geometry to see if I can get them load faster

# 1
# I'm filtering out self connection loops because (1) It complicates the plotting of the other lines
# that have just 2 points and (2) they aren't super visible with how big I made the arcs anyways.
# So one thing for the future:
# Put those values into the MPA polygons that can be viewed on hover.

# 2
# Persistence points and lines

# 3
# How will I do the settlement rasters? Bitmap looked like shit.
# Maybe I'll need to do a whole different kind of map.

