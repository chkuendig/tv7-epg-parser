import json
import os.path
import argparse
from lxml import etree
import dateutil.parser
import requests
from stat import S_ISSOCK
from datetime import timedelta
import socket

import time

BASE_URL = "https://api.tv.init7.net/api/"
DATE_FORMAT = '%Y%m%d%H%M%S%z'
MAX_DOWNLOADS = 10
MAX_FILE_AGE = 48*60*60
TMP_FOLDER = "tmp/"
TVH_XMLTV_SOCKET = "epggrab/xmltv.sock"
arg_parser = argparse.ArgumentParser(
    description='fetch epg data from init7 and return it')
arg_parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable Debugging')
args = vars(arg_parser.parse_args())

def addChannels(root_elem, channels_data):
    for result in channels_data:
        channel = etree.Element("channel")
        channel.set('id',  result['canonical_name'])
        name_elem = etree.SubElement(channel, "display-name")
        name_elem.text = result['name']
        ordernum_elem = etree.SubElement(channel, "display-name")
        ordernum_elem.text = str(result['ordernum'])  

        icon_elem = etree.SubElement(channel, "icon")
        icon_elem.set('src', result['logo'])
        root.append(channel)

def checkProgrammesUnique(iterator):
    try:
        first = next(iterator)
    except StopIteration:
        return False
    return not all(first['title'] == x['title'] for x in iterator)

def addProgrammes(root_elem, programme_data):
    if(len(programme_data) == 0):
        return 0 # empty epg
    
    if(not checkProgrammesUnique(iter(programme_data))):
        if args['debug']:
            print("Skipping channel with placeholder data: "+ programme_data[0]['channel']['name'])
        return 0 # some channels only have placeholder data
        
    for result in programme_data:
        programme = etree.Element("programme")
        for key, value in result.items():
            if key == 'pk':
                continue
            elif key == 'timeslot':
                startTime = dateutil.parser.isoparse(value['lower'])
                stopTime = dateutil.parser.isoparse(value['upper'])

                # TV7 streams the More4+1 stream but has the More4 EPG data.
                if result['channel']['canonical_name'] == "More4.uk":
                    if args['debug']:
                        print("Changing times for "+result['channel']['name'] )
                    startTime = startTime +  timedelta(hours=1)
                    stopTime = startTime +  timedelta(hours=1)
                
                programme.set("start", startTime.strftime(DATE_FORMAT))
                programme.set("stop", stopTime.strftime(DATE_FORMAT))
                continue
            elif key == 'channel':
                programme.set("channel",value['canonical_name'])
                lang = etree.SubElement(programme, "language")
                lang.text = value['language']
                programme.append(lang)
                continue
            elif key == 'title':
                title_elem = etree.SubElement(programme, "title")
                title_elem.set("lang", result['channel']['language'])
                title_elem.text = value
                continue
            elif key == 'sub_title':
                sub_title_elem = etree.SubElement(programme, "sub-title")
                sub_title_elem.set("lang", result['channel']['language'])
                sub_title_elem.text = value
            elif key == 'desc':
                desc_elem = etree.SubElement(programme, "desc")
                desc_elem.set("lang", result['channel']['language'])
                desc_elem.text = value
            elif key == 'categories' and value:
                for category_str in value:
                    category_elem = etree.SubElement(programme, "category")
                    category_elem.set("lang", result['channel']['language'])
                    category_elem.text = category_str
            elif key == 'country' and value:
                country_elem = etree.SubElement(programme, "country")
                country_elem.set("lang", result['channel']['language'])
                country_elem.text = value
            elif key == 'date' and value:
                date_elem = etree.SubElement(programme, "date")
                date_elem.text = str(value)
            elif key == 'icons' and value:
                for icon_url in value:
                    category_elem = etree.SubElement(programme, "icon")
                    category_elem.set("src", icon_url)
            elif key == 'credits' and value:
                credits_elem = etree.SubElement(programme, "credits")
                for credit in value:
                    credit_elem = etree.SubElement(
                        credits_elem, credit['position'])
                    credit_elem.text = credit['name']
            elif key == 'rating_system' and value:
                rating_elem = programme.find('rating')
                if rating_elem is None:
                    rating_elem = etree.SubElement(programme, 'rating')
                rating_elem.set("system", value)
            elif key == 'rating' and value:
                rating_elem = programme.find('rating')
                if rating_elem is None:
                    rating_elem = etree.SubElement(programme, 'rating')
                rating_elem.text = value
            elif key == 'episode_num_system' and value:
                episode_num_elem = programme.find('episode-num')
                if episode_num_elem is None:
                    episode_num_elem = etree.SubElement(
                        programme, 'episode-num')
                episode_num_elem.set("system", value)
            elif key == 'episode_num' and value:
                episode_num_elem = programme.find('episode-num')
                if episode_num_elem is None:
                    episode_num_elem = etree.SubElement(
                        programme, 'episode-num')
                episode_num_elem.text = value
            elif key == 'premiere' and value:
                premiere_elem = etree.SubElement(programme, 'premiere')
                if not isinstance(value, (bool)):
                    premiere_elem.text = value
            elif key == 'subtitles' and value:
                subtitles_elem = etree.SubElement(programme, 'subtitles')
                if not isinstance(value, (bool)):
                    subtitles_elem.text = value
            elif key == 'star_rating' and value:
                star_rating_elem = etree.SubElement(programme, 'star-rating')
                star_rating_elem.text = value
        root_elem.append(programme)
    return len(programme_data)

