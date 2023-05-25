

# to run from conda
# python -m streamlit run app.py
# to close: while window still open do ctrl+ScrLk

import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import urllib.request
import gzip

# for testing:
#root = r'C:\Users\cristianij\Documents\Projects\mpa_connectivity_app'


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




st.title('MPA Network Connectivity')

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


# I couldn't get this to work when deployed. It seemed like a pandas error, but it only worked
# when I did cache_data instead of cache_resource. I also needed to set persist='disk'.

@st.cache_data(persist='disk')
def load_connectivity_lines():
    path = 'https://github.com/jcristia/connectivity_mpa_app/blob/master/lines.json.gz?raw=true'
    with urllib.request.urlopen(path) as data_file:
        d = gzip.open(data_file, 'rb')
        df = pd.read_json(d)
    return df

mpas = load_mpas()
lines = load_connectivity_lines()

# To do:
# Split out year and month (remove day)
# Built in threshold value and set as mid range and update filter

with st.sidebar.form(key="my_form"):
    selectbox_pld = st.selectbox('PLD', [1, 3, 7, 10, 21, 30, 40, 60])
    selectbox_date = st.selectbox('Release date', ['average', '2011-01-01', '2011-05-01'])
    pressed = st.form_submit_button("Generate map")
    expander = st.sidebar.expander("Study description")
    expander.write(
        """
    This app visualizes data from **PAPER TITLE AND LINK**
    Blah blah blah
    Blah blah blah
    """
    )

@st.cache_data(persist='disk')
def filterdata(lines, selectbox_pld, selectbox_date):
    return lines[(lines.pld==selectbox_pld) & (lines.date==selectbox_date)]

# To do:
# Set zoom and center point
# Color and hover of MPAs
# Color and hover of lines
# Legend of lines


def map(updated_df):
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
                updated_df,
                get_source_position='start',
                get_target_position='end',
                get_with=2,
            ),
        ],
    )
    return fig


if pressed:
    updated_df = filterdata(lines, selectbox_pld, selectbox_date)
    st.pydeck_chart(map(updated_df), use_container_width=True)
else: # to display on start
    updated_df = filterdata(lines, 1, 'average')
    st.pydeck_chart(map(updated_df), use_container_width=True)

# updated_df = lines
# updated_df = updated_df.query('to_id == 19')
# st.pydeck_chart(map(updated_df), use_container_width=True)

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