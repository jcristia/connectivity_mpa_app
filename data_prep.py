
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

# If I want to try again in the future, maybe I could do gridlayer


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

plds = ['1', '3', '7', '10', '21', '30', '40', '60']
dates = ['avg', '1101', '1105', '1108', '1401', '1405', '1408', '1701', '1705', '1708']
gdb = os.path.join(root, 'spatial_original/lines/COMBINED.gdb')

df_all = pd.DataFrame(columns=['from_id'])

for pld in plds:
    for date in dates:
        lines = gpd.read_file(gdb, layer=f'connectivity_{date}_pld{pld}')
        lines = lines.drop(['Shape_Length'], axis=1)
        lines = lines[lines.from_id != lines.to_id]  # remove self connections. See notes below.
        lines = lines.explode(index_parts=False)  # now that we removed the arcs, we can change from multilinestring to linestring. It should not create any new features
        lines = lines.to_crs(4326) # project

        # get xy of start and end points
        lines['start'] = lines.geometry.apply(lambda g: list(g.coords[0]))
        lines['end'] = lines.geometry.apply(lambda g: list(g.coords[-1]))

        lines = pd.DataFrame(lines.drop(columns='geometry'))

        # simplify date
        lines['date'] = lines.date_start.str[:10]

        # for average ones, date should be "average"
        if date=='avg':
            lines['date'] = 'average'

        # drop a bunch of fields for now
        if date=='avg':
            lines['prob'] = lines.prob_avg
            lines = lines.drop(['date_start', 'totalori', 'totquant', 'prob_avg'], axis=1)
        else:
            lines['freq'] = 1
            lines = lines.drop(['quantity', 'totalori', 'time_int', 'date_start'], axis=1)

        df_all = pd.concat([df_all, lines], sort=True, ignore_index=True)


# remove ones that are less than 0.00001
# My lowest values are 0.000001. These only occur in the averaged dataset and it is a small part of
# the dataset.
df_all = df_all[df_all.prob >= 0.00001]

# color scheme
# It's a bit annoying, but the easiest way to symbolize the lines in the map is to have the color
# as a field in the dataframe.
color_scheme = [
    [13,8,135],
    [126,3,168],
    [204,71,121],
    [249,149,65],
    [241,250,34]
]

def get_color(row):
    prob = row['prob']
    if prob >= 0.1:
        color = color_scheme[0]
    elif prob >= 0.01:
        color = color_scheme[1]
    elif prob >= 0.001:
        color = color_scheme[2]
    elif prob >= 0.0001:
        color = color_scheme[3]
    elif prob >= 0.00001:
        color = color_scheme[4]
    return color

df_all['color'] = df_all.apply(get_color, axis=1)

df_all.to_json('lines.json.gz')

######################################
# TO do in the future:


# 1
# Persistence points and lines

# 2
# How will I do the settlement rasters? Bitmap looked like shit.
# Maybe I'll need to do a whole different kind of map. See GridLayer and H3HexagonLayer

