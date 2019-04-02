# -*- coding: utf-8 -*-
from flask import Flask
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
from scipy import stats
import numpy as np

import plotly.graph_objs as go

import localDBConnector as db
import urlparse

import sys
import os
import json

import csv

import time
import datetime

import functools32


local_version = False

if local_version:
	database_url = sys.argv[1]
else:
	server = Flask('Influencer Form Prototype')
	server.secret_key = os.environ.get('secret_key', 'secret')
	database_url = os.environ["DATABASE_URL"]

urlparse.uses_netloc.append('postgres')
url = urlparse.urlparse(database_url)

def getDBConnection():
	return db.SQLConnector(url)


colour_palette = ['rgb(240,21,22)',
                  'rgb(22,96,185)',
                  'rgb(6,193,95)',
                  'rgb(255,234,0)',
                  'rgb(163,95,224)',                  
                  'rgb(209,210,212)',
                  'rgb(204,123,6)']


if local_version:
	app = dash.Dash()
else:
	app = dash.Dash('Trump Dash', server=server)
	app.config.supress_callback_exceptions = True	


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Trump Tweets</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
        </footer>
    </body>
</html>
'''

external_css = ["https://s3.eu-west-2.amazonaws.com/desigual-decks-2/skeleton_dash_fixed.css",
				"https://s3.eu-west-2.amazonaws.com/desigual-decks-2/dcc_component.css",
				"//fonts.googleapis.com/css?family=Poppins",
				"//fonts.googleapis.com/css?family=PT+Serif"]

for css in external_css:
	app.css.append_css({ "external_url": css })

if 'DYNO' in os.environ:
	app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })

metrics = ["RETWEETS","FAVOURITES"]
heatmap_metrics = ["NUMBER OF POSTS","RETWEETS","FAVOURITES"]


app.layout = html.Div([
		html.Div([# page 1	


			html.Div([
	            html.Div([

		            html.Div([
		                html.H6('Choose Date Range:', className = "input__text"),
		                html.Div([
		                	dcc.DatePickerRange(
						        id='date-picker-range',
						        min_date_allowed=datetime.date(2011, 1, 1),
						        display_format="DD/MM/YY",
	        					initial_visible_month=datetime.date(2017, 8, 5)
							)
			            ],)

		                ]
		            ),
	            	html.Div([
		                html.H6('Filter by caption:', className = "input__text"),
		                dcc.Input(id='caption-search-input-box', type="text")

		                ],
		            ),
	            	html.Div([
		                html.H6('Try some suggestions:', className = "input__text"),
		                html.Button('MAGA',id='maga-button'),
		                html.Button('Crooked Hillary',id='crooked-hillary-button'),
		                html.Button('Witch Hunt',id='witch-hunt-button'),
		                html.Button('Obama',id='obama-button')

		                ],
		            ),
	            ],className='input-wrapper'),
            	html.Div(
		            [dcc.Graph(id='main-graph',
			            		config={'displayModeBar': False},
		            			className='heatmap-graph')],
			        className='main-graph-wrapper'
			    ),
			    html.Div(id='selected-post-div',
                    	 className='selected-post-wrapper')	

	        ],className='l-subgrid'),

		    html.Div([
		    	html.Div([
		    		html.Div(id='post-percentage-div'),
		    		html.Div(id='favourite-ratio-div')
		    	],className='stat-box-1-wrapper'),
            	html.Div([
            		dcc.Graph(id='heatmap-graph',
		            		config={'displayModeBar': False},
		            		className='heatmap-graph')
		        ],className='heatmap-wrapper'),
		        html.Div([
		        	html.Div(id='regress-stat-div')
		        ],className='stat-box-2-wrapper')		     
            ],className='l-subgrid'),
		], className='l-grid'),
	])



@functools32.lru_cache(maxsize=32)
def getTrumpTwitterPostsDataframe(start_date,
								end_date,
								keywords=None):
	c2 = getDBConnection()
	data = c2.getTrumpTweetsData(start_date=start_date,
												 end_date=end_date,
												 keywords=keywords)
	#print data[0]

	df = pd.DataFrame(data, columns=["POST ID","HANDLE","DATE POSTED","TEXT","CONTRIBUTORS","IN REPLY TO STATUS ID","TWEET SOURCE","IN REPLY TO SCREENNAME","RETWEETS","FAVOURITES","URL","HASHTAGS","MEDIA URL"])
	
	return df[df['TEXT'].str.startswith('RT @')==False]


'''*****************************************************************************************
Selected Post functions
*******************************************************************************************'''	

def checkSelectedPost(clickData,
				 	  start_date,
				 	  end_date):
	df = getTrumpTwitterPostsDataframe(start_date,
									end_date)
	if clickData:
		post_id = clickData["points"][0]["customdata"]
		if post_id in df['POST ID'].values:
			return df[df['POST ID'] == post_id]
	return df.tail(n=1)


@app.callback(
    Output('selected-post-div', 'children'),
    [Input('main-graph', 'clickData'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('caption-search-input-box', 'value')])
def display_selected_post(clickData,
				 			start_date,
				 			end_date,
				 			search_term):
	if not start_date: start_date = datetime.date(2000,1,1)	
	else: start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
	if not end_date: end_date = datetime.date.today()
	else: end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

	df_selection = checkSelectedPost(clickData,
								 	  start_date,
								 	  end_date)
	print df_selection
	if df_selection.empty:
		return None
	else:
		return [
				html.Iframe(src="https://twitframe.com/show?url=https://twitter.com/realdonaldtrump/status/"+df_selection["POST ID"].values.tolist()[0],
							style={'height':'500',
									'border':'0',
									'frameborder':'0',
									'theme':'dark'})			          
	        ]


'''**************************************************************************************************************************8
	CAPTION BOX FUNCTIONS
