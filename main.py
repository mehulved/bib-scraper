#!/usr/bin/env python

import ConfigParser
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from bs4 import BeautifulSoup
import simplejson
import urllib
import unicodecsv as csv
import os
import sys
from time import sleep
from datetime import datetime
import codecs

# Read config file
config = ConfigParser.ConfigParser()
config.readfp(open(sys.argv[1]))
eventname=config.get('event','name')
bibstart=config.getint('bib','start')
bibend=config.getint('bib', 'end')

# Application Variables
results_url="https://www.sportstimingsolutions.in/resultstable1.php"

print("Job started at: {}".format(datetime.now()))


def get_event_id(eventname):
    event_search_url="https://www.sportstimingsolutions.in/result_search.php?term=" + eventname.replace(' ','+')
    req = requests.get(event_search_url, verify=False)
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
    session.verify = False
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

for bibno in range(bibstart,bibend,1):
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
        with codecs.open(userfile, 'w', 'utf-8') as participant_html:
            participant_html.write(content)
    else:
        fetch_time = datetime.now()
        print("Opening existing data for bib no: {} at {}.".format(bibno, fetch_time))
        with open(userfile, 'r') as contentfile:
            content = contentfile.read()

    # Parsing the html content
    soup = BeautifulSoup(content, "html.parser")
    if len(soup.findAll(name="div")) > 0:
        participant_name = soup.find(name="input", attrs={"name": "firstname"}).get("value")
        category = soup.find(name="input", attrs={"name": "race_name"}).get("value")
        gun_time = soup.find(name="input", attrs={"name": "gun_time"}).get("value")

        rank_name = soup.findAll(name="input", attrs={"name": "bracket_name[]"})
        ranks = soup.findAll(name="input", attrs={"name":"bracket_rank[]"})
        if len(ranks) > 0:
            rank_overall = ranks[0].get("value")
            if len(ranks) == 1: ## Puru put this in
                rank_gender = -999999
            else:
                rank_gender = ranks[1].get("value")
            if len(ranks) == 2:
                ag_name = ""
                rank_ag = ""
            if len(ranks) == 3:
                ag_name = rank_name[2].get("value")
                rank_ag = ranks[2].get("value")

        splits = simplejson.loads(urllib.unquote(soup.findAll(name="input", attrs={"name":'split_time'})[0].get("value")))
        if len(splits) > 0:
            nettime = splits[0][1]
            netpace = splits[0][2]

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

        result['ag_name'] = ag_name
        fieldnames.append('ag_name')

        result["net_time"] = nettime
        fieldnames.append("net_time")

        result["net_pace"] = netpace
        fieldnames.append("net_pace")

        result['rank_overall'] = rank_overall
        fieldnames.append('rank_overall')

        result['rank_gender'] = rank_gender
        fieldnames.append('rank_gender')

        while False:
            try:
                result['rank_gender'] = rank_gender
                fieldnames.append('rank_gender')
            except:
                print("Could not find or handle gender rank for Bib #{}".format(bibno))
                break

        result['rank_ag'] = rank_ag
        fieldnames.append('rank_ag')

        for split in splits:
            if len(split) > 1:
                split_name = split[0].strip().replace('+',' ').replace('Split @ ','')
                split_time = split[1].strip()
                split_pace = split[2].strip()
                split_speed = split[3].strip()

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

    print("\n\n\n")

print("Job ended at: {}".format(datetime.now()))

