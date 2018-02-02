#!/usr/bin/env python

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from bs4 import BeautifulSoup
import simplejson
import urllib
import csv
import os
import sys
from time import sleep
from datetime import datetime

# User Variables
eventname="Tata Mumbai Marathon 2018"

# Application Variables
results_url="https://www.sportstimingsolutions.in/resultstable1.php"

print("Job started at: {}".format(datetime.now()))


def get_event_id(eventname):
    event_search_url="https://www.sportstimingsolutions.in/result_search.php?term=" + eventname.split(' ')[0]
    req = requests.get(event_search_url)
    if req.ok:
        event_list = simplejson.loads(req.content)
        for event in event_list:
            if event['value'] == eventname:
               return event['id']
    else:
        print(req.reason)
        sys.exit(1)


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

eventdir = eventname.replace("+","_")
if not os.path.exists(eventdir):
    os.makedirs(eventdir)
eventhtml = os.path.join(eventdir, "html")
if not os.path.exists(eventhtml):
    os.makedirs(eventhtml)

eventId = get_event_id(eventname)

for bibno in range(1,200,1):
    rank = []
    participants = []
    rank_category = []
    result = {}
    fieldnames = []
    participant_name=""

    
    #Fetching the data
    userfile = os.path.join(eventhtml, str(bibno) + ".html") 
    if not os.path.exists(userfile):
        fetch_time = datetime.now()
        print("Requesting data for bib no: {} at {}.".format(bibno, fetch_time))
        postdata={"eventId":eventId, "eventname":eventname, "bibno":bibno}
        req = requests_retry_session().post(results_url, data=postdata)
        content = req.text
        with open(userfile, 'w') as participant_html:
            participant_html.write(content)
    else:
        print("Opening existing file for bib no: {}.".format(bibno))
        with open(userfile, 'r') as contentfile:
            content = contentfile.read()

    # Parsing the html content
    soup = BeautifulSoup(content, "html.parser")
    heading_tags = soup.find_all(['h1','h2','h3','h4','h5'])
    if len(heading_tags) > 0:
        participant_name = heading_tags[2].text
        category = heading_tags[4].text

        timing_table = soup.table.extract()
        participant_timing = timing_table.find_all('td')
        if len(participant_timing) > 0:
            nettime = participant_timing[0].text
            netpace = participant_timing[1].text

        rank_table = soup.table.extract()
        ranks = rank_table.find_all('td')
        if len(ranks) > 0:
            rank_overall = ranks[0].text.replace('of ','/')
            rank_gender = ranks[1].text.replace('of ','/')
            if len(ranks) == 2:
                rank_ag = ""  
            if len(ranks) == 3:
                rank_ag = ranks[2].text.replace('of ','/')

        split_list = []
        splits_table = soup.table.extract()
        splits_header_row = splits_table.tr.extract()
        splits_header = splits_header_row.find_all('th')
        if len(splits_header) > 0:
           try:
               while True:
                   split_row = splits_table.tr.extract()
                   split = split_row.find_all('td')
                   if len(split) > 0:
                      split_list.append(split)
           except:
               pass
        
    
        # Write the data to a dictionary
        
        print("Processing bib no: {}".format(bibno))

        result["fetch_time"] = fetch_time
        fieldnames.append("fetch_time")

        result["bib"] = bibno
        fieldnames.append("bib")
    
        result["name"] = participant_name
        fieldnames.append("name")
        
        result["category"] = category
        fieldnames.append("category")
        
        result["net_time"] = nettime
        fieldnames.append("net_time")
        
        result["net_pace"] = netpace
        fieldnames.append("net_pace") 
        
        result['rank_overall'] = rank_overall
        fieldnames.append('rank_overall')

        result['rank_gender'] = rank_gender
        fieldnames.append('rank_gender')

        result['rank_ag'] = rank_ag
        fieldnames.append('rank_ag')

        for split in split_list:
            if len(split) > 1:
                split_name = split[0].text.strip().replace('Split @ ','')
                split_time = split[1].text.strip()
                split_pace = split[2].text.strip()
                split_speed = split[3].text.strip()
            elif len(split) == 1: 
                gun_time = split[0].text.strip().replace('Full Course - Gun Time - ','')
        
            result[split_name + " time"] = split_time
            fieldnames.append(split_name + " time")
        
            result[split_name + " pace"] = split_pace
            fieldnames.append(split_name + " pace")
        
            result[split_name + " speed"] = split_speed
            fieldnames.append(split_name + " speed")

        result["gun_time"] = gun_time
        fieldnames.append('gun_time')
        
       
        #Generate dictionary of result
        # Write to csv
        eventfile= os.path.join(eventdir, category + ".csv")
        file_exists = os.path.isfile(eventfile)
        with open(eventfile, "ab") as csvfile:
            writer = csv.DictWriter(csvfile,fieldnames=fieldnames,delimiter=",",quotechar='"',quoting=csv.QUOTE_ALL)
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)

    sleep(2) # wait for 2 seconds after every request, to not overwhelm the server
    print("\n\n\n")

print("Job ended at: {}".format(datetime.now()))

