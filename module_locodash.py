from module_general import *

import numpy as np
import pandas as pd
import os
import folium
from folium.plugins import HeatMap, HeatMapWithTime
import polyline
import ast
import time
from dateutil.relativedelta import relativedelta
import math

import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output


############ BASIC PARAMETERS #######################################################################################
#### userAthlete
athlete_name = 'none'

#### Dates
today = date.today()    #store today's date
gbl_startdate = today-timedelta(6)
gbl_enddate = today
min_day = date(2000, 1, 1)

#### Units
measure_systems = [['Imperial', 'mi'], ['Metric', 'km']]        #Default measurement systems and primary unit
df_measure_systems = pd.DataFrame(measure_systems, columns = ['system', 'unit']).set_index('system', drop=True)
#[!!] Set the default global measurement system here
gbl_measure_system = 'Imperial'
gbl_measure_unit = df_measure_systems.loc[gbl_measure_system][0]


#### Colors
color1 = 'rgb(1, 51, 26)'
color2 = 'rgb(77, 40, 0)'

#### Error Handling
gen_err_msg = '*Invalid / Feelsbad'


############ INPUT ACTIVITY DATA #####################################################################################################
cwd = os.getcwd()
df_strava_travs = pd.DataFrame(columns=[])
min_record_date = min_day
df_locations = pd.DataFrame(columns=[])

def read_activities():
    ''' Read downloaded user information '''
    global df_strava_travs
    global min_record_date
    global df_locations
    global athlete_name
    ######## Get Strava activities with polyline coordinates. If it does not exist, create empty dataframe with necessary columns
    try:
        df_strava_activities = pd.read_csv('strava_activities.csv', index_col='id')
    except FileNotFoundError:       #Create an empty dataframe with the same necessary columns
        df_strava_travs = pd.DataFrame(columns=strava_pulledFormatted_col)
        min_record_date = min_day
    else:
        df_strava_travs = df_strava_activities.dropna(subset=['map.summary_polyline'])
        pd.options.mode.chained_assignment = None #default = 'warn'. Ignore warning on next line
        df_strava_travs['event_date'] = df_strava_travs['event_date'].str[:10]      #Remove time from datetime string
        #Get earliest date on record
        min_record_date = s_to_date(df_strava_travs.iloc[0]['event_date'])

    #### Get Locations spreadsheet notes. If it does not exist, create empty dataframe
    #Location notes should have the following columns ['name', 'coordinates', 'type', 'notes']
    try:
        df_locations = pd.read_excel(cwd + '\Locations.xlsx', engine='openpyxl')
        df_locations['coord'] = df_locations['coordinates'].str.split(',')      #convert string of coordinates to array
    except FileNotFoundError: df_locations = pd.DataFrame(columns=[])       #Create empty dataframe

    #Get user name
    try:
        with open('athlete.txt', 'r') as f:
            athlete_name = f.read()
    except FileNotFoundError:
        athlete_name = 'none'

    return df_strava_travs, min_record_date, df_locations, athlete_name

