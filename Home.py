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
import streamlit_authenticator as stauth
from streamlit_autorefresh import st_autorefresh

import folium
from streamlit_folium import st_folium, folium_static
from folium.plugins import Fullscreen

#from folium.plugins import HeatMap, AntPath

#import pickle  #to load a saved modelimport base64  #to open .gif files in streamlit app
#import psycopg2
#from psycopg2.extras import NamedTupleCursor
#import matplotlib.pyplot as plt
#import base64

#import plotly
#import kaleido
import pandas as pd
from streamlit_extras.grid import grid
from streamlit_extras.altex import sparkline_chart, get_stocks_data
from streamlit_extras.app_logo import add_logo
from streamlit_extras.chart_container import chart_container

from streamlit.components.v1 import html

from tools.utility import *
from tools.queries import *
#from tools.maptools import *

import datetime
from datetime import datetime

import altair as alt

import webbrowser


from dateutil import tz

import math 


# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------


def dashboard():
    
    #st.session_state.hubeau_checkbox_value = st.sidebar.checkbox("Afficher les données hubeau", value=st.session_state.hubeau_checkbox_value)

    # # get all hydrological stations
    # url = "https://reyssouze.myliaq.fr/api//hydrologicalStation/dataTypes"
    # headers = {
    #     "Content-Type" : "application/json; charset=utf-8",
    #     "Authorization" : 'Bearer '+st.secrets["myliaq"]["api_key"]
    # }

    # print(headers)

    # parameters = {}
    # response = requests.get(url, headers=headers , params=parameters)
    # print("Status Code", response.status_code)
    # print("JSON Response ", response.json())
    # st.text( response.json())

    
    #print(samples)
    
    if True:
        stations = dict()
        stations[4] = "Majornas"
        stations[3] = "Montagnat"
        stations[1] = "Saone à Macon"
        stations[2] = "Saint Julien sur R."
        stations[11] = "Viriat"
        stations[5] = "Baudières"
        #stations[12] = "Pont de vaux"
        
        nb_days = 3
        today = datetime.now(timezone.utc)
        two_days_ago = today - timedelta(days=nb_days)
        
        #timestamp in milliseconds
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
        ts_end = int(round(today.timestamp()*1000.0))

        type_values = ['mm/h','m','m3/s','°C', 'V']
        
        for idx, type_value in enumerate(type_values):
            #st.dataframe(samples)
            if type_value == "m":
                st.subheader("Hauteur d'eau")
            elif type_value == "mm/h":
                st.subheader(":new: Vitesse de montée des eaux (moy 3h)")
            elif type_value == "°C":
                st.subheader("Température")
            elif type_value == "V":
                st.subheader("Batterie")
            elif type_value == "m3/s":
                st.subheader("Débit")

            cols = st.columns((len(stations)))
            idx = 0
            for station_id in stations:
                samples = m_getAllSamplesAnalyse(station_id,type_value,start_date=ts_start,end_date=ts_end)
                #st.line_chart(samples, x='timestamp', y='numeric_value')
                if samples.shape[0] == 0:
                    idx += 1
                    continue

                with cols[idx]:
                    station_name = stations[station_id]

                    try:
                        last_record = samples.tail(1)
                        pre_last_record = samples.tail(2).head(1)
                        m_dif= last_record.numeric_value.item() - pre_last_record.numeric_value.item()
                        #st.warning(pre_last_record)
                        #st.warning(last_record)
                        #st.markdown(f"[:green[{station_name}]](/station/{station})")
                        st.markdown(f'<a href="https://reyssouze.myliaq.fr/#/station/hydrometry/{station_id}/dashboard" target="_blank"><h3>:green[{station_name}]</h3></a>', unsafe_allow_html=True)
                        
                        #MAJ indicator
                        #date_diff = datetime.now(timezone.utc)- (last_record.timestamp.item())
                        date_diff = int(round(datetime.now(timezone.utc).timestamp())) - int(round(last_record.timestamp.item().timestamp()))
                        date_diff_hour = (date_diff/3600)

                        #st.warning(date_diff_hour)
                        if (date_diff_hour<=1): #everything seems OK
                            st.metric(":large_green_circle: MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M")), "{} {}".format(round(last_record.numeric_value.item(),3),type_value)) #, delta="{}".format(round(m_dif,3)))
                        elif (date_diff_hour>1 and date_diff_hour <=6) : #paid attention...
                            st.metric(":large_orange_circle: MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M")), "{} {}".format(round(last_record.numeric_value.item(),3),type_value)) #, delta="{}".format(round(m_dif,3)))
                        else: #something wrong...
                            st.metric(":red_circle: MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M")), "{} {}".format(round(last_record.numeric_value.item(),3),type_value)) #, delta="{}".format(round(m_dif,3)))
                            
                        #simple graph
                        #st.line_chart(data,x='date', y='numeric_value')

                        #nicer graph
                        #selection = alt.selection_multi(fields=['ust'], bind='legend')
                        
                        if type_value == 'm':
                            #zoom on y axis - 10cm over and above
                            y_min = samples.min(numeric_only=True).numeric_value - 0.1
                            y_max = samples.max(numeric_only=True).numeric_value + 0.1

                            m_domain = [y_min, y_max]
                        else:
                            #zoom on y axis - 0.5° ove and above
                            y_min = samples.min(numeric_only=True).numeric_value - 0.5
                            y_max = samples.max(numeric_only=True).numeric_value + 0.5

                            m_domain = [y_min, y_max]
                        
                        
                        c = alt.Chart(samples).mark_line(interpolate='monotone',point=True).transform_calculate(
                            combined_tooltip = "datum.numeric_value"
                        ).encode(
                            alt.X('timestamp:T', axis = alt.Axis(tickCount="hour", ticks = True, title = '', 
                                                                        #labelAngle=-75,
                                                                        labelExpr="[timeFormat(datum.value, '%H:%M'),  timeFormat(datum.value, '%H') == '00' ? timeFormat(datum.value, '%d-%m-%Y') : '', timeFormat(datum.value, '%m') == '01' ? timeFormat(datum.value, '%Y') : '']")),
                            alt.Y( 'numeric_value:Q', axis=alt.Axis(labels=True,title=''), scale=alt.Scale(domain=m_domain)),
                            #alt.Color('ust:N',legend=alt.Legend(title='Données')),
                            #alt.Color('ust:N',legend=None),
                            #opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
                            tooltip=[
                                alt.Tooltip("timestamp:T",  format="%Y-%m-%d@%H:%M:%S", title="Date (local)"), 
                                alt.Tooltip("combined_tooltip:N", title="Valeur"), 
                                #alt.Tooltip("ust:N", title="Variable")
                            ]
                        #).add_selection(
                        #    selection
                        ).properties(
                            height=200
                        ).interactive()

                        #recup des seuils
                        seuils = m_getAllSeuils(station_id,type_value)
                        #print(seuils)
                        m_chart = c
                        if seuils.shape[0] > 0:
                            for index, seuil in seuils.iterrows():
                                try:
                                    if str(seuil.htmlColor) == 'nan': 
                                        m_color = 'black'
                                    else:
                                        m_color = str(seuil.htmlColor)
                                except:
                                    m_color = 'black'

                                try:
                                    m_text = str(seuil['name'])
                                except:
                                    m_text = ""
                
                                m_s = alt.Chart(pd.DataFrame({'y': [seuil.value]})).mark_rule(color=m_color).encode(y='y')
                                m_t = alt.Chart(pd.DataFrame({'y': [seuil.value]})).mark_text(text=m_text).encode(y='y')
                                m_chart = m_chart + m_s +m_t

                        
                        st.altair_chart(m_chart, use_container_width=True)             

                    except Exception as e:
                        st.error(e)
                        raise e
                    
                idx += 1
                         

# ---------------------------------------------------------------------------------------------
# Main page*
# ---------------------------------------------------------------------------------------------


faviconPath = "static/images/cropped-favicon-32x32.jpg"

st.set_page_config(layout="wide", page_icon=faviconPath, page_title="SBVR Observatoire MYLIAQ", initial_sidebar_state='collapsed')

#st.experimental_set_query_params()

#plotly.io.kaleido.scope.mathjax= None

#from PIL import Image
## Loading Image using PIL
#im = Image.open('/content/App_Icon.png')
## Adding Image to web app
#st.set_ page_config(page_title="Surge Price Prediction App", page_icon = im)


hide_rainbow_bar()
hide_streamlit_credits()

st.title('SBVR Observatoire MYLIAQ')
st.text('MAJ : {}'.format(datetime.now().strftime('%d/%M/%Y @ %H:%M')))
add_logo('static/images/small-logo-carre-quadri-SBVR.jpg')
dashboard()

# update page every 10 mins
st_autorefresh(interval=10 * 60 * 1000, key="dashboardrefresh")

