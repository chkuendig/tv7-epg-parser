FROM python:3-slim

# Sample from https://hub.docker.com/_/python

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python3", "./tv7-epg-parser.py" ]