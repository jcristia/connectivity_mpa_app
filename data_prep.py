
import pandas as pd
import geopandas as gpd
import os
import json
import numpy as np

root = r'C:\Users\cristianij\Documents\Projects\mpa_connectivity_app'


# To get the coordinates in the format that pydeck needs I ended going from shp/gdb to gpd to json to
# pd. I tried pickle and parquet and it works locally, but I get errors when loading from a url.
# I also tried with csv, but it stores the array or coordinates as a big string and it takes a while
# to convert back in the app script.



######################################
# Connectivity lines

plds = ['1', '3', '7', '10', '21', '30', '40', '60']
dates = ['avg', '1101', '1105', '1108', '1401', '1405', '1408', '1701', '1705', '1708']
gdb = os.path.join(root, 'spatial_original/lines/COMBINED.gdb')

df_all = pd.DataFrame(columns=['pld'])

# MPAs to exclude
mpas_gdb = os.path.join(root, 'spatial_original/mpas/mpas.gdb')
df_ex = gpd.read_file(mpas_gdb, layer='M10_toexcludefromanalysis')
df_ex = df_ex[df_ex.exclude == 1.0]
ex_list = list(df_ex.uID_20201124)
# MPA names
mpa_names = gpd.read_file(mpas_gdb, layer='M09_mpa_joined')
mpa_names = pd.DataFrame(mpa_names[['uID_20201124', 'name']])

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
            lines = lines.drop(['date_start', 'totalori', 'totquant', 'prob_avg', 'freq'], axis=1)
        else:
            #lines['freq'] = 1
            lines = lines.drop(['quantity', 'totalori', 'time_int', 'date_start'], axis=1)

        # Exclude
        lines = lines[(~lines.to_id.isin(ex_list)) & (~lines.from_id.isin(ex_list))]

        # Get MPA names for to and from ids
        # If things are too slow to load then I could try loading the names separately and doing
        # the merge in app.py.
        lines = lines.merge(mpa_names, left_on='from_id', right_on='uID_20201124')
        lines = lines.rename(columns={'name':'From MPA'})
        lines = lines.drop(['uID_20201124'], axis=1)
        lines = lines.merge(mpa_names, left_on='to_id', right_on='uID_20201124')
        lines = lines.rename(columns={'name':'To MPA'})
        lines = lines.drop(['uID_20201124', 'from_id', 'to_id'], axis=1)

        # Round coordinate values
        # This is just to reduce the file size that needs to be uploaded by the app. Once in the app
        # it will read it into pandas as a float and will probably take the same disk space, but it
        # might help with the initial load.
        lines['start'] = lines['start'].apply(lambda x: np.round(np.array(x),5))
        lines['end'] = lines['end'].apply(lambda x: np.round(np.array(x),5))

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
# Get just the self connections as a separate table

plds = ['1', '3', '7', '10', '21', '30', '40', '60']
dates = ['avg', '1101', '1105', '1108', '1401', '1405', '1408', '1701', '1705', '1708']
gdb = os.path.join(root, 'spatial_original/lines/COMBINED.gdb')

df_all = pd.DataFrame(columns=['pld'])

# MPAs to exclude
mpas_gdb = os.path.join(root, 'spatial_original/mpas/mpas.gdb')
df_ex = gpd.read_file(mpas_gdb, layer='M10_toexcludefromanalysis')
df_ex = df_ex[df_ex.exclude == 1.0]
ex_list = list(df_ex.uID_20201124)
# MPA names
mpa_names = gpd.read_file(mpas_gdb, layer='M09_mpa_joined')
mpa_names = pd.DataFrame(mpa_names[['uID_20201124', 'name']])

