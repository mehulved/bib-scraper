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
eventname="Airtel Delhi Half Marathon 2017"

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

for bibno in range(1,100000,1):
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
    input_tags = soup.find_all('input')
    for itag in input_tags:
        if 'name' in itag.attrs:
            if itag.attrs['name'] == "firstname":
                participant_name = itag.attrs['value']
            if itag.attrs['name'] == "chip_time":
                nettime = itag.attrs['value']
            if itag.attrs['name'] == "gun_time":
                grosstime = itag.attrs['value']
            if itag.attrs['name'] == "race_name":
                category = itag.attrs['value']
            if itag.attrs['name'] == "split_time":
                splits = eval(urllib.unquote(itag.attrs['value']).decode('UTF8'))
            if itag.attrs['name'] == "gender":
                gender = itag.attrs['value']
            if itag.attrs['name'] == "bracket_rank[]":
                rank.append(itag.attrs['value'])
            if itag.attrs['name'] == "bracket_participants[]":
                participants.append(itag.attrs['value'])
            if itag.attrs['name'] == "bracket_name[]":
                rank_category.append(itag.attrs['value'])
    
    # Write the data to a dictionary
        
    print("Processing bib no: {}".format(bibno))

    result = {}
    fieldnames = []
    
    if participant_name != "":
        result["fetch_time"] = fetch_time
        fieldnames.append("fetch_time")

        result["bib"] = bibno
        fieldnames.append("bib")
    
        result["name"] = participant_name
        fieldnames.append("name")

        result["category"] = category
        fieldnames.append("category")

        result["gender"] = gender
        fieldnames.append("gender")

        result["net_time"] = nettime
        fieldnames.append("net_time")
        
        result["gross_time"] = grosstime
        fieldnames.append("gross_time") 
        
        for split in splits:
            split_name = split[0].replace("Split+@+","")
            split_time = split[1]
            split_pace = split[2]
            split_speed = split[3].replace("+"," ").replace("\\", "")
        
        result[split_name + " time"] = split_time
        fieldnames.append(split_name + " time")
        
        result[split_name + " pace"] = split_pace
        fieldnames.append(split_name + " pace")
        
        result[split_name + " speed"] = split_speed
        fieldnames.append(split_name + " speed")
        
        print(rank_category)
        result['rank_overall'] = rank[0] + "/" + participants[0]
        fieldnames.append('rank_overall')

        if len(rank_category) > 1:
            result['rank_gender'] = rank[1] + "/" + participants[1]
        fieldnames.append('rank_gender')

        if len(rank_category) > 2:
            result['rank_ag'] = rank[2] + "/" + participants[2]
            result['ag_name'] = rank_category[2]
        fieldnames.append('rank_ag')
        fieldnames.append('ag_name')

        #Generate dictionary of result
        # Write to csv
        eventfile= os.path.join(eventdir, category + ".csv")
        file_exists = os.path.isfile(eventfile)
        with open(eventfile, "ab") as csvfile:
            writer = csv.DictWriter(csvfile,fieldnames=fieldnames,delimiter=",",quotechar='"',quoting=csv.QUOTE_ALL)
            if not file_exists:
                writer.writeheader()
            writer.writerow(result)

    print("\n\n\n")

print("Job ended at: {}".format(datetime.now()))

