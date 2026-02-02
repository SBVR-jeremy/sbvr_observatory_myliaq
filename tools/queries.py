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
import pandas as pd
import numpy as np
import datetime
import pytz
import re
import io
import json
import requests
import requests_cache

import traceback

from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation

from sqlalchemy import create_engine
import toml

from bs4 import BeautifulSoup

#Load secret file
try:
    secrets = toml.load("./.streamlit/secrets.toml")
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+secrets["myliaq"]["api_key"]
    }
except Exception as e:
    print("Loading secret file failed : queries.py l:35")
    print(e)
    headers = {}



#patch request cache
#requests_cache.install_cache('api_cache')

# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------

#factorize get request to myliaq
def m_getJSONFromMyliaqAPI(url):
    response = requests.get(url, headers=headers )
    #print("Status Code", response.status_code)
    #print("JSON Response ", response.json())

    #stations = pd.read_json(io.StringIO(response.text)))
    #print(stations)
    #print(response.json())
    
    return response.json()

def m_getAllSamplesAnalyse(station_id, type_value_id, start_date=None, end_date=None, grpFunc="",chartMode=True):
    
    #timestamp in milliseconds
    if start_date is None:
        ts_start = int(round(datetime.datetime.now().timestamp()*1000.0)) 
    else :
        if start_date != -1:
            ts_start = start_date
        else:
            ts_start = None

    if end_date is None : 
        today = datetime.datetime.now()
        ts_end = int(round(today.timestamp()*1000.0))
    else:
        if end_date == -1:
            ts_end = None
        else :
            ts_end = end_date
    
    # print(ts_start)
    # print(ts_end)
    # print(pd.to_datetime(ts_start/1000.0, unit='s'))
    # print(pd.to_datetime(ts_end/1000.0, unit='s'))

    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/chronic/measures"
    print(url)

    #CARREFUL startDate and endDate HAVE TO BE UTC ! we need to perform conversion before !!!!
    parameters = {
            "stationId" :  station_id,
            "dataType" :   type_value_id ,
            "groupFunc" : grpFunc, # Vide - Toutes / SUM_HOUR - somme horaire /  Toutes / MAX - max journalier / AVERAGE - Moyenne journalieres / MIN - min journaliers
            "chartMode" :  chartMode,
            "startDate" : ts_start, 
            "endDate" : ts_end,
            "distinctByCodePoint": True
    }
    data_json =  json.dumps(parameters)
    #print(data_json)
    response = requests.post(url, headers=headers , data=data_json)


    #print("Status Code", response.status_code)
    if response.status_code == 200:
         #print("JSON Response ", response.json())
        samples = pd.read_json(io.StringIO(response.text))
        #print(samples.shape[0]) #[1755079200000, 0, 1, 2, 4]
        #print(samples.shape[1])

        if chartMode == False:
            samples.columns = ['station_id', 'data_type', 'timestamp', 'min_numeric_value?', 'numeric_value'] +  [str(i) for i in range(5,samples.shape[1])]

        if samples.shape[0] == 0:
            return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification', 'initialPoint','unknown', 'station_id'])
        
        if samples.shape[1] == 7:
            samples.columns =['timestamp', 'numeric_value', 'status', 'qualification', 'initialPoint','unknown', 'station_id']
        elif samples.shape[1] == 5:
            samples.columns =['timestamp', 'numeric_value', 'status', 'qualification', 'initialPoint']
        elif samples.shape[1] == 4:
            samples.columns =['timestamp', 'numeric_value', 'status', 'qualification']
        elif samples.shape[1] == 3:
            samples.columns =['timestamp', 'numeric_value', 'status']

        samples['timestamp'] = pd.to_datetime(samples['timestamp'], unit='ms', utc=True).map(lambda x: x.astimezone(pytz.timezone('Europe/Paris')).replace(tzinfo=pytz.UTC))


        #EXAMPLE IF WE NEED TO PERFORM POST COMPUTATIONS HERE...
        ##Perform post computations
        # if perform_custom_computation:
        #     #print('0 ---------------')
        #     #print(samples['numeric_value'])
        #     computed_samples= samples.set_index(pd.DatetimeIndex(samples['timestamp'])).resample("60min").mean(numeric_only=True) #resample per hour
        #     #print('1 ---------------')
        #     #print(computed_samples)
        #     computed_samples = computed_samples.diff(periods=1) #difference with following row
        #     #print('2 ---------------')
        #     #print(computed_samples)
        #     computed_samples['numeric_value'] = computed_samples['numeric_value'] * 1000.0 #convert to mm
        #     #print('3 ---------------')
        #     #print(computed_samples)
        #     computed_samples = computed_samples.rolling(3).mean() #mean over 3h for a better visualization
        #     #print('4 ---------------')
        #     #print(computed_samples)
        #     computed_samples['numeric_value'] = round(computed_samples['numeric_value'],1) #round values

        #     computed_samples['timestamp'] = pd.to_datetime(computed_samples.index, unit='ms', utc=True)
        #     #print(computed_samples)
        #     return computed_samples

        return samples
    else:
        return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification'])