for pld in plds:
    for date in dates:
        lines = gpd.read_file(gdb, layer=f'connectivity_{date}_pld{pld}')
        lines = lines.drop(['Shape_Length'], axis=1)
        lines = lines[lines.from_id == lines.to_id]  # get just the self connections

        lines = pd.DataFrame(lines.drop(columns='geometry'))

        # simplify date
        lines['date'] = lines.date_start.str[:10]

        # for average ones, date should be "average"
        if date=='avg':
            lines['date'] = 'average'

        # drop a bunch of fields for now
        if date=='avg':
            lines['prob'] = lines.prob_avg
            lines = lines.drop(['date_start', 'totalori', 'totquant', 'prob_avg', 'freq'], axis=1)
        else:
            #lines['freq'] = 1
            lines = lines.drop(['quantity', 'totalori', 'time_int', 'date_start'], axis=1)

        # Exclude
        lines = lines[(~lines.to_id.isin(ex_list)) & (~lines.from_id.isin(ex_list))]

        # Get MPA names for to and from ids
        lines = lines.merge(mpa_names, left_on='from_id', right_on='uID_20201124')
        lines = lines.rename(columns={'name':'From MPA'})
        lines = lines.drop(['uID_20201124'], axis=1)
        lines = lines.merge(mpa_names, left_on='to_id', right_on='uID_20201124')
        lines = lines.rename(columns={'name':'To MPA'})
        lines = lines.drop(['uID_20201124'], axis=1)

        df_all = pd.concat([df_all, lines], sort=True, ignore_index=True)


# remove ones that are less than 0.00001
df_all = df_all[df_all.prob >= 0.00001]

df_all.to_csv('selfconn.csv')


######################################
# MPAs

# To get the coordinates in the format that pydeck needs I ended going from shp to gpd to json to
# pd. I tried pickle and parquet and it works locally, but I get errors when loading from a url.
# I also tried with csv, but it stores the array or coordinates as a big string and it takes a while
# to convert back in the app.

#mpas = os.path.join(root, 'spatial_original/mpas/mpa_.shp')
mpas_gdb = os.path.join(root, 'spatial_original/mpas/mpas.gdb')
df = gpd.read_file(mpas_gdb, layer='M09_mpa_joined')
df = df.explode(index_parts=False, ignore_index=True) # Geopandas reads in as multipolygon (doesn't do this with the shapefile). Explode.
df['geometry'] = df.geometry.simplify(tolerance=50, preserve_topology=True) # remove some vertices to reduce file size
df = df.to_crs(4326) # project

# read in the table that lists which ones I ended up excluding from the analysis because of ocean model resolution issues
df_ex = gpd.read_file(mpas_gdb, layer='M10_toexcludefromanalysis')
df = df.merge(df_ex, on='uID_20201124')
df = df[df.exclude != 1.0]

# clean up fields
df = df[['uID_20201124', 'name', 'geometry_x']]
df = df.rename(columns={'uID_20201124':'uID', 'geometry_x':'geom'})

df = gpd.GeoDataFrame(df, geometry='geom')
df.to_file('mpas.geojson', driver='GeoJSON')

# OK, this ended up being a bit round about, but I decided to move some of the data munging that was
# happening in app.py to here.
with open('mpas.geojson') as data_file:
    d = json.load(data_file)
dfjson = pd.DataFrame.from_dict(d['features'])
df = pd.DataFrame()
df["coordinates"] = dfjson.apply(lambda row: row['geometry']["coordinates"][0], axis=1) # This was hard to figure out because the coordinates get double wrapped in list brackets, so you need to go in 1 level.
df["MPA ID"] = dfjson.apply(lambda row: row['properties']['uID'], axis=1)
df['MPA name'] = dfjson.apply(lambda row: row['properties']['name'], axis=1)

# Round coordinate values
# This is just to reduce the file size that needs to be uploaded by the app. Once in the app
# it will read it into pandas as a float and will probably take the same disk space, but it
# might help with the initial load.
df['coordinates'] = df['coordinates'].apply(lambda x: np.round(np.array(x),5))

# Join self connections csv
selfconns = pd.read_csv('selfconn.csv')
selfconns = selfconns.merge(df, left_on='from_id', right_on='MPA ID')
df = selfconns.drop(['Unnamed: 0', 'from_id', 'to_id', 'MPA ID', 'MPA name'], axis=1)

