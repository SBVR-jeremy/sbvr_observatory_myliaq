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
import pytz
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
        today = datetime.datetime.now(datetime.timezone.utc)
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
    elif unit_symbol == "mm/h":
        dataType = 4

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
            return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification','pointInitial','station_id', 'unknown'])
        samples.columns =['timestamp', 'numeric_value', 'status', 'qualification','pointInitial','station_id', 'unknown']
        samples['timestamp'] = pd.to_datetime(samples['timestamp'], unit='ms', utc=True).map(lambda x: x.astimezone(pytz.timezone('Europe/Paris')).replace(tzinfo=pytz.UTC))
        #Perform post computations
        if unit_symbol == "mm/h":
            #print('0 ---------------')
            #print(samples['numeric_value'])
            computed_samples= samples.set_index(pd.DatetimeIndex(samples['timestamp'])).resample("60min").mean(numeric_only=True) #resample per hour
            #print('1 ---------------')
            #print(computed_samples)
            computed_samples = computed_samples.diff(periods=1) #difference with following row
            #print('2 ---------------')
            #print(computed_samples)
            computed_samples['numeric_value'] = computed_samples['numeric_value'] * 1000.0 #convert to mm
            #print('3 ---------------')
            #print(computed_samples)
            computed_samples = computed_samples.rolling(3).mean() #mean over 3h for a better visualization
            #print('4 ---------------')
            #print(computed_samples)
            computed_samples['numeric_value'] = round(computed_samples['numeric_value'],1) #round values

            computed_samples['timestamp'] = pd.to_datetime(computed_samples.index, unit='ms', utc=True)
            #print(computed_samples)
            return computed_samples
        

        return samples
    else:
        return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification','pointInitial','station_id', 'unknown'])

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
    elif unit_symbol == "mm/h": #Define empirical thresolds
        seuils = pd.DataFrame(data={'id':[1], 'code':[ 'dangerous_rising_level'],'name':['Niveau de montée anormal'],'value':[100],'color':['red'],'isOverrunThreshold':[True],'dataType':[0],'htmlColor':['#FF8800']})
            
        #columns = ['id','code','name','value','color','isOverrunThreshold','dataType','htmlColor'])

        return seuils

    else:
        dataType = 0

    if seuils.shape[0] == 0:
        return pd.DataFrame(columns = ['id','code','name','value','color','isOverrunThreshold','dataType','htmlColor'])
        
    if unit_symbol == '':
        return seuils
    else:
        #print(seuils)
        seuils_filtered = seuils.query('dataType == @dataType')
        #print(seuils_filtered)
    return seuils_filtered