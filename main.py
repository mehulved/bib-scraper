#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import urllib
import csv
import os
from time import sleep

# User Variables
eventId="37056"
eventname="Tata+Mumbai+Marathon+2018"

# Application Variables
url="https://www.sportstimingsolutions.in/resultstable1.php"

eventdir = eventname.replace("+","_")
if not os.path.exists(eventdir):
    os.makedirs(eventdir)
eventhtml = os.path.join(eventdir, "html")
if not os.path.exists(eventhtml):
    os.makedirs(eventhtml)

for bibno in range(1,10,1):
    rank = []
    participants = []
    rank_category = []
    result = {}
    fieldnames = []
    participant_name=""

    
    #Fetching the data
    userfile = os.path.join(eventhtml, str(bibno) + ".html") 
    if not userfile:
        print("Requesting data for bib no: {}".format(bibno))
        postdata={"eventId":eventId, "eventname":eventname, "bibno":bibno}
        req = requests.post(url, data=postdata)
        content = req.text
        with open(userfile, 'w') as participant_html:
            participant_html.write(content)
    else:
        print("Opening existing file for bib no: {}".format(bibno))
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
        
        print("Processing bib no: {}\n\n".format(bibno))
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

        if rank_ag != "":
            result['rank_ag'] = rank_ag
            fieldnames.append('rank_ag')

        for split in split_list:
           split_name = split[0].text.strip().replace('Split @ ','')
           split_time = split[1].text.strip()
           split_pace = split[2].text.strip()
           split_speed = split[3].text.strip()
        
           result[split_name + " time"] = split_time
           fieldnames.append(split_name + " time")
        
           result[split_name + " pace"] = split_pace
           fieldnames.append(split_name + " pace")
        
           result[split_name + " speed"] = split_speed
           fieldnames.append(split_name + " speed")
        
       
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

