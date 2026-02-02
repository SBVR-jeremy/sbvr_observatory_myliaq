#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""2_BresseVallons.py: Display informations about a Station at BresseVallons (Cras)"""

__author__ = "Jeremy Bluteau"
__copyright__ = "Copyright 2026, SBVR Observatory"
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
from streamlit.components.v1 import html
import streamlit.components.v1 as components
from streamlit_extras.no_default_selectbox import selectbox
from streamlit_extras.chart_container import chart_container
from streamlit_extras.app_logo import add_logo

from streamlit.components.v1 import iframe
from streamlit_pdf_viewer import pdf_viewer #PDF viewer
from streamlit_quill import st_quill #WYSIWYG editor

import yaml #login config
from yaml.loader import SafeLoader

import pandas as pd
import numpy as np
import io

from datetime import datetime, date, timezone
from dateutil.relativedelta import *

#import altair as alt

#from PIL import Image

#from selenium import webdriver
#from selenium.webdriver.chrome.service import Service as ChromeService
#from webdriver_manager.chrome import ChromeDriverManager

#from selenium.webdriver.chrome.options import Options  


################
#PDF export template


import pdfkit
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

from pdfkit.api import configuration

#This need to be changed on production !!!
import toml

#Load secret file
try:
    secrets = toml.load("./.streamlit/secrets.toml")
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+secrets["myliaq"]["api_key"]
    }
    wkhtml_path = pdfkit.configuration(wkhtmltopdf = secrets["pdfkit"]["wkhtml"])  #by using configuration you can add path value.

except Exception as e:
    print("Loading secret file failed : 2_BresseVallons.py l:62")
    print(e)
    wkhtml_path = pdfkit.configuration(wkhtmltopdf = "")  #by using configuration you can add path value.

#import locale
#locale.setlocale(locale.LC_TIME, "fr_FR")
from babel.dates import format_date, format_datetime, format_time

import requests
import os

from tools.utility import *
from tools.streamlit_utility import *
from tools.queries import *

# ---------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------
# Test page
# ---------------------------------------------------------------------------------------------
#faviconPath = "static/images/cropped-favicon-32x32.jpg"

#st.set_page_config(layout="wide", page_icon=faviconPath, page_title="SBVR Observatoire - Test images") #,initial_sidebar_state='collapsed')

st.set_page_config(layout="wide")
st.title("Surveillance Risque Inondation Bresse-Vallons")

try:
    #define station constant
    stations = dict()
    station_id = 54
    stations[station_id] = "Cras"
            

    #show meteo previ
    #meteoblue montrevel
    [col1,col2] = st.columns(2)
    with col1:
        components.iframe(
                    "https://www.meteoblue.com/fr/weather/widget/daily/cras-sur-reyssouze_france_3022674?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                    , height=420, width=300)

    with col2:
        data = requests.get("http://127.0.0.1:1111/api/graphAlerte?station_id="+str(station_id)).json()
        #display json
        #st.write(data)
        st.vega_lite_chart(data, use_container_width=True)
     
    #show chronique hydro graphs

    #     id        label displayData     unit  order  numberDecimal
    # 1   4      Hauteur         NaN        m    1.0            NaN
    # 3   9  Hauteur NGF        True  m (NGF)    5.0            2.0
    # 6   5        Débit        True     m3/s    2.0            4.0
    # 4   7  Température        True       °C    3.0            NaN
    # 2   8     Batterie        True        V    4.0            2.0


    hydro_data_types = pd.DataFrame({'id': [4, 9, 5,7,8], 'label': ["Hauteur","Hauteur NGF", "Débit","Température", "Batterie"], 'unit': ["m","m (NGF)","m3/s", "°C", "V"]},
                      index = [1,3,6,4,2])
   
    for idx, dt in hydro_data_types.iterrows():
        m_title = ":straight_ruler: {}".format(dt["label"])
        m_loading_title = "Chargement {}...".format(dt["label"])
        
        expander = st.expander(m_title, expanded=True)
        with expander:
            with st.spinner(m_loading_title):
                #display update informations
                try:
                    url = "http://127.0.0.1:1111/api/graphUpdate?station_id="+str(station_id)+"&type_value_id="+str(dt["id"])+"&show_title=false"
                    #print(url)
                    #data = requests.get(url).json()
                    response = requests.get(url)
                    data = json.loads(response.content)

                    #display json
                    #st.write(data)
                
                    st.container( border=False, height=100).vega_lite_chart(data=data, use_container_width=True)
                except Exception as e:
                    print(traceback.format_exc())
                    st.text("No graph Update")

                #display informations
                try:
                    url = "http://127.0.0.1:1111/api/graphChronique?station_id="+str(station_id)+"&type_value_id="+str(dt["id"])+"&show_title=true"
                    print(url)
                    response = requests.get(url)

                    #print(response.status_code)
                    #print(response.headers)
                    
                    #data = response.json()
                    data = json.loads(response.content)

                    #display json
                    #st.write(data)
                
                    #st.container( border=False, height=250)
                    st.vega_lite_chart(data, use_container_width=True)
                except Exception as e:
                    print(traceback.format_exc())
                    st.text("No graph Chronique")
                    raise e

except requests.exceptions.ConnectionError as e: 
    st.warning("La connexion à l'API est impossible, verifiez le serveur API")
except Exception as e:
    st.error(e)

# update page every 10 mins
st_autorefresh(interval=10 * 60 * 1000, key="dashboard-cras-refresh")