def m_getAllPluvioMeasures(station_id, type_value_id, start_date=None, end_date=None, grpFunc="SUM_DAY",chartMode=True):
    try:
        #url https://reyssouze.myliaq.fr/api/pluviometer/chartMeasures
        #{"stationId":21,"dataType":1,"groupFunc":"SUM_DAY","chartMode":true,"startDate":1755071088577,"distinctByCodePoint":true}
        #timestamp in milliseconds
        if start_date is None:
            ts_start = int(round(datetime.datetime.now().timestamp()*1000.0)) 
        else :
            if start_date != -1:
                ts_start = start_date
            else:
                ts_start = None

        if end_date is None : 
            today = datetime.datetime.now()
            ts_end = int(round(today.timestamp()*1000.0))
        else:
            if end_date == -1:
                ts_end = None
            else :
                ts_end = end_date

        url = "https://reyssouze.myliaq.fr/api/pluviometer/chartMeasures"
        print(url)
        #hack for pluie efficace théorique
        if type_value_id == 2 : 
            type_value_id = -1

        #hack for grpFunc if temp, 
        if type_value_id == 4 and grpFunc == "SUM_DAY":
            grpFunc="AVERAGE"

        parameters = {
            "stationId" :  station_id,
            "dataType" :   type_value_id ,
            "groupFunc" : grpFunc, # Vide - SUM_HOUR - somme horaire /  Toutes / MAX - max journalier / AVERAGE - Moyenne journalieres / MIN - min journaliers
            "chartMode" :  chartMode,
            "startDate" : ts_start, 
            "endDate" : ts_end,
            "distinctByCodePoint": True
        }
        
        data_json =  json.dumps(parameters)
        #print(data_json)
        response = requests.post(url, headers=headers , data=data_json)

        #print("Status Code", response.status_code)
        if response.status_code == 200:
            #print("JSON Response ", response.json())
            samples = pd.read_json(io.StringIO(response.text))
            #print(samples.shape[0]) #[1755079200000, 0, 1, 2, 4]
            #print(samples.shape[1])

            if chartMode == False:
                samples.columns = ['station_id', 'data_type', 'timestamp', 'min_numeric_value?', 'numeric_value'] +  [str(i) for i in range(5,samples.shape[1])]

            if samples.shape[0] == 0:
                return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification'])
            
            if samples.shape[1] == 5:
                samples.columns =['timestamp', 'numeric_value', 'status', 'qualification', 'initialPoint']
            elif samples.shape[1] == 4:
                samples.columns =['timestamp', 'numeric_value', 'status', 'qualification']
            elif samples.shape[1] == 3:
                samples.columns =['timestamp', 'numeric_value', 'status']

            samples['timestamp'] = pd.to_datetime(samples['timestamp'], unit='ms', utc=True).map(lambda x: x.astimezone(pytz.timezone('Europe/Paris')).replace(tzinfo=pytz.UTC))
            
            return samples
        else:
            return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification'])
    except Exception as e:
        print(traceback.format_exc())
        raise e