############# MAINVIEW AND REPORT GENERATORS #########################################################################################
def gen_stats_and_tblview(df_strava_travs_sliced, date_start, date_end):
    ''' takes in relevant df slice of activities and datetime objects. Returns: statistics df, activities df. '''
    global today
    today = date.today()

    #First handle empty sliced df case.
    if len(df_strava_travs_sliced)==0:
        return pd.DataFrame({'Fast Stats - No Data' : []}), pd.DataFrame({'Activity - No Data' : []})

    ############ GENERATE LINE_ITEM REPORTING ########
    df_trav_stats = pd.DataFrame(columns = ['Fast Stats', 'Value'])
    ####BLOCK 1: Activity count, total distance, total time, max distance, max time
    df_trav_stats.loc['Activity Count'] = ['Activity Count'] + [str(len(df_strava_travs_sliced)) + ' events']
    df_trav_stats.loc['Total Distance'] = ['Total Distance Recorded'] + [str(round(m_to_mi(df_strava_travs_sliced['distance'].sum()), 1)) + ' miles']
    time_ttl = seconds_to_HrMinSec(df_strava_travs_sliced['elapsed_time'].sum())
    df_trav_stats.loc['Total Recorded Time'] = ['Total Recorded Time'] + [time_ttl[0] + 'hr ' + time_ttl[1] + 'min']   #Using ELAPSED time
    df_trav_stats.loc['Max Distance in Single Event'] = ['Max Distance in Single Event'] + [str(round(m_to_mi(df_strava_travs_sliced['distance'].max()), 1)) + ' miles']
    time_max = seconds_to_HrMinSec(df_strava_travs_sliced['elapsed_time'].max())
    df_trav_stats.loc['Max Recorded Time in Single Event'] = ['Max Recorded Time in Single Event'] + [time_max[0] + 'hr ' + time_max[1] + 'min']
    #foot_elevGain_ttl = round(line_report_actvs['total_elevation_gain'].sum(), 1)
    ####BLOCK 2:
    actv_rate = len(set(df_strava_travs_sliced['event_date'])) / ((date_end-date_start).days+1) #Unique days divided by length of time period slice, rounded to 3 decimal
    df_trav_stats.loc['Activity Rate (by days)'] = ['Activity Rate (by days)'] + [str(round(100*actv_rate, 1))+'%']
    date_serials = [(datetime.strptime(x, '%Y-%m-%d').date() - date_start).days for x in df_strava_travs_sliced['event_date'].tolist()]     #Turn event dates into list of # of days since start date
    df_trav_stats.loc['Longest Streak (by days)'] = ['Longest Streak (by days)'] + [str(get_len_streak(date_serials))]


    ######## GENERATE RECENT ACTIVITY REPORTING ########
    df_actvs_tbl = df_strava_travs_sliced[['event_date', 'name', 'type', 'distance', 'elapsed_time', 'average_heartrate']]
    #Reverse the order of rows to display most recent data on top
    df_actvs_tbl = df_actvs_tbl.iloc[::-1]
    #Format data for display
    df_actvs_tbl['event_date'] = df_actvs_tbl['event_date'].apply(s_to_easyDate)
    df_actvs_tbl['distance'] = df_actvs_tbl['distance'].apply(m_to_mi).round(1)
    df_actvs_tbl['pace'] = df_actvs_tbl.apply(lambda x: calc_pace(x['elapsed_time'], x['distance'], add_lead=True, digital=True), axis=1)
    df_actvs_tbl['elapsed_time'] = df_actvs_tbl['elapsed_time'].apply(seconds_to_HrMinSec, add_lead=True, digital=True)
    df_actvs_tbl = df_actvs_tbl[['event_date', 'name', 'type', 'distance', 'pace', 'elapsed_time', 'average_heartrate']]    #Reorder the columns
    df_actvs_tbl.columns = [x.title().replace('_',' ') for x in df_actvs_tbl.columns]     #Format for userfriendly reading: Captilizaton and spacing
    df_actvs_tbl.rename(columns={'Distance': 'Distance ' + '(' + gbl_measure_unit + ')'}, inplace=True)

    return df_trav_stats, df_actvs_tbl

######## MAINVIEWS ########
def gen_standard_map(df_strava_travs_sliced):
    #First handle empty sliced df case. Create a generic zoomed out map with additional features
    if len(df_strava_travs_sliced)==0:
        m = folium.Map(location=[36,-108], zoom_start=4, control_scale=True)
        folium.TileLayer('stamenterrain').add_to(m)
        m.save('map.html')  #Save map without routes or markers and create dash layout
        return html.Iframe(id='mainview', srcDoc=open('map.html','r').read(), width='100%', height='100%')
    #Slice not empty:
    #Create map based on starting location of last run
    init_coord = df_strava_travs_sliced.iloc[-1]['start_latlng']
    init_coord = ast.literal_eval(init_coord)
    m = folium.Map(location=init_coord, zoom_start=12, control_scale=True)
    folium.TileLayer('stamenterrain').add_to(m)
    #Construct polylines
    for i in df_strava_travs_sliced.index:
        route_coord = polyline.decode(df_strava_travs_sliced.loc[i]['map.summary_polyline'])
        folium.PolyLine(locations=route_coord,
            tooltip=s_to_easyDate(df_strava_travs_sliced.loc[i]['event_date']) + ' - ' + str(df_strava_travs_sliced.loc[i]['name']),
            popup=folium.Popup('<a href=\"https://www.strava.com/activities/' + str(i) + '"target="_blank"> Strava.com </a>'),
            smooth_factor=4, weight=4,
            ).add_to(m)
    #### Add location notes markers
    for i in df_locations.index:
        folium.Marker(df_locations.loc[i]['coord'],
            tooltip=df_locations.loc[i]['name'],
            popup=df_locations.loc[i]['notes'],
            icon=folium.Icon(color='red', icon='leaf'),
        ).add_to(m)
    ######## Show activity start markers if <= 60 routes sliced
    if len(df_strava_travs_sliced) <= 60:
        for i in df_strava_travs_sliced.index:
            trav_start_coord = polyline.decode(df_strava_travs_sliced.loc[i]['map.summary_polyline'])[0]    #Get first coordinate from polyline as start
            folium.Marker(trav_start_coord,
                tooltip=s_to_easyDate(df_strava_travs_sliced.loc[i]['event_date']) + ' - ' + str(df_strava_travs_sliced.loc[i]['name']),
                popup=folium.Popup('<a href=\"https://www.strava.com/activities/' + str(i) + '"target="_blank"> Strava.com </a>'),
                icon=folium.Icon(color='green', icon='cloud', icon_color='white'),
            ).add_to(m)
    #Save the map and create the mainview
    m.save('map.html')
    return html.Iframe(id='mainview', srcDoc=open('map.html','r').read(), width='100%', height='100%')


