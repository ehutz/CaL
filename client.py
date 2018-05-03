#!/usr/bin/python

import argparse
import rmq_params
import pika
import pickle
import datetime
import time
from time import sleep
from flask import Flask, request
import requests
from pprint import pprint
from mongoHelper import *

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", type=str, help="TCP_IP")
parser.add_argument("-u", type=str, help="username" )
parser.add_argument("-p", type=str, help="password" )
args = parser.parse_args()
username = "ehutz"
password = ""
if args.s:
    rmq_host = args.s
    host_ip = args.s
    
conn = MongoClient(host_ip, 27017)
if args.p:
    password = args.p
if args.u:
    username = args.u
    while ~userExists(conn, username) and (password != findPassword(conn, username)):
        username = input('Username and password combination does not exist. Please enter correct username: ')
        password = input('Password:')
        print(findPassword(conn, username))
    
# Setup RabbitMQ
credentials = pika.PlainCredentials(username, password)
parameters = pika.ConnectionParameters(rmq_host, 5672, rmq_params.rmq_params["vhost"], credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

print('[Checkpoint] Connected to vhost '
      + '\''
      + rmq_params.rmq_params["vhost"]
      + '\''
      + ' on RMQ server at \''
      + rmq_host
      + '\' as user \''
      + username
      + '\'')
msg = {'username': username, 'message': ""}
while True:
    inputting = input("Press enter to make a timestamp")
    now = datetime.datetime.now()
    msg['message'] = time.mktime(now.timetuple())
    channel.basic_publish(exchange=rmq_params.rmq_params["exchange"],
                  routing_key=rmq_params.rmq_params["client_queue"],
                  body=pickle.dumps(msg))
    time.sleep(1)

    status = requests.get('http://'+host_ip+':20000/status')
    print(status.text)
    if status.text == 'SESSION COMPLETE':
        session_name = requests.get('http://'+host_ip+':20000/session')
        audio = requests.get('http://'+host_ip+':20000/audio/retrieve_file')
        audio_filename = (audio.headers['content-disposition']).split('filename=')[-1]
        #audio_file = audio.file[audio_filename]
        with open('./'+audio_filename, 'wb') as f:
            for chunk in audio.iter_content(chunk_size=512 * 1024):
                f.write(chunk)
            f.close()
            
        # Get PixyCam images
        getPixyCamImages(conn, session_name)
        break