def m_getAllSeuils(station_id, type_value_id=None):
    
    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/{}/threshold".format(station_id)
    #print(url)
    response = requests.get(url, headers=headers )
    #print("Status Code", response.status_code)
    #print("JSON Response ", response.json())

    seuils = pd.read_json(io.StringIO(response.text))
    #print(seuils)
    
    if seuils.shape[0] == 0:
        return pd.DataFrame(columns = ['id','code','name','value','color','isOverrunThreshold','dataType','htmlColor'])

    if type_value_id is not None:
        print("filter dataType={}".format(type_value_id))
        seuils.query("dataType=={}".format(type_value_id), inplace=True)

    return seuils
    
def m_getAllZones(zones, station_id, type_value_id=None):

    #zones = pd.DataFrame(columns=["station","seuil","isOverrunThreshold", "min", "max", "value","color"])
    
    seuils = m_getAllSeuils(station_id,type_value_id)
    #oder seuils by value
    seuils = seuils.sort_values("value", ascending=True)
    #print (seuils)
    if seuils.shape[0] > 0:
        sum_seuils = []
        sum_v = 0
        prev_overrun = 0
        prev_seuilname = ""
        prev_color = ""
        for index, seuil in seuils.iterrows():
            try:
                if str(seuil['htmlColor']) == 'nan': 
                    m_color = 'black'
                else:
                    m_color = str(seuil['htmlColor'])
            except : 
                m_color = 'black'

            if(seuil.isOverrunThreshold == 0):
                #zones.loc[stations[station_id],str(str(index)+seuil["name"]+"_min")] = sum_v
                zones.loc[-1] = {"station": station_id, "seuil": seuil["name"] , "isOverrunThreshold" : seuil.isOverrunThreshold, "min" : sum_v, "max": seuil.value, "value":(seuil.value - sum_v), "color": m_color}
                zones.index = zones.index + 1
                zones = zones.sort_index()
                prev_overrun = seuil.isOverrunThreshold
            else:
                #handle normal zone
                if (seuil.isOverrunThreshold != prev_overrun):
                    #zones.loc[stations[station_id], str(index)+"Normale_min"] = sum_v
                    zones.loc[-1] = {"station" : station_id, "seuil" : "Normale", "isOverrunThreshold" : 0, "min": sum_v, "max": seuil.value , "value":(seuil.value - sum_v), "color": "#0000ff"}
                    zones.index = zones.index + 1
                    zones = zones.sort_index()
                    sum_v = seuil.value
                    prev_seuilname=seuil["name"]
                    try:
                        prev_color = seuil.htmlColor
                    except : 
                        prev_color = 'black'
                    prev_overrun = seuil.isOverrunThreshold
                else:
                    #zones.loc[stations[station_id],str(str(index)+prev_seuilname+"_min")] = sum_v
                    zones.loc[-1] = {"station" : station_id, "seuil" : prev_seuilname, "isOverrunThreshold" : seuil.isOverrunThreshold, "min": sum_v, "max": seuil.value , "value":(seuil.value - sum_v), "color":prev_color}
                    zones.index = zones.index + 1
                    zones = zones.sort_index()
                    prev_seuilname=seuil["name"]
                    try:
                        prev_color = seuil.htmlColor
                    except : 
                        prev_color = 'black'
                
            sum_v = seuil.value
        
        #Add last entrie
        #zones.loc[stations[station_id],str(str(index+1)+prev_seuilname+"_min")] = sum_v
        zones.loc[-1] ={"station" : station_id, "seuil" : prev_seuilname, "isOverrunThreshold" : seuil.isOverrunThreshold, "min": sum_v , "max": (sum_v+0.2) ,"value":0.2, "color":prev_color} 
        zones.index = zones.index + 1
        zones = zones.sort_index()

    return zones

def m_getStation(station_id):
    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/{}".format(station_id)
    return m_getJSONFromMyliaqAPI(url)

# API call to get hydrologicalStations from myliaq
# stations = getStations()
# returns JSON response 
#[{'id': 30, 'code': '06001598', 'name': "Bief de l'Enfer à St-Etienne-sur-Reyssouze [TH_BEN_101]", 'stationType': 1, 'creationDate': 1686866400000, 'x': 854408, 'y': 6592497, 'projection': 26, 'altitude': 177, 'comment': "Limnimètre cours d'eau\n+ sonde thermie (03/10/2023)", 'townCode': '01352', 'updateLogin': 'jeremy.bluteau', 'updateDate': 1738053878319},  ...

