#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""maptools.py: Contains usefuls function dealing with maps (folium), linked to our Database"""

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
import folium
import json
from folium.plugins import HeatMap, AntPath
import folium.plugins as plugins
from folium.plugins import GroupedLayerControl
from folium.plugins import MarkerCluster

from tools.queries import *

# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------


#function that create and returns a folium map based on leaflet (folium)
def create_map_bv(showMultipleLayers=True, showBorders=True, showDecorations=True):
    # st.secrets["observatory"]["center_map_location"] contains static values instead of cumputing it always

    m = folium.Map(location=st.secrets["observatory"]["center_map_location"], zoom_start=10, control_scale=True)

    #LAYERS
    if showMultipleLayers:
        # see http://leaflet-extras.github.io/leaflet-providers/preview/
        folium.raster_layers.TileLayer(
        tiles='https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png',
        attr='&copy; OpenStreetMap France | &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="OpenStreetMap",
        max_zoom=20,
        overlay=False,
        control=True,
        ).add_to(m)
        
        folium.raster_layers.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; ESRI',
        name="ESRI Topo",
        max_zoom=20,
        overlay=False,
        control=True,
        ).add_to(m)

        folium.raster_layers.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr="Tiles &copy; ESRI",
        name="ESRI ORTHO",
        max_zoom=20,
        overlay=False,
        control=True,
        ).add_to(m)

    #Logo syndicat
    if showDecorations:
        folium.plugins.FloatImage('./app/static/images/logo-carre-quadri-SBVR.jpg',  bottom=3, left=87, width='100px').add_to(m)
        # etoile nord
        north_url = "./app/static/images/cardinal-point.png"
        folium.plugins.FloatImage(north_url, bottom=10, left=1,width='45px').add_to(m)

    #Display contour of SBVR
    if showBorders:
        g1 = folium.FeatureGroup( "Contours")  # First subgroup of fg
        
        # I've used this technic to create a mask
        #contour.geometry.coordinates[0].unshift([[180, -90], [180, 90], [-180, 90], [-180, -90]]);
        style = {'fillColor': '#FFFFFFFF', 'color': '#FF0000FF' , 'fillOpacity' : 0.8}
        field_locations = 'static/Contour_sbvr.geojson'
        folium.GeoJson(field_locations,
                style_function=lambda x: style
                ).add_to(g1)
        g1.add_to(m)
    
    return m

#Function that add streams to the given map
def add_streams_to_map(map):
    #--------------------------------------------
    #display locations from observatory
    #display streams
    #load waterstream infos and convert it to json with EPS:4326 transformation
    streams = getAllStreams()

    def style_fct(feature):
        default_style = {
            'color': 'lightblue',
        }
        if feature['geometry']['properties']['classification'] == 1:
            default_style['color'] = 'red'
        elif feature['geometry']['properties']['classification'] == 2:
            default_style['color'] = 'blue'


        return default_style
    
    ##Loop through each row in the dataframe
    g2 = folium.FeatureGroup( "Cours d'eau")  # Second subgroup of fg
    ce1 = folium.plugins.FeatureGroupSubGroup(g2, "Reyssouze", {'className':'subgroup'})  # First subgroup of fg
    ce2 = folium.plugins.FeatureGroupSubGroup(g2, "Affluents directs")  # Second subgroup of fg
    ce3 = folium.plugins.FeatureGroupSubGroup(g2, "Affluents secondaires", show=False)

    for i,row in streams.iterrows():
        #for stream in streams:
        json_g = json.loads(row['json_geom'])
        json_g['properties'] = {}
        json_g['properties']['classification'] = row['classification']
        json_g['properties']['name'] = row['name']
        #print (json_g)
        mstream = folium.GeoJson(data = json_g,
                                 style_function=style_fct,
                                 tooltip=row['name'],
                                 )
        #add popup
        html_popup = """<table>
            <tr>
                <td><b>Nom</b></td><td>{}</td>
            </tr>
            <tr>
                <td><b>Longueur</b></td><td>{} m</td>
            </tr>
        </table>
        """.format(row['name'], row['length'])
        folium.Popup(html_popup).add_to(mstream)

        #add geometry to map
        if row['classification'] == 1:
            mstream.add_to(ce1)
        elif row['classification'] == 2:
            mstream.add_to(ce2)
        else:
            mstream.add_to(ce3)

    g2.add_to(map)
    ce1.add_to(map)
    ce2.add_to(map)
    ce3.add_to(map)
    #Add Group
    GroupedLayerControl(
                groups={'Reseau Hydrographique': [ ce1, ce2, ce3]},
                exclusive_groups = False,
                collapsed=False,
    ).add_to(map)

