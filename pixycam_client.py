#!/usr/bin/python

import argparse
import rmq_params
import pika
import pickle
import time
import datetime
# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", help="TCP_PORT")
args=parser.parse_args()

if args.s:
    rmq_host = args.s

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
i = 0
msg = {'username': rmq_params.rmq_params['username'], 'password':rmq_params.rmq_params['password'], 'message': ""}
while i <= 300:    
    now = datetime.datetime.now()
    msg['message'] = time.mktime(now.timetuple())
    channel.basic_publish(exchange=rmq_params.rmq_params["exchange"],
                  routing_key=rmq_params.rmq_params["pixycam_queue"],
                  body=pickle.dumps(msg))
    time.sleep(0.01)
    i = i + 1