def getStations():
    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/"
    return m_getJSONFromMyliaqAPI(url)


def m_getStationPluvio(station_id):
    url = "https://reyssouze.myliaq.fr/api/pluviometer/{}".format(station_id)
    return m_getJSONFromMyliaqAPI(url)


def getStationsPluvio():
    url = "https://reyssouze.myliaq.fr/api/pluviometer/"
    return m_getJSONFromMyliaqAPI(url)

def getDataTypePluvio():
    url = "https://reyssouze.myliaq.fr/api/pluviometer/dataTypes"
    return m_getJSONFromMyliaqAPI(url)

def getDataTypeHydro():
    url = "https://reyssouze.myliaq.fr/api/hydrologicalStation/dataTypes"
    return m_getJSONFromMyliaqAPI(url)

# Utility function that extract the station object from stations [given by getStations() ] with id=station_id
# station_4 = m_extractStation(stations,4)
# returns JSON object or None if not found
# {'id': 4, 'code': 'U401402001', 'name': 'La Reyssouze à Bourg-en-Bresse [Majornas]', ...
def m_extractStation(stations, station_id):
    try:
        return list(filter(lambda x: x['id'] == station_id, stations))[0]
    except IndexError:
        return None

# Utility function that filter the communications object from communications [given by m_getCommunications() ] with idCategory=category_id
# returns JSON object or None if not found
# [{"id": 31, "title": "Situation des nappes - Bulletin de situation hydrologique du 1er ao\u00fbt 2025", "subtitle": "Bulletin de situation hydrologique (BSH) 11 ao\u00fbt 2025", "idCategory": 2, "comment": "
def m_extractCategory(communications, category_id):
    try:
        return list(filter(lambda x: x['idCategory'] == category_id, communications))
    except IndexError:
        return None
        
def m_getCommunications():
    
    url = "https://reyssouze.myliaq.fr/api/cms" #.format(station_id)
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+secrets["myliaq"]["api_key"]
    }

    response = requests.get(url, headers=headers )
    #print("Status Code", response.status_code)
    #print("JSON Response ", response.json())

    #stations = pd.read_json(io.StringIO(response.text))
    #print(stations)
    #print(response.json())
    
    #filter idCategory=2 #communication externes
    return m_extractCategory(response.json(),2)

#Map situation ONDES
#https://reyssouze.myliaq.fr/api/station/hydrometry/mapSituation
#get °6 (name="Situation ondes") m_situation
#get endDate
#POST https://reyssouze.myliaq.fr/api/station/hydrometry/mapSituationResults/6/[endDate] with payload m_situation
# retreive points...
# [
#     {
#         "id": 24,
#         "simulationDate": 1757362239000,
#         "code": "06001602",
#         "name": "Bief d'Augiors à St-jean-sur-Reyssouze 3 [TH_BAU_101]",
#         "city": "SAINT-JEAN-SUR-REYSSOUZE [01364]",
#         "townCode": "01364",
#         "x": 857613,
#         "y": 6593508,
#         "projection": 26,
#         "trendLabel": "Ecoulement visible acceptable",
#         "trendColor": "blue",
#         "indicatorDate": 1756979692994,
#         "thresholdName": "Ecoulement visible acceptable",
#         "comment": "Ecoulement visible acceptable",
#         "lastMeasureDate": 1756979692994,
#         "creationDate": 1757362239848
#     }, 

