#####################
# this script crawls onemap for routing times
# available for walk, pt, drive
# onemap2 beta: https://beta.onemap.sg/main/v2/
# docs: https://docs.onemap.sg/
#####################

import requests
import pandas as pd
import random
import time
from google.colab import files

def get_tokens():
    baseurl = "https://developers.onemap.sg/publicapi/publicsessionid"
    result = requests.get(baseurl).json()
    time.sleep(random.uniform(0.9, 4.5))
    return result

#convert SVY21 to WGS
def SVY_WGS(x, y):
    conv_url= 'https://developers.onemap.sg/commonapi/convert/3414to4326'
    payload = {'X' : x, 'Y' : y}
    return requests.get(conv_url, params = payload).json()

#start code with getting 30 tokens
tok_count = 20

tokens = {}
for i in range(0,tok_count):
    tokens[i] = get_tokens()
    print ('got token '+ str(i))

baseurl = "https://developers.onemap.sg/publicapi/routingsvc/route?"
#specify the routing type
routeType= "pt"

#open input file
infile = pd.read_csv(r"mrts_sample.csv", sep = ";" , header = 0)

#slice to rows desired
infile = infile[front_index:last_index]

#new columns to save data
infile['total_pt_time'] = None
infile['transit_time'] = None
infile['walking_time'] = None
infile['waiting_time'] = None

#make call per row

for index, row in infile.iterrows():

    #randomise token for each call
    #check if token is valid
    ran_t = random.randint(0,tok_count-1)
    #token not valid, need update
    #if expired OR if random index mod 3 == random int (rand & rand lol)
    if (tokens[ran_t]['expiry_timestamp'] < int(time.time())) or (ran_t % 10 == random.randint(0,9)):
        tokens[ran_t] = get_tokens()
        print('updated token')
        curr_token = tokens[ran_t]
    else:
        #token still valid
        curr_token = tokens[ran_t]['access_token']
    
    #INPUT SHOULD BE WGS ALRDY
    #convert coordinates
    #start = [row['OY'], row['DX']]
    #end = str(row['OY']) + ',' + str(row['DX'])

    #create url call
    payload = {'start' : str(row['OY']) +','+ str(row['OX']),
               'end' : str(row['DY']) +','+ str(row['DX']),
               'routeType': routeType ,
               'token': curr_token,
               'date': '2017-11-21',
               'time': '12:00:00',
               'mode' : 'TRANSIT',
               'numItineraries': 1} 
    
    #try max 8 times for connection error catching
    for i in range(0, 8):
        try:
            result = requests.get(baseurl, params = payload).json()
        except:
            time.sleep(random.uniform(5, 10)) # generous sleep time
            print('CALL FAILED, internet problem?')
            print('attempt ' + str(i) )
            continue
        else:
            pass
    
    
    #error catching if input point is invalid
    try:
        if 'plan' in result:
            pt_time = result['plan']
        else:
            pass
    except:
        pass
    
#   FOR PT
    #if route found
    try:
        if len(pt_time['itineraries']) > 0:
            itin = pt_time['itineraries'][0]
            infile.set_value(index, 'total_pt_time', itin['duration'])
            infile.set_value(index, 'transit_time', itin['transitTime'])
            infile.set_value(index, 'waiting_time', itin['waitingTime'])
            infile.set_value(index, 'walking_time', itin['walkTime'])
    except:
        pass

    #if route not found
    try:
        if 'error' in result:
            infile.set_value(index, 'total_pt_time', -9)
            infile.set_value(index, 'transit_time', -9)
            infile.set_value(index, 'waiting_time', -9)
            infile.set_value(index, 'walking_time', -9)
    except:
        pass
    
    print (str(index) + ' done')

    #sleep to not crash server, max is 4 call per sec
    time.sleep(random.uniform(0.5, 6))

#save everything again
of_name = "result"+ str(front_index) + "_" + str(last_index)  +".csv"
infile.to_csv(of_name , index = False)
files.download(of_name)

#output per 100k rows?
    if index != 0 and index % 1000 == 0:
        #save the 1k rows
        infile[ind_front:index].to_csv(r"C:\Users\kelmanc\Desktop\datasets\MRT_PT_mine\result_"+ str(index) +".csv" , index = False)
        #update the top index for the output
        ind_front = index