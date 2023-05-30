

# to run from conda
# python -m streamlit run app.py
# to close: while window still open do ctrl+ScrLk

import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import urllib.request
import gzip


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
    #mpa-network-connectivity {{ /* padding of title */
        padding-left: 2rem;
    }}
    footer {{visibility: hidden;}}
    </style> """, unsafe_allow_html=True)



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

# UGH, and now once I added color to lines the caching issue comes up again. It works with the one
# on filter data, but not on this one, even when I clear the Chrome cache. Perhaps test again after
# next restart.

# TODO: (perhaps wait until everthing else is built) try to cache_data again and try other options
# for persist. Also look into the streamlit state stuff.

#@st.cache_data(persist='disk')
def load_connectivity_lines():
    path = 'https://github.com/jcristia/connectivity_mpa_app/blob/master/lines.json.gz?raw=true'
    with urllib.request.urlopen(path) as data_file:
        d = gzip.open(data_file, 'rb')
        df = pd.read_json(d)
    return df

mpas = load_mpas()
lines = load_connectivity_lines()



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


# To do:
# Split out year and month (remove day)
# Built in threshold value and set as mid range and update filter
# Option to select to and from MPA by name (perhaps for multipart ones, it can select all pieces)


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
    st.markdown(legend_html, unsafe_allow_html=True)

@st.cache_data(persist='disk')
def filterdata(lines, selectbox_pld, selectbox_date):
    return lines[(lines.pld==selectbox_pld) & (lines.date==selectbox_date)]


# TODO:

# Simplify MPA geometry
# From all of the connectivity lines, pull the self connections and associate them with the MPA 
# polygons. Also at this time, get the actual MPA names. Decide how to manage multipart ones.
# Also at this time - remove any fields I don't need.

# Tooltip html

# Opacity of lines (this can also be defined in the rgba. It is the 'a')
# Tooltip of lines
# Auto highlight of lines
# Perhaps have small arrows along the line?



def map(updated_df):
    fig = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": 51.6,
                "longitude":-128.2,
                "zoom": 5,
                'height':700,
            },
        description=legend_html,
        layers=[
            pdk.Layer(
                'PolygonLayer',
                mpas[['coordinates', 'MPA ID']],
                get_polygon='coordinates',
                opacity=0.5,
                stroked=True,
                filled=True,
                get_fill_color=[0,92,230],
                pickable=True,
                auto_highlight=True
            ),
            pdk.Layer(
                'LineLayer',
                updated_df,
                get_source_position='start',
                get_target_position='end',
                getWidth=1,
                get_color='color',
                pickable=False,
                auto_highlight=False
            ),
        ],
        # Annoyingly, you can only have ONE tooltip structure for all layers. Perhaps I can change
        # MPAs to include their self-connection values so that the tooltip structure can match.
        tooltip={
            "html": "<b>MPA ID:</b> {MPA ID}"
        },   # Tooltips seem to really slow down the load time, I think(?)
    )
    return fig

if pressed:
    updated_df = filterdata(lines, selectbox_pld, selectbox_date)
    st.pydeck_chart(map(updated_df), use_container_width=True)
else: # to display on start
    updated_df = filterdata(lines, 1, 'average')
    st.pydeck_chart(map(updated_df), use_container_width=True)









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