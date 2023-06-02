

# to run app from conda: python -m streamlit run app.py
# to close: while tab still open do ctrl+ScrLk

import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import urllib.request
import gzip


st.set_page_config(page_title="MPA Network Connectivity", layout="wide", page_icon="🌊")

# set padding around containers, remove footer
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

#--------Create legend----------#
# (Can't do this in pydeck unfortunately, but given my custom legend, it might just be easier to
# build it manually)
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


# TODO:
# Option to select to and from MPA by name. Hard code this in. Produce the text of the list in 
# data_prep and copy it here (make sure special characters are ok).

# Then down below I will need to add this in to the filter function.

# Study description

#--------Sidebar----------#
with st.sidebar.form(key="my_form"):
    selectbox_pld = st.selectbox('PLD (days)', [1, 3, 7, 10, 21, 30, 40, 60])
    selectbox_date = st.selectbox('Release year-month', ['average', '2011-01', '2011-05', '2011-08', '2014-01', '2014-05', '2014-08', '2017-01', '2017-05', '2017-08'])
    selectbox_thresh = st.selectbox('Connection strength threshold %', [0.001, 0.01, 0.1, 1, 10])
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

#--------Load MPA polygons----------#
@st.cache_resource
def load_mpas():
    path = 'https://github.com/jcristia/connectivity_mpa_app/blob/master/mpas.json.gz?raw=true'
    with urllib.request.urlopen(path) as data_file:
        d = gzip.open(data_file, 'rb')
        df = pd.read_json(d)
    return df


#--------Load connectivity lines----------#
# Issues with cache_data and pandas filtering on the dataset
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


#--------Filter data----------#
@st.cache_data(persist='disk')
def filterdata(mpas, lines, selectbox_pld, period, thresh):
    mpas_filtered = mpas[(mpas.pld==selectbox_pld) & (mpas.date==period)]
    lines_filtered =  lines[(lines.pld==selectbox_pld) & (lines.date==period) & (lines.prob>=thresh)]
    return mpas_filtered, lines_filtered


# TODO:

# Tooltip html to include to/from MPAs and connection strength.

# Opacity of lines (this can also be defined in the rgba. It is the 'a')
# Auto highlight of lines


#--------Build map----------#
def map(mpas_filter, lines_filter):
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
                mpas_filter[['coordinates', 'From MPA']],
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
                lines_filter,
                get_source_position='start',
                get_target_position='end',
                getWidth=1,
                get_color='color',
                pickable=False,
                auto_highlight=False
            ),
        ],
        # Annoyingly, you can only have ONE tooltip structure for all layers.
        tooltip={
            "html": "<b>MPA:</b> {From MPA}"
        },
    )
    return fig


#--------Generate map on load or when button clicked----------#
if pressed:
    if selectbox_date != 'average':
        selectbox_date = f'{selectbox_date}-01'
    mpas_filter, lines_filter = filterdata(mpas, lines, selectbox_pld, selectbox_date, selectbox_thresh/100.0)
    st.pydeck_chart(map(mpas_filter, lines_filter), use_container_width=True)
else: # to display on start
    with st.spinner('Initial map load. This may take a few seconds...'):
        mpas_filter, lines_filter = filterdata(mpas, lines, 1, 'average', 0.00001)
        st.pydeck_chart(map(mpas_filter, lines_filter), use_container_width=True)