def gen_heat_map(df_strava_travs_sliced):
    #First handle empty sliced df case. Create a generic zoomed out map with additional features
    if len(df_strava_travs_sliced)==0:
        m = folium.Map(location=[36,-108], zoom_start=4, control_scale=True)
        folium.TileLayer('stamenterrain').add_to(m)
        m.save('map.html')  #Save map without routes or markers and create dash layout
        return html.Iframe(id='mainview', srcDoc=open('map.html','r').read(), width='100%', height='100%')
    #Slice not empty:
    #Create map based on staring location of last run
    init_coord = df_strava_travs_sliced.iloc[-1]['start_latlng']
    init_coord = ast.literal_eval(init_coord)
    m = folium.Map(location=init_coord, zoom_start=12, control_scale=True)
    folium.TileLayer('stamenterrain').add_to(m)
    #Initilaize arrays to store heatmap parameters
    heat_coords = []
    heat_date_ind = []
    for i in df_strava_travs_sliced.index:
        route_coord = polyline.decode(df_strava_travs_sliced.loc[i]['map.summary_polyline'])
        route_coord = [[i[0],i[1]] for i in route_coord]
        #Estimate number of splits
        cnt_splits = max(round(m_to_mi(df_strava_travs_sliced.loc[i]['distance'])),1)
        coords_in_split = len(route_coord)//cnt_splits       #Count number of coorindates to include in split
        route_coord =  [route_coord[x:x+coords_in_split] for x in range(0, len(route_coord), coords_in_split)]
        heat_coords.extend(route_coord)        #Add coordinates into list
        heat_date_ind.extend([s_to_easyDate(df_strava_travs_sliced.loc[i]['event_date'][0:10])] * len(route_coord))      #Get date as heatmap time index
    heat_coords_flat = [item for sublist in heat_coords for item in sublist]
    #Construct HeatMap
    HeatMap(heat_coords_flat, radius=6).add_to(m)
    #Construct HeatMap with time
    HeatMapWithTime(heat_coords, heat_date_ind,
        radius=12, min_opacity=2, max_opacity=4, min_speed=5, max_speed=12, speed_step=1).add_to(m)
    #Save the map and create the mainview
    m.save('map.html')
    return html.Iframe(id='mainview', srcDoc=open('map.html','r').read(), width='100%', height='100%')

def gen_dist_over_time(df_strava_travs_sliced, date_start, date_end):
    ''' Takes sliced df, and dates in date() form. Returns bar chart of distance over time '''
    df_strava_travs_sliced = df_strava_travs_sliced[['name', 'event_date', 'distance', 'type']]
    #Add upper and lower time bounds for event date axis, and populate with necessary data to prevent NaN error
    df_strava_travs_sliced.loc['time_axis_min', 'event_date'] = date_to_s(date_start)
    df_strava_travs_sliced.loc['time_axis_max', 'event_date'] = date_to_s(date_end)
    df_strava_travs_sliced.loc['time_axis_min', 'type'] = ''
    df_strava_travs_sliced.loc['time_axis_max', 'type'] = ''
    #Convert distance units
    df_strava_travs_sliced['distance'] = df_strava_travs_sliced['distance'].apply(m_to_mi).round(1)
    fig = px.bar(df_strava_travs_sliced, x='event_date', y='distance', color='type',
        hover_data=['name'], text='distance')
    fig = fig.update_layout(barmode='group')
    fig = fig.update_traces(texttemplate='%{text:.2s} ' + gbl_measure_unit, textposition='outside')
    fig = fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    return dcc.Graph(id='mainview', figure=fig, style={'width':'100%', 'height':'100%'})


############# EXECUTE ############

#read activities
read_activities()
