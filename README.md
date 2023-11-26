# ![TV7](logo.png) EPG Parser

This is a python script to download the official EPG data from the tv7 backend and export it as XMLTV. The backend API was reverse-engineered from the official Android TV app - for more information check out the the writeup on personal website: [February 6, 2020: Extracting EPG data from the TV7 IPTV service](https://christian.kuendig.info/posts/2020-02-tv7-epg/).

It's designed to include all data available (including picons and channel numbers), and includes caching and rate-limiting to avoid excessive polling the backend no matter how often it is run, making it easy to setup as a scheduled job. It can directly pipe data into the xmltv grabber of Tvheadend via Unix domain sockets. 

# Usage
- For a dockerized deployment (recommended), see [docker-compose.yml](docker-compose.yml) for a sample.

- To run it directly, install the python requirements (`pip3 install -r requirements.txt`) and then  `python3 tv7-epg-parser.py`.

- The script is quiet and the only output you get is the xmltv, this should make it easy to pipe the data for further processing as part of a cron job.
 
- The script supports only one parameter: `-d`/`--debug` enables debug output.