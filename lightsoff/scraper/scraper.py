

'''
    scraper.py

    This script should be used by calling the scrape function and passing the 
    last processed document id by parameter.

    The outputs will be saved in the outputs folder if a new document id is found.
'''

import os
from lxml import html
import re
import requests
import shutil

base_dir = f"{os.getcwd()}/lightsoff"
scraperFolder = f"{base_dir}/scraper/"
hardcodedFolder = f"{scraperFolder}/hardcoded/"
outputsFolder = f"{scraperFolder}/outputs/"
lastProcessedFileName = 'last_processed_document_id.txt'
placesFileName = 'places.json'
schedulesFileName = 'schedules.json'


def scrape(last_document_id):

    print("Scraper started with param %s." % (last_document_id))

    # Get the Google Docs url
    targetUrl = get_target_url()
    if targetUrl == "":
        print("ERROR: Unable to retrieve document from ceb.lk")
        return ""
    print("Target Google Docs URL:" + targetUrl)

    # Get the Google Docs id
    new_document_id = targetUrl.split('/')[5]
    print("Target Google Docs ID:" + new_document_id)

    # Check if should continue processing
    isValidId = last_document_id != new_document_id
    if not isValidId:
        print("Skipping target, this file is already processed")
        return ""
    print("Detected new document to process")

    #TODO: Download the Google Docs
    
    #TODO: Extract data

    #TODO: Save extracted data to outputs folder
    #TEMP: Copy hardcoded files into output
    print("Saving data to output folder")
    shutil.copy(hardcodedFolder + placesFileName, outputsFolder)
    shutil.copy(hardcodedFolder + schedulesFileName, outputsFolder)

    # Save processed doc id to outputs folder
    with open(outputsFolder + lastProcessedFileName, 'w') as f:
        f.write(new_document_id)

    print("Scraper finished, new data available")
    return new_document_id


def get_target_url():
    # Get links from ceb.lk home page
    req = requests.get('https://ceb.lk', verify=False)
    webpage = html.fromstring(req.content)
    links = webpage.xpath('//a/@href')

    # Search google drive links
    gd_link = [i for i in links if 'drive.google.com' in i]
    gd_link = list(set(gd_link))
    if len(gd_link)>0:
        return gd_link[0]

    # Search bit.ly links and resolve it
    bl_link = [i for i in links if 'bit.ly' in i]
    bl_link = list(set(bl_link))
    if len(bl_link)>0:
        print("Resolving Bit.ly: %s" % (bl_link[0]))
        req = requests.get(bl_link[0] + '+', verify=False)
        resolved_gd_link = re.search("\"long_url\": \"(.*)\", \"user_hash\": \"", str(req.content)).group(1)
        print("Resolved Bit.ly: %s" % (resolved_gd_link))
        return resolved_gd_link

    return ""