df.to_json('mpas.json.gz')




######################################
# Legend html testing

# https://github.com/visgl/deck.gl/issues/4850
# https://mybinder.org/v2/gh/ajduberstein/interactive-legend-example/master
# https://discuss.streamlit.io/t/are-you-using-html-in-markdown-tell-us-why/96/65

from ipywidgets import HTML  # this library allows me to render it in Jupyter to see what it looks like, but i don't need it in the actual app

legend_html = """
      <style>
        .line1 {
        height: 2px;
        width: 40px;
        background: rgba(13,8,135);
        display: inline-block;
        margin-bottom: 3px;
        }
        .line2 {
        height: 2px;
        width: 40px;
        background: rgba(126,3,168);
        display: inline-block;
        margin-bottom: 3px;
        }
        .line3 {
        height: 2px;
        width: 40px;
        background: rgba(204,71,121);
        display: inline-block;
        margin-bottom: 3px;
        }
        .line4 {
        height: 2px;
        width: 40px;
        background: rgba(249,149,65);
        display: inline-block;
        margin-bottom: 3px;
        }
        .line5 {
        height: 2px;
        width: 40px;
        background: rgba(241,250,34);
        display: inline-block;
        margin-bottom: 3px;
        }
      </style>
      <div style="text-align:left; margin-bottom:10px">
        <h4 style="margin-bottom:-10px">Connection probability</h4>
        <span class="line1"></span>  &#62;10%<br>
        <span class="line2"></span>  &#62;1%<br>
        <span class="line3"></span>  &#62;0.1%<br>
        <span class="line4"></span>  &#62;0.01%<br>
        <span class="line5"></span>  &#62;0.001%<br>
      </div>
    """

HTML(legend_html)



######################################
# Coastline

# I tried to load my coastline on the map, but I don't think its worth it.

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

# If I want to try again in the future, maybe I could do gridlayer, or simplify the geometry.



#############################################################
# These were style edits to make the map the full height. It was extermely tedious and this was the
# only way to get it to work.
# I don't think its worth doing this.
# You can't say 100% but you can set it in pixels. Doing just 1 line of code is better than all of 
# the below, which may not stay stable overtime.

# remove padding
# remove bottom container and footer
# set map height to 100%
# padding = 0
# st.markdown(f""" <style>
#     .appview-container .main .block-container{{
#         padding-top: {padding}rem;
#         padding-right: {padding}rem;
#         padding-left: {padding}rem;
#         padding-bottom: {padding}rem;
#     }}
#     .egzxvld4 {{  /* can't just set it as all descendants. This is a bit tedious but only way I could get it to work. */
#         height: 100%;
#     }}
#     .egzxvld4 > div:first-child {{  /* This div doesn't have a class identifier. This reads as: get all the descendant div, then only the first child */
#         height: 100%;
#     }}
#     .e1tzin5v0 > div:nth-child(3){{
#         height: 100%;
#     }}
#     .e19lei0e0 {{
#         height: 100%;
#     }}
#     .stDeckGlJsonChart{{
#         height: 100%;
#     }}
#     #deckgl-wrapper {{
#         height: 100% !important;
#     }}
#     #view-default-view {{
#         height: 100% !important;
#     }}
#     #view-default-view > div:first-child {{
#         height: 100% !important;
#     }}
#     .css-qcqlej {{
#         display: none;
#     }}
#     .css-164nlkn {{
#         display: none;
#     }}
#     </style> """, unsafe_allow_html=True)
#############################################################


######################################
# TO do in the future:


# 1
# Persistence points and lines
# Make this its own tab. Coloring is going to be a challenge.
# There was that example in the legend links showing how to generate random colors, perhaps do this
# (maybe there is a more general library too), and then code it into the conn points and lines.
# The lines can have opacity.

# 2
# How will I do the settlement rasters? Bitmap looked like shit.
# Maybe I'll need to do a whole different kind of map. See GridLayer and H3HexagonLayer

