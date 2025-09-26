#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""graphtools.py: Contains usefuls function to generate altair graphs"""

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

import pandas as pd
import altair as alt
from datetime import datetime, date, timezone
import traceback

from tools.queries import *
from tools.utility import *


TEMPERATURE_ID = 4
PLUIE_ID = 1

# ---------------------------------------------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------------------------------------------
def generateAlerteGraph(station_id, type_value_id, ts_start, ts_end):
    zones = pd.DataFrame(columns=["station","seuil","isOverrunThreshold", "min", "max", "value","color"])
    zones = m_getAllZones(zones, station_id, type_value_id)
    #print(zones)
    type_values = getDataTypeHydro()
    type_value = m_extractStation(type_values,type_value_id)

    try:
        unit_symbol = type_value["unit"] if type_value is not None else "Unit not Found"
    except KeyError:
        unit_symbol = '' #This type_value has no unit

    m_width=200
    if zones.shape[0] > 0:
        #print(zones)
        chart = (
            alt.Chart(zones, width=m_width)
            .mark_bar()
            .transform_calculate(
                v_min= 'round(datum.min * 100) / 100',
                v_max='round(datum.max * 100) / 100',
                combined_tooltip = "datum.v_min + '"+ unit_symbol + " <= ' + datum.seuil + ' < ' + datum.v_max + '" + unit_symbol +  "'"
            )
            .encode(
                x=alt.X("station:N", title=""),
                y=alt.Y("value:Q", title=unit_symbol),
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


    stations = getStations()
    my_station = m_extractStation(stations,station_id)
    station_name = my_station['name'] if my_station is not None else "Station not Found"

    samples = m_getAllSamplesAnalyse(station_id,type_value_id,start_date=ts_start,end_date=ts_end)
    annotations_df = pd.DataFrame(columns=["index", "value", "marker", "description"])

    #st.line_chart(samples, x='timestamp', y='numeric_value')
    if samples.shape[0] != 0:
        last_record = samples.tail(1)
        #print('----')
        #print(last_record)
        annotations_df.loc[-1] = [station_id, "{}".format(round(last_record.numeric_value.item(),3)), "◀{}{}▶ ".format(round(last_record.numeric_value.item(),3),unit_symbol), "MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))]
        #annotations_df.loc[-1] = [stations[station_id],2, "◀{}m ".format(round(last_record.numeric_value.item(),3)), "MAJ ({})".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))]
        annotations_df.index = annotations_df.index + 1
        annotations_df = annotations_df.sort_index()
        #append MAJ date to station_name
        station_name = [station_name, "{}".format(utc2local(last_record.timestamp.item()).strftime("%d/%m/%Y @ %H:%M"))]
    
    annotation_layer = (
        alt.Chart(annotations_df, width=m_width)
        .mark_text(size=20, dx=-50, dy=0, align="left")
        .encode(
            x=alt.X("index:N", title=station_name, axis=alt.Axis(labelExpr="")), 
            y=alt.Y("value:Q", title=""), 
            text="marker", 
            color=alt.Color("value:Q", title="",legend=None).scale(domain=domainT, range=rangeT_), 
            tooltip="description")
    )


    
    if zones.shape[0] > 0:
        combined_chart = chart + annotation_layer
    else :
        combined_chart = annotation_layer
    
    return combined_chart

def generateCumulatedChroniqueGraph(stations_id, type_value_id, date_start, date_end, showTitle=True, draw_seuils = True):
    try:

        #construct domain and range base on stations_id
        domain = []
        range_ = []
        
        for station_idx in stations_id:
            station = stations_id[station_idx]
            domain.append(station["title"])
            range_.append(station["color"])


        #convert date_start and date_end to datetime UTC aware!
        time_start = datetime.datetime.min.time()
        time_start = time_start.replace(tzinfo=timezone.utc)
        
        time_end = datetime.datetime.max.time()
        time_end = time_end.replace(tzinfo=timezone.utc)

        #
        date_start = datetime.datetime.strptime(date_start, '%Y-%m-%d').date()
        date_end = datetime.datetime.strptime(date_end, '%Y-%m-%d').date()

        #returns  'date_start 00:00:00' and 'date_end 23:59:59'
        n_date_start = datetime.datetime.combine(date_start,time_start)
        n_date_end = datetime.datetime.combine(date_end,time_end)

        #timestamp in milliseconds
        ts_start = int(round(n_date_start.timestamp()*1000.0)) 
        ts_end = int(round(n_date_end.timestamp()*1000.0))

        type_values = getDataTypeHydro()
        type_value = m_extractStation(type_values,type_value_id)

        try:
            unit_symbol = type_value["unit"] if type_value is not None else "Unit not Found"
        except KeyError:
            unit_symbol = '' #This type_value has no unit

        m_chart = None

        #print("loop")
        for station_id in stations_id:
            #print (station_id)
            samples = m_getAllSamplesAnalyse(int(station_id),type_value_id,start_date=ts_start,end_date=ts_end)
            #print(samples.head(10))
            
            #addcolor
            samples["station_name"] = stations_id[station_id]["title"]

            if not showTitle:
                station_name = None
                unit_symbol_y= ''
            else:
                unit_symbol_y=unit_symbol

            c = alt.Chart(samples).mark_line(interpolate='monotone',point=True).transform_calculate(
                combined_tooltip = "datum.numeric_value"
            ).encode(
                alt.X('timestamp:T', axis = alt.Axis(tickCount="day", ticks = True, title = '', 
                                                            #labelAngle=-75,
                                                            labelExpr="[timeFormat(datum.value, '%d-%m-%Y'),  timeFormat(datum.value, '%d') == '00' ? timeFormat(datum.value, '%d-%m-%Y') : '', timeFormat(datum.value, '%m') == '01' ? timeFormat(datum.value, '%Y') : '']")),
                alt.Y( 'numeric_value:Q', axis=alt.Axis(labels=True,title=unit_symbol_y)),
                #alt.Color('station_id:N',legend=alt.Legend(title='Données')),
                #alt.Color('station_id:N',legend=None),
                #opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
                #color=alt.value(colors[station_id]),
                color=alt.Color('station_name', title='Station').scale(domain=domain, range=range_),
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
                seuils = m_getAllSeuils(station_id,type_value_id)
                #print(seuils)
                domain_ = list(seuils['name']) 
                #print(domain_)
                try:
                    range_ = list(seuils['htmlColor'])
                    range_ = ['black' if str(x)=='nan' else x for x in range_] #replace NaN values
                except :
                    range_ = []
                    for i in range(0,len(domain_)): range_.append("black")

                #print(range_)
                m_s = alt.Chart(seuils).mark_rule().encode(y='value', color=alt.Color("name:N", title="", legend=None, scale=alt.Scale(domain=domain_, range=range_)))
                m_t = alt.Chart(seuils).mark_text().encode(y='value', text='name:N')
                m_chart =  m_s + m_t + m_chart
        

        return m_chart
    except Exception as e:
        print(e)
        return None

def generateChroniqueGraph(station_id, type_value_id, ts_start, ts_end, showTitle=True):
    try:

        samples = m_getAllSamplesAnalyse(station_id, type_value_id,start_date=ts_start,end_date=ts_end)
        #print(samples.head(10))
        
        #st.line_chart(samples, x='timestamp', y='numeric_value')
        if samples.shape[0] == 0:
            return

        stations = getStations()
        my_station = m_extractStation(stations,station_id)
        station_name = my_station['name'] if my_station is not None else "Station not Found"

        type_values = getDataTypeHydro()
        type_value = m_extractStation(type_values,type_value_id)

        try:
            unit_symbol = type_value["unit"] if type_value is not None else "Unit not Found"
        except KeyError:
            unit_symbol = '' #This type_value has no unit

        if unit_symbol == 'm':
            #zoom on y axis - 10cm over and above
            y_min = samples.min(numeric_only=True).numeric_value - 0.1
            y_max = samples.max(numeric_only=True).numeric_value + 0.1

            m_domain = [y_min, y_max]
        else:
            #zoom on y axis - 0.5° ove and above
            y_min = samples.min(numeric_only=True).numeric_value - 0.5
            y_max = samples.max(numeric_only=True).numeric_value + 0.5

            m_domain = [y_min, y_max]
        
        if not showTitle:
            station_name = None
            unit_symbol_y= ''
        else:
            unit_symbol_y=unit_symbol

        #print("design graph")
        c = alt.Chart(samples).mark_line(interpolate='monotone',point=True).transform_calculate(
            combined_tooltip = "datum.numeric_value"
        ).encode(
            alt.X('timestamp:T', axis = alt.Axis(tickCount="hour", ticks = True, title = station_name, 
                                                        #labelAngle=-75,
                                                        labelExpr="[timeFormat(datum.value, '%H:%M'),  timeFormat(datum.value, '%H') == '00' ? timeFormat(datum.value, '%d-%m-%Y') : '', timeFormat(datum.value, '%m') == '01' ? timeFormat(datum.value, '%Y') : '']")),
            alt.Y( 'numeric_value:Q', axis=alt.Axis(labels=True,title=unit_symbol_y), scale=alt.Scale(domain=m_domain)),
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

        m_chart = c
        
        # #recup des seuils
        seuils = m_getAllSeuils(station_id, type_value_id)
        #print(seuils)
        if seuils.shape[0] > 0:
            #print(seuils)
            domain_ = list(seuils['name']) 
            #print(domain_)
            try:
                range_ = list(seuils['htmlColor'])
                range_ = ['black' if str(x)=='nan' else x for x in range_] #replace NaN values
            except :
                range_ = []
                for i in range(0,len(domain_)): range_.append("black")

            #print(range_)
            m_s = alt.Chart(seuils).mark_rule().encode(y='value', color=alt.Color("name:N", title="", legend=None, scale=alt.Scale(domain=domain_, range=range_)))
            m_t = alt.Chart(seuils).mark_text().encode(y='value', text='name:N')
            m_chart =  m_s + m_t + m_chart
            
        return m_chart
    except Exception as e:
        print(e)
        return None
    
def generateChroniquePluvioGraph(station_id, type_value_id, ts_start, ts_end, showTitle=True):
    try:
        samples = m_getAllPluvioMeasures(station_id, type_value_id,start_date=ts_start,end_date=ts_end)
        #print(samples)
        #print (samples.shape[0])
        #st.line_chart(samples, x='timestamp', y='numeric_value')
        if samples.shape[0] == 0:
            return

        #print("search pluvio station")
        stations = getStationsPluvio()
        my_station = m_extractStation(stations,station_id)
        station_name = my_station['name'] if my_station is not None else "Station not Found"

        type_values = getDataTypePluvio()
        type_value = m_extractStation(type_values,type_value_id)

        try:
            unit_symbol = type_value["unit"] if type_value is not None else "Unit not Found"
        except KeyError:
            unit_symbol = '' #This type_value has no unit

        #customize zoom
        if unit_symbol == 'm':
            #zoom on y axis - 10cm over and above
            y_min = samples.min(numeric_only=True).numeric_value - 0.1
            y_max = samples.max(numeric_only=True).numeric_value + 0.1

            m_domain = [y_min, y_max]
        else:
            #zoom on y axis - 0.5° ove and above
            y_min = samples.min(numeric_only=True).numeric_value - 0.5
            y_max = samples.max(numeric_only=True).numeric_value + 0.5

            m_domain = [y_min, y_max]
        
        if not showTitle:
            station_name = None
            unit_symbol_y= ''
        else:
            unit_symbol_y=unit_symbol


        #display lines for temperature
        displayLines = (type_value_id >= 4)

        if displayLines:
            #print("generate graph")
            if type_value_id == 4:
                m_interpolate='monotone'
            else:
                m_interpolate='linear'

            c = alt.Chart(samples).mark_line(interpolate=m_interpolate,point=True).transform_calculate(
                combined_tooltip = "datum.numeric_value"
            ).encode(
                alt.X('timestamp:T', axis = alt.Axis(tickCount="hour", ticks = True, title = station_name, 
                                                            #labelAngle=-75,
                                                            labelExpr="[timeFormat(datum.value, '%H:%M'),  timeFormat(datum.value, '%H') == '00' ? timeFormat(datum.value, '%d-%m-%Y') : '', timeFormat(datum.value, '%m') == '01' ? timeFormat(datum.value, '%Y') : '']")),
                alt.Y( 'numeric_value:Q', axis=alt.Axis(labels=True,title=unit_symbol_y), scale=alt.Scale(domain=m_domain)),
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
        else :
            #print("generate graph")
            
            c = alt.Chart(samples).mark_bar(interpolate='monotone',point=True).transform_calculate(
                combined_tooltip = "datum.numeric_value"
            ).encode(
                alt.X('timestamp:T', axis = alt.Axis(tickCount="hour", ticks = True, title = station_name, 
                                                            #labelAngle=-75,
                                                            labelExpr="[timeFormat(datum.value, '%H:%M'),  timeFormat(datum.value, '%H') == '00' ? timeFormat(datum.value, '%d-%m-%Y') : '', timeFormat(datum.value, '%m') == '01' ? timeFormat(datum.value, '%Y') : '']")),
                alt.Y( 'numeric_value:Q', axis=alt.Axis(labels=True,title=unit_symbol_y), scale=alt.Scale(domain=m_domain)),
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

            if type_value_id == 2 : 
                c = c + alt.Chart(samples).transform_calculate(
                    negative='datum.numeric_value < 0'
                ).mark_bar().encode(
                    x='timestamp:T',
                    y=alt.Y('numeric_value:Q', impute={'value': 0}),
                    color=alt.Color('negative:N', legend=None, scale=alt.Scale(domain=[True,False], range=["#FF0000","#0000FF"])),
                )

        m_chart = c

        #Add labels
        showLabels = False
        if showLabels :
            m_chart = m_chart + alt.Chart(samples.query("numeric_value > 0")).mark_text(align='center',  dx=10).encode(
                x = alt.X('timestamp:T', axis=alt.Axis(grid=False)),
                y = alt.Y( 'numeric_value:Q', axis=alt.Axis(grid=False)),
                text='numeric_value'
            )

        # #recup des seuils
        # seuils = m_getAllSeuils(station_id,unit_symbol)
        # #print(seuils)
        #m_chart = c
        # if seuils.shape[0] > 0:
        #     for index, seuil in seuils.iterrows():
        #         try:
        #             if str(seuil.htmlColor) == 'nan': 
        #                 m_color = 'black'
        #             else:
        #                 m_color = str(seuil.htmlColor)
        #         except:
        #             m_color = 'black'

        #         try:
        #             m_text = str(seuil['name'])
        #         except:
        #             m_text = ""

        #         m_s = alt.Chart(pd.DataFrame({'y': [seuil.value]})).mark_rule(color=m_color).encode(y='y')
        #         m_t = alt.Chart(pd.DataFrame({'y': [seuil.value]})).mark_text(text=m_text).encode(y='y')
        #         m_chart =  m_s + m_t + m_chart
        
        return m_chart
    except Exception as e:
        print(traceback.format_exc())
        raise e

#COULD: could be fastened
def generateAnalyseMeteoGraph(station_id, ts_start, ts_end, showTitle=True):
    try:

        #4 id temperature
        samples_temp = m_getAllPluvioMeasures(station_id, TEMPERATURE_ID, start_date=ts_start, end_date=ts_end, grpFunc="all")

        #1 id pluie
        samples_pluie = m_getAllPluvioMeasures(station_id, PLUIE_ID, start_date=ts_start, end_date=ts_end, grpFunc="all")
        
        #print(samples_temp.head(10))
        
        
        #print (samples.shape[0])
        #st.line_chart(samples, x='timestamp', y='numeric_value')
        if samples_temp.shape[0] == 0:
            return

        #compute values mean, min, max
        samples_temp_day = samples_temp.resample('1d', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ymin=pd.NamedAgg(column="numeric_value", aggfunc="min"),
            ymax=pd.NamedAgg(column="numeric_value", aggfunc="max"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        samples_temp_day["timestamp"] = pd.to_datetime(samples_temp_day.index) 


        samples_pluie_day = samples_pluie.resample('1d', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ymin=pd.NamedAgg(column="numeric_value", aggfunc="min"),
            ymax=pd.NamedAgg(column="numeric_value", aggfunc="max"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        samples_pluie_day["timestamp"] = pd.to_datetime(samples_pluie_day.index) 

        #print(samples_temp.head(10))
        #print(samples_pluie_day.head(10))
        #print(samples_pluie_day)


        base = alt.Chart(samples_temp_day).transform_calculate(
                combined_tooltip = "datum.numeric_value"
            )
        
        #generate points
        points = base.mark_point(
            filled=True, size=50, color='black'
        ).encode(
                x=alt.X('timestamp:T', title="Date"), #, axis = alt.Axis(tickCount="day", ticks = True, title = "station_name TO EDIT", 
                                                            #labelAngle=-75,
                                        #                    labelExpr="[timeFormat(datum.value, '%d-%m-%Y')]")),
                y=alt.Y( 'ymean', axis=alt.Axis(labels=True,title="°C")).scale(domain=[-10,40]), #, scale=alt.Scale(domain=m_domain)),
                #alt.Color('ust:N',legend=alt.Legend(title='Données')),
                #alt.Color('ust:N',legend=None),
                #opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
                #tooltip=[
                #    alt.Tooltip("timestamp:T",  format="%Y-%m-%d@%H:%M:%S", title="Date (local)"), 
                #    alt.Tooltip("combined_tooltip:N", title="Valeur"), 
                #    #alt.Tooltip("ust:N", title="Variable")
                #]
            #).add_selection(
            #    selection 
            ).properties( width=600)
        # generate error bars
        minmaxbar = base.mark_errorbar().encode(
            x=alt.X("timestamp:T", title="Date"),
            y=alt.Y("ymin", axis=alt.Axis(labels=False, title="")),
            y2=alt.Y2("ymax")
        )

        #precipitations
        pluies = alt.Chart(samples_pluie_day).mark_bar(width=alt.RelativeBandSize(0.7)).encode(
            x="timestamp:T",
            y=alt.Y("ysum:Q", axis=alt.Axis(labels=True,title="mm/jour")).scale(domain=[0,50])
        )

        m_chart = alt.layer(pluies , points + minmaxbar ).resolve_scale(
            y='independent'
        )


        # jauge pluie

        #1 id pluie - cumul mensuel
        samples_pluie_months = m_getAllPluvioMeasures(station_id, PLUIE_ID, start_date=-1, end_date=ts_end, grpFunc="SUM_MONTH", chartMode=False)
        samples_pluie_months.index = pd.to_datetime(samples_pluie_months['timestamp'])
        
        #print(samples_pluie_months.head(10))

        stats_samples_pluie_months = samples_pluie_months.groupby(by=samples_pluie_months.index.month).agg( 
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        stats_samples_pluie_months['month'] = stats_samples_pluie_months.index
        #print(stats_samples_pluie_months)

        samples_pluie_month = samples_pluie.resample('1m', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        
        samples_pluie_month["timestamp"] = pd.to_datetime(samples_pluie_month.index) 
        samples_pluie_month["month"] = samples_pluie_month['timestamp'].dt.month

        #add column mean_months
        samples_pluie_month["mean_months"] = None
        samples_pluie_month["evolution"] = None
        for idx, row in samples_pluie_month.iterrows():
            a = stats_samples_pluie_months[stats_samples_pluie_months["month"] == row["month"]]["ymean"]
            #print(a)
            samples_pluie_month.at[idx, "mean_months"] = float(a.iloc[0])

            evol_percent = round(( row["ysum"] / float(a.iloc[0]) * 100.0 ) - 100,2)
            if evol_percent >=0:
                samples_pluie_month.at[idx, "evolution_percent"] = " +"+str(evol_percent)+"%"
            else:
                samples_pluie_month.at[idx, "evolution_percent"] = " "+str(evol_percent)+"%"

            evol_value = round(row["ysum"] - float(a.iloc[0]) ,2)
            if evol_value >=0:
                samples_pluie_month.at[idx, "evolution_value"] = " +"+str(evol_value)+"mm"
            else:
                samples_pluie_month.at[idx, "evolution_value"] = " "+str(evol_value)+"mm"
        
        #samples_pluie_month["mean_months"] = samples_pluie_month.apply(lambda x: stats_samples_pluie_months["ymean"].filter(stats_samples_pluie_months["month"] == x.index.month))

        #print(samples_pluie_month.head(10))

        nb_jours_pluie = samples_pluie_day[samples_pluie_day["ysum"]>0].shape[0]
        print("NB JOUR PLUIE:"+str(nb_jours_pluie))

        nb_jours_sup_30 = samples_temp_day[samples_temp_day["ymax"]>=30].shape[0]
        print("NB JOUR >30:"+str(nb_jours_sup_30))

        #4 id temperature - moy mensuel
        samples_temp_months = m_getAllPluvioMeasures(station_id, TEMPERATURE_ID, start_date=-1, end_date=ts_end, grpFunc="AVERAGE", chartMode=False)
        samples_temp_months.index = pd.to_datetime(samples_temp_months['timestamp'])
        
        #print(samples_temp_months.head(10))

        stats_samples_temp_months = samples_temp_months.groupby(by=samples_temp_months.index.month).agg( 
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        stats_samples_temp_months['month'] = stats_samples_temp_months.index

        samples_temp_month = samples_temp.resample('1m', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        
        samples_temp_month["timestamp"] = pd.to_datetime(samples_temp_month.index) 
        samples_temp_month["month"] = samples_temp_month['timestamp'].dt.month

        #print(stats_samples_temp_months)
        #add column mean_months
        samples_temp_month["mean_months"] = None
        samples_temp_month["evolution_percent"] = None
        samples_temp_month["evolution_value"] = None
        for idx, row in samples_temp_month.iterrows():
            #print("Normale mensuelle : {}".format(str(row["month"])))
            a = stats_samples_temp_months[stats_samples_temp_months["month"] == row["month"]]["ymean"]
            #print(a)
            samples_temp_month.at[idx, "mean_months"] = float(a.iloc[0])
            evol_percent = round(( row["ymean"] / float(a.iloc[0]) * 100.0 ) - 100,2)
            if evol_percent >=0:
                samples_temp_month.at[idx, "evolution_percent"] = " +"+str(evol_percent)+"%"
            else:
                samples_temp_month.at[idx, "evolution_percent"] = " -"+str(evol_percent)+"%"

            evol_value = round(row["ymean"] - float(a.iloc[0]) ,2)
            if evol_value >=0:
                samples_temp_month.at[idx, "evolution_value"] = " +"+str(evol_value)+"°C"
            else:
                samples_temp_month.at[idx, "evolution_value"] = " -"+str(evol_value)+"°C"


        
        #print("Moy/Norm temp :")
        #print(samples_temp_month)

        #norm_temp_mois = samples_temp["ymean"].mean()
        #print("Normale temp mensuelle :"+str(norm_temp_mois))

        base1 = alt.Chart(samples_pluie_month)

        sum_pluies = base1.mark_bar().encode(
            x=alt.X('ysum', axis=alt.Axis(grid=True, title='')).scale(domain=[0,300]),
            y=alt.Y('timestamp:O', axis=None),
        ).properties(
            title='Rapport du cumul mensuel des précipitations aux normales'
        )

        sum_pluies_rule = base1.mark_rule(color='red').encode(
            x=alt.X("mean_months", title=''),
            #y=alt.Y('timestamp:O', axis=None),
            size=alt.value(5),
        )

        sum_pluies_labels = alt.Chart(samples_pluie_month.query("ysum > 0")).mark_text(align='center',  dx=10).encode(
                y = alt.Y('timestamp:O', axis=alt.Axis(grid=False)),
                x = alt.X( 'ysum:Q', axis=alt.Axis(grid=False)),
                text='ysum'
        )

        sum_pluies_labels_ev = alt.Chart(samples_pluie_month.query("ysum > 0")).mark_text(align='center',  dx=10, color="white").encode(
                y = alt.Y('timestamp:O', axis=alt.Axis(grid=False)),
                x = alt.value(10),
                text='evolution_percent'
        )

        m_chart1 = sum_pluies + sum_pluies_rule  + sum_pluies_labels + sum_pluies_labels_ev

        base2 = alt.Chart(samples_temp_month)

        mean_temps = base2.mark_bar().encode(
            x=alt.X('ymean', axis=alt.Axis(grid=True, title='')).scale(domain=[0,40]),
            y=alt.Y('timestamp:O', axis=None),
        ).properties(
            title='Rapport des températures moyennes mensuelles aux normales'
        )

        mean_temps_rule = base2.mark_rule(color='red').encode(
            x=alt.X("mean_months", title=''),
            #y=alt.Y('timestamp:O', axis=None),
            size=alt.value(5),
        )

        mean_temps_labels = alt.Chart(samples_temp_month).mark_text(align='center',  dx=10).encode(
                y = alt.Y('timestamp:O', axis=alt.Axis(grid=False)),
                x = alt.X( 'ymean:Q', axis=alt.Axis(grid=False)),
                text='ymean'
        )

        mean_temps_labels_ev = alt.Chart(samples_temp_month).mark_text(align='center',  dx=10, color="red").encode(
                y = alt.Y('timestamp:O', axis=alt.Axis(grid=False)),
                x = alt.value(10),
                text='evolution_value'
        )

        m_chart2 = mean_temps + mean_temps_rule  + mean_temps_labels + mean_temps_labels_ev
        
        m_chart = alt.hconcat( alt.vconcat(m_chart1, m_chart2),  m_chart)


        m_chart.properties(
                #height=200
            ).interactive()
        
        return m_chart
    
    except Exception as e:
        print(traceback.format_exc())
        raise e

#COULD: could be fastened
def graphAnalyseAnnuelleMeteo(station_id,ts_start, ts_end, showTitle=True):
    
    try:
        # cummul mensuels
        #1 id pluie - cumul mensuel
        samples_pluie_months = m_getAllPluvioMeasures(station_id, PLUIE_ID ,start_date=-1,  grpFunc="SUM_MONTH", chartMode=True)
        samples_pluie_months.index = pd.to_datetime(samples_pluie_months['timestamp'])
        
        #1 id pluie
        samples_pluie = m_getAllPluvioMeasures(station_id, PLUIE_ID , start_date=ts_start, end_date=ts_end,  grpFunc="SUM_MONTH", chartMode=True)
        

        #print(samples_pluie_months.head(10))

        stats_samples_pluie_months = samples_pluie_months.groupby(by=samples_pluie_months.index.month).agg( 
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        stats_samples_pluie_months['month'] = stats_samples_pluie_months.index
        #print(stats_samples_pluie_months)

        samples_pluie_month = samples_pluie.resample('1m', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        
        samples_pluie_month["timestamp"] = pd.to_datetime(samples_pluie_month.index)
        samples_pluie_month["month"] = samples_pluie_month['timestamp'].dt.month

        #add column mean_months
        samples_pluie_month["mean_months"] = None
        samples_pluie_month["evolution"] = None
        for idx, row in samples_pluie_month.iterrows():
            a = stats_samples_pluie_months[stats_samples_pluie_months["month"] == row["month"]]["ymean"]
            #print(a)
            samples_pluie_month.at[idx, "mean_months"] = float(a.iloc[0])

            evol_percent = round(( row["ysum"] / float(a.iloc[0]) * 100.0 ) - 100,2)
            samples_pluie_month.at[idx, "evolution_percent"] = evol_percent 


            evol_value = round(row["ysum"] - float(a.iloc[0]) ,2)
            samples_pluie_month.at[idx, "evolution_value"] = evol_value
            
        # #samples_pluie_month["mean_months"] = samples_pluie_month.apply(lambda x: stats_samples_pluie_months["ymean"].filter(stats_samples_pluie_months["month"] == x.index.month))
        #df_reordered = samples_pluie_month.loc[:, ["timestamp", "ysum", "mean_months","evolution_percent","evolution_value"]]
        #print(df_reordered)

        #nb_jours_pluie = samples_pluie_month[samples_pluie_month["ycount"]>0].shape[0]
        #print("NB JOUR PLUIE:"+str(nb_jours_pluie))

        # nb_jours_sup_30 = samples_temp_day[samples_temp_day["ymax"]>=30].shape[0]
        # print("NB JOUR >30:"+str(nb_jours_sup_30))

        #4 id temperature - moy mensuel
        samples_temp_months = m_getAllPluvioMeasures(station_id, TEMPERATURE_ID, start_date=-1, end_date=ts_end, grpFunc="AVERAGE", chartMode=True)
        samples_temp_months.index = pd.to_datetime(samples_temp_months['timestamp'])
        
        #print(samples_temp_months.head(10))

        samples_temp = m_getAllPluvioMeasures(station_id, TEMPERATURE_ID, start_date=ts_start, end_date=ts_end, grpFunc="ALL", chartMode=True)
        samples_temp.index = pd.to_datetime(samples_temp['timestamp'])

        stats_samples_temp_months = samples_temp_months.groupby(by=samples_temp_months.index.month).agg( 
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        stats_samples_temp_months['month'] = stats_samples_temp_months.index

        samples_temp_month = samples_temp.resample('1m', on="timestamp").agg( 
            ysum=pd.NamedAgg(column="numeric_value", aggfunc="sum"),
            ymean=pd.NamedAgg(column="numeric_value", aggfunc="mean"),
            ymin=pd.NamedAgg(column="numeric_value", aggfunc="min"),
            ymax=pd.NamedAgg(column="numeric_value", aggfunc="max"),
            ycount=pd.NamedAgg(column="numeric_value", aggfunc="count"),
        )
        
        samples_temp_month["timestamp"] = pd.to_datetime(samples_temp_month.index) 
        samples_temp_month["month"] = samples_temp_month['timestamp'].dt.month

        #print(stats_samples_temp_months)
        
        #add column mean_months
        samples_temp_month["mean_months"] = None
        samples_temp_month["evolution_percent"] = None
        samples_temp_month["evolution_value"] = None
        for idx, row in samples_temp_month.iterrows():
            #print("Normale mensuelle : {}".format(str(row["month"])))
            a = stats_samples_temp_months[stats_samples_temp_months["month"] == row["month"]]["ymean"]
            #print(a)
            samples_temp_month.at[idx, "mean_months"] = float(a.iloc[0])

            evol_percent = round(( row["ymean"] / float(a.iloc[0]) * 100.0 ) - 100,2)
            samples_temp_month.at[idx, "evolution_percent"]  = evol_percent

            evol_value = round(row["ymean"] - float(a.iloc[0]) ,2)
            samples_temp_month.at[idx, "evolution_value"] = evol_value
            
        
        #print("Moy/Norm temp :")
        #print(samples_temp_month)

        #norm_temp_mois = samples_temp["ymean"].mean()
        #print("Normale temp mensuelle :"+str(norm_temp_mois))

        base = alt.Chart(samples_temp_month).transform_calculate(
                combined_tooltip = "datum.ymean",
                #x_lbl=u''
            )
        
        #generate points
        points = base.mark_point(
            filled=True, size=50, color='red'
        ).encode(
                x=alt.X('month(timestamp):O' , axis=alt.Axis(labels=True,title="Mois")), #, axis = alt.Axis(tickCount="day", ticks = True, title = "station_name TO EDIT", 
                                                            #labelAngle=-75,
                                        #                    labelExpr="[timeFormat(datum.value, '%d-%m-%Y')]")),
                y=alt.Y( 'ymean', axis=alt.Axis(labels=True,title="°C")).scale(domain=[-10,40]), #, scale=alt.Scale(domain=m_domain)),
                #alt.Color('ust:N',legend=alt.Legend(title='Données')),
                #alt.Color('ust:N',legend=None),
                #opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
                #tooltip=[
                #    alt.Tooltip("timestamp:T",  format="%Y-%m-%d@%H:%M:%S", title="Date (local)"), 
                #    alt.Tooltip("combined_tooltip:N", title="Valeur"), 
                #    #alt.Tooltip("ust:N", title="Variable")
                #]
            #).add_selection(
            #    selection 
            ).properties( width=600)
        

        #points1 is the normale saisoniere
        points1 = base.mark_bar(
            filled=False, color='gray'
        ).encode(
                x=alt.X('month(timestamp):O', axis=alt.Axis(labels=True,title="Mois")), #, axis = alt.Axis(tickCount="day", ticks = True, title = "station_name TO EDIT", 
                                                            #labelAngle=-75,
                                        #                    labelExpr="[timeFormat(datum.value, '%d-%m-%Y')]")),
                y=alt.Y( 'mean_months', axis=alt.Axis(labels=True,title="°C")).scale(domain=[-10,40])
        )


        # generate error bars
        minmaxbar = base.mark_errorbar().encode(
            x=alt.X("month(timestamp):O", axis=alt.Axis(labels=True,title="Mois")),
            y=alt.Y("ymin", axis=alt.Axis(labels=False, title="")),
            y2=alt.Y2("ymax")
        )

        # #precipitations
        # pluies = alt.Chart(samples_pluie_day).mark_bar(width=alt.RelativeBandSize(0.7)).encode(
        #     x="timestamp:T",
        #     y=alt.Y("ysum:Q", axis=alt.Axis(labels=True,title="mm/jour")).scale(domain=[0,50])
        # )

        # m_chart = alt.layer(pluies , points + minmaxbar ).resolve_scale(
        #     y='independent'
        # )

        temp_labels_ev = alt.Chart(samples_temp_month).transform_calculate(
                    negative='datum.evolution_value < 0',
                    evolution_value_lbl = f'datum.evolution_value <0 ? format(datum.evolution_value,".1f") + " °C" : "+" + format(datum.evolution_value,".1f") + " °C"'
                ).mark_text(align='center',  dy=10, color="red").encode(
                x = alt.X('month(timestamp):O', axis=alt.Axis(grid=False)),
                y = alt.value(0), #alt.Y( 'ysum:Q', axis=alt.Axis(grid=False)),
                text=alt.Text('evolution_value_lbl:N', title="Anormalité de températures"),
                #color=alt.Color('negative:N', legend=None, scale=alt.Scale(domain=[True,False], range=["#FF0000","#0000FF"])),
                color=alt.Color('evolution_value', title="Anormalité de températures").scale(scheme="turbo", domainMid=0)
        )

        #m_chart = points + points1 + minmaxbar +temp_labels_ev
        m_chart = points  + minmaxbar +temp_labels_ev

        base1 = alt.Chart(samples_pluie_month)

        sum_pluies = base1.mark_bar().encode(
            x=alt.X('month(timestamp):O', axis=alt.Axis(labels=True,title="Mois")),
            y=alt.Y('ysum', scale=alt.Scale(domain=[0,250]), axis=alt.Axis(labels=True,title="mm")),
        )
        
        # sum_pluies_rule = base1.mark_rule(color='red').encode(
        #     x=alt.X('timestamp:O', axis=None),
        #     y=alt.Y("mean_months", title=''),
        #     size=alt.value(5),
        # )

        sum_pluies_labels = alt.Chart(samples_pluie_month.query("ysum > 0")).mark_text(align='center',  dx=0).encode(
                x = alt.X('month(timestamp):O', axis=alt.Axis(grid=False, title="")),
                y = alt.Y( 'ysum:Q', axis=alt.Axis(grid=False, title="")),
                text='ysum'
        )

        
        sum_pluies_labels_ev = alt.Chart(samples_pluie_month.query("ysum > 0")).transform_calculate(
                    negative='datum.evolution_percent < 0',
                    evolution_percent_lbl = f'datum.evolution_percent <0 ? format(datum.evolution_percent,".0f") + " %" : "+" + format(datum.evolution_percent,".0f") + " %"'
                ).mark_text(align='center',  dy=10, color="red").encode(
                x = alt.X('month(timestamp):O', axis=alt.Axis(grid=False, title="")),
                y = alt.Y( 'ysum:Q', axis=alt.Axis(grid=False, title="")),
                #text='evolution_percent',
                text='evolution_percent_lbl:N',
                color=alt.Color('negative:N', legend=None, scale=alt.Scale(domain=[True,False], range=["#FF0000","#0000FF"])),
        )

        m_chart1 = sum_pluies + sum_pluies_labels + sum_pluies_labels_ev
        
        # m_chart1 = sum_pluies + sum_pluies_rule  + sum_pluies_labels + sum_pluies_labels_ev

        #combine 2 graphs
        m_chart = alt.hconcat( m_chart1, m_chart )
        #m_chart = alt.hconcat( alt.vconcat(m_chart1, m_chart2), m_chart )

        m_chart.properties(
                #height=200
            ).interactive()
        
        
        return m_chart
    
    except Exception as e:
        print(traceback.format_exc())
        raise e