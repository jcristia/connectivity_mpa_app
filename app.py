

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
    a {{
        text-decoration: none;
    }}
    footer {{visibility: hidden;}}
    </style> """, unsafe_allow_html=True)

# TODO: remove underline from link

st.title('MPA Network Connectivity')
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
        <span class="line1"></span>  &#62;10%<br>
        <span class="line2"></span>  &#62;1%<br>
        <span class="line3"></span>  &#62;0.1%<br>
        <span class="line4"></span>  &#62;0.01%<br>
        <span class="line5"></span>  &#62;0.001%<br>
      </div>
    """

# Hardcode MPA names so that I don't need to generate them here. Generated in data prep script.
mpa_names = ['ALL', 'Admiralty Head Marine Preserve', 'Alaska Maritime National Wildlife Refuge', 'Alty Conservancy', 'Anne Vallee (Triangle Island) Ecological Reserve', 'Apodaca Park', 'Argyle Lagoon San Juan Islands Marine Preserve', 'Baeria Rocks Ecological Reserve', 'Banks Nii Luutiksm Conservancy', 'Bella Coola Estuary Conservancy', 'Beresford Island Ecological Reserve', 'Big Bunsby Marine Park', 'Billy Frank Jr. Nisqually National Wildlife Refuge', 'Bishop Bay-Monkey Beach Conservancy', 'Bishop Bay-Monkey Beach Corridor Conservancy', 'Blake Island Underwater Park', 'Bligh Island Marine Park', 'Bodega Ridge Park', 'Boiler Bay Research Reserve', 'Bone River Natural Area Preserve', 'Boundary Bay Wildlife Management Area', 'Broughton Archipelago Park', 'Buccaneer Bay Park', 'Byers/Conroy/Harvey/Sinnett Islands Ecological Reserve', 'Cape Falcon Marine Reserve', 'Cape Falcon Shoreside Marine Protected Area', 'Cape Kiwanda Marine Garden', 'Cape Scott Park', 'Carter Bay Conservancy', 'Cascade Head Marine Reserve', 'Cascade Head North Marine Protected Area', 'Cascade Head South Marine Protected Area', 'Catala Island Marine Park', 'Checleset Bay Ecological Reserve', 'Cherry Point Aquatic Reserve', 'Cluxewe Wildlife Management Area', 'Clyak Estuary Conservancy', 'Codville Lagoon Marine Park', 'Colvos Passage Marine Preserve', 'Copeland Islands Marine Park', 'Cormorant Channel Marine Park', 'Coste Rocks Park', 'Cypress Island Aquatic Reserve', 'Daawuuxusda Conservancy', 'Dabob Bay Natural Area Preserve', 'Dala-Kildala Rivers Estuaries Park', 'Damaxyaa Conservancy', 'Dawley Passage Park', 'Deception Pass Underwater Park', 'Desolation Sound Marine Park', 'Dewdney And Glide Islands Ecological Reserve', 'Dixie Cove Marine Park', 'Drumbeg Park', 'Duke Of Edinburgh (Pine/Storm/Tree Islets) Ecological Reserve', 'Dungeness National Wildlife Refuge', 'Duu Guusd Conservancy', 'Dzawadi/Klinaklini Estuary Conservancy', "Ebey's Landing National Historical Reserve", 'Echo Bay Marine Park', 'Elk River Natural Resources Conservation Area', 'Epper Passage Park', 'Esquimalt Lagoon Migratory Bird Sanctuary', 'False Bay San Juan Islands Marine Preserve', 'Fidalgo Bay Aquatic Reserve', 'Fiordland Conservancy', 'Flores Island Park', 'Foch-Gilttoyees Park', 'Foch-Gilttoyees Protected Area', 'Fort Casey Underwater Park', 'Fort Ward Underwater Park', 'Fort Worden Underwater Park', 'Francis Point Ecolgical Reserve', 'Francis Point Park', 'Friday Harbor San Juan Islands Marine Preserve', 'Gabriola Sands Park', 'Garden Bay Marine Park', 'George C. Reifel Migratory Bird Sanctuary', 'Gitxaala Nii Luutiksm/Kitkatla Conservancy', 'Glacier Bay National Park & Preserve', 'Goat Cove Conservancy', "God's Pocket Marine Park", 'Gowlland Tod Park', 'Grays Harbor National Wildlife Refuge', 'Green Inlet Marine Park', 'Gulf Islands National Park Reserve Of Canada', 'Gwaii Haanas National Marine Conservation Area Reserve & Haida Heritage Site', 'Hakai Conservation Study Area', 'Hakai Luxvbalis Conservancy', 'Halkett Bay Marine Park', 'Harmony Islands Marine Park', 'Hathayim Marine Park [A.K.A. Von Donop Marine Park]', 'Haystack Rock Marine Garden', 'Helliwell Park', 'Hesquiat Peninsula Park', 'Homathko Estuary Park', 'Hudson Rocks Ecological Reserve', 'Jackson Narrows Marine Park', 'Jedediah Island Marine Park', 'Jesse Falls Protected Area', 'Juan De Fuca Park', "K'distsausk/Turtle Point Conservancy", "K'nabiyaaxl/Ashdown Conservancy", "K'uuna Gwaay Conservancy", "K'waal Conservancy", 'Kennedy Creek Natural Area Preserve', 'Kennedy Island Conservancy', 'Keystone Conservation Area', 'Khutzeymateen Inlet Conservancy', 'Kilbella Estuary Conservancy', 'Kimsquit Estuary Conservancy', 'Kitson Island Marine Park', 'Kopachuck Underwater Park', 'Ksgaxl/Stephens Island Conservancy', "Ksi X' Anmaas Conservancy", "Ksi Xts'at'kw/Stagoo Conservancy", 'Ktisgaidz/Macdonald Bay Conservancy', 'Kunxalas Conservancy', 'Kwatna Estuary Conservancy', 'Lanz And Cox Islands Park', 'Larcom Lagoon Conservancy', 'Lawn Point Park', "Lax Ka'gaas/Campania Conservancy", 'Lax Kul Nii Luutiksm/Bonilla Conservancy', 'Lax Kwaxl/Dundas And Melville Islands Conservancy', 'Lax Kwil Dziidz/Fin Conservancy', 'Lucy Islands Conservancy', 'Mahpahkum-Ahkwuna/Deserters-Walker Conservancy', 'Mansons Landing Park', 'Manzanita Cove Conservancy', 'Maquinna Marine Park', 'Maury Island Aquatic Reserve', "Maxtaktsm'aa/Union Passage Conservancy", 'Miracle Beach Park', 'Mitlenatch Island Nature Park', 'Monckton Nii Luutiksm Conservancy', 'Montague Harbour Marine Park', 'Moore/Mckenney/Whitmore Islands Ecological Reserve', 'Muqqiwn/Brooks Peninsula Park', 'Naikoon Park', 'Nang Xaldangaas Conservancy', 'Negiy/Nekite Estuary Conservancy', 'Nestucca Bay National Wildlife Refuge', 'Newcastle Island Marine Park', 'Niawiakum River Natural Area Preserve', 'Nisqually Reach Aquatic Reserve', 'North Bay Natural Area Preserve', 'Nuchatlitz Park', 'Oak Bay Islands Ecological Reserve', 'Octopus Hole Conservation Area', 'Octopus Islands Marine Park', 'Oliver Cove Marine Park', 'Olympic Coast National Marine Sanctuary', 'Olympic National Park', 'Orchard Rocks Conservation Area', 'Otter Rock Marine Garden', 'Otter Rock Marine Reserve', 'Pacific Rim National Park Reserve Of Canada', 'Padilla Bay National Estuarine Research Reserve', 'Palemin/Estero Basin Conservancy', 'Parksville-Qualicum Beach Wildlife Management Area', 'Penrose Island Marine Park', 'Phillips Estuary/?Nacinuxw Conservancy', 'Pirate Cove Research Reserve', 'Pirates Cove Marine Park', 'Plumper Cove Marine Park', 'Porteau Cove Park', 'Protection Island Aquatic Reserve', 'Protection Island National Wildlife Refuge', 'Quatse Estuary Wildlife Management Area', 'Quatsino Park', 'Qwiquallaaq/Boat Bay Conservancy', 'Race Rocks Ecological Reserve', 'Raft Cove Park', 'Rathtrevor Beach Park', 'Rebecca Spit Marine Park', 'Rendezvous Island South Park', 'Roberts Bank Wildlife Management Area', 'Robson Bight (Michael Bigg) Ecological Reserve', 'Rock Bay Marine Park', 'Roscoe Bay Park', 'Rugged Point Marine Park', 'Sabine Channel Marine Park', "Saltar's Point Beach Conservation Area", 'Saltery Bay Park', 'San Juan County/Cypress Island Marine Biological Preserve', 'San Juan Island National Historical Park', 'San Juan Islands National Wildlife Refuge', 'Sandwell Park', 'Santa Gertrudis-Boca Del Infierno Park', 'Sargeant Bay Park', 'Sartine Island Ecological Reserve', 'Shaw Island San Juan Islands Marine Preserve', 'Shearwater Hot Springs Conservancy', 'Shoal Harbour Migratory Bird Sanctuary', 'Siletz Bay National Wildlife Refuge', 'Sitka National Historical Park', 'Skeena Bank Conservancy', "Skwelwil'em Squamish Estuary Wildlife Management Area", 'Small Inlet Marine Park', 'Smelt Bay Park', 'Smith and Minor Island Aquatic Reserve', 'Smuggler Cove Marine Park', 'South Puget Sound Wildlife Area', 'Stair Creek Conservancy', 'Strait Of Georgia And Howe Sound Glass Sponge Reef closure (Dorman Point)', 'Strait Of Georgia And Howe Sound Glass Sponge Reef closure (East Defence Islands)', 'Strait Of Georgia And Howe Sound Glass Sponge Reef closure (Queen Charlotte Channel)', 'Strathcona Park', 'Sturgeon Bank Wildlife Management Area', 'Sue Channel Park', 'Sulphur Passage Park', 'Sund Rock Conservation Area', 'Surge Narrows Park', 'Sydney Inlet Park', 'Tahsish River Ecological Reserve', 'Tahsish-Kwois Park', 'Teakerne Arm Park', 'Ten Mile Point Ecological Reserve', 'Thurston Bay Marine Park', 'Titlow Beach Marine Preserve', 'Tlall Conservancy', 'Tofino Mudflats Wildlife Management Area', 'Tolmie Underwater Park', 'Tongue Point Marine Life Sanctuary', 'Tow Hill Ecological Reserve', 'Tribune Bay Park', "Ugwiwa'/Cape Caution Conservancy", "Ugwiwa'/Cape Caution-Blunden Bay Conservancy", 'Union Passage Marine Park', 'Vargas Island Park', 'Victoria Harbour Migratory Bird Sanctuary', 'Wakeman Estuary Conservancy', 'Wakes Cove Park', 'Waketickeh Creek Conservation Area', 'Wallace Island Marine Park', 'Walsh Cove Park', 'Weewanie Hot Springs Park', 'Whale Cove Habitat Refuge', 'Whaleboat Island Marine Park', 'Willapa National Wildlife Refuge', 'Woodard Bay Natural Resources Conservation Area', 'Xwakwe?Naxde?Ma/Stafford Estuary Conservancy', 'Yaquina Head Marine Garden', 'Yellow and Low Islands San Juan Islands Marine Preserve', "Z's Reef Marine Preserve"]

# TODO:
# Study description

#--------Sidebar----------#
with st.sidebar.form(key="my_form"):
    selectbox_pld = st.selectbox('PLD (days)', [1, 3, 7, 10, 21, 30, 40, 60])
    selectbox_date = st.selectbox('Release year-month', ['average', '2011-01', '2011-05', '2011-08', '2014-01', '2014-05', '2014-08', '2017-01', '2017-05', '2017-08'])
    selectbox_thresh = st.selectbox('Connection strength threshold %', [0.001, 0.01, 0.1, 1, 10])
    selectbox_from = st.selectbox('From MPA', mpa_names)
    selectbox_to = st.selectbox('To MPA', mpa_names)
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
    mpas_filter, lines_filter = filterdata(mpas, lines, selectbox_pld, selectbox_date, selectbox_thresh, selectbox_from, selectbox_to)
    st.pydeck_chart(map(mpas_filter, lines_filter), use_container_width=True)
else: # to display on start
    with st.spinner('Initial map load. This may take a few seconds...'):
        mpas_filter, lines_filter = filterdata(mpas, lines, 1, 'average', 0.001, 'ALL', 'ALL')
        st.pydeck_chart(map(mpas_filter, lines_filter), use_container_width=True)

