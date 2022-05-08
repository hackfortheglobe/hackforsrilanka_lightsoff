

'''
    scraper.py

    This script should be used by calling the scrape function and passing the 
    last processed document id by parameter.

    The outputs will be saved in the outputs folder if a new document id is found.
'''

from calendar import c
from pickle import FALSE, TRUE
from lxml import html
import requests
import camelot
import pandas as pd
from datetime import datetime
import json
import re
from pathlib import Path
import string
import numpy as np
import os
import sys
from lxml import html
import re
import requests
from io import StringIO
from datetime import datetime as dt,timedelta
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
import urllib3

start_datetime = datetime.now()

scraperFolder = f"{os.path.dirname(os.path.abspath(__file__))}/"
tempFolder = f"{scraperFolder}temp/"
currentFileName = 'ceb_current.pdf'
outputsFolder = f"{scraperFolder}outputs/"
lastProcessedFileName = 'last_processed_document_id.txt'
placesFileName = 'places.json'
schedulesFileName = 'schedules.json'

def scrape(last_document_id):

    print("Scraper started with param %s." % (last_document_id))
    global start_datetime
    start_datetime = datetime.now()

    try:
        result = run_scraper(last_document_id)
    except Exception as e:
        print(e)
        logFinish("Error running the scrapper")
        return ""

    if result == "":
        logFinish("Nothing extracted")
    else:
        logFinish("NEW DATA EXTRACTED")
    
    return result


def run_scraper(last_document_id):
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
    extracted_data = extract_data(localDocPath)
    json_places = extracted_data[0]
    json_schedules = extracted_data[1]

    # Validate data
    isValid = validate_extracted_data(json_places, json_schedules)

    if not isValid:
        print("Extrtacted data is not valid")
        return ""

    # Return all results as array instead of using output folder
    extracted_data.append(new_document_id)
    return extracted_data

    # Save all outputs into the output folder
    #save_all_outputs(json_places, json_schedules, new_document_id)

    # Export outputs in CSV
    #export_outputs_to_CSV(json_places, json_schedules)

    #return new_document_id


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


def extract_data(pdf_local_path):
    # Reading the pdf file
    tables = camelot.read_pdf(pdf_local_path,pages='all')

    # Prepare dictionary to store all tables in pandas dataframe with keys assigned as data0,data1 and so on..
    # for all tables found by camelot
    data_dic = {}
    # getting all the tables from pdf file
    for no in range(0,len(tables)):
        data_dic['data{}'.format(no)] = tables[no].df

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

    schedules = extract_schedule_data(data_dic,all_groups,groups,pdf_local_path)
    places = extract_places_data(data_dic,all_groups,groups,actual_groups)

    return [places,schedules]


def extract_schedule_data(data_dic,all_groups,groups,pdf_local_path):
    # converting schedues data from pdf to dictionary form
    schedules = {'schedules':[]}
    date_range = get_dates(pdf_local_path)
    print(f"Document schedule tables: {len(all_groups)}")
    for table_no in range(0,len(all_groups)):
        #passing rows of current table
        current_table = data_dic['data{}'.format(table_no)]
        print(f"Document schedule table #{table_no + 1} has {len(current_table)} data rows.")
        for index,row in current_table.iterrows():
            joined_row = ' '.join(row.values)
            timings = re.finditer(r'\s\d?\d[:.]\d{2}\s(a.m|p.m)?',joined_row)
            #print('Timings after match : ',timings)
            timings = [i.group(0) for i in timings]
            #print('Timings after list : ',timings)
            timings = timeformat_convert24_hr(timings)
            #print('Timings After func : ',timings)
            if timings:
                if ',' in row[all_groups[1][1]]:
                    groups = row[all_groups[1][1]].split(',')
                else:
                    if 'CC' in row[all_groups[1][1]]:
                        continue
                    else:
                        groups = [group for group in row[all_groups[1][1]]]
                for group in groups:
                    for date in date_range:
                        starting_period = f'{date.strftime("%Y-%m-%d")} {timings[0].strip()}'.replace('.',':')
                        ending_period = f'{date.strftime("%Y-%m-%d")} {timings[-1].strip()}'.replace('.',':')
                        schedules['schedules'].append({'group':group.strip(),
                        'starting_period':starting_period,
                        'ending_period':ending_period})
    return schedules

