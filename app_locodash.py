from flask import request, redirect
from module_locodash import *
from get_strava import *

############ DASH APP ####################################################################################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
dash_app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = dash_app.server
dash_app.title = 'Locomotion Fitness Dashboard'
app_URL = 'http://127.0.0.1:8050'

user_auth_code = 'No Auth Code'
#When auth code exchange token provided, save token to variable and redirect to url
@server.route('/exchange_token')
def get_token():
    user_auth_code = request.args.get('code')
    #Run get strava data with the user auth code. Saves most recent data to file. Should only run when redirected from Strava login when getting new auth code
    get_strava_data(user_auth_code)
    return redirect(app_URL)


############ SET PARAMETERS ####################################################################################
trav_actv_types = gen_ordered_setlist(df_strava_travs['type'].tolist())         #List of all travel activity types. For slicer.
view_modes = ['Table Only', 'Standard Map', 'Heat Map', 'Distance over Time']
mainview_style_default = {'width':'90%', 'height':'800px',}


############ LAYOUT #######################################################################################################
dash_app.layout = html.Div(children=[
    #Dummy objects to trigger callbacks
    html.Div(id='CB0', style={'height': '0px'}), html.Div(id='CB1_-1:2', style={'height': '0px'}),

    html.A(id='authLink', children = 'Get Your Strava Data',
        href = 'http://www.strava.com/oauth/authorize?client_id=58494&response_type=code&redirect_uri=' + app_URL + '/exchange_token&approval_prompt=force&scope=activity:read',
        target='_self',
        style = {'display': 'in-line block', 'fontWeight': 'bold'}),
    html.B(id='athleteUserText', children = 'Athlete: '+ athlete_name,
        style = {'display': 'in-line block', 'marginLeft': '20px'}),
    html.Div(
        className = 'banner',
        style = {'backgroundColor': color1, 'border': 'solid', 'borderColor': color1, 'borderRadius': '5px',
            'height': '26px',},
        children = [
            html.B('Locomotion Fitness Dashboard',
                id = 'title',
                style = {'fontSize': '18px', 'marginTop': '2px','marginLeft': '10px',
                    'fontWeight': 'bold', 'color': 'white', 'textAlign': 'left', 'display': 'in-line block'}),
        ]
    ), ####END banner
    html.Div(className = "Container_A",
        style = {'backgroundColor': 'white', 'minWidth': '100%', 'width': '100%', 'height':'1200px',
        'display': 'inline-block'},
        children = [
            html.Div(id = 'A.1_Left',
                className = 'column',
                style = {'paddingLeft': '10px', 'paddingTop': '4px',
                   'backgroundColor': 'rgb(225,225,225)',
                   'height': '100%', 'width': '25%',
                   'marginLeft': '0px'},
                children = [
                    html.Div(id = 'A.1.1',
                        className = 'column',
                        style = {'paddingLeft': '10px', 'paddingTop': '4px',
                           'backgroundColor': 'rgb(200,225,200)',
                           'height': '375px', 'width': '100%',
                           'marginLeft': '0px'},
                        children = [
                         ######## DATE SELECTION ITEMS ########
                            html.Label('Dates Selection',
                                style={'color': 'black', 'fontWeight': 'bold',}),
                            html.Div( id = 'timespan', style = {'fontSize': '14px', 'color': 'rgb(75,75,75)',}, #children = 'Span: ' + str(days_span) + ' days',
                            ),
                            dcc.DatePickerRange(
                                id='date_slicer',
                                min_date_allowed=min_day,
                                start_date=gbl_startdate, end_date=gbl_enddate,     #Default range is last 7 days
                                first_day_of_week=1, #Mondays
                                style = {'border': '2px solid', 'borderColor': color1},
                            ),
                            #### Navigation Buttons
                            html.Div(className = 'row',     #Month navigation buttons
                                style = {'marginLeft': '10px', 'height': '25px'},
                                children = [
                                    html.Label('Month:',
                                        style = {'display': 'inline-block', 'fontSize': '14px', 'fontWeight': '600'}),
                                    html.Div(style = {'width': '35px', 'display': 'inline-block'}),
                                    html.Button(children='<', id='prevMonth',
                                        style = {'height': '25px', 'display': 'inline-block', 'backgroundColor': color1, 'color': 'white'},
                                    ),
                                    html.Button(children='>', id='nextMonth',
                                        style = {'height': '25px', 'display': 'inline-block', 'backgroundColor': color1, 'color': 'white'},
                                    ),
                                ],
                            ),
                            html.Div(className = 'row',     #Span navigation buttons
                                style = {'marginLeft': '10px', 'height': '25px'},
                                children = [
                                    html.Label('Days Span:',
                                        style = {'display': 'inline-block', 'fontSize': '14px', 'fontWeight': '600'}),
                                    html.Div(style = {'width': '5px', 'display': 'inline-block'}),
                                    html.Button(children='<', id='prevSpan',
                                        style = {'height': '25px', 'display': 'inline-block', 'backgroundColor': color1, 'color': 'white'},
                                    ),
                                    html.Button(children='>', id='nextSpan',
                                        style = {'height': '25px', 'display': 'inline-block', 'backgroundColor': color1, 'color': 'white'},
                                    ),
                                ],
                            ),
                            html.Div(className = 'row',     #Show all button
                                style = {'marginLeft': '10px', 'height': '25px'},
                                children = [
                                html.Label('Records to date:',
                                    style = {'display': 'inline-block', 'fontSize': '14px', 'fontWeight': '600'}),
                                    html.Div(style = {'width': '10px', 'display': 'inline-block'}),
                                    html.Button(children='Show all', id='showAll',
                                        style = {'height': '25px', 'display': 'inline-block', 'backgroundColor': color1, 'color': 'white'},
                                    ),
                                ],
                            ), html.Br(),
                            ######## ACTIVITY TYPES ########
                            html.Label('Activity Type(s)',
                                style={'color': 'black', 'fontWeight': 'bold',}),
                            dcc.Checklist(
                                id='actv_type_slicer',
                                options=[{'label': actv_type, 'value': actv_type} for actv_type in trav_actv_types],
                                value = trav_actv_types,
                                labelStyle={'display': 'inline-block'}, inputStyle={'margin-left': '15px'}
                            ), html.Br(),
                            ######## DISTANCE SLICING ########
                            html.Label('Distance ' + '(' + gbl_measure_unit + ')',
                                style={'color': 'black', 'fontWeight': 'bold',}),
                            html.Div(
                                html.Div(
                                    children = [
                                    html.Div('Min:', style={'display': 'inline-block'}),
                                    dcc.Input(id='input_dist_min',
                                        type='number', value=0, min=0, max=9999, debounce=True,
                                        style={'width': '75px'}),
                                    html.Div(style={'width': '10px', 'display': 'inline-block'}),
                                    html.Div('Max:', style={'display': 'inline-block'}),
                                    dcc.Input(id='input_dist_max',
                                        type='number', value=999, min=0, max=9999, debounce=True,
                                        style={'width': '75px', 'display': 'inline-block'}),
                                    html.Div(id='input_error', style={'display': 'inline-block', 'color': 'red'}),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    html.Div(className = 'column',
                        style = {'backgroundColor': 'rgb(225,225,225)', 'marginLeft': '0px', 'height': '10px', 'width': '100%',}),
                    html.Div(id = 'A.1.2',
                        className = 'column',
                        style = {'paddingLeft': '10px', 'paddingTop': '4px',
                           'backgroundColor': 'rgb(245,245,245)',
                           'height': '850px', 'width': '100%',
                           'marginLeft': '0px'},
                        children = [
                            # html.Label('Athlete Statistics',
                            #     style={'color': 'black', 'fontWeight': 'bold',}),
                            dash_table.DataTable(
                                id = 'summary_rpt_tbl',
                                style_table = {'width':'90%', 'border': '1px solid ' + str(color2)},
                                style_header = {'backgroundColor': color2, 'color': 'white', 'fontWeight': 'bold', 'fontSize': '14px', 'textAlign': 'left',},
                            ),
                        ]
                    ),
                ],
            ),  #### END A.1 Left
            html.Div(id = 'A.2_Right',
                className = 'column',
                style = {'paddingLeft': '10px', 'paddingTop': '4px',
                   'backgroundColor': 'rgb(225,225,225)',
                   'height': '100%', 'width': '75%',
                   'marginLeft': '0px'},
                children = [
                    dcc.Dropdown(
                        id='choose_view_mode',
                        options=[{'label': view_mode, 'value': view_mode} for view_mode in view_modes],
                        value = 'Standard Map', clearable=False,
                        style={'width': '75%'}
                    ),
                    html.Div(id = 'mainview_container',
                        style = mainview_style_default,
                    ),
                    html.Div(className = 'column',
                        style = {'backgroundColor': 'rgb(225,225,225)','height': '10px', 'width': '100%',}),
                    dash_table.DataTable(id = 'recent_actvs_tbl',
                        style_table = {'width':'90%', 'border': '1px solid ' + str(color2)},
                        style_cell = {'maxWidth': '20px', #!! May make some modifications based on field, some field lengths can be expected to be fixed. Add tooltips
                            'overflow': 'hidden', 'textOverflow': 'ellipsis',},
                        style_header = {'backgroundColor': color2, 'color': 'white', 'fontWeight': 'bold', 'fontSize': '14px', 'textAlign': 'left',},
                        style_data = {'fontSize': '14px'},
                        style_data_conditional = [{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(240, 240, 240)'}],
                        sort_action='native',
                        page_size=15,
                    ),
                ],
            ), #### END A.2 Right
        ],
    ), #### END Container_A
])

############ FUNCTIONS ################################################################################################################
def update_gbl_date(start, end):        #Created for callback 1. Has to be in this file due to changing global variable
    ''' takes strings as inputs '''
    global gbl_startdate
    gbl_startdate = datetime.strptime(start, '%Y-%m-%d').date()
    global gbl_enddate
    gbl_enddate = datetime.strptime(end, '%Y-%m-%d').date()
    return

############ CALLBACKS ##################################################################################################################
####CALLBACK 0
@dash_app.callback(
Output('CB1_-1:2', 'children'),     #Dummy i/o
[Input('CB0', 'children')]
)
def callback0(input):
    ''' Initial load should kickstart all necessary operations. Starting with the most updated load of data:
        strava actvs, min date of strava acts, and locations '''
    #These global variables are initially imported from the module.
    #Update these global variables in the scope of this script file for the entire dash program at every load
    global df_strava_travs
    global min_record_date
    global df_locations
    global athlete_name
    df_strava_travs, min_record_date, df_locations, athlete_name = read_activities()
    print('[JL] > Callback0')
    return None


####CALLBACK 1.-1:1
@dash_app.callback(
[Output('date_slicer', 'start_date'),
Output('date_slicer', 'end_date')],
[Input('prevMonth', 'n_clicks'),
Input('nextMonth', 'n_clicks'),
Input('prevSpan', 'n_clicks'),
Input('nextSpan', 'n_clicks'),
Input('showAll', 'n_clicks')]
)
def navig_date(prevMonth, nextMonth, prevSpan, nextSpan, showAll):
    ''' For date navigation buttons to change date selection.
        All dates in date() format.
        prevMonth updates span to first to last day of last month,
        nextMonth updates span to first to last day of next month.
        prevSpan and nextSpan add/subtrack from start and end date respectively

        This CALLBACK1.-1 will automatically call CALLBACK1 to update global date variables'''
    start = gbl_startdate
    end = gbl_enddate
    span = end - start + timedelta(days=1)

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if 'prevMonth' in changed_id:
        start -= relativedelta(months=1)    #Go back 1 month
        start = start.replace(day=1)    #Assign first day of month
        end = start + relativedelta(months=1) - timedelta(days=1)
    elif 'nextMonth' in changed_id:
        start += relativedelta(months=1)    #Go forward 1 month
        start = start.replace(day=1)    #Assign first day of month
        end = start + relativedelta(months=1) - timedelta(days=1)
    elif 'prevSpan' in changed_id:
        start -= span
        end -= span
    elif 'nextSpan' in changed_id:
        start += span
        end += span
    elif 'showAll' in changed_id:
        start = min_record_date
        end = today

    return start, end

####CALLBACK 1.-1:2
@dash_app.callback(
[Output('athleteUserText', 'children'),
Output('actv_type_slicer', 'options'),
Output('actv_type_slicer', 'value')],
[Input('CB1_-1:2', 'children'),] #dummy input
)
def actv_type_update(input):
    ''' When read in new data,
        1. athlete name must change
        2. actv type options and value must reflect that change for proper slicing '''
    trav_actv_types = gen_ordered_setlist(df_strava_travs['type'].tolist())
    options=[{'label': actv_type, 'value': actv_type} for actv_type in trav_actv_types]
    value=trav_actv_types
    return 'Athlete: '+ athlete_name, options, value

#### CALLBACK1
@dash_app.callback(
[Output('mainview_container', 'children'),
Output('mainview_container', 'style'),
Output('summary_rpt_tbl', 'columns'),   #Summary line reporting stats table
Output('summary_rpt_tbl', 'data'),
Output('recent_actvs_tbl', 'columns'),  #Recent activities table
Output('recent_actvs_tbl', 'data'),
Output('input_error', 'children')],
[Input('date_slicer', 'start_date'),
Input('date_slicer', 'end_date'),
Input('actv_type_slicer', 'value'),
Input('input_dist_min', 'value'),
Input('input_dist_max', 'value'),
Input('choose_view_mode', 'value')]
)
def callback_1(start, end, actv_types, dist_min, dist_max, view_mode):
    ''' Accepts date selection and other slicers. Updates glb date variables. Generates report views.
        Returns: mainview object, mainview style, columns, data, columns, data, error message. '''
    #First manage potential cases in which start date is on or comes after end date
    if datetime.strptime(start, '%Y-%m-%d').date() >= datetime.strptime(end, '%Y-%m-%d').date():
        return None, None, None, None, None, None, None
    #If input is out of range or invalid, Dash will assign it a NoneType. If min is greater than max, invalid. Handle it.
    if (dist_min == None) or (dist_max == None) or (dist_min > dist_max):
        return None, None, [{'id':'.','name':gen_err_msg}], [], [{'id':'.','name':gen_err_msg}], [], gen_err_msg

    #Update global variables start and end date based on what the date slicer takes
    update_gbl_date(start, end)

    today = date.today() #Update when ran. Save today's date in case it needs to be used for anything.
    start = datetime.strptime(start,'%Y-%m-%d').date()
    end = datetime.strptime(end,'%Y-%m-%d').date()
    #Create sliced activity dataframe
    df_strava_travs_sliced = pd.DataFrame(columns = df_strava_travs.columns)
    for i in df_strava_travs.index:
        #If event in selected date range, activity types, and distance range
        if ((start <= datetime.strptime(df_strava_travs.loc[i]['event_date'], '%Y-%m-%d').date() <= end) and
        (df_strava_travs.loc[i]['type'] in actv_types) and
        (dist_min <= m_to_mi(df_strava_travs.loc[i]['distance']) <= dist_max)):
            df_strava_travs_sliced.loc[i] = df_strava_travs.loc[i]
    #Generate basic stats and table view
    reports = gen_stats_and_tblview(df_strava_travs_sliced, start, end)
    #build dashtable contents from stats and actvs tblview report
    dt_contents_1 = gen_dashtable_col_and_data(reports[0])
    dt_contents_2 = gen_dashtable_col_and_data(reports[1])

    #Building the mainview starting with layout style
    mainview_style = mainview_style_default     #The style of the container
    #Choosing the main view
    if view_mode == 'Table Only':
        mainview = html.Div()  #empty placeholder child component
        mainview_style = {'height': '0px'}  #Remove the container from view if user chooses 'None'
    elif view_mode == 'Standard Map':
        mainview = gen_standard_map(df_strava_travs_sliced)
    elif view_mode == 'Heat Map':
        mainview = gen_heat_map(df_strava_travs_sliced)
    elif view_mode == 'Distance over Time':
        mainview = gen_dist_over_time(df_strava_travs_sliced, start, end)
    return mainview, mainview_style, dt_contents_1[0], dt_contents_1[1], dt_contents_2[0], dt_contents_2[1], None

####CALLBACK 1.1
@dash_app.callback(
Output('timespan', 'children'),
[Input('date_slicer', 'start_date'),
Input('date_slicer', 'end_date')]
)
def calc_days_span(start, end):
    span = (datetime.strptime(end, '%Y-%m-%d').date() - datetime.strptime(start, '%Y-%m-%d').date()).days + 1  #Add 1 to be inclusive of start and end days
    return s_to_easyDate(start) + ' - ' + s_to_easyDate(end) + '.' + ' ('  + str(span) + ' days)'




if __name__ == '__main__':
    dash_app.run_server(debug=True)
    callback0('input')