**************************************************************************************************************************************'''

@app.callback(
    Output('caption-search-input-box', 'value'),
    [Input('maga-button', 'n_clicks'),
    Input('maga-button', 'n_clicks_timestamp'),
    Input('crooked-hillary-button', 'n_clicks'),
    Input('crooked-hillary-button', 'n_clicks_timestamp'),
    Input('witch-hunt-button', 'n_clicks'),
    Input('witch-hunt-button', 'n_clicks_timestamp'),
    Input('obama-button', 'n_clicks'),
    Input('obama-button', 'n_clicks_timestamp')])
def update_caption_box(maga_clicks,
					 maga_timestamp,
					 crooked_hillary_clicks,
					 crooked_hillary_timestamp,
					 witch_hunt_clicks,
					 witch_hunt_timestamp,
					 obama_clicks,
					 obama_timestamp):
	if maga_clicks is None and crooked_hillary_clicks is None and witch_hunt_clicks is None and obama_clicks is None:
		return None
	if (maga_timestamp > crooked_hillary_timestamp) and (maga_timestamp > witch_hunt_timestamp) and (maga_timestamp > obama_timestamp):
		return "MAGA"
	elif (crooked_hillary_timestamp > witch_hunt_timestamp) and (crooked_hillary_timestamp > obama_timestamp):
		return "Crooked Hillary"
	elif (witch_hunt_timestamp > obama_timestamp):
		return "Witch Hunt"
	else:
		return "Obama"

'''****************************************************************************************************************************
	SCATTER GRAPH FUNCTIONS
