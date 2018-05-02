#!/usr/bin/python

import argparse
import rmq_params
import pika
import pickle
import datetime
import time
from flask import Flask, request
import requests

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", help="TCP_IP")
args = parser.parse_args()
if args.s:
    rmq_host = args.s
    host_ip = args.s

# Setup RabbitMQ
credentials = pika.PlainCredentials(rmq_params.rmq_params["username"], rmq_params.rmq_params["password"])
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
      + rmq_params.rmq_params["username"]
      + '\'')
msg = {'username': rmq_params.rmq_params['username'], 'password':rmq_params.rmq_params['password'], 'message': ""}
while True:
    inputting = input("Press enter to make a timestamp")
    now = datetime.datetime.now()
    msg['message'] = time.mktime(now.timetuple())
    channel.basic_publish(exchange=rmq_params.rmq_params["exchange"],
                  routing_key=rmq_params.rmq_params["client_queue"],
                  body=pickle.dumps(msg))
    time.sleep(1)
    
    status = requests.get('http://'+host_ip+':20002/status')
    print(status.text)
    if status.text == 'SESSION COMPLETE':
        audio_file = requests.get('http://'+host_ip+':20002/audio')
        break
    
            
