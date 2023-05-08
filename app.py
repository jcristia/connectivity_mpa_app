

# to run from conda
# python -m streamlit run app.py


import streamlit as st
import pandas as pd
#import geopandas as gpd
#import os
import pydeck as pdk
import json
import urllib.request
import gzip

# for testing:
root = r'C:\Users\cristianij\Documents\Projects\mpa_connectivity_app'


st.set_page_config(page_title="MPA Network Connectivity", layout="wide", page_icon="🌊")


# remove padding
padding = 0
st.markdown(f""" <style>
    .appview-container .main .block-container{{
        padding-top: {padding}rem;
        padding-right: {padding}rem;
        padding-left: {padding}rem;
        padding-bottom: {padding}rem;
    }}
    footer {{visibility: hidden;}}
    </style> """, unsafe_allow_html=True)

# To do:
# remove the footer (see below)
# add some padding for just the title


#############################################################
# These were style edits to make the map the full height. It was extermely tedious and this was the
# only way to get it to work.
# I don't think its worth doing this.
# With the plotly map I will make I should just see if I can control the height from there.
# Otherwise you can do it with a pydeck map. You can't say 100% but you can set it in pixels. Doing
# just 1 line of code is better than all of the below, which may not stay stable overtime.

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





st.title('MPA Network Connectivity')


with st.sidebar.form(key="my_form"):
    expander = st.sidebar.expander("Study description")
    expander.write(
        """
    This app visualizes data from **PAPER TITLE AND LINK**
    Blah blah blah
    Blah blah blah
    """
    )

@st.cache_resource
def load_mpas():
    path = 'https://github.com/jcristia/connectivity_mpa_app/blob/master/mpas.geojson?raw=true'  # have to add ?raw=true to the end
    with urllib.request.urlopen(path) as data_file:
        d = json.load(data_file)
    dfjson = pd.DataFrame.from_dict(d['features'])
    df = pd.DataFrame()
    df["coordinates"] = dfjson.apply(lambda row: row['geometry']["coordinates"][0], axis=1) # This was hard to figure out because the coordinates get double wrapped in list brackets, so you need to go in 1 level.
    df["MPA ID"] = dfjson.apply(lambda row: row['properties']['uID_202011'], axis=1)
    return df

@st.cache_resource
def load_connectivity_lines():
    path = 'https://github.com/jcristia/connectivity_mpa_app/blob/master/lines.json.gz?raw=true'
    with urllib.request.urlopen(path) as data_file:
        d = gzip.open(data_file, 'rb')
        df = pd.read_json(d)
    return df

mpas = load_mpas()
lines = load_connectivity_lines()

def map():
    fig = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": 49.3,
                "longitude":-123.13,
                "zoom": 11,
                'height':700,
            },
        layers=[
            pdk.Layer(
                'PolygonLayer',
                mpas[['coordinates', 'MPA ID']],
                get_polygon='coordinates',
                opacity=0.8,
                stroked=False,
                filled=True,
            ),
            pdk.Layer(
                'LineLayer',
                lines,
                get_source_position='start',
                get_target_position='end',
                get_with=2,
            ),
        ],
    )
    return fig

st.pydeck_chart(map(), use_container_width=True)