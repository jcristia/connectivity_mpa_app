

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
    #nearshore-mpa-network-connectivity {{ /* padding of title */
        padding-left: 2rem;
    }}
    a {{
        text-decoration: none;
    }}
    footer {{visibility: hidden;}}
    </style> """, unsafe_allow_html=True)

st.title('Nearshore MPA Network Connectivity')
st.markdown("<div id=pub style='padding-left: 2rem;'><a href='https://www.biorxiv.org/content/10.1101/2023.05.01.538971v1'>Cristiani et al. 2023</a></div>", unsafe_allow_html=True)

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
        <p style="font-size: 0.75em; margin-bottom:3px"># of larvae settled / # released from origin * 100</p>
        <span class="line1"></span>  &#62;10%<br>
        <span class="line2"></span>  &#62;1%<br>
        <span class="line3"></span>  &#62;0.1%<br>
        <span class="line4"></span>  &#62;0.01%<br>
        <span class="line5"></span>  &#62;0.001%<br>
      </div>
    """

# Hardcode MPA names so that I don't need to generate them here. Generated in data prep script.
mpa_names = ['ALL', 'Admiralty Head Marine Preserve', 'Alaska Maritime National Wildlife Refuge', 'Anne Vallee (Triangle Island) Ecological Reserve', 'Apodaca Park', 'Argyle Lagoon San Juan Islands Marine Preserve', 'Baeria Rocks Ecological Reserve', 'Banks Nii Luutiksm Conservancy', 'Beresford Island Ecological Reserve', 'Big Bunsby Marine Park', 'Blake Island Underwater Park', 'Bligh Island Marine Park', 'Bodega Ridge Park', 'Boiler Bay Research Reserve', 'Boundary Bay Wildlife Management Area', 'Broughton Archipelago Park', 'Buccaneer Bay Park', 'Byers/Conroy/Harvey/Sinnett Islands Ecological Reserve', 'Cape Falcon Marine Reserve', 'Cape Falcon Shoreside Marine Protected Area', 'Cape Kiwanda Marine Garden', 'Cape Scott Park', 'Cascade Head Marine Reserve', 'Cascade Head North Marine Protected Area', 'Cascade Head South Marine Protected Area', 'Catala Island Marine Park', 'Checleset Bay Ecological Reserve', 'Cherry Point Aquatic Reserve', 'Cluxewe Wildlife Management Area', 'Colvos Passage Marine Preserve', 'Copeland Islands Marine Park', 'Cormorant Channel Marine Park', 'Cypress Island Aquatic Reserve', 'Daawuuxusda Conservancy', 'Dabob Bay Natural Area Preserve', 'Damaxyaa Conservancy', 'Deception Pass Underwater Park', 'Desolation Sound Marine Park', 'Dewdney And Glide Islands Ecological Reserve', 'Drumbeg Park', 'Duke Of Edinburgh (Pine/Storm/Tree Islets) Ecological Reserve', 'Dungeness National Wildlife Refuge', 'Duu Guusd Conservancy', "Ebey's Landing National Historical Reserve", 'Esquimalt Lagoon Migratory Bird Sanctuary', 'False Bay San Juan Islands Marine Preserve', 'Fidalgo Bay Aquatic Reserve', 'Flores Island Park', 'Fort Casey Underwater Park', 'Fort Ward Underwater Park', 'Fort Worden Underwater Park', 'Francis Point Ecolgical Reserve', 'Francis Point Park', 'Friday Harbor San Juan Islands Marine Preserve', 'Gabriola Sands Park', 'Garden Bay Marine Park', 'George C. Reifel Migratory Bird Sanctuary', 'Gitxaala Nii Luutiksm/Kitkatla Conservancy', 'Glacier Bay National Park & Preserve', "God's Pocket Marine Park", 'Gowlland Tod Park', 'Gulf Islands National Park Reserve Of Canada', 'Gwaii Haanas National Marine Conservation Area Reserve & Haida Heritage Site', 'Hakai Luxvbalis Conservancy', 'Halkett Bay Marine Park', 'Harmony Islands Marine Park', 'Hathayim Marine Park [A.K.A. Von Donop Marine Park]', 'Haystack Rock Marine Garden', 'Helliwell Park', 'Hesquiat Peninsula Park', 'Homathko Estuary Park', 'Hudson Rocks Ecological Reserve', 'Jedediah Island Marine Park', 'Juan De Fuca Park', "K'nabiyaaxl/Ashdown Conservancy", "K'uuna Gwaay Conservancy", 'Kennedy Creek Natural Area Preserve', 'Kennedy Island Conservancy', 'Keystone Conservation Area', 'Kitson Island Marine Park', 'Kopachuck Underwater Park', 'Ksgaxl/Stephens Island Conservancy', 'Ktisgaidz/Macdonald Bay Conservancy', 'Kunxalas Conservancy', 'Lanz And Cox Islands Park', 'Lawn Point Park', "Lax Ka'gaas/Campania Conservancy", 'Lax Kul Nii Luutiksm/Bonilla Conservancy', 'Lax Kwaxl/Dundas And Melville Islands Conservancy', 'Lax Kwil Dziidz/Fin Conservancy', 'Lucy Islands Conservancy', 'Mahpahkum-Ahkwuna/Deserters-Walker Conservancy', 'Mansons Landing Park', 'Manzanita Cove Conservancy', 'Maquinna Marine Park', 'Maury Island Aquatic Reserve', 'Miracle Beach Park', 'Mitlenatch Island Nature Park', 'Monckton Nii Luutiksm Conservancy', 'Montague Harbour Marine Park', 'Moore/Mckenney/Whitmore Islands Ecological Reserve', 'Muqqiwn/Brooks Peninsula Park', 'Naikoon Park', 'Nang Xaldangaas Conservancy', 'Nestucca Bay National Wildlife Refuge', 'Newcastle Island Marine Park', 'Nisqually Reach Aquatic Reserve', 'Nuchatlitz Park', 'Oak Bay Islands Ecological Reserve', 'Octopus Hole Conservation Area', 'Octopus Islands Marine Park', 'Olympic Coast National Marine Sanctuary', 'Olympic National Park', 'Orchard Rocks Conservation Area', 'Otter Rock Marine Garden', 'Otter Rock Marine Reserve', 'Pacific Rim National Park Reserve Of Canada', 'Padilla Bay National Estuarine Research Reserve', 'Palemin/Estero Basin Conservancy', 'Parksville-Qualicum Beach Wildlife Management Area', 'Penrose Island Marine Park', 'Phillips Estuary/?Nacinuxw Conservancy', 'Pirate Cove Research Reserve', 'Pirates Cove Marine Park', 'Plumper Cove Marine Park', 'Porteau Cove Park', 'Protection Island Aquatic Reserve', 'Protection Island National Wildlife Refuge', 'Race Rocks Ecological Reserve', 'Raft Cove Park', 'Rathtrevor Beach Park', 'Rebecca Spit Marine Park', 'Rendezvous Island South Park', 'Roberts Bank Wildlife Management Area', 'Rock Bay Marine Park', 'Roscoe Bay Park', 'Rugged Point Marine Park', 'Sabine Channel Marine Park', "Saltar's Point Beach Conservation Area", 'Saltery Bay Park', 'San Juan County/Cypress Island Marine Biological Preserve', 'San Juan Island National Historical Park', 'San Juan Islands National Wildlife Refuge', 'Sandwell Park', 'Santa Gertrudis-Boca Del Infierno Park', 'Sargeant Bay Park', 'Sartine Island Ecological Reserve', 'Shaw Island San Juan Islands Marine Preserve', 'Shoal Harbour Migratory Bird Sanctuary', 'Siletz Bay National Wildlife Refuge', 'Sitka National Historical Park', 'Skeena Bank Conservancy', "Skwelwil'em Squamish Estuary Wildlife Management Area", 'Small Inlet Marine Park', 'Smelt Bay Park', 'Smith and Minor Island Aquatic Reserve', 'Smuggler Cove Marine Park', 'South Puget Sound Wildlife Area', 'Strait Of Georgia And Howe Sound Glass Sponge Reef closure (Dorman Point)', 'Strait Of Georgia And Howe Sound Glass Sponge Reef closure (East Defence Islands)', 'Strait Of Georgia And Howe Sound Glass Sponge Reef closure (Queen Charlotte Channel)', 'Sturgeon Bank Wildlife Management Area', 'Sund Rock Conservation Area', 'Surge Narrows Park', 'Teakerne Arm Park', 'Ten Mile Point Ecological Reserve', 'Thurston Bay Marine Park', 'Titlow Beach Marine Preserve', 'Tlall Conservancy', 'Tolmie Underwater Park', 'Tongue Point Marine Life Sanctuary', 'Tow Hill Ecological Reserve', 'Tribune Bay Park', "Ugwiwa'/Cape Caution Conservancy", "Ugwiwa'/Cape Caution-Blunden Bay Conservancy", 'Vargas Island Park', 'Victoria Harbour Migratory Bird Sanctuary', 'Wakes Cove Park', 'Waketickeh Creek Conservation Area', 'Wallace Island Marine Park', 'Walsh Cove Park', 'Whale Cove Habitat Refuge', 'Whaleboat Island Marine Park', 'Willapa National Wildlife Refuge', 'Woodard Bay Natural Resources Conservation Area', 'Xwakwe?Naxde?Ma/Stafford Estuary Conservancy', 'Yaquina Head Marine Garden', 'Yellow and Low Islands San Juan Islands Marine Preserve', "Z's Reef Marine Preserve"]

