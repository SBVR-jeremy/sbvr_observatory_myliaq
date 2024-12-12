#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""1_station.py: Display informations about a Station"""

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
import streamlit_authenticator as stauth
import yaml #login config
from yaml.loader import SafeLoader
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.chart_container import chart_container
from streamlit_extras.app_logo import add_logo

import pandas as pd
import numpy as np
import datetime

import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

import folium
from streamlit_folium import st_folium, folium_static
from folium.plugins import HeatMap, AntPath
import pickle  #to load a saved modelimport base64  #to open .gif files in streamlit app
import psycopg2
from psycopg2.extras import NamedTupleCursor
import matplotlib.pyplot as plt
import base64

import plotly
import kaleido
import plotly 
import json
import altair as alt

from tools.utility import *
from tools.queries import *

# ---------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------
# Station page
# ---------------------------------------------------------------------------------------------
faviconPath = "static/images/cropped-favicon-32x32.jpg"

st.set_page_config(layout="wide", page_icon=faviconPath, page_title="SBVR Observatoire - Statistiques") #,initial_sidebar_state='collapsed')
 
hide_rainbow_bar()
hide_streamlit_credits()

add_logo('static/images/small-logo-carre-quadri-SBVR.jpg')

st.markdown("# Stats reférence")

st.text("Q-X : Maximum annuels des débits instantanés (m3/s)")
stations = dict()
stations[3] = {'code': 'U4014010', 'name':"Montagnat",'Q2': 7.72, 'Q2_min': 6.82, 'Q2_max' : 8.68,'Q5': 11.1, 'Q5_min': 9.61, 'Q5_max' : 12.5, 'Q10': 13.3, 'Q10_min': 11.4, 'Q10_max' : 15.2, 'Q20': 15.4, 'Q20_min': 13.1, 'Q20_max' : 17.8, 'Q50': 18.2, 'Q50_min': 15.2, 'Q50_max' : 21.2 }
stations[4] = {'code': 'U4014020', 'name':"Majornas",'Q2': 21.7, 'Q2_min': 19.9, 'Q2_max' : 23.6,'Q5': 27.4, 'Q5_min': 24.6, 'Q5_max' : 30.6, 'Q10': 31.2, 'Q10_min': 27.5, 'Q10_max' : 35.5, 'Q20': 34.8, 'Q20_min': 30.4, 'Q20_max' : 40.4, 'Q50': 39.4, 'Q50_min': 33.9, 'Q50_max' : 46.6 }
stations[2] = {'code': 'U4054010', 'name':"Saint Julien sur R.",'Q2': 53.3, 'Q2_min': 47, 'Q2_max' : 61.2,'Q5': 70, 'Q5_min': 60.4, 'Q5_max' : 83.2, 'Q10': 81, 'Q10_min': 68.8, 'Q10_max' : 98.7, 'Q20': 91.6, 'Q20_min': 76.1, 'Q20_max' : 114, 'Q50': 105, 'Q50_min': 85.5, 'Q50_max' : 134 }
stations[1] = {'code': 'U4300010', 'name':"Saone à Macon",'Q2': 1470, 'Q2_min': 1340, 'Q2_max' : 1600,'Q5': 1810, 'Q5_min': 1610, 'Q5_max' : 2040, 'Q10': 2030, 'Q10_min': 1780, 'Q10_max' : 2350, 'Q20': 2250, 'Q20_min': 1940, 'Q20_max' : 2640, 'Q50': 2530, 'Q50_min': 2140, 'Q50_max' : 3020 }

stations_filtered = dict()
for station_id in stations:
    stations_filtered[station_id] = {'name': "<a href=\""+"https://www.hydroportail.developpement-durable.gouv.fr/sitehydro/"+stations[station_id]['code'][:8]+"/synthese/regime/hautes-eaux\">"+stations[station_id]['name']+"</a>"
                                     ,'Q2' : str(stations[station_id]['Q2'])+"&#9;&#9;["+str(stations[station_id]['Q2_min'])+";"+str(stations[station_id]['Q2_max'])+"]"
                                     ,'Q5' : str(stations[station_id]['Q5'])+"&#9;&#9;["+str(stations[station_id]['Q5_min'])+";"+str(stations[station_id]['Q5_max'])+"]"
                                     ,'Q10' : str(stations[station_id]['Q10'])+"&#9;&#9;["+str(stations[station_id]['Q10_min'])+";"+str(stations[station_id]['Q10_max'])+"]"
                                     ,'Q20' : str(stations[station_id]['Q20'])+"&#9;&#9;["+str(stations[station_id]['Q20_min'])+";"+str(stations[station_id]['Q20_max'])+"]" }


df = pd.DataFrame(stations_filtered)
st.write(df.to_html(escape=False,index=True, header=False), unsafe_allow_html=True)

st.markdown("# Seuils")
type_values = ['m','m3/s']

#Append stations
stations[11] = {'code': 'U4014010', 'name':"Viriat"}
stations[5] = {'code': 'U4014010', 'name':"Baudières"}
stations[54] = {'code': 'U4014010', 'name':"Cras"}

for idx, type_value in enumerate(type_values):
    #st.dataframe(samples)
    if type_value == "m":
        st.header("Hauteur d'eau")
    elif type_value == "mm/h":
        st.header(":new: Vitesse de montée des eaux (moy 3h)")
    elif type_value == "°C":
        st.header("Température")
    elif type_value == "V":
        st.header("Batterie")
    elif type_value == "m3/s":
        st.header("Débit")

    for station_id in stations:
        # print station
        station = m_getStation(station_id)
        st.text(station['code'][:8]+" - "+station['name'])
        #st.link_button(station['code'][:8]+" - "+station['name'], "https://www.hydroportail.developpement-durable.gouv.fr/sitehydro/"+station['code'][:8]+"/synthese/regime/hautes-eaux")
        #recup des seuils
        seuils = m_getAllSeuils(station_id,type_value)
        if seuils.shape[0] > 0:
            for index, seuil in seuils.iterrows():
                st.markdown("- "+seuil['name']+" : "+str(seuil['value'])+" "+type_value)
                #st.text(seuil)


