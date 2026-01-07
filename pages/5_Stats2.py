#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""3_api.py: Display informations about a Station"""

__author__ = "Jeremy Bluteau"
__copyright__ = "Copyright 2023, SBVR Observatory"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Jeremy Bluteau"
__email__ = "jeremy.bluteau@syndicat-reyssouze.fr"
__status__ = "Dev"

# ---------------------------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------------------------

import streamlit as st
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.chart_container import chart_container
from streamlit_extras.app_logo import add_logo

import yaml #login config
from yaml.loader import SafeLoader

import pandas as pd

from datetime import datetime, timezone, timedelta
from dateutil import tz

from tools.utility import *
from tools.streamlit_utility import *
from tools.queries import *

# ---------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------
# Test page
# ---------------------------------------------------------------------------------------------
import streamlit.components.v1 as components
from jinja2 import Template
import requests


st.set_page_config(layout="wide")

st.title("Stats 2 calls")
#----------------------------------------------------------------------------------
#function
# type_value = {id: 1, label: "Pluie", displayData: true, unit: "mm", order: 1}  (JSON)
def showDebitsAnalyseGraphs(type_value, m_title, m_loading_title, expanded=False):
    expander = st.expander(m_title, expanded=expanded)
    with expander:
        with st.spinner(m_loading_title):
            stations = dict()
            stations[4] = "Majornas"
            #stations[3] = "Montagnat"
            #stations[1] = "Saone à Macon"
            #stations[2] = "Saint Julien sur R."
            #stations[11] = "Viriat"
            #stations[5] = "Baudières"
            #stations[54] = "Cras"
            #stations[58] = "Pont de Vaux"
            
            #cols = st.columns((len(stations)%4))
            idx = 0
            nbcols = 4 if len(stations)>=4 else len(stations)

            for station_id in stations:
                if (idx % 4 == 0):
                    cols = st.columns(nbcols)

                with cols[idx %4 ]:
                    stationsFull = getStations()
                    my_station = m_extractStation(stationsFull,station_id)
                    try:
                        station_name = my_station['name'] if my_station is not None else "Station not Found"
                    except KeyError:
                        station_name = stations[station_id]

                    st.container(border=False, height=150).markdown(f'<a href="https://reyssouze.myliaq.fr/#/station/hydrometry/{station_id}/dashboard" target="_blank"><h4>:green[{station_name}]</h4></a>', unsafe_allow_html=True)

                    #display informations
                    try:
                        url = "http://127.0.0.1:1111/api/graphDebit?station_id="+str(station_id)+"&type_value_id="+str(type_value["id"])+"&show_title=true"
                        print(url)
                        data = requests.get(url).json()
                        #display json
                        #st.write(data)
                    
                        #st.container( border=False, height=250)
                        st.vega_lite_chart(data, use_container_width=True)
                    except Exception as e:
                        print(traceback.format_exc())
                        st.text("No graph Chronique")
                        raise e

                    idx += 1




#----------------------------------------------------------------------------------
#MAIN PROG
try:
    
    
    #show chronique hydro graphs
    if True:
        
        hydro_data_types = pd.DataFrame(getDataTypeHydro())
        hydro_data_types = hydro_data_types.query('(id >= 0) & (displayData.isnull() | displayData==True)')
        hydro_data_types = hydro_data_types.query('id in [5]')
        hydro_data_types.sort_values(by=['order'],inplace=True)
        #print(hydro_data_types)

        for idx, dt in hydro_data_types.iterrows():
            m_title = ":chart_with_upwards_trend: {}".format(dt["label"])
            m_loading_title = "Chargement {}...".format(dt["label"])
            showDebitsAnalyseGraphs(dt, m_title, m_loading_title, True)
            
        
except requests.exceptions.ConnectionError as e: 
    st.warning("La connexion à l'API est impossible, verifiez le serveur API")
except Exception as e:
    st.error(e)