#Function that add stations to the given map
def add_stations_to_map(map, clustered=False):
    #--------------------------------------------
    #display locations from observatory
    #display map
    #load stations infos
    stations = getAllStationsWithLocations()
    html_lnk = ""
    stations_paratronic = folium.FeatureGroup(name='Stations', show=True)
    if clustered:
        marker_cluster = MarkerCluster().add_to(stations_paratronic)

    ##Loop through each row in the dataframe
    for i,row in stations.iterrows():
        #Setup the content of the popup
        station_id = str(row["station_id"])
        station_code = str(row["code_sbvr"])
        html_str = 'Station :' + str(row["name"])+'<br /><a href="#" target="_top" onclick="$(\'#lnk_station_'+station_id+'\', parent.document.body)[0].click(); return false;">Informations détaillées</a>'
        html_lnk = html_lnk + '<a href="/station?station_id='+station_id+'" target="_self" id="lnk_station_'+station_id+'" class="lnk_hidden">Hyperlink '+station_id+' </a>'
                
        #iframe = folium.IFrame(html)
        #Initialise the popup using the iframe
        popup = folium.Popup(html_str, min_width=300, max_width=300)

        purpose_colour = {'TH':'blue', 'PZ':'green', 'STA':'red'}

        try:
            icon_color = purpose_colour[row['type']]
        except:
            #Catch nans
            icon_color = 'gray'

        #Add each row to the map
        mark = folium.Marker(location=[row['lat'],row['lon']],
                    popup = popup,
                    c=row['name'],
                    lazy=True,
                    icon=folium.Icon(color=icon_color, icon=''))
        
        if clustered:
            mark.add_to(marker_cluster)
        else:
            mark.add_to(stations_paratronic)
    
    #Add to layer to handle button
    stations_paratronic.add_to(map)

    #Add hidden link to pass trough iframe sandbox 'allow-top-navigation allow-top-navigation-by-user-activation'
    #print(html_lnk)
    html_lnk = html_lnk + '''<style>
             .lnk_hidden {
                display: none;
                visibility: hidden;
            }
        </style>
        '''
    st.markdown(html_lnk, unsafe_allow_html=True)

#function that add all existing locations to the given map
def add_locations_to_map(map):
    #--------------------------------------------
    #display locations from observatory
    #display map
    #load waterstream infos and convert it to json with EPS:4326 transformation
    locations = getAllLocations()
    
    ##Loop through each row in the dataframe
    for i,row in locations.iterrows():
        #Setup the content of the popup
        iframe = folium.IFrame('Lieu d\'observation :' + str(row["description"])+'<br />')
        
        #Initialise the popup using the iframe
        popup = folium.Popup(iframe, min_width=300, max_width=300)
        
        icon_color = 'gray'

        #Add each row to the map
        folium.Marker(location=[row['lat'],row['lon']],
                    popup = popup,
                    c=row['description'],
                    icon=folium.Icon(color=icon_color, icon='')).add_to(map)

#function that add current heatmap to the given map
def add_heat_map_to_map(map,start_date,end_date):
    #HeatMap - [latitude, longitude, frequency]
    group_heatmap = folium.FeatureGroup(name='Carte des températures sur les 30 derniers jours', show=True)
    type_values = '°C'
    stations = getAllStationsWithLocations()
    m_stations_list = dict()
    for station in stations.itertuples():
        m_stations_list[station.station_id] = station.name

    options = list(m_stations_list.keys())

    samples = getAllSamplesAnalyseWithLocations(options,type_values,start_date,end_date)
    samples = samples.groupby(["ust"])
    samples = samples[["lat","lon","numeric_value"]]
    samples = samples.mean()
    
    heat_map = HeatMap(samples,min_opacity=0.4,blur = 40, radius =50, gradient={0: 'blue', .5: 'lime', 1: 'red'})
    heat_map.add_to(group_heatmap)
    group_heatmap.add_to(map)
    return samples