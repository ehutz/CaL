#!/usr/bin/python

import argparse
import rmq_params
import pika
import pickle

# START: Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-s", help="TCP_PORT")

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

while True:
    msg_to_send = input("Please type a message: ")
    channel.basic_publish(exchange=rmq_params.rmq_params["exchange"],
                  routing_key=rmq_params.rmq_params["client_queue"],
                  body=msg_to_send)
            
