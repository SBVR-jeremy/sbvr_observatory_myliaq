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
#from streamlit_extras.altex import sparkline_chart, get_stocks_data
from streamlit_extras.app_logo import add_logo
from streamlit_extras.chart_container import chart_container

from streamlit.components.v1 import html
import streamlit.components.v1 as components

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
def previs():
    with st.spinner('Chargement'):
        expander = st.expander(":sun_small_cloud: Prévi METEO")
        with expander:
            [col1,col2,col3] = st.columns(3)
            #meteoblue Bourg en bresse
            with col1:
                components.iframe(
                    "https://www.meteoblue.com/en/weather/widget/daily/bourg-en-bresse_france_3031009?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                    , height=420, width=300)
            
            #meteoblue montrevel
            with col2:
                components.iframe(
                    "https://www.meteoblue.com/en/weather/widget/daily/montrevel-en-bresse_france_2992050?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                    , height=420, width=300)
            
            #meteoblue Pont de vaux
            with col3:
                components.iframe(
                "https://www.meteoblue.com/en/weather/widget/daily/pont-de-vaux_france_2986227?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                , height=420, width=300)

def printGraphNiveau(station_id, stations, ts_start, ts_end, unit_symbol='m'):
    zones = pd.DataFrame(columns=["station","seuil","isOverrunThreshold", "min", "max", "value","color"])
    zones = m_getAllZones(zones, station_id, unit_symbol)

    if zones.shape[0] > 0:
        #print(zones)
        chart = (
            alt.Chart(zones)
            .mark_bar()
            .transform_calculate(
                v_min= 'round(datum.min * 100) / 100',
                v_max='round(datum.max * 100) / 100',
                combined_tooltip = "datum.v_min + '"+ unit_symbol + " <= ' + datum.seuil + ' < ' + datum.v_max + '" + unit_symbol +  "'"
            )
            .encode(
                x=alt.X("station:N", title=""),
                y=alt.Y("value:Q", title=""),
                color=alt.Color("color:N").scale(None),
                tooltip=alt.Tooltip("combined_tooltip:N"),
                order=alt.Order("min:N", sort="ascending"),
                )
        )
        #st.altair_chart(chart, use_container_width=True)

        annotations_df = pd.DataFrame(columns=["index", "value", "marker", "description"])

        #define text color depending the max value
        val_max = zones['max'].max()
        #val_max = 2
        domainT = [0, val_max/2,  val_max]
        rangeT_ = ['white', 'white', 'red']

    else:
        domainT = [0]
        rangeT_ = ['black']



    samples = m_getAllSamplesAnalyse(station_id,unit_symbol,start_date=ts_start,end_date=ts_end)
    annotations_df = pd.DataFrame(columns=["index", "value", "marker", "description"])

    #st.line_chart(samples, x='timestamp', y='numeric_value')
    if samples.shape[0] != 0:
        last_record = samples.tail(1)
        annotations_df.loc[-1] = [station_id, "{}".format(round(last_record.numeric_value.item(),3)), "◀{}{}▶ ".format(round(last_record.numeric_value.item(),3),unit_symbol), "MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))]
        #annotations_df.loc[-1] = [stations[station_id],2, "◀{}m ".format(round(last_record.numeric_value.item(),3)), "MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))]
        annotations_df.index = annotations_df.index + 1
        annotations_df = annotations_df.sort_index()
    
    
    annotation_layer = (
        alt.Chart(annotations_df)
        .mark_text(size=20, dx=-10, dy=0, align="left")
        .encode(
            x=alt.X("index:N", title="", axis=alt.Axis(labelExpr=f"{stations}[datum.value]")), 
            y=alt.Y("value:Q", title=""), 
            text="marker", 
            color=alt.Color("value:Q", title="",legend=None).scale(domain=domainT, range=rangeT_), 
            tooltip="description")
    )

    
    if zones.shape[0] > 0:
        combined_chart = chart + annotation_layer
    else :
        combined_chart = annotation_layer
    st.altair_chart(combined_chart, use_container_width=True)

def niveauAlerte():
    
    with st.spinner('Chargement'):
        expander = st.expander(":warning: Niveau Alerte")
        with expander:
            stations = dict()
            #stations[4] = "Majornas"
            #stations[3] = "Montagnat"
            #stations[1] = "Saone à Macon"
            #stations[2] = "Saint Julien sur R."
            stations[11] = "Viriat"
            stations[5] = "Baudières"
            stations[54] = "Cras"

            nb_days = 3
            today = datetime.now(timezone.utc)
            two_days_ago = today - timedelta(days=nb_days)
            
            #timestamp in milliseconds
            ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
            ts_end = int(round(today.timestamp()*1000.0))

            type_values = ['m', "°C" , "V" , "m3/s", "mm/h"]
            unit_symbol = 'm'

            cols = st.columns((len(stations)))
            idx = 0
            for station_id in stations:
                with cols[idx]:
                    printGraphNiveau(station_id, stations, ts_start, ts_end, unit_symbol)
                    idx += 1

            
            

def dashboard():
    
    #st.session_state.hubeau_checkbox_value = st.sidebar.checkbox("Afficher les données hubeau", value=st.session_state.hubeau_checkbox_value)

    # # get all hydrological stations
    # url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/dataTypes"
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
        stations[54] = "Cras"
        
        nb_days = 3
        today = datetime.now(timezone.utc)
        two_days_ago = today - timedelta(days=nb_days)
        
        #timestamp in milliseconds
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
        ts_end = int(round(today.timestamp()*1000.0))

        type_values = ['mm/h','m','m3/s','°C', 'V']
        expanders = []
        spinners = []
        placeholders = []

        #create expanders first
        for idx, type_value in enumerate(type_values):
            
            #st.dataframe(samples)
            if type_value == "m":
                #st.subheader("Hauteur d'eau")
                m_title = ":straight_ruler: Hauteur d'eau"
                m_loading_title = "Chargement Hauteur d'eau..."
            elif type_value == "mm/h":
                #st.subheader(":new: Vitesse de montée des eaux (moy 3h)")
                m_title = ":new: Vitesse de montée des eaux (moy 3h)"
                m_loading_title = "Chargement Vitesse de montée des eaux..."
            elif type_value == "°C":
                #st.subheader("Température")
                m_title = ":thermometer: Température"
                m_loading_title = "Chargement Température..."
            elif type_value == "V":
                #st.subheader("Batterie")
                m_title = ":battery: Batterie"
                m_loading_title = "Chargement Batterie..."
            elif type_value == "m3/s":
                #st.subheader("Débit")
                m_title = ":chart_with_upwards_trend: Débit"
                m_loading_title = "Chargement Débit..."
            
            
            expander = st.expander(m_title)
            #add placeholder
            with expander:
                placeholder = st.empty()
                placeholder.text(m_loading_title)    
                placeholders.append(placeholder)

        
        #loop over type_values
        for idx, type_value in enumerate(type_values):
            
            m_placeholder = placeholders[idx]
            m_placeholder.empty()
            with m_placeholder.container():
                spinner = st.spinner("Chargement des données en cours...")
                with spinner:
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
st.text('MAJ : {}'.format(datetime.now().strftime('%d/%m/%Y @ %H:%M')))
add_logo('static/images/small-logo-carre-quadri-SBVR.jpg')
previs()
niveauAlerte()
dashboard()

# update page every 10 mins
st_autorefresh(interval=10 * 60 * 1000, key="dashboardrefresh")

