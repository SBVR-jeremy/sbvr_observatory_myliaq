import os
import json

from flask import Flask, request, render_template_string
from flask import Flask, request, jsonify
from flask import Flask, render_template, Response
from flask_cors import CORS
from flask_caching import Cache

from tools.queries import * 
from tools.graphtools import *
from tools.utility import *

from datetime import datetime, date, timezone, timedelta
from dateutil import tz
from dateutil.relativedelta import *
import vl_convert as vlc

#temporary, should be used outside (graphtools)
import altair as alt
from vega_datasets import data
import geopandas as gpd
import pandas as pd

from pyproj import Transformer
import io
from PIL import Image
from filelock import FileLock

cache_config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs "FileSystemCache"
    "CACHE_DEFAULT_TIMEOUT": 300, #300s = 5 minutes
    "CACHE_DIR": "/cache/" #Used if FileSystemCache
}

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config.from_mapping(cache_config)
cache = Cache(app)


#WIDTH = 600
#HEIGHT = 300

#fontion from https://flask-caching.readthedocs.io/en/latest/
def make_key():
   """A function which is called to derive the key for a computed value.
      The key in this case is the concat value of all the json request
      parameters. Other strategy could to use any hashing function.
   :returns: unique string for which the value should be cached.
   """
   user_data = request.args
   return request.url+"?"+",".join([f"{key}={value}" for key, value in user_data.items()])

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/check_api")
def check_api():
    query = request.args.get("query")
    if query:
        response = {"response": "API IS WORKING - GET query too"}
        json_data = json.dumps(response)
        return json_data
    else:
        response = {"response": "API IS WORKING"}
        json_data = json.dumps(response)
        return json_data

@app.route("/api/communication")
def getCommunications():
    query = request.args.get("query")
    response = m_getCommunications()
    json_data = json.dumps(response)
    return json_data

@app.route('/api/qmna5', methods=['GET'])
@cache.cached(timeout=300, make_cache_key=make_key)
def qmna5Handler():
    #print ("Graph ALERTE generation handler")
    station_id = request.args.get("station_id",None)  
    if station_id is None:
        return "add ?station_id=XX to generate graph !"
    else:
        station_id = int(station_id)
    
    #print ("Graph generation for station_id "+str(station_id))

    nb_days = 3
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    ts_end = int(round(today.timestamp()*1000.0))

    type_value_id = 4 #TODO: REPLACE CONSTANT

    m_graph = m_getQMNA5_HYDROPORTAIL(station_id) #,type_value_id, ts_start,ts_end)

    if m_graph is not None:
        return m_graph.to_json()
    else:
        return """{"error":"Aucune donnée"}"""
    
@app.route("/api/statsChronique", methods=['GET'])
@cache.cached(timeout=300, make_cache_key=make_key)
def getStatsChroniques():
    try:
        stations = request.args.get("stations",None)  
        type_value_id = request.args.get("type_value_id",None)
        show_title = request.args.get("show_title",None)
        
        today = datetime.now(timezone.utc)
        two_days_ago = today - timedelta(days=7)

        date_start = request.args.get("date_start",two_days_ago.strftime("%Y-%m-%d"))
        date_end = request.args.get("date_end",today.strftime("%Y-%m-%d"))
                                    
        m_stations = getStations()
        if stations is not None and len(stations) <= 2:
            stations = None

        if stations is not None:
            stations_ids = list(map(int,stations[1:len(stations)-1].split(',')))
            
            initial_stations = dict()
            initial_stations[4] = {"title": "Majornas", "color" : '#003A7D'}
            initial_stations[3] = {"title": "Montagnat", "color" : '#008DFF'}
            initial_stations[1] = {"title": "Saone à Macon", "color" : "#F7A1CB"}
            initial_stations[2] = {"title": "Saint Julien sur R.", "color" : "#FF00FF"}
            initial_stations[11] = {"title": "Viriat", "color" : '#4ECB8D'}
            initial_stations[5] = {"title": "Baudières", "color" : '#FF9D3A'}
            initial_stations[54] = {"title": "Cras", "color" : '#F9E858'}
            initial_stations[58] = {"title" : "Pont de Vaux", "color" : "#00EEFF"}

            #filter stations to get uniformized colors
            stations = dict()
            for s_id in stations_ids:
                stations[s_id] = initial_stations[s_id]
                
        if stations is None:
            raise Exception("add ?station_id=XX to generate graph !")

        if type_value_id is None:
            raise Exception("add &type_value_id=XX to generate graph !")
        else:
            type_value_id = int(type_value_id)
        
        #turn date_start to start_date in ms
        #convert date_start and date_end to datetime UTC aware!
        time_start = datetime.min.time()
        time_start = time_start.replace(tzinfo=timezone.utc)
        
        time_end = datetime.max.time()
        time_end = time_end.replace(tzinfo=timezone.utc)

        #
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()

        #returns  'date_start 00:00:00' and 'date_end 23:59:59'
        n_date_start = datetime.combine(date_start,time_start)
        n_date_end = datetime.combine(date_end,time_end)

        #timestamp in milliseconds
        ts_start = int(round(n_date_start.timestamp()*1000.0)) 
        ts_end = int(round(n_date_end.timestamp()*1000.0))

        print ("Stats generation for stations_id "+str(stations))
        response = m_getStatsChroniqueHydro(stations, type_value_id,start_date=ts_start,end_date=ts_end)
        json_data = json.dumps(response)
        return json_data
    except Exception as e:
        #print (e)
        #print("NO DATA")
        new_data = {"error" : "Aucune donnée",
                    "exception" : str(e)}
        #print(new_data)
        return json.dumps(new_data)
    
