import json, os.path
from lxml import etree 
import dateutil.parser 
import requests

BASE_URL="https://tv7api2.tv.init7.net/api/"
DATE_FORMAT = '%Y%m%d%H%M%S%z'

def addChannels(root_elem, channels_data ):
    for result in channels_data:
        channel = etree.Element("channel") 
        channel.set('id',result['pk'].replace('-', ''))
        name_elem = etree.SubElement(channel, "display-name")
        name_elem.text = result['name']
        epg_id_elem = etree.SubElement(channel, "display-name")
        epg_id_elem.text = result['epg_id']
        ordernum_elem = etree.SubElement(channel, "display-name")
        ordernum_elem.text = str(result['ordernum'])

        icon_elem = etree.SubElement(channel, "icon")
        icon_elem.set('src',result['logo'])
        root.append(channel)
        
def addProgrammes(root_elem, programme_data ):
    for result in programme_data:
        programme = etree.Element("programme") 
        for key, value in result.items():
            if key == 'pk':
                continue
            elif key == 'timeslot':
                startTime = dateutil.parser.isoparse(value['lower'])
                stopTime = dateutil.parser.isoparse(value['upper'])
                programme.set("start",startTime.strftime(DATE_FORMAT))
                programme.set("stop",stopTime.strftime(DATE_FORMAT))
                continue
            elif key == 'channel':
                programme.set("channel",value['pk'].replace('-', ''));
                lang = etree.SubElement(programme, "language")
                lang.text = value['language']
                programme.append(lang)
                continue
            elif key == 'title':
                title_elem = etree.SubElement(programme, "title")
                title_elem.set("lang",result['channel']['language'])
                title_elem.text = value
                continue
            elif key == 'sub_title':
                sub_title_elem = etree.SubElement(programme, "sub-title")
                sub_title_elem.set("lang",result['channel']['language'])
                sub_title_elem.text = value
            elif key == 'desc':
                desc_elem = etree.SubElement(programme, "desc")
                desc_elem.set("lang",result['channel']['language'])
                desc_elem.text = value
            elif key == 'categories' and value:
                for category_str in value:
                    category_elem = etree.SubElement(programme, "category")
                    category_elem.set("lang",result['channel']['language'])
                    category_elem.text = category_str
            elif key == 'country' and value:
                country_elem = etree.SubElement(programme,"country")
                country_elem.set("lang",result['channel']['language'])
                country_elem.text = value
            elif key == 'date' and value:
                date_elem = etree.SubElement(programme,"date")
                date_elem.text = str(value)
            elif key == 'icons' and value:
                for icon_url in value:
                    category_elem = etree.SubElement(programme, "icon")
                    category_elem.set("src",icon_url)
            elif key == 'credits' and value:
                credits_elem = etree.SubElement(programme, "credits")
                for credit in value:
                    credit_elem = etree.SubElement(credits_elem,credit['position'])
                    credit_elem.text = credit['name']
            elif key == 'rating_system' and value:
                rating_elem = programme.find('rating')
                if rating_elem is  None:
                    rating_elem = etree.SubElement(programme,'rating')
                rating_elem.set("system",value)
            elif key == 'rating' and value:
                rating_elem = programme.find('rating')
                if rating_elem is  None:
                    rating_elem = etree.SubElement(programme,'rating')
                rating_elem.text = value
            elif key == 'episode_num_system' and value:
                episode_num_elem = programme.find('episode-num')
                if episode_num_elem is  None:
                    episode_num_elem = etree.SubElement(programme,'episode-num')
                episode_num_elem.set("system",value)
            elif key == 'episode_num' and value:
                episode_num_elem = programme.find('episode-num')
                if episode_num_elem is  None:
                    episode_num_elem = etree.SubElement(programme,'episode-num')
                episode_num_elem.text = value
            elif key == 'premiere' and value:
                premiere_elem = etree.SubElement(programme,'premiere')
                if not isinstance(value, (bool)):
                    premiere_elem.text = value
            elif key == 'subtitles' and value:
                subtitles_elem = etree.SubElement(programme,'subtitles')
                if not isinstance(value, (bool)):
                    subtitles_elem.text = value
            elif key == 'star_rating' and value:
                star_rating_elem = etree.SubElement(programme,'star-rating')
                star_rating_elem.text = value
        root_elem.append( programme )




root = etree.Element("tv")

# @GET("allowed/")
# Call<AllowedResponse> allowed();
# curl "${BASE_URL}allowed/" > allowed.json
# TODO: Check allowed URL

# @GET("tvchannel/")
# Call<TvChannelListResponse> tvChannelList();
# curl "${BASE_URL}tvchannel/" > tvChannelList.json

url = BASE_URL+"tvchannel/"

filename = 'tmp/tvChannelList.json'
if not os.path.isfile(filename):
    r = requests.get(url, allow_redirects=True)
    open(filename, 'wb').write(r.content)



with open(filename) as json_file:
    channels_data = json.load(json_file)
    addChannels(root, channels_data['results'])

    for channel in channels_data['results']:
        channel_id = channel['pk']

        # @GET("epg/")
        # Call<EPGListResponse> getEPG(@Query("channel") String paramString);
        # curl "${BASE_URL}epg/?channel=4c8a7d39-009d-4835-b6f9-69c7268fd9d4" > getEPG-channel.json
        url = BASE_URL+"epg/?channel="+channel_id
        filename = 'tmp/getEPG-'+channel_id+'.json'

        if not os.path.isfile(filename):
            r = requests.get(url, allow_redirects=True)
            open(filename, 'wb').write(r.content)

        with open(filename) as json_file:
            programme_data = json.load(json_file)
            addProgrammes(root, programme_data['results'])

    doctype = '<!DOCTYPE tv SYSTEM "https://github.com/XMLTV/xmltv/raw/master/xmltv.dtd">'
    document_str = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8", doctype=doctype)

    with open('./init7-xmltv.xml', 'wb') as f:
        f.write(document_str)

    with open('./init7-xmltv.xml', 'wb') as f:
        f.write(document_str)