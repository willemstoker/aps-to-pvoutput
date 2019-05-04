#!/usr/bin/python

import requests
import json
from datetime import date
from datetime import datetime
import os.path

#id's and keys
ECU_ID = '<ecuid>'
PV_OUTPUT_SYSTEMID = '<systemid>'
PV_OUTPUT_APIKEY = '<apikey>'

#enter a path and filename below, a file wil be create to save the last update datetime
LAST_UPDATE_FILE = "<path/file>" #example "text.txt" or "/home/pi/aps/lastupdate"

#usually all below this point should not be modified
MAX_NUMBER_HISTORY = 6
APSYSTEMS_URL = 'http://api.apsystemsema.com:8073/apsema/v1/ecu/getPowerInfo'
PVOUTPUT_URL = 'http://pvoutput.org/service/r2/addstatus.jsp'

def readLastUpdate():
    f = open(LAST_UPDATE_FILE,"r")
    datestring = f.read()
    f.close()
    return datetime.strptime(datestring, "%Y%m%d %H:%M")

def writeLastUpdate(timestringminutes):
    f = open(LAST_UPDATE_FILE,"w+")
    f.write(getDateStringOfToday()+ ' ' +timestringminutes)
    f.close()

def getDateStringOfToday():
    return date.today().strftime("%Y%m%d");

def getDataFromAPS():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
      'ecuId': ECU_ID,
      'filter': 'power',
      'date': getDateStringOfToday()
    }

    response = requests.post(APSYSTEMS_URL, headers=headers, data=data)
    return response.json();

def sendUpdateToPVOutput(timestringminutes, powerstring):
    pvoutputdata = {
      'd': getDateStringOfToday(),
      't': timestringminutes,
      'v2': powerstring
    }

    headerspv = {
        'X-Pvoutput-SystemId': PV_OUTPUT_SYSTEMID,
        'X-Pvoutput-Apikey': PV_OUTPUT_APIKEY
    }

    responsepv = requests.post(PVOUTPUT_URL, headers=headerspv, data=pvoutputdata)

    print ("Response: " + responsepv.text + " updated: " + timestringminutes + " power: " + powerstring)

if not os.path.isfile(LAST_UPDATE_FILE):
    writeLastUpdate('00:00') #create file for the first time

rootdict = getDataFromAPS()
timesstring = rootdict.get("data").get("time")
powersstring = rootdict.get("data").get("power")

timelist = json.loads(timesstring)
powerlist = json.loads(powersstring)
latestUpdate = readLastUpdate()
print("Found latest update: ")
print(latestUpdate)

i = len(timelist) - 1
count = 0;
while i >= 0 and count < MAX_NUMBER_HISTORY:
    timestringminutes = timelist[i][:-3] #get time and strip the seconds
    powerstring = powerlist[i] #get power

    currentUpdate = datetime.strptime(getDateStringOfToday()+ ' ' +timestringminutes, "%Y%m%d %H:%M")

    if currentUpdate > latestUpdate:
        sendUpdateToPVOutput(timestringminutes, powerstring)
    else:
        print("No update needed for: " + timestringminutes)

    if count == 0:
        writeLastUpdate(timestringminutes)
        
    i -= 1
    count += 1