def clean_schedules_timings(timings):
    timings1 = []
    for time in timings:
        #print('Time :',time)
        time = time.strip()
        pattern = r'[:. ]'
        if 'a.m' in time or 'p.m' in time:
            time = re.split(pattern,time)
            #print('Time after regex : ',time)

            #print(f'time 0 {time[0]} time 1 {time[1]} time 2 {time[2]} time 3 {time[3]}')
            # it is 12 hour format
            if time[2] == "a" and int(time[0]) == "12":
                timings1.append(f'00:{time[1]}')
            # remove the AM
            elif time[2] == "a":
                timings1.append(time[0]+':'+time[1])
                # Checking if last two elements of time
                # is PM and first two elements are 12
            elif time[2] == "p" and time[2] == "12":
                timings1.append(f'12:{time[1]}')
            else:
                # add 12 to hours and remove PM
                timings1.append(str(int(time[0]) + 12)+':'+time[1])
    return timings1

def timeformat_convert24_hr(timings):
    if 'a.m' in timings[0] or 'p.m' in timings[0]:
        # it is 12 hour format
        timings = clean_schedules_timings(timings)
        return timings
    else:
        # it is 24 hours format
        timings = [timing.strip() for timing in timings]
        return timings


def extract_places_data(data_dic,all_groups,groups,actual_groups):
    main_dict = {}
    group_count = 0
    not_found=True
    # settings indexes,removing extra row, assigning groups
    for table_no in range(len(all_groups),len(data_dic)):
        # it checks whether tht table has 3 cols
        # it rules out of adding unsymmetrical data to group which just got processed
        if data_dic['data{}'.format(table_no)].shape[1] != 3 or not_found:
            col_check=[]
            for col in data_dic['data{}'.format(table_no)].iloc[0].values:
                if 'GSS' in col:
                    col_check.append(True)
                elif 'Affected' in col:
                    col_check.append(True)
                elif 'Feeder' in col:
                    col_check.append(True)
                else:
                    col_check.append(False)
            if all(col_check):
                not_found =False
            else:
                not_found=True
                continue

        if data_dic['data{}'.format(table_no)].shape[1] == 3:
            # it checks whether the data is countinuing for last group or data for new group
            col_check=[]
            for col in data_dic['data{}'.format(table_no)].iloc[0].values:
                if 'GSS' in col:
                    col_check.append(True)
                elif 'Affected' in col:
                    col_check.append(True)
                elif 'Feeder' in col:
                    col_check.append(True)
                else:
                    col_check.append(False)
            # Starting a New Group
            if all(col_check):
                data_dic['data{}'.format(table_no)].columns  = ['GSS','Feeder No','Affected area']
                data_dic['data{}'.format(table_no)].drop(0,inplace=True)
                main_dict['Group {}'.format(groups[group_count])] = data_dic['data{}'.format(table_no)]
                last_group = 'Group {}'.format(groups[group_count])
                group_count+=1
            # Starting new group for data whose groups are not indexed on above pages
            elif actual_groups:
                if table_no>=actual_groups[0][0] and table_no<=actual_groups[-1][0]:
                    data_dic['data{}'.format(table_no)].columns  = ['GSS','Feeder No','Affected area']
                    main_dict[data_dic['data{}'.format(table_no)].iloc[0].values[0]]= data_dic['data{}'.format(table_no)][2:]

                    last_group = data_dic['data{}'.format(table_no)].iloc[0].values[0]
            # it is concatenating continous data of last group(Note: one filter only: which is.. it should have 3 columns
            #  no way of knowing what data is on current page.)
            else:
                # setting index for this
                data_dic['data{}'.format(table_no)].columns = ['GSS','Feeder No','Affected area']
                main_dict[last_group] = pd.concat([main_dict[last_group],data_dic['data{}'.format(table_no)]])

    # reseting index to make data continous
    main_dict = reset_index(main_dict)
    # fixing multiple rows in same row
    main_dict = fix_multiple_row(main_dict)
    # cleaning areas here
    main_dict = cleaned_areas(main_dict)

    # Creating final output as json dictionary
    final_dic = {}
    for group,table in main_dict.items():
        for row in table.iterrows():
            # checking if GSS is already stored in as keys of final_dic
            if row[1][0] in final_dic.keys():
                # looping through places to save data
                for place in row[1][2]:
                    # skipping place which is empty after cleaning the place
                    if not len(place):
                        continue
                    # checking if place is already stored or not.. as key of District
                    if place in final_dic['{}'.format(row[1][0])].keys():
                        final_dic['{}'.format(row[1][0])][place]['groups'].append(group.split()[1])
                        final_dic['{}'.format(row[1][0])][place]['feeders'].append(row[1][1])

                        # saving only unique groups and feeder No
                        final_dic['{}'.format(row[1][0])][place]['groups'] = list(set(final_dic['{}'.format(row[1][0])][place]['groups']))
                        final_dic['{}'.format(row[1][0])][place]['feeders'] = list(set(final_dic['{}'.format(row[1][0])][place]['feeders']))

                    # if place is not saved yet
                    else:
                        final_dic['{}'.format(row[1][0])][place] = {'groups':[(group.split()[1])],'feeders':[row[1][1]]}
            else:
                final_dic['{}'.format(row[1][0])] = {}
                for place in row[1][2]:
                    if not len(place):
                        continue
                    final_dic['{}'.format(row[1][0])][place] = {'groups':[(group.split()[1])],'feeders':[row[1][1]]}

    return final_dic

