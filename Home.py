#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Home.py: This file display the Home page. It's the entrance of the application."""

__author__ = "Jeremy Bluteau"
__copyright__ = "Copyright 2024, SBVR Observatory"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Jeremy Bluteau"
__email__ = "jeremy.bluteau@syndicat-reyssouze.fr"
__status__ = "Dev"


# ---------------------------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------------------------

import streamlit as st
from streamlit_autorefresh import st_autorefresh

#import pickle  #to load a saved modelimport base64  #to open .gif files in streamlit app
#import psycopg2
#from psycopg2.extras import NamedTupleCursor
#import matplotlib.pyplot as plt
#import base64

#import plotly

from streamlit_extras.grid import grid
#from streamlit_extras.altex import sparkline_chart, get_stocks_data
from streamlit_extras.app_logo import add_logo
from streamlit_extras.chart_container import chart_container

from streamlit.components.v1 import html
import streamlit.components.v1 as components

import pandas as pd
import math 
import requests
import datetime

from tools.utility import *
from tools.streamlit_utility import *

# ---------------------------------------------------------------------------------------------
# Main page*
# ---------------------------------------------------------------------------------------------

faviconPath = "static/images/cropped-favicon-32x32.jpg"
st.set_page_config(layout="wide", page_icon=faviconPath, page_title="SBVR Observatoire MYLIAQ", initial_sidebar_state='collapsed')

#st.experimental_set_query_params()

#from PIL import Image
## Loading Image using PIL
#im = Image.open('/content/App_Icon.png')
## Adding Image to web app
#st.set_ page_config(page_title="Surge Price Prediction App", page_icon = im)


# ---------------------------------------------------------------------------------------------

hide_rainbow_bar()
hide_streamlit_credits()

st.title('SBVR Observatoire MYLIAQ')
st.text('MAJ : {}'.format(datetime.datetime.now().strftime('%d/%m/%Y @ %H:%M')))

add_logo('static/images/small-logo-carre-quadri-SBVR.jpg')
# previs()
# niveauAlerte()
# niveauAlerteBis()
# #dashboard()
# chroniqueHauteur()
try:
    #show meteo previ
    previs(True)

    #show alertes graphs
    showAlerteGraphs(True)

    # #show chronique pluvio grahs
    # pluvio_data_types = pd.DataFrame(getDataTypePluvio())

    # #print(pluvio_data_types)
    # for idx, dt in pluvio_data_types.iterrows():
    #     m_title = ":droplet: {}".format(dt["label"])
    #     m_loading_title = "Chargement {}...".format(dt["label"])
    #     showPluvioGraphs(dt, m_title, m_loading_title)
                    
    #show chronique hydro graphs
    hydro_data_types = pd.DataFrame(getDataTypeHydro())
    hydro_data_types = hydro_data_types.query('(id >= 0) & (displayData.isnull() | displayData==True)')
    hydro_data_types.sort_values(by=['order'],inplace=True)
    #print(hydro_data_types)

    for idx, dt in hydro_data_types.iterrows():
        m_title = ":straight_ruler: {}".format(dt["label"])
        m_loading_title = "Chargement {}...".format(dt["label"])
        showNiveauxGraphs(dt, m_title, m_loading_title)
            
        
except requests.exceptions.ConnectionError as e: 
    st.warning("La connexion à l'API est impossible, verifiez le serveur API")
except Exception as e:
    st.error(e)

# update page every 10 mins
st_autorefresh(interval=10 * 60 * 1000, key="dashboardrefresh")

