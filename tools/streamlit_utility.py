#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""streamlit_utility.py: This file contains functions shared over the streamlit application"""

__author__ = "Jeremy Bluteau"
__copyright__ = "Copyright 2025, SBVR Observatory"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Jeremy Bluteau"
__email__ = "jeremy.bluteau@syndicat-reyssouze.fr"
__status__ = "Dev"


# ---------------------------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------------------------
import streamlit as st
import streamlit.components.v1 as components
import requests
import numpy as np
import json
import datetime
import traceback
import toml


from tools.queries import *
from tools.graphtools import *

# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------

def hide_rainbow_bar():
    hide_decoration_bar_style = '''
    <style>
        header {visibility: hidden;}
        .css-z5fcl4 {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        [data-testid="stSidebarNav"] {
            padding-top: 200px !important;
        }
        
    </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

def hide_streamlit_credits():
    hide_default_format = """
       <style>
       #MainMenu {visibility: hidden; }
       footer {visibility: hidden;}
       </style>
       """
    st.markdown(hide_default_format, unsafe_allow_html=True)


DEFAULT = ' --- '
def selectbox_with_default(text, values, default=DEFAULT, sidebar=False, index=0):
    func = st.sidebar.selectbox if sidebar else st.selectbox
    return func(text, np.insert(np.array(values, object), index, default))

def protect_by_password():
    if 'password' not in st.session_state:
        st.session_state.password = None

    if 'is_logged' not in st.session_state:
        st.session_state.is_logged = False


    password = st.text_input("Entrer le mot de passe de sécurité:", type="password")

    if not authenticate_password(password):
        st.error("Mot de passe incorrect. Accès refusé.")
        st.stop()


def authenticate_password(password):
    #Load secret file
    try:
        secrets = toml.load("./.streamlit/secrets.toml")
        ADMIN_PASSWORD = secrets["observatory"]["admin_password"]
    except Exception as e:
        print("Loading secret file failed : 3_API.py l:49")
        print(e)
        st.stop()

    st.session_state.password = password

    if st.session_state.password != ADMIN_PASSWORD:
        return False
    
    st.session_state.is_logged = True
    return True

def previs(expanded=False):
    with st.spinner('Chargement'):
        expander = st.expander(":sunny: Prévi METEO",expanded=expanded)
        with expander:
            [col1,col2,col3] = st.columns(3)
            #meteoblue Bourg en bresse
            with col1:
                components.iframe(
                    "https://www.meteoblue.com/fr/weather/widget/daily/bourg-en-bresse_france_3031009?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                    , height=420, width=300)
            
            #meteoblue montrevel
            with col2:
                components.iframe(
                    "https://www.meteoblue.com/fr/weather/widget/daily/montrevel-en-bresse_france_2992050?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                    , height=420, width=300)
            
            #meteoblue Pont de vaux
            with col3:
                components.iframe(
                "https://www.meteoblue.com/fr/weather/widget/daily/pont-de-vaux_france_2986227?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light"
                , height=420, width=300)

def showAlerteGraphs(expanded=False):
    expander = st.expander(":warning: Niveau Alerte", expanded=expanded)
    with expander:
        with st.spinner('Chargement'):
            stations = dict()
            #stations[4] = "Majornas"
            #stations[3] = "Montagnat"
            #stations[1] = "Saone à Macon"
            #stations[2] = "Saint Julien sur R."
            stations[11] = "Viriat"
            stations[5] = "Baudières"
            stations[54] = "Cras"
            stations[58] = "Pont de Vaux"
            cols = st.columns((len(stations)))
            idx = 0
            for station_id in stations:
                with cols[idx]:
                    data = requests.get("http://127.0.0.1:1111/api/graphAlerte?station_id="+str(station_id)).json()
                    #display json
                    #st.write(data)
                    st.vega_lite_chart(data, use_container_width=True)
                    idx += 1

def showSituationMap():
    expander = st.expander(":eye: Observations ONDE", True)
    with expander:
        with st.spinner('Chargement...'):
    
            #data = requests.get("http://127.0.0.1:1111/api/mapSituation").json()
            #st.vega_lite_chart(data, use_container_width=True)

            url = "http://127.0.0.1:1111/api/mapSituation"
            data = requests.get(url)
            st.image(data.content)

# type_value = {id: 1, label: "Pluie", displayData: true, unit: "mm", order: 1}  (JSON)
def showNiveauxGraphs(type_value, m_title, m_loading_title, expanded=False):
    expander = st.expander(m_title, expanded=expanded)
    with expander:
        with st.spinner(m_loading_title):
            stations = dict()
            stations[4] = "Majornas"
            stations[3] = "Montagnat"
            stations[1] = "Saone à Macon"
            stations[2] = "Saint Julien sur R."
            stations[11] = "Viriat"
            stations[5] = "Baudières"
            stations[54] = "Cras"
            stations[58] = "Pont de Vaux"
            #cols = st.columns((len(stations)%4))
            idx = 0
            nbcols = 4 if len(stations)>=4 else len(stations)

            for station_id in stations:
                if (idx % 4 == 0):
                    cols = st.columns(nbcols)

                with cols[idx %4 ]:
                    stationsFull = getStations()
                    my_station = m_extractStation(stationsFull,station_id)
                    station_name = my_station['name'] if my_station is not None else "Station not Found"

                    st.container(border=False, height=150).markdown(f'<a href="https://reyssouze.myliaq.fr/#/station/hydrometry/{station_id}/dashboard" target="_blank"><h4>:green[{station_name}]</h4></a>', unsafe_allow_html=True)


                    #display update informations
                    try:
                        url = "http://127.0.0.1:1111/api/graphUpdate?station_id="+str(station_id)+"&type_value_id="+str(type_value["id"])+"&show_title=false"
                        #print(url)
                        data = requests.get(url).json()
                        #display json
                        #st.write(data)
                    
                        st.container( border=False, height=100).vega_lite_chart(data=data, use_container_width=True)
                    except Exception as e:
                        print(traceback.format_exc())
                        st.text("No graph Update")

                    #display informations
                    try:
                        url = "http://127.0.0.1:1111/api/graphChronique?station_id="+str(station_id)+"&type_value_id="+str(type_value["id"])+"&show_title=false"
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
                    
# type_value = {id: 1, label: "Pluie", displayData: true, unit: "mm", order: 1}  (JSON)
def showPluvioGraphs(type_value, m_title, m_loading_title, expanded=False):
    expander = st.expander(m_title, expanded=expanded)
    with expander:
        with st.spinner(m_loading_title):
            stations = dict()
            stations[21] = "Ceyzeriat SAPC"
            stations[1] = "ERA5 Bourg-en-Bresse_1"
            stations[143] = "SAFRAN_8280_21370 - SAFRAN Bourg-en-Bresse_1 [ceyzeriat]"
            stations[145] = "SAFRAN_8200_21450 - SAFRAN Viriat_1 [Bresse Vallons]"
            cols = st.columns((len(stations)))
            idx = 0
            for station_id in stations:
                with cols[idx]:
                    stationsFull = getStationsPluvio()
                    my_station = m_extractStation(stationsFull,station_id)
                    station_name = my_station['name'] if my_station is not None else "Station not Found"

                    st.container(border=False, height=150).markdown(f'<a href="https://reyssouze.myliaq.fr/#/station/pluviometry/{station_id}/dashboard" target="_blank"><h4>:green[{station_name}]</h4></a>', unsafe_allow_html=True)

                    # try:        
                    #     data = requests.get("http://127.0.0.1:1111/api/graphUpdatePluvio?station_id="+str(station_id)+"&unit_symbol="+type_value+"&show_title=false").json()
                    #     #display json
                    #     #st.write(data)
                    
                    #     st.container( border=False, height=100).vega_lite_chart(data=data, use_container_width=True)
                    # except Exception as e:
                    #     print(traceback.format_exc())
                    #     st.text("No graph Update")

                    try:
                        url = "http://127.0.0.1:1111/api/graphChroniquePluvio?station_id="+str(station_id)+"&type_value_id="+str(type_value["id"])+"&show_title=true"
                        print (url)
                        data = requests.get(url).json()
                        #display json
                        #st.write(data)
                    
                        #st.container( border=False, height=250)
                        st.vega_lite_chart(data, use_container_width=True)
                    except Exception as e:
                        print(traceback.format_exc())
                        st.text("No graph Chronique Pluvio")
                        raise e

                    idx += 1

# type_value = {id: 1, label: "Pluie", displayData: true, unit: "mm", order: 1}  (JSON)
def showCumulatedGraphs(type_value, m_title, m_loading_title, expanded=False):
    expander = st.expander(m_title, expanded=expanded)
    with expander:
        with st.spinner(m_loading_title):

            #type_value = 'm3/s'
            nb_days = 30
            date_start = datetime.datetime.now(timezone.utc) - timedelta(days=nb_days)
            date_end = datetime.datetime.now(timezone.utc)
 
            stations = dict()
            stations[4] = {"title": "Majornas", "color" : '#003A7D'}
            stations[3] = {"title": "Montagnat", "color" : '#008DFF'}
            #stations[1] = {"title": "Saone à Macon", "color" : "#F7A1CB"}
            stations[2] = {"title": "Saint Julien sur R.", "color" : "#FF00FF"}
            stations[11] = {"title": "Viriat", "color" : '#4ECB8D'}
            stations[5] = {"title": "Baudières", "color" : '#FF9D3A'}
            stations[54] = {"title": "Cras", "color" : '#F9E858'}
            stations[58] = {"title" : "Pont de Vaux", "color" : "#00EEFF"}

            try:        
                payload = {
                    "stations": stations,
                    "type_value_id": type_value['id'],
                    "show_title" : True,
                    "draw_seuils" : False,
                    "date_start" : date_start.strftime('%Y-%m-%d'),
                    "date_end" : date_end.strftime('%Y-%m-%d'),
                    "output" : "png"
                }
                #print (payload)
                url = "http://127.0.0.1:1111/api/graphCumulatedChronique"
                data = requests.post(url, json=json.dumps(payload))
                #print("Response 3_API")
                st.image(data.content)
                
                #data = data.json()
                #display json
                #st.write(data)
            
                #st.container( border=False).vega_lite_chart(data=data, use_container_width=True)
            except Exception as e:
                print(traceback.format_exc())
                st.text("No graph Update")
                raise e

# type_value = {id: 1, label: "Pluie", displayData: true, unit: "mm", order: 1}  (JSON)
def showMeteorologicalAnalysis(m_title, m_loading_title, expanded=False):
    expander = st.expander(m_title, expanded=expanded)
    with expander:
        with st.spinner(m_loading_title):
            import calendar
            #this_year = datetime.date.today().year
            this_month = datetime.date.today().month
            #report_year = st.selectbox('Select yeay', range(this_year, this_year - 5, -1))
            month_abbr = calendar.month_abbr[1:]
            report_month_str = st.radio('Select month', month_abbr, index=this_month - 1, horizontal=True)
            report_month = month_abbr.index(report_month_str) + 1
            st.text(f'{report_month_str}')
            if report_month:
            
                stations = dict()
                stations[21] = "Ceyzeriat SAPC"
                stations[143] = "SAFRAN_8280_21370 - SAFRAN Bourg-en-Bresse_1 [ceyzeriat]"
                stations[1] = "ERA5 Bourg-en-Bresse_1"
                #cols = st.columns((len(stations)))
                idx = 0
                for station_id in stations:
                    #with cols[idx]:
                    stationsFull = getStationsPluvio()
                    my_station = m_extractStation(stationsFull,station_id)
                    station_name = my_station['name'] if my_station is not None else "Station not Found"

                    st.container(border=False, height=150).markdown(f'<a href="https://reyssouze.myliaq.fr/#/station/pluviometry/{station_id}/dashboard" target="_blank"><h4>:green[{station_name}]</h4></a>', unsafe_allow_html=True)

                    # try:        
                    #     data = requests.get("http://127.0.0.1:1111/api/graphUpdatePluvio?station_id="+str(station_id)+"&unit_symbol="+type_value+"&show_title=false").json()
                    #     #display json
                    #     #st.write(data)
                    
                    #     st.container( border=False, height=100).vega_lite_chart(data=data, use_container_width=True)
                    # except Exception as e:
                    #     print(traceback.format_exc())
                    #     st.text("No graph Update")
                    
                    try:
                        nb_days = 30
                        month=report_month
                        date_end = datetime.datetime(2025,month+1,1,0,0,0)- timedelta(days=1)
                        date_start = datetime.datetime(2025,month,1,0,0,0) 
            
                        url = "http://127.0.0.1:1111/api/graphAnalyseMeteo?station_id="+str(station_id)+"&date_start="+date_start.strftime("%Y-%m-%d")+"&date_end="+date_end.strftime("%Y-%m-%d")+"&show_title=true" #&date=...
                        print (url)
                        data = requests.get(url).json()
                        #display json
                        #st.write(data)
                    
                        #st.container( border=False, height=250)
                        st.vega_lite_chart(data, use_container_width=True)
                    except Exception as e:
                        print(traceback.format_exc())
                        st.text("No graph Analyse meteo")
                        raise e

                    idx += 1

# type_value = {id: 1, label: "Pluie", displayData: true, unit: "mm", order: 1}  (JSON)
def showMeteorologicalAnnualAnalysis(m_title, m_loading_title, expanded=False):
    expander = st.expander(m_title, expanded=expanded)
    with expander:
        with st.spinner(m_loading_title):
            this_year = datetime.date.today().year
            #this_month = datetime.date.today().month
            report_year = st.selectbox('Select yeay', range(this_year, this_year - 5, -1))
            #month_abbr = calendar.month_abbr[1:]
            #report_month_str = st.radio('Select month', month_abbr, index=this_month - 1, horizontal=True)
            #report_month = month_abbr.index(report_month_str) + 1
            st.text(f'Rapport de l\'année {report_year}')
            if report_year:
            
                stations = dict()
                stations[21] = "Ceyzeriat SAPC"
                #stations[143] = "SAFRAN_8280_21370 - SAFRAN Bourg-en-Bresse_1 [ceyzeriat]"
                #stations[1] = "ERA5 Bourg-en-Bresse_1"
                #cols = st.columns((len(stations)))
                idx = 0
                for station_id in stations:
                    #with cols[idx]:
                    stationsFull = getStationsPluvio()
                    my_station = m_extractStation(stationsFull,station_id)
                    station_name = my_station['name'] if my_station is not None else "Station not Found"

                    st.container(border=False, height=150).markdown(f'<a href="https://reyssouze.myliaq.fr/#/station/pluviometry/{station_id}/dashboard" target="_blank"><h4>:green[{station_name}]</h4></a>', unsafe_allow_html=True)

                    # try:        
                    #     data = requests.get("http://127.0.0.1:1111/api/graphUpdatePluvio?station_id="+str(station_id)+"&unit_symbol="+type_value+"&show_title=false").json()
                    #     #display json
                    #     #st.write(data)
                    
                    #     st.container( border=False, height=100).vega_lite_chart(data=data, use_container_width=True)
                    # except Exception as e:
                    #     print(traceback.format_exc())
                    #     st.text("No graph Update")
                    
                    try:
                        nb_days = 30
                        #month=report_year
                        #date_end = datetime.datetime(2025,month+1,1,0,0,0)- timedelta(days=1)
                        #"date_start = datetime.datetime(2025,month,1,0,0,0) 
            
                        url = "http://127.0.0.1:1111/api/graphAnalyseAnnuelleMeteo?station_id="+str(station_id)+"&year="+str(report_year)+"&show_title=true" #&date=...
                        print (url)
                        data = requests.get(url).json()
                        #display json
                        #st.write(data)
                    
                        #st.container( border=False, height=250)
                        st.vega_lite_chart(data, use_container_width=True)
                    except Exception as e:
                        print(traceback.format_exc())
                        st.text("No graph Analyse meteo")
                        raise e

                    idx += 1