# Get the dates affecting the schedule
def get_dates(localDocPath):
    months = ['January','February','March','April','May','June','July','August','September','October','November','December']
    dates_line = extract_dates_line(localDocPath)
    dates = re.findall(r'\b\d{2}\D',dates_line)
    months = re.findall('|'.join(months),dates_line)
    dates = list(map(lambda x: re.findall(r'\d{2}',x)[0],dates))

    if len(dates) == 1:
        range = [dt.strptime(f'{months[0][0:3]} {dates[0]} 2022','%b %d %Y')]
    else:
        if len(months)==1:
            start_date = dt.strptime(f'{months[0][0:3]} {dates[0]} 2022','%b %d %Y')
            end_date = dt.strptime(f'{months[0][0:3]} {dates[1]} 2022','%b %d %Y')
        else:
            start_date = dt.strptime(f'{months[0][0:3]} {dates[0]} 2022','%b %d %Y')
            end_date = dt.strptime(f'{months[1][0:3]} {dates[1]} 2022','%b %d %Y')
        range = get_dates_between(start_date,end_date)

    print(f"Document dates: {range}")
    return range

# Read the days affecting the schedule by reading the first line at the pdf
def extract_dates_line(localDocPath):
    output_string = StringIO()
    with open(localDocPath, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    pdf_data= output_string.getvalue()
    dates_line = re.findall(r'Demand Management Schedule.+\b\d{2}\D+\b',pdf_data)[0]
    print (f"Document title: {dates_line}")
    return dates_line

# Gives all days between two dates in datetime format
def get_dates_between(start, end):
    delta = end - start  # as timedelta
    days = [start + timedelta(days=i) for i in range(delta.days + 1)]
    return days

def cleaned_areas(main_dict):
    for key,value in main_dict.items():
        count=0
        for places,gss in value[['Affected area','GSS']].itertuples(index=False):
            # cleaning GSS
            gss = re.sub(r'(\b|\s)new_','',gss.replace("\n", ""),flags=re.IGNORECASE)
            main_dict[key]['GSS'][count] = gss
            # cleaning Affected Area
            places = [ x.replace("\n", "").strip() for x in places.split(',')]
            places = list(map(lambda x: re.sub(r'\srd(\b|\s)',' Road ',x,flags=re.IGNORECASE),places))
            places = list(map(lambda x: re.sub(r'\spl(\b|\s)',' Place',x,flags=re.IGNORECASE),places))
            places = [x for x in places if 'colony' not in x.lower() and 'colonies' not in x.lower()]
            places = list(map(lambda x: re.sub(r'(\b|\s)new_','',x,flags=re.IGNORECASE),places))
            places = list(map(lambda x: re.sub(r'[.]?(\w|\s|^\.|\b)+\bleco\b(\w|\s|:|\(|\))+[.]?','',x,flags=re.IGNORECASE),places))
            places = list(map(lambda x: x.capitalize(),places))
            places = [x for x in places if len(x)>3]
            main_dict[key]['Affected area'][count] = places
            count+=1
    return main_dict

def reset_index(main_dict):
    for group,table in main_dict.items():
        table.reset_index(drop=True,inplace=True)
    return main_dict

def fix_multiple_row(main_dict):
    for table in main_dict.values():
        table['GSS'][table['GSS']==''] = np.NaN
        table['Feeder No'][table['Feeder No']==''] = np.NaN
        table['GSS'].fillna(method='ffill',inplace=True)
        table['Feeder No'].fillna(method='ffill',inplace=True)
    return main_dict

def validate_extracted_data(json_places, json_schedules):
    # Print extracted places
    gss_count = len(json_places)
    area_count = 0
    for gss_name in json_places.keys():
        current_gss_areas = len(json_places[gss_name])
        area_count = area_count + current_gss_areas
    print("Extracted places: %s areas in %s gss" % (area_count, gss_count))

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