@app.route('/api/graphAlerte', methods=['GET'])
@cache.cached(timeout=300, make_cache_key=make_key)
def graphAlerteHandler():
    #print ("Graph ALERTE generation handler")
    station_id = request.args.get("station_id",None)  
    if station_id is None:
        return "add ?station_id=XX to generate graph !"
    else:
        station_id = int(station_id)
    
    #print ("Graph generation for station_id "+str(station_id))

    nb_days = 3
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    ts_end = int(round(today.timestamp()*1000.0))

    type_value_id = 4 #TODO: REPLACE CONSTANT

    m_graph = generateAlerteGraph(station_id,type_value_id, ts_start,ts_end)
    if m_graph is not None:
        return m_graph.to_json()
    else:
        return """{"error":"Aucune donnée"}"""
    
@app.route('/api/graphCumulatedChronique', methods=['GET','POST'])
#@cache.cached(timeout=180, make_cache_key=make_key)
def graphCumulatedChroniqueHandler():
    #print ("Graph Cumulated Chronique generation handler")
    #print(request.method)
    try:
        if request.method== "POST":
            payload = request.get_json()
            if payload:
                #print("load json payload")
                payload = json.loads(payload)
                #print (payload)
            #else:
                #print ("no payload")
            
            stations = payload["stations"]
            #print(stations_id)
            #if stations_id is not None:
            #    print(stations_id)

            type_value_id = payload["type_value_id"]
            show_title = payload["show_title"]
            date_start = payload["date_start"]
            date_end = payload["date_end"]
            draw_seuils=payload["draw_seuils"]
            output = payload["output"]
        else:
            stations = request.args.get("stations",None)  
            type_value_id = request.args.get("type_value_id",None)
            show_title = request.args.get("show_title",None)
            output = request.args.get("output", "vega")

            today = datetime.now(timezone.utc)
            two_days_ago = today - timedelta(days=7)

            date_start = request.args.get("date_start",two_days_ago.strftime("%Y-%m-%d"))
            date_end = request.args.get("date_end",today.strftime("%Y-%m-%d"))
                                        
            draw_seuils=request.args.get("draw_seuils",None)
            m_stations = getStations()
            if stations is not None:
                stations_ids = list(map(int,stations[1:len(stations)-1].split(',')))
                

                initial_stations = dict()
                initial_stations[4] = {"title": "Majornas", "color" : '#003A7D'}
                initial_stations[3] = {"title": "Montagnat", "color" : '#008DFF'}
                initial_stations[1] = {"title": "Saone à Macon", "color" : "#F7A1CB"}
                initial_stations[2] = {"title": "Saint Julien sur R.", "color" : "#FF00FF"}
                initial_stations[11] = {"title": "Viriat", "color" : '#4ECB8D'}
                initial_stations[5] = {"title": "Baudières", "color" : '#FF9D3A'}
                initial_stations[54] = {"title": "Cras", "color" : '#F9E858'}
                initial_stations[58] = {"title" : "Pont de Vaux", "color" : "#00EEFF"}

                #filter stations to get uniformized colors
                stations = dict()
                for s_id in stations_ids:
                    stations[s_id] = initial_stations[s_id]

                
        if stations is None:
            return ("add ?station_id=XX to generate graph !")

            
        if type_value_id is None:
            return ("add &type_value_id=XX to generate graph !")
        else:
            type_value_id = int(type_value_id)
        
        print ("Graph generation for stations_id "+str(stations))
        #print(show_title)

        m_graph = generateCumulatedChroniqueGraph(stations, type_value_id, date_start, date_end,showTitle=show_title, draw_seuils = draw_seuils)
        print("graph generated")                                       
        # try:
        #     m_graph["usermeta"] = {
        #         "embedOptions": {
        #             "downloadFileName": "my-download-name",
        #             "actions": {"export": True, "source": False, "editor": False, "compiled": False},
        #         }
        #     }
        # except TypeError:
        #     print("Type error")
        #     m_graph = None

        if output is None or output == "vega" :
            if m_graph is not None : 
                return m_graph.to_json()
            else:
                print("NO DATA")
                return """{"error":"Aucune donnée"}"""
        elif output == "png":
            if m_graph is not None : 
                lock = FileLock("./static/graph_cummulated_chronique.png.lock")
                with lock:
                    m_graph.save("./static/graph_cummulated_chronique.png", ppi=200)
                    response = app.send_static_file('graph_cummulated_chronique.png')
                
                return response
            else:
                return None
    
        # if m_graph is not None : 
        #     print ("save image to file")
        #     lock = FileLock("./static/chartWaterHeightT.png.lock")
        #     with lock:
        #         m_graph.save("./static/chartWaterHeightT.png")
        #         response = app.send_static_file('chartWaterHeightT.png')
            
        #     return response
        # else:
        #     return None
        #     #return """{"error":"Aucune donnée"}"""
    except Exception as e:
        print (e)
        return app.send_static_file('temp.png')
    