*****************************************************************************************************************************'''
def getEmptyScatterPlot():
	data = []
	data.append(go.Scatter( x=[],y=[]))	
	figure = {	'data': data,
				'layout': go.Layout(showlegend=False)
		    }
	return figure

@app.callback(
    Output('main-graph', 'figure'),
    [Input('main-graph', 'clickData'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('caption-search-input-box', 'value')])
def update_scatter_plot(clickData,
						 start_date,
						 end_date,
						 search_term):
	if not start_date: start_date = datetime.date(2000,1,1)	
	else: start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
	if not end_date: end_date = datetime.date.today()
	else: end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
	
	#if search_clicks=='No Filter': search_term=None

	df = getTrumpTwitterPostsDataframe(start_date,
									end_date)

	
	if df.empty:
		return getEmptyScatterPlot()


	if clickData:
		post_id = clickData["points"][0]["customdata"]
	else:
		post_id = None

	df_post = pd.DataFrame()
	if post_id in df['POST ID'].values:
		df_post = df[df['POST ID'] == post_id]	
	else:
		df_post = df.tail(n=1)	

	data = []

	print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

	if search_term:
		df_search = df[df['TEXT'].str.contains(search_term,case=False)==True]
		df = df[df['TEXT'].str.contains(search_term,case=False)==False]
		data.append(go.Scatter( x=df["DATE POSTED"],
						        y=df["FAVOURITES"], 
						        customdata = df["POST ID"],  
						        mode='markers',
						        name="",
						        marker=dict(
						            color=colour_palette[0],
						        ),
						        text=df['HANDLE'],
						        opacity=0.6
						    ))

		
		data.append(go.Scatter( x=df_search["DATE POSTED"],
						        y=df_search["FAVOURITES"], 
						        customdata = df_search["POST ID"],  
						        mode='markers',
						        name="",
						        marker=dict(
						            color=colour_palette[1],
						        ),
						        text=df_search['HANDLE'],
						        opacity=0.9
						    ))
		date_list = df_search["DATE POSTED"].tolist()
		engagement_list = df_search["FAVOURITES"].tolist()
		trendline_x_data = [int((row- date_list[-1]).total_seconds()) for row in date_list]
		xi = np.array(trendline_x_data)
		slope, intercept, r_value, p_value, std_err = stats.linregress(trendline_x_data,engagement_list)
		line = slope*xi+intercept

		data.append(go.Scatter( x=date_list,
							    y=line,
							    mode='lines',
							    name="All Posts",
							    marker=dict(
							        color=colour_palette[1],
							    ),
							    opacity=0.6,
							    showlegend=False
							))
	else:
		data.append(go.Scatter( x=df["DATE POSTED"],
						        y=df["FAVOURITES"], 
						        customdata = df["POST ID"],  
						        mode='markers',
						        name="",
						        marker=dict(
						            color=colour_palette[0],
						        ),
						        text=df['HANDLE'],
						        opacity=0.6
						    ))

	date_list = df["DATE POSTED"].tolist()
	engagement_list = df["FAVOURITES"].tolist()
	trendline_x_data = [int((row- date_list[-1]).total_seconds()) for row in date_list]
	xi = np.array(trendline_x_data)
	slope, intercept, r_value, p_value, std_err = stats.linregress(trendline_x_data,engagement_list)
	line = slope*xi+intercept

	data.append(go.Scatter( x=date_list,
						    y=line,
						    mode='lines',
						    name="All Posts",
						    marker=dict(
						        color=colour_palette[0],
						    ),
						    opacity=0.6,
						    showlegend=False
						))
	max_y = 0.0
	max_y = df["FAVOURITES"].max()	
	y_axis_range = [0.0,max_y+0.1*max_y]

	if not df_post.empty:
		data.append(go.Scatter( x=df_post["DATE POSTED"],
						        y=df_post["FAVOURITES"], 
						        customdata = df_post["POST ID"],  
						        mode='markers',
						        name='Selected Post',
						        marker=dict(
						            color='rgb(0,0,0)',
						        ),
						        opacity=1.0,
	    						showlegend=False
							    ))

	figure = {	'data': data,
				'layout': go.Layout(title='What nonsense is he tweeting?',
									titlefont=dict(size=20,family='PT Serif',color='black'),
									showlegend=False,
									hovermode='closest',
									yaxis=dict(range=y_axis_range),
				                    height=450,
				                    autosize=True)
		    }
	print "***********************************************************************************"
	return figure



'''**************************************************************************************************************************
	HEATMAP FUNCTIONS
**************************************************************************************************************************'''

@functools32.lru_cache(maxsize=32)
def getTwitterPostsHeatmapDataframe(metric,
									  start_date,
									  end_date,
									  keywords=[]):

	c =  getDBConnection()
	data = c.getTrumpTweetsData(keywords=keywords,
								 start_date=start_date,
								 end_date=end_date)
	#print data
	parsed_data = []
	for row in data:
		row_list = [row[2],row[8],row[9]]
		parsed_data.append(row_list)
	df = pd.DataFrame(parsed_data, columns=["DATE POSTED","RETWEETS","FAVOURITES"])

	df["DATE POSTED"] = pd.DatetimeIndex(df["DATE POSTED"])
	df.set_index(keys="DATE POSTED",inplace=True)
	print df

	offset_hours=-5

	data_array = []
	for weekday in range(0,7):
		weekday_array = []
		df_week = df[df.index.weekday == weekday]
		for hour in range(0,24):
			if metric == "RETWEETS":
				mean_metric = df_week.between_time(datetime.time((hour-offset_hours)%24,0,0),datetime.time((hour-offset_hours+1)%24,0,0))["RETWEETS"].mean()
			elif metric == "FAVOURITES":
				mean_metric = df_week.between_time(datetime.time((hour-offset_hours)%24,0,0),datetime.time((hour-offset_hours+1)%24,0,0))["FAVOURITES"].mean()
			else:
				mean_metric = df_week.between_time(datetime.time((hour-offset_hours)%24,0,0),datetime.time((hour-offset_hours+1)%24,0,0)).shape[0]
			weekday_array.append(mean_metric)				
		data_array.append(weekday_array)

	return data_array


def getHeatmap(data_array):
	data = []
	data.append(go.Heatmap( z= data_array,
							x=['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23'],
					        y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday','Sunday'],
					        colorscale= [[0, 'rgb(0,0,0)'], [0.25, 'rgb(22,96,185)'], [0.5, 'rgb(163,95,224)'], [0.75, 'rgb(240,21,22)'], [1, 'rgb(255,234,0)']] ))
					        #colorscale= [[0, 'rgb(22,96,185)'], [0.33, 'rgb(163,95,224)'], [0.66, 'rgb(240,21,22)'], [1, 'rgb(255,234,0)']] ))	
	figure = {	'data': data,
				'layout': go.Layout(title='What time of the day is he tweeting this nonsense?',
									titlefont=dict(size=20,family='PT Serif',color='black'),
									showlegend=False,
									yaxis=dict(showticklabels=True),
									xaxis=dict(showticklabels=True,
												#autotick=False,
												dtick=0,
												ticklen=1))}
	return figure	


@app.callback(
    Output('heatmap-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('caption-search-input-box', 'value')])
def update_heatmap(start_date,
				 end_date,
				 search_term):

	if not start_date: start_date = datetime.date(2000,1,1)	
	else: start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
	if not end_date: end_date = datetime.date.today()
	else: end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

	metric = "NUMBER OF POSTS"
	data_array = getTwitterPostsHeatmapDataframe( metric,
									  start_date,
									  end_date,
									  search_term)

	print data_array

	
	return getHeatmap(data_array)


'''****************************************************************************************************************************
	STAT FUNCTIONS
