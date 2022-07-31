'''
    scraper.py

    This script should be used by calling the scrape function and passing the 
    last processed document id by parameter.

    The outputs will be saved in the outputs folder if a new document id is found.
'''

from calendar import c
import copy
from pickle import FALSE, TRUE
from lxml import html
import requests
import camelot
import pandas as pd
from datetime import datetime
import json
import re
import string
import numpy as np
import os
from lxml import html
import re
import requests
import urllib3
import fitz

from collections import Counter
import json
import time
import os
from lightsoff.scraper.DriverManager import DriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

start_datetime = datetime.now()

scraperFolder = f"{os.path.dirname(os.path.abspath(__file__))}/"
tempFolder = f"{scraperFolder}temp/"
currentFileName = 'ceb_current.pdf'
outputsFolder = f"{scraperFolder}outputs/"
lastProcessedFileName = 'last_processed_document_id.txt'
placesFileName = 'places.json'
schedulesFileName = 'schedules.json'
COMPOSITE_SEPARATOR = ";;"

def scrape(last_pdf_id, last_proxy_id):

    print("Scraper started with params '%s' and '%s'" % (last_pdf_id, last_proxy_id))
    global start_datetime
    start_datetime = datetime.now()
    results = {}

    try:
        pdf_result = run_pdf_scraper(last_pdf_id)
        print("validate_places_data")
        isValidPlaces = validate_places_result(pdf_result)
        if isValidPlaces:
            print("Adding places to results")
            results['places_id'] = pdf_result['id']
            results['places_data'] = pdf_result['data']
        else:
            print("Places is not valid, skipping")
    except Exception as e:
        print("Exception while running places scraper")
        print(e)

    try:
        proxy_result = run_proxy_scraper(last_proxy_id)
        print("validate_schedules_data")
        isValidSchedules = validate_schedules_result(proxy_result)
        if isValidSchedules:
            print("Adding schedules to results")
            results['schedules_id'] = proxy_result['id']
            results['schedules_data'] = proxy_result['data']
    except WebDriverException as e:
        if ("ERR_TUNNEL_CONNECTION_FAILED" in e.msg):
            print("WebDriverException while running schedules scrapper: the proxy is down!")
        else:
            print("WebDriverException while running schedules scrapper: there is a problem with the proxy")
            print(e)
    except Exception as e: 
        print(e)
        print("Exception while running schedules scraper")

    if results == "" or len(results) == 0:
        logFinish("Nothing extracted")
    else:
        logFinish("NEW DATA EXTRACTED")
    return results



def run_pdf_scraper(last_document_id):
    print("run_pdf_scraper(%s)" % (last_document_id))
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

    # Download the Google Docs
    localDocPath = tempFolder + currentFileName
    print("Saving Google Doc into " + localDocPath)
    download_file_from_google_drive(new_document_id, localDocPath)

    # Extract data
    print("Extracting places data from pdf...")
    extraction = {}
    json_places = extract_data_from_pdf(localDocPath)
    extraction['id'] = new_document_id
    extraction['data'] = json_places

    return extraction

