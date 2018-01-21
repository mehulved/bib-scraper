#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import urllib
import csv
import os.path
import time

# User Variables
eventId="35388"
eventname="Airtel+Delhi+Half+Marathon+2017"

# Application Variables
url="https://www.sportstimingsolutions.in/resultstable1.php"

for bibno in range(1,100000,1):
    postdata={"eventId":eventId, "eventname":eventname, "bibno":bibno}
    rank = []
    participants = []
    rank_category = []
    
    #Fetching the data
    req = requests.post(url, data=postdata)
    content = req.text
    
    # Parsing the html content
    soup = BeautifulSoup(content, "html.parser")
    input_tags = soup.find_all('input')
    print input_tags
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
    result = {}
    fieldnames = []
    
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
        split_name = split[0].replace("+"," ")
        split_time = split[1].replace("+"," ")
        split_pace = split[2].replace("+"," ")
        split_speed = split[3].replace("+"," ").replace("\\", "")
    
        result[split_name + " time"] = split_time
        fieldnames.append(split_name + " time")
    
        result[split_name + " pace"] = split_pace
        fieldnames.append(split_name + " pace")
    
        result[split_name + " speed"] = split_speed
        fieldnames.append(split_name + " speed")
    
    print(len(rank_category))
    size = 0
    while size < len(rank_category):
        result[rank_category[size]] = rank[size] + "/" + participants[size]
        fieldnames.append(rank_category[size])
        size = size + 1
    
   
    
    #Generate dictionary of result
    # Write to csv
    eventfile=eventname.replace("+","_") + ".csv"
    file_exists = os.path.isfile(eventfile)
    with open(eventfile, "ab") as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames,delimiter=",",quotechar='"',quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result)

    sleep(2) # wait for 2 seconds after every request, to not overwhelm the server