*****************************************************************************************************************************'''


@app.callback(
    Output('post-percentage-div', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('caption-search-input-box', 'value')])
def update_percentage_stat(start_date,
						 end_date,
						 search_term):
	if not start_date: start_date = datetime.date(2000,1,1)	
	else: start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
	if not end_date: end_date = datetime.date.today()
	else: end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
	
	if search_term is None:
		return None

	df = getTrumpTwitterPostsDataframe(start_date,
									end_date)

	
	if df.empty:
		return None

	df_search = df[df['TEXT'].str.contains(search_term,case=False)==True]
	if df_search.empty:
		return None

	percentage = float(df_search.shape[0])/float(df.shape[0])

	return html.Div([html.H2("{:.2f}".format(100.0*float(percentage)) + "%",className='stat__number'),
			  		html.H2(" of all posts contain " + search_term,className='stat__text')])
	#return "{:.2f}".format(100.0*float(percentage)) + "% of all posts contain " + search_term


@app.callback(
    Output('favourite-ratio-div', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('caption-search-input-box', 'value')])
def update_ratio_stat(start_date,
						 end_date,
						 search_term):
	if not start_date: start_date = datetime.date(2000,1,1)	
	else: start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
	if not end_date: end_date = datetime.date.today()
	else: end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
	
	if search_term is None:
		return None

	df = getTrumpTwitterPostsDataframe(start_date,
									end_date)

	
	if df.empty:
		return None

	df_search = df[df['TEXT'].str.contains(search_term,case=False)==True]
	if df_search.empty:
		return None

	percentage = float(df_search['FAVOURITES'].mean())/float(df['FAVOURITES'].mean())
	return html.Div([html.H2("{:.2f}".format(float(percentage)),className='stat__number'),
			  		html.H2(" is the ratio of the average number of favourites for " + 
			  				search_term + 
			  				" posts compared to all others. A ratio of greater than 1.0 means that " +
			  				search_term +
			  				" posts are more popular than other posts.",className='stat__text')])
	#return "{:.2f}".format(100.0*float(percentage)) + "% is the ratio of the average number of favourites for " + search_term + " posts compared to all others"


@app.callback(
    Output('regress-stat-div', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('caption-search-input-box', 'value')])
def update_regress_stat(start_date,
						 end_date,
						 search_term):
	if not start_date: start_date = datetime.date(2000,1,1)	
	else: start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
	if not end_date: end_date = datetime.date.today()
	else: end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
	
	if search_term is None:
		return None

	df = getTrumpTwitterPostsDataframe(start_date,
									end_date)

	
	if df.empty:
		return None

	df_search = df[df['TEXT'].str.contains(search_term,case=False)==True]
	if df_search.empty:
		return None


	date_list = df_search["DATE POSTED"].tolist()
	engagement_list = df_search["FAVOURITES"].tolist()
	trendline_x_data = [int((row- date_list[-1]).total_seconds()) for row in date_list]
	xi = np.array(trendline_x_data)
	slope_search, intercept, r_value, p_value, std_err_search = stats.linregress(trendline_x_data,engagement_list)

	date_list = df["DATE POSTED"].tolist()
	engagement_list = df["FAVOURITES"].tolist()
	trendline_x_data = [int((row- date_list[-1]).total_seconds()) for row in date_list]
	xi = np.array(trendline_x_data)
	slope_all, intercept, r_value, p_value, std_err_all = stats.linregress(trendline_x_data,engagement_list)

	slope_ratio = slope_search/slope_all

	return html.Div([html.H2("{:.2f}".format(float(slope_ratio)),className='stat__number'),
			  		html.H2("is the ratio between the gradients of the trendlines for " + search_term + 
			  				" posts and other posts. This is a crude statistic but, in general, a ratio of greater than 1.0 indicates that the popularity of " +
			  				search_term + " posts is growing compared to all other posts. Less than 1.0 indicates the popularity of those posts is decreasing." ,className='stat__text')])

if __name__ == '__main__':
    app.run_server(debug=True)