def get_target_url():

    # TODO: Properly remove SSL warnings: https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
    urllib3.disable_warnings()

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

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)
    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)
    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768
    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def extract_data_from_pdf(pdf_local_path):
    # Reading the pdf file
    print("Reading the PDF with camelot")
    tables = camelot.read_pdf(pdf_local_path,pages='all')

    print("Preparing structures")
    # Prepare dictionary to store all tables in pandas dataframe with keys assigned as data0,data1 and so on..
    # for all tables found by camelot
    data_dic = {}
    # getting all the tables from pdf file
    for no in range(0,len(tables)):
        data_dic['data{}'.format(no)] = copy.copy(tables[no].df)

    # Retrieve group info in each table dataFrame by looping through it. 'x' is column no, 'no' is table no
    all_groups = [] # all groups that are indexed in starting pages
    actual_groups = [] # Groups infs available in the cells of their table
    for no in range(0,len(data_dic)):
        for x in range(0,data_dic['data{}'.format(no)].shape[1]):
            if 'Group' in data_dic['data{}'.format(no)].iloc[0].values[x]:
                if no>5:
                    actual_groups.append((no,x))
                else:
                    all_groups.append((no,x))

    # Setting columns for main(all) grouping data
    for y in range(0,len(all_groups)):
        data_dic['data{}'.format(y)].columns  = data_dic['data{}'.format(y)].iloc[0]
        data_dic['data{}'.format(y)].drop(0,inplace=True)

    # look for what groups we have by looping through columns data
    groups =[]
    for table_no in range(0,len(all_groups)):
        current_table = data_dic['data{}'.format(table_no)]
        for x in current_table.iloc[:,all_groups[1][1]].values:
            for letter in string.ascii_uppercase:
                if letter in x:
                    groups.append(letter)
    groups = sorted(list(set(groups)))
    
    print("Extracting places from PDF...")
    places = extract_places_data(pdf_local_path, tables)
    return places

