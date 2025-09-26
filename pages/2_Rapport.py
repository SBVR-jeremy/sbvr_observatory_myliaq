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

from datetime import datetime, date, timezone
from dateutil.relativedelta import *

#import altair as alt

#from PIL import Image

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.options import Options  


################
#PDF export template


import pdfkit
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

from pdfkit.api import configuration

#This need to be changed on production !!!
wkhtml_path = pdfkit.configuration(wkhtmltopdf = "C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")  #by using configuration you can add path value.

#import locale
#locale.setlocale(locale.LC_TIME, "fr_FR")
from babel.dates import format_date, format_datetime, format_time

import requests
import os

from tools.utility import *
from tools.streamlit_utility import *
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

################
if False : 
    chrome_options = Options()  
    chrome_options.add_argument("--headless")  

    driver = webdriver.Chrome(options=chrome_options)

    driver.implicitly_wait(10)

    # Navigate to the desired web page
    #meteoblue Bourg
    url = ' https://www.meteoblue.com/en/weather/widget/daily/bourg-en-bresse_france_3031009?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light'  # Replace with your desired URL
    driver.get(url)
    driver.get_screenshot_as_file('./static/PreviMeteoBlueBourg.png')

    #meteoblue Montrevel
    url = 'https://www.meteoblue.com/en/weather/widget/daily/montrevel-en-bresse_france_2992050?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light'
    driver.get(url)
    driver.get_screenshot_as_file('./static/PreviMeteoBlueMontrevel.png')

    #meteoblue Pont de vaux
    url = 'https://www.meteoblue.com/en/weather/widget/daily/pont-de-vaux_france_2986227?geoloc=fixed&days=7&tempunit=CELSIUS&windunit=KILOMETER_PER_HOUR&precipunit=MILLIMETER&coloured=coloured&pictoicon=1&maxtemperature=1&mintemperature=1&windspeed=1&windgust=0&winddirection=0&uv=0&humidity=0&precipitation=1&precipitationprobability=1&spot=1&pressure=0&layout=light'
    driver.get(url)
    driver.get_screenshot_as_file('./static/PreviMeteoBluePontDeVaux.png')
                    
    driver.close()


    st.text("Capture images of wheather widget OK")

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

#DEPRECATED (type_value turned to type_value_id...)
def save_graph(stations, type_value, date_start, date_end, graph_name, display_graph=True, draw_seuils=False):
    domain = [ "Majornas", "Montagnat","Saone à Macon","Saint Julien sur R.","Viriat","Baudières","Cras"]
    range_ = ['#003A7D','#008DFF','#FF73B6','#C701FF','#4ECB8D','#FF9D3A','#F9E858','#D83034']
    
    #convert date_start and date_end to datetime UTC aware!
    time_start = datetime.datetime.min.time()
    time_start = time_start.replace(tzinfo=timezone.utc)
    
    time_end = datetime.datetime.max.time()
    time_end = time_end.replace(tzinfo=timezone.utc)


    #returns  'date_start 00:00:00' and 'date_end 23:59:59'
    n_date_start = datetime.datetime.combine(date_start,time_start)
    n_date_end = datetime.datetime.combine(date_end,time_end)

    #timestamp in milliseconds
    ts_start = int(round(n_date_start.timestamp()*1000.0)) 
    ts_end = int(round(n_date_end.timestamp()*1000.0))

    m_chart = None
    for station_id in stations:
        samples = m_getAllSamplesAnalyse(station_id,type_value,start_date=ts_start,end_date=ts_end)
        #print(samples)
        #addcolor
        samples["station_name"] = stations[station_id]

        c = alt.Chart(samples).mark_line(interpolate='monotone',point=True).transform_calculate(
            combined_tooltip = "datum.numeric_value"
        ).encode(
            alt.X('timestamp:T', axis = alt.Axis(tickCount="day", ticks = True, title = '', 
                                                        #labelAngle=-75,
                                                        labelExpr="[timeFormat(datum.value, '%d-%m-%Y'),  timeFormat(datum.value, '%d') == '00' ? timeFormat(datum.value, '%d-%m-%Y') : '', timeFormat(datum.value, '%m') == '01' ? timeFormat(datum.value, '%Y') : '']")),
            alt.Y( 'numeric_value:Q', axis=alt.Axis(labels=True,title='')),
            #alt.Color('station_id:N',legend=alt.Legend(title='Données')),
            #alt.Color('station_id:N',legend=None),
            #opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
            #color=alt.value(colors[station_id]),
            color=alt.Color('station_name').scale(domain=domain, range=range_),
            tooltip=[
                alt.Tooltip("timestamp:T",  format="%Y-%m-%d@%H:%M:%S", title="Date (local)"), 
                alt.Tooltip("combined_tooltip:N", title="Valeur"), 
                #alt.Tooltip("ust:N", title="Variable")
            ]
        #).add_selection(
        #    selection
        ).properties(
            height=600,
            width=800
        ).interactive()

        if m_chart is None :
            m_chart = c
        else:
            m_chart = m_chart + c

        #recup des seuils
        if draw_seuils :
            seuils = m_getAllSeuils(station_id,type_value)
            #print(seuils)
    
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
  
    if display_graph :
            st.altair_chart(m_chart, use_container_width=True)   
    m_chart.save(graph_name, ppi=200)

