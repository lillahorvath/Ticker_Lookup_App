# dependencies
from flask import Flask, render_template, request, redirect
import requests
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.resources import CDN
from bokeh.embed import json_item 
import simplejson
import os

# initialize objects
app = Flask(__name__)
app.user_input = {}
app.user_input['req_fail'] = 'False'
app.tdata = pd.DataFrame()

# app home
@app.route('/home', methods=['GET','POST'])
def start_page():
	if request.method == 'GET':
		return render_template('start_page.html')
	else:
		# get user input
		app.user_input['ticker'] = request.form['ticker']
		app.user_input['toplot'] = request.form.getlist('price')

		# if missing user data
		if app.user_input['ticker'] == '' or len(app.user_input['toplot']) == 0 :
			return redirect('/cantshow')
		# get data
		else: 
			return redirect('/')

# can't show the plot
@app.route('/cantshow')
def cantshow():
	
	# if missing user data
	if app.user_input['ticker'] == '' and len(app.user_input['toplot']) == 0 :
		return render_template('except_page.html', message = 'Please enter a ticker symbol and select a price to plot')
	elif app.user_input['ticker'] == '':
		return render_template('except_page.html', message = 'Please enter a ticker symbol')	
	elif len(app.user_input['toplot']) == 0:
		return render_template('except_page.html', message ='Please select a price to plot')

	# if invalid user data
	if app.user_input['req_fail']:
		return render_template('except_page.html', message = 'Please enter a valid ticker symbol')	

# prepare to show (or not show) the plot
@app.route('/')
def root():

	# get data
	fixed_url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&outputsize=compact&apikey=69N0R6WUDFW63EKD'
	ticker = dict(symbol = app.user_input['ticker'])
	
	try: 
		tdata = requests.get(url=fixed_url, params=ticker)
		
		# format data
		tdata_dict = tdata.json()
		tdata_df = pd.DataFrame(tdata_dict['Time Series (Daily)'])
		tdata_df = tdata_df.transpose()
		tdata_df = tdata_df[['1. open', '4. close']]
		tdata_df.columns = ['open', 'close']
		tdata_df['open'] = tdata_df['open'].astype(float)
		tdata_df['close'] = tdata_df['close'].astype(float)

		# set data
		app.tdata = tdata_df
		app.user_input['req_fail'] == 'False'

		return render_template('plot_page.html', resources=CDN.render())

	except: 
		app.user_input['req_fail'] == 'True'
		
		return redirect('/cantshow')

# show the plot
@app.route('/showme')
def show_me():

	# plot data
	tdata_df = app.tdata
	tdata_df = tdata_df[:30]
	tdata_df.index = pd.to_datetime(tdata_df.index, format='%Y-%m-%d')
	toplot_df = ColumnDataSource(tdata_df)

	p = figure(title="Alpha Vantage Stock Prices - last 30 days", 
		x_axis_label='date', 
        x_axis_type='datetime',
        tools="pan,box_zoom,reset,save")

	if len(app.user_input['toplot']) == 2:
	    p.line(x = 'index', y = 'open', legend=app.user_input['ticker'] + ' open', line_width=2, line_color = 'blue', source=toplot_df)   
	    p.line(x = 'index', y = 'close', legend=app.user_input['ticker'] + ' close', line_width=2, line_color = 'orange', source=toplot_df)   
	else: 
	    if 'open' in app.user_input['toplot']:
	        p.line(x = 'index', y = 'open', legend=app.user_input['ticker'] + ' open', line_width=2, line_color = 'blue', source=toplot_df) 
	    else: 
	        p.line(x = 'index', y = 'close', legend=app.user_input['ticker'] + ' close', line_width=2, line_color = 'orange', source=toplot_df)   

	return simplejson.dumps(json_item(p, "myplot"))
	
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

#if __name__ == '__main__':
#  app.run(port=33507)
