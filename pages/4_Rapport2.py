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


#from spire.doc import *
#from spire.doc.common import *
#from spire.doc import Document as sp_Document

#This need to be changed on production !!!
import toml

################
#PDF export template

#import pdfkit
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

##### Doc template
from docxtpl import DocxTemplate
from docxtpl import InlineImage
from docx.shared import Mm


import re

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

#Load secret file
try:
    secrets = toml.load("./.streamlit/secrets.toml")
    headers = {
        "Content-Type" : "application/json; charset=utf-8",
        "Authorization" : 'Bearer '+secrets["myliaq"]["api_key"]
    }

except Exception as e:
    print("Loading secret file failed : 2_Rapport.py l:62")
    print(e)

#import locale
#locale.setlocale(locale.LC_TIME, "fr_FR")
from babel.dates import format_date, format_datetime, format_time

import requests
import os

from tools.utility import *
from tools.streamlit_utility import *
from tools.queries import *

#---------------------------------------------------------------------------------------------
# Capture screenhot for meteoblue

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options  

# ---------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------

def generate_docx_report():
    print("GENERATE DOCS REPORT")
    print(bulletins[type_bsh])
    template_path = bulletins[type_bsh]["template"]
    print(template_path)
    doc = DocxTemplate(template_path)
    context = { 'company_name' : "Reyssouze et Affluents" }
    
    data  = dict()
    #generic informations
    data["type_bsh"] = type_bsh
    data["date_donnees_val"] = date_donnees_val
    data["date_publication_val"] = date_publication_val
    data["date_donnees_range_start"] = date_donnees_range_start
    data["date_donnees_range_end"] = date_donnees_range_end
    
    # images list
    data["imgMeteoData"] = imgMeteoData
    data["imgHydroData"] = imgHydroData
    data["imgTemperatureData"] = imgTemperatureData
    # data["imgPiezoData"] = imgPiezoData

    # Visibility controllers
    data["showPrevis"] = showPrevis
    data["showCouranto"] = showCouranto
    data["showONDE"] = showONDE
    # data["showEauxSout"] = showEauxSout
    data["showCommunications"] = showCommunications

    #raw data
    # data["dataMeteo"] = meteo_data
    data["temperature_data"] = temperature_data
    # data["dataHydro"] = hydro_data
    # data["dataPiezo"] = piezo_data
    # data["dataCommunications"] = communications_data

    
    #print(communications_externes)
    
    #title
    # communications_externes_data = {}
    # #communications_externes_data[0] = {"col1": "ID", "col2" : "Title" , "col3": "Subtitle", "col4": "Comment"}
    # #idx1 = 1

    # idx1 = 0
    # for row in communications_externes:
        
    #     try:
    #         sub_title = row['subtitle']
    #     except KeyError:
    #         sub_title=""
        
    #     communications_externes_data[idx1] = {"col1" : row['id'], "col2" : row['title'], "col3": sub_title, "col4": row['comment']}
    #     idx1 += 1
    
    # communications_externes_data = dict(communications_externes_data)
    #print(communications_externes_data)

    #print(communications_externes)
    data["communications_externes"] = communications_externes

    #data[""] = 
    #data[""] = 

    #format date...
    data["date_publication"]=format_date(date_publication_val,format='long', locale='fr')

    #fille couranto img
    myimage = InlineImage(doc, image_descriptor='./static/bulletin/couranto.png', width=Mm(120), height=Mm(160))
    data["couranto_img"] = myimage

    #fill onde img
    myimage = InlineImage(doc, image_descriptor='./static/bulletin/situationOnde.png', width=Mm(120), height=Mm(160))
    data["onde_img"] = myimage
    
    #fill previs meteo img
    data["previs_meteo_img"] = []
    today = datetime.datetime.today()
    if showPrevis:
        for img_url in ['./static/bulletin/PreviMeteoBlueBourg'+today.strftime("%Y%m%d")+'.png', './static/bulletin/PreviMeteoBlueMontrevel'+today.strftime("%Y%m%d")+'.png', './static/bulletin/PreviMeteoBluePontDeVaux'+today.strftime("%Y%m%d")+'.png']:
            myTempImage = InlineImage(doc, image_descriptor=img_url  , width=Mm(100) )
            data["previs_meteo_img"].append(myTempImage)

    #fill meteo img
    data["meteo_img"] = []
    idx = 0
    for img_url in data["imgMeteoData"]:
        #print("generate static file for meteoData")
        #print(img_url)
        
        try:
            response = requests.get(img_url)
            img_path = "./static/bulletin/meteo-temp"+str(idx)+".png"
            file = open(img_path, "wb")
            file.write(response.content)
            current_size = file.tell()
            file.close()
            
            if current_size > 69: #60 is one by one pixel png image 
                myTempimage = InlineImage(doc, image_descriptor="./static/bulletin/meteo-temp"+str(idx)+".png" , width=Mm(50))
                data["meteo_img"].append(myTempimage)
                idx = idx + 1
        
        except:
            #print("image error, empty ?")
            pass

    #fill hydro img
    data["hydro_img"] = []
    idx = 0
    for img_url in data["imgHydroData"]:
        #print("generate static file for hydroData")
        #print(img_url)
        
        try:
            response = requests.get(img_url)
            img_path = "./static/bulletin/hydro-temp"+str(idx)+".png"
            file = open(img_path, "wb")
            file.write(response.content)
            current_size = file.tell()
            file.close()
            
            if current_size > 69: #60 is one by one pixel png image 
                myTempimage = InlineImage(doc, image_descriptor="./static/bulletin/hydro-temp"+str(idx)+".png" , width=Mm(50))
                data["hydro_img"].append(myTempimage)
                idx = idx + 1
        except:
            #print("image error, empty ?")
            pass    

    try:
        doc.render(data)
        print("end rendering doc")
        doc.save("./static/bulletin/test.docx")
    except Exception as e:
        print(e)
        st.warning(e)

    output_bulletin =  "./static/bulletin/test.docx"

    with open(output_bulletin, "rb") as reportfile:
        st.download_button(
                label="Download report",
                data=reportfile,
                file_name=output_bulletin,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                icon=":material/download:",
            )

