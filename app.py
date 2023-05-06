

# to run from conda
# python -m streamlit run app.py


import streamlit as st

st.title('MPA Network Connectivity')

#@st.cache_data
# geojson data

with st.sidebar.form(key="my_form"):
    expander = st.sidebar.expander("Study description")
    expander.write(
        """
    This app visualizes data from **PAPER TITLE AND LINK**
    Blah blah blah
    Blah blah blah
    """
    )

st.map(data=None, zoom=None, use_container_width=True)
