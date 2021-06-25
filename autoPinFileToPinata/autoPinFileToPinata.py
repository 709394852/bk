# autoPinFileToPinata.py
# Automatically add and pin files to IPFS using Pinata.cloud
# Output a csv with important fields filled, including the IPFS hash
#
# usage : 
# syntax: python autoPinFileToPinata.py xmlfilename.xml
# copy the files to be uploaded to a folder in the current folder, name the folder by the input xml filename

import sys
import os
from os import path

sys.stdout.reconfigure(encoding='utf-8')

# Copy your Pinata API Key and Secret here
endpoint = "https://api.pinata.cloud/pinning/pinFileToIPFS"

# Pinata API key
headers = {
"pinata_api_key": "your API key",
"pinata_secret_api_key": "your API secret"}


#Global variable
# CSV fields
fieldnames = ['filename', 'hash', 'title', 'link', 'author', 'subtitle', 'image_href', 'summary', 'enclosure_url', 'enclosure_length', 'enclosure_type', 'guid', 'pubDate', 'explicit', 'duration','showname']
total_records =0 #total number of records to be uploaded

# Parsing Parameter
if(len(sys.argv) != 2):
    print("usage: python autoPinFileToPinata.py xmlfile")
    raise SystemExit

xml_filename = sys.argv[1]

# Load XML file
import xml.etree.ElementTree as ET
print('Reading ', xml_filename, '...... ', end = '', flush= True)
with open(xml_filename, mode='r', encoding="utf-8") as xml_file:
    mytree = ET.parse(xml_file)
    myroot = mytree.getroot()
    print('Done')



def removeBracketedString(s):
    s.replace(" ", "")
    start = s.find("{")
    end = s.find("}")
    if start != -1 and end != -1:
        result = s[end+1:len(s)]
        return result
    return s

# botched get showname
for channel in myroot[0].iter('channel'):
    for child in channel:
        tag = removeBracketedString(child.tag)
        if(tag== 'title'):
            showname = child.text
            print(showname)

listedDict = []
# Read XML data
for item in myroot[0].iter('item'):
    itemDict = {}
    itemDict['filename'] = ''
    itemDict['hash'] = ''
    for child in item:
        tag = removeBracketedString(child.tag)
        if(tag == 'title'):
            itemDict[tag] = child.text
        if(tag == 'link'):
            itemDict[tag] = child.text
        if(tag == 'author'):
            itemDict[tag] = child.text
        if(tag == 'subtitle'):
            itemDict[tag] = child.text
        if(tag == 'image'):
            itemDict['image_href'] = child.attrib['href']
        if(tag == 'summary'):
            itemDict[tag] = child.text
        if(tag == 'enclosure'):
            itemDict['enclosure_url'] = child.attrib['url']
            itemDict['enclosure_length'] = child.attrib['length']
            itemDict['enclosure_type'] = child.attrib['type']
        if(tag == 'guid'):
            itemDict[tag] = child.text
            filename = path.basename(child.text)
            itemDict['filename'] = filename
        if(tag == 'pubDate'):
            itemDict[tag] = child.text
        if(tag == 'explicit'):
            itemDict[tag] = child.text
        if(tag == 'duration'):
            itemDict[tag] = child.text
    itemDict['showname'] = showname
    listedDict.append(itemDict)
total_records=len(listedDict)
print("Total number of records to be uploaded:{}".format(total_records))


import csv

# Load CSV file with the same name, if not exist, create a new one
pre, ext = path.splitext(xml_filename)
csv_filename = pre + '.csv'
if path.isfile(csv_filename):
    # Read the CSV and update our listed dictionary
    with open(csv_filename, mode='r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            for item in listedDict:
                if(row['guid'] == item['guid']):
                    item['hash'] = row['hash']
        print('Read Successful')

        # for some reason, the original csv output file may miss the showname.  Amend this field if that happen
        if ('showname' not in reader.fieldnames):
            with open(csv_filename, mode='w', encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for item in listedDict:
                    print("Writing row ", item)
                    writer.writerow(item)
            print('Write showname Successful')

else:
    # Create a new csv file
    with open(csv_filename, mode='w', encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in listedDict:
            print("Writing row ", item)
            writer.writerow(item)
    print('Write Successful')

import requests
import time #for sleep

# Check each record and upload
for item in listedDict:
    filename = item['filename']
    filepath = os.path.join(pre,filename)
    if(item['hash'] == ''):

        print("filepath={}".format(filepath))
        if path.isfile(filepath):
            print('Uploading {} of {}'.format(listedDict.index(item)+1,total_records), filename, '...... ', end = '', flush= True)
            files = {"file":open(filepath, 'rb')}

            # Retry for 3 times if failed
            retry=0
            print("attempt {}...".format(retry+1),end='',flush=True)
            resp = requests.post(endpoint, headers=headers, files=files)
            while(resp.status_code != 200 and retry < 3):
                retry +=1
                print("attempt {}...".format(retry+1),end='',flush=True)
                time.sleep(15)
                resp = requests.post(endpoint, headers=headers, files=files)
                
            
            if(resp.status_code == 200):
                print("Upload success")
                item['hash'] = resp.json()["IpfsHash"]
                # Update csv file
                with open(csv_filename, mode='w', encoding="utf-8") as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in listedDict:
                        writer.writerow(item)
            else:
                print("Upload failed.  Error:"+str(resp.status_code))
        else:
            print("File ", filename," is missing.")
    else:
        print(item['filename'], " already uploaded before")