def reset_submitted():
    st.session_state.submitted = False
    
def download_report():
    return False

def clean_everything():
    print("Function to clean temporary files")
    return True

def record_submitted():
    display_form = False
    st.session_state.submitted = True
    try:
        with st.spinner("Wait for it...", show_time=True):
            #generate_report(data)
            generate_docx_report()
            clean_everything()
        st.success("Done!")
        st.stop()
        
    except Exception as e:
        st.warning(e)
    return False
            
def check_report_image_exists(filename,url_hint='',show_upload_form=True, img_width=200):
    try:
        if os.path.exists(filename):
            st.markdown(filename+" :white_check_mark:")
            st.image(filename, width=img_width)
            return filename
        else:
            st.markdown(filename+" :x:")
            st.markdown(url_hint)
            if show_upload_form:
                uploaded_file = st.file_uploader("Choose a file")
                if uploaded_file is not None:
                    b = uploaded_file.getvalue()
                    with open(filename, "wb") as f:
                        f.write(b)
                        st.text("Fichier enregistré !")
                        st.rerun()
                else:
                    return None
            else:
                return None
    except:
        st.text("Selectionnez la plage de données ... Image manquante...")
        return None


# ---------------------------------------------------------------------------------------------
# Test page
# ---------------------------------------------------------------------------------------------

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

############## 
# init data
##############