#--------Sidebar----------#
with st.sidebar.form(key="my_form"):
    selectbox_pld = st.selectbox('Pelagic larval duration (days)', [1, 3, 7, 10, 21, 30, 40, 60])
    selectbox_date = st.selectbox('Release year-month', ['average', '2011-01', '2011-05', '2011-08', '2014-01', '2014-05', '2014-08', '2017-01', '2017-05', '2017-08'])
    selectbox_thresh = st.selectbox('Connection strength threshold %', ['ALL (0.001)', 0.01, 0.1, 1, 10])
    selectbox_from = st.selectbox('From MPA', mpa_names)
    selectbox_to = st.selectbox('To MPA', mpa_names)
    pressed = st.form_submit_button("Generate map")
    expander = st.sidebar.expander("Study description")
    expander.write(
        """
    This app visualizes data from Cristiani et al. 2023: [Quantifying marine larval dispersal to
    assess MPA network connectivity and inform furture national and transboundary planning efforts](https://www.biorxiv.org/content/10.1101/2023.05.01.538971v1).

    We modeled the dispersal of multiple nearshore species to estimate the potential connectivity of the existing MPAs in British Columbia, Canada, including connections to MPAs in the United States by simulating dispersal using a biophysical model with regional oceanographic currents.
    
    A dispersal simulation was initiated by simultaneously releasing particles from all MPAs. 
    Particles were released every 4 hours for 2 weeks to capture tidal variation. Simulations were 
    conducted for three seasons (winter: Jan-Mar, spring freshet: May-Jul, summer/fall:
    Aug-Oct) over three years (2011, 2014, 2017). There were 2.7 million particles released per time
    period. Particles were tracked as they were advected by velocity fields in the hydrodynamic 
    models and diffused at a constant rate. We applied a 15% daily mortality rate. Particles were 
    tracked for the length of each pelagic larval duration (PLD). At the end of the PLD, any 
    particles that were over an MPA were assumed to settle and make a successful connection between 
    the source population and the destination population. We then calculated a directional 
    probability of connectivity between MPAs by dividing the number of particles that settle on an 
    MPA by the total amount of particles released from the origin MPA (x 100).
    """
    )
    st.markdown(legend_html, unsafe_allow_html=True)

