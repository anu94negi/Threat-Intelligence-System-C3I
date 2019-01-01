from flask import Flask
from flask_cors import CORS
from flask import  make_response, request, current_app  
from functools import update_wrapper
from datetime import timedelta  
import mysql.connector
from flask import request
import pandas as pd
import json
import time
import csv
from flask_cors import cross_origin
mydb = mysql.connector.connect( host="localhost", user="root", passwd="qwertyuiop", database="ugp_analytics" )

app = Flask(__name__)
CORS(app)

data = pd.DataFrame() #creates a new dataframe that's empty
countrydata = {}
normalLogs = 0
abnormalLogs = 0
iplocations = []
ipcountries = {}
lastLog = {}
lastminrespvalues = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
lastminrespqueue = []
lastLocationsBuffer = []

with open('ip_loc3.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count != 0:
            try:
                iplocations.append([float(row[4]), float(row[5]), 1])
                ipcountries[row[0]] = row[1]
            except ValueError:
                print('Non float')
        line_count += 1

@app.route('/push-log', methods=['POST'])
def pushLog():
    global normalLogs, abnormalLogs, countrydata, lastminrespqueue, lastminrespvalues, lastLog, lastLocationsBuffer
    currtime = time.time()
    json = request.get_json(force=True)
    for i in range(0, json['response1']['Total']):
        resp = json['response1']['log'][str(i)]['response']
        if(json['response2'][str(i)]['public']=='true'):
            cont = json['response2'][str(i)]['detail_loc']['country']
            lastminrespqueue = [{'value': resp[0], 'timestamp': currtime}] + lastminrespqueue
            lastminrespvalues[resp[0]] += 1
            try:
                if(cont != ''):
                    countrydata[cont] += 1
            except KeyError:
                countrydata[cont] = 1
            if(json['response1']['log'][str(i)]['response'][0] in ['4', '5']):
                lastLocationsBuffer.append([json['response2'][str(i)]['detail_loc']['lat'], json['response2'][str(i)]['detail_loc']['long']])
	last = json['response1']['Total']-1
	public=None
	if json['response2'][str(last)]['public']=='true':
		public='true'
			
	if last!=None:		
		i1 = ['ip', 'payload', 'Num_byte', 'timestamp', 'response', 'user_agent']
		i2 = ['lat', 'long', 'country']
		lastLog['public'] = (json['response2'][str(last)]['public']=='true')
		for i in i1:
			lastLog[i] = json['response1']['log'][str(last)][i]
		for i in i2:
			lastLog[i] = json['response2'][str(last)]['detail_loc'][i]
		backtime = currtime - 60
		while(lastminrespqueue[len(lastminrespqueue)-1]['timestamp'] < backtime):
			el = lastminrespqueue.pop()
			lastminrespvalues[el['value']] = lastminrespvalues[el['value']] - 1
		abnormalLogs += json['response1']['abnormal']
		normalLogs += (json['response1']['Total'] - json['response1']['abnormal'])
		return ""
	else:
		abnormalLogs += json['response1']['abnormal']
		normalLogs += (json['response1']['Total'] - json['response1']['abnormal'])c
		lastlog['country']="NA"
		return "all private ips"
@app.route('/get-analytics', methods=['POST','OPTIONS'])
def analyze():
    global normalLogs, abnormalLogs, ipcountries, countrydata, lastminrespvalues, lastLog, lastLocationsBuffer
    totalLogs = normalLogs + abnormalLogs
    ret = {}
    requests = {}
    requests['normal'] = normalLogs
    requests['abnormal'] = abnormalLogs
    requests['total'] = abnormalLogs + normalLogs
    ret['requests'] = requests
    ret['lastminrespvalues'] = lastminrespvalues
    ret['lastLog'] = lastLog
    ret['lastLocations'] = lastLocationsBuffer
    lastLocationsBuffer = []
    return json.dumps(ret)


@app.route('/get-mapdata', methods=['POST','OPTIONS'])
def maps():
    global iplocations
    return json.dumps(iplocations)