#     {
#         "id": 17,
#         "simulationDate": 1757362239000,
#         "code": "06580597",
#         "name": "Reyssouze à Journans [source] [TH_REY_101]",
#         "city": "JOURNANS [01197]",
def m_getMapSituation(simulation_date=None):
    
    url = "https://reyssouze.myliaq.fr/api/station/hydrometry/mapSituation"
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+secrets["myliaq"]["api_key"]
    }

    #print(url)
    response = requests.get(url, headers=headers )
    #print("Status Code", response.status_code)
    #print("JSON Response ", response.json())

    situations = response.json()
    #print(situations)
    
    #filter name="Situation ondes" #Situation ondes"
    try:

        map_situation  = list(filter(lambda x: x['name'] == "Situation ondes", situations))[0]
        #print(map_situation)
        
        #get simulationResultsDates
        if simulation_date is not None :
            month_date_ts = int(datetime.datetime.strptime(simulation_date,"%Y-%m-%d").timestamp() *1000)
        else:
            #first day of month - should display the last record is exists...
            month_date_ts = int(datetime.datetime.now().replace(day=1,hour=0,minute=0,second = 0,microsecond=0).timestamp() *1000)
        
        #print(month_date_ts)


        #myliaq return the exact date and time of simulation
        url = "https://reyssouze.myliaq.fr/api/station/hydrometry/mapSituationResultsDate/{}/{}".format(map_situation["id"],month_date_ts)
        #print(url)
        response = requests.get(url, headers=headers )
        #print("Status Code", response.status_code)
        #print("JSON Response ", response.json())

        situations_dates = pd.read_json(io.StringIO(response.text))
        try:
            situations_dates = situations_dates[0]
        except KeyError:
            print("NO SITUATIONS FOR THIS DATE...")
            return None
        
        #we need to compute the timestamp of the begining of the day instead for the calls !
        df = pd.DataFrame({'timestamp':situations_dates.values})
        #print(df)
        df["timestamp_s"] = df.apply(lambda x : int(x["timestamp"] / 1000), axis=1)
        #print(df)
        df["timestamp_2s"] = df.apply(lambda x : int(datetime.datetime.fromtimestamp(x["timestamp_s"]).replace(hour=0,minute=0,second=0,microsecond=0).timestamp()*1000),axis=1)
        #print(df)
        situations_dates = df

        #https://reyssouze.myliaq.fr/api/station/hydrometry/mapSituationResultsDate/6/1752236967692
        if simulation_date is not None :
            #filter after simulation_date
            #print("Filter SIMULATION DATE")
            month_date_ts = int(datetime.datetime.strptime(simulation_date,"%Y-%m-%d").timestamp() *1000)
            #print(month_date_ts)
            situations_dates = situations_dates[situations_dates["timestamp_2s"] >= month_date_ts ]
            #print(situations_dates)

        simulation_date = situations_dates["timestamp_2s"].iloc[0]
        #print("SIMULATION DATE")
        #print(simulation_date)
        #retreive last situation map
        url = "https://reyssouze.myliaq.fr/api/station/hydrometry/mapSituationResults/{}/{}".format(map_situation["id"],simulation_date)
        #print(url)

        #print(headers)

        data_json =  json.dumps(map_situation)
        #print(data_json)
        response = requests.post(url, headers=headers , data=data_json)
        #print("Status Code", response.status_code)
        if response.status_code == 200:
            #print("SECOND JSON Response ", response.json())
            #situations = pd.read_json(response.text)
            situations = pd.read_json(io.StringIO(response.text))
            return situations
        else:
            print("Error while retreiving map_situation") 
            return None
    except IndexError:
        return None
    