#--------Load MPA polygons----------#
#@st.cache_resource
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
def filterdata(mpas, lines, selectbox_pld, period, thresh, selectbox_from, selectbox_to):
    mpas_filtered = mpas[(mpas.pld==selectbox_pld) & (mpas.date==period)]
    if selectbox_from == 'ALL' and selectbox_to == 'ALL':
        lines_filtered =  lines[(lines.pld==selectbox_pld) & (lines.date==period) & (lines.prob>=thresh)]
    elif selectbox_from != 'ALL' and selectbox_to == 'ALL':
        lines_filtered =  lines[(lines.pld==selectbox_pld) & (lines.date==period) & (lines.prob>=thresh) & (lines['From MPA']==selectbox_from)]
    elif selectbox_from == 'ALL' and selectbox_to != 'ALL':
        lines_filtered =  lines[(lines.pld==selectbox_pld) & (lines.date==period) & (lines.prob>=thresh) & (lines['To MPA']==selectbox_to)]
    else:
        lines_filtered =  lines[(lines.pld==selectbox_pld) & (lines.date==period) & (lines.prob>=thresh) & (lines['From MPA']==selectbox_from) & (lines['To MPA']==selectbox_to)]
    return mpas_filtered, lines_filtered


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
                mpas_filter,
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
            pdk.Layer( # this is a dummy layer that is a thicker width to make hovering easier. Unfortunately, you can't change the picking radius.
                'LineLayer',
                lines_filter,
                get_source_position='start',
                get_target_position='end',
                getWidth=4,
                get_color=[0,0,0,0],
                pickable=True,
                auto_highlight=True
            ),
        ],
        # Annoyingly, you can only have ONE tooltip structure for all layers.
        tooltip={
            "html": 
            "<b>From MPA:</b> {From MPA}<br/>" 
            "<b>To MPA:</b> {To MPA}<br/>"
            "<b>Connection:</b> {prob}<br/>"
        },
    )
    return fig


#--------Generate map on load or when button clicked----------#
if pressed:
    if selectbox_date != 'average':
        selectbox_date = f'{selectbox_date}-01'
    if selectbox_thresh == 'ALL (0.001)':
        selectbox_thresh = 0.001
    mpas_filter, lines_filter = filterdata(mpas, lines, selectbox_pld, selectbox_date, selectbox_thresh, selectbox_from, selectbox_to)
    if len(lines_filter)==0 and selectbox_from != selectbox_to:
        st.warning('There are no connections for that combination of parameter values.')
    st.pydeck_chart(map(mpas_filter, lines_filter), use_container_width=True)
else: # to display on start
    with st.spinner('Initial map load. This may take a few seconds...'):
        mpas_filter, lines_filter = filterdata(mpas, lines, 1, 'average', 0.001, 'ALL', 'ALL')
        st.pydeck_chart(map(mpas_filter, lines_filter), use_container_width=True)

