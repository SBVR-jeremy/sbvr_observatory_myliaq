#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""2_test.py: Display informations about a Station"""

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
# Test page
# ---------------------------------------------------------------------------------------------
#faviconPath = "static/images/cropped-favicon-32x32.jpg"

#st.set_page_config(layout="wide", page_icon=faviconPath, page_title="SBVR Observatoire - Test images") #,initial_sidebar_state='collapsed')
 
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service as ChromeService
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions
# from selenium.webdriver.common.by import By

#options = webdriver.ChromeOptions()
#options.headless = True
#driver = webdriver.Chrome()
#URL = "https://www.mellifere.com/climat/station-ceyzeriat.php"
#driver.get(URL)


# add the cookie responsible for blocking screenshot banners
#driver.get(URL)
#driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# request target web page
#driver.get("https://www.mellifere.com/climat/station-ceyzeriat.php")

#  take sceenshot and directly save it
#driver.save_screenshot('MeteoCeyzeriat.png')

#_timeout = 10  # set the maximum timeout to 10 seconds
#wait = WebDriverWait(driver, _timeout)
#wait.until(expected_conditions.presence_of_element_located(
#    #(By.XPATH, "//div[id='containerClimat']") # wait for XPath selector
#    #(By.CSS_SELECTOR, "div#containerClimat") # wait for CSS selector
#    (By.ID, "containerClimat") # wait for CSS selector
#    )
#)

# image as bytes
#bytes = driver.get_screenshot_as_png()

# image as base64 string
#base64_string = driver.get_screenshot_as_base64()

faviconPath = "static/images/cropped-favicon-32x32.jpg"

st.set_page_config(layout="wide", page_icon=faviconPath, page_title="SBVR Observatoire - Test" ,initial_sidebar_state='collapsed')
 
hide_rainbow_bar()
hide_streamlit_credits()

#st.image(bytes)
st.image('MeteoCeyzeriat.png')