def extract_places_data(pdf_local_path, tables):
    
    data_dic = {}
    for no in range(0, len(tables)):
        data_dic['{}'.format(no)] = tables[no].df

    # validkeys list determines keys from data_dic which have group id values in group dataframe
    validkeys = []
    for keys in data_dic:
        x = 'GSS' in data_dic[keys][0].unique()
        validkeys.append([int(keys), x])
    temp = []
    while validkeys:
        x = validkeys.pop()
        if x[1] == True:
            temp.append(x)
    # li grabs first value of "true" where 'GSS' is column header
    li = list(reversed(temp.copy()))
    valididx = []
    for x in li:
        valididx.append(x[0])

    # Extract all pages and read text values of pages...  Current exceptions for output containing
    # "group" are:  Group_*[A-Z], but other exceptions may need to be added depending on
    # possible variations of pdf report being scraped
    pages = []
    print("Reading pdf text with PyMuPDF (fitz)...")
    with fitz.open(pdf_local_path) as doc:
        text = ""
        for page in doc:
            text = page.get_text()
            pages.append(text)
    groups = []
    for index, group in enumerate(pages):
        x = re.findall(r"Group *[A-Z]", group)
        y = [index+1, x]
        groups.append(y)

    # Takes scraped data and drops into dataframe. Fills null values following first mention of 
    # "Group_*[A-Z]" (to account for groups that appear on multiple consecutive pages
    df = pd.DataFrame(groups)

    df['group'] = df[1]
    df['group'] = df['group'].astype(str).apply(lambda x: x.replace(
        '[', '').replace('Group', '').replace("'", '').replace(']', ''))
    df['page'] = df[0]
    df = df.drop(columns=[0, 1])

    df = df[['page', 'group']]

    z = df['group'].unique().tolist()
    df['group'][df['group'] == z[0]] = np.NaN
    df['group'] = df['group'].fillna(method='ffill')

    df = df.dropna(axis=0)

    # Re-performs data_dic iteration but includes only valid data tables and concats tables with 
    # multiple pages. Uses range of valididx min (first valid table to be used in output) and 
    # len(tables) (for range of tables to be used in output)
    dfx = pd.DataFrame()
    dfz = pd.DataFrame()
    data_dic1 = {}
    n = min(valididx)-1

    for no in range(min(valididx), len(tables)):
        data_dic1['{}'.format(no)] = tables[no].df

    for keys in data_dic1:
        if (data_dic1[keys][0][0] == 'GSS') == True:
            n = n+1
            dfz = pd.DataFrame.from_dict(data_dic1[keys])
            x = str(df[df['page'] == n]['group'].tolist())
            dfz = dfz.assign(group=x)
            dfx = pd.concat([dfx, dfz], axis=0, ignore_index=True)
        elif (data_dic1[keys][0][1] == 'GSS') == True:
            n = n+1
            dfz = pd.DataFrame.from_dict(data_dic1[keys])
            x = str(df[df['page'] == n]['group'].tolist())
            dfz = dfz.assign(group=x)
            dfx = pd.concat([dfx, dfz], axis=0, ignore_index=True)
        elif (data_dic1[keys][0][1].isnumeric()):
            n = n
        else:
            n = n+1
            dfz = pd.DataFrame.from_dict(data_dic1[keys])
            x = str(df[df['page'] == n]['group'].tolist())
            dfx = pd.concat([dfx, dfz], axis=0, ignore_index=True)

    # Cleaning / Filling empties / Dropping null values
    dfx = dfx.fillna(method='ffill')
    dfx['group'] = dfx['group'].astype(str).apply(
        lambda x: x.replace('[', '').replace("'", '').replace(']', ''))
    dfx['group'] = dfx['group'].replace(to_replace='', value=np.NaN)
    dfx['group'] = dfx['group'].fillna(method='ffill')

    # Reformatting DF for cleaner output
    df = pd.DataFrame()
    df['GSS'] = dfx[0]
    df['Feeder No'] = dfx[1]
    df['Affected Area'] = dfx[2]
    df['Group'] = dfx['group']
    df = df[df['GSS'] != 'GSS']
    df['GSS'] = df['GSS'].replace(to_replace='\\nra', value='', regex=True)
    df['GSS'] = df['GSS'].replace(to_replace='\\na', value='', regex=True)
    df['GSS'] = df['GSS'].replace(to_replace='\\n', value='', regex=True)
    df['GSS'] = df['GSS'].replace(to_replace='', value=np.NaN)
    df['GSS'] = df['GSS'].fillna(method='ffill')
    df['GSS'].replace(to_replace=r'(?i)(\b|\s)new_', value='',
                    regex=True,  inplace=True)
    df['GSS'] = df['GSS'].replace(
        to_replace=r'(?i)Sri_jpura', value='Sri Jayewardenepura', regex=True)
    df['GSS'] = df['GSS'].replace(
        to_replace=r'(?i)Nuwara_Eliya', value='Nuwara Eliya', regex=True)
    df['GSS'] = df['GSS'].replace(
        to_replace=r'(?i)Nuwaraeliya', value='Nuwara Eliya', regex=True)

    df['Feeder No'] = df['Feeder No'].replace(to_replace='', value=np.NaN)
    df['Feeder No'] = df['Feeder No'].fillna(method='ffill')

    df['Affected Area'] = df['Affected Area'].replace(
        to_replace=' \\n', value='', regex=True)
    df['Affected Area'] = df['Affected Area'].replace(
        to_replace='\\n', value='', regex=True)

    df['Affected Area'] = df['Affected Area'].replace(
        to_replace=r'(?i)\srd(\b|\s)', value=' Road ', regex=True)
    df['Affected Area'] = df['Affected Area'].replace(
        to_replace=r'(?i)\spl(\b|\s)', value=' Place ', regex=True)
    df['Affected Area'] = df['Affected Area'].replace(
        to_replace=r'(?i)(\b|\s)new_', value='', regex=True)
    df['Affected Area'] = df['Affected Area'].replace(
        to_replace=r'(?i)[.]?(\w|\s|^\.|\b)+\bleco\b(\w|\s|:|\(|\))+[.]?', value='', regex=True)
    df['Affected Area'] = df['Affected Area'].replace(
        to_replace=r'(?i)\(([portion]+)\)', value='', regex=True)

    # Explode DF w/ string split on Affected Areas, filter out blank values for Affected Areas
    df["Affected Area"] = df["Affected Area"].str.split(",")
    df = df.explode("Affected Area").reset_index(drop=True)
    df["Affected Area"] = df["Affected Area"].str.split("-")
    df = df.explode("Affected Area").reset_index(drop=True)
    df = df[df['Affected Area'] != ""]

    df['GSS'] = df['GSS'].str.strip()
    df['Affected Area'] = df['Affected Area'].str.strip()
    df['Group'] = df['Group'].str.strip()
    df['GSS'] = df['GSS'].str.title()
    df['Affected Area'] = df['Affected Area'].str.capitalize()
    df = df[df['Affected Area'].str.contains(
        'colony|colonies', case=False) == False]
    df = df[df['GSS'].str.contains(
        'Group|Cc Sub', case=False) == False]
    df = df[df['GSS'].str.contains(
        '^Sub', case=False, regex=True) == False]

    df = df[df['GSS'].map(len) > 3]
    df = df[df['Affected Area'].map(len) > 3]
    df = df[~df['GSS'].str.isdigit()]
    # df = df.set_index(['GSS', 'Affected Area', 'Group', 'Feeder No'])

    # Reformat for final json output
    temp_list = df.to_dict('records')
    final_dict = {}
    for item in temp_list:
        group_name = item['Group']
        gss_name = item["GSS"]
        feeder_name = item["Feeder No"]
        feeding_area = item["Affected Area"]

        if gss_name not in final_dict:
            final_dict[gss_name] = dict()

        if feeding_area not in final_dict[gss_name]:
            final_dict[gss_name][feeding_area] = dict()

        if "groups" not in final_dict[gss_name][feeding_area]:
            final_dict[gss_name][feeding_area]["groups"] = list()

        if "feeders" not in final_dict[gss_name][feeding_area]:
            final_dict[gss_name][feeding_area]["feeders"] = list()

        if group_name not in final_dict[gss_name][feeding_area]["groups"]:
            final_dict[gss_name][feeding_area]["groups"].append(group_name)

        if feeder_name not in final_dict[gss_name][feeding_area]["feeders"]:
            final_dict[gss_name][feeding_area]["feeders"].append(feeder_name)

    return final_dict