def generate_report(data):
    
    if data is not None:
        type_bsh = data["type_bsh"]
        date_publication_val = data["date_publication_val"] 
        
    #format date...
    data["date_publication"]=format_date(date_publication_val,format='long', locale='fr')

    #add media folder
    data["media_folder"] = os.getcwd()+"\\static\\bulletin"
    
    print("################")    
    #print(data)
    
    env = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
    template_bulletin = "./templates/BMSH.html"
    output_bulletin = "./static/bulletin/BMSH-SBVR-{}.pdf".format(date_publication_val.strftime("%Y-%m"))

    if type_bsh == "Hebdomadaire":
        template_bulletin = "./templates/BHSH.html"
        output_bulletin =  "./static/bulletin/BHSH-SBVR-{}.pdf".format(date_publication_val.strftime("%Y-%m-%d"))

    template = env.get_template(template_bulletin)
    
    html = template.render(
        data=data
    )

    #st.text(html)
    options = { 
        'page-size': 'A4',
        #'page-height': '1109px',
        #'page-width': '793px',
        'margin-top': '0',
        'margin-right': '0',
        'margin-bottom': '0',
        'margin-left': '0',
        'dpi': '200',
        'enable-local-file-access': '',
        'footer-right': '[page] of [topage]' 
    }  

    pdf = pdfkit.from_string(html, output_bulletin, configuration = wkhtml_path, options=options)

    st.text("Generate PDF OK "+datetime.datetime.today().strftime('%d/%m/%Y, %H:%M:%S'))
    
    pdf_viewer(output_bulletin, width=795, pages_vertical_spacing=5)

def reset_submitted():
    st.session_state.submitted = False

def record_submitted():
    display_form = False
    st.session_state.submitted = True
    data  = dict()
    data["type_bsh"] = type_bsh
    data["date_donnees_val"] = date_donnees_val
    data["date_publication_val"] = date_publication_val
    data["date_donnees_range_start"] = date_donnees_range_start
    data["date_donnees_range_end"] = date_donnees_range_end
    data["synthese_val"] = synthese_val
    data["precipitations_val"] = precipitations_val
    data["synthese_hydro_val"] = synthese_hydro_val
    data["hauteur_eau_txt"] = hauteur_eau_txt
    data["showCouranto"] = showCouranto
    data["couranto_txt"] = couranto_txt
    data["showONDE"] = showONDE
    data["onde_txt"] = onde_txt
    data["temperature_txt"] = temperature_txt
    data["temperature_data"] = temperature_data
    data["showEauxSout"] = showEauxSout
    data["synthese_sout_val"] = synthese_sout_txt
    data["communications_externes"] = communications_externes
    #data[""] = 
    #data[""] = 

    try:
        with st.spinner("Wait for it...", show_time=True):
            generate_report(data)
        st.success("Done!")

        output_bulletin = "./static/bulletin/BMSH-SBVR-{}.pdf".format(date_publication_val.strftime("%Y-%m"))

        if type_bsh == "Hebdomadaire":
            output_bulletin =  "./static/bulletin/BHSH-SBVR-{}.pdf".format(date_publication_val.strftime("%Y-%m-%d"))

        with open(output_bulletin, "rb") as pdffile:
            st.download_button(
                    label="Download PDF",
                    data=pdffile,
                    file_name=output_bulletin,
                    mime="application/pdf",
                    icon=":material/download:",
                )

    except Exception as e:
        st.warning(e)
            
