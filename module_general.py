from datetime import datetime, date, timedelta

#Columns to pull for Strava Activities as they are named in Strava.
init_strava_pulled_col = ['id',
    'name',
    'start_date_local',
    'elapsed_time',
    'moving_time',
    'type',
    'distance',
    'average_speed',
    'total_elevation_gain',
    'gear_id',
    'average_heartrate',
    'max_heartrate',
    'map.summary_polyline',
    'start_latlng', 'end_latlng',
]
#Strava columns after initial editing and processing for LOCO DASH page. (Specifically, the df_strava_travs dataframe)
strava_pulledFormatted_col = ['name', 'event_date', 'elapsed_time', 'moving_time', 'type', 'distance', 'average_speed', 'total_elevation_gain', 'gear_id', 'average_heartrate', 'max_heartrate', 'map.summary_polyline', 'start_latlng', 'end_latlng']

def s_to_date(s):
    ''' Takes a string YYYY-MM-DD. Return as date() object '''
    return datetime.strptime(s, '%Y-%m-%d').date()

def date_to_s(dte):
    ''' Takes a date() object. Return as string YYYY-MM-DD '''
    return dte.strftime('%Y-%m-%d')

def s_to_easyDate(s):
    ''' Takes a string YYYY-MM-DD. Return string date as easy human-readable format, e.g. Jan 19 2020 '''
    return datetime.strptime(s, '%Y-%m-%d').strftime("%b %d, %Y")

def seconds_to_HrMinSec(seconds, add_lead=False, digital=False):
    hr = seconds // 3600
    min = (seconds % 3600) // 60
    sec = seconds % 60
    ret_time = [str(hr), str(min), str(sec)]
    #Request to add leading zeroes (default is none)
    if add_lead: ret_time = ['0'+i if len(i)==1 else i for i in ret_time] #If lead zero is needed for string
    #request in digital Style (default is array)
    if digital:
        ret_time = ret_time[0] + ':' + ret_time[1] + ':' + ret_time[2]
        if hr == 0:
            ret_time = ret_time[3:]   #if hr is 0, remove hour place
    return ret_time

def gen_ordered_setlist(lst):
    setlist = []
    for i in lst:
        if i not in setlist:    setlist.append(i)
    return setlist

def gen_dashtable_col_and_data(df):
    ''' returns columns and data parameters for dash table'''
    return [{'id': col, 'name': col} for col in df.columns], df.to_dict('records')


def m_to_mi(m):
    ''' convert m to mile '''
    return m*0.00062

def calc_pace(seconds, distance_units, mile=True, add_lead=False, digital=False):
    ''' Arguments are seconds and the # of DESIRED distance units (mi, km, etc.); return pace by calling seconds_to_HrMinSec() '''
    if distance_units == 0: return 'None'
    return seconds_to_HrMinSec(round(seconds/distance_units), add_lead, digital)

def get_len_streak(items):
    ''' Expects the list of integers to be sorted '''
    if len(items)==0: return 0  #If list is empty, longest streak is nonexistent
    if len(items)==1: return 1  #If list has one elem, longest streak is 1
    streak_record=1     #Longest streak to be returned
    streak=1
    curr=0      
    while curr < len(items)-1:
        if items[curr]+1 == items[curr+1]:
            streak+=1
            if streak_record < streak: streak_record = streak
        else:
            streak=0
        curr+=1
    return streak_record