def run_proxy_scraper(last_row_id):
    print("run_proxy_scraper(%s)" % (last_row_id))
    print("Extracting schedules data from proxy...")

    site_url = "https://cebcare.ceb.lk/Incognito/DemandMgmtSchedule"
    data_url = "https://cebcare.ceb.lk/Incognito/GetLoadSheddingEvents"

    driverManager = DriverManager()
    driver = driverManager.get_driver()
    driver.get(site_url)
    driverManager.print_request()

    time.sleep(4)
    driver.find_element(by=By.CSS_SELECTOR,
                        value="button.fc-dayGridMonth-button").click()
    time.sleep(4)

    browser_log = driver.get_log('performance')
    events = [process_browser_log_entry(entry) for entry in browser_log]
    events = [event for event in events if 'Network.response' in event['method']]

    item_index = None
    for (index, event) in enumerate(events):
        try:
            if(event["params"]["response"]["url"] == data_url):
                item_index = index
        except:
            pass
    
    if (item_index == None):
        print("Data Not Found")
        driver.close()
        return ""

    # Check staus code, on busy time we receive a 429 (Too many requests received)
    data_response_status_code = events[item_index]["params"]["response"]["status"]    
    data_response_status_text = events[item_index]["params"]["response"]["statusText"]    
    if (events[item_index]["params"]["response"]["status"] != 200):
        print("Wrong status code received when requesting data: %s %s" % (data_response_status_code, data_response_status_text))
        driver.close()
        # TODO: Wait and retry
        return ""

    data = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': events[item_index]["params"]["requestId"]})
    data = json.loads(data["body"])
    print(f"Received schedules: {len(data)}")

    # Filter already inserted rows
    data_filter = filter(lambda item: item['id']>last_row_id, data)
    filtered_data = sorted(data_filter, key = lambda item: (item['id']))
    print(f"Filtered schedules: {len(filtered_data)}")

    if (len(filtered_data) == 0):
        return ""

    # Calculate new last id
    new_last_row_id = filtered_data[-1]['id']
    print(f"new_last_row_id: {new_last_row_id}")

    # Count schedules by group (not needed, just for logs and visual verification)
    counted = Counter((item['loadShedGroupId']) for item in filtered_data)
    output = [({'Group' : doctor}, k) for (doctor), k in counted.items()]
    print(output)

    # Sort schedules by date and group
    filtered_data = sorted(filtered_data, key = lambda item: (item['startTime'], item['loadShedGroupId']))

    final_data = list(map(remap_data, filtered_data))

    extraction = {}
    extraction['id'] = new_last_row_id
    extraction['data'] = {'schedules':final_data}

    #with open(os.path.join('output', 'schedule', 'new_schedules.json'), 'w') as outfile:
    #    json.dump(final_data, outfile)
    #print("Data saved in new_schedules.json")
    
    driver.close()
    return extraction