def m_getStatsChroniqueHydro(stations_id, type_value_id, start_date, end_date ):
    #timestamp in milliseconds
    if start_date is None:
        ts_start = int(round(datetime.datetime.now().timestamp()*1000.0)) 
    else :
        if start_date != -1:
            ts_start = start_date
        else:
            ts_start = None

    if end_date is None : 
        today = datetime.datetime.now()
        ts_end = int(round(today.timestamp()*1000.0))
    else:
        if end_date == -1:
            ts_end = None
        else :
            ts_end = end_date

    # print(ts_start)
    # print(ts_end)
    # print(pd.to_datetime(ts_start/1000.0, unit='s'))
    # print(pd.to_datetime(ts_end/1000.0, unit='s'))
    
    stats_array = pd.DataFrame(columns = ["station_id","min","max","mean", "sum", "nb", "nb_computed", "raw_daily_data"])

    for station_id in stations_id:
        #print(station_id)
        
        #print(type_value_id)
        #4 id temperature
        samples = m_getAllSamplesAnalyse(station_id, type_value_id, start_date=ts_start, end_date=ts_end, grpFunc="all")
        #print(samples)
        #print (samples.shape[0])
        #st.line_chart(samples, x='timestamp', y='numeric_value')
        if samples.shape[0] == 0:
            continue

        #compute values mean, min, max
        samples_day = samples.resample('1d', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ymin=pd.NamedAgg(column="numeric_value", aggfunc="min"),
            ymax=pd.NamedAgg(column="numeric_value", aggfunc="max"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        samples_day["timestamp"] = pd.to_datetime(samples_day.index) 
        samples_day["datetime"] =samples_day["timestamp"].apply(lambda x : x.strftime("%m/%d/%Y, %H:%M:%S"))

        #compute specific nb
        if type_value_id == 7:
            nb_jours_sup_30 = samples_day[samples_day["ymax"]>=30].shape[0] #Nb of day over 30°C
            nb_jours_inf_0 = samples_day[samples_day["ymin"]<=0].shape[0] #Nb of day under 0°C
            nb_jours_dce_0 = samples_day[samples_day["ymax"]<=24].shape[0] #nb of day in DCE under 24° -tres bon
            nb_jours_dce_1 = samples_day[(samples_day["ymax"]>24) & (samples_day["ymax"]<=25.5)].shape[0] #nb of day in DCE over 24° and below 25.5° - bon
            nb_jours_dce_2 = samples_day[(samples_day["ymax"]>25.5) & (samples_day["ymax"]<=27)].shape[0] #nb of day in DCE over 25.5° and below 27° - moyen
            nb_jours_dce_3 = samples_day[(samples_day["ymax"]>27) & (samples_day["ymax"]<=28)].shape[0] #nb of day in DCE over 27° and below 28° - medriocre
            nb_jours_dce_4 = samples_day[samples_day["ymax"]>28].shape[0] #nb of day in DCE over 28° - mauvais

            nb_computed = [nb_jours_sup_30, nb_jours_inf_0, nb_jours_dce_0, nb_jours_dce_1, nb_jours_dce_2, nb_jours_dce_3, nb_jours_dce_4]
        else:
            nb_computed = None

        new_data = {
             "station_id" : [station_id], 
             "min" : [samples["numeric_value"].min()], 
             "max" : [samples["numeric_value"].max()], 
             "mean" : [samples["numeric_value"].mean()], 
             "sum" : [samples["numeric_value"].sum()], 
             "nb" : [samples.shape[1]], 
             "nb_computed": [nb_computed],
             "raw_daily_data" : [samples_day]
        }
        #print(new_data)
        new_data = pd.DataFrame(new_data)

        stats_array = pd.concat([stats_array,new_data], ignore_index=True)

    #print(stats_array)
    return stats_array.to_json()

def m_getQMNA5_HYDROPORTAIL(station_id):
    stationsFull = getStations()
    my_station = m_extractStation(stationsFull,station_id)
    
    code_hydro = my_station['code']
    code_hydro = code_hydro[0:len(code_hydro)-2]

    #Get Q-J analysis
    print("Station "+code_hydro)
    url = 'https://hydro.eaufrance.fr/sitehydro/'+code_hydro+'/synthese/regime/toutes-eaux'  # Replace with your desired URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    print(url)
    print('get hydroportail page for station')
    page = requests.get(url, headers=headers)
    print('parse page')
    soup = BeautifulSoup(page.text, 'html.parser')
    #st.text(soup)
    # get the element with id="main-title"
    #email_element = soup.find(attrs={'data-entity-code':"U401402001"})
    print('select analysis results')
    email_element = soup.select('div.statistics-result.position-relative')
    
    try: 
        txt = email_element[0]['data-analysis']
        #print('--------------')
        #print(txt)
        #print('--------------')
        
    except IndexError:
        print('("Analyse inconnue sur hydroportail")')
        quantile = pd.DataFrame([],
                            columns=['T','p','q','u','IC.low','IC.high','quality','nom'])
        return quantile
        #raise Exception("Analyse inconnue sur hydroportail")
    #st.text(txt)
    #print(str(email_element[0]))
    print('filter module')
    m = re.search(r'"mean":([0-9]*),"continuity0"', txt)
    #st.text(m.span())
    module = float(m.group(1))/1000.0
    print("Module = "+str(module)+" m3/s")
    
    #TODO : add module to df
    # T = 1 ; p  = 1 ; q = module; u = N/A ; IC.Low = module - ecarttype ; IC.High = module + eccarttype; quality = N/A; nom="Module / Moyenne"
    

    #GET QMNA analysis
    print("Station "+code_hydro)
    url = 'https://hydro.eaufrance.fr/sitehydro/'+code_hydro+'/synthese/regime/basses-eaux'  # Replace with your desired URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    print(url)
    print('get hydroportail page for station')
    page = requests.get(url, headers=headers)
    print('parse page')
    soup = BeautifulSoup(page.text, 'html.parser')
    #st.text(soup)
    # get the element with id="main-title"
    #email_element = soup.find(attrs={'data-entity-code':"U401402001"})
    print('select analysis results')
    email_element = soup.select('div.statistics-result.position-relative')
    
    try: 
        txt = email_element[0]['data-result']
        #print('--------------')
        #print(txt)
        #print('--------------')
        
    except IndexError:
        print('("Analyse inconnue sur hydroportail")')
        quantile = pd.DataFrame([],
                            columns=['T','p','q','u','IC.low','IC.high','quality','nom'])
        return quantile
    
    print('json quantiles')
    data_json = json.loads(txt)
    #st.text(data_json['result']['result']['quantile'])
    #print(data_json['quantile'])
    quantile = data_json['quantile']
    quantile = quantile[1:len(quantile)-1]
    #st.text(quantile)
    #print(quantile)
    print('convert to df')
    df = pd.DataFrame(list(quantile))

    print('filter module')
    print('add module to df')
    # T = 1 ; p  = 1 ; q = module; u = N/A ; IC.low = module - ecarttype ; IC.high = module + eccarttype; quality = N/A; nom="Module / Moyenne"
    
    df.loc[-1] = [1, 1, module* 1000.0, None, None, None,  None ]
    df.index = df.index + 1 
    df = df.sort_index()  # sorting by index

    print('add names')
    # add names
    for quant in df.itertuples(index=True):
        #print(quant)
        #print(quant.p)
        if quant.p == 0.5:
            nom = "Biennale (médiane)"
        elif quant.p == 0.2:
            nom = "Quinquennale (sèche)"
        elif quant.p == 0.1:
            nom = "Décennale (sèche)"
        elif quant.p == 0.05:
            nom = "Vicennale (sèche)"
        elif quant.p == 0.02:
            nom = "Cinquantennale (sèche)"
        elif quant.p == 0.8:
            nom = "Quinquennale (humide)"
        elif quant.p == 0.9:
            nom = "Décennale (humide)"
        elif quant.p == 0.95:
            nom = "Vicennale (humide)"
        elif quant.p == 0.98:
            nom = "Cinquantennale (humide)"
        elif quant.p == 1:
            nom = "Module/Moyenne"
        else:
            nom = ""
        df.at[quant.Index,'nom'] = nom

    #print(df)
    print('filtering and convertions')
    df = df[df['nom']!=""] #filter named quantiles
    df['q'] = round(df['q']/1000.0, 3) #return m3/S
    df['IC.low'] = round(df['IC.low']/1000.0, 3) #return m3/S
    df['IC.high'] = round(df['IC.high']/1000.0, 3) #return m3/S


    #print(df)
    qmna5 = df[df['T']==5]
    #print(qmna5)
    print("QMNA5 = "+str(qmna5['q'].values[0])+" m3/s")

    return df


def m_getQMNA5(station_id):
    
    # CALCUL LOCAL du QMNA5
    type_value_id = 5 #constant for DEBIT #TODO: Should be moved into conf !
    debits_moyen_journaliers = m_getAllSamplesAnalyse(station_id, type_value_id , start_date=-1, end_date=-1, grpFunc="AVERAGE",chartMode=True)
    
    if debits_moyen_journaliers.shape[0] == 0:
        return pd.DataFrame(columns = ['timestamp', 'numeric_value', 'status', 'qualification', 'initialPoint','unknown', 'station_id'])

    #compute QMNA5 from data
    return_period = 5
    freq_return = 1/return_period #0.2

    print("CALCUL DU QMNA5 LOCAL")
    samples = debits_moyen_journaliers
    quantile = pd.DataFrame([],
                            columns=['T','p','q','u','IC.low','IC.high','quality','nom'])
    
    #2-5 5-10 10-20 20-50
    #1-(2-5 5-10 10-20 20-50)

    # Calculer le percentile 98% (1/1.02)
    QMNA1_02 = np.percentile(samples[['numeric_value']], 98)
    print(QMNA1_02)
    quantile.loc[-1] = [1.02, 98/100, QMNA1_02, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index


    # Calculer le percentile 90% (1/1.11)
    QMNA1_11 = np.percentile(samples[['numeric_value']], 90)
    print(QMNA1_11)
    quantile.loc[-1] = [1.11, 90/100, QMNA1_11, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index

    # Calculer le percentile 80% (1/1.25)
    QMNA1_25 = np.percentile(samples[['numeric_value']], 80)
    print(QMNA1_25)
    quantile.loc[-1] = [1.25, 80/100, QMNA1_25, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index


    # Calculer le percentile 50% (1/2)
    QMNA2 = np.percentile(samples[['numeric_value']], 50)
    print(QMNA2)
    quantile.loc[-1] = [2, 50/100, QMNA2, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index

    # Calculer le percentile 20% (1/5)
    QMNA5 = np.percentile(samples[['numeric_value']], 20)
    print(QMNA5)
    quantile.loc[-1] = [5, 20/100, QMNA5, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index

    # Calculer le percentile 10% (1/10)
    QMNA10 = np.percentile(samples[['numeric_value']], 10)
    print(QMNA10)
    quantile.loc[-1] = [10, 10/100, QMNA10, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index

    # Calculer le percentile 2% (1/50)
    QMNA50 = np.percentile(samples[['numeric_value']], 2)
    print(QMNA50)
    quantile.loc[-1] = [50, 2/100, QMNA50, None, None, None,  None,None]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index

    print('filter module')
    m = float(samples[['numeric_value']].mean())
    s  = float(samples[['numeric_value']].std())
    print (m)

    #TODO : add module to df
    # T = 1 ; p  = 1 ; q = module; u = N/A ; IC.low = module - ecarttype ; IC.high = module + eccarttype; quality = N/A; nom="Module / Moyenne"
    
    quantile.loc[-1] = [1, 1, m, None, (m-s/2), (m+s/2),  None,"Module/Moyenne"  ]
    quantile.index = quantile.index + 1 
    quantile = quantile.sort_index()  # sorting by index

    print(quantile)
    print('convert to df')
    df = quantile
    print('add names')

    # add names
    for quant in df.itertuples(index=True):
        print(quant)
        print(quant.p)
        if quant.p == 0.5:
            nom = "Biennale (médiane)"
        elif quant.p == 0.2:
            nom = "Quinquennale (sèche)"
        elif quant.p == 0.1:
            nom = "Décennale (sèche)"
        elif quant.p == 0.05:
            nom = "Vicennale (sèche)"
        elif quant.p == 0.02:
            nom = "Cinquantennale (sèche)"
        elif quant.p == 0.8:
            nom = "Quinquennale (humide)"
        elif quant.p == 0.9:
            nom = "Décennale (humide)"
        elif quant.p == 0.95:
            nom = "Vicennale (humide)"
        elif quant.p == 0.98:
            nom = "Cinquantennale (humide)"
        elif quant.p == 1:
            nom = "Module/Moyenne"
        else:
            nom = ""
        df.at[quant.Index,'nom'] = nom

    print(df)
    #print('filtering and convertions')
    #df = df[df['nom']!=""] #filter named quantiles
    #df['q'] = round(df['q']/1000.0, 2) #return m3/S
    #df['IC.low'] = round(df['IC.low']/1000.0, 2) #return m3/S
    #df['IC.high'] = round(df['IC.high']/1000.0, 2) #return m3/S


    #print(df)
    qmna5 = df[df['T']==5]
    if not qmna5.empty:
        #print(qmna5)
        print("QMNA5 = "+str(qmna5['q'].values[0])+" m3/s")

    return df