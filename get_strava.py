import numpy as np
import pandas as pd
from pandas.io.json import json_normalize
import time
import requests
import json
import csv

from module_general import *
from private import *       #Made a module to store my client information. You may enter your client information below

def get_strava_data(user_auth_code):
    ######## APP API PARAMETERS ############################################################
    #client_id = <REPLACE WITH YOUR CLIENT ID>
    #client_secret = <REPLACE WITH YOUR CLIENT SECRET>

    ######## GET ACCESS TOKEN WITH AUTH CODE ######################################
    response = requests.post(
        url = 'https://www.strava.com/oauth/token',
        data = {'client_id': client_id,
                'client_secret': client_secret,
                'code': user_auth_code,
                'grant_type': 'authorization_code'})
    strava_tokens = response.json()         #Save json response to variable
    access_token = strava_tokens['access_token']

    ######## GET STRAVA ACTIVITIES ########################################################################
    url = "https://www.strava.com/api/v3/activities"
    page = 1

    # Create the dataframe ready for the API call to store your activity data
    df_activities = pd.DataFrame(columns = init_strava_pulled_col)
    while True:
        # get page of activities from Strava
        r = requests.get(url + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(page))
        r = r.json()

        if (not r):
            break
        # otherwise add new data to dataframe
        for x in range(len(r)):
            for col in init_strava_pulled_col:
                #Special Cases
                if col == 'map.summary_polyline':    #special JSON multi-layer index case
                    df_activities.loc[x + (page-1)*200, col] = r[x]['map']['summary_polyline']
                    continue
                #Regular case
                try:
                    df_activities.loc[x + (page-1)*200, col] = r[x][col]
                except KeyError:
                    df_activities.loc[x + (page-1)*200, col] = ''              #some fields will not be in the JSON fields if the instance has a null in said field
        page += 1       # increment page

    # Format and export your activities file
    df_activities.rename(columns={'start_date_local': 'event_date'}, inplace=True)
    df_activities.set_index('id', drop=True, inplace=True)
    df_activities = df_activities.sort_values(['event_date'])  #Ensure sorting by date
    #EXPORT ACTIVITIES
    df_activities.to_csv('strava_activities.csv')


    ######## STRAVA SPLITS FOR RUNS/RIDES/WALKS ETC ########################################################################
    # filter to only activities with route GPS data
    df_travs = df_activities.dropna(subset=['map.summary_polyline'])
    # initialize dataframe for split data
    col_names = ['event_date', 'average_speed','distance','elapsed_time','elevation_difference','moving_time','split','id']
    df_splitsStandard = pd.DataFrame(columns=col_names)
    df_splitsMetric = pd.DataFrame(columns=col_names)

    # loop through each activity id and retrieve data
    for id in df_travs.index:
        # Load activity data
        r = requests.get(url + '/' + str(id) + '?access_token=' + access_token)
        r = r.json()

        # Extract Activity Splits STANDARD IMPERIAL
        df_trav_splits = pd.DataFrame(r['splits_standard'])
        df_trav_splits['id'] = id
        df_trav_splits['event_date'] = df_travs.loc[id]['event_date']
        df_trav_splits['split_id'] = df_trav_splits[['id', 'split']].apply(lambda row: '_mi_'.join(row.values.astype(str)), axis=1)        #create concat key with activity id and split number
        # Add to total list of splits
        df_splitsStandard = pd.concat([df_splitsStandard, df_trav_splits])

        # Extract Activity Splits METRIC
        df_trav_splits = pd.DataFrame(r['splits_metric'])
        df_trav_splits['id'] = id
        df_trav_splits['event_date'] = df_travs.loc[id]['event_date']
        df_trav_splits['split_id'] = df_trav_splits[['id', 'split']].apply(lambda row: '_km_'.join(row.values.astype(str)), axis=1)        #create concat key with activity id and split number
        # Add to total list of splits
        df_splitsMetric = pd.concat([df_splitsMetric, df_trav_splits])

    # Format and EXPORT SPLITS
    #STANDARD/IMPERIAL
    df_splitsStandard.set_index('split_id', drop=True, inplace=True)
    df_splitsStandard.rename(columns={'start_date_local': 'event_date'}, inplace=True)
    #METRIC
    df_splitsMetric.set_index('split_id', drop=True, inplace=True)
    df_splitsMetric.rename(columns={'start_date_local': 'event_date'}, inplace=True)

    #Load to CSV
    df_splitsStandard.to_csv('strava_splits_imperial.csv')
    df_splitsMetric.to_csv('strava_splits_metric.csv')


    ############ GET ATHLETE INFORMATION #############################################
    #In this sample, I am pulling the athlete/user name and writing to a file. Modify to add more data points.
    r = requests.get('https://www.strava.com/api/v3/athlete' + '?access_token=' + access_token)
    r = r.json()
    with open('athlete.txt', 'w') as output_file:
        output_file.write(r['firstname'] + ' ' + r['lastname'])

    return