@app.route('/api/graphChronique', methods=['GET'])
@cache.cached(timeout=180, make_cache_key=make_key, unless=lambda : request.args.get("output","vega") == "png")
def graphChroniqueHandler():
    #print ("Graph ALERTE generation handler")
    station_id = request.args.get("station_id", None)
    show_title = request.args.get("show_title", True)
    type_value_id = request.args.get("type_value_id", None)
    output = request.args.get("output", "vega")

    date_start = request.args.get("date_start", None)
    date_end = request.args.get("date_end", None)

    if station_id is None:
        return ("add ?station_id=XX to generate graph !")
    else:
        station_id = int(station_id)

    if type_value_id is None:
        return ("add &type_value_id=XX to generate graph !")
    else:
        type_value_id = int(type_value_id)

   
    #print ("Graph generation for station_id "+str(station_id))
    #print(show_title)
    
    nb_days = 3  #TODO: Handle this as variable .toml
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    if date_start is not None:
        ts_start = int(round(datetime.strptime(date_start,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    
    if date_end is not None:
        ts_end = int(round(datetime.strptime(date_end,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_end = int(round(today.timestamp()*1000.0))


    m_graph = generateChroniqueGraph(station_id, type_value_id, ts_start, ts_end, showTitle=(show_title!="false"))
    try:
        m_graph["usermeta"] = {
            "embedOptions": {
                "downloadFileName": "Chronique",
                "actions": {"export": True, "source": False, "editor": False, "compiled": False, "fullscreen": True},
                "fullscreen": True,
            }
        }

        
    except TypeError:
        m_graph = None

    if output == "vega":
        if m_graph is not None : 
            return m_graph.to_json()
        else:
            print("NO DATA")
            return """{"error":"Aucune donnée"}"""
    elif output == "png":
        if m_graph is not None : 
            lock = FileLock("./static/graph_chronique_pluvio.png.lock")
            with lock:
                m_graph.save("./static/graph_chronique_pluvio.png", ppi=200)
                response = app.send_static_file('graph_chronique_pluvio.png')
            
            return response
        else:
            #from PIL import Image
            img = Image.new("RGB", (1, 1), (255, 255, 255))
            img.save("./static/pixelEmptyGraph.png", "PNG")

            response = app.send_static_file('pixelEmptyGraph.png')
            return response
            #return None
        
@app.route('/api/graphDebit', methods=['GET'])
@cache.cached(timeout=180, make_cache_key=make_key, unless=lambda : request.args.get("output","vega") == "png")
def graphDebitHandler():
    #print ("Graph ALERTE generation handler")
    station_id = request.args.get("station_id", None)
    show_title = request.args.get("show_title", True)
    type_value_id = request.args.get("type_value_id", None)
    output = request.args.get("output", "vega")

    date_start = request.args.get("date_start", None)
    date_end = request.args.get("date_end", None)

    if station_id is None:
        return ("add ?station_id=XX to generate graph !")
    else:
        station_id = int(station_id)

    #type value should be restricted to Debit only...
    if type_value_id is None:
        return ("add &type_value_id=XX to generate graph !")
    else:
        type_value_id = int(type_value_id)

   
    #print ("Graph generation for station_id "+str(station_id))
    #print(show_title)
    
    nb_days = 90  #TODO: Handle this as variable .toml
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    if date_start is not None:
        ts_start = int(round(datetime.strptime(date_start,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    
    if date_end is not None:
        ts_end = int(round(datetime.strptime(date_end,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_end = int(round(today.timestamp()*1000.0))


    m_graph = generateChroniquePeriodeRetour2Graph(station_id, type_value_id, ts_start, ts_end, showTitle=(show_title!="false"))
    try:
        m_graph["usermeta"] = {
            "embedOptions": {
                "downloadFileName": "Debit",
                "actions": {"export": True, "source": False, "editor": False, "compiled": False, "fullscreen": True},
                "fullscreen": True,
            }
        }

        
    except TypeError:
        m_graph = None

    if output == "vega":
        if m_graph is not None : 
            return m_graph.to_json()
        else:
            print("NO DATA")
            return """{"error":"Aucune donnée"}"""
    elif output == "png":
        if m_graph is not None : 
            lock = FileLock("./static/graph_debit_hydro.png.lock")
            with lock:
                m_graph.save("./static/graph_debit_hydro.png", ppi=200)
                response = app.send_static_file('graph_debit_hydro.png')
            
            return response
        else:
            return None

@app.route('/api/graphUpdate', methods=['GET'])
@cache.cached(timeout=180, make_cache_key=make_key, unless=lambda : request.args.get("output","vega") == "png")
def graphUpdateHandler():
    station_id = request.args.get("station_id", None)
    show_title = request.args.get("show_title", True)
    type_value_id = request.args.get("type_value_id", None)
    output = request.args.get("output", "vega")

    if station_id is None:
        return ("add ?station_id=XX to generate graph !")
    else:
        station_id = int(station_id)

    if type_value_id is None:
        return ("add &type_value_id=XX to generate graph !")
    else:
        type_value_id = int(type_value_id)

    nb_days = 3
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    ts_end = int(round(today.timestamp()*1000.0))

    samples = m_getAllSamplesAnalyse(station_id,type_value_id, start_date=ts_start, end_date=ts_end)

    if samples.shape[0] == 0:
        return """{"error":"Aucune donnée"}"""

    stations = getStations()
    my_station = m_extractStation(stations,station_id)
    station_name = my_station['name'] if my_station is not None else "Station not Found"

    type_values = getDataTypeHydro()
    type_value = m_extractStation(type_values,type_value_id)

    try:
        unit_symbol = type_value["unit"] if type_value is not None else "Unit not Found"
    except KeyError:
        unit_symbol = '' #This type_value has no unit

    last_record = samples.tail(1)
    pre_last_record = samples.tail(2).head(1)
    m_dif= last_record.numeric_value.item() - pre_last_record.numeric_value.item()
    
    #MAJ indicator
    #date_diff = datetime.now(timezone.utc)- (last_record.timestamp.item())
    date_diff = int(round(datetime.now(timezone.utc).timestamp())) - int(round(last_record.timestamp.item().timestamp()))
    date_diff_hour = (date_diff/3600)

    if (date_diff_hour<=1): #everything seems OK
        text_data = "🟢 MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))
    elif (date_diff_hour>1 and date_diff_hour <=6) : #paid attention...
        text_data = "🟠 MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))
    else: #something wrong...
        text_data = "🔴 MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))

    #text_data = "🟢 MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))
    val_data = "{} {}".format(round(last_record.numeric_value.item(),3),unit_symbol)
    # 🟢 / 🟠/ 🔴

    ANNOTATIONS = [
        (0, 0.75, text_data, 4),
        (0.2, 0, val_data, 14),
    ]
    annotations_df = pd.DataFrame(
        ANNOTATIONS, columns=["idx", "idy", "txt", "txt_size"]
    )
    #annotation_df = pd.DataFrame({'idx':0, 'idy':0, 'txt': text_data})
    
    points = alt.Chart(annotations_df, height=80).mark_text(size=12, dx=0, dy=0, align="left").encode(
            x=alt.X('idx', axis=None, scale=alt.Scale(domain=[0,1])),
            y=alt.Y('idy', axis=None, scale=alt.Scale(domain=[0,1])),
            text=alt.Text('txt'),
            size=alt.Size('txt_size', legend=None),
            tooltip=alt.value(None),
            )

    points["usermeta"] = {
        "embedOptions": {
            "actions": False,
            "fullscreen": False
        }
    }

    text = alt.Chart(annotations_df).mark_text(
        align='left',
        baseline='middle',
        dx=7
    ).encode(
        x='idx:Q',
        y='idy:Q',
        text='idx',
        size='txt_size'
    )

    annotation_layer = points # + text

    if output == "vega":
        if annotation_layer is not None : 
            return annotation_layer.to_json()
        else:
            print("NO DATA")
            return """{"error":"Aucune donnée"}"""
    elif output == "png":
        if annotation_layer is not None : 
            #annotation_layer.save("./static/graph_update_hydro.png", ppi=200)
            #return app.send_static_file('graph_update_hydro.png')
            lock = FileLock("./static/graph_update_hydro.png.lock")
            with lock:
                annotation_layer.save("./static/graph_update_hydro.png", ppi=200)
                response = app.send_static_file('graph_update_hydro.png')
            
            return response
    
        else:
            return None

def convertCoords(row):
    transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326")
    x2,y2 = transformer.transform(row['x'],row['y'])
    return pd.Series([x2, y2])

@app.route('/api/mapSituation', methods=['GET'])
def mapSituationHandler():
    simulation_date = request.args.get("simulation_date", None)

    situations = m_getMapSituation(simulation_date)
    if situations is None :
        return app.send_static_file('emptyGraph.png')
        
    situations[['xWSG','yWSG']] = situations.apply(convertCoords,axis=1)
    
    #print("SIMULATION FROM MAPSITUATION\n\n")
    #print(situations)
    #remove "Absence de données"
    situations = situations[situations['thresholdName'] != "Absence de données"]
    
    if situations.shape[0] == 0:
        return app.send_static_file('emptyGraph.png')
    
    #print("SITUATION IDX=0")
    #print(situations["simulationDate"])
    #print(situations["simulationDate"].iloc[0])

    #list(filter(lambda x: x['idCategory'] == category_id, communications))

    domain = ["Ecoulement visible acceptable", "Ecoulement visible faible", "Ecoulement non visible", "Assec", "Observation impossible"]
    range_ = ["#0000FF","#FFFF00", "#FFa500", "#FF0000", "#808080"]
    
    source = alt.topo_feature(data.world_110m.url, 'countries')

    background = alt.Chart(source).mark_geoshape(
        fill='gray',
        fillOpacity=0.1,
        stroke='lightgreen',
    ).encode(
        tooltip='id:N' 
    )

    
    #add contour SBVR
    # Load the random GeoJSON data
    sbvr_df = gpd.read_file('./static/Contour_sbvr.geojson')
    #print(sbvr_df)

    # Create a map using Altair
    sbvr_chart = alt.Chart(sbvr_df).mark_geoshape(fill="white", stroke="blue", strokeWidth=2)
    
    points = alt.Chart(situations).mark_circle(stroke='black').encode(
        longitude='yWSG:Q',
        latitude='xWSG:Q',
        size=alt.value(100),
        tooltip='name',
        color=alt.Color('thresholdName',  title='Observation ONDE').scale(domain=domain, range=range_),
    )

    simulationDate = datetime.fromtimestamp(situations["simulationDate"].iloc[0]/1000)
    #print(simulationDate)

    m_graph = (background + sbvr_chart+ points ).project(
        type= 'naturalEarth1',
        scale= 40000,
        center= [5.16113,46.27347],                     # [lon, lat] 46.30347,5.16113
        #translate=[0, 0], 
    ).properties(
        title="Situation ONDE le {}".format(simulationDate.strftime("%d/%m/%Y"))
    )
    
    if m_graph is not None : 
        print ("save mapSituation onde image to file")
        lock = FileLock("./static/situationOnde.png.lock")
        with lock:
            m_graph.save("./static/situationOnde.png", ppi=200)
            response = app.send_static_file('situationOnde.png')
        
        return response
    
        #m_graph.save("./static/situationOnde.png", ppi=100)
        #return app.send_static_file('situationOnde.png')
    else:
        return None
    
    #print ("okok")
    #return m_graph.to_json()

@app.route('/api/graphChroniquePluvio', methods=['GET'])
@cache.cached(timeout=180, make_cache_key=make_key, unless=lambda : request.args.get("output","vega") == "png")
def graphChroniquePluvioHandler():
    #print ("Graph  pluvio generation handler")
    station_id = request.args.get("station_id", None)
    type_value_id = request.args.get("type_value_id", None)
    show_title = request.args.get("show_title", True)
    output = request.args.get("output", "vega")

    if station_id is None:
        return ("add ?station_id=XX to generate graph !")
    else:
        station_id = int(station_id)

    if type_value_id is None:
        return ("add &type_value_id=XX to generate graph !")
    else:
        type_value_id = int(type_value_id)
    
    date_start = request.args.get("date_start", None)
    date_end = request.args.get("date_end", None)

    
    #print ("Graph generation for pluvio station_id "+str(station_id))
    #print(show_title)
    nb_days = 7
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)

    #timestamp in milliseconds
    if date_start is not None:
        ts_start = int(round(datetime.strptime(date_start,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    
    if date_end is not None:
        ts_end = int(round(datetime.strptime(date_end,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_end = int(round(today.timestamp()*1000.0))
    

    m_graph = None
    try:
        m_graph = generateChroniquePluvioGraph(station_id, type_value_id, ts_start, ts_end, show_title!="false")
    
        m_graph["usermeta"] = {
            "embedOptions": {
                "downloadFileName": "Chronique",
                "actions": {"export": True, "source": False, "editor": False, "compiled": False, "fullscreen": True},
                "fullscreen": True,
            }
        }

    except TypeError:
        m_graph = None
    except Exception as e:
        print (e)

    if output == "vega":
        if m_graph is not None : 
            return m_graph.to_json()
        else:
            print("NO DATA")
            return """{"error":"Aucune donnée"}"""
    elif output == "png":
        if m_graph is not None : 
            #m_graph.save("./static/analyse_chronique_pluvio.png", ppi=200)
            #return app.send_static_file('analyse_chronique_pluvio.png')
            lock = FileLock("./static/analyse_chronique_pluvio.png.lock")
            with lock:
                m_graph.save("./static/analyse_chronique_pluvio.png", ppi=100)
                response = app.send_static_file('analyse_chronique_pluvio.png')
            
            return response
        else:
            #from PIL import Image
            img = Image.new("RGB", (1, 1), (255, 255, 255))
            img.save("./static/pixelEmptyGraph.png", "PNG")

            response = app.send_static_file('pixelEmptyGraph.png')
            return response
            #return None
    
@app.route('/api/graphAnalyseMeteo', methods=['GET'])
@cache.cached(timeout=180, make_cache_key=make_key, unless=lambda : request.args.get("output","vega") == "png")
def graphAnalyseMeteoHandler():
    print ("Graph analyse meteo generation handler")
    station_id = request.args.get("station_id", None)
    show_title = request.args.get("show_title", True)
    date_start = request.args.get("date_start", None)
    date_end = request.args.get("date_end", None)
    output = request.args.get("output", "vega")

    if station_id is None:
        return ("add ?station_id=XX to generate graph !")
    else:
        station_id = int(station_id)

    
    #print ("Graph generation for meteo station_id "+str(station_id))
    #print(show_title)
    nb_days = 30
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    if date_start is not None:
        ts_start = int(round(datetime.strptime(date_start,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
    
    if date_end is not None:
        ts_end = int(round(datetime.strptime(date_end,"%Y-%m-%d").timestamp()*1000.0))
    else:
        ts_end = int(round(today.timestamp()*1000.0))

    m_graph = None
    m_graph = generateAnalyseMeteoGraph(station_id,ts_start, ts_end, show_title!="false")

    try:
        m_graph["usermeta"] = {
            "embedOptions": {
                "downloadFileName": "Analyse_meteo",
                "actions": {"export": True, "source": False, "editor": False, "compiled": False, "fullscreen": True},
                "fullscreen": True,
            }
        }

    except TypeError:
        m_graph = None
    except Exception as e:
        print (e)

    if output == "vega":
        if m_graph is not None : 
            return m_graph.to_json()
        else:
            print("NO DATA")
            return """{"error":"Aucune donnée"}"""
    elif output == "png":
        if m_graph is not None : 
            #m_graph.save("./static/analyse_meteo.png", ppi=200)
            #return app.send_static_file('analyse_meteo.png')
            lock = FileLock("./static/analyse_meteo.png.lock")
            with lock:
                m_graph.save("./static/analyse_meteo.png", ppi=200)
                response = app.send_static_file('analyse_meteo.png')
            
            return response
        else:
            return None


@app.route('/api/graphAnalyseAnnuelleMeteo', methods=['GET'])
@cache.cached(timeout=180, make_cache_key=make_key, unless=lambda : request.args.get("output","vega") == "png")
def graphAnalyseMeteoAnnuelleHandler():
    print ("Graph analyse meteo generation handler")
    station_id = request.args.get("station_id", None)
    show_title = request.args.get("show_title", True)
    year = request.args.get("year", None)
    output = request.args.get("output", "vega")
    
    if station_id is None:
        return ("add ?station_id=XX to generate graph !")
    else:
        station_id = int(station_id)

    
    print ("Graph generation for meteo annuelle station_id "+str(station_id)+" annee "+str(year))
    #print(show_title)
    nb_days = 365
    today = datetime.now(timezone.utc)
    two_days_ago = today - timedelta(days=nb_days)
    
    #timestamp in milliseconds
    if year is not None:
        first_of_year = datetime(int(year),1,1,0,0,0,0)
        end_of_year = datetime(int(year),12,31,23,59,59)
        ts_start = int(round(first_of_year.timestamp()*1000.0))
        ts_end = int(round(end_of_year.timestamp()*1000.0))
    else:
        ts_start = int(round(two_days_ago.timestamp()*1000.0)) 
        ts_end = int(round(today.timestamp()*1000.0)) 
    

    m_graph = None
    m_graph = graphAnalyseAnnuelleMeteo(station_id, ts_start , ts_end, show_title==True)

    try:
        m_graph["usermeta"] = {
            "embedOptions": {
                "downloadFileName": "Analyse_meteo_annuelle",
                "actions": {"export": True, "source": False, "editor": False, "compiled": False, "fullscreen": True},
                "fullscreen": True,
            }
        }

    except TypeError:
        m_graph = None
    except Exception as e:
        print (e)
    
    if output == "vega":
        if m_graph is not None : 
            return m_graph.to_json()
        else:
            print("NO DATA")
            return """{"error":"Aucune donnée"}"""
    elif output == "png":
        if m_graph is not None : 
            #m_graph.save("./static/analyse_annuelle_meteo.png", ppi=200)
            #return app.send_static_file('analyse_annuelle_meteo.png')
            lock = FileLock("./static/analyse_annuelle_meteo.png.lock")
            with lock:
                m_graph.save("./static/analyse_annuelle_meteo.png", ppi=200)
                response = app.send_static_file('analyse_annuelle_meteo.png')
            
            return response
        else:
            return None
#-----------------------------------------------------------------
# LAUNCH APP
#-----------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1111, debug=True)

