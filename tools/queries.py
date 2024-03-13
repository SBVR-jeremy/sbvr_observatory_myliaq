#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""utility.py: This file contains functions to performs SQL queries on database"""

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
import pandas as pd
import numpy as np
import datetime
import re
import json
import requests

import traceback

from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from sqlalchemy import create_engine
# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------


#@st.cache_data(ttl=3600)
def m_getAllSamplesAnalyse(station_id, unit_symbol,unit_fk=None, start_date=None, end_date=None):
    
    #timestamp in milliseconds
    if start_date is None:
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    else:
        ts_start = start_date
    
    if end_date is None : 
        ts_end = int(round(today.timestamp()*1000.0))
    else:
        ts_end = end_date

    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/chronic/measures"
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+st.secrets["myliaq"]["api_key"]
    }

    #print(headers)

    #station_id = 4
    #station_name = "MAJORNAS"
     #4 hauteur - 7 - Temperature
    if unit_symbol == "m":
        dataType = 4
    elif unit_symbol == "°C":
        dataType = 7
    elif unit_symbol == "V":
        dataType = 8
    elif unit_symbol == "m3/s":
        dataType = 5

    parameters = {
        "stationId" :  station_id,
        "chartMode" :  True,
        "dataType" :   dataType ,
        "startDate" : ts_start, 
        "endDate" : ts_end,
        "grpFunc" : "" # Vide - Toutes / MAX - max journalier / AVERAGE - Moyenne journalieres / MIN - min journaliers
    }
    data_json =  json.dumps(parameters)
    #print(data_json)
    response = requests.post(url, headers=headers , data=data_json)
    #print("Status Code", response.status_code)
    if response.status_code == 200:
        #print("JSON Response ", response.json())
        samples = pd.read_json(response.text)
        #print(samples.shape[0])
        if samples.shape[0] == 0:
            return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification','pointInitial','station_id'])
        samples.columns =['timestamp', 'numeric_value', 'status', 'qualification','pointInitial','station_id']
        samples['timestamp'] = pd.to_datetime(samples['timestamp'], unit='ms', utc=True)
        return samples
    else:
        return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification','pointInitial','station_id'])

#@st.cache_data(ttl=3600)
def m_getAllSeuils(station_id, unit_symbol=''):
    
    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/{}/threshold".format(station_id)
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+st.secrets["myliaq"]["api_key"]
    }

    response = requests.get(url, headers=headers )
    #print("Status Code", response.status_code)
    #print("JSON Response ", response.json())

    seuils = pd.read_json(response.text)

    if unit_symbol == "m":
        dataType = 4
    elif unit_symbol == "°C":
        dataType = 7
    elif unit_symbol == "V":
        dataType = 8
    elif unit_symbol == "m3/s":
        dataType = 5

    if seuils.shape[0] == 0:
        return pd.DataFrame(columns = ['id','code','name','value','color','isOverrunThreshold','dataType','htmlColor'])
        
    if unit_symbol == '':
        return seuils
    else:
        #print(seuils)
        seuils_filtered = seuils.query('dataType == @dataType')
        #print(seuils_filtered)
    return seuils_filtered