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

protect_by_password()

st.title("API calls")

#MAIN PROG
try:
    show_previs = st.checkbox("Prévisions météoblue",False)
    show_meteo_analysis = st.checkbox("Analyse Meteo",False)
    show_meteo_annual_analysis = st.checkbox("Analyse Annuelle Meteo",False)
    
    show_chronique_pluvio = st.checkbox("Données pluvio",False)
    show_situation_onde = st.checkbox("Situation ONDE",False)
    show_alerte = st.checkbox("Echelles d'alerte",False)
    show_chronique_hydro = st.checkbox("Données hydro",False)
    show_last_communications = st.checkbox("Communications externes",False)
    show_cummulated_chronique_hydro = st.checkbox("Chroniques hydro cummulées",False)
    
    #show meteo analysis
    if show_meteo_analysis:
        m_title = ":chart: {}".format("Analyse meteorologique")
        m_loading_title = "Chargement {}...".format("Analyse meteorologique")
        showMeteorologicalAnalysis(m_title, m_loading_title)

    #show meteo analysis
    if show_meteo_annual_analysis:
        m_title = ":chart: {}".format("Analyse annuelle meteorologique")
        m_loading_title = "Chargement {}...".format("Analyse annuelle meteorologique")
        showMeteorologicalAnnualAnalysis(m_title, m_loading_title)

    if show_previs : 
        #show meteo previ
        previs()

    #show chronique pluvio grahs
    if show_chronique_pluvio:
        pluvio_data_types = pd.DataFrame(getDataTypePluvio())

        #print(pluvio_data_types)
        for idx, dt in pluvio_data_types.iterrows():
            m_title = ":droplet: {}".format(dt["label"])
            m_loading_title = "Chargement {}...".format(dt["label"])
            showPluvioGraphs(dt, m_title, m_loading_title)
                    
    #show situation map ONDE
    if show_situation_onde :
        showSituationMap()

    #show alertes graphs
    if show_alerte:
        showAlerteGraphs()
    
    #show chronique hydro graphs
    if show_chronique_hydro:
        
        hydro_data_types = pd.DataFrame(getDataTypeHydro())
        hydro_data_types = hydro_data_types.query('(id >= 0) & (displayData.isnull() | displayData==True)')
        hydro_data_types.sort_values(by=['order'],inplace=True)
        #print(hydro_data_types)

        for idx, dt in hydro_data_types.iterrows():
            m_title = ":straight_ruler: {}".format(dt["label"])
            m_loading_title = "Chargement {}...".format(dt["label"])
            showNiveauxGraphs(dt, m_title, m_loading_title)
            
    #show last communications of type external
    if show_last_communications:
        try:
            data = requests.get("http://127.0.0.1:1111/api/communication").json()
            #filter august data
            
            m_datedebut =  int(round(datetime.datetime(2025,8,1,0,0,0).timestamp()*1000.0))  #timestamp in milliseconds
            m_datefin = int(round(datetime.datetime(2025,8,31,23,59,59).timestamp()*1000.0))  #timestamp in milliseconds
            data = list(filter(lambda x: x['dateDebut'] >= m_datedebut, data))
            try:
                data = list(filter(lambda x: x['dateFin'] <= m_datefin, data))
            except: #Keyerror - pas de datefin
                pass
            st.dataframe(data)

            #display json
            for line in data:
                st.header(str(line["id"])+" "+line["title"])
                st.subheader('     '+line["subtitle"])
                st.html("<a href=\""+line["link"]+"\">Lien</a>")

        except Exception as e:
            print(traceback.format_exc())
            st.text("No communication externes")

    #show cummulated chronique graphs
    #show chronique graphs
    if show_cummulated_chronique_hydro:

        hydro_data_types = pd.DataFrame(getDataTypeHydro())

        #hydro_data_types = hydro_data_types.query('(id >= 0) & (displayData.isnull() | displayData==True)')
        hydro_data_types = hydro_data_types.query('id in [4,5,7]')
        hydro_data_types.sort_values(by=['order'],inplace=True)
        #print(hydro_data_types)

        for idx, dt in hydro_data_types.iterrows():
            m_title = ":chart_with_upwards_trend: {}".format(dt["label"])
            m_loading_title = "Chargement {}...".format(dt["label"])
            showCumulatedGraphs(dt, m_title, m_loading_title)
        
except requests.exceptions.ConnectionError as e: 
    st.warning("La connexion à l'API est impossible, verifiez le serveur API")
except Exception as e:
    st.error(e)