def process_browser_log_entry(entry):
    response = json.loads(entry['message'])['message']
    return response

def remap_data(item):
    obj = {
        #"id": item['id'],
        "group": item['loadShedGroupId'],
        "starting_period": format_date_time(item['startTime']),
        "ending_period": format_date_time(item['endTime']),
    }
    return obj

def format_date_time(date_time):
    # Replace middle T by a space and remove last 3 character for seconds. 
    # Sample: from "2022-05-20T05:00:00" to "2022-05-20 05:00"
    return date_time.replace("T", " ")[:-3]


def validate_places_result(result):
    if (result == "" or not type(result) is dict or not 'data' in result.keys()):
        return False

    json_places = result['data']
    # Print extracted places
    gss_count = len(json_places)
    area_count = 0
    for gss_name in json_places.keys():
        current_gss_areas = len(json_places[gss_name])
        area_count = area_count + current_gss_areas
    print("Extracted places: %s areas in %s gss" % (area_count, gss_count))

    # TODO: validate more things
    if gss_count==0 or area_count==0:
        return False
    
    return True

def validate_schedules_result(result):
    if (result == "" or not type(result) is dict or not 'data' in result.keys()):
        return False

    json_schedules = result['data']
    # Print extracted schedules
    schedules_count = len(json_schedules["schedules"])
    print("Extracted schedules: %s power cuts" % (schedules_count))

    # TODO: validate more things
    if schedules_count==0:
        return False

    return True

def save_all_outputs(places, schedules, document_id):
    with open(outputsFolder + placesFileName, 'w') as outfile:
        json.dump(places, outfile) #, indent=4)
    with open(outputsFolder + schedulesFileName, 'w') as outfile:
        json.dump(schedules, outfile) #, indent=4)
    with open(outputsFolder + lastProcessedFileName, 'w') as f:
        f.write(document_id)
    return


def export_outputs_to_CSV(json_places, json_schedules):
    # Save extracted places in CSV
    csvPath = (outputsFolder + placesFileName).replace(".json", ".csv")
    data = []
    for gss_name in json_places.keys():
        for area_name in json_places[gss_name].keys():
            current_area = json_places[gss_name][area_name]
            for group_name in current_area["groups"]:
                row = {"gss": gss_name, "area": area_name, "group": group_name}
                data.append(row)
    df = pd.DataFrame(data)
    df.to_csv (csvPath, index = None)

    # Save extracted schedules in CSV
    csvPath = (outputsFolder + schedulesFileName).replace(".json", ".csv")
    data = []
    for schedule in json_schedules["schedules"]:
        row = {"group": schedule["group"], "starting_period": schedule["starting_period"], "ending_period": schedule["ending_period"]}
        data.append(row)
    df = pd.DataFrame(data)
    df.to_csv (csvPath, index = None)


def logFinish(reason):
    print("========> %s" % (reason))
    print("========> %s seconds" % (datetime.now().timestamp() - start_datetime.timestamp()))
    print("")