def _file_age_in_seconds(pathname):
    return time.time() - os.path.getmtime(pathname)


def is_valid_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError as e:
    return False
  return True

downloadCount = 0


def _downloadFile(filename, url):
    global downloadCount
    if not os.path.isfile(filename) or (downloadCount < MAX_DOWNLOADS and _file_age_in_seconds(filename) > MAX_FILE_AGE):
        if args['debug']:
            print("downloading ", url)
        r = requests.get(url, allow_redirects=True)
        if(is_valid_json(r.content)):
            open(filename, 'wb').write(r.content)
        time.sleep(1)
        downloadCount = downloadCount+1
    else:
        if args['debug']:
            print("skipping %s already downloaded to %s"%( url, filename))

# @GET("allowed/")
# Call<AllowedResponse> allowed();
# curl "${BASE_URL}allowed/" > allowed.json
# TODO: Check allowed URL


######
# start building xmltv file
######

# URL found at https://www.init7.net/en/tv/channels/
url = 'https://api.init7.net/fiber7-tv-channels.v2.json?lang_order=en&streaming_type=all'
filename = os.path.join(TMP_FOLDER, 'fiber7-tv-channels.v2.json')
_downloadFile(filename, url)
root = etree.Element("tv")
with open(filename) as json_file:
    channels_data = json.load(json_file)
    addChannels(root, channels_data['results'])
    missing_epg = []
    for channel in channels_data['results']:
        channel_id = channel['pk']

        # @GET("epg/")
        # Call<EPGListResponse> getEPG(@Query("channel") String paramString);
        # curl "${BASE_URL}epg/?channel=4c8a7d39-009d-4835-b6f9-69c7268fd9d4" > getEPG-channel.json
        url = BASE_URL+"epg/?channel="+channel_id+"&limit=999"

        filename = os.path.join(
            TMP_FOLDER, 'getEPG-'+channel_id + ".json")
        _downloadFile(filename, url)

        with open(filename) as json_file:

            try:
                programme_data = json.load(json_file)

                if 'results' in programme_data:
                    programme_cnt = addProgrammes(root, programme_data['results'])
                    if(programme_cnt == 0 and args['debug']):
                        print("No EPG data for "+channel['name'])
                        missing_epg.append(channel['name'])
                else:
                    if args['debug']:
                        print(programme_data)
            except json.JSONDecodeError as e:
                if args['debug']:
                    print(filename + " parsing error: ")
                    print(e)
                    print("deleting file...")
                    os.remove(filename)
 
    if args['debug']:
        missing_epg.sort(key=str.casefold)
        print("Fetching EPG done. Total %d channels, %d channels missing EPG: %s"%(len(channels_data['results']),len(missing_epg), ", ".join(missing_epg)))
    
    doctype = '<!DOCTYPE tv SYSTEM "https://github.com/XMLTV/xmltv/raw/master/xmltv.dtd">'
    document_str = etree.tostring(
        root, pretty_print=True, xml_declaration=True, encoding="UTF-8", doctype=doctype)

    xmltv_file = os.path.join(TMP_FOLDER, 'init7-xmltv' + ".xml")
    with open(xmltv_file, 'wb') as f:
        f.write(document_str)

    if os.path.exists(TVH_XMLTV_SOCKET):
        if S_ISSOCK(os.stat(TVH_XMLTV_SOCKET).st_mode):
            if args['debug']:
                print("Socket exists")
                
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

            try:
                # Connect to server and send data
                if args['debug']:
                    print ("Attempting connection")
                sock.connect(TVH_XMLTV_SOCKET)
                if args['debug']:
                    print ("Sending XMLTV string")

                with open(xmltv_file, 'r') as fin:
                     sock.sendall(fin.read().encode())
                if args['debug']:
                    print( "XMLTV sent")

            finally:
                sock.close()
        else: 
            if args['debug']:
                print("XML Socket file exists but isn't socket")
    else:
        if args['debug']:
            print("XML Socket file doesn't exist")
        else:
            with open(xmltv_file, 'r') as fin:
                print(fin.read())
        