def check_report_image_exists(filename,url_hint,show_upload_form=True, img_width=200):
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

st.set_page_config(layout="wide")
protect_by_password()
st.title("Generateur de rapport")

synthese_text= """<b>Fait marquant</b><br /> Texte de synthèse en 5 ligne max."""
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

#selecteur de contenu
showCouranto = st.checkbox("Afficher carte Couranto", False)
showONDE = st.checkbox("Afficher carte ONDE", False)
showEauxSout = st.checkbox("Afficher infos Eaux sout", False)

#selection des dates
date_donnees_range = st.date_input(
    "Selection des dates",
    (mois_1, mois_31),
    format="DD/MM/YYYY",
    #on_change=print_func,
)

#selection du type de bulletin
type_bsh = st.selectbox(
    "Type de bulletin",
    ("Hebdomadaire", "Mensuel", "Test"),
    index=None,
    placeholder="Selectionnez le type de bulletin...",
)

display_form = (date_donnees_range and type_bsh)
if display_form:
    try:
        (date_donnees_range_start, date_donnees_range_end) = date_donnees_range
    except ValueError:
        print('Date selection not completed')
        display_form = False
        pass

if display_form and st.session_state.submitted :
    st.button("Re-generate form", on_click=reset_submitted)

if display_form and not st.session_state.submitted :

    with st.spinner("Chargement du formulaire..."):
        with st.form("report_form", enter_to_submit=False):
            (datetime_donnees_range_start, datetime_donnees_range_end) = (datetime.datetime.strptime(str(date_donnees_range_start)+ " 00:00:00","%Y-%m-%d %H:%M:%S"), datetime.datetime.strptime(str(date_donnees_range_end)+" 23:59:59","%Y-%m-%d  %H:%M:%S"))
                
            tab1, tab2, tab3, tab4 = st.tabs(["Général", "Météorologie", "Hydrologie", "Eaux souterraines"])

            with tab1:

                initial_txt = "DONNEES D'AVRIL 2025"
                if date_donnees_range_start:
                    initial_txt = "Données du "+date_donnees_range_start.strftime("%d/%m/%Y")+ " au "+date_donnees_range_end.strftime("%d/%m/%Y")
            
                date_donnees_val = st.text_input("Libelle Période des données", initial_txt)
                

                date_publication_val = st.date_input("Date de publication",datetime.date.today(),format="DD/MM/YYYY")
                # Spawn a new Quill editor
                st.text("Synthèse du rapport")
                synthese_val = st_quill(value=synthese_text, placeholder='Synthèse du rapport', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
            
            with tab2:
                
                try:
                    st.text("Station Ceyzeriat")
                    station_id = 21 #station ceyzeriat SPAC
                    report_year = date_donnees_range_start.year
                    url = "http://127.0.0.1:1111/api/graphAnalyseAnnuelleMeteo?station_id="+str(station_id)+"&year="+str(report_year)+"&show_title=true" #&date=...
                    print (url)
                    data = requests.get(url).json()
                    st.vega_lite_chart(data, use_container_width=True)
                    url = "http://127.0.0.1:1111/api/graphAnalyseMeteo?station_id="+str(station_id)+"&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&show_title=true" #&date=...
                    print (url)
                    data = requests.get(url).json()
                    st.vega_lite_chart(data, use_container_width=True)


                    st.text("Station St Julien")
                    station_id = 28 #station St julien
                    url = "http://127.0.0.1:1111/api/graphAnalyseMeteo?station_id="+str(station_id)+"&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&show_title=true" #&date=...
                    print (url)
                    data = requests.get(url).json()
                    st.vega_lite_chart(data, use_container_width=True)
                    
                except Exception as e:
                    st.text("No graph Analyse meteo")
                    raise e
                
                st.text("Texte précipitations")
                precipitations_val = st_quill(value=precipitations_text, placeholder='Texte précipitations', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)

            with tab3:    
                st.text("Synthèse Hydrologie")
                synthese_hydro_val = st_quill(value=synthese_hydro_text, placeholder='Texte hydrologie', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key='hydro_txt')
                
                #graph cumulé hauteur eau
                url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=[4,3,2,11,5,54]&type_value_id=4&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                print (url)
                data = requests.get(url)
                st.image(data.content, width=500)
                
                
                #graph cumulé debit eau
                url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=[4,3,2,11,5,54]&type_value_id=5&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                print (url)
                data = requests.get(url)
                st.image(data.content, width=500)
                
                st.text("Texte Niveau d'eau")
                hauteur_eau_txt = st_quill(value=hauteur_eau_txt, placeholder='Texte Niveau d\'eau', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
                if showCouranto:
                    st.text("Texte Couranto")
                    couranto_txt = st_quill(value=couranto_txt, placeholder='Texte Couranto', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
                

                #graph cumulé temperature
                url = "http://127.0.0.1:1111/api/graphCumulatedChronique?stations=[11,5,54]&type_value_id=7&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                print (url)
                data = requests.get(url)
                st.image(data.content, width=500)

                #compute temperature table
                temperature_data = {}

                url = "http://127.0.0.1:1111/api/statsChronique?stations=[11,5,54]&type_value_id=7&type_value_id=7&date_start="+date_donnees_range_start.strftime("%Y-%m-%d")+"&date_end="+date_donnees_range_end.strftime("%Y-%m-%d")
                #print (url)
                stats_temp = requests.get(url).json()
                pd_temperature_data = pd.read_json(stats_temp)
                stations = getStations()

                pd_temperature_data["station_name"] = pd_temperature_data.apply(lambda x: m_extractStation(stations, x["station_id"])['name'], axis=1)
                #st.dataframe(pd_temperature_data)
                #suppress columns
                pd_temperature_data = pd_temperature_data[["station_name","min","max","mean", "nb_computed"]] 
                st.text("Tableau des températures")
                st.dataframe(pd_temperature_data)
                
                #title
                temperature_data[0] = {"col1": "Station", "col2" : "Tmin (°C)" , "col3": "Tmax (°C)", "col4": "Tmoy (°C)", "col5": "Nb jours > 30°C"}
                
                idx1 = 1
                for row in pd_temperature_data.itertuples():
                    temperature_data[idx1] = {"col1" : row.station_name, "col2" : round(row.min,2), "col3": round(row.max,2), "col4": round(row.mean,2), "col5": row.nb_computed}
                    idx1 += 1
                    
                temperature_data = [value for key, value in temperature_data.items()]

                #print(temperature_data)
                #raise Exception("sortie")

                st.text("Texte Températures")
                temperature_txt = st_quill(value=temperature_txt, placeholder='Texte Températures', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
            with tab4: 
                if showONDE:
                    #graph last situation onde
                    url = "http://127.0.0.1:1111/api/mapSituation" #?simulation_date="+date_donnees_range_end.strftime("%Y-%m-%d")+"&output=png"
                    print (url)
                    data = requests.get(url)
                    st.image(data.content, width=500)

                    st.text("Texte ONDE")
                    onde_txt = st_quill(value=onde_txt, placeholder='Texte Onde', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)

                if showEauxSout:
                    st.text("Texte Eaux Souterraines")
                    synthese_sout_txt = st_quill(value=synthese_sout_txt, placeholder='Texte Eaux souterraines', html=True, toolbar=None, history=True, preserve_whitespace=True, readonly=False, key=None)
            
                #Get communications externes from myliaq
                communications_externes = requests.get("http://127.0.0.1:1111/api/communication").json()
                #filter august data
                
                m_datedebut =  int(round(datetime_donnees_range_start.timestamp()*1000.0))  #timestamp in milliseconds
                m_datefin = int(round(datetime_donnees_range_end.timestamp()*1000.0))  #timestamp in milliseconds
                communications_externes = list(filter(lambda x: x['dateDebut'] >= m_datedebut, communications_externes))
                communications_externes = list(filter(lambda x: x['dateFin'] <= m_datefin, communications_externes))
                st.dataframe(communications_externes)
                # #display json
                # for line in communications_externes:
                #     st.header(str(line["id"])+" "+line["title"])
                #     st.html("<a href=\""+line["link"]+"\">Lien</a>")
                # Every form must have a submit button.
            
            submitted = st.form_submit_button("Generer le PDF", on_click=record_submitted)



# #Test affichage images
# #pluvio mensuelle
# try:
#     (date_donnees_range_start, date_donnees_range_end) = date_donnees_range
#     filename = "./static/bulletin/MeteoPluvio-"+date_donnees_range_start.strftime("%Y-%m")+".png"
#     pluvio_mensuelle = check_report_image_exists(filename, "https://www.auvergne-rhone-alpes.developpement-durable.gouv.fr/bulletins-de-situation-hydrologique-a26946.html" )
#     display_form = display_form and (pluvio_mensuelle is not None)
# except:
#     st.text("Selectionnez la plage de données ... Image manquante...")

# #pluvio Ceyze annuelle
# try:
#     (date_donnees_range_start, date_donnees_range_end) = date_donnees_range
#     filename = "./static/bulletin/MeteoCeyzeriat-"+date_donnees_range_start.strftime("%Y")+".png"
#     meteo_ceyze_annuelle = check_report_image_exists(filename, "https://www.mellifere.com/climat/station-ceyzeriat.php", img_width=600 )
#     display_form = display_form and (meteo_ceyze_annuelle is not None)
# except:
#     st.text("Selectionnez la plage de données ... Image manquante...")

#all images are ok, display form 
#limit height of wysiwyg editor
# st.markdown("""
# <style>
# .element-container:has(> iframe) {
#   height: 150px;
#   overflow-y: scroll;
#   overflow-x: hidden;
# }
# </style>
# """, unsafe_allow_html=True)

# # Temperatures 30j
# type_value = '°C'
# nb_days = 30
# date_start = datetime.datetime.now(timezone.utc) - timedelta(days=nb_days)
# date_end = datetime.datetime.now(timezone.utc)
# graph_name = './static/chartWaterTemperature30.png'
# stations = dict()
# stations[11] = "Viriat"
# stations[5] = "Baudières"
# stations[54] = "Cras"
# #save_graph(stations, stype_value, date_start, date_end, graph_name)


# stations = dict()
# #stations[4] = "Majornas"
# #stations[3] = "Montagnat"
# stations[1] = "Saone à Macon"
# #stations[2] = "Saint Julien sur R."
# #stations[11] = "Viriat"
# #stations[5] = "Baudières"
# stations[54] = "Cras"

# stations_color = dict()
# stations_color[4] = 'red'
# stations_color[3] = 'steelblue'
# stations_color[1] = 'chartreuse'
# stations_color[2] = '#F4D03F'
# stations_color[11] = '#D35400'
# stations_color[5] = '#7D3C98'
# stations_color[54] = '#FF0000'

# #stations_color = ['red', 'green','red', 'green','red', 'green']


# # Hauteur d'eau, 30j
# type_value = 'm'
# nb_days = 30
# graph_name = './static/chartWaterHeight30.png'

# #save_graph(stations, stations_color, type_value, nb_days, graph_name)

 
# # Hauteur d'eau, 7j
# type_value = 'm'
# nb_days = 7
# graph_name = './static/chartWaterHeight7.png'

# #save_graph(stations, stations_color, type_value, nb_days, graph_name)