synthese_text= """<b>Faits marquants</b><br />Texte de synthèse en 5 ligne max. <br /><b>Info vannes</b><br />Texte à remplacer<br /><b>Prévisions</b><br />Texte previsions."""
precipitations_text= """Le cumul de précipitations de ce mois d’avril 2025 atteint 101 mm à l'échelle de la région, soit un excédent de 15 %. Un fort épisode de pluie s’est produit les 15 et 16 avril, après un début de mois relativement sec : il est tombé en 24 heures 47 mm à Ambérieu-en-Bugey (01), 135 mm à Barnas (07) et 109 mm à Termignon (73). """
synthese_hydro_text=""" La situation n’évolue pas beaucoup par rapport au mois de mars 2025 : l’hydraulicité est globalement faible à moyenne sur l'ensemble de la région, sauf dans les départements de la Haute-Loire et de l'Ardèche. On observe une hausse dans l’Ain et la Drôme."""
hauteur_eau_txt = """Texte sur la Hauteur d'eau"""
couranto_txt = """Texte jaugeages"""
temperature_txt="""Texte températures"""
temperature_data= [
    {"col1": "", "col2" : "Localisation", "col3": "Date", "col4": "Valeur"},
]

onde_txt = """Carte de situation ONDE"""
synthese_sout_txt="""Synthese eaux souterraines"""


#Selection période des données
today = datetime.datetime.now()        
today_1 = today -  relativedelta(months=1)
mois_1 = beginning_of_month (today_1)
mois_31 = end_of_month(today_1)


##############
# Main page
##############
st.set_page_config(layout="wide")
protect_by_password()
st.title("Generateur de rapport")

#selection des dates
date_donnees_range = st.date_input(
    "Selection des dates",
    (mois_1, mois_31),
    format="DD/MM/YYYY",
    #on_change=print_func,
)


#Load bulletins file
try:
    bulletins = toml.load("./templates/bulletins.toml") 

except Exception as e:
    print("Loading bulletins definition file failed : 2_Rapport.py l:321")
    print(e)
    st.error(e)

#selection du type de bulletin
type_bsh = st.selectbox(
    "Type de bulletin",
    bulletins,
    index=None,
    placeholder="Selectionnez le type de bulletin...",
    format_func=lambda x: bulletins[x]["name"]
)
st.write("You selected:", type_bsh)

display_form = (date_donnees_range and type_bsh)
if display_form:
    try:
        (date_donnees_range_start, date_donnees_range_end) = date_donnees_range
    except ValueError:
        print('Date selection not completed')
        display_form = False
        pass

if display_form : #and not st.session_state.submitted :

    preview = st.checkbox("Previsualiser les graphiques (long)", False)
    with st.spinner("Chargement du formulaire..."):
        
        with st.container():
            (datetime_donnees_range_start, datetime_donnees_range_end) = (datetime.datetime.strptime(str(date_donnees_range_start)+ " 00:00:00","%Y-%m-%d %H:%M:%S"), datetime.datetime.strptime(str(date_donnees_range_end)+" 23:59:59","%Y-%m-%d  %H:%M:%S"))
                
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Général", "Météorologie", "Hydrologie", "Température", "Communications externes"])

            with tab1:

                initial_txt = "DONNEES D'AVRIL 2025"
                if date_donnees_range_start:
                    initial_txt = "Données du "+date_donnees_range_start.strftime("%d/%m/%Y")+ " au "+date_donnees_range_end.strftime("%d/%m/%Y")
            
                date_donnees_val = st.text_input("Période des données", initial_txt)

                date_publication_val = st.date_input("Date de publication",datetime.date.today(),format="DD/MM/YYYY")
                
                # # Spawn a new Quill editor
                # st.text("Synthèse du rapport")
                # synthese_val = st_quill(value=synthese_text, placeholder='Synthèse du rapport', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
            with tab2:
                st.subheader("Prévisions météorologiques")
                try:
                    m_show_previs = bulletins[type_bsh]["pluvio_show_previs"]
                except:
                    m_show_previs = False

                showPrevis = st.checkbox("Afficher prévisions meteoblue", m_show_previs)
                if showPrevis:
                    #save meteoblue as images to be integrated into doc file
                    chrome_options = Options()  
                    chrome_options.add_argument("--headless")  
                    driver = webdriver.Chrome(options=chrome_options)

                    #meteoblue Bourg
                    img_path = './static/bulletin/PreviMeteoBlueBourg'+today.strftime("%Y%m%d")+'.png'
                    url = ' https://www.meteoblue.com/fr/weather/widget/daily/bourg-en-bresse_france_3031009?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light'  # Replace with your desired URL
                    
                    if not os.path.exists(img_path):
                        driver.get(url)
                        driver.get_screenshot_as_file(img_path)

                    #meteoblue Montrevel
                    img_path = './static/bulletin/PreviMeteoBlueMontrevel'+today.strftime("%Y%m%d")+'.png'
                    url = 'https://www.meteoblue.com/fr/weather/widget/daily/montrevel-en-bresse_france_2992050?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light'
                    if not os.path.exists(img_path):
                        driver.get(url)
                        driver.get_screenshot_as_file(img_path)

                    #meteoblue Pont de vaux
                    img_path = './static/bulletin/PreviMeteoBluePontDeVaux'+today.strftime("%Y%m%d")+'.png'
                    url = 'https://www.meteoblue.com/fr/weather/widget/daily/pont-de-vaux_france_2986227?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light'
                    if not os.path.exists(img_path):
                        driver.get(url)
                        driver.get_screenshot_as_file(img_path)

                    #driver.implicitly_wait(1)

                    # Navigate to the desired web page          
                    driver.close()

                    if preview :
                        meteoblue = st.container()
                        with meteoblue:
                            [col1,col2,col3] = st.columns(3)
                            #meteoblue Bourg en bresse
                            with col1:
                                img_path = './static/bulletin/PreviMeteoBlueBourg'+today.strftime("%Y%m%d")+'.png'
                                st.image(img_path)
                            
                            #meteoblue montrevel
                            with col2:
                                img_path = './static/bulletin/PreviMeteoBlueMontrevel'+today.strftime("%Y%m%d")+'.png'
                                st.image(img_path)
                            
                            #meteoblue Pont de vaux
                            with col3:
                                img_path = './static/bulletin/PreviMeteoBluePontDeVaux'+today.strftime("%Y%m%d")+'.png'
                                st.image(img_path)
                        

                st.subheader("Données météorologiques")
                
                pluvio_stations = getStationsPluvio()

                try:
                    #print("Default selected stations")
                    m_default_pluvio = []
                    for m_d_p in bulletins[type_bsh]["pluvio_stations"]:
                        m_default_pluvio.append(list(filter(lambda x : x["id"] == m_d_p, pluvio_stations))[0])
                except:
                    m_default_pluvio = []

                options = st.multiselect(
                    "Stations",
                    pluvio_stations,
                    default=m_default_pluvio,
                    max_selections=5,
                    format_func=lambda x: "Meteo " + x['name']
                )
                #st.write("You selected:", options)
                try:
                    m_pluvio_show_data = bulletins[type_bsh]["pluvio_show_data"]
                except:
                    m_pluvio_show_data = False
                showMeteoData = st.checkbox("Afficher données météo", m_pluvio_show_data)

                try:
                    m_pluvio_show_analysis = bulletins[type_bsh]["pluvio_show_analysis"]
                except:
                    m_pluvio_show_analysis = False
                showMeteoAnalyse = st.checkbox("Afficher analyse météo", m_pluvio_show_analysis)

                try:
                    m_pluvio_show_yearly_analysis = bulletins[type_bsh]["pluvio_show_yearly_analysis"]
                except:
                    m_pluvio_show_yearly_analysis = False
                showMeteoYearlyAnalyse = st.checkbox("Afficher analyse météo annuelle", m_pluvio_show_yearly_analysis)

                imgMeteoData = []
                if showMeteoData:
                    pluvio_data_types = pd.DataFrame(getDataTypePluvio())
                    #print(pluvio_data_types)
                    
                    for station in options:
                        station_name = station['name']

                        for idx, dt in pluvio_data_types.iterrows():

                            #graph pluvio
                            ds = date_donnees_range_start.strftime("%Y-%m-%d")
                            de = date_donnees_range_end.strftime("%Y-%m-%d")
                            url = "http://127.0.0.1:1111/api/graphChroniquePluvio?station_id="+str(station['id'])+"&date_start="+ds+"&date_end="+de+"&type_value_id="+str(dt["id"])+"&show_title=True&output=png"
                            print (url)
                            imgMeteoData.append(url)
                            if preview :
                                st.text(url)
                                try :
                                    data = requests.get(url)
                                    st.image(data.content, width=500)
                                except: 
                                    pass

                if showMeteoAnalyse:
                    for station in options:
                        station_name = station['name']

                        #graph meteo analysis
                        ds = date_donnees_range_start.strftime("%Y-%m-%d")
                        de = date_donnees_range_end.strftime("%Y-%m-%d")
                        url = "http://127.0.0.1:1111/api/graphAnalyseMeteo?station_id="+str(station['id'])+"&date_start="+ds+"&date_end="+de+"&show_title=True&output=png"
                        print (url)
                        imgMeteoData.append(url)
                        if preview :
                            st.text(url)
                            try :
                                data = requests.get(url)
                                st.image(data.content, width=500)
                            except: 
                                pass

                if showMeteoYearlyAnalyse:
                    for station in options:
                        station_name = station['name']

                        #graph meteo yearly analysis 
                        ds = date_donnees_range_start.strftime("%Y-%m-%d")
                        de = date_donnees_range_end.strftime("%Y-%m-%d")
                        year = date_donnees_range_start.strftime("%Y")

                        url = "http://127.0.0.1:1111/api/graphAnalyseAnnuelleMeteo?station_id="+str(station['id'])+"&year="+year+"&show_title=True&output=png"
                        print (url)
                        imgMeteoData.append(url)
                        if preview :
                            st.text(url)
                            try :
                                data = requests.get(url)
                                st.image(data.content, width=500)
                            except: 
                                pass

            with tab3:
                #selecteur de contenu
                try:
                    m_hydro_show_couranto = bulletins[type_bsh]["hydro_show_couranto"]
                except:
                    m_hydro_show_couranto = False
                showCouranto = st.checkbox("Afficher carte Couranto", m_hydro_show_couranto)
                
                if showCouranto and preview:
                    st.image('./static/bulletin/couranto.png')

                try:
                    m_hydro_show_onde = bulletins[type_bsh]["hydro_show_onde"]
                except:
                    m_hydro_show_onde = False
                showONDE = st.checkbox("Afficher carte ONDE", m_hydro_show_onde)
                if showONDE and preview:
                    #graph last situation onde
                    url = "http://127.0.0.1:1111/api/mapSituation" #?simulation_date="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                    print (url)
                    data = requests.get(url)
                    st.image(data.content, width=500)

                    #st.text("Texte ONDE")
                    #onde_txt = st_quill(value=onde_txt, placeholder='Texte Onde', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)

                st.subheader("Données hydrologie")
                
                hydro_stations = getStations()

                try:
                    #print("Default selected stations")
                    m_default_hydro = []
                    for m_d_p in bulletins[type_bsh]["hydro_stations"]:
                        m_default_hydro.append(list(filter(lambda x : x["id"] == m_d_p, hydro_stations))[0])
                except:
                    m_default_hydro = []
                options_hydro = st.multiselect(
                    "Stations",
                    hydro_stations,
                    default=m_default_hydro,
                    max_selections=10,
                    format_func=lambda x: "Hydro " + x['name'],
                    key="hydro_stations"
                )
                #st.write("You selected:", options)
                
                try:
                    m_hydro_show_data = bulletins[type_bsh]["hydro_show_data"]
                except:
                    m_hydro_show_data = False
                showHydroData = st.checkbox("Afficher données hydro", m_hydro_show_data)
                #showHydroAnalyse = st.checkbox("Afficher analyse hydro", True)
                #showMHydroYearlyAnalyse = st.checkbox("Afficher analyse hydro annuelle", False)

                imgHydroData = []

                if showHydroData:
                    hydro_data_types = pd.DataFrame(getDataTypeHydro())
                    #print(hydro_data_types)
                    
                    for station in options_hydro:
                        station_name = station['name']

                        for idx, dt in hydro_data_types.iterrows():
                            # #graph hydro
                            ds = date_donnees_range_start.strftime("%Y-%m-%d")
                            de = date_donnees_range_end.strftime("%Y-%m-%d")
                            url = "http://127.0.0.1:1111/api/graphChronique?station_id="+str(station['id'])+"&date_start="+ds+"&date_end="+de+"&type_value_id="+str(dt["id"])+"&show_title=True&output=png"
                            print (url)
                            imgHydroData.append(url)
                            if preview :
                                st.text(url)
                                try :
                                    data = requests.get(url)
                                    st.image(data.content, width=500)
                                except: 
                                    pass

                # if showHydroAnalyse:
                #     for station in options:
                #         station_name = station['name']

                #         # #graph hydro
                #         ds = date_donnees_range_start.strftime("%Y-%m-%d")
                #         de = date_donnees_range_end.strftime("%Y-%m-%d")
                #         url = "http://127.0.0.1:1111/api/graphAnalyseMeteo?station_id="+str(station['id'])+"&date_start="+ds+"&date_end="+de+"&show_title=True&output=png"
                #         print (url)
                #         imgMeteoData.append(url)
                #         st.text(url)
                #         if preview :
                #             try :
                #                 data = requests.get(url)
                #                 st.image(data.content, width=500)
                #             except: 
                #                 pass

                # if showMeteoYearlyAnalyse:
                #     for station in options:
                #         station_name = station['name']

                #         # #graph pluvio
                #         ds = date_donnees_range_start.strftime("%Y-%m-%d")
                #         de = date_donnees_range_end.strftime("%Y-%m-%d")
                #         year = date_donnees_range_start.strftime("%Y")

                #         url = "http://127.0.0.1:1111/api/graphAnalyseAnnuelleMeteo?station_id="+str(station['id'])+"&year="+year+"&show_title=True&output=png"
                #         print (url)
                #         imgMeteoData.append(url)
                #         st.text(url)
                #         if preview :
                #             try :
                #                 data = requests.get(url)
                #                 st.image(data.content, width=500)
                #             except: 
                #                 pass


                # st.text("Synthèse Hydrologie")
                # synthese_hydro_val = st_quill(value=synthese_hydro_text, placeholder='Texte hydrologie', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key='hydro_txt')
                
                # #graph cumulé hauteur eau
                # url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=[4,3,2,11,5,54,58]&type_value_id=4&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                # print (url)
                # data = requests.get(url)
                # st.image(data.content, width=500)
                
                
                # #graph cumulé debit eau
                # url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=[4,3,2,11,5,54,58]&type_value_id=5&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                # print (url)
                # data = requests.get(url)
                # st.image(data.content, width=500)
                
                # st.text("Texte Niveau d'eau")
                # hauteur_eau_txt = st_quill(value=hauteur_eau_txt, placeholder='Texte Niveau d\'eau', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            

                # #graph cumulé temperature
                # url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=[11,5,54,58]&type_value_id=7&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                # print (url)
                # data = requests.get(url)
                # st.image(data.content, width=500)

                # #compute temperature table
                # temperature_data = {}

                # url = "http://127.0.0.1:1111/api/statsChronique?stations=[11,5,54,58]&type_value_id=7&type_value_id=7&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")
                # #print (url)
                # stats_temp = requests.get(url).json()
                # pd_temperature_data = pd.read_json(io.StringIO(stats_temp))
                # stations = getStations()

                # pd_temperature_data["station_name"] = pd_temperature_data.apply(lambda x: m_extractStation(stations, x["station_id"])['name'], axis=1)
                # #st.dataframe(pd_temperature_data)
                # #suppress columns
                # pd_temperature_data = pd_temperature_data[["station_name","min","max","mean", "nb_computed"]] 
                # st.text("Tableau des températures")
                # st.dataframe(pd_temperature_data)
                
                # #title
                # temperature_data[0] = {"col1": "Station", "col2" : "Tmin (°C)" , "col3": "Tmax (°C)", "col4": "Tmoy (°C)", "col5": "Nb jours > 30°C"}
                
                # idx1 = 1
                # for row in pd_temperature_data.itertuples():
                #     temperature_data[idx1] = {"col1" : row.station_name, "col2" : round(row.min,2), "col3": round(row.max,2), "col4": round(row.mean,2), "col5": row.nb_computed}
                #     idx1 += 1
                    
                # temperature_data = [value for key, value in temperature_data.items()]

                # #print(temperature_data)
                # #raise Exception("sortie")

                #st.text("Texte Températures")
                #temperature_txt = st_quill(value=temperature_txt, placeholder='Texte Températures', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
            with tab4:
                #showEauxSout = st.checkbox("Afficher infos Eaux sout", False)
                imgTemperatureData = []

                
                hydro_stations = getStations()

                try:
                    #print("Default selected stations")
                    m_default_hydro_temp = []
                    for m_d_p in bulletins[type_bsh]["hydro_temp_stations"]:
                        m_default_hydro_temp.append(list(filter(lambda x : x["id"] == m_d_p, hydro_stations))[0])
                except:
                    m_default_hydro = []
                options_hydro_temp = st.multiselect(
                    "Stations",
                    hydro_stations,
                    default=m_default_hydro_temp,
                    max_selections=10,
                    format_func=lambda x: "Hydro " + x['name'],
                    key="hydro_temp_stations"
                )
                #st.write("You selected:", options)

                ds = date_donnees_range_start.strftime("%Y-%m-%d")
                de = date_donnees_range_end.strftime("%Y-%m-%d")
                        

                stations_temp_ids = ""
                for station in options_hydro_temp:
                    if stations_temp_ids != "":
                        stations_temp_ids = stations_temp_ids + ","

                    stations_temp_ids = stations_temp_ids + str(station["id"])

                #graph cumulé temperature
                url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=["+stations_temp_ids+"]&type_value_id=7&date_start="+ds+"&date_end="+de+"&output=png"
                imgTemperatureData.append(url)
                if preview :
                    st.text(url)
                    try :
                        data = requests.get(url)
                        st.image(data.content, width=500)
                    except: 
                        pass
                # print (url)

                
                # data = requests.get(url)
                # st.image(data.content, width=500)

                #compute temperature table
                temperature_data = {}

                url = "http://127.0.0.1:1111/api/statsChronique?stations=["+stations_temp_ids+"]&type_value_id=7&type_value_id=7&date_start="+ds+"&date_end="+de
                print (url)
                stats_temp = requests.get(url).json()
                #st.text(stats_temp)
                
                try:

                    pd_temperature_data =pd.read_json(io.StringIO(stats_temp))
                    stations = getStations()

                    pd_temperature_data["station_name"] = pd_temperature_data.apply(lambda x: m_extractStation(stations, x["station_id"])['name'], axis=1)
                    #st.dataframe(pd_temperature_data)
                    #suppress columns
                    pd_temperature_data = pd_temperature_data[["station_name","min","max","mean", "nb_computed"]] 
                    st.text("Tableau des températures")
                    st.dataframe(pd_temperature_data)
                except : 
                    pd_temperature_data = None
                    pass
                
                #title
                #temperature_data[0] = {"col1": "Station", "col2" : "Tmin (°C)" , "col3": "Tmax (°C)", "col4": "Tmoy (°C)", "col5": "Nb jours > 30°C"}
                #idx1 = 1

                idx1 = 0
                if pd_temperature_data is not None:
                    for row in pd_temperature_data.itertuples():
                        # row.nb_computed -  nb_computed = [nb_jours_sup_30, nb_jours_inf_0, nb_jours_dce_0, nb_jours_dce_1, nb_jours_dce_2, nb_jours_dce_3, nb_jours_dce_4]

                        temperature_data[idx1] = {"station_name" : row.station_name, "tmin" : round(row.min,2), "tmax": round(row.max,2), "tmoy": round(row.mean,2), 
                                                "nb_jours_sup_30": row.nb_computed[0],
                                                "nb_jours_inf_0": row.nb_computed[1],
                                                "nb_jours_dce_0": row.nb_computed[2],
                                                "nb_jours_dce_1": row.nb_computed[3],
                                                "nb_jours_dce_2": row.nb_computed[4],
                                                "nb_jours_dce_3": row.nb_computed[5],
                                                "nb_jours_dce_4": row.nb_computed[6]}
                        idx1 += 1
                        
                    temperature_data = [value for key, value in temperature_data.items()]
     
                
            with tab5:
                try:
                    m_show_external_communications = bulletins[type_bsh]["show_external_communications"]
                except:
                    m_show_external_communications = False
                showCommunications = st.checkbox("Afficher les communications externes", m_show_external_communications)
                
                #Get communications externes from myliaq
                comm_temp = requests.get("http://127.0.0.1:1111/api/communication").json()
                #print(json.dumps(comm_temp))
                #communications_externes = pd.read_json(io.StringIO(json.dumps(comm_temp)))
                #print(communications_externes)
                communications_externes = pd.read_json(io.StringIO(json.dumps(comm_temp)))
                
                #filter monthly data
                ds = datetime_donnees_range_start+relativedelta(months=-1)
                #d_e = datetime_donnees_range_end+relativedelta(months=+1)
                m_datedebut =  int(round(ds.timestamp()*1000.0))  #timestamp in milliseconds
                #m_datefin = int(round(datetime_donnees_range_end.timestamp()*1000.0))  #timestamp in milliseconds

                communications_externes = communications_externes[communications_externes['dateDebut'] >= m_datedebut ]
                #try:
                #    communications_externes = communications_externes[communications_externes['dateFin'] <= m_datefin ]
                #except KeyError:
                #    pass
                
                #this cause the template to crash !
                communications_externes['comment'] = communications_externes['comment'].map(lambda x: remove_tags(x))
                communications_externes = communications_externes.replace({float('nan'): None})
                communication_data = []
                for row in communications_externes.itertuples():
                    ##['id', 'title', 'subtitle', 'idCategory', 'comment', 'author', 'link','authorization', 'status', 'updateDate', 'levelContent', 'dateDebut','dateFin', 'login', 'cmsDocument', 'hasTrad', 'cmsMessages','cmsFollowers', 'cmsTrads', 'cmsLinked'
                    communication_data.append({"id": row.id, "title": row.title, "subtitle": row.subtitle, 
                                               "comment": row.comment,
                                               "author": row.author,
                                               "link": row.link,
                                               "status": row.status,
                                               "updateDate": datetime.datetime.fromtimestamp(row.updateDate/1000.0).strftime("%Y-%m-%d %H:%M:%S") if row.updateDate else None,
                                               "dateDebut": datetime.datetime.fromtimestamp(row.dateDebut/1000.0).strftime("%Y-%m-%d %H:%M:%S") if row.dateDebut else None,
                                               "dateFin": datetime.datetime.fromtimestamp(row.dateFin/1000.0).strftime("%Y-%m-%d %H:%M:%S") if row.dateFin else None
                                               })
                communications_externes = communication_data
                st.dataframe(communications_externes)
                
                if preview:
                    #display json
                    for line in communications_externes:
                        st.header(str(line["id"])+" "+line["title"])
                        st.html("<a href=\""+line["link"]+"\">Lien</a>")
                
            
            submitted = st.button("Generer le Rapport", on_click=record_submitted)